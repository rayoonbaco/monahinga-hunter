from __future__ import annotations

from pathlib import Path
import copy
import json
import math
import time
from typing import Any

from .zones import generate_candidate_zones
from .scoring import score_zone, parse_wind_degrees


_ENGINE_VERSION = "hunter_core_2_0_pass10_ui_role_labels"


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _plain_summary(top: list[dict[str, Any]]) -> str:
    if not top:
        return "No ranked hunt zones were produced. Verify terrain data and rerun."

    best = top[0]
    label = str(best.get("label") or "best setup")
    score = best.get("score", "--")
    reason = best.get("reasoning") or []
    risk = best.get("risks") or []

    reason_text = reason[0] if reason else "it has the best combined terrain, wind, access, cover, and pressure score"
    risk_text = risk[0] if risk else "wind, legal access, and fresh sign still need field verification"

    return (
        f"Best Setup: {label}. "
        f"This is the lead option at {score}/100 because {reason_text}. "
        f"Best move: enter low, stay off the obvious travel edge, and hunt the downwind side. "
        f"Breaks if: {risk_text}."
    )


def _zone_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    za = a.get("zone") or {}
    zb = b.get("zone") or {}
    try:
        return math.hypot(
            float(za.get("x")) - float(zb.get("x")),
            float(za.get("y")) - float(zb.get("y")),
        )
    except Exception:
        pass

    try:
        return math.hypot(
            float(a.get("lon")) - float(b.get("lon")),
            float(a.get("lat")) - float(b.get("lat")),
        )
    except Exception:
        return 999.0


def _label_family(label: object) -> str:
    text = str(label or "").strip().lower()
    if "bench" in text:
        return "bench"
    if "ridge" in text or "spur" in text:
        return "ridge"
    if "drainage" in text or "creek" in text or "bottom" in text:
        return "drainage"
    if "saddle" in text:
        return "saddle"
    if "bowl" in text or "thermal" in text:
        return "thermal"
    if "edge" in text or "transition" in text:
        return "edge"
    return text or "unknown"




# MONAHINGA_CHALLENGE_SIT_ALGORITHM_V1
# Algorithm specialists:
# - Access Reality Engineer: blocks sits a hunter cannot practically reach.
# - Parcel Legality Sentinel: keeps primary sits off private parcel context when parcel data exists.
# - Water/Slope Gatekeeper: rejects water, extreme slope, exposed peak-only crowns, and impenetrable terrain proxies.
# - Wildlife Behavior Director: keeps PAD-US/legal signal as a qualifier, not the automatic winner.
def _iter_geojson_features(geojson: object) -> list[dict[str, Any]]:
    if not isinstance(geojson, dict):
        return []
    if geojson.get("type") == "FeatureCollection":
        return [f for f in (geojson.get("features") or []) if isinstance(f, dict)]
    if geojson.get("type") == "Feature":
        return [geojson]
    if geojson.get("type") in {"Polygon", "MultiPolygon"}:
        return [{"type": "Feature", "properties": {}, "geometry": geojson}]
    return []


def _point_in_ring(lon: float, lat: float, ring: object) -> bool:
    if not isinstance(ring, list) or len(ring) < 3:
        return False
    inside = False
    j = len(ring) - 1
    for i, current in enumerate(ring):
        previous = ring[j]
        try:
            xi, yi = float(current[0]), float(current[1])
            xj, yj = float(previous[0]), float(previous[1])
        except Exception:
            j = i
            continue
        crosses = ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi)
        if crosses:
            inside = not inside
        j = i
    return inside


def _point_in_polygon_coords(lon: float, lat: float, coords: object) -> bool:
    if not isinstance(coords, list) or not coords:
        return False
    outer = coords[0]
    if not _point_in_ring(lon, lat, outer):
        return False
    for hole in coords[1:]:
        if _point_in_ring(lon, lat, hole):
            return False
    return True


def _geometry_contains_point(geom: object, lon: float, lat: float) -> bool:
    if not isinstance(geom, dict):
        return False
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if gtype == "Polygon":
        return _point_in_polygon_coords(lon, lat, coords)
    if gtype == "MultiPolygon" and isinstance(coords, list):
        return any(_point_in_polygon_coords(lon, lat, poly) for poly in coords)
    return False


def _point_in_parcel_context(lon: float, lat: float, parcel_geojson: object) -> bool:
    for feature in _iter_geojson_features(parcel_geojson):
        if _geometry_contains_point(feature.get("geometry"), lon, lat):
            return True
    return False


def _zone_constraint_reasons(zone: object, parcel_geojson: object | None) -> list[str]:
    reasons: list[str] = []
    try:
        lon = float(getattr(zone, "lon"))
        lat = float(getattr(zone, "lat"))
        elevation = float(getattr(zone, "elevation_norm"))
        slope = float(getattr(zone, "slope_norm"))
        relief = float(getattr(zone, "relief_norm"))
        drainage = float(getattr(zone, "drainage_signal"))
        bench = float(getattr(zone, "bench_signal"))
        edge = float(getattr(zone, "edge_signal"))
    except Exception:
        return ["Rejected: candidate signals were not readable enough for the safety/reality gate."]

    if parcel_geojson and _point_in_parcel_context(lon, lat, parcel_geojson):
        reasons.append("Rejected: candidate falls inside available private-parcel context. Use PAD-US/public signal outside parcel context or verify permission manually.")

    water_like = (
        (elevation <= 0.16 and drainage >= 0.40 and slope <= 0.24)
        or (elevation <= 0.12 and relief <= 0.22)
    )
    if water_like:
        reasons.append("Rejected: candidate looks water/floodplain-low from the terrain signals.")

    if slope >= 0.82:
        reasons.append("Rejected: slope is too steep for a practical primary sit/access recommendation.")

    if relief >= 0.88 and slope >= 0.68:
        reasons.append("Rejected: broken relief and steepness suggest impenetrable or unsafe approach terrain.")

    if elevation >= 0.96 and slope >= 0.42 and bench <= 0.34:
        reasons.append("Rejected: exposed peak/top crown with weak bench signal; likely hard to reach and poor concealment.")

    if edge <= 0.16 and bench <= 0.18 and slope >= 0.58:
        reasons.append("Rejected: weak edge/bench value with hard slope; not enough hunting setup value for the effort.")

    return reasons


def _apply_challenge_sit_constraints(zones: list[Any], parcel_geojson: object | None) -> tuple[list[Any], dict[str, Any]]:
    rejected: list[dict[str, Any]] = []
    accepted: list[Any] = []
    for zone in zones:
        reasons = _zone_constraint_reasons(zone, parcel_geojson)
        if reasons:
            rejected.append({
                "id": getattr(zone, "id", "unknown"),
                "label": getattr(zone, "label", "unknown"),
                "lon": getattr(zone, "lon", None),
                "lat": getattr(zone, "lat", None),
                "reasons": reasons,
            })
        else:
            accepted.append(zone)

    parcel_features = len(_iter_geojson_features(parcel_geojson)) if parcel_geojson else 0
    warnings: list[str] = []
    if parcel_features:
        warnings.append("Private parcel context was available, so primary candidates inside parcel polygons were removed when alternatives existed.")
    warnings.append("Challenge gate also screens obvious water/floodplain lows, extreme slopes, exposed peak crowns, and impenetrable terrain proxies.")

    strict_enough = len(accepted) >= 3
    if not strict_enough:
        warnings.append("Strict sit gate found fewer than three clean candidates, so the model kept the original pool with stronger risk warnings. Treat this run as scouting-only until verified.")

    return (accepted if strict_enough else zones), {
        "enabled": True,
        "version": "MONAHINGA_CHALLENGE_SIT_ALGORITHM_V1",
        "parcel_features_available": parcel_features,
        "original_candidates": len(zones),
        "accepted_candidates": len(accepted),
        "rejected_candidates": len(rejected),
        "strict_filter_applied": strict_enough,
        "warnings": warnings,
        "sample_rejections": rejected[:6],
    }


def _curate_top_zones(scored: list[dict[str, Any]], *, limit: int = 5) -> list[dict[str, Any]]:
    """Pick hunt options that feel useful, not repetitive."""
    if not scored:
        return []

    selected: list[dict[str, Any]] = [scored[0]]
    selected_ids = {str(scored[0].get("id"))}
    selected_families = {_label_family(scored[0].get("label"))}

    def already_selected(zone: dict[str, Any]) -> bool:
        zid = str(zone.get("id"))
        if zid and zid in selected_ids:
            return True
        return any(zone is existing for existing in selected)

    def add(zone: dict[str, Any]) -> None:
        selected.append(zone)
        selected_ids.add(str(zone.get("id")))
        selected_families.add(_label_family(zone.get("label")))

    # Pass 1: build top 3 from unique terrain families first.
    for zone in scored[1:]:
        if len(selected) >= min(3, limit):
            break
        if already_selected(zone):
            continue
        family = _label_family(zone.get("label"))
        if family in selected_families:
            continue
        add(zone)

    # Pass 2: if there still are not 3 unique families, use well-separated duplicate families.
    for zone in scored[1:]:
        if len(selected) >= min(3, limit):
            break
        if already_selected(zone):
            continue
        if any(_zone_distance(zone, existing) < 0.24 for existing in selected):
            continue
        add(zone)

    # Pass 3: fill remaining top 5 with unique families where possible.
    for zone in scored[1:]:
        if len(selected) >= limit:
            break
        if already_selected(zone):
            continue
        family = _label_family(zone.get("label"))
        if family in selected_families:
            continue
        add(zone)

    # Pass 4: final fallback, still avoiding very close duplicates first.
    for zone in scored[1:]:
        if len(selected) >= limit:
            break
        if already_selected(zone):
            continue
        if any(_zone_distance(zone, existing) < 0.16 for existing in selected):
            continue
        add(zone)

    # Pass 5: absolute fallback so the panel never goes empty on simple terrain.
    for zone in scored[1:]:
        if len(selected) >= limit:
            break
        if not already_selected(zone):
            add(zone)

    return selected[:limit]


def _with_ui_role_labels(top: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Make repeated top labels useful in the visible brain panel.

    We preserve the actual terrain label under original_label, then adjust the
    display label only when a top-3 repeat would look confusing to a hunter.
    """
    role_names = {
        0: "Primary",
        1: "Backup",
        2: "Secondary",
        3: "Alternate",
        4: "Scout",
    }

    result: list[dict[str, Any]] = []
    seen_labels: dict[str, int] = {}

    for idx, zone in enumerate(top):
        item = copy.deepcopy(zone)
        raw_label = str(item.get("label") or f"Zone {idx + 1}").strip()
        key = raw_label.lower()
        item["original_label"] = raw_label
        item["ui_role"] = role_names.get(idx, "Option")

        if idx < 3:
            prior_count = seen_labels.get(key, 0)
            if prior_count > 0:
                item["label"] = f"{item['ui_role']} {raw_label}"
            else:
                item["label"] = raw_label

        seen_labels[key] = seen_labels.get(key, 0) + 1
        result.append(item)

    return result


def run_hunter_core(
    *,
    bbox: list[float],
    terrain_summary_path: str | Path,
    heightmap_path: str | Path,
    vegetation_classification: str = "unknown",
    wind_direction: object = "",
    notes: str = "",
    mode: str = "hunter",
    max_zones: int = 18,
    parcel_geojson: dict | None = None,
) -> dict[str, Any]:
    """Run fast deterministic hunt intelligence before the legacy decision renderer."""
    started = time.perf_counter()
    terrain_summary = _read_json(terrain_summary_path)
    terrain_bias = str(terrain_summary.get("structure_bias") or "unknown terrain")

    zones = generate_candidate_zones(
        bbox=bbox,
        heightmap_path=heightmap_path,
        max_zones=max_zones,
    )
    zones_for_scoring, challenge_gate = _apply_challenge_sit_constraints(zones, parcel_geojson)

    scored = [
        score_zone(
            zone=zone,
            vegetation_classification=vegetation_classification,
            wind_direction=wind_direction,
            terrain_bias=terrain_bias,
            notes=notes,
        ).to_dict()
        for zone in zones_for_scoring
    ]
    scored.sort(key=lambda z: (int(z.get("score", 0)), int(z.get("confidence", 0))), reverse=True)

    curated = _curate_top_zones(scored, limit=5)
    top = _with_ui_role_labels(curated)
    wind_degrees = parse_wind_degrees(wind_direction)

    return {
        "ok": True,
        "version": _ENGINE_VERSION,
        "mode": str(mode or "hunter"),
        "bbox": [float(v) for v in bbox],
        "runtime_ms": int(round((time.perf_counter() - started) * 1000)),
        "inputs": {
            "vegetation_classification": str(vegetation_classification or "unknown"),
            "wind_direction": str(wind_direction or ""),
            "wind_degrees": wind_degrees,
            "terrain_bias": terrain_bias,
            "elevation_range_m": terrain_summary.get("elevation_range_m"),
        },
        "summary": _plain_summary(top),
        "zones_considered": len(scored),
        "challenge_sit_gate": challenge_gate,
        "top_zones": top,
        "all_zones": scored,
        "curation": {
            "enabled": True,
            "method": "strict_top3_unique_families_plus_ui_role_labels_for_repeats",
            "top3_role_labels": True,
        },
        "scoring_model": {
            "terrain_funnel": "0-20",
            "wind_advantage": "0-20",
            "thermal_behavior": "0-15",
            "access_safety": "0-15",
            "bedding_security": "0-10",
            "food_water_route": "0-10",
            "pressure_avoidance": "0-10",
            "cover_value": "0-10",
            "challenge_constraints": "hard gate before ranking",
        },
        "warnings": [
            "This is a decision-support layer, not legal or safety authority.",
            "Always verify land access, laws, wind, thermals, and animal sign in the field.",
            "Challenge sit gate blocks obvious private-parcel, water, extreme slope, exposed peak, and impenetrable-terrain candidates when alternatives exist.",
        ] + list(challenge_gate.get("warnings") or []),
    }
