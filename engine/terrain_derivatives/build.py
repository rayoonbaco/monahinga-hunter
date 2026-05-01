from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
from PIL import Image

try:
    import rasterio
except Exception:
    rasterio = None

try:
    import tifffile
except Exception:
    tifffile = None


@dataclass
class TerrainDerivativeResult:
    hillshade_path: Path
    summary_path: Path
    elevation_min_m: float
    elevation_max_m: float
    structure_bias: str
    width: int
    height: int


def _load_dem(dem_path: Path) -> np.ndarray:
    if rasterio is not None:
        with rasterio.open(dem_path) as ds:
            arr = ds.read(1).astype(np.float32)
            nodata = ds.nodata
            if nodata is not None:
                arr[arr == nodata] = np.nan
            return arr

    if tifffile is not None:
        return np.asarray(tifffile.imread(dem_path), dtype=np.float32)

    img = Image.open(dem_path)
    return np.asarray(img, dtype=np.float32)


def _sanitize_dem(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float32)
    finite = np.isfinite(arr)
    if not finite.any():
        return np.zeros_like(arr, dtype=np.float32)

    valid = arr[finite]
    valid = valid[(valid > -500.0) & (valid < 9000.0)]
    if valid.size == 0:
        valid = arr[finite]

    low = float(np.percentile(valid, 0.5))
    high = float(np.percentile(valid, 99.5))
    fill = float(np.median(valid))

    cleaned = np.where(np.isfinite(arr), arr, fill)
    cleaned = np.clip(cleaned, low, high)
    return cleaned.astype(np.float32)


def _box_blur_axis(arr: np.ndarray, radius: int, axis: int) -> np.ndarray:
    if radius <= 0:
        return arr.astype(np.float32, copy=True)

    pad = [(0, 0)] * arr.ndim
    pad[axis] = (radius, radius)
    padded = np.pad(arr, pad, mode="edge")

    cumsum = np.cumsum(padded, axis=axis, dtype=np.float64)
    zero_shape = list(cumsum.shape)
    zero_shape[axis] = 1
    cumsum = np.concatenate([np.zeros(zero_shape, dtype=np.float64), cumsum], axis=axis)

    size = 2 * radius + 1
    slicer_hi = [slice(None)] * arr.ndim
    slicer_lo = [slice(None)] * arr.ndim
    slicer_hi[axis] = slice(size, None)
    slicer_lo[axis] = slice(None, -size)

    blurred = cumsum[tuple(slicer_hi)] - cumsum[tuple(slicer_lo)]
    return (blurred / size).astype(np.float32)


def _smooth(arr: np.ndarray, radius: int, passes: int = 1) -> np.ndarray:
    out = arr.astype(np.float32, copy=True)
    for _ in range(max(1, passes)):
        out = _box_blur_axis(out, radius, axis=1)
        out = _box_blur_axis(out, radius, axis=0)
    return out


def _normalize(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float32)
    lo = float(np.min(arr))
    hi = float(np.max(arr))
    if hi - lo < 1e-6:
        return np.zeros_like(arr, dtype=np.float32)
    return (arr - lo) / (hi - lo)


def _compress_signed(arr: np.ndarray, amount: float | np.ndarray) -> np.ndarray:
    amt = np.clip(np.asarray(amount, dtype=np.float32), 0.0, 0.95)
    if float(np.max(amt)) <= 0.0:
        return arr.astype(np.float32, copy=True)
    scale = 1.0 / np.maximum(0.05, 1.0 - amt)
    return (np.tanh(arr * scale) / scale).astype(np.float32)


def _hillshade(array: np.ndarray, azimuth: float, altitude: float, z_factor: float) -> np.ndarray:
    dy, dx = np.gradient(array * z_factor)
    slope = np.pi / 2.0 - np.arctan(np.hypot(dx, dy))
    aspect = np.arctan2(-dx, dy)

    azimuth_rad = np.deg2rad(azimuth)
    altitude_rad = np.deg2rad(altitude)

    shaded = (
        np.sin(altitude_rad) * np.sin(slope)
        + np.cos(altitude_rad) * np.cos(slope) * np.cos(azimuth_rad - aspect)
    )
    return _normalize(shaded.astype(np.float32))


def _local_relief(dem: np.ndarray, radius: int) -> np.ndarray:
    neighbors = [dem]
    for dy, dx in ((radius, 0), (-radius, 0), (0, radius), (0, -radius)):
        shifted = np.roll(np.roll(dem, dy, axis=0), dx, axis=1)
        neighbors.append(shifted)
    return np.maximum.reduce(neighbors) - np.minimum.reduce(neighbors)


def _to_uint8(arr: np.ndarray) -> np.ndarray:
    return np.clip(_normalize(arr) * 255.0, 0, 255).astype(np.uint8)


def _viewer_vertical_scale(elevation_range_m: float) -> float:
    if elevation_range_m < 20.0:
        return 1.12
    if elevation_range_m < 60.0:
        return 1.04
    if elevation_range_m < 160.0:
        return 0.98
    if elevation_range_m < 450.0:
        return 0.93
    return 0.88


def _viewer_default_exaggeration(elevation_range_m: float) -> float:
    if elevation_range_m < 20.0:
        return 1.10
    if elevation_range_m < 60.0:
        return 1.04
    if elevation_range_m < 160.0:
        return 0.99
    if elevation_range_m < 450.0:
        return 0.95
    return 0.92


def _build_heightmap_payload(cleaned_dem: np.ndarray) -> dict:
    rows, cols = cleaned_dem.shape

    macro = _smooth(cleaned_dem, radius=5, passes=1)
    mid = _smooth(cleaned_dem, radius=3, passes=1)
    fine = _smooth(cleaned_dem, radius=1, passes=1)
    low_noise = _smooth(cleaned_dem, radius=2, passes=2)

    slope_mid = _normalize(np.hypot(*np.gradient(mid)))
    low_slope_mask = np.clip(1.0 - slope_mid * 1.9, 0.0, 1.0)
    steep_mask = np.clip((slope_mid - 0.34) / 0.66, 0.0, 1.0)

    terrain_base = low_noise * (0.58 + low_slope_mask * 0.22) + fine * (0.42 - low_slope_mask * 0.12)
    micro = fine - terrain_base
    micro = _compress_signed(micro, 0.55 * low_slope_mask + 0.22 * steep_mask)
    terrain_truth = terrain_base + micro

    macro_n = _normalize(macro)
    mid_n = _normalize(mid)
    truth_n = _normalize(terrain_truth)

    ridge_detail = _normalize(np.clip(terrain_truth - mid, 0.0, None))
    drainage_detail = _normalize(np.clip(mid - terrain_truth, 0.0, None))
    local_relief = _normalize(_local_relief(terrain_truth, 1))

    geometry = np.clip(
        0.50 * macro_n
        + 0.30 * mid_n
        + 0.14 * truth_n
        + ridge_detail * 0.05
        + local_relief * 0.02
        - drainage_detail * 0.01
        - low_slope_mask * local_relief * 0.015,
        0.0,
        1.0,
    )

    zmin = float(np.min(cleaned_dem))
    zmax = float(np.max(cleaned_dem))
    elevation_range = zmax - zmin
    return {
        "rows": int(rows),
        "cols": int(cols),
        "geometry_values": np.round(geometry, 6).tolist(),
        "values": np.round(geometry, 6).tolist(),
        "zmin": round(zmin, 3),
        "zmax": round(zmax, 3),
        "viewer_vertical_scale": _viewer_vertical_scale(elevation_range),
        "viewer_default_exaggeration": _viewer_default_exaggeration(elevation_range),
        "geometry_mode": "terrain_elevation_detail_preserving",
        "geometry_smoothing_passes": 1,
    }


def _render_terrain(dem: np.ndarray) -> np.ndarray:
    base = _smooth(dem, radius=2, passes=1)
    medium = _smooth(dem, radius=5, passes=1)
    broad = _smooth(dem, radius=10, passes=1)
    mellow = _smooth(dem, radius=2, passes=2)

    slope = _normalize(np.hypot(*np.gradient(base)))
    low_slope_mask = np.clip(1.0 - slope * 1.8, 0.0, 1.0)
    steep_mask = np.clip((slope - 0.32) / 0.68, 0.0, 1.0)
    display_base = mellow * (0.52 + low_slope_mask * 0.18) + base * (0.48 - low_slope_mask * 0.10)

    elev = _normalize(display_base)

    hs_primary = _hillshade(display_base, 315.0, 44.0, 1.9)
    hs_fill = _hillshade(display_base, 32.0, 24.0, 1.0)
    hs_macro = _hillshade(medium, 255.0, 54.0, 0.95)
    hs_detail = _hillshade(base, 300.0, 38.0, 1.8)

    hill = 0.46 * hs_primary + 0.16 * hs_fill + 0.24 * hs_macro + 0.14 * hs_detail

    ridge_mask = _normalize(np.clip((display_base - medium) * 0.72 + (medium - broad) * 0.28, 0, None))
    valley_mask = _normalize(np.clip((medium - display_base) * 0.68 + (broad - medium) * 0.32, 0, None))

    relief_local = _normalize(_local_relief(display_base, 1))
    relief_mid = _normalize(_local_relief(_smooth(display_base, radius=2, passes=1), 2))

    brightness = (
        0.15
        + hill * 0.59
        + ridge_mask * 0.09
        + relief_local * 0.03
        + relief_mid * 0.04
        + elev * 0.04
        - valley_mask * 0.08
        - slope * 0.015
        - low_slope_mask * relief_local * 0.03
        - steep_mask * relief_local * 0.01
    )
    brightness = np.clip(brightness, 0.0, 1.0)

    r = 20 + brightness * 84 + ridge_mask * 10 + elev * 6
    g = 24 + brightness * 94 + ridge_mask * 8 + relief_mid * 5
    b = 13 + brightness * 42 - valley_mask * 7

    rgb = np.stack([r, g, b], axis=-1)
    rgb += ridge_mask[..., None] * np.array([10.0, 8.0, 3.0], dtype=np.float32)
    rgb -= valley_mask[..., None] * np.array([4.0, 5.0, 7.0], dtype=np.float32)

    yy, xx = np.mgrid[0:dem.shape[0], 0:dem.shape[1]]
    cx = dem.shape[1] * 0.52
    cy = dem.shape[0] * 0.42
    rx = dem.shape[1] * 0.88
    ry = dem.shape[0] * 0.84
    vignette = 1.0 - 0.06 * (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    vignette = np.clip(vignette, 0.93, 1.01)[..., None]
    rgb *= vignette

    return np.clip(rgb, 0, 255).astype(np.uint8)


def build_terrain_derivatives(dem_path: Path, out_dir: Path) -> TerrainDerivativeResult:
    arr = _sanitize_dem(_load_dem(dem_path))

    out_dir.mkdir(parents=True, exist_ok=True)

    rgb = _render_terrain(arr)
    render_path = out_dir / "terrain_render.png"
    Image.fromarray(rgb, mode="RGB").save(render_path)

    hillshade = _hillshade(_smooth(arr, radius=3, passes=2), 315.0, 42.0, 2.0)
    hillshade_path = out_dir / "hillshade.png"
    Image.fromarray(_to_uint8(hillshade), mode="L").save(hillshade_path)

    slope = np.hypot(*np.gradient(_smooth(arr, radius=2, passes=1)))
    slope_path = out_dir / "slope.png"
    Image.fromarray(_to_uint8(slope), mode="L").save(slope_path)

    local_relief = _local_relief(_smooth(arr, radius=3, passes=1), 2)
    lrm_path = out_dir / "local_relief.png"
    Image.fromarray(_to_uint8(local_relief), mode="L").save(lrm_path)

    heightmap_path = out_dir / "heightmap.json"
    heightmap_path.write_text(json.dumps(_build_heightmap_payload(arr), indent=2), encoding="utf-8")

    elev_min = float(np.min(arr))
    elev_max = float(np.max(arr))
    elev_range = elev_max - elev_min

    if elev_range > 500:
        bias = "steep mountain relief"
    elif elev_range > 250:
        bias = "rolling ridge and drainage relief"
    else:
        bias = "low-relief terrain"

    summary_path = out_dir / "terrain_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "elevation_min_m": elev_min,
                "elevation_max_m": elev_max,
                "elevation_range_m": elev_range,
                "structure_bias": bias,
                "width": int(arr.shape[1]),
                "height": int(arr.shape[0]),
                "terrain_render_path": str(render_path.name),
                "hillshade_path": str(hillshade_path.name),
                "slope_path": str(slope_path.name),
                "local_relief_path": str(lrm_path.name),
                "heightmap_path": str(heightmap_path.name),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return TerrainDerivativeResult(
        hillshade_path=render_path,
        summary_path=summary_path,
        elevation_min_m=elev_min,
        elevation_max_m=elev_max,
        structure_bias=bias,
        width=int(arr.shape[1]),
        height=int(arr.shape[0]),
    )
