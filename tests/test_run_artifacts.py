from pathlib import Path
import json


def _find_latest_run_with_wildlife(runs_dir: Path) -> Path:
    run_dirs = sorted(
        [p for p in runs_dir.iterdir() if p.is_dir() and p.name.startswith("run_")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for run in run_dirs:
        wildlife_path = run / "terrain_truth" / "wildlife" / "wildlife_adapter_request.json"
        if wildlife_path.exists():
            return run

    raise AssertionError("No run with wildlife adapter output found")


def test_run_artifacts_exist_after_real_run():
    runs_dir = Path("runs")
    assert runs_dir.exists(), "runs directory does not exist"

    latest_run = _find_latest_run_with_wildlife(runs_dir)

    dem_path = latest_run / "terrain_truth" / "terrain" / "dem.tif"
    wildlife_path = latest_run / "terrain_truth" / "wildlife" / "wildlife_adapter_request.json"
    command_surface_path = latest_run / "command_surface" / "index.html"
    terrain_contract_path = latest_run / "terrain_truth" / "terrain_contract.json"
    decision_contract_path = latest_run / "terrain_truth" / "decision" / "decision_contract.json"

    assert dem_path.exists(), f"DEM file missing: {dem_path}"
    assert wildlife_path.exists(), f"Wildlife adapter file missing: {wildlife_path}"
    assert command_surface_path.exists(), f"Command surface missing: {command_surface_path}"
    assert terrain_contract_path.exists(), f"Terrain contract missing: {terrain_contract_path}"
    assert decision_contract_path.exists(), f"Decision contract missing: {decision_contract_path}"


def test_wildlife_bbox_consistency_with_run():
    runs_dir = Path("runs")
    assert runs_dir.exists()

    latest_run = _find_latest_run_with_wildlife(runs_dir)

    wildlife_file = latest_run / "terrain_truth" / "wildlife" / "wildlife_adapter_request.json"
    assert wildlife_file.exists()

    data = json.loads(wildlife_file.read_text(encoding="utf-8"))

    assert "bbox_authority" in data
    bbox = data["bbox_authority"]

    assert isinstance(bbox, dict)

    required_keys = ["min_lon", "min_lat", "max_lon", "max_lat"]
    for key in required_keys:
        assert key in bbox, f"Missing {key} in bbox_authority"
        assert isinstance(bbox[key], (int, float)), f"{key} must be numeric"

    assert bbox["min_lon"] < bbox["max_lon"]
    assert bbox["min_lat"] < bbox["max_lat"]


def test_latest_run_preserves_vegetation_and_decision_summary():
    runs_dir = Path("runs")
    assert runs_dir.exists()

    latest_run = _find_latest_run_with_wildlife(runs_dir)

    terrain_contract_file = latest_run / "terrain_truth" / "terrain_contract.json"
    decision_contract_file = latest_run / "terrain_truth" / "decision" / "decision_contract.json"

    assert terrain_contract_file.exists(), f"Terrain contract missing: {terrain_contract_file}"
    assert decision_contract_file.exists(), f"Decision contract missing: {decision_contract_file}"

    terrain_data = json.loads(terrain_contract_file.read_text(encoding="utf-8"))
    decision_data = json.loads(decision_contract_file.read_text(encoding="utf-8"))

    assert "vegetation" in terrain_data, "Terrain contract missing vegetation section"
    vegetation = terrain_data["vegetation"]
    assert isinstance(vegetation, dict), "Vegetation section must be an object"
    assert "classification" in vegetation, "Vegetation classification missing"
    assert "provider" in vegetation, "Vegetation provider missing"

    assert "summary" in decision_data, "Decision contract missing summary"
    summary = decision_data["summary"]
    assert isinstance(summary, dict), "Decision summary must be an object"
    assert "vegetation_classification" in summary, "Decision summary missing vegetation classification"