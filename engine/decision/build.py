from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json
import math

import numpy as np
from PIL import Image

from engine.terrain_truth.bbox import BBox
from engine.terrain_truth.contract import SiteArtifact, CorridorArtifact, DecisionArtifact
from engine.species_profiles import GENERAL_SPECIES_ID, get_species_profile, species_profile_to_dict

try:
    import rasterio
except Exception:
    rasterio = None


def _provider_penalty_from_notes(notes: list[str]) -> tuple[float, float, list[str]]:
    terrain = "unknown"
    legal = "unknown"
    reasons = []

    for note in notes:
        if note.startswith("Provider status:"):
            parts = note.replace("Provider status:", "").split(",")
            for part in parts:
                if "terrain=" in part:
                    terrain = part.split("=", 1)[1].strip().lower()
                if "legal=" in part:
                    legal = part.split("=", 1)[1].strip().lower()

    score_penalty = 0.0
    confidence_penalty = 0.0

    if terrain == "failed":
        score_penalty -= 20.0
        confidence_penalty -= 30.0
        reasons.append("Terrain provider failed")

    if legal == "failed":
        score_penalty -= 12.0
        confidence_penalty -= 18.0
        reasons.append("Legal data unavailable")
    elif legal == "empty":
        score_penalty -= 4.0
        confidence_penalty -= 8.0
        reasons.append("No legal features returned")

    return score_penalty, confidence_penalty, reasons


def _vegetation_profile(operator_context: dict | None) -> dict:
    operator_context = operator_context or {}
    vegetation = str(operator_context.get("vegetation_classification") or "unknown").strip().lower()
    provider = str(operator_context.get("vegetation_provider") or "unknown").strip().lower()

    profiles = {
        "forest": {
            "classification": "forest",
            "score_delta": 8.0,
            "confidence_delta": 6.0,
            "travel_delta": 4.0,
            "bedding_delta": 10.0,
            "feeding_delta": 0.0,
            "reason": "Vegetation read: forest cover materially improves concealment, strengthens bedding reliability, and supports a more trustworthy sit call.",
            "tags": ["Cover Advantage", "Bedding Support"],
        },
        "shrub": {
            "classification": "shrub",
            "score_delta": 4.0,
            "confidence_delta": 3.0,
            "travel_delta": 3.0,
            "bedding_delta": 5.0,
            "feeding_delta": 1.0,
            "reason": "Vegetation read: shrub cover adds workable concealment and modestly strengthens travel and bedding confidence.",
            "tags": ["Cover Advantage", "Mixed Cover"],
        },
        "open": {
            "classification": "open",
            "score_delta": -6.0,
            "confidence_delta": -6.0,
            "travel_delta": -2.0,
            "bedding_delta": -10.0,
            "feeding_delta": 2.0,
            "reason": "Vegetation read: open ground sharply reduces concealment, weakens bedding security, and should pull this sit down unless terrain is doing unusual work.",
            "tags": ["Open Exposure", "Weak Bedding"],
        },
        "water": {
            "classification": "water",
            "score_delta": -12.0,
            "confidence_delta": -10.0,
            "travel_delta": -5.0,
            "bedding_delta": -12.0,
            "feeding_delta": -3.0,
            "reason": "Vegetation read: water-dominant ground is a poor default sit signal here and should be treated as a strong downgrade.",
            "tags": ["Water Penalty", "Weak Bedding"],
        },
        "unknown": {
            "classification": "unknown",
            "score_delta": 0.0,
            "confidence_delta": -1.0,
            "travel_delta": 0.0,
            "bedding_delta": 0.0,
            "feeding_delta": 0.0,
            "reason": "Vegetation input is unavailable, so cover influence stays conservative and no concealment bonus was applied.",
            "tags": ["Vegetation Unknown"],
        },
    }

    profile = dict(profiles.get(vegetation, profiles["unknown"]))
    profile["provider"] = provider
    if provider == "terrain_heuristic":
        profile["score_delta"] *= 0.75
        profile["confidence_delta"] -= 1.5
        profile["reason"] += " This read came from terrain fallback rather than direct land-cover data, so confidence stays slightly tempered."
        if "Heuristic Cover" not in profile["tags"]:
            profile["tags"] = [*profile["tags"], "Heuristic Cover"][:3]
    elif provider not in {"nlcd_annual", "terrain_heuristic"} and profile["classification"] != "unknown":
        profile["confidence_delta"] -= 2.0
        profile["reason"] += " Vegetation provider quality is limited here, so the signal is kept cautious."

    return profile




def _species_region_key(bbox: list[float]) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    center_lon = (float(min_lon) + float(max_lon)) / 2.0
    center_lat = (float(min_lat) + float(max_lat)) / 2.0
    if center_lon < -108 and center_lat > 36:
        return "rocky_mountains"
    if center_lon < -108 and center_lat <= 36:
        return "southwest"
    if center_lon > -90 and center_lat < 37:
        return "southeast"
    if -104 < center_lon < -92 and 35 < center_lat < 47:
        return "great_plains"
    if center_lon < -117 and center_lat < 42:
        return "california_coastal_west"
    if center_lon < -117:
        return "pacific_northwest"
    if center_lon > -83 and center_lat > 40:
        return "northeast"
    if center_lon > -90 and center_lat >= 37:
        return "appalachia"
    if -92 <= center_lon <= -83 and center_lat >= 40:
        return "great_lakes"
    if -104 <= center_lon <= -90:
        return "midwest"
    return "texas_south_central" if center_lat < 35 else "mid_atlantic"


def _species_region_supported(profile, region_key: str) -> bool:
    if profile.profile_id == GENERAL_SPECIES_ID:
        return True
    return region_key in set(profile.regions_supported)


def _species_profile_for_run(operator_context: dict, bbox: list[float]) -> dict:
    profile = get_species_profile(operator_context.get("selected_species"))
    region_key = _species_region_key(bbox)
    supported = _species_region_supported(profile, region_key)
    data = species_profile_to_dict(profile)
    data["region_key"] = region_key
    data["region_supported"] = supported
    if profile.profile_id == GENERAL_SPECIES_ID:
        data["effective_multiplier"] = 0.0
    elif supported:
        data["effective_multiplier"] = 1.0
    else:
        data["effective_multiplier"] = 0.60
    return data


def _terrain_feature_flags(terrain_read: dict, vegetation_classification: str) -> dict[str, bool]:
    """Return the small, structured terrain feature set used for species-aware scoring.

    These flags intentionally mirror signals already computed by _terrain_reasoning,
    so the command surface payload stays stable and no template/UI changes are required.
    """
    veg = str(vegetation_classification or "unknown").lower()
    return {
        "ridge": bool(terrain_read.get("ridge_like") or terrain_read.get("shoulder_like") or terrain_read.get("funnel_like")),
        "bench": bool(terrain_read.get("bench_like") or terrain_read.get("bedding_like")),
        "edge": bool(terrain_read.get("edge_risk") or terrain_read.get("intercept_like") or terrain_read.get("funnel_like") or terrain_read.get("convergence_like")),
        "open": bool(veg == "open"),
        "cover": bool(veg in {"forest", "shrub"} or terrain_read.get("interior_secure") or terrain_read.get("bedding_like")),
    }


def _feature_weight(deltas: dict, keys: list[str]) -> float:
    values = [float(deltas[key]) for key in keys if key in deltas]
    if not values:
        return 0.0
    return sum(values) / len(values)


def _species_family(species_profile: dict) -> str:
    """Collapse the selected profile into a broad behavior family for feature scoring.

    This covers the whole launch-page species list, then the dominant-trait
    scoring pass uses each profile's actual weights for fine separation.
    """
    text = " ".join(
        str(species_profile.get(key) or "").lower()
        for key in ("profile_id", "label", "common_name")
    )
    if "turkey" in text:
        return "turkey"
    if "elk" in text:
        return "elk"
    if "moose" in text:
        return "moose"
    if "bear" in text:
        return "bear"
    if "hog" in text or "boar" in text:
        return "hog"
    if "javelina" in text:
        return "javelina"
    if "bighorn" in text or "sheep" in text:
        return "bighorn"
    if "pronghorn" in text or "antelope" in text:
        return "pronghorn"
    if "coyote" in text or "predator" in text:
        return "coyote"
    if "mule" in text and "deer" in text:
        return "mule_deer"
    if "deer" in text or "whitetail" in text or "white-tailed" in text:
        return "deer"
    return "general"

def _structured_species_feature_delta(species_profile: dict, features: dict[str, bool]) -> tuple[float, list[str]]:
    """Convert explicit feature flags into a visible species-specific score modifier.

    This is intentionally still small enough to keep the original terrain engine in
    charge, but strong enough that deer, turkey, bear, and elk do not all choose
    the same terrain when the map offers better species-specific alternatives.
    """
    if species_profile.get("profile_id") == GENERAL_SPECIES_ID:
        return 0.0, []

    deltas = species_profile.get("deltas") or {}
    feature_weight_keys = {
        "ridge": ["ridge_weight", "saddle_weight", "elevation_position_weight", "escape_terrain_weight"],
        "bench": ["bench_weight", "bedding_cover_weight", "thermal_behavior_weight", "shade_heat_refuge_weight"],
        "edge": ["edge_density_weight", "crop_edge_weight", "funnel_corridor_weight", "access_route_risk_weight"],
        "open": ["open_visibility_weight", "glassing_visibility_weight"],
        "cover": ["cover_density_weight", "bedding_cover_weight", "shade_heat_refuge_weight"],
    }

    family_matrix: dict[str, dict[str, float]] = {
        "deer": {"bench": 4.0, "edge": 3.0, "cover": 2.5, "ridge": 0.75, "open": -3.25},
        "mule_deer": {"bench": 3.25, "ridge": 2.75, "open": 2.25, "edge": 1.0, "cover": -0.75},
        "turkey": {"open": 4.25, "ridge": 3.25, "edge": 2.0, "bench": 0.75, "cover": -2.5},
        "bear": {"cover": 4.25, "edge": 1.5, "bench": 0.75, "ridge": -1.5, "open": -3.25},
        "hog": {"cover": 4.0, "edge": 2.25, "bench": 0.25, "ridge": -2.0, "open": -2.75},
        "javelina": {"cover": 3.75, "edge": 1.25, "bench": 0.5, "ridge": -0.75, "open": -2.25},
        "elk": {"ridge": 3.5, "bench": 2.25, "edge": 1.5, "open": 1.25, "cover": 0.5},
        "moose": {"cover": 3.0, "bench": 1.0, "edge": 0.75, "ridge": -1.25, "open": -0.75},
        "bighorn": {"ridge": 4.25, "open": 4.0, "bench": 0.5, "edge": -1.0, "cover": -4.0},
        "pronghorn": {"open": 4.5, "ridge": 1.25, "edge": -1.0, "bench": -0.5, "cover": -3.5},
        "coyote": {"open": 2.75, "ridge": 2.25, "edge": 2.5, "bench": 0.25, "cover": 0.25},
        "general": {},
    }

    family = _species_family(species_profile)
    family_weights = family_matrix.get(family, {})
    raw_delta = 0.0
    active_labels: list[str] = []
    for feature_name, keys in feature_weight_keys.items():
        if not bool(features.get(feature_name)):
            continue
        profile_weight = _feature_weight(deltas, keys)
        family_weight = float(family_weights.get(feature_name, 0.0))
        combined_weight = (profile_weight * 0.45) + family_weight
        if combined_weight == 0.0:
            continue
        raw_delta += combined_weight
        active_labels.append(feature_name)

    multiplier = float(species_profile.get("effective_multiplier") or 0.0)
    return max(-9.5, min(9.5, raw_delta * 0.72 * multiplier)), active_labels[:5]


def _feature_readout_text(features: dict[str, bool], species_profile: dict) -> str:
    """Plain-English internal feature read for debugging and future tuning."""
    ordered = ["ridge", "bench", "edge", "open", "cover"]
    active = [name for name in ordered if bool((features or {}).get(name))]
    inactive = [name for name in ordered if name not in active]
    active_text = ", ".join(active) if active else "none"
    inactive_text = ", ".join(inactive) if inactive else "none"
    family = _species_family(species_profile)
    if family == "deer":
        bias = "Whitetail weighting favors bench-edge-cover security and penalizes exposed open ground."
    elif family == "turkey":
        bias = "Turkey weighting favors open visibility, ridge/spur travel, and lighter cover."
    elif family == "bear":
        bias = "Bear weighting favors lower, thicker, shaded drainage and food-cover structure."
    elif family == "hog":
        bias = "Hog weighting favors low wet cover, food edges, wallow context, and pressure-safe movement."
    elif family == "javelina":
        bias = "Javelina weighting favors brush, washes, shade, water context, and protected group movement."
    elif family == "elk":
        bias = "Elk weighting favors ridge, bench, saddle, water, and larger herd-travel structure."
    elif family == "moose":
        bias = "Moose weighting favors wet cover, low draws, shade, and heavy browse security."
    elif family == "mule_deer":
        bias = "Mule deer weighting favors glassable broken country, benches, draws, and escape position."
    elif family == "bighorn":
        bias = "Bighorn weighting favors steep open escape terrain and visibility over timber cover."
    elif family == "pronghorn":
        bias = "Pronghorn weighting favors open visibility and penalizes tight cover."
    elif family == "coyote":
        bias = "Coyote weighting favors wind-controlled visibility, draws, edges, and downwind travel checks."
    else:
        bias = "General weighting keeps the base terrain read dominant."
    return f"Feature read: active={active_text}; inactive={inactive_text}. {bias}"


def _species_signal_value(variable: str, terrain_read: dict, sample: dict, slope_bias: str, elev_norm: float, vegetation_classification: str) -> float:
    veg = str(vegetation_classification or "unknown").lower()
    local_relief = float(sample.get("local_relief") or 0.0)
    slope = float(sample.get("slope") or 0.0)
    if variable == "edge_density_weight":
        return 1.0 if terrain_read.get("edge_risk") or terrain_read.get("intercept_like") else 0.35
    if variable == "cover_density_weight":
        return 1.0 if veg in {"forest", "shrub"} or terrain_read.get("interior_secure") else -0.35 if veg == "open" else 0.0
    if variable == "open_visibility_weight":
        return 1.0 if veg == "open" or elev_norm >= 0.58 else -0.35 if veg == "forest" else 0.25
    if variable == "elevation_position_weight":
        return max(-0.5, min(1.0, (elev_norm - 0.35) * 2.0))
    if variable == "slope_weight":
        return 1.0 if slope_bias in {"shoulder", "steep", "ridge"} or slope >= 14 else 0.25
    if variable == "ridge_weight":
        return 1.0 if terrain_read.get("ridge_like") else 0.0
    if variable == "saddle_weight":
        return 1.0 if terrain_read.get("convergence_like") or terrain_read.get("funnel_like") else 0.0
    if variable == "bench_weight":
        return 1.0 if terrain_read.get("bench_like") else 0.0
    if variable == "draw_drainage_weight":
        return 1.0 if terrain_read.get("convergence_like") or terrain_read.get("funnel_like") or elev_norm <= 0.42 else 0.25
    if variable == "water_proximity_weight":
        return 1.0 if veg == "water" or elev_norm <= 0.38 else 0.35
    if variable == "food_source_weight":
        return 1.0 if veg in {"forest", "shrub", "open"} and (terrain_read.get("edge_risk") or elev_norm <= 0.45) else 0.35
    if variable == "crop_edge_weight":
        return 1.0 if veg == "open" and terrain_read.get("edge_risk") else 0.0
    if variable == "mast_hardwood_weight":
        return 1.0 if veg == "forest" else 0.0
    if variable == "roost_tree_weight":
        return 1.0 if veg == "forest" and (terrain_read.get("ridge_like") or elev_norm >= 0.45) else 0.0
    if variable == "bedding_cover_weight":
        return 1.0 if terrain_read.get("bedding_like") or terrain_read.get("interior_secure") or veg in {"forest", "shrub"} else -0.35
    if variable == "wallow_mud_water_weight":
        return 1.0 if veg == "water" or elev_norm <= 0.35 else 0.0
    if variable == "wind_discipline_weight":
        return 1.0
    if variable == "thermal_behavior_weight":
        return 1.0 if local_relief >= 18 or slope_bias in {"bench", "shoulder", "ridge"} else 0.25
    if variable == "human_pressure_avoidance_weight":
        return 1.0 if terrain_read.get("interior_secure") else 0.35
    if variable == "access_route_risk_weight":
        return 1.0 if terrain_read.get("edge_risk") else 0.35
    if variable == "time_of_day_bias":
        return 0.5
    if variable == "seasonal_phase_bias":
        return 0.5
    if variable == "nocturnal_bias":
        return 0.5
    if variable == "group_movement_bias":
        return 0.5 if terrain_read.get("funnel_like") or terrain_read.get("convergence_like") else 0.2
    if variable == "glassing_visibility_weight":
        return 1.0 if veg == "open" or elev_norm >= 0.55 else 0.0
    if variable == "funnel_corridor_weight":
        return 1.0 if terrain_read.get("funnel_like") or terrain_read.get("convergence_like") or terrain_read.get("intercept_like") else 0.0
    if variable == "escape_terrain_weight":
        return 1.0 if slope >= 16 or terrain_read.get("ridge_like") or elev_norm >= 0.60 else 0.0
    if variable == "shade_heat_refuge_weight":
        return 1.0 if veg in {"forest", "shrub"} or slope_bias in {"bench", "shoulder"} else 0.0
    return 0.0



def _dominant_trait_delta(species_profile: dict, terrain_read: dict, sample: dict, slope_bias: str, elev_norm: float, vegetation_classification: str) -> tuple[float, str]:
    """Amplify the selected animal's strongest identity instead of hand-studying each one.

    Every profile already has trait weights. This finds the strongest traits,
    makes those traits matter more, and adds a small terrain-band push so
    animals stop collapsing onto the same generally-good sit.
    """
    if species_profile.get("profile_id") == GENERAL_SPECIES_ID:
        return 0.0, ""

    deltas = species_profile.get("deltas") or {}
    if not deltas:
        return 0.0, ""

    multiplier = float(species_profile.get("effective_multiplier") or 0.0)
    veg = str(vegetation_classification or "unknown").lower()
    family = _species_family(species_profile)

    ranked = sorted(deltas.items(), key=lambda kv: abs(float(kv[1])), reverse=True)
    dominant = ranked[:6]
    dominant_raw = 0.0
    labels: list[str] = []
    for variable, weight in dominant:
        signal = _species_signal_value(variable, terrain_read, sample, slope_bias, elev_norm, vegetation_classification)
        weight_f = float(weight)
        authority = 1.65 if abs(weight_f) >= 3.0 else 1.30
        dominant_raw += weight_f * signal * authority
        labels.append(variable.replace("_weight", "").replace("_bias", "").replace("_", " "))

    high_axis = (
        float(deltas.get("elevation_position_weight", 0.0))
        + 0.75 * float(deltas.get("ridge_weight", 0.0))
        + 0.70 * float(deltas.get("glassing_visibility_weight", 0.0))
        + 0.50 * float(deltas.get("escape_terrain_weight", 0.0))
    )
    low_axis = (
        float(deltas.get("draw_drainage_weight", 0.0))
        + float(deltas.get("water_proximity_weight", 0.0))
        + float(deltas.get("wallow_mud_water_weight", 0.0))
        + 0.65 * float(deltas.get("shade_heat_refuge_weight", 0.0))
    )
    open_axis = (
        float(deltas.get("open_visibility_weight", 0.0))
        + float(deltas.get("glassing_visibility_weight", 0.0))
        - 0.75 * float(deltas.get("cover_density_weight", 0.0))
    )
    cover_axis = (
        float(deltas.get("cover_density_weight", 0.0))
        + float(deltas.get("bedding_cover_weight", 0.0))
        + float(deltas.get("shade_heat_refuge_weight", 0.0))
        - 0.75 * float(deltas.get("open_visibility_weight", 0.0))
    )
    corridor_axis = (
        float(deltas.get("edge_density_weight", 0.0))
        + float(deltas.get("funnel_corridor_weight", 0.0))
        + float(deltas.get("crop_edge_weight", 0.0))
    )

    band_delta = 0.0
    if high_axis - low_axis >= 2.0:
        band_delta += (elev_norm - 0.50) * 8.0
    elif low_axis - high_axis >= 2.0:
        band_delta += (0.48 - elev_norm) * 10.0

    if open_axis >= 2.5:
        band_delta += 3.0 if (veg == "open" or elev_norm >= 0.56 or terrain_read.get("ridge_like")) else -2.0
    elif cover_axis >= 3.5:
        band_delta += 3.0 if (veg in {"forest", "shrub"} or terrain_read.get("interior_secure")) else -2.0

    if corridor_axis >= 4.5:
        band_delta += 2.0 if (terrain_read.get("edge_risk") or terrain_read.get("funnel_like") or terrain_read.get("convergence_like")) else -1.5

    if family in {"bear", "hog", "javelina", "moose"}:
        band_delta += (0.44 - elev_norm) * 7.0
        if terrain_read.get("ridge_like") and family in {"bear", "hog", "javelina"}:
            band_delta -= 3.0
    elif family in {"bighorn", "pronghorn"}:
        band_delta += (elev_norm - 0.45) * 7.0
        if veg in {"forest", "shrub"} and family == "pronghorn":
            band_delta -= 4.0
    elif family in {"turkey", "coyote", "mule_deer"}:
        band_delta += (elev_norm - 0.42) * 3.5

    raw = (dominant_raw * 0.24) + band_delta
    delta = max(-13.0, min(13.0, raw * multiplier))
    label_text = ", ".join(labels[:4]) if labels else "profile traits"
    note = f"Dominant-trait read: {label_text} shaped this species call ({delta:+.1f})."
    return delta, note

def _apply_species_tuning(species_profile: dict, terrain_read: dict, sample: dict, slope_bias: str, elev_norm: float, vegetation_classification: str, features: dict[str, bool], travel_score: float, bedding_score: float, feeding_score: float, score: float, confidence: float) -> tuple[float, float, float, float, float, list[str], str]:
    if species_profile.get("profile_id") == GENERAL_SPECIES_ID:
        return travel_score, bedding_score, feeding_score, score, confidence, [], ""
    multiplier = float(species_profile.get("effective_multiplier") or 0.0)
    raw_delta = 0.0
    for variable, weight in (species_profile.get("deltas") or {}).items():
        signal = _species_signal_value(variable, terrain_read, sample, slope_bias, elev_norm, vegetation_classification)
        raw_delta += float(weight) * signal
    capped_delta = max(-12.0, min(12.0, raw_delta * 0.55 * multiplier))
    feature_delta, active_features = _structured_species_feature_delta(species_profile, features)
    dominant_delta, dominant_note = _dominant_trait_delta(species_profile, terrain_read, sample, slope_bias, elev_norm, vegetation_classification)
    total_delta = capped_delta + feature_delta + dominant_delta
    score += total_delta
    confidence += max(-6.0, min(6.0, total_delta * 0.35))
    if total_delta > 2.0:
        travel_score += min(6.0, total_delta * 0.35)
        bedding_score += min(5.0, total_delta * 0.22)
        feeding_score += min(5.0, total_delta * 0.22)
    elif total_delta < -2.0:
        travel_score += max(-5.0, total_delta * 0.25)
        bedding_score += max(-5.0, total_delta * 0.20)
        feeding_score += max(-5.0, total_delta * 0.20)
    label = str(species_profile.get("label") or "Selected Species")
    tag = f"{label} Tune"
    warning = ""
    if not species_profile.get("region_supported", True):
        warning = f"Species-region caution: {label} may be uncommon or unavailable in this broad region, so Monahinga™ reduced species influence and kept the general terrain read dominant."
    feature_text = ""
    if active_features:
        feature_text = " Feature-aware signals: " + ", ".join(active_features) + f" ({feature_delta:+.1f})."
    dominant_text = (" " + dominant_note) if dominant_note else ""
    note = f"Species tuning: {label} modifier {total_delta:+.1f}." + feature_text + dominant_text + f" {species_profile.get('positive_hook') or ''}"
    if warning:
        note += " " + warning
    return travel_score, bedding_score, feeding_score, score, confidence, [tag], note



def _clamp_float(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _stable_behavior_drift(species_key: str, item: dict) -> float:
    """Tiny deterministic drift so tied sites do not collapse into identical choices."""
    seed = f"{species_key}:{float(item.get('lon', 0.0)):.6f}:{float(item.get('lat', 0.0)):.6f}:{item.get('source_name', '')}"
    total = sum((idx + 1) * ord(ch) for idx, ch in enumerate(seed))
    return ((total % 2001) / 1000.0) - 1.0


def _candidate_behavior_metrics(item: dict, candidates: list[dict], bbox: list[float]) -> dict[str, float]:
    elevations = [float(c.get('elevation_m') or 0.0) for c in candidates]
    if elevations:
        lo = min(elevations)
        hi = max(elevations)
        rng = max(1.0, hi - lo)
        elev_norm = (float(item.get('elevation_m') or lo) - lo) / rng
    else:
        elev_norm = float(item.get('elevation_norm') or 0.5)
    elev_norm = _clamp_float(float(item.get('elevation_norm', elev_norm)), 0.0, 1.0)

    features = item.get('features') or {}
    slope = float(item.get('slope') or 0.0)
    relief = float(item.get('local_relief') or 0.0)
    ridge = 1.0 if features.get('ridge') else 0.0
    bench = 1.0 if features.get('bench') or item.get('bench_like') else 0.0
    edge = 1.0 if features.get('edge') or item.get('edge_risk') or item.get('intercept_like') else 0.0
    open_ground = 1.0 if features.get('open') else 0.0
    cover = 1.0 if features.get('cover') or item.get('interior_secure') else 0.0
    funnel = 1.0 if item.get('funnel_like') or item.get('convergence_like') else 0.0
    shoulder = 1.0 if item.get('shoulder_like') else 0.0

    flow = _clamp_float((funnel * 0.35) + (shoulder * 0.20) + (edge * 0.18) + (bench * 0.17) + (ridge * 0.10), 0.0, 1.0)
    security = _clamp_float((cover * 0.45) + (bench * 0.22) + (1.0 - open_ground) * 0.18 + (1.0 - elev_norm) * 0.15, 0.0, 1.0)
    visibility = _clamp_float((open_ground * 0.38) + (ridge * 0.22) + (shoulder * 0.14) + (elev_norm * 0.18) + (min(slope, 28.0) / 28.0) * 0.08, 0.0, 1.0)
    food = _clamp_float((cover * 0.26) + (edge * 0.22) + ((1.0 - elev_norm) * 0.22) + (bench * 0.12) + (open_ground * 0.10) + (funnel * 0.08), 0.0, 1.0)
    broken = _clamp_float((min(relief, 45.0) / 45.0) * 0.34 + (min(slope, 30.0) / 30.0) * 0.24 + shoulder * 0.18 + ridge * 0.12 + bench * 0.12, 0.0, 1.0)
    low = 1.0 - elev_norm
    high = elev_norm
    loop = _clamp_float((food * 0.40) + (low * 0.24) + (cover * 0.22) + (edge * 0.12) - (flow * 0.22), 0.0, 1.0)

    min_lon, min_lat, max_lon, max_lat = bbox
    diag = max(1e-9, math.hypot(max_lon - min_lon, max_lat - min_lat))
    flow_anchors = []
    for cand in candidates:
        cand_features = cand.get('features') or {}
        cand_flow = (
            (0.35 if cand.get('funnel_like') or cand.get('convergence_like') else 0.0)
            + (0.20 if cand.get('shoulder_like') else 0.0)
            + (0.18 if cand_features.get('edge') or cand.get('edge_risk') or cand.get('intercept_like') else 0.0)
            + (0.17 if cand_features.get('bench') or cand.get('bench_like') else 0.0)
            + (0.10 if cand_features.get('ridge') else 0.0)
        )
        if cand_flow >= 0.45:
            flow_anchors.append(cand)
    if flow_anchors:
        d = min(math.hypot(float(item.get('lon', 0.0)) - float(c.get('lon', 0.0)), float(item.get('lat', 0.0)) - float(c.get('lat', 0.0))) for c in flow_anchors)
        distance_from_flow = _clamp_float(d / diag / 0.35, 0.0, 1.0)
    else:
        distance_from_flow = 0.5

    return {
        'flow': flow,
        'security': security,
        'visibility': visibility,
        'edge': edge,
        'food': food,
        'broken': broken,
        'low': low,
        'high': high,
        'loop': loop,
        'distance_from_flow': distance_from_flow,
    }


def _behavior_profile_v2(species_profile: dict) -> dict[str, float | str]:
    family = _species_family(species_profile)
    profiles: dict[str, dict[str, float | str]] = {
        'deer': {'label': 'edge-security optimizer', 'flow_follow': 0.52, 'security_bias': 0.90, 'visibility_bias': 0.18, 'edge_affinity': 1.00, 'feed_drive': 0.55, 'broken_bias': 0.25, 'low_bias': 0.05, 'high_bias': -0.12, 'loop_bias': 0.10, 'flow_distance': -0.10, 'drift': 0.25},
        'turkey': {'label': 'visibility mover', 'flow_follow': 0.58, 'security_bias': -0.18, 'visibility_bias': 1.08, 'edge_affinity': 0.45, 'feed_drive': 0.55, 'broken_bias': 0.10, 'low_bias': -0.12, 'high_bias': 0.35, 'loop_bias': -0.05, 'flow_distance': 0.05, 'drift': 0.30},
        'bear': {'label': 'feed-and-hide cover user', 'flow_follow': 0.18, 'security_bias': 0.95, 'visibility_bias': -0.30, 'edge_affinity': 0.50, 'feed_drive': 1.08, 'broken_bias': 0.20, 'low_bias': 0.70, 'high_bias': -0.35, 'loop_bias': 0.55, 'flow_distance': 0.15, 'drift': 0.35},
        'hog': {'label': 'low feed-loop crawler', 'flow_follow': -0.25, 'security_bias': 0.95, 'visibility_bias': -0.55, 'edge_affinity': 0.50, 'feed_drive': 1.20, 'broken_bias': -0.05, 'low_bias': 0.85, 'high_bias': -0.45, 'loop_bias': 0.90, 'flow_distance': 0.30, 'drift': 0.45},
        'javelina': {'label': 'brush-and-wash group mover', 'flow_follow': 0.10, 'security_bias': 0.90, 'visibility_bias': -0.25, 'edge_affinity': 0.35, 'feed_drive': 0.85, 'broken_bias': 0.15, 'low_bias': 0.65, 'high_bias': -0.28, 'loop_bias': 0.70, 'flow_distance': 0.25, 'drift': 0.42},
        'mule_deer': {'label': 'offset glass-and-escape selector', 'flow_follow': -0.15, 'security_bias': 0.45, 'visibility_bias': 0.92, 'edge_affinity': 0.30, 'feed_drive': 0.48, 'broken_bias': 0.95, 'low_bias': -0.10, 'high_bias': 0.22, 'loop_bias': -0.15, 'flow_distance': 0.78, 'drift': 0.28},
        'elk': {'label': 'herd-flow corridor follower', 'flow_follow': 1.10, 'security_bias': 0.55, 'visibility_bias': 0.22, 'edge_affinity': 0.48, 'feed_drive': 0.62, 'broken_bias': -0.25, 'low_bias': -0.05, 'high_bias': 0.20, 'loop_bias': -0.20, 'flow_distance': -0.50, 'drift': 0.22},
        'moose': {'label': 'wet-cover browse drifter', 'flow_follow': -0.05, 'security_bias': 1.00, 'visibility_bias': -0.45, 'edge_affinity': 0.30, 'feed_drive': 1.05, 'broken_bias': -0.20, 'low_bias': 0.80, 'high_bias': -0.55, 'loop_bias': 0.70, 'flow_distance': 0.20, 'drift': 0.38},
        'bighorn': {'label': 'steep open escape selector', 'flow_follow': 0.10, 'security_bias': -0.35, 'visibility_bias': 1.05, 'edge_affinity': -0.25, 'feed_drive': 0.20, 'broken_bias': 1.10, 'low_bias': -0.70, 'high_bias': 0.95, 'loop_bias': -0.35, 'flow_distance': 0.05, 'drift': 0.25},
        'pronghorn': {'label': 'open-country sightline selector', 'flow_follow': -0.10, 'security_bias': -0.60, 'visibility_bias': 1.20, 'edge_affinity': -0.35, 'feed_drive': 0.35, 'broken_bias': -0.40, 'low_bias': 0.00, 'high_bias': 0.25, 'loop_bias': -0.25, 'flow_distance': 0.20, 'drift': 0.35},
        'coyote': {'label': 'wind-edge predator checker', 'flow_follow': 0.38, 'security_bias': 0.15, 'visibility_bias': 0.70, 'edge_affinity': 0.80, 'feed_drive': 0.25, 'broken_bias': 0.45, 'low_bias': 0.05, 'high_bias': 0.25, 'loop_bias': 0.05, 'flow_distance': 0.35, 'drift': 0.55},
        'general': {'label': 'general terrain reader', 'flow_follow': 0.25, 'security_bias': 0.25, 'visibility_bias': 0.25, 'edge_affinity': 0.25, 'feed_drive': 0.25, 'broken_bias': 0.00, 'low_bias': 0.00, 'high_bias': 0.00, 'loop_bias': 0.00, 'flow_distance': 0.00, 'drift': 0.10},
    }
    return profiles.get(family, profiles['general'])


def _apply_behavior_profiles_v2(candidates: list[dict], species_profile: dict, bbox: list[float]) -> None:
    """Post-score behavior layer for all launch-page species."""
    if not candidates or species_profile.get('profile_id') == GENERAL_SPECIES_ID:
        return
    multiplier = float(species_profile.get('effective_multiplier') or 0.0)
    if multiplier <= 0.0:
        return
    family = _species_family(species_profile)
    profile = _behavior_profile_v2(species_profile)
    label = str(profile.get('label') or family)
    for item in candidates:
        metrics = _candidate_behavior_metrics(item, candidates, bbox)
        axis = (
            metrics['flow'] * float(profile['flow_follow'])
            + metrics['security'] * float(profile['security_bias'])
            + metrics['visibility'] * float(profile['visibility_bias'])
            + metrics['edge'] * float(profile['edge_affinity'])
            + metrics['food'] * float(profile['feed_drive'])
            + metrics['broken'] * float(profile['broken_bias'])
            + metrics['low'] * float(profile['low_bias'])
            + metrics['high'] * float(profile['high_bias'])
            + metrics['loop'] * float(profile['loop_bias'])
            + metrics['distance_from_flow'] * float(profile['flow_distance'])
        )
        delta = (axis - 0.62) * 11.0
        if family == 'mule_deer':
            delta += (metrics['distance_from_flow'] - 0.30) * 7.0
            delta += metrics['broken'] * 3.0
            delta -= metrics['flow'] * 3.5
        elif family == 'elk':
            delta += metrics['flow'] * 4.0
            delta -= metrics['distance_from_flow'] * 3.0
            delta -= metrics['broken'] * 1.25
        elif family == 'turkey':
            delta += metrics['visibility'] * 4.0
            delta -= metrics['security'] * 2.8
            delta -= metrics['low'] * 1.5
        elif family == 'deer':
            delta += metrics['security'] * 2.6
            delta += metrics['edge'] * 2.2
            delta -= metrics['visibility'] * 1.3
        elif family in {'hog', 'javelina'}:
            delta += metrics['loop'] * 5.0
            delta += metrics['low'] * 2.5
            delta -= metrics['flow'] * 3.5
            delta -= metrics['visibility'] * 2.5
        elif family in {'bear', 'moose'}:
            delta += metrics['food'] * 3.0
            delta += metrics['security'] * 2.0
            delta += metrics['low'] * 2.0
            delta -= metrics['visibility'] * 1.8
        elif family in {'bighorn', 'pronghorn'}:
            delta += metrics['visibility'] * 4.0
            delta += metrics['high'] * 2.5
            delta -= metrics['security'] * 2.5
            if family == 'bighorn':
                delta += metrics['broken'] * 3.5
            else:
                delta -= metrics['broken'] * 1.5
        elif family == 'coyote':
            delta += metrics['edge'] * 2.5
            delta += metrics['visibility'] * 2.0
            delta += metrics['distance_from_flow'] * 1.5
        delta += _stable_behavior_drift(family, item) * float(profile['drift'])
        # Squash instead of hard-clipping. The old hard clamp made many very-good
        # candidates all land at +11, which hid useful behavioral separation during
        # close comparisons. This keeps the same safe range while preserving order.
        delta = math.tanh(delta / 18.0) * 11.0 * multiplier
        delta = _clamp_float(delta, -11.0, 11.0)
        if abs(delta) < 0.15:
            continue
        item['score'] = int(round(float(item.get('score') or 0.0) + delta))
        item['confidence'] = int(round(float(item.get('confidence') or 0.0) + _clamp_float(delta * 0.25, -3.0, 3.0)))
        item['behavior_profile_v2_delta'] = round(delta, 1)
        item['behavior_profile_v2_label'] = label
        item['behavior_profile_v2_metrics'] = {
            'flow': round(metrics['flow'], 2),
            'security': round(metrics['security'], 2),
            'visibility': round(metrics['visibility'], 2),
            'food': round(metrics['food'], 2),
            'broken': round(metrics['broken'], 2),
            'low': round(metrics['low'], 2),
            'flow_offset': round(metrics['distance_from_flow'], 2),
        }
        metric_bits = ', '.join(f"{k}={v}" for k, v in item['behavior_profile_v2_metrics'].items())
        item['reasoning'] = str(item.get('reasoning') or '') + f" Behavior Profiles v2: {label} adjusted this final selection ({delta:+.1f}; {metric_bits})."

def _sanity_gate(bbox):
    if bbox is None:
        raise ValueError("Sanity gate failed: bbox is None")

    if bbox.min_lat >= bbox.max_lat:
        raise ValueError("Sanity gate failed: invalid latitude range")

    if bbox.min_lon >= bbox.max_lon:
        raise ValueError("Sanity gate failed: invalid longitude range")

    return bbox


def _legality_gate(features):
    gated = []
    for feat in features:
        props = dict(feat.get("properties") or {})
        legal_class = str(props.get("monahinga_legal_class", "unknown")).lower()
        if legal_class == "legal":
            gated.append(feat)
    return gated


def _legal_confidence_weight(interior_secure: bool, edge_risk: bool) -> tuple[float, float]:
    score_delta = 0.0
    confidence_delta = 0.0
    if interior_secure:
        score_delta += 3.0
        confidence_delta += 4.0
    if edge_risk:
        score_delta -= 3.0
        confidence_delta -= 5.0
    return score_delta, confidence_delta


def _boundary_hunt_weight(edge_risk: bool, terrain_read: dict) -> tuple[float, float, str | None]:
    if not edge_risk:
        return 0.0, 0.0, None

    movement_edge = bool(
        terrain_read.get("funnel_like")
        or terrain_read.get("convergence_like")
        or terrain_read.get("shoulder_like")
        or terrain_read.get("intercept_like")
    )
    bedding_edge = bool(terrain_read.get("bedding_like") and terrain_read.get("bench_like"))

    if movement_edge:
        return 6.0, 4.5, "Boundary Funnel"
    if bedding_edge:
        return 3.5, 2.5, "Boundary Bedding Edge"
    return -1.5, -1.5, "Boundary Exposure"


def _wildlife_micro_signal(
    terrain_truth_root: Path,
    terrain_read: dict,
) -> tuple[float, float, float, float, str | None]:
    adapter_path = terrain_truth_root / "wildlife" / "wildlife_adapter_request.json"
    if not adapter_path.exists():
        return 0.0, 0.0, 0.0, 0.0, None

    try:
        payload = json.loads(adapter_path.read_text(encoding="utf-8"))
    except Exception:
        return 0.0, 0.0, 0.0, 0.0, None

    conditions = payload.get("conditions") or {}
    wind_speed = conditions.get("wind_speed_mph")
    try:
        wind_speed = float(wind_speed) if wind_speed is not None else None
    except Exception:
        wind_speed = None

    if wind_speed is None:
        return 0.0, 0.0, 0.0, 0.0, None

    movement_lane = bool(
        terrain_read.get("funnel_like")
        or terrain_read.get("convergence_like")
        or terrain_read.get("shoulder_like")
        or terrain_read.get("intercept_like")
    )
    bedding_hold = bool(terrain_read.get("bedding_like") and terrain_read.get("interior_secure"))
    edge_lane = bool(terrain_read.get("edge_risk") and movement_lane)
    interior_bedding = bool(
        terrain_read.get("bedding_like")
        and terrain_read.get("interior_secure")
        and not terrain_read.get("edge_risk")
    )

    if wind_speed >= 8.0 and edge_lane:
        return 12.0, 4.0, 8.0, 0.0, "Wildlife Movement Push"

    if wind_speed >= 8.0 and movement_lane:
        return 9.0, 3.0, 6.0, 0.0, "Wildlife Movement Push"

    if wind_speed <= 6.0 and interior_bedding:
        return 8.0, 3.0, 0.0, 7.0, "Wildlife Bedding Hold"

    if wind_speed <= 6.0 and bedding_hold:
        return 6.0, 2.0, 0.0, 5.0, "Wildlife Bedding Hold"

    return 0.0, 0.0, 0.0, 0.0, None


def _wind_behavior_override(
    requested_wind: str,
    preferred_wind: str,
    terrain_read: dict,
) -> tuple[float, float, float, float, str | None]:
    requested_wind = str(requested_wind or "").strip().upper()
    preferred_wind = str(preferred_wind or "").strip().upper()
    if not requested_wind or not preferred_wind:
        return 0.0, 0.0, 0.0, 0.0, None

    movement_lane = bool(
        terrain_read.get("funnel_like")
        or terrain_read.get("convergence_like")
        or terrain_read.get("shoulder_like")
        or terrain_read.get("intercept_like")
    )
    secure_cover = bool(terrain_read.get("interior_secure"))
    exposed_edge = bool(terrain_read.get("edge_risk"))
    bedding_hold = bool(terrain_read.get("bedding_like") and secure_cover)

    if requested_wind == preferred_wind:
        if movement_lane and secure_cover:
            return 28.0, 18.0, 4.0, 8.0, "Wind-Driven Movement"
        if bedding_hold:
            return 18.0, 2.0, 14.0, 7.0, "Wind-Safe Bedding"
        if movement_lane:
            return 20.0, 14.0, 2.0, 5.0, "Wind-Driven Movement"
        return 0.0, 0.0, 0.0, 0.0, None

    if movement_lane and exposed_edge:
        return -30.0, -20.0, -2.0, -14.0, "Wind-Blown Travel"
    if bedding_hold:
        return -22.0, -4.0, -16.0, -10.0, "Wind-Exposed Bedding"
    if movement_lane:
        return -24.0, -16.0, -2.0, -10.0, "Wind-Blown Travel"
    return -8.0, -2.0, -2.0, -4.0, "Wind-Misaligned"


def _sanitize_dem(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float32)
    finite = np.isfinite(arr)
    if not finite.any():
        return np.zeros_like(arr, dtype=np.float32)
    valid = arr[finite]
    valid = valid[(valid > -1000.0) & (valid < 9000.0)]
    if valid.size == 0:
        valid = arr[finite]
    low = float(np.percentile(valid, 2.0))
    high = float(np.percentile(valid, 98.0))
    cleaned = np.clip(np.where(np.isfinite(arr), arr, np.nan), low, high)
    fill = float(np.nanmedian(valid))
    cleaned = np.nan_to_num(cleaned, nan=fill, posinf=high, neginf=low)
    return cleaned.astype(np.float32)


def _load_dem(dem_path: Path) -> np.ndarray:
    if rasterio is not None:
        with rasterio.open(dem_path) as ds:
            arr = ds.read(1).astype(np.float32)
            nodata = ds.nodata
            if nodata is not None:
                arr[arr == nodata] = np.nan
            return arr
    return np.array(Image.open(dem_path), dtype=np.float32)


def _resolve_dem_path(terrain_truth_root: Path) -> Path:
    contract_path = terrain_truth_root / "terrain_contract.json"
    if contract_path.exists():
        try:
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            rel = ((contract.get("terrain") or {}).get("path") or "").strip()
            if rel:
                candidate = terrain_truth_root.parent / Path(rel)
                if candidate.exists():
                    return candidate
        except Exception:
            pass

    terrain_dir = terrain_truth_root / "terrain"
    for name in ["dem.tif", "usgs_dem.tif", "copernicus_dem.tif"]:
        candidate = terrain_dir / name
        if candidate.exists():
            return candidate

    tif_files = sorted(terrain_dir.glob("*.tif"))
    if tif_files:
        return tif_files[0]

    raise FileNotFoundError(f"No DEM file found under {terrain_dir}")


def _point_in_ring(point_lon: float, point_lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = ((yi > point_lat) != (yj > point_lat)) and (
            point_lon < (xj - xi) * (point_lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _point_in_polygon(point_lon: float, point_lat: float, coords: list) -> bool:
    if not coords:
        return False
    if not _point_in_ring(point_lon, point_lat, coords[0]):
        return False
    for hole in coords[1:]:
        if _point_in_ring(point_lon, point_lat, hole):
            return False
    return True


def _feature_contains(lon: float, lat: float, geom: dict) -> bool:
    geom_type = geom.get("type")
    coords = geom.get("coordinates") or []
    if geom_type == "Polygon":
        return _point_in_polygon(lon, lat, coords)
    if geom_type == "MultiPolygon":
        return any(_point_in_polygon(lon, lat, poly) for poly in coords)
    return False


def _feature_center(geom: dict) -> tuple[float, float]:
    coords = geom.get("coordinates") or []
    points = []
    if geom.get("type") == "Polygon":
        for ring in coords:
            points.extend(ring)
    elif geom.get("type") == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                points.extend(ring)
    xs = [p[0] for p in points] or [0.0]
    ys = [p[1] for p in points] or [0.0]
    return float(sum(xs) / len(xs)), float(sum(ys) / len(ys))


def _feature_bbox(geom: dict) -> tuple[float, float, float, float]:
    coords = geom.get("coordinates") or []
    points = []
    if geom.get("type") == "Polygon":
        for ring in coords:
            points.extend(ring)
    elif geom.get("type") == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                points.extend(ring)
    xs = [p[0] for p in points] or [0.0]
    ys = [p[1] for p in points] or [0.0]
    return float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))


def _feature_name(props: dict) -> str:
    for key in ["Unit_Nm", "MngNm_Desc", "ManagerName", "BndryName"]:
        value = str(props.get(key, "")).strip()
        if value and value.lower() != "not applicable":
            return value
    return "Unnamed Ground"


def _descriptor(lon: float, lat: float, bbox: list[float]) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    x = (lon - min_lon) / max(max_lon - min_lon, 1e-12)
    y = (lat - min_lat) / max(max_lat - min_lat, 1e-12)
    vertical = "North" if y > 0.66 else "South" if y < 0.33 else "Mid"
    horizontal = "East" if x > 0.66 else "West" if x < 0.33 else "Core"
    if vertical == "Mid" and horizontal == "Core":
        return "Core Converge"
    if vertical == "Mid":
        return f"{horizontal} Shoulder"
    if horizontal == "Core":
        return f"{vertical} Bench"
    return f"{vertical} {horizontal} Spur"


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _dedupe_points(points: list[list[float]]) -> list[list[float]]:
    out: list[list[float]] = []
    for pt in points:
        if not out or abs(pt[0] - out[-1][0]) > 1e-9 or abs(pt[1] - out[-1][1]) > 1e-9:
            out.append([float(pt[0]), float(pt[1])])
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) <= 1e-9 and abs(out[0][1] - out[-1][1]) <= 1e-9:
        out.pop()
    return out


def _intersect_vertical(start: list[float], end: list[float], x_edge: float) -> list[float]:
    dx = end[0] - start[0]
    if abs(dx) <= 1e-12:
        return [x_edge, start[1]]
    t = (x_edge - start[0]) / dx
    return [x_edge, start[1] + t * (end[1] - start[1])]


def _intersect_horizontal(start: list[float], end: list[float], y_edge: float) -> list[float]:
    dy = end[1] - start[1]
    if abs(dy) <= 1e-12:
        return [start[0], y_edge]
    t = (y_edge - start[1]) / dy
    return [start[0] + t * (end[0] - start[0]), y_edge]


def _clip_ring_to_bbox(ring: list[list[float]], bbox: BBox) -> list[list[float]]:
    if len(ring) < 3:
        return []
    subject = _dedupe_points([list(map(float, pt[:2])) for pt in ring if len(pt) >= 2])
    if len(subject) < 3:
        return []

    def clip(points: list[list[float]], inside, intersect):
        if not points:
            return []
        output: list[list[float]] = []
        prev = points[-1]
        prev_inside = inside(prev)
        for curr in points:
            curr_inside = inside(curr)
            if curr_inside:
                if not prev_inside:
                    output.append(intersect(prev, curr))
                output.append(curr)
            elif prev_inside:
                output.append(intersect(prev, curr))
            prev = curr
            prev_inside = curr_inside
        return _dedupe_points(output)

    clipped = subject
    clipped = clip(clipped, lambda p: p[0] >= bbox.min_lon - 1e-9, lambda a, b: _intersect_vertical(a, b, bbox.min_lon))
    clipped = clip(clipped, lambda p: p[0] <= bbox.max_lon + 1e-9, lambda a, b: _intersect_vertical(a, b, bbox.max_lon))
    clipped = clip(clipped, lambda p: p[1] >= bbox.min_lat - 1e-9, lambda a, b: _intersect_horizontal(a, b, bbox.min_lat))
    clipped = clip(clipped, lambda p: p[1] <= bbox.max_lat + 1e-9, lambda a, b: _intersect_horizontal(a, b, bbox.max_lat))
    clipped = _dedupe_points(clipped)
    return clipped if len(clipped) >= 3 else []


def _clip_geometry_to_bbox(geom: dict, bbox: BBox) -> dict | None:
    geom_type = geom.get("type")
    coords = geom.get("coordinates") or []
    if geom_type == "Polygon":
        clipped = []
        for idx, ring in enumerate(coords):
            ring_clipped = _clip_ring_to_bbox(ring, bbox)
            if not ring_clipped:
                continue
            if idx == 0:
                clipped.insert(0, ring_clipped)
            else:
                clipped.append(ring_clipped)
        return {"type": "Polygon", "coordinates": clipped} if clipped else None
    if geom_type == "MultiPolygon":
        polys = []
        for poly in coords:
            clipped_poly = []
            for idx, ring in enumerate(poly):
                ring_clipped = _clip_ring_to_bbox(ring, bbox)
                if not ring_clipped:
                    continue
                if idx == 0:
                    clipped_poly.insert(0, ring_clipped)
                else:
                    clipped_poly.append(ring_clipped)
            if clipped_poly:
                polys.append(clipped_poly)
        return {"type": "MultiPolygon", "coordinates": polys} if polys else None
    return None


def _sample_dem(arr: np.ndarray, bbox: list[float], lon: float, lat: float) -> dict:
    min_lon, min_lat, max_lon, max_lat = bbox
    width = arr.shape[1]
    height = arr.shape[0]
    x = int(round((lon - min_lon) / max(max_lon - min_lon, 1e-12) * (width - 1)))
    y = int(round((1.0 - (lat - min_lat) / max(max_lat - min_lat, 1e-12)) * (height - 1)))
    x = max(1, min(width - 2, x))
    y = max(1, min(height - 2, y))

    elevation = float(arr[y, x])

    neighborhood = arr[y - 1 : y + 2, x - 1 : x + 2]
    slope = float(np.std(neighborhood))

    dzdx = float(arr[y, x + 1] - arr[y, x - 1]) / 2.0
    dzdy = float(arr[y + 1, x] - arr[y - 1, x]) / 2.0
    aspect_deg = (math.degrees(math.atan2(-dzdx, dzdy)) + 360.0) % 360.0

    broad = arr[max(0, y - 5) : min(height, y + 6), max(0, x - 5) : min(width, x + 6)]
    local_relief = float(np.max(broad) - np.min(broad))

    return {
        "elevation_m": elevation,
        "slope": slope,
        "aspect_deg": aspect_deg,
        "local_relief": local_relief,
    }


def _quantize_slope(slope_value: float) -> str:
    if slope_value < 1.8:
        return "bench"
    if slope_value < 4.0:
        return "shoulder"
    return "steeper side-slope"


def _sample_indices(arr: np.ndarray, bbox: list[float], lon: float, lat: float) -> tuple[int, int]:
    min_lon, min_lat, max_lon, max_lat = bbox
    width = arr.shape[1]
    height = arr.shape[0]
    x = int(round((lon - min_lon) / max(max_lon - min_lon, 1e-12) * (width - 1)))
    y = int(round((1.0 - (lat - min_lat) / max(max_lat - min_lat, 1e-12)) * (height - 1)))
    x = max(1, min(width - 2, x))
    y = max(1, min(height - 2, y))
    return x, y


def _window(arr: np.ndarray, x: int, y: int, radius: int) -> np.ndarray:
    height, width = arr.shape
    return arr[max(0, y - radius) : min(height, y + radius + 1), max(0, x - radius) : min(width, x + radius + 1)]


def _normalized_edge_proximity(lon: float, lat: float, geom_bbox: tuple[float, float, float, float]) -> float:
    min_lon, min_lat, max_lon, max_lat = geom_bbox
    width = max(max_lon - min_lon, 1e-12)
    height = max(max_lat - min_lat, 1e-12)
    x_edge = min(lon - min_lon, max_lon - lon) / width
    y_edge = min(lat - min_lat, max_lat - lat) / height
    return float(max(0.0, min(0.5, min(x_edge, y_edge))))


def _radial_isolation_metrics(arr: np.ndarray, x: int, y: int, center_elev: float, max_radius: int = 18, directions: int = 16) -> dict:
    height, width = arr.shape
    max_radius = max(6, min(max_radius, max(6, min(height, width) // 3)))
    directional_drops: list[float] = []
    early_drops: list[float] = []
    severe_dirs = 0
    sharp_dirs = 0
    escape_dirs = 0

    for idx in range(directions):
        angle = (2.0 * math.pi * idx) / directions
        coords: list[tuple[int, int]] = []
        for radius in range(2, max_radius + 1):
            sx = int(round(x + math.cos(angle) * radius))
            sy = int(round(y + math.sin(angle) * radius))
            sx = max(0, min(width - 1, sx))
            sy = max(0, min(height - 1, sy))
            if not coords or coords[-1] != (sx, sy):
                coords.append((sx, sy))
        if not coords:
            continue

        values = np.array([float(arr[sy, sx]) for sx, sy in coords], dtype=np.float32)
        full_drop = float(center_elev - np.min(values))
        early_span = max(3, min(len(values), max_radius // 3))
        early_drop = float(center_elev - np.min(values[:early_span]))
        directional_drops.append(full_drop)
        early_drops.append(early_drop)
        if full_drop >= 28.0:
            severe_dirs += 1
        if early_drop >= 16.0:
            sharp_dirs += 1
        if full_drop <= 24.0:
            escape_dirs += 1

    if not directional_drops:
        return {
            "max_drop": 0.0,
            "min_drop": 0.0,
            "mean_drop": 0.0,
            "severe_fraction": 0.0,
            "sharp_fraction": 0.0,
            "escape_fraction": 0.0,
        }

    return {
        "max_drop": float(max(directional_drops)),
        "min_drop": float(min(directional_drops)),
        "mean_drop": float(sum(directional_drops) / len(directional_drops)),
        "severe_fraction": float(severe_dirs / len(directional_drops)),
        "sharp_fraction": float(sharp_dirs / len(directional_drops)),
        "escape_fraction": float(escape_dirs / len(directional_drops)),
    }


def _terrain_reasoning(
    arr: np.ndarray,
    bbox: list[float],
    lon: float,
    lat: float,
    sample: dict,
    slope_bias: str,
    elev_norm: float,
    geom_bbox: tuple[float, float, float, float],
    source_name: str,
    legal_class: str,
) -> dict:
    x, y = _sample_indices(arr, bbox, lon, lat)
    core = _window(arr, x, y, 2)
    broad = _window(arr, x, y, 6)
    local_mean = float(np.mean(core))
    broad_mean = float(np.mean(broad))
    ridge_signal = float(sample["elevation_m"] - broad_mean)
    local_relief = float(sample["local_relief"])
    slope_value = float(sample["slope"])
    flatness_ratio = float(max(0.0, 1.0 - (slope_value / max(local_relief * 0.22, 1.25))))
    edge_proximity = _normalized_edge_proximity(lon, lat, geom_bbox)

    directional_windows = {
        "n": arr[max(0, y - 7):max(0, y - 3), max(0, x - 1):min(arr.shape[1], x + 2)],
        "s": arr[min(arr.shape[0], y + 3):min(arr.shape[0], y + 7), max(0, x - 1):min(arr.shape[1], x + 2)],
        "e": arr[max(0, y - 1):min(arr.shape[0], y + 2), min(arr.shape[1], x + 3):min(arr.shape[1], x + 7)],
        "w": arr[max(0, y - 1):min(arr.shape[0], y + 2), max(0, x - 7):max(0, x - 3)],
        "ne": arr[max(0, y - 6):max(0, y - 2), min(arr.shape[1], x + 2):min(arr.shape[1], x + 6)],
        "nw": arr[max(0, y - 6):max(0, y - 2), max(0, x - 6):max(0, x - 2)],
        "se": arr[min(arr.shape[0], y + 2):min(arr.shape[0], y + 6), min(arr.shape[1], x + 2):min(arr.shape[1], x + 6)],
        "sw": arr[min(arr.shape[0], y + 2):min(arr.shape[0], y + 6), max(0, x - 6):max(0, x - 2)],
    }
    directional_delta = {
        key: float(local_mean - np.mean(win)) if win.size else 0.0
        for key, win in directional_windows.items()
    }
    lower_dirs = [key for key, delta in directional_delta.items() if delta >= max(1.6, local_relief * 0.045)]
    higher_dirs = [key for key, delta in directional_delta.items() if delta <= -max(1.6, local_relief * 0.045)]
    low_cardinals = sum(1 for key in ["n", "s", "e", "w"] if key in lower_dirs)
    high_cardinals = sum(1 for key in ["n", "s", "e", "w"] if key in higher_dirs)

    bench_like = slope_bias in {"bench", "shoulder"} and flatness_ratio >= 0.44
    ridge_like = ridge_signal >= max(2.0, local_relief * 0.10) and elev_norm >= 0.52
    intercept_like = local_relief >= 8.0 and slope_bias in {"bench", "shoulder"}
    bedding_like = bench_like and elev_norm >= 0.42
    slope_shelter_like = slope_bias == "steeper side-slope" and local_relief >= 10.0
    shoulder_like = slope_bias == "shoulder" and low_cardinals >= 2 and high_cardinals >= 1
    funnel_like = (ridge_like or shoulder_like) and low_cardinals >= 2 and len(lower_dirs) >= 3
    convergence_like = bench_like and low_cardinals >= 3 and len(higher_dirs) >= 1
    interior_secure = edge_proximity >= 0.22
    edge_risk = edge_proximity <= 0.12

    tag_scores: dict[str, float] = {}

    def add_tag(tag: str, value: float) -> None:
        if value > 0.0:
            tag_scores[tag] = max(tag_scores.get(tag, 0.0), value)

    add_tag("Core Convergence", 6.2 if convergence_like else 0.0)
    add_tag("Ridge Funnel", 5.9 if funnel_like else 0.0)
    add_tag("Shoulder Travel Lane", 5.5 if shoulder_like else 0.0)
    add_tag("Bench Bedding Edge", 5.4 if bedding_like else 0.0)
    add_tag("Travel Intercept", 4.6 if intercept_like else 0.0)
    add_tag("Slope Shelter", 3.8 if slope_shelter_like else 0.0)
    add_tag("Interior Security", 3.6 if interior_secure else 0.0)
    add_tag("Edge Exposure Risk", 3.4 if edge_risk else 0.0)
    add_tag("Legal Interior Access", 2.7 if legal_class == "legal" and interior_secure else 0.0)
    add_tag("Verified Legal Access", 1.4 if legal_class == "legal" and not interior_secure else 0.0)
    if not tag_scores:
        add_tag("Terrain Read", 1.0)

    dominance_replacements = {
        "Bench Bedding Edge": {"Travel Intercept", "Interior Security", "Legal Interior Access"},
        "Core Convergence": {"Travel Intercept", "Interior Security", "Legal Interior Access"},
        "Ridge Funnel": {"Travel Intercept", "Interior Security", "Legal Interior Access"},
        "Shoulder Travel Lane": {"Travel Intercept", "Interior Security", "Legal Interior Access"},
    }
    prioritized_pool = sorted(tag_scores.items(), key=lambda item: (-item[1], item[0]))
    prioritized_tags: list[str] = []
    for tag, _ in prioritized_pool:
        skip = False
        for chosen in prioritized_tags:
            if tag in dominance_replacements.get(chosen, set()):
                skip = True
                break
            if chosen in dominance_replacements.get(tag, set()):
                prioritized_tags.remove(chosen)
                break
        if skip:
            continue
        prioritized_tags.append(tag)

    priority_order = [
        "Core Convergence",
        "Ridge Funnel",
        "Shoulder Travel Lane",
        "Bench Bedding Edge",
        "Travel Intercept",
        "Slope Shelter",
        "Interior Security",
        "Legal Interior Access",
        "Edge Exposure Risk",
        "Verified Legal Access",
        "Terrain Read",
    ]
    unique_tags = []
    for tag in priority_order:
        if tag in prioritized_tags and tag not in unique_tags:
            unique_tags.append(tag)
    for tag in prioritized_tags:
        if tag not in unique_tags:
            unique_tags.append(tag)

    display_tags = unique_tags[:3]
    primary_tag = display_tags[0]
    support_tags = display_tags[1:3]

    height_phrase = "upper third" if elev_norm >= 0.67 else "mid-slope" if elev_norm >= 0.34 else "lower third"
    if ridge_signal >= max(3.5, local_relief * 0.18):
        position_phrase = "slightly above the surrounding pull"
    elif ridge_signal <= -max(3.5, local_relief * 0.18):
        position_phrase = "slightly below the surrounding pull"
    else:
        position_phrase = "level with the surrounding pull"

    terrain_shape_bits: list[str] = []
    if convergence_like:
        terrain_shape_bits.append("multiple side-hill pulls feeding into the same usable shelf")
    if funnel_like:
        terrain_shape_bits.append("upper-ground shape that narrows movement into a smaller lane")
    if shoulder_like:
        terrain_shape_bits.append("a shoulder lane with fall-away on both sides")
    if bench_like and not convergence_like:
        terrain_shape_bits.append("a flatter shelf on the side-hill")
    if slope_shelter_like:
        terrain_shape_bits.append("steeper fall-away that gives cover")
    if not terrain_shape_bits:
        terrain_shape_bits.append("usable terrain shape without a clean named funnel")

    support_text = ", ".join(support_tags) if support_tags else "terrain continuity"
    reason = (
        f"{source_name} stays {legal_class} here; {int(round(sample['elevation_m']))} m on a {height_phrase} {slope_bias}. "
        f"Primary read: {primary_tag}. Support: {support_text}. "
        f"This sit is {position_phrase} with {terrain_shape_bits[0]}, which creates a more believable hunting setup than a flat random point."
    )
    if edge_risk:
        reason += " It sits close to a legal edge, so entry and exit discipline matter."
    elif interior_secure:
        reason += " It also holds better interior security than a boundary-hugging sit."
    elif legal_class == "legal":
        reason += " Clean legal access keeps the recommendation cleaner."

    score_bonus = 0.0
    if primary_tag == "Core Convergence":
        score_bonus += 6.0
    elif primary_tag == "Ridge Funnel":
        score_bonus += 5.2
    elif primary_tag == "Shoulder Travel Lane":
        score_bonus += 4.8
    elif primary_tag == "Bench Bedding Edge":
        score_bonus += 4.2
    elif primary_tag == "Travel Intercept":
        score_bonus += 3.4
    if "Interior Security" in display_tags:
        score_bonus += 1.4
    if "Legal Interior Access" in display_tags:
        score_bonus += 1.8
    elif "Verified Legal Access" in prioritized_tags:
        score_bonus += 1.0
    if edge_risk:
        score_bonus -= 2.8

    confidence_bonus = 0.0
    if primary_tag in {"Core Convergence", "Ridge Funnel", "Bench Bedding Edge"}:
        confidence_bonus += 4.5
    elif primary_tag == "Shoulder Travel Lane":
        confidence_bonus += 3.2
    if "Travel Intercept" in display_tags:
        confidence_bonus += 1.8
    if "Interior Security" in display_tags:
        confidence_bonus += 1.5
    if edge_risk:
        confidence_bonus -= 3.5

    return {
        "primary_tag": primary_tag,
        "support_tags": support_tags,
        "all_tags": display_tags,
        "reasoning": reason,
        "score_bonus": score_bonus,
        "confidence_bonus": confidence_bonus,
        "edge_risk": edge_risk,
        "interior_secure": interior_secure,
        "bench_like": bench_like,
        "ridge_like": ridge_like,
        "intercept_like": intercept_like,
        "bedding_like": bedding_like,
        "shoulder_like": shoulder_like,
        "funnel_like": funnel_like,
        "convergence_like": convergence_like,
        "ridge_signal": ridge_signal,
        "local_relief": local_relief,
    }


def _terrain_validity_read(
    arr: np.ndarray,
    bbox: list[float],
    lon: float,
    lat: float,
    sample: dict,
    legal_class: str,
) -> dict:
    x, y = _sample_indices(arr, bbox, lon, lat)
    core = _window(arr, x, y, 3)
    broad = _window(arr, x, y, 10)

    local_relief = float(sample["local_relief"])
    slope_value = float(sample["slope"])
    broad_relief = float(np.ptp(broad)) if broad.size else local_relief

    rounded = np.round(broad.astype(np.float32), 1) if broad.size else np.array([sample["elevation_m"]], dtype=np.float32)
    flat = rounded.reshape(-1)
    if flat.size:
        _, counts = np.unique(flat, return_counts=True)
        unique_ratio = float(len(counts) / flat.size)
        terrace_strength = float(np.max(counts) / flat.size)
    else:
        unique_ratio = 1.0
        terrace_strength = 0.0

    flat_ground = broad_relief <= 3.0 and slope_value <= 0.9
    blocky_dem = broad_relief >= 12.0 and unique_ratio <= 0.12 and terrace_strength >= 0.18
    weak_relief = broad_relief <= 5.0 and local_relief <= 3.5
    unverified_hunt = legal_class != "legal"

    suppress_positive = flat_ground or blocky_dem
    if unverified_hunt:
        suppress_positive = True

    display_tags: list[str] = []
    if unverified_hunt:
        display_tags.append("Exploration Only")
        display_tags.append("Unverified Hunt Access")
    if flat_ground:
        display_tags.append("Flat Terrain Signal")
    if blocky_dem:
        display_tags.append("Terrain Data Quality Risk")
    elif weak_relief and not unverified_hunt:
        display_tags.append("Weak Terrain Definition")

    reason_bits: list[str] = []
    if unverified_hunt:
        reason_bits.append("Legal hunting access is not verified here")
    if flat_ground:
        reason_bits.append("terrain relief is too flat to treat this like a real hunting setup")
    if blocky_dem:
        reason_bits.append("terrain sampling looks stepped or low-quality, so terrain reads should be treated cautiously")
    elif weak_relief and not unverified_hunt:
        reason_bits.append("terrain definition is weak enough that confidence should stay conservative")

    summary_reason = ""
    if unverified_hunt and flat_ground:
        summary_reason = "Legal hunting access is not verified here, and terrain relief is too flat to support a real hunting recommendation. Keep this in exploration mode."
    elif unverified_hunt and blocky_dem:
        summary_reason = "Legal hunting access is not verified here, and the terrain sampling looks too stepped to trust a sit recommendation. Keep this in exploration mode."
    elif unverified_hunt:
        summary_reason = "Legal hunting access is not verified here, so this should stay in exploration mode until access is confirmed."
    elif flat_ground:
        summary_reason = "Terrain relief is too flat to support a credible hunting sit recommendation."
    elif blocky_dem:
        summary_reason = "Terrain sampling looks stepped or low-quality here, so the sit read should be treated cautiously."
    elif weak_relief:
        summary_reason = "Terrain definition is weak here, so confidence should stay conservative."

    score_penalty = 0.0
    confidence_penalty = 0.0
    if unverified_hunt:
        score_penalty += 14.0
        confidence_penalty += 18.0
    if flat_ground:
        score_penalty += 16.0
        confidence_penalty += 22.0
    if blocky_dem:
        score_penalty += 12.0
        confidence_penalty += 16.0
    elif weak_relief and not unverified_hunt:
        score_penalty += 4.0
        confidence_penalty += 6.0

    cleaned_tags: list[str] = []
    for tag in display_tags:
        if tag not in cleaned_tags:
            cleaned_tags.append(tag)

    return {
        "display_tags": cleaned_tags[:3],
        "reason_bits": reason_bits,
        "summary_reason": summary_reason,
        "suppress_positive": suppress_positive,
        "score_penalty": score_penalty,
        "confidence_penalty": confidence_penalty,
        "flat_ground": flat_ground,
        "blocky_dem": blocky_dem,
        "weak_relief": weak_relief,
        "unverified_hunt": unverified_hunt,
    }


def _practical_access_read(
    arr: np.ndarray,
    bbox: list[float],
    lon: float,
    lat: float,
    sample: dict,
    elev_norm: float,
    geom_bbox: tuple[float, float, float, float],
    legal_class: str,
) -> dict:
    x, y = _sample_indices(arr, bbox, lon, lat)
    broad = _window(arr, x, y, 12)
    wide = _window(arr, x, y, 18)
    broad_relief = float(np.ptp(broad)) if broad.size else float(sample["local_relief"])
    wide_relief = float(np.ptp(wide)) if wide.size else broad_relief
    broad_mean = float(np.mean(broad)) if broad.size else float(sample["elevation_m"])
    broad_std = float(np.std(broad)) if broad.size else 0.0

    gy, gx = np.gradient(broad.astype(np.float32)) if broad.size else (
        np.zeros((1, 1), dtype=np.float32),
        np.zeros((1, 1), dtype=np.float32),
    )
    slope_energy = float(np.mean(np.hypot(gx, gy))) if broad.size else 0.0
    steep_fraction = float(np.mean(np.hypot(gx, gy) >= max(4.0, slope_energy * 1.2))) if broad.size else 0.0

    ridge_signal = float(sample["elevation_m"] - broad_mean)
    edge_proximity = _normalized_edge_proximity(lon, lat, geom_bbox)
    radial = _radial_isolation_metrics(arr, x, y, float(sample["elevation_m"]))

    high_elevation = elev_norm >= 0.82
    upper_third = elev_norm >= 0.68
    isolated_high_point = ridge_signal >= max(10.0, broad_relief * 0.22)
    peak_position_risk = high_elevation and isolated_high_point and broad_relief >= 20.0
    rugged_access = (wide_relief >= 28.0 and steep_fraction >= 0.24) or (broad_relief >= 24.0 and slope_energy >= 5.0)

    severe_ring_drop = radial["mean_drop"] >= max(24.0, broad_relief * 0.55) and radial["severe_fraction"] >= 0.56
    sharp_ring_drop = radial["sharp_fraction"] >= 0.42 and radial["max_drop"] >= max(30.0, wide_relief * 0.6)
    connected_escape = radial["escape_fraction"] >= 0.18 or radial["min_drop"] <= 24.0
    weak_escape = radial["escape_fraction"] < 0.22 and radial["min_drop"] >= 26.0
    isolated_landform = (
        legal_class == "legal"
        and not connected_escape
        and severe_ring_drop
        and sharp_ring_drop
        and radial["min_drop"] >= max(40.0, broad_relief * 0.10)
        and broad_std <= max(18.0, wide_relief * 0.45)
    )
    cliff_isolation_risk = isolated_landform and (edge_proximity <= 0.28 or high_elevation or ridge_signal >= 12.0)

    summit_cap_risk = legal_class == "legal" and upper_third and weak_escape and (
        (ridge_signal >= max(10.0, broad_relief * 0.16) and radial["severe_fraction"] >= 0.44 and radial["sharp_fraction"] >= 0.24)
        or (peak_position_risk and radial["sharp_fraction"] >= 0.24 and radial["min_drop"] >= max(28.0, broad_relief * 0.07))
        or (high_elevation and radial["mean_drop"] >= max(18.0, broad_relief * 0.42) and steep_fraction >= 0.15)
    )
    low_connected_terrain = (
        (radial["severe_fraction"] >= 0.38 and weak_escape)
        or (radial["sharp_fraction"] >= 0.28 and radial["min_drop"] >= 26.0)
        or steep_fraction >= 0.26
    )

    high_effort_access = legal_class == "legal" and (
        cliff_isolation_risk
        or summit_cap_risk
        or ((peak_position_risk and rugged_access) or (high_elevation and wide_relief >= 30.0))
    )
    limited_practical_access = high_effort_access and (
        cliff_isolation_risk
        or summit_cap_risk
        or edge_proximity <= 0.18
        or steep_fraction >= 0.28
        or broad_std >= 11.0
        or low_connected_terrain
    )

    hard_override = legal_class == "legal" and (
        cliff_isolation_risk
        or isolated_landform
        or (summit_cap_risk and limited_practical_access)
        or (
            upper_third
            and weak_escape
            and low_connected_terrain
            and radial["mean_drop"] >= max(18.0, broad_relief * 0.38)
            and ridge_signal >= max(8.0, broad_relief * 0.12)
            and radial["severe_fraction"] >= 0.50
            and radial["sharp_fraction"] >= 0.30
            and steep_fraction >= 0.18
        )
        or (peak_position_risk and low_connected_terrain and upper_third)
    )

    tag_scores: dict[str, float] = {}
    if cliff_isolation_risk:
        tag_scores["Cliff Isolation Risk"] = 7.2
    if isolated_landform:
        tag_scores["Isolated Landform"] = 6.7
    if summit_cap_risk and not cliff_isolation_risk:
        tag_scores["Peak Position Risk"] = 6.1
    if limited_practical_access:
        tag_scores["Limited Practical Access"] = 6.0 if hard_override else 4.8
    if high_effort_access:
        tag_scores["High Effort Access"] = 5.5 if hard_override else 4.8
    if peak_position_risk:
        tag_scores["Peak Position Risk"] = max(tag_scores.get("Peak Position Risk", 0.0), 5.4)
    if rugged_access:
        tag_scores["Rugged Terrain Access"] = 4.0

    display_tags = [tag for tag, _ in sorted(tag_scores.items(), key=lambda item: (-item[1], item[0]))][:3]

    reason_bits: list[str] = []
    if isolated_landform:
        reason_bits.append(
            "the sit rides on a top that stays elevated above most surrounding directions, which makes the whole landform feel isolated rather than normally huntable"
        )
    if cliff_isolation_risk:
        reason_bits.append(
            "the surrounding drop is severe enough in multiple directions that this behaves more like a cliff-isolated cap than a normal bench"
        )
    if summit_cap_risk and not cliff_isolation_risk:
        reason_bits.append(
            "the point sits high on the landform with enough fall-away around it that a locally calm patch should not be trusted like a normal travel system"
        )
    if peak_position_risk:
        reason_bits.append("the sit rides high enough on the landform that peak exposure becomes part of the hunt problem")
    if high_effort_access:
        reason_bits.append("the climb and elevation isolation make this harder to hunt practically than the local terrain read alone suggests")
    if rugged_access:
        reason_bits.append("surrounding relief is rugged enough that approach effort stays high")
    if limited_practical_access:
        reason_bits.append("access looks limited enough that this may hunt well on paper but poorly in the real world")

    score_penalty = 0.0
    confidence_penalty = 0.0
    if isolated_landform:
        score_penalty += 10.0
        confidence_penalty += 12.0
    if cliff_isolation_risk:
        score_penalty += 14.0
        confidence_penalty += 18.0
    if summit_cap_risk:
        score_penalty += 10.0
        confidence_penalty += 12.0
    if peak_position_risk:
        score_penalty += 6.0
        confidence_penalty += 7.0
    if rugged_access:
        score_penalty += 3.0
        confidence_penalty += 3.0
    if high_effort_access:
        score_penalty += 7.0
        confidence_penalty += 9.0
    if limited_practical_access:
        score_penalty += 6.0
        confidence_penalty += 7.0
    if hard_override:
        score_penalty += 18.0
        confidence_penalty += 16.0

    summary_reason = ""
    if cliff_isolation_risk:
        summary_reason = (
            "This point sits on an isolated cap with severe drop around it, so even if the top reads calm the setup should be treated as a poor practical hunt option rather than a trustworthy default sit."
        )
    elif hard_override:
        summary_reason = (
            "This point sits too high and too isolated on the landform to trust as a default sit, so it should rank behind more connected terrain if any cleaner option exists inside the box."
        )
    elif limited_practical_access:
        summary_reason = (
            "This terrain may read well on the map, but practical access looks limited enough that it should be treated as a higher-effort hunt rather than an easy default sit."
        )
    elif high_effort_access:
        summary_reason = (
            "This sit has usable terrain, but the elevation isolation and surrounding ruggedness make it a higher-effort hunt than the local shelf read alone suggests."
        )
    elif peak_position_risk:
        summary_reason = "This point sits high enough on the landform that peak exposure risk should temper confidence."

    override_primary = ""
    if cliff_isolation_risk:
        override_primary = "Cliff Isolation Risk"
    elif isolated_landform or hard_override:
        override_primary = "Isolated Landform"

    return {
        "display_tags": display_tags,
        "reason_bits": reason_bits,
        "summary_reason": summary_reason,
        "score_penalty": score_penalty,
        "confidence_penalty": confidence_penalty,
        "peak_position_risk": peak_position_risk,
        "high_effort_access": high_effort_access,
        "rugged_access": rugged_access,
        "limited_practical_access": limited_practical_access,
        "isolated_landform": isolated_landform,
        "cliff_isolation_risk": cliff_isolation_risk,
        "summit_cap_risk": summit_cap_risk,
        "low_connected_terrain": low_connected_terrain,
        "hard_override": hard_override,
        "identity_block": hard_override or cliff_isolation_risk or summit_cap_risk,
        "score_cap": 64 if hard_override else 999,
        "confidence_cap": 60 if hard_override else 999,
        "override_primary": override_primary,
    }


def _merge_display_tags(base_tags: list[str], extra_tags: list[str], limit: int = 3) -> list[str]:
    merged: list[str] = []
    for tag in [*(base_tags or []), *(extra_tags or [])]:
        if tag and tag not in merged:
            merged.append(tag)
    return merged[:limit]

def _apply_vegetation_influence(
    vegetation_profile: dict,
    terrain_read: dict,
    travel_score: float,
    bedding_score: float,
    feeding_score: float,
    score: float,
    confidence: float,
) -> tuple[float, float, float, float, float, list[str]]:
    vegetation = str(vegetation_profile.get("classification") or "unknown")
    tags = list(vegetation_profile.get("tags") or [])

    if vegetation == "forest":
        if terrain_read.get("bedding_like"):
            bedding_score += 4.0
            score += 3.0
            confidence += 2.5
        if terrain_read.get("interior_secure"):
            travel_score += 2.0
            score += 1.5
    elif vegetation == "shrub":
        if terrain_read.get("bedding_like"):
            bedding_score += 2.0
            score += 1.5
        if terrain_read.get("intercept_like") or terrain_read.get("shoulder_like"):
            travel_score += 1.5
    elif vegetation == "open":
        if terrain_read.get("bedding_like"):
            bedding_score -= 8.0
            score -= 6.0
            confidence -= 6.0
        if not terrain_read.get("interior_secure"):
            travel_score -= 2.0
            score -= 3.0
            confidence -= 2.5
    elif vegetation == "water":
        if terrain_read.get("bedding_like") or terrain_read.get("interior_secure"):
            bedding_score -= 4.0
            score -= 4.0
            confidence -= 3.0

    return travel_score, bedding_score, feeding_score, score, confidence, tags


def _wind_from_aspect(aspect_deg: float) -> str:
    labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int(((aspect_deg + 22.5) % 360.0) // 45.0)
    down_slope = labels[idx]
    opposite = {
        "N": "S",
        "NE": "SW",
        "E": "W",
        "SE": "NW",
        "S": "N",
        "SW": "NE",
        "W": "E",
        "NW": "SE",
    }
    return opposite.get(down_slope, "NW")


def _candidate_offsets() -> list[tuple[float, float, float]]:
    return [
        (0.50, 0.52, 1.00),
        (0.35, 0.58, 0.96),
        (0.65, 0.46, 0.93),
        (0.28, 0.38, 0.89),
        (0.72, 0.66, 0.86),
        (0.55, 0.30, 0.83),
    ]


def _timing_label(travel_score: float, bedding_score: float, feeding_score: float) -> tuple[str, str]:
    if feeding_score >= bedding_score and feeding_score >= travel_score:
        return "Evening destination window", "2.5 hours before sunset through last light"
    if bedding_score >= feeding_score and bedding_score >= travel_score:
        return "Morning edge window", "First light through mid-morning"
    return "Travel corridor window", "First light or last two hours before sunset"


def _readiness_label(score: float, confidence: float, wind_fit: bool | None) -> str:
    if score >= 84 and confidence >= 74 and wind_fit is True:
        return "Strike Ready"
    if score >= 76 and confidence >= 65:
        return "Huntable"
    if score >= 68:
        return "Conditional"
    return "Scout First"


def _comparison_gap_label(primary: dict, challenger: dict) -> str:
    if not challenger:
        return "uncontested"
    score_gap = int(primary.get("score", 0)) - int(challenger.get("score", 0))
    confidence_gap = int(primary.get("confidence", 0)) - int(challenger.get("confidence", 0))
    combined = score_gap + max(0, confidence_gap // 2)
    if combined >= 12:
        return "clear"
    if combined >= 6:
        return "solid"
    return "narrow"


def _competitive_edge(primary: dict, challenger: dict) -> str:
    if not challenger:
        return "No comparable legal backup is close enough to pressure this sit."

    reasons: list[str] = []
    if int(primary.get("bedding_score", 0)) >= int(challenger.get("bedding_score", 0)) + 4:
        reasons.append("stronger bedding security")
    if int(primary.get("travel_score", 0)) >= int(challenger.get("travel_score", 0)) + 4:
        reasons.append("cleaner travel compression")
    if bool(primary.get("interior_secure")) and not bool(challenger.get("interior_secure")):
        reasons.append("better interior legal margin")
    if not bool(primary.get("edge_risk")) and bool(challenger.get("edge_risk")):
        reasons.append("less edge exposure")
    if bool(primary.get("wind_fit")) and not bool(challenger.get("wind_fit")):
        reasons.append("better wind fit")
    if not bool(primary.get("limited_practical_access") or primary.get("high_effort_access")) and bool(challenger.get("limited_practical_access") or challenger.get("high_effort_access")):
        reasons.append("cleaner practical access")
    if int(primary.get("confidence", 0)) >= int(challenger.get("confidence", 0)) + 6 and not reasons:
        reasons.append("higher terrain trust")

    if not reasons:
        reasons.append("slightly cleaner total terrain fit")

    gap = _comparison_gap_label(primary, challenger)
    if len(reasons) == 1:
        return f"Competitive read: this is a {gap} win over the nearest backup because it carries {reasons[0]}."
    lead = ", ".join(reasons[:-1]) + f", and {reasons[-1]}"
    return f"Competitive read: this is a {gap} win over the nearest backup because it carries {lead}."


def _conditional_outlook(primary: dict, challenger: dict, requested_wind: str) -> str:
    risks: list[str] = []
    if requested_wind and primary.get("wind_fit") is False:
        risks.append("the current wind is already working against the preferred guard")
    if bool(primary.get("edge_risk")):
        risks.append("edge pressure rises on entry or exit")
    if bool(primary.get("limited_practical_access") or primary.get("high_effort_access")):
        risks.append("real-world access turns harder than the map read suggests")
    if challenger and int(challenger.get("travel_score", 0)) >= int(primary.get("travel_score", 0)) + 4:
        risks.append("movement loads harder into the backup lane than this shelf")
    if challenger and int(challenger.get("bedding_score", 0)) >= int(primary.get("bedding_score", 0)) + 4:
        risks.append("bedding pressure settles deeper toward the backup option")

    if not risks:
        return "Conditional read: this should stay on top unless wind, entry pressure, or animal use shifts away from the current shelf."
    return "Conditional read: this stays viable unless " + risks[0] + "."


def _forced_primary_visibility(primary: dict, challenger: dict, requested_wind: str) -> str:
    pressure = _comparison_gap_label(primary, challenger).title()

    break_reason = "wind, edge pressure, or animal use shifts away from the current shelf"
    if requested_wind and primary.get("wind_fit") is False:
        break_reason = "the current wind is already working against the preferred guard"
    elif bool(primary.get("edge_risk")):
        break_reason = "edge pressure rises on entry or exit"
    elif bool(primary.get("limited_practical_access") or primary.get("high_effort_access")):
        break_reason = "real-world access turns harder than the map read suggests"
    elif challenger and int(challenger.get("travel_score", 0)) >= int(primary.get("travel_score", 0)) + 4:
        break_reason = "movement loads harder into the backup lane than this shelf"
    elif challenger and int(challenger.get("bedding_score", 0)) >= int(primary.get("bedding_score", 0)) + 4:
        break_reason = "bedding pressure settles deeper toward the backup option"

    return f"Win strength: {pressure}. Breaks if: {break_reason}."


def _rank_pressure_summary(item: dict, stronger: dict | None) -> str:
    if not stronger:
        return "Top-ranked sit in this box."
    reasons: list[str] = []
    if int(item.get("score", 0)) <= int(stronger.get("score", 0)) - 8:
        reasons.append("trails on total score")
    if int(item.get("confidence", 0)) <= int(stronger.get("confidence", 0)) - 6:
        reasons.append("carries less terrain trust")
    if int(item.get("bedding_score", 0)) <= int(stronger.get("bedding_score", 0)) - 4:
        reasons.append("gives up bedding security")
    if int(item.get("travel_score", 0)) <= int(stronger.get("travel_score", 0)) - 4:
        reasons.append("gives up movement compression")
    if bool(item.get("edge_risk")) and not bool(stronger.get("edge_risk")):
        reasons.append("leans closer to edge exposure")
    if bool(item.get("limited_practical_access") or item.get("high_effort_access")) and not bool(stronger.get("limited_practical_access") or stronger.get("high_effort_access")):
        reasons.append("asks more from access")
    if not reasons:
        reasons.append("sits just behind the stronger lane")
    gap = _comparison_gap_label(stronger, item)
    return f"{gap.title()} pressure behind the next stronger sit: {reasons[0]}."


def _derive_primary_trust_tags(primary_record: dict, alternatives: list[dict], requested_wind: str) -> list[str]:
    tags: list[str] = []

    terrain_tag = _select_trust_terrain_tag(primary_record)
    if terrain_tag:
        tags.append(terrain_tag)

    modifier_tag = _select_trust_modifier_tag(primary_record, alternatives, requested_wind)
    if modifier_tag and modifier_tag not in tags:
        tags.append(modifier_tag)

    caution_tag = _select_trust_caution_tag(primary_record, alternatives, requested_wind)
    if caution_tag and caution_tag not in tags and len(tags) < 3:
        tags.append(caution_tag)

    vegetation_tag = str(primary_record.get("vegetation_trust_tag") or "").strip()
    if vegetation_tag and vegetation_tag not in tags and len(tags) < 3:
        tags.append(vegetation_tag)

    return tags[:3]


def _select_trust_terrain_tag(primary_record: dict) -> str:
    primary = str(primary_record.get("primary_tag") or "").strip()
    mapping = {
        "Bench Bedding Edge": "Bench Travel",
        "Core Convergence": "Compressed Movement",
        "Ridge Funnel": "Compressed Movement",
        "Shoulder Travel Lane": "Compressed Movement",
        "Travel Intercept": "Compressed Movement",
        "Slope Shelter": "Transition Edge",
    }
    if primary in mapping:
        return mapping[primary]
    if primary and primary not in {
        "Exploration Only",
        "Terrain Read",
        "Interior Security",
        "Legal Interior Access",
        "Verified Legal Access",
    }:
        return "Transition Edge"
    if primary_record.get("bench_like"):
        return "Bench Travel"
    if primary_record.get("convergence_like") or primary_record.get("funnel_like") or primary_record.get("shoulder_like") or primary_record.get("intercept_like"):
        return "Compressed Movement"
    return "Transition Edge"


def _select_trust_modifier_tag(primary_record: dict, alternatives: list[dict], requested_wind: str) -> str | None:
    alt_best = alternatives[0] if alternatives else {}
    alt_access_risk = bool(
        alt_best.get("limited_practical_access")
        or alt_best.get("high_effort_access")
        or alt_best.get("hard_override")
    )
    primary_access_clean = not bool(
        primary_record.get("limited_practical_access")
        or primary_record.get("high_effort_access")
        or primary_record.get("hard_override")
    )

    if primary_access_clean and alt_access_risk:
        return "Clean Entry"

    if requested_wind and primary_record.get("wind_fit") is True:
        return "Wind-Fit Sit"

    if primary_record.get("legality_status") == "legal" and primary_record.get("interior_secure") and not primary_record.get("edge_risk"):
        return "Full Legal Setup"

    return None


def _select_trust_caution_tag(primary_record: dict, alternatives: list[dict], requested_wind: str) -> str | None:
    if requested_wind and primary_record.get("wind_fit") is False:
        return "Wind Sensitive"

    if primary_record.get("limited_practical_access") or primary_record.get("high_effort_access"):
        return "Access Risk"

    if primary_record.get("edge_risk"):
        return "Tight Legal Margin"

    return None


def build_decision_artifact(
    terrain_truth_root: Path,
    bbox: list[float],
    out_path: Path,
    operator_context: dict | None = None,
) -> DecisionArtifact:
    operator_context = operator_context or {}
    requested_wind = str(operator_context.get("wind_direction") or "").strip().upper()
    vegetation_profile = _vegetation_profile(operator_context)
    species_profile = _species_profile_for_run(operator_context, bbox)

    bbox_obj = BBox(*bbox)
    bbox_obj = _sanity_gate(bbox_obj)
    dem_path = _resolve_dem_path(terrain_truth_root)
    legal_geojson_path = terrain_truth_root / "legal" / "legal_surface.geojson"
    dem = _sanitize_dem(_load_dem(dem_path))
    geo = json.loads(legal_geojson_path.read_text(encoding="utf-8"))
    raw_features = geo.get("features", [])
    features = []
    for feat in raw_features:
        geom = feat.get("geometry") or {}
        clipped_geom = _clip_geometry_to_bbox(geom, bbox_obj)
        if not clipped_geom:
            continue
        features.append({**feat, "geometry": clipped_geom})
    legal_features = _legality_gate(features)
    dem_min = float(np.min(dem))
    dem_range = max(float(np.ptp(dem)), 1.0)

    contract_notes = []
    contract_path = terrain_truth_root / "terrain_contract.json"
    if contract_path.exists():
        try:
            contract_data = json.loads(contract_path.read_text(encoding="utf-8"))
            contract_notes = contract_data.get("notes", [])
        except Exception:
            contract_notes = []

    legal_candidates: list[dict] = []
    suppressed_candidates: list[dict] = []

    for feat in legal_features:
        props = dict(feat.get("properties") or {})
        geom = feat.get("geometry") or {}
        legal_class = str(props.get("monahinga_legal_class", "unknown")).lower()
        name = _feature_name(props)
        min_lon, min_lat, max_lon, max_lat = _feature_bbox(geom)
        area_hint = float(props.get("GIS_AcrsDb", props.get("GIS_Acres", 1.0)) or 1.0)

        for idx, (fx, fy, weight) in enumerate(_candidate_offsets(), start=1):
            lon = min_lon + (max_lon - min_lon) * fx
            lat = min_lat + (max_lat - min_lat) * fy
            if not bbox_obj.contains(lon, lat):
                continue
            if not _feature_contains(lon, lat, geom):
                continue

            sample = _sample_dem(dem, bbox, lon, lat)
            slope_bias = _quantize_slope(sample["slope"])
            elev_norm = max(0.0, min(1.0, (sample["elevation_m"] - dem_min) / dem_range))

            travel_score = 44.0 + sample["local_relief"] * 0.25 + (8.0 if slope_bias == "shoulder" else 3.0)
            bedding_score = 42.0 + (10.0 if slope_bias in {"bench", "shoulder"} else 2.0) + elev_norm * 18.0
            feeding_score = 40.0 + max(0.0, (1.0 - elev_norm)) * 16.0 + area_hint * 0.01
            terrain_score = elev_norm * 22.0 + sample["local_relief"] * 0.18
            shape_bonus = max(0.0, min(10.0, math.log(max(area_hint, 1.0), 1.5) - 10.0))
            score = 50.0 + terrain_score + shape_bonus + weight * 6.0 + travel_score * 0.10 + bedding_score * 0.08

            preferred_wind = _wind_from_aspect(sample["aspect_deg"])
            wind_fit = None
            if requested_wind:
                wind_fit = requested_wind == preferred_wind
                score += 8.0 if wind_fit else -25.0

            terrain_read = _terrain_reasoning(
                dem,
                bbox,
                lon,
                lat,
                sample,
                slope_bias,
                elev_norm,
                (min_lon, min_lat, max_lon, max_lat),
                name,
                legal_class,
            )

            cover_bonus = 0.0
            feed_bonus = 0.0

            if terrain_read.get("convergence_like") or terrain_read.get("funnel_like") or terrain_read.get("shoulder_like"):
                cover_bonus += 6.0
            if terrain_read.get("interior_secure") and not terrain_read.get("edge_risk"):
                cover_bonus += 3.0

            if terrain_read.get("bench_like") or terrain_read.get("edge_risk"):
                feed_bonus += 5.0
            if elev_norm <= 0.40:
                feed_bonus += 4.0

            travel_score += cover_bonus
            feeding_score += feed_bonus
            score += cover_bonus * 0.85 + feed_bonus * 0.65

            validity_read = _terrain_validity_read(dem, bbox, lon, lat, sample, legal_class)
            practical_read = _practical_access_read(
                dem,
                bbox,
                lon,
                lat,
                sample,
                elev_norm,
                (min_lon, min_lat, max_lon, max_lat),
                legal_class,
            )
            if not practical_read.get("identity_block"):
                if terrain_read["ridge_like"] or terrain_read["intercept_like"]:
                    travel_score += 6.0
                if terrain_read.get("shoulder_like"):
                    travel_score += 4.0
                if terrain_read.get("funnel_like") or terrain_read.get("convergence_like"):
                    travel_score += 5.0
                if terrain_read["bedding_like"]:
                    bedding_score += 6.0
                if terrain_read.get("interior_secure"):
                    bedding_score += 2.0
            if terrain_read["edge_risk"]:
                travel_score -= 2.0
                bedding_score -= 3.0

            travel_score += vegetation_profile["travel_delta"]
            bedding_score += vegetation_profile["bedding_delta"]
            feeding_score += vegetation_profile["feeding_delta"]

            travel_score, bedding_score, feeding_score, score, vegetation_confidence_delta, vegetation_tags = _apply_vegetation_influence(
                vegetation_profile,
                terrain_read,
                travel_score,
                bedding_score,
                feeding_score,
                score,
                0.0,
            )

            feature_flags = _terrain_feature_flags(terrain_read, vegetation_profile["classification"])

            legal_score_delta, legal_confidence_delta = _legal_confidence_weight(
                bool(terrain_read.get("interior_secure")),
                bool(terrain_read.get("edge_risk")),
            )
            boundary_score_delta, boundary_confidence_delta, boundary_tag = _boundary_hunt_weight(
                bool(terrain_read.get("edge_risk")),
                terrain_read,
            )
            wildlife_score_delta, wildlife_confidence_delta, wildlife_travel_delta, wildlife_bedding_delta, wildlife_tag = _wildlife_micro_signal(
                terrain_truth_root,
                terrain_read,
            )
            wind_behavior_score_delta, wind_behavior_travel_delta, wind_behavior_bedding_delta, wind_behavior_confidence_delta, wind_behavior_tag = _wind_behavior_override(
                requested_wind,
                preferred_wind,
                terrain_read,
            )
            provider_score_delta, provider_conf_delta, provider_reasons = _provider_penalty_from_notes(contract_notes)

            travel_score += wildlife_travel_delta + wind_behavior_travel_delta
            bedding_score += wildlife_bedding_delta + wind_behavior_bedding_delta
            score += legal_score_delta + boundary_score_delta + wildlife_score_delta + wind_behavior_score_delta
            score += provider_score_delta
            score += vegetation_profile["score_delta"]

            if not practical_read.get("identity_block"):
                score += terrain_read["score_bonus"]

            if validity_read["suppress_positive"]:
                travel_score = min(travel_score, 46.0)
                bedding_score = min(bedding_score, 45.0)
                feeding_score = min(feeding_score, 44.0)
            elif practical_read.get("hard_override"):
                travel_score = min(travel_score, 54.0)
                bedding_score = min(bedding_score, 50.0)
                feeding_score = min(feeding_score, 48.0)
                terrain_read["score_bonus"] = min(terrain_read["score_bonus"], 0.0)
                terrain_read["confidence_bonus"] = min(terrain_read["confidence_bonus"], 0.0)
            score -= validity_read["score_penalty"]
            score -= practical_read["score_penalty"]
            best_label, best_window = _timing_label(travel_score, bedding_score, feeding_score)
            confidence = max(
                32.0 if validity_read["suppress_positive"] else 44.0,
                min(
                    92.0,
                    56.0
                    + terrain_score * 0.45
                    + shape_bonus * 1.3
                    + terrain_read["confidence_bonus"]
                    + legal_confidence_delta
                    + boundary_confidence_delta
                    + wildlife_confidence_delta
                    + wind_behavior_confidence_delta
                    + vegetation_profile["confidence_delta"]
                    + vegetation_confidence_delta
                    + (5.0 if legal_class == "legal" else -10.0)
                    - validity_read["confidence_penalty"]
                    - practical_read["confidence_penalty"]
                    + provider_conf_delta
                ),
            )
            travel_score, bedding_score, feeding_score, score, confidence, species_tags, species_note = _apply_species_tuning(
                species_profile,
                terrain_read,
                sample,
                slope_bias,
                elev_norm,
                vegetation_profile["classification"],
                feature_flags,
                travel_score,
                bedding_score,
                feeding_score,
                score,
                confidence,
            )


            if validity_read["suppress_positive"]:
                if validity_read["display_tags"]:
                    terrain_read["primary_tag"] = validity_read["display_tags"][0]
                    terrain_read["support_tags"] = validity_read["display_tags"][1:3]
                    terrain_read["all_tags"] = validity_read["display_tags"][:3]
                terrain_read["score_bonus"] = 0.0
                terrain_read["confidence_bonus"] = min(terrain_read["confidence_bonus"], 0.0)
            elif practical_read.get("hard_override"):
                terrain_read["primary_tag"] = practical_read["override_primary"] or "Isolated Landform"
                terrain_read["support_tags"] = [
                    tag for tag in practical_read["display_tags"]
                    if tag and tag != terrain_read["primary_tag"]
                ][:2]
                if len(terrain_read["support_tags"]) < 2:
                    for fallback_tag in [
                        "Cliff Isolation Risk",
                        "Limited Practical Access",
                        "Peak Position Risk",
                        "High Effort Access",
                    ]:
                        if fallback_tag != terrain_read["primary_tag"] and fallback_tag not in terrain_read["support_tags"]:
                            terrain_read["support_tags"].append(fallback_tag)
                        if len(terrain_read["support_tags"]) >= 2:
                            break
                terrain_read["all_tags"] = [terrain_read["primary_tag"], *terrain_read["support_tags"]][:3]
                terrain_read["score_bonus"] = 0.0
                terrain_read["confidence_bonus"] = min(terrain_read["confidence_bonus"], 0.0)
                score = min(score, practical_read.get("score_cap", 64.0)) - 8.0
                confidence = min(confidence, practical_read.get("confidence_cap", 60.0))
            elif practical_read.get("override_primary"):
                terrain_read["primary_tag"] = practical_read["override_primary"]
                remaining = [tag for tag in practical_read["display_tags"] if tag != terrain_read["primary_tag"]] + terrain_read["support_tags"]
                terrain_read["all_tags"] = _merge_display_tags([terrain_read["primary_tag"]], remaining)
                terrain_read["support_tags"] = terrain_read["all_tags"][1:3]
            elif practical_read["display_tags"]:
                terrain_read["all_tags"] = _merge_display_tags(
                    [terrain_read["primary_tag"]],
                    practical_read["display_tags"] + terrain_read["support_tags"],
                )
                terrain_read["support_tags"] = terrain_read["all_tags"][1:3]

            terrain_read["all_tags"] = _merge_display_tags(
                [terrain_read["primary_tag"]],
                vegetation_tags + terrain_read["support_tags"],
            )
            terrain_read["support_tags"] = terrain_read["all_tags"][1:3]

            if species_tags:
                terrain_read["all_tags"] = _merge_display_tags(
                    [terrain_read["primary_tag"]],
                    species_tags + terrain_read["support_tags"],
                )
                terrain_read["support_tags"] = terrain_read["all_tags"][1:3]

            if boundary_tag:
                terrain_read["all_tags"] = _merge_display_tags(
                    [terrain_read["primary_tag"]],
                    [boundary_tag] + terrain_read["support_tags"],
                )
                terrain_read["support_tags"] = terrain_read["all_tags"][1:3]

            if wildlife_tag:
                terrain_read["all_tags"] = _merge_display_tags(
                    [terrain_read["primary_tag"]],
                    [wildlife_tag] + terrain_read["support_tags"],
                )
                terrain_read["support_tags"] = terrain_read["all_tags"][1:3]

            if wind_behavior_tag:
                terrain_read["all_tags"] = _merge_display_tags(
                    [terrain_read["primary_tag"]],
                    [wind_behavior_tag] + terrain_read["support_tags"],
                )
                terrain_read["support_tags"] = terrain_read["all_tags"][1:3]

            reasoning = terrain_read["reasoning"]
            feature_readout = _feature_readout_text(feature_flags, species_profile)
            if species_note:
                reasoning += " " + species_note
            if feature_readout:
                reasoning += " " + feature_readout
            if provider_reasons:
                reasoning += " Data reliability note: " + ", ".join(provider_reasons) + "."
            if vegetation_profile["reason"]:
                reasoning += " " + vegetation_profile["reason"]
            if validity_read["suppress_positive"] and validity_read.get("summary_reason"):
                reasoning = validity_read["summary_reason"] + (
                    (" Data reliability note: " + ", ".join(provider_reasons) + ".") if provider_reasons else ""
                )
                if vegetation_profile["reason"]:
                    reasoning += " " + vegetation_profile["reason"]
            else:
                if practical_read.get("summary_reason"):
                    reasoning += " " + practical_read["summary_reason"]
                elif practical_read["reason_bits"]:
                    reasoning += " " + " ".join(bit + "." for bit in practical_read["reason_bits"])
                if validity_read["reason_bits"]:
                    reasoning += " " + " ".join(
                        bit + "." for bit in validity_read["reason_bits"]
                    )
            if boundary_tag == "Boundary Funnel":
                reasoning += " This edge behaves like a boundary funnel, so the legal line may concentrate movement instead of just creating exposure."
            elif boundary_tag == "Boundary Bedding Edge":
                reasoning += " This edge also reads like a bedding boundary, where legal cover meets a cleaner transition line."
            elif boundary_tag == "Boundary Exposure":
                reasoning += " This edge reads more like exposed boundary pressure than a productive legal ambush line."

            if wildlife_tag == "Wildlife Movement Push":
                reasoning += " Wildlife micro-signal: current wind speed adds a small movement push into connected travel terrain."
            elif wildlife_tag == "Wildlife Bedding Hold":
                reasoning += " Wildlife micro-signal: calmer conditions slightly favor secure bedding-style terrain."

            if cover_bonus > 0.0:
                reasoning += " Cover proxy: thicker-feeling travel structure adds security to movement here."
            if feed_bonus > 0.0:
                reasoning += " Feeding proxy: bench-edge and lower-shelf terrain adds a mild destination pull."

            if wind_behavior_tag == "Wind-Driven Movement":
                reasoning += " Wind-behavior override: matching wind sharply upgrades covered travel terrain and can move this sit ahead of calmer structure."
            elif wind_behavior_tag == "Wind-Safe Bedding":
                reasoning += " Wind-behavior override: matching wind stabilizes this secure bedding-style setup."
            elif wind_behavior_tag == "Wind-Blown Travel":
                reasoning += " Wind-behavior override: wrong wind sharply degrades exposed travel use here."
            elif wind_behavior_tag == "Wind-Exposed Bedding":
                reasoning += " Wind-behavior override: wrong wind destabilizes this bedding-style setup."
            elif wind_behavior_tag == "Wind-Misaligned":
                reasoning += " Wind-behavior override: the current wind is mildly misaligned with how this terrain wants to hunt."

            if requested_wind:
                if wind_fit:
                    reasoning += f" Current wind ({requested_wind}) matches the preferred guard."
                else:
                    reasoning += f" Current wind ({requested_wind}) conflicts with the preferred guard ({preferred_wind})."

            record = {
                "lon": float(lon),
                "lat": float(lat),
                "elevation_m": float(sample["elevation_m"]),
                "elevation_norm": float(elev_norm),
                "slope": float(sample.get("slope") or 0.0),
                "local_relief": float(sample.get("local_relief") or 0.0),
                "slope_bias": slope_bias,
                "score": int(round(score - (idx - 1))),
                "source_name": name,
                "legality_status": legal_class,
                "reasoning": reasoning,
                "preferred_wind": preferred_wind,
                "best_time_window": best_window,
                "best_time_label": best_label,
                "travel_score": int(round(travel_score)),
                "bedding_score": int(round(bedding_score)),
                "feeding_score": int(round(feeding_score)),
                "confidence": int(round(confidence)),
                "wind_fit": wind_fit,
                "primary_tag": terrain_read["primary_tag"],
                "support_tags": terrain_read["support_tags"],
                "all_tags": terrain_read["all_tags"],
                "hard_override": bool(practical_read.get("hard_override")),
                "edge_risk": bool(terrain_read.get("edge_risk")),
                "interior_secure": bool(terrain_read.get("interior_secure")),
                "bench_like": bool(terrain_read.get("bench_like")),
                "intercept_like": bool(terrain_read.get("intercept_like")),
                "shoulder_like": bool(terrain_read.get("shoulder_like")),
                "funnel_like": bool(terrain_read.get("funnel_like")),
                "convergence_like": bool(terrain_read.get("convergence_like")),
                "limited_practical_access": bool(practical_read.get("limited_practical_access")),
                "high_effort_access": bool(practical_read.get("high_effort_access")),
                "provider_reliability_reasons": provider_reasons,
                "vegetation_classification": vegetation_profile["classification"],
                "vegetation_trust_tag": vegetation_tags[0] if vegetation_tags else "",
                "features": feature_flags,
                "feature_readout": feature_readout,
                "selected_species": species_profile.get("profile_id"),
                "species_label": species_profile.get("label"),
                "species_region_supported": bool(species_profile.get("region_supported", True)),
                "species_tuning_note": species_note,
            }

            legal_candidates.append(record)

    for feat in features:
        props = dict(feat.get("properties") or {})
        geom = feat.get("geometry") or {}
        legal_class = str(props.get("monahinga_legal_class", "unknown")).lower()
        if legal_class == "legal":
            continue
        name = _feature_name(props)
        center_lon, center_lat = bbox_obj.clamp_point(*_feature_center(geom))
        sample = _sample_dem(dem, bbox, center_lon, center_lat)
        suppressed_candidates.append(
            {
                "lon": float(center_lon),
                "lat": float(center_lat),
                "elevation_m": float(sample["elevation_m"]),
                "slope_bias": _quantize_slope(sample["slope"]),
                "score": 48 if legal_class == "unknown" else 42,
                "source_name": name,
                "legality_status": legal_class,
                "reasoning": f"Suppressed because legality is {legal_class} at {name}; visible for caution, not surfaced as legal sit.",
                "preferred_wind": _wind_from_aspect(sample["aspect_deg"]),
                "best_time_window": "Ground-check first",
                "best_time_label": "Operator awareness",
                "travel_score": 45,
                "bedding_score": 44,
                "feeding_score": 44,
                "confidence": 42,
                "wind_fit": None,
                "features": {"ridge": False, "bench": False, "edge": False, "open": False, "cover": False},
            }
        )

    analysis_mode = "legal_hunt"
    if not legal_candidates:
        analysis_mode = "terrain_only"
        fallback = []
        sample_points = [
            (0.5, 0.5, "Center Box"),
            (0.33, 0.38, "West Shoulder"),
            (0.67, 0.42, "East Shoulder"),
            (0.44, 0.68, "North Bench"),
            (0.58, 0.24, "South Shelf"),
        ]
        box_min_lon, box_min_lat, box_max_lon, box_max_lat = bbox
        for idx, (fx, fy, name) in enumerate(sample_points, start=1):
            lon = box_min_lon + (box_max_lon - box_min_lon) * fx
            lat = box_min_lat + (box_max_lat - box_min_lat) * fy
            sample = _sample_dem(dem, bbox, lon, lat)
            slope_bias = _quantize_slope(sample["slope"])
            elev_norm = max(0.0, min(1.0, (sample["elevation_m"] - dem_min) / dem_range))
            terrain_score = elev_norm * 25.0 + sample["local_relief"] * 0.22
            terrain_read = _terrain_reasoning(
                dem,
                bbox,
                lon,
                lat,
                sample,
                slope_bias,
                elev_norm,
                (box_min_lon, box_min_lat, box_max_lon, box_max_lat),
                name,
                "unverified",
            )
            feature_flags = _terrain_feature_flags(terrain_read, vegetation_profile["classification"])
            validity_read = _terrain_validity_read(dem, bbox, lon, lat, sample, "unverified")
            terrain_read["primary_tag"] = "Exploration Only"
            terrain_read["support_tags"] = [tag for tag in validity_read["display_tags"] if tag not in {"Exploration Only"}][:2]
            terrain_read["all_tags"] = ["Exploration Only", *terrain_read["support_tags"]][:3]
            score = 54.0 + terrain_score - validity_read["score_penalty"] - idx + vegetation_profile["score_delta"]
            fallback.append(
                {
                    "lon": float(lon),
                    "lat": float(lat),
                    "elevation_m": float(sample["elevation_m"]),
                    "elevation_norm": float(elev_norm),
                    "slope": float(sample.get("slope") or 0.0),
                    "local_relief": float(sample.get("local_relief") or 0.0),
                    "slope_bias": slope_bias,
                    "score": int(round(score)),
                    "source_name": name,
                    "legality_status": "unverified",
                    "reasoning": (
                        validity_read.get("summary_reason")
                        or (
                            terrain_read["reasoning"]
                            + " Legal hunting access is not verified here, so use this as exploration guidance only."
                            + (
                                " "
                                + " ".join(
                                    bit + "."
                                    for bit in validity_read["reason_bits"]
                                    if bit != "Legal hunting access is not verified here"
                                )
                                if validity_read["reason_bits"]
                                else ""
                            )
                        )
                    ) + (" " + vegetation_profile["reason"] if vegetation_profile["reason"] else ""),
                    "preferred_wind": _wind_from_aspect(sample["aspect_deg"]),
                    "best_time_window": "Scout first and verify access",
                    "best_time_label": "Terrain-only review",
                    "travel_score": int(round(42.0 + sample["local_relief"] * 0.06 + vegetation_profile["travel_delta"])),
                    "bedding_score": int(round(42.0 + elev_norm * 8.0 + vegetation_profile["bedding_delta"])),
                    "feeding_score": int(round(40.0 + (1.0 - elev_norm) * 8.0 + vegetation_profile["feeding_delta"])),
                    "confidence": int(
                        round(
                            max(
                                32.0,
                                44.0 + terrain_score * 0.12 - validity_read["confidence_penalty"] + vegetation_profile["confidence_delta"]
                            )
                        )
                    ),
                    "wind_fit": None,
                    "features": feature_flags,
                    "primary_tag": terrain_read["primary_tag"],
                    "support_tags": terrain_read["support_tags"],
                    "all_tags": terrain_read["all_tags"],
                    "vegetation_classification": vegetation_profile["classification"],
                    "vegetation_trust_tag": (vegetation_profile.get("tags") or [""])[0],
                }
            )
        legal_candidates = fallback

    _apply_behavior_profiles_v2(legal_candidates, species_profile, bbox)

    legal_candidates.sort(
        key=lambda item: (
            item["score"] - (18 if item.get("hard_override") else 0),
            item["confidence"] - (10 if item.get("hard_override") else 0),
            -item["elevation_m"] if item.get("hard_override") else item["elevation_m"],
        ),
        reverse=True,
    )
    selected: list[dict] = []
    min_spacing = max(abs(bbox[2] - bbox[0]), abs(bbox[3] - bbox[1])) * 0.12
    for item in legal_candidates:
        pt = (item["lon"], item["lat"])
        if all(_distance(pt, (s["lon"], s["lat"])) >= min_spacing for s in selected):
            selected.append(item)
        if len(selected) >= 5:
            break
    if len(selected) < min(5, len(legal_candidates)):
        for item in legal_candidates:
            if item not in selected:
                selected.append(item)
            if len(selected) >= min(5, len(legal_candidates)):
                break

    if selected and selected[0].get("hard_override"):
        for alt in legal_candidates:
            if alt is selected[0]:
                continue
            if alt.get("hard_override"):
                continue
            if alt["score"] >= selected[0]["score"] - 14:
                selected.remove(selected[0])
                selected.insert(0, alt)
                break

    if selected and requested_wind and selected[0].get("wind_fit") is False:
        for alt in legal_candidates:
            if alt is selected[0]:
                continue
            if alt.get("hard_override"):
                continue
            if alt.get("wind_fit") is True and alt["score"] >= selected[0]["score"] - 10:
                selected.remove(selected[0])
                if alt in selected:
                    selected.remove(alt)
                selected.insert(0, alt)
                break

    def make_site(rank: int, tier: str, item: dict, title_prefix: str) -> SiteArtifact:
        subtitle = _descriptor(item["lon"], item["lat"], bbox)
        return SiteArtifact(
            rank=rank,
            tier=tier,
            title=f"{title_prefix} — {subtitle}",
            score=int(item["score"]),
            lon=float(item["lon"]),
            lat=float(item["lat"]),
            elevation_m=float(item["elevation_m"]),
            slope_bias=str(item["slope_bias"]),
            legality_status=str(item["legality_status"]),
            source_name=str(item["source_name"]),
            reasoning=str(item["reasoning"]),
            features=dict(item.get("features") or {}),
            feature_readout=str(item.get("feature_readout") or ""),
        )

    primary = make_site(1, "primary", selected[0], "Primary Sit")
    alternates = [
        make_site(i, "alternate", item, f"Alternate Sit #{i}")
        for i, item in enumerate(selected[1:5], start=2)
    ]

    suppressed_candidates.sort(key=lambda item: item["score"], reverse=True)
    near_misses = [
        make_site(i, "near-miss", item, f"Near-Miss #{i}")
        for i, item in enumerate(suppressed_candidates[:3], start=len(alternates) + 2)
    ]

    corridors: list[CorridorArtifact] = []
    if alternates:
        lead = alternates[0]
        corridors.append(
            CorridorArtifact(
                name="Dominant Corridor",
                strength="dominant",
                points=[
                    [primary.lon, primary.lat],
                    [(primary.lon + lead.lon) / 2.0, max(primary.lat, lead.lat)],
                    [lead.lon, lead.lat],
                ],
                reasoning="Main travel line between the strongest legal sit positions along upper structure.",
            )
        )
    if len(alternates) >= 2:
        a = alternates[0]
        b = alternates[1]
        corridors.append(
            CorridorArtifact(
                name="Secondary Corridor A",
                strength="secondary",
                points=[
                    [a.lon, a.lat],
                    [(a.lon + b.lon) / 2.0, (a.lat + b.lat) / 2.0],
                    [b.lon, b.lat],
                ],
                reasoning="Fallback connection between alternate sits when the primary lane is compromised.",
            )
        )

    primary_record = selected[0]
    challenger_record = selected[1] if len(selected) > 1 else {}
    primary_record["reasoning"] = (
        _forced_primary_visibility(primary_record, challenger_record, requested_wind)
        + " "
        + str(primary_record["reasoning"]).rstrip()
        + " "
        + _competitive_edge(primary_record, challenger_record)
        + " "
        + _conditional_outlook(primary_record, challenger_record, requested_wind)
    ).strip()
    primary.reasoning = str(primary_record["reasoning"])
    confidence_value = int(primary_record["confidence"])
    readiness = _readiness_label(float(primary_record["score"]), float(confidence_value), primary_record["wind_fit"])
    cluster_summary = [
        {
            "title": primary.title,
            "score": primary.score,
            "why": f"{primary_record.get('primary_tag', 'Terrain Read')} · Support {' / '.join(primary_record.get('support_tags') or []) if primary_record.get('support_tags') else 'terrain continuity'} · Travel {primary_record['travel_score']} · Bedding {primary_record['bedding_score']}",
        }
    ]
    for alt, raw in zip(alternates[:2], selected[1:3]):
        cluster_summary.append(
            {
                "title": alt.title,
                "score": alt.score,
                "why": f"{raw.get('primary_tag', 'Terrain Read')} · Support {' / '.join(raw.get('support_tags') or []) if raw.get('support_tags') else 'terrain continuity'} · Travel {raw['travel_score']} · Bedding {raw['bedding_score']} · {_rank_pressure_summary(raw, primary_record if raw is selected[1] else selected[max(0, selected.index(raw) - 1)] if raw in selected else None)}",
            }
        )

    legal_coverage_state = "strong" if analysis_mode == "legal_hunt" and len(selected) >= 3 else "partial" if analysis_mode == "legal_hunt" else "none"
    provider_penalty_reasons = primary_record.get("provider_reliability_reasons") or []
    trust_tags = _derive_primary_trust_tags(primary_record, selected[1:3], requested_wind)
    if provider_penalty_reasons:
        if "Data Reliability Reduced" not in trust_tags:
            trust_tags = [*trust_tags[:2], "Data Reliability Reduced"][:3]

    summary = {
        "analysis_mode": analysis_mode,
        "terrain_only_fallback": analysis_mode != "legal_hunt",
        "mode": "terrain_only_exploration" if analysis_mode != "legal_hunt" else str(operator_context.get("mode") or "hunter"),
        "legal_state": legal_coverage_state,
        "legal_state_label": "Strong verified legal hunting land" if legal_coverage_state == "strong" else "Partial verified legal hunting land" if legal_coverage_state == "partial" else "No verified legal hunting land",
        "preferred_wind": primary_record["preferred_wind"],
        "current_wind": requested_wind,
        "wind_fit": primary_record["wind_fit"],
        "confidence": confidence_value,
        "confidence_label": "High" if confidence_value >= 78 else "Medium" if confidence_value >= 62 else "Low",
        "trust_tags": trust_tags,
        "readiness": readiness if analysis_mode == "legal_hunt" else "Terrain Review",
        "best_time_label": primary_record["best_time_label"],
        "best_time_window": primary_record["best_time_window"],
        "cluster_summary": cluster_summary,
        "operator_notes": str(operator_context.get("notes") or "").strip(),
        "bbox_enforced": True,
        "provider_reliability_reasons": provider_penalty_reasons,
        "vegetation_classification": str(operator_context.get("vegetation_classification") or "unknown"),
        "selected_species": species_profile.get("profile_id"),
        "species_label": species_profile.get("label"),
        "species_profile": species_profile,
        "species_region_key": species_profile.get("region_key"),
        "species_region_supported": bool(species_profile.get("region_supported", True)),
        "invalidators": [
            "Wind drifts into the preferred approach lane.",
            "Access pressure rises on the legal edge.",
            "The route forces you through the hot corridor instead of offsetting from it.",
            "Terrain quality or legal verification is too weak to trust the sit call.",
        ],
    }

    payload = {
        "primary": asdict(primary),
        "alternates": [asdict(item) for item in alternates],
        "near_misses": [asdict(item) for item in near_misses],
        "corridors": [asdict(item) for item in corridors],
        "notes": [
            "Selected bbox is enforced as a hard analysis fence before ranking and viewer payload generation.",
            "Only legal areas can surface primary or alternate sits when verified legal candidates exist.",
            "Restricted and unknown areas remain visible as suppressed near-misses.",
            "Ranking now adds relative terrain trust logic so convergence, shoulder, funnel, bench, and edge reads come from the DEM instead of presentation-only phrasing.",
            "Ranking blends terrain structure, legal gating, timing fit, and wind guard logic.",
            "When no verified legal candidates exist inside the selected bbox, the system falls back to terrain-only review mode instead of crashing.",
            "Provider health now reduces confidence and score when terrain or legal data is degraded.",
            "Vegetation classification now meaningfully changes concealment, bedding confidence, and weak-cover penalties inside sit scoring.",
        ],
        "summary": summary,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return DecisionArtifact(
        path=str(out_path.relative_to(terrain_truth_root.parent.parent)),
        primary=primary,
        alternates=alternates,
        near_misses=near_misses,
        corridors=corridors,
        notes=payload["notes"],
        summary=summary,
    )
