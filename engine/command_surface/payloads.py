from __future__ import annotations

from pathlib import Path
import html
import json
from typing import Iterable

from engine.command_surface.config import ViewerDefaults
from engine.terrain_truth.contract import TerrainTruthContract


EPS = 1e-9


def normalize_point(lon: float, lat: float, bbox: list[float]) -> tuple[float, float]:
    min_lon, min_lat, max_lon, max_lat = bbox
    x = 0.5 if max_lon == min_lon else (lon - min_lon) / (max_lon - min_lon)
    y = 0.5 if max_lat == min_lat else (lat - min_lat) / (max_lat - min_lat)
    return float(x), float(y)


def _ring_area(ring: list[list[float]]) -> float:
    if len(ring) < 3:
        return 0.0
    area = 0.0
    for idx, point in enumerate(ring):
        nxt = ring[(idx + 1) % len(ring)]
        area += point[0] * nxt[1] - nxt[0] * point[1]
    return abs(area) * 0.5


def _ensure_closed(points: list[list[float]]) -> list[list[float]]:
    if not points:
        return []
    if points[0] != points[-1]:
        return points + [points[0]]
    return points


def _dedupe_consecutive(points: list[list[float]]) -> list[list[float]]:
    if not points:
        return []
    out = [points[0]]
    for point in points[1:]:
        if abs(point[0] - out[-1][0]) > EPS or abs(point[1] - out[-1][1]) > EPS:
            out.append(point)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) <= EPS and abs(out[0][1] - out[-1][1]) <= EPS:
        out.pop()
    return out


def _intersect_vertical(start: list[float], end: list[float], x_edge: float) -> list[float]:
    dx = end[0] - start[0]
    if abs(dx) <= EPS:
        return [x_edge, start[1]]
    t = (x_edge - start[0]) / dx
    return [x_edge, start[1] + t * (end[1] - start[1])]


def _intersect_horizontal(start: list[float], end: list[float], y_edge: float) -> list[float]:
    dy = end[1] - start[1]
    if abs(dy) <= EPS:
        return [start[0], y_edge]
    t = (y_edge - start[1]) / dy
    return [start[0] + t * (end[0] - start[0]), y_edge]


def _clip_ring_to_bbox(ring: list[list[float]], bbox: list[float]) -> list[list[float]]:
    if len(ring) < 3:
        return []
    min_lon, min_lat, max_lon, max_lat = bbox
    subject = [list(map(float, pt[:2])) for pt in ring]
    subject = _dedupe_consecutive(subject)
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
        return _dedupe_consecutive(output)

    clipped = subject
    clipped = clip(clipped, lambda p: p[0] >= min_lon - EPS, lambda a, b: _intersect_vertical(a, b, min_lon))
    clipped = clip(clipped, lambda p: p[0] <= max_lon + EPS, lambda a, b: _intersect_vertical(a, b, max_lon))
    clipped = clip(clipped, lambda p: p[1] >= min_lat - EPS, lambda a, b: _intersect_horizontal(a, b, min_lat))
    clipped = clip(clipped, lambda p: p[1] <= max_lat + EPS, lambda a, b: _intersect_horizontal(a, b, max_lat))
    clipped = _dedupe_consecutive(clipped)
    if len(clipped) < 3:
        return []
    return clipped


def _convert_ring(ring: list[list[float]], bbox: list[float]) -> list[list[float]]:
    points = []
    for pt in ring:
        if len(pt) < 2:
            continue
        x, y = normalize_point(float(pt[0]), float(pt[1]), bbox)
        x = min(1.0, max(0.0, x))
        y = min(1.0, max(0.0, y))
        points.append([round(x, 6), round(y, 6)])
    points = _dedupe_consecutive(points)
    if len(points) >= 3 and _ring_area(points) > 1e-7:
        return points
    return []


def _polygon_feature_from_rings(cls: str, rings: Iterable[list[list[float]]], bbox: list[float]) -> dict | None:
    converted = []
    for idx, ring in enumerate(rings):
        clipped = _clip_ring_to_bbox(ring, bbox)
        if not clipped:
            continue
        conv = _convert_ring(clipped, bbox)
        if not conv:
            continue
        if idx == 0:
            converted.insert(0, conv)
        else:
            converted.append(conv)
    if not converted:
        return None
    return {"class": cls, "rings": converted}


def polygon_features(geojson_path: Path, bbox: list[float]) -> tuple[list[dict], dict]:
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    out: list[dict] = []
    stats = {"coverage_ratio": 0.0, "cropped": False, "feature_count": 0}
    min_lon, min_lat, max_lon, max_lat = bbox
    bbox_area = max((max_lon - min_lon) * (max_lat - min_lat), EPS)

    for feat in data.get("features", []):
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        cls = str(props.get("monahinga_legal_class", "unknown")).lower()
        geom_type = geom.get("type")
        if geom_type == "Polygon":
            polys = [geom.get("coordinates") or []]
        elif geom_type == "MultiPolygon":
            polys = geom.get("coordinates") or []
        else:
            continue

        for poly in polys:
            if not poly:
                continue
            original_exterior = poly[0] if poly else []
            original_area = _ring_area(_dedupe_consecutive([list(map(float, pt[:2])) for pt in original_exterior if len(pt) >= 2]))
            feature = _polygon_feature_from_rings(cls, poly, bbox)
            if not feature:
                if original_area > 0:
                    stats["cropped"] = True
                continue
            clipped_area = _ring_area(feature["rings"][0])
            if original_area > 0 and abs(clipped_area - original_area / bbox_area) > 1e-4:
                stats["cropped"] = True
            stats["coverage_ratio"] += clipped_area
            out.append(feature)

    stats["coverage_ratio"] = round(min(1.0, stats["coverage_ratio"]), 4)
    stats["feature_count"] = len(out)
    return out, stats


def build_payload(
    run_root: Path,
    contract: TerrainTruthContract,
    available_layers: dict[str, str],
    summary: dict,
    viewer_defaults: ViewerDefaults,
) -> dict:
    terrain_truth_root = run_root / "terrain_truth"
    legal_geojson_path = terrain_truth_root / "legal" / "legal_surface.geojson"
    if legal_geojson_path.exists():
        polygons, legal_stats = polygon_features(legal_geojson_path, contract.bbox)
    else:
        polygons, legal_stats = [], {"coverage_ratio": 0.0, "cropped": False, "feature_count": 0}

    sites = [contract.decision.primary] + contract.decision.alternates + contract.decision.near_misses
    site_payload = []
    for site in sites:
        nx, ny = normalize_point(site.lon, site.lat, contract.bbox)
        site_payload.append(
            {
                "rank": site.rank,
                "tier": site.tier,
                "title": site.title,
                "score": site.score,
                "lon": site.lon,
                "lat": site.lat,
                "nx": round(nx, 6),
                "ny": round(ny, 6),
                "elevation_m": site.elevation_m,
                "reasoning": site.reasoning,
                "source_name": site.source_name,
                "slope_bias": site.slope_bias,
                "legality_status": site.legality_status,
            }
        )
    corridor_payload = [
        {
            "name": corridor.name,
            "strength": corridor.strength,
            "points": corridor.points,
            "reasoning": corridor.reasoning,
        }
        for corridor in contract.decision.corridors
    ]
    min_lon, min_lat, max_lon, max_lat = contract.bbox
    return {
        "bbox": contract.bbox,
        "bbox_center": {
            "lon": round((min_lon + max_lon) / 2.0, 6),
            "lat": round((min_lat + max_lat) / 2.0, 6),
        },
        "layers": available_layers,
        "defaultLayer": viewer_defaults.default_layer,
        "defaultPadusMode": viewer_defaults.default_padus_mode,
        "wildlife_atmosphere": (contract.operator_context or {}).get("wildlife_atmosphere") or {},
        "heightmap_url": "../terrain_truth/terrain_derivatives/heightmap.json",
        "sites": site_payload,
        "corridors": corridor_payload,
        "legal_polygons": polygons,
        "summary": {
            "mesh_width": summary.get("width"),
            "mesh_height": summary.get("height"),
            "terrain_strength": summary.get("terrain_strength"),
            "surface_trust": summary.get("surface_trust"),
            "legal_coverage_ratio": legal_stats.get("coverage_ratio"),
            "legal_cropped_to_bbox": legal_stats.get("cropped"),
            "legal_feature_count": legal_stats.get("feature_count"),
        },
    }


def build_layer_buttons(available_layers: dict[str, str], active_layer: str) -> str:
    return "".join(
        f'<button class="layer-btn{" active" if key == active_layer else ""}" data-layer="{key}">{html.escape(key.title())}</button>'
        for key in available_layers.keys()
    )


def build_cluster_markup(decision_summary: dict) -> str:
    clusters = decision_summary.get("cluster_summary") or []
    return "".join(
        f'<div class="intel-row"><strong>{html.escape(str(c.get("title") or ""))}</strong><span>{html.escape(str(c.get("why") or ""))}</span></div>'
        for c in clusters[:3]
    )


def build_invalidators(decision_summary: dict) -> str:
    return "".join(
        f"<li>{html.escape(str(x))}</li>" for x in (decision_summary.get("invalidators") or [])[:3]
    )


def build_ranked_rows(sites: list) -> str:
    rows = []
    for s in sites:
        tier_label = "PRIMARY" if s.tier == "primary" else "ALTERNATE" if s.tier == "alternate" else "NEAR-MISS"
        rows.append(
            f'<button class="row row-button{ " active" if s.rank == 1 else ""}" type="button" data-rank="{s.rank}" data-tier="{html.escape(s.tier)}">'
            f'<div class="row-rank">{s.rank}</div>'
            f'<div class="row-main">'
            f'<div class="row-tier">{tier_label}</div>'
            f'<div class="row-title">{html.escape(s.title)}</div>'
            f'<div class="row-reason">{html.escape(s.reasoning)}</div>'
            f'</div>'
            f'<div class="row-score">{s.score}</div>'
            f'</button>'
        )
    return "".join(rows)
