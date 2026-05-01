from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from engine.decision.build import build_decision_artifact


def _write_dem(path: Path) -> None:
    arr = np.arange(400, dtype=np.uint16).reshape(20, 20)
    Image.fromarray(arr).save(path)


def _write_geojson(path: Path, features: list[dict]) -> None:
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2), encoding="utf-8")


def _make_feature(coords: list[list[list[float]]], legal_class: str = "legal", name: str = "Test Unit") -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": coords},
        "properties": {
            "monahinga_legal_class": legal_class,
            "Unit_Nm": name,
            "GIS_Acres": 100,
        },
    }


def _prep_root(tmp_path: Path) -> Path:
    root = tmp_path / "run" / "terrain_truth"
    (root / "terrain").mkdir(parents=True)
    (root / "legal").mkdir(parents=True)
    _write_dem(root / "terrain" / "dem.tif")
    return root


def test_decision_candidates_stay_inside_bbox_when_feature_crosses_edge(tmp_path: Path) -> None:
    terrain_truth_root = _prep_root(tmp_path)
    bbox = [0.0, 0.0, 1.0, 1.0]
    feature = _make_feature(
        [[
            [0.8, 0.2],
            [1.8, 0.2],
            [1.8, 0.8],
            [0.8, 0.8],
            [0.8, 0.2],
        ]],
        legal_class="legal",
        name="Edge Crossing Unit",
    )
    _write_geojson(terrain_truth_root / "legal" / "legal_surface.geojson", [feature])

    artifact = build_decision_artifact(
        terrain_truth_root,
        bbox,
        terrain_truth_root / "decision" / "decision_contract.json",
        operator_context={"mode": "hunter"},
    )

    sites = [artifact.primary] + artifact.alternates + artifact.near_misses
    assert sites
    for site in sites:
        assert 0.0 <= site.lon <= 1.0
        assert 0.0 <= site.lat <= 1.0
    assert artifact.summary["bbox_enforced"] is True
    assert artifact.summary["analysis_mode"] == "legal_hunt"


def test_decision_falls_back_to_terrain_only_when_no_verified_legal_features(tmp_path: Path) -> None:
    terrain_truth_root = _prep_root(tmp_path)
    bbox = [0.0, 0.0, 1.0, 1.0]
    feature = _make_feature(
        [[
            [0.1, 0.1],
            [0.3, 0.1],
            [0.3, 0.3],
            [0.1, 0.3],
            [0.1, 0.1],
        ]],
        legal_class="restricted",
        name="Restricted Unit",
    )
    _write_geojson(terrain_truth_root / "legal" / "legal_surface.geojson", [feature])

    artifact = build_decision_artifact(
        terrain_truth_root,
        bbox,
        terrain_truth_root / "decision" / "decision_contract.json",
        operator_context={"mode": "hunter"},
    )

    assert artifact.primary.legality_status == "unverified"
    assert artifact.summary["analysis_mode"] == "terrain_only"
    assert artifact.summary["readiness"] == "Terrain Review"
    assert any("hard analysis fence" in note for note in artifact.notes)
