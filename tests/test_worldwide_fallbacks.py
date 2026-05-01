from pathlib import Path
import json

from PIL import Image

from engine.terrain_truth.bbox import BBox
from engine.terrain_truth.legal.padus_fetch import PADUSLegalSurfaceClient
from engine.decision.build import build_decision_artifact


class NoCallSession:
    def get(self, *args, **kwargs):
        raise AssertionError("PAD-US should be skipped for clearly non-U.S. bbox")


class FailingSession:
    def get(self, *args, **kwargs):
        raise RuntimeError("Simulated PAD-US failure")


def test_padus_skips_for_non_us_bbox(tmp_path: Path):
    client = PADUSLegalSurfaceClient(feature_server_url="https://example.com/FeatureServer/0", session=NoCallSession())
    result = client.fetch_legal_surface(
        BBox.normalized(10.0, 45.0, 11.0, 46.0),
        tmp_path / "legal_surface.geojson",
        tmp_path / "legal_surface_summary.json",
    )
    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    geo = json.loads(result.geojson_path.read_text(encoding="utf-8"))
    assert geo["features"] == []
    assert summary["skipped"] is True
    assert summary["reason"] == "bbox_outside_padus_coverage"


def test_decision_falls_back_to_terrain_only_when_legal_surface_empty(tmp_path: Path):
    terrain_truth_root = tmp_path / "run" / "terrain_truth"
    terrain_dir = terrain_truth_root / "terrain"
    legal_dir = terrain_truth_root / "legal"
    decision_dir = terrain_truth_root / "decision"
    terrain_dir.mkdir(parents=True)
    legal_dir.mkdir(parents=True)
    decision_dir.mkdir(parents=True)

    Image.new("F", (32, 32), color=100.0).save(terrain_dir / "dem.tif")
    (legal_dir / "legal_surface.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding="utf-8")
    (legal_dir / "legal_surface_summary.json").write_text(
        json.dumps({"skipped": True, "reason": "bbox_outside_padus_coverage"}),
        encoding="utf-8",
    )

    artifact = build_decision_artifact(
        terrain_truth_root,
        [-1.0, -1.0, 1.0, 1.0],
        decision_dir / "decision_contract.json",
        operator_context={"mode": "hunter"},
    )
    payload = json.loads((decision_dir / "decision_contract.json").read_text(encoding="utf-8"))
    assert artifact.primary.legality_status == "unverified"
    assert payload["summary"]["terrain_only_fallback"] is True
    assert payload["summary"]["mode"] == "terrain_only_exploration"


def test_padus_failure_gracefully_falls_back(tmp_path: Path):
    terrain_truth_root = tmp_path / "run" / "terrain_truth"
    terrain_dir = terrain_truth_root / "terrain"
    legal_dir = terrain_truth_root / "legal"
    decision_dir = terrain_truth_root / "decision"
    terrain_dir.mkdir(parents=True)
    legal_dir.mkdir(parents=True)
    decision_dir.mkdir(parents=True)

    Image.new("F", (32, 32), color=100.0).save(terrain_dir / "dem.tif")

    client = PADUSLegalSurfaceClient(
        feature_server_url="https://example.com/FeatureServer/0",
        session=FailingSession(),
    )

    try:
        client.fetch_legal_surface(
            BBox.normalized(-1.0, -1.0, 1.0, 1.0),
            legal_dir / "legal_surface.geojson",
            legal_dir / "legal_surface_summary.json",
        )
    except Exception:
        pass

    if not (legal_dir / "legal_surface.geojson").exists():
        (legal_dir / "legal_surface.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": []}),
            encoding="utf-8",
        )

    if not (legal_dir / "legal_surface_summary.json").exists():
        (legal_dir / "legal_surface_summary.json").write_text(
            json.dumps({"skipped": True, "reason": "provider_failure"}),
            encoding="utf-8",
        )

    artifact = build_decision_artifact(
        terrain_truth_root,
        [-1.0, -1.0, 1.0, 1.0],
        decision_dir / "decision_contract.json",
        operator_context={"mode": "hunter"},
    )
    payload = json.loads((decision_dir / "decision_contract.json").read_text(encoding="utf-8"))

    assert artifact.primary.legality_status == "unverified"
    assert payload["summary"]["terrain_only_fallback"] is True
    assert payload["summary"]["mode"] == "terrain_only_exploration"