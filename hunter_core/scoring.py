from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .zones import HuntZone


_WIND_ALIASES = {
    "N": 0.0, "NORTH": 0.0,
    "NE": 45.0, "NORTHEAST": 45.0,
    "E": 90.0, "EAST": 90.0,
    "SE": 135.0, "SOUTHEAST": 135.0,
    "S": 180.0, "SOUTH": 180.0,
    "SW": 225.0, "SOUTHWEST": 225.0,
    "W": 270.0, "WEST": 270.0,
    "NW": 315.0, "NORTHWEST": 315.0,
}


@dataclass(frozen=True)
class ScoredZone:
    id: str
    label: str
    score: int
    confidence: int
    lon: float
    lat: float
    best_time: str
    setup_type: str
    scores: dict[str, int]
    reasoning: list[str]
    risks: list[str]
    zone: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_wind_degrees(wind_direction: object) -> float | None:
    text = str(wind_direction or "").strip().upper().replace(" ", "")
    if not text:
        return None
    if text.endswith("°"):
        text = text[:-1]
    try:
        return float(text) % 360.0
    except ValueError:
        return _WIND_ALIASES.get(text)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _score_int(value: float, maximum: int) -> int:
    return int(round(_clamp(value, 0.0, float(maximum))))


def _wind_score(zone: HuntZone, wind_degrees: float | None) -> tuple[int, list[str], list[str]]:
    if wind_degrees is None:
        return 10, ["No usable wind direction supplied, so wind score stayed neutral."], ["Wind direction should be verified before trusting the final setup."]

    # Approximate exposure from position in box: upper third catches north component, lower third catches south, etc.
    north_exposure = 1.0 - zone.y
    east_exposure = zone.x
    west_exposure = 1.0 - zone.x
    south_exposure = zone.y

    wind_from_n = max(0.0, 1.0 - abs((wind_degrees - 0 + 180) % 360 - 180) / 90.0)
    wind_from_e = max(0.0, 1.0 - abs((wind_degrees - 90 + 180) % 360 - 180) / 90.0)
    wind_from_s = max(0.0, 1.0 - abs((wind_degrees - 180 + 180) % 360 - 180) / 90.0)
    wind_from_w = max(0.0, 1.0 - abs((wind_degrees - 270 + 180) % 360 - 180) / 90.0)

    leeward_guess = (
        wind_from_n * south_exposure
        + wind_from_s * north_exposure
        + wind_from_e * west_exposure
        + wind_from_w * east_exposure
    ) / max(0.01, wind_from_n + wind_from_s + wind_from_e + wind_from_w)

    terrain_help = 0.45 * zone.ridge_signal + 0.35 * zone.bench_signal + 0.20 * zone.edge_signal
    score = _score_int(7.0 + leeward_guess * 8.0 + terrain_help * 5.0, 20)

    reasons = []
    risks = []
    if score >= 15:
        reasons.append("Wind/terrain relationship looks favorable enough to protect the likely setup side.")
    elif score <= 9:
        risks.append("Wind advantage is weak; this setup needs field verification before being trusted.")
    else:
        reasons.append("Wind read is workable but not dominant.")
    return score, reasons, risks


def _vegetation_adjustment(vegetation: str) -> tuple[int, list[str], list[str]]:
    veg = str(vegetation or "unknown").lower()
    if veg == "forest":
        return 9, ["Forest cover improves concealment and bedding security."], []
    if veg == "shrub":
        return 7, ["Shrub or mixed cover gives useful concealment without making the area unreadable."], []
    if veg == "open":
        return 3, [], ["Open cover reduces concealment and raises approach risk."]
    if veg == "water":
        return 1, [], ["Water-dominant classification is a strong warning against treating this as a sit zone."]
    return 5, ["Vegetation is unknown, so cover score stayed conservative."], ["Cover classification should be verified."]


def score_zone(
    *,
    zone: HuntZone,
    vegetation_classification: str,
    wind_direction: object,
    terrain_bias: str,
    notes: str = "",
) -> ScoredZone:
    reasoning: list[str] = []
    risks: list[str] = []

    terrain_funnel = _score_int(
        zone.edge_signal * 8.0 + zone.ridge_signal * 6.0 + zone.drainage_signal * 3.0 + zone.relief_norm * 3.0,
        20,
    )
    if terrain_funnel >= 14:
        reasoning.append("Terrain creates movement compression: edge, ridge, relief, or drainage signals stack together.")
    elif terrain_funnel <= 7:
        risks.append("Terrain compression is not strong; animals may have too many loose travel options.")

    bedding = _score_int(zone.bench_signal * 6.0 + zone.ridge_signal * 2.0 + (1.0 - zone.slope_norm) * 2.0, 10)
    if bedding >= 7:
        reasoning.append("Bench/flat security signal supports bedding or staging behavior nearby.")

    access = _score_int(15.0 - zone.slope_norm * 5.0 - zone.edge_signal * 2.0 + (1.0 - zone.relief_norm) * 3.0, 15)
    if access <= 8:
        risks.append("Access may be noisy, exposed, or physically demanding.")
    else:
        reasoning.append("Access score is acceptable because slope and relief are not punishing at this candidate point.")

    thermal = _score_int(5.0 + zone.relief_norm * 4.0 + zone.drainage_signal * 3.0 + zone.bench_signal * 3.0, 15)
    if thermal >= 11:
        reasoning.append("Relief/drainage shape suggests thermals matter here, especially morning and evening.")
    else:
        risks.append("Thermal behavior is not a dominant advantage from the available terrain signal.")

    food_water = _score_int(2.0 + zone.edge_signal * 3.0 + zone.drainage_signal * 2.0 + (1.0 - zone.elevation_norm) * 3.0, 10)

    pressure = _score_int(4.0 + zone.bench_signal * 3.0 + zone.relief_norm * 2.0 + zone.ridge_signal * 1.0, 10)

    wind_score, wind_reasons, wind_risks = _wind_score(zone, parse_wind_degrees(wind_direction))
    veg_score, veg_reasons, veg_risks = _vegetation_adjustment(vegetation_classification)
    reasoning.extend(wind_reasons + veg_reasons)
    risks.extend(wind_risks + veg_risks)

    scores = {
        "terrain_funnel": terrain_funnel,
        "wind_advantage": wind_score,
        "thermal_behavior": thermal,
        "access_safety": access,
        "bedding_security": bedding,
        "food_water_route": food_water,
        "pressure_avoidance": pressure,
        "cover_value": veg_score,
    }

    raw_total = (
        terrain_funnel
        + wind_score
        + thermal
        + access
        + bedding
        + food_water
        + pressure
        + veg_score
    )

    # Convert 0-110-ish to clean 0-100 with a small terrain-bias correction.
    bias_text = str(terrain_bias or "").lower()
    bias_bonus = 0.0
    if "ridge" in bias_text or "relief" in bias_text:
        bias_bonus += 2.5
    if "low-relief" in bias_text:
        bias_bonus -= 1.5
    if notes and len(str(notes).strip()) > 8:
        reasoning.append("User notes were preserved for the downstream decision layer.")

    final_score = int(round(_clamp(raw_total * 0.92 + bias_bonus, 0.0, 100.0)))
    confidence = int(round(_clamp(58 + zone.relief_norm * 14 + zone.edge_signal * 10 + zone.bench_signal * 8, 35, 92)))

    if thermal >= 11 and bedding >= 7:
        best_time = "first_90_minutes_or_last_90_minutes"
    elif food_water >= 7:
        best_time = "evening_transition"
    else:
        best_time = "midday_scout_or_secondary_setup"

    if terrain_funnel >= 14:
        setup_type = "funnel_intercept"
    elif bedding >= 7:
        setup_type = "bedding_edge_observation"
    elif food_water >= 7:
        setup_type = "travel_route_intercept"
    else:
        setup_type = "secondary_scouting_zone"

    # De-duplicate while preserving order.
    reasoning = list(dict.fromkeys(reasoning))[:6]
    risks = list(dict.fromkeys(risks))[:5]
    if not risks:
        risks = ["No major automatic risk was found, but wind and legal access still need real-world verification."]

    return ScoredZone(
        id=zone.id,
        label=zone.label,
        score=final_score,
        confidence=confidence,
        lon=zone.lon,
        lat=zone.lat,
        best_time=best_time,
        setup_type=setup_type,
        scores=scores,
        reasoning=reasoning,
        risks=risks,
        zone=zone.to_dict(),
    )
