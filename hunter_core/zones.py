from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math
from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None


@dataclass(frozen=True)
class HuntZone:
    id: str
    label: str
    x: float
    y: float
    lon: float
    lat: float
    elevation_norm: float
    slope_norm: float
    relief_norm: float
    ridge_signal: float
    drainage_signal: float
    bench_signal: float
    edge_signal: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_heightmap(heightmap_path: Path) -> list[list[float]]:
    payload = json.loads(Path(heightmap_path).read_text(encoding="utf-8"))
    values = payload.get("geometry_values") or payload.get("values") or []
    if not values or not isinstance(values, list):
        raise ValueError(f"Heightmap has no geometry values: {heightmap_path}")
    return values


def _height_band(elevation_norm: float) -> str:
    if elevation_norm >= 0.72:
        return "Upper"
    if elevation_norm <= 0.32:
        return "Lower"
    return "Mid-Slope"


def _terrain_label_from_signals(
    *,
    elevation_norm: float,
    slope_norm: float,
    relief_norm: float,
    ridge_signal: float,
    drainage_signal: float,
    bench_signal: float,
    edge_signal: float,
) -> str:
    """Translate numeric terrain signals into hunter-readable names.

    This is intentionally deterministic and simple. The goal is not to invent
    fake certainty; it is to avoid robotic duplicate labels like "Candidate zone"
    and to make similar benches read differently when the terrain signal differs.
    """
    band = _height_band(elevation_norm)

    # Strong combined reads first.
    if bench_signal >= 0.56 and drainage_signal >= 0.42:
        return f"{band} Bench-to-Drainage Transition"
    if bench_signal >= 0.56 and ridge_signal >= 0.42:
        return f"{band} Bench Below Ridge"
    if bench_signal >= 0.56 and edge_signal >= 0.50:
        return f"{band} Bench Edge"
    if ridge_signal >= 0.55 and edge_signal >= 0.44:
        return "Leeward Ridge Edge"
    if drainage_signal >= 0.55 and relief_norm >= 0.42:
        return "Lower Drainage Pinch"
    if edge_signal >= 0.62 and relief_norm >= 0.40:
        return "Movement Edge Funnel"

    # Primary terrain reads.
    if bench_signal >= 0.56:
        return f"{band} Bench"
    if ridge_signal >= 0.55:
        return "Ridge Edge"
    if drainage_signal >= 0.55:
        return "Lower Drainage Line"
    if edge_signal >= 0.55:
        return "Terrain Edge"

    # Softer fallback reads.
    if slope_norm <= 0.28 and relief_norm >= 0.35:
        return f"{band} Flat Shelf"
    if relief_norm >= 0.58:
        return "Broken Relief Transition"
    return "Terrain Transition"


def _fallback_zones(bbox: list[float], count: int = 9) -> list[HuntZone]:
    min_lon, min_lat, max_lon, max_lat = [float(v) for v in bbox]
    zones: list[HuntZone] = []
    idx = 1
    for gy in (0.25, 0.50, 0.75):
        for gx in (0.25, 0.50, 0.75):
            elevation_norm = 0.5
            slope_norm = 0.35
            relief_norm = 0.25
            ridge_signal = 0.35
            drainage_signal = 0.25
            bench_signal = 0.45
            edge_signal = 0.40
            zones.append(HuntZone(
                id=f"zone_{idx:02d}",
                label=_terrain_label_from_signals(
                    elevation_norm=elevation_norm,
                    slope_norm=slope_norm,
                    relief_norm=relief_norm,
                    ridge_signal=ridge_signal,
                    drainage_signal=drainage_signal,
                    bench_signal=bench_signal,
                    edge_signal=edge_signal,
                ),
                x=gx,
                y=gy,
                lon=min_lon + (max_lon - min_lon) * gx,
                lat=min_lat + (max_lat - min_lat) * (1.0 - gy),
                elevation_norm=elevation_norm,
                slope_norm=slope_norm,
                relief_norm=relief_norm,
                ridge_signal=ridge_signal,
                drainage_signal=drainage_signal,
                bench_signal=bench_signal,
                edge_signal=edge_signal,
            ))
            idx += 1
    return zones[:count]


def generate_candidate_zones(
    *,
    bbox: list[float],
    heightmap_path: str | Path,
    max_zones: int = 18,
) -> list[HuntZone]:
    """Create candidate zones from the existing heightmap without changing the UI pipeline.

    This is intentionally fast and deterministic. It does not need outside services.
    """
    if np is None:
        return _fallback_zones(bbox, min(max_zones, 9))

    try:
        arr = np.asarray(_load_heightmap(Path(heightmap_path)), dtype=np.float32)
    except Exception:
        return _fallback_zones(bbox, min(max_zones, 9))

    if arr.ndim != 2 or arr.size == 0:
        return _fallback_zones(bbox, min(max_zones, 9))

    rows, cols = arr.shape
    if rows < 8 or cols < 8:
        return _fallback_zones(bbox, min(max_zones, 9))

    gy, gx = np.gradient(arr)
    slope = np.hypot(gx, gy)

    def norm(a):
        lo = float(np.nanpercentile(a, 2))
        hi = float(np.nanpercentile(a, 98))
        if hi - lo < 1e-6:
            return np.zeros_like(a, dtype=np.float32)
        return np.clip((a - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)

    elev_n = norm(arr)
    slope_n = norm(slope)

    neighbors = [arr]
    for dy, dx in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        neighbors.append(np.roll(np.roll(arr, dy, axis=0), dx, axis=1))
    local_relief = np.maximum.reduce(neighbors) - np.minimum.reduce(neighbors)
    relief_n = norm(local_relief)

    smooth = arr.copy()
    for _ in range(2):
        smooth = (
            smooth
            + np.roll(smooth, 1, axis=0) + np.roll(smooth, -1, axis=0)
            + np.roll(smooth, 1, axis=1) + np.roll(smooth, -1, axis=1)
        ) / 5.0

    ridge = norm(np.clip(arr - smooth, 0.0, None))
    drainage = norm(np.clip(smooth - arr, 0.0, None))
    bench = np.clip((1.0 - slope_n) * (0.35 + relief_n * 0.65), 0.0, 1.0)
    edge = np.clip(0.50 * slope_n + 0.35 * relief_n + 0.15 * np.abs(ridge - drainage), 0.0, 1.0)

    candidate_strength = (
        ridge * 0.28
        + bench * 0.26
        + edge * 0.24
        + drainage * 0.10
        + relief_n * 0.12
    )

    margin_y = max(2, rows // 16)
    margin_x = max(2, cols // 16)
    candidate_strength[:margin_y, :] *= 0.80
    candidate_strength[-margin_y:, :] *= 0.80
    candidate_strength[:, :margin_x] *= 0.80
    candidate_strength[:, -margin_x:] *= 0.80

    flat_order = np.argsort(candidate_strength.ravel())[::-1]
    min_dist = max(6, min(rows, cols) // 7)
    selected: list[tuple[int, int]] = []

    for flat in flat_order:
        y, x = divmod(int(flat), cols)
        if any(math.hypot(y - sy, x - sx) < min_dist for sy, sx in selected):
            continue
        selected.append((y, x))
        if len(selected) >= max_zones:
            break

    if not selected:
        return _fallback_zones(bbox, min(max_zones, 9))

    min_lon, min_lat, max_lon, max_lat = [float(v) for v in bbox]
    zones: list[HuntZone] = []
    for idx, (y, x) in enumerate(selected, start=1):
        xn = x / max(1, cols - 1)
        yn = y / max(1, rows - 1)
        lon = min_lon + (max_lon - min_lon) * xn
        lat = max_lat - (max_lat - min_lat) * yn

        elevation_norm = round(float(elev_n[y, x]), 4)
        slope_norm = round(float(slope_n[y, x]), 4)
        relief_norm = round(float(relief_n[y, x]), 4)
        ridge_signal = round(float(ridge[y, x]), 4)
        drainage_signal = round(float(drainage[y, x]), 4)
        bench_signal = round(float(bench[y, x]), 4)
        edge_signal = round(float(edge[y, x]), 4)

        zones.append(HuntZone(
            id=f"zone_{idx:02d}",
            label=_terrain_label_from_signals(
                elevation_norm=elevation_norm,
                slope_norm=slope_norm,
                relief_norm=relief_norm,
                ridge_signal=ridge_signal,
                drainage_signal=drainage_signal,
                bench_signal=bench_signal,
                edge_signal=edge_signal,
            ),
            x=round(float(xn), 4),
            y=round(float(yn), 4),
            lon=round(float(lon), 6),
            lat=round(float(lat), 6),
            elevation_norm=elevation_norm,
            slope_norm=slope_norm,
            relief_norm=relief_norm,
            ridge_signal=ridge_signal,
            drainage_signal=drainage_signal,
            bench_signal=bench_signal,
            edge_signal=edge_signal,
        ))
    return zones
