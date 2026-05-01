from __future__ import annotations

import numpy as np
import pytest

from engine.decision.build import _practical_access_read, _sample_dem


BBOX = [0.0, 0.0, 1.0, 1.0]
GEOM_BBOX = (0.0, 0.0, 1.0, 1.0)
SIZE = 81


def _xy_to_lon_lat(x: int, y: int, size: int = SIZE) -> tuple[float, float]:
    lon = x / (size - 1)
    lat = 1.0 - (y / (size - 1))
    return lon, lat


def _evaluate(arr: np.ndarray, x: int, y: int, legal_class: str = "legal") -> dict:
    lon, lat = _xy_to_lon_lat(x, y, arr.shape[0])
    sample = _sample_dem(arr.astype(np.float32), BBOX, lon, lat)
    elev_norm = float((sample["elevation_m"] - float(arr.min())) / max(float(np.ptp(arr)), 1.0))
    return _practical_access_read(
        arr.astype(np.float32),
        BBOX,
        lon,
        lat,
        sample,
        elev_norm,
        GEOM_BBOX,
        legal_class,
    )


def _base_grid(size: int = SIZE) -> tuple[np.ndarray, np.ndarray]:
    axis = np.linspace(-1.0, 1.0, size, dtype=np.float32)
    xx, yy = np.meshgrid(axis, axis)
    return xx, yy


def _knife_edge_ridge(variant: int) -> tuple[np.ndarray, tuple[int, int]]:
    xx, yy = _base_grid()
    ridge = 1200 + 260 * np.exp(-((yy + 0.04 * variant) ** 2) / (0.010 + variant * 0.0015))
    side_fall = -105 * np.abs(yy) - 24 * (xx ** 2)
    length_roll = 14 * np.sin((variant + 1) * xx * 1.2)
    arr = ridge + side_fall + length_roll
    return arr.astype(np.float32), (39 + (variant % 3), 29 + (variant % 3))


def _glaciated_basin_transition(variant: int) -> tuple[np.ndarray, tuple[int, int]]:
    xx, yy = _base_grid()
    bowl = 1650 - 320 * (xx ** 2 + yy ** 2)
    wall = 150 * np.exp(-((np.sqrt(xx ** 2 + yy ** 2) - (0.62 + variant * 0.01)) ** 2) / 0.012)
    transition_shelf = 36 * np.exp(-((yy + 0.18 - variant * 0.01) ** 2) / 0.010)
    arr = bowl + wall + transition_shelf - 35 * yy
    return arr.astype(np.float32), (39 + (variant % 3), 48 + (variant % 2))


def _deep_drainage_sidehill(variant: int) -> tuple[np.ndarray, tuple[int, int]]:
    xx, yy = _base_grid()
    drainage = 1520 - 240 * np.abs(xx + 0.10 * np.sin(yy * 4.0))
    sidehill = -85 * yy + 45 * np.exp(-((yy + 0.18 - variant * 0.015) ** 2) / 0.016)
    fingers = 18 * np.sin((xx - yy) * (5.0 + variant * 0.4))
    arr = drainage + sidehill + fingers
    return arr.astype(np.float32), (29 + (variant % 4), 43 + (variant % 2))


def _plateau_edge_bench(variant: int) -> tuple[np.ndarray, tuple[int, int]]:
    xx, yy = _base_grid()
    plateau = 1900 + 18 * np.sin(xx * (2.0 + variant * 0.1))
    edge_break = -240 / (1.0 + np.exp(-(yy - (0.02 * variant)) * 13.0))
    just_inside_bench = 42 * np.exp(-((yy + 0.12 - variant * 0.01) ** 2) / 0.008)
    arr = plateau + edge_break + just_inside_bench - 20 * (xx ** 2)
    return arr.astype(np.float32), (37 + (variant % 3), 29 + (variant % 2))


def _rugged_huntable_sidehill(variant: int) -> tuple[np.ndarray, tuple[int, int]]:
    xx, yy = _base_grid()
    major_slope = 1480 - 130 * yy - 35 * xx
    roughness = (
        28 * np.sin(xx * (5.0 + variant * 0.4))
        + 22 * np.cos(yy * (6.0 + variant * 0.3))
        + 16 * np.sin((xx + yy) * (4.5 + variant * 0.2))
    )
    connected_shelf = 32 * np.exp(-((yy + 0.16 - variant * 0.01) ** 2) / 0.016)
    arr = major_slope + roughness + connected_shelf
    return arr.astype(np.float32), (36 + (variant % 3), 46 + (variant % 2))


def _isolated_summit_cap(variant: int) -> tuple[np.ndarray, tuple[int, int]]:
    xx, yy = _base_grid()
    summit = 2100 + 240 * np.exp(-((xx ** 2 + yy ** 2) / (0.020 + variant * 0.002)))
    cliff_ring = -360 * (np.sqrt(xx ** 2 + yy ** 2) ** 1.35)
    tiny_cap = 34 * np.exp(-((yy + 0.02 * (variant - 2)) ** 2) / 0.006)
    arr = summit + cliff_ring + tiny_cap
    return arr.astype(np.float32), (40 + (variant % 2), 39 + (variant % 3) - 1)


CONNECTED_CASE_BUILDERS = [
    _knife_edge_ridge,
    _glaciated_basin_transition,
    _deep_drainage_sidehill,
    _plateau_edge_bench,
    _rugged_huntable_sidehill,
]


@pytest.mark.parametrize("builder_idx", range(len(CONNECTED_CASE_BUILDERS)))
@pytest.mark.parametrize("variant", range(5))
def test_connected_huntable_terrain_does_not_trigger_hard_override(builder_idx: int, variant: int) -> None:
    arr, (x, y) = CONNECTED_CASE_BUILDERS[builder_idx](variant)
    read = _evaluate(arr, x, y)
    assert read["hard_override"] is False
    assert read["override_primary"] in {"", "Isolated Landform", "Cliff Isolation Risk"}
    assert read["confidence_cap"] in {60, 999}
    assert read["score_cap"] in {64, 999}


@pytest.mark.parametrize("variant", range(5))
def test_isolated_summit_caps_trigger_hard_override(variant: int) -> None:
    arr, (x, y) = _isolated_summit_cap(variant)
    read = _evaluate(arr, x, y)
    assert read["hard_override"] is True
    assert read["override_primary"] in {"Isolated Landform", "Cliff Isolation Risk"}
    assert "Limited Practical Access" in read["display_tags"] or "Peak Position Risk" in read["display_tags"]
    assert read["confidence_cap"] == 60
    assert read["score_cap"] == 64


def test_connected_terrain_not_penalized_worse_than_isolated():
    """
    Sanity check:
    Connected terrain should not receive stricter penalties than isolated terrain.
    """

    arr_connected, (x_c, y_c) = _rugged_huntable_sidehill(variant=2)
    read_connected = _evaluate(arr_connected, x_c, y_c)

    arr_isolated, (x_i, y_i) = _isolated_summit_cap(variant=2)
    read_isolated = _evaluate(arr_isolated, x_i, y_i)

    assert read_connected["hard_override"] is False
    assert read_isolated["hard_override"] is True

    assert read_connected["score_cap"] >= read_isolated["score_cap"]
    assert read_connected["confidence_penalty"] <= read_isolated["confidence_penalty"]