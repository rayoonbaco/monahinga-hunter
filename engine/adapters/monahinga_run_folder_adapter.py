from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import Any


@dataclass
class MonahingaAdapterRequest:
    adapter_version: str
    source_system: str
    source_run_root: str
    bbox_authority: dict[str, Any]
    terrain_bundle: dict[str, Any]
    derived_layers: dict[str, Any]
    legal_context: dict[str, Any]
    conditions: dict[str, Any]
    pressure_proxies: dict[str, Any]
    metadata: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _resolve_dem_path(run_root: Path, terrain_contract: dict[str, Any]) -> tuple[str | None, str | None]:
    rel = (((terrain_contract.get("terrain") or {}).get("path")) or "").strip()
    if rel:
        candidate = run_root / rel
        if candidate.exists():
            return str(candidate), candidate.name

    terrain_dir = run_root / "terrain"
    for name in ("dem.tif", "usgs_dem.tif", "copernicus_dem.tif"):
        candidate = terrain_dir / name
        if candidate.exists():
            return str(candidate), name

    tif_files = sorted(terrain_dir.glob("*.tif")) if terrain_dir.exists() else []
    if tif_files:
        return str(tif_files[0]), tif_files[0].name

    return None, None


def _find_legal_surface_path(run_root: Path) -> str | None:
    candidate = run_root / "legal" / "legal_surface.geojson"
    if candidate.exists():
        return str(candidate)
    return None


def build_monahinga_adapter_request(
    run_root: str | Path,
    bbox: list[float],
    operator_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    operator_context = operator_context or {}
    run_root = Path(run_root)

    terrain_contract_path = run_root / "terrain_contract.json"
    terrain_contract = _read_json(terrain_contract_path)

    dem_path, dem_source = _resolve_dem_path(run_root, terrain_contract)
    legal_surface_path = _find_legal_surface_path(run_root)

    request = MonahingaAdapterRequest(
        adapter_version="1.0.0",
        source_system="MONAHINGA",
        source_run_root=str(run_root),
        bbox_authority={
            "min_lon": bbox[0],
            "min_lat": bbox[1],
            "max_lon": bbox[2],
            "max_lat": bbox[3],
            "authority": "terrain_truth_bbox",
            "required": True,
        },
        terrain_bundle={
            "terrain_contract_path": str(terrain_contract_path) if terrain_contract_path.exists() else None,
            "dem_path": dem_path,
            "dem_source": dem_source,
            "cell_size_m": None,
            "crs": None,
            "required": True,
        },
        derived_layers={
            "precomputed": {
                "slope": None,
                "aspect": None,
                "local_relief": None,
                "medium_relief": None,
                "relative_elevation": None,
                "ridge_tendency": None,
                "valley_tendency": None,
                "bench_index": None,
                "drainage_index": None,
                "thermal_cover": None,
                "road_exposure": None,
                "human_pressure": None,
            },
            "runtime_derivable": {
                "slope": True,
                "aspect": True,
                "local_relief": True,
                "ridge_tendency_proxy": True,
                "bench_index_proxy": True,
                "edge_proximity": True,
                "terrain_shape_tags": True,
            },
        },
        legal_context={
            "legal_features_path": legal_surface_path,
            "features_inline": None,
            "required_feature_property": "monahinga_legal_class",
            "allowed_hunt_class": "legal",
            "coverage_inside_bbox_pct": None,
            "ground_name_fields": ["Unit_Nm", "MngNm_Desc", "ManagerName", "BndryName"],
            "required": True,
        },
        conditions={
            "wind_direction_deg": None,
            "wind_direction_label": str(operator_context.get("wind_direction") or "") or None,
            "wind_speed_mph": operator_context.get("wind_speed_mph"),
            "time_of_day": operator_context.get("time_of_day"),
            "hours_before_sunset": operator_context.get("hours_before_sunset"),
            "temperature_f": operator_context.get("temperature_f"),
            "pressure_state": operator_context.get("pressure_state"),
            "input_condition_quality": "partial",
        },
        pressure_proxies={
            "edge_exposure": None,
            "interior_security": None,
            "verified_legal_access": None,
            "boundary_hunt_risk": None,
            "road_exposure": None,
            "human_pressure": None,
            "proxy_quality": "minimal",
        },
        metadata={
            "run_id": run_root.name,
            "generated_at": None,
            "viewer_context_available": True,
            "selected_box_label": operator_context.get("selected_box_label"),
            "operator_notes": operator_context.get("notes"),
            "source_artifacts": [
                "terrain_contract.json",
                "terrain/*.tif",
                "legal/legal_surface.geojson",
                "viewer status fields",
            ],
        },
    )
    return asdict(request)


def write_monahinga_adapter_request(
    run_root: str | Path,
    bbox: list[float],
    out_path: str | Path,
    operator_context: dict[str, Any] | None = None,
) -> Path:
    payload = build_monahinga_adapter_request(run_root, bbox, operator_context)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    example = build_monahinga_adapter_request(
        run_root=".",
        bbox=[-78.1022, 41.8911, -78.0749, 41.9092],
        operator_context={"wind_direction": "SW"},
    )
    print(json.dumps(example, indent=2))
