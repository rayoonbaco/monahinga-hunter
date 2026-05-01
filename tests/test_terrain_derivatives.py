from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from engine.terrain_derivatives.build import build_terrain_derivatives


def test_detail_preserving_heightmap_payload(tmp_path: Path) -> None:
    x = np.linspace(-1.0, 1.0, 32, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, 32, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    dem = 180.0 + (xx * 40.0) + (yy * 25.0) + np.exp(-((xx - 0.15) ** 2 + (yy + 0.1) ** 2) * 18.0) * 55.0
    dem -= np.exp(-((xx + 0.35) ** 2 + (yy - 0.2) ** 2) * 16.0) * 35.0

    dem_path = tmp_path / "dem.tif"
    Image.fromarray(dem.astype(np.float32), mode="F").save(dem_path)

    out_dir = tmp_path / "out"
    result = build_terrain_derivatives(dem_path, out_dir)

    summary = json.loads((out_dir / "terrain_summary.json").read_text(encoding="utf-8"))
    heightmap = json.loads((out_dir / "heightmap.json").read_text(encoding="utf-8"))

    assert result.width == 32
    assert result.height == 32
    assert summary["terrain_render_path"] == "terrain_render.png"
    assert heightmap["geometry_mode"] in {"terrain_elevation_detail_preserving", "terrain_elevation_smoothed_natural"}
    assert heightmap["geometry_smoothing_passes"] == 1
    assert heightmap["viewer_default_exaggeration"] <= 1.04
    assert len(heightmap["geometry_values"]) == 32
    assert len(heightmap["geometry_values"][0]) == 32


def test_heightmap_payload_calms_low_slope_micro_noise(tmp_path: Path) -> None:
    x = np.linspace(-1.0, 1.0, 48, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, 48, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    broad = 220.0 + xx * 18.0 + yy * 12.0
    ridge = np.exp(-((xx + 0.12) ** 2 + (yy - 0.08) ** 2) * 10.0) * 24.0
    noise = (np.sin(xx * 42.0) + np.cos(yy * 39.0)) * 1.8
    dem = broad + ridge + noise

    dem_path = tmp_path / "dem_noise.tif"
    Image.fromarray(dem.astype(np.float32), mode="F").save(dem_path)

    out_dir = tmp_path / "out_noise"
    build_terrain_derivatives(dem_path, out_dir)
    heightmap = json.loads((out_dir / "heightmap.json").read_text(encoding="utf-8"))
    values = np.asarray(heightmap["geometry_values"], dtype=np.float32)

    assert float(values.std()) > 0.12
    assert float(np.abs(np.diff(values, axis=0)).mean()) < 0.06
    assert float(np.abs(np.diff(values, axis=1)).mean()) < 0.06
