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

    scored = [
        score_zone(
            zone=zone,
            vegetation_classification=vegetation_classification,
            wind_direction=wind_direction,
            terrain_bias=terrain_bias,
            notes=notes,
        ).to_dict()
        for zone in zones
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
        },
        "warnings": [
            "This is a decision-support layer, not legal or safety authority.",
            "Always verify land access, laws, wind, thermals, and animal sign in the field.",
        ],
    }
