from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import shutil
import time

import requests

from .bbox import BBox
from .contract import (
    TerrainArtifact,
    TerrainDerivativeArtifact,
    VegetationArtifact,
    LegalArtifact,
    TerrainTruthContract,
    CommandSurfaceArtifact,
)
from .terrain.dem_fetch import AutoDEMClient, bbox_looks_like_usa
from .legal.padus_fetch import PADUSLegalSurfaceClient
from engine.terrain_derivatives.build import build_terrain_derivatives
from engine.decision.build import build_decision_artifact
from engine.command_surface.render import render_command_surface
from engine.adapters.monahinga_run_folder_adapter import write_monahinga_adapter_request
from engine.wildlife_atmosphere import build_wildlife_atmosphere
from hunter_core.engine import run_hunter_core


NLCD_IMAGE_SERVER_URL = (
    "https://di-nlcd.img.arcgis.com/arcgis/rest/services/"
    "USA_NLCD_Annual_LandCover/ImageServer/getSamples"
)

NLCD_GROUP_MAP: dict[int, str] = {
    11: "water",
    12: "water",
    21: "open",
    22: "open",
    23: "open",
    24: "open",
    31: "open",
    41: "forest",
    42: "forest",
    43: "forest",
    51: "shrub",
    52: "shrub",
    71: "open",
    72: "open",
    73: "open",
    74: "open",
    81: "open",
    82: "open",
    90: "shrub",
    95: "shrub",
}


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_ROOT = PROJECT_ROOT / ".monahinga_cache"


def _cache_enabled() -> bool:
    return os.getenv("MONAHINGA_DISABLE_CACHE", "0").strip().lower() not in {"1", "true", "yes", "on"}


def _use_live_nlcd() -> bool:
    """Default to fast vegetation classification unless live NLCD is explicitly enabled."""
    return os.getenv("MONAHINGA_USE_NLCD", "0").strip().lower() in {"1", "true", "yes", "on"}


def _cache_key(prefix: str, bbox: BBox, *, width: int | None = None, height: int | None = None) -> str:
    payload = {
        "bbox": [round(float(v), 6) for v in bbox.as_list()],
        "width": width,
        "height": height,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _bbox_center(bbox: BBox) -> tuple[float, float]:
    min_lon, min_lat, max_lon, max_lat = bbox.as_list()
    return ((min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0)


def _bbox_sample_points(bbox: BBox) -> list[tuple[float, float]]:
    min_lon, min_lat, max_lon, max_lat = bbox.as_list()
    inset_x = (max_lon - min_lon) * 0.1
    inset_y = (max_lat - min_lat) * 0.1

    return [
        ((min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0),
        (min_lon + inset_x, min_lat + inset_y),
        (min_lon + inset_x, max_lat - inset_y),
        (max_lon - inset_x, min_lat + inset_y),
        (max_lon - inset_x, max_lat - inset_y),
    ]


def _coerce_nlcd_code(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _terrain_heuristic_classification(bbox: BBox) -> tuple[str, list[str], str]:
    min_lon, min_lat, max_lon, max_lat = bbox.as_list()
    area = abs((max_lon - min_lon) * (max_lat - min_lat))

    if area < 0.0005:
        return (
            "forest",
            ["Heuristic fallback: small, dense terrain window biased toward forest cover."],
            "terrain_heuristic",
        )

    if area < 0.002:
        return (
            "shrub",
            ["Heuristic fallback: mid-scale terrain window biased toward shrub or mixed cover."],
            "terrain_heuristic",
        )

    return (
        "open",
        ["Heuristic fallback: larger terrain window biased toward open cover."],
        "terrain_heuristic",
    )


def fetch_nlcd_center_classification(
    bbox: BBox,
    *,
    session: requests.Session | None = None,
    timeout: int = 10,
    retries: int = 2,
) -> tuple[str, list[str], str]:
    if not _use_live_nlcd():
        heuristic_class, heuristic_notes, heuristic_provider = _terrain_heuristic_classification(bbox)
        return (
            heuristic_class,
            [
                "Fast vegetation mode: live NLCD sampling skipped for launch speed. Set MONAHINGA_USE_NLCD=1 to enable live vegetation samples.",
                *heuristic_notes,
            ],
            heuristic_provider,
        )

    if not bbox_looks_like_usa(bbox):
        return (
            "unknown",
            ["NLCD skipped: outside U.S. coverage area."],
            "nlcd_unavailable",
        )

    sess = session or requests.Session()
    sample_points = _bbox_sample_points(bbox)

    collected_classes: list[str] = []
    notes: list[str] = []
    last_error: Exception | None = None

    for lon, lat in sample_points:
        params = {
            "f": "json",
            "geometry": f"{lon},{lat}",
            "geometryType": "esriGeometryPoint",
            "sr": "4326",
            "returnFirstValueOnly": "true",
            "sampleCount": "1",
        }

        for attempt in range(1, retries + 1):
            try:
                resp = sess.get(NLCD_IMAGE_SERVER_URL, params=params, timeout=timeout)
                resp.raise_for_status()
                payload = resp.json()

                samples = payload.get("samples") or []
                if not samples:
                    continue

                sample = samples[0] or {}
                raw_value = sample.get("value")
                code = _coerce_nlcd_code(raw_value)

                if code is None:
                    continue

                classification = NLCD_GROUP_MAP.get(code, "open")
                collected_classes.append(classification)
                notes.append(f"Sample ({lon:.4f},{lat:.4f}) -> {classification} on attempt {attempt}.")
                break

            except Exception as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(0.3)

    if collected_classes:
        majority = max(set(collected_classes), key=collected_classes.count)
        notes.append(f"NLCD multi-sample majority={majority}")
        return majority, notes, "nlcd_annual"

    heuristic_class, heuristic_notes, heuristic_provider = _terrain_heuristic_classification(bbox)
    notes.append(f"NLCD failed after retries: {last_error}")
    notes.extend(heuristic_notes)
    return heuristic_class, notes, heuristic_provider


def _fetch_dem_cached(bbox: BBox, out_path: Path, *, width: int, height: int) -> tuple[object, bool]:
    cache_dir = CACHE_ROOT / _cache_key("dem", bbox, width=width, height=height)
    cache_dem = cache_dir / "dem.tif"
    cache_meta = cache_dir / "dem_meta.json"

    if _cache_enabled() and cache_dem.exists() and cache_meta.exists():
        meta = _read_json(cache_meta)
        _copy_file(cache_dem, out_path)
        return (
            type("CachedDEMFetchResult", (), {
                "path": out_path,
                "pixel_dimensions": meta.get("pixel_dimensions") or [width, height],
                "provider": f"{meta.get('provider', 'cached_dem')}_cache",
                "format": meta.get("format", "image/tiff"),
            })(),
            True,
        )

    dem_client = AutoDEMClient()
    dem = dem_client.fetch_dem(bbox, out_path, width=width, height=height)
    if _cache_enabled():
        cache_dir.mkdir(parents=True, exist_ok=True)
        _copy_file(out_path, cache_dem)
        _write_json(cache_meta, {
            "provider": dem.provider,
            "pixel_dimensions": dem.pixel_dimensions,
            "format": dem.format,
            "bbox": bbox.as_list(),
            "width": width,
            "height": height,
        })
    return dem, False


def _fetch_legal_cached(bbox: BBox, out_geojson_path: Path, out_summary_path: Path) -> tuple[object, bool]:
    cache_dir = CACHE_ROOT / _cache_key("legal", bbox)
    cache_geojson = cache_dir / "legal_surface.geojson"
    cache_summary = cache_dir / "legal_surface_summary.json"

    if _cache_enabled() and cache_geojson.exists() and cache_summary.exists():
        summary = _read_json(cache_summary)
        _copy_file(cache_geojson, out_geojson_path)
        _copy_file(cache_summary, out_summary_path)
        return (
            type("CachedPADUSFetchResult", (), {
                "geojson_path": out_geojson_path,
                "summary_path": out_summary_path,
                "legal_feature_count": int(summary.get("legal_feature_count") or 0),
                "restricted_feature_count": int(summary.get("restricted_feature_count") or 0),
                "unknown_feature_count": int(summary.get("unknown_feature_count") or 0),
                "provider": "padus_arcgis_cache",
            })(),
            True,
        )

    padus_client = PADUSLegalSurfaceClient()
    legal = padus_client.fetch_legal_surface(bbox, out_geojson_path, out_summary_path)
    if _cache_enabled():
        cache_dir.mkdir(parents=True, exist_ok=True)
        _copy_file(out_geojson_path, cache_geojson)
        _copy_file(out_summary_path, cache_summary)
    return legal, False


def _build_derivatives_cached(dem_path: Path, out_dir: Path, bbox: BBox, *, width: int, height: int):
    cache_dir = CACHE_ROOT / _cache_key("derivatives", bbox, width=width, height=height)
    cache_summary = cache_dir / "terrain_summary.json"
    derivative_names = [
        "terrain_render.png",
        "hillshade.png",
        "slope.png",
        "local_relief.png",
        "heightmap.json",
        "terrain_summary.json",
    ]

    if _cache_enabled() and cache_summary.exists() and all((cache_dir / name).exists() for name in derivative_names):
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in derivative_names:
            _copy_file(cache_dir / name, out_dir / name)
        summary = _read_json(out_dir / "terrain_summary.json")
        return (
            type("CachedTerrainDerivativeResult", (), {
                "hillshade_path": out_dir / (summary.get("terrain_render_path") or "terrain_render.png"),
                "summary_path": out_dir / "terrain_summary.json",
                "elevation_min_m": float(summary.get("elevation_min_m") or 0.0),
                "elevation_max_m": float(summary.get("elevation_max_m") or 0.0),
                "structure_bias": str(summary.get("structure_bias") or "unknown terrain"),
                "width": int(summary.get("width") or width),
                "height": int(summary.get("height") or height),
            })(),
            True,
        )

    derivatives = build_terrain_derivatives(dem_path, out_dir)
    if _cache_enabled():
        cache_dir.mkdir(parents=True, exist_ok=True)
        for name in derivative_names:
            src = out_dir / name
            if src.exists():
                _copy_file(src, cache_dir / name)
    return derivatives, False


def _fetch_vegetation_cached(bbox: BBox) -> tuple[str, list[str], str, bool]:
    mode = "live_nlcd" if _use_live_nlcd() else "fast_heuristic"
    cache_dir = CACHE_ROOT / _cache_key(f"vegetation_{mode}", bbox)
    cache_payload = cache_dir / "vegetation.json"

    if _cache_enabled() and cache_payload.exists():
        payload = _read_json(cache_payload)
        notes = list(payload.get("notes") or [])
        notes.insert(0, "Vegetation cache hit: reused prior cover classification.")
        return str(payload.get("classification") or "unknown"), notes, str(payload.get("provider") or "unknown"), True

    classification, notes, provider = fetch_nlcd_center_classification(bbox)
    if _cache_enabled():
        _write_json(cache_payload, {
            "classification": classification,
            "notes": notes,
            "provider": provider,
            "bbox": bbox.as_list(),
            "mode": mode,
        })
    return classification, notes, provider, False


def build_terrain_truth_run(
    bbox: BBox,
    run_root: Path,
    *,
    width: int = 1024,
    height: int = 1024,
    operator_context: dict | None = None,
) -> TerrainTruthContract:
    operator_context = dict(operator_context or {})

    terrain_dir = run_root / "terrain_truth" / "terrain"
    legal_dir = run_root / "terrain_truth" / "legal"
    decision_dir = run_root / "terrain_truth" / "decision"
    derivative_dir = run_root / "terrain_truth" / "terrain_derivatives"
    terrain_dir.mkdir(parents=True, exist_ok=True)
    legal_dir.mkdir(parents=True, exist_ok=True)
    decision_dir.mkdir(parents=True, exist_ok=True)
    derivative_dir.mkdir(parents=True, exist_ok=True)

    provider_status = {
        "terrain": "unknown",
        "legal": "unknown",
        "vegetation": "unknown",
        "messages": [],
    }

    try:
        dem, dem_cache_hit = _fetch_dem_cached(bbox, terrain_dir / "dem.tif", width=width, height=height)
        provider_status["terrain"] = "cache" if dem_cache_hit else "ok"
        if dem_cache_hit:
            provider_status["messages"].append("Terrain cache hit: reused DEM instead of refetching elevation data.")
    except Exception as e:
        provider_status["terrain"] = "failed"
        provider_status["messages"].append(f"Terrain provider failed: {str(e)}")
        raise

    try:
        legal, legal_cache_hit = _fetch_legal_cached(
            bbox,
            legal_dir / "legal_surface.geojson",
            legal_dir / "legal_surface_summary.json",
        )

        if legal.legal_feature_count == 0:
            provider_status["legal"] = "empty_cache" if legal_cache_hit else "empty"
            provider_status["messages"].append("Legal surface returned no accessible features.")
        else:
            provider_status["legal"] = "cache" if legal_cache_hit else "ok"
        if legal_cache_hit:
            provider_status["messages"].append("Legal cache hit: reused PAD-US legal surface instead of querying ArcGIS.")

    except Exception as e:
        provider_status["legal"] = "failed"
        provider_status["messages"].append(f"Legal provider failed: {str(e)}")

        legal = PADUSLegalSurfaceClient().empty_result(
            bbox,
            legal_dir / "legal_surface.geojson",
            legal_dir / "legal_surface_summary.json",
        )

    terrain_derivatives, derivative_cache_hit = _build_derivatives_cached(
        dem.path,
        derivative_dir,
        bbox,
        width=width,
        height=height,
    )
    if derivative_cache_hit:
        provider_status["messages"].append("Terrain derivative cache hit: reused rendered terrain layers and heightmap JSON.")

    vegetation_classification, vegetation_notes, vegetation_provider, vegetation_cache_hit = _fetch_vegetation_cached(bbox)
    if vegetation_cache_hit:
        provider_status["messages"].append("Vegetation cache hit: reused cover classification.")
    vegetation = VegetationArtifact(
        provider=vegetation_provider,
        classification=vegetation_classification,
        notes=vegetation_notes,
    )

    operator_context["vegetation_classification"] = vegetation_classification
    operator_context["vegetation_provider"] = vegetation_provider
    operator_context["wildlife_atmosphere"] = build_wildlife_atmosphere(
        bbox,
        vegetation_classification=vegetation_classification,
    )

    operator_context["hunt_intelligence"] = run_hunter_core(
        bbox=bbox.as_list(),
        terrain_summary_path=terrain_derivatives.summary_path,
        heightmap_path=derivative_dir / "heightmap.json",
        vegetation_classification=vegetation_classification,
        wind_direction=operator_context.get("wind_direction", ""),
        notes=operator_context.get("notes", ""),
        mode=operator_context.get("mode", "hunter"),
    )

    provider_status["messages"].append(
        "Hunter core generated ranked zone intelligence before the decision artifact was built."
    )

    if vegetation_provider in {"nlcd_annual", "terrain_heuristic"}:
        provider_status["vegetation"] = "ok" if vegetation_provider == "nlcd_annual" else "degraded"
    else:
        provider_status["vegetation"] = "degraded"

    provider_status["messages"].extend(vegetation_notes)

    decision = build_decision_artifact(
        run_root / "terrain_truth",
        bbox.as_list(),
        decision_dir / "decision_contract.json",
        operator_context=operator_context,
    )

    contract = TerrainTruthContract(
        run_id=run_root.name,
        bbox=bbox.as_list(),
        crs="EPSG:4326",
        terrain=TerrainArtifact(
            provider=dem.provider,
            path=str(dem.path.relative_to(run_root)),
            format=dem.format,
            pixel_dimensions=dem.pixel_dimensions,
        ),
        terrain_derivatives=TerrainDerivativeArtifact(
            hillshade_path=str(terrain_derivatives.hillshade_path.relative_to(run_root)),
            summary_path=str(terrain_derivatives.summary_path.relative_to(run_root)),
            structure_bias=terrain_derivatives.structure_bias,
            elevation_min_m=terrain_derivatives.elevation_min_m,
            elevation_max_m=terrain_derivatives.elevation_max_m,
        ),
        vegetation=vegetation,
        legal_surface=LegalArtifact(
            provider=legal.provider,
            path=str(legal.geojson_path.relative_to(run_root)),
            summary_path=str(legal.summary_path.relative_to(run_root)),
            legal_feature_count=legal.legal_feature_count,
            restricted_feature_count=legal.restricted_feature_count,
            unknown_feature_count=legal.unknown_feature_count,
        ),
        decision=decision,
        command_surface=CommandSurfaceArtifact(path=""),
        notes=[
            "Terrain layer fetched from the preferred real provider path.",
            "Vegetation layer now uses multi-sample NLCD with terrain heuristic fallback.",
            "Wildlife atmosphere layer generated BBOX-driven species and method context without touching the 3D terrain core.",
            "Decision layer consumed DEM-derived terrain structure and legal gating.",
            "Command surface rendered a terrain-first operator view with intelligence controls.",
            f"Provider status: terrain={provider_status['terrain']}, legal={provider_status['legal']}, vegetation={provider_status['vegetation']}",
            *provider_status["messages"],
            "Legal land output is an aid, not final authority. Always verify land access, ownership, boundaries, and hunting legality in the real world before hunting.",
        ],
        operator_context=operator_context,
    )

    command_surface_path = render_command_surface(run_root, contract)
    contract.command_surface = CommandSurfaceArtifact(path=str(command_surface_path.relative_to(run_root)))
    contract.write_json(run_root / "terrain_truth" / "terrain_contract.json")

    wildlife_request_path = write_monahinga_adapter_request(
        run_root=run_root / "terrain_truth",
        bbox=bbox.as_list(),
        out_path=run_root / "terrain_truth" / "wildlife" / "wildlife_adapter_request.json",
        operator_context=operator_context,
    )

    print(f"[wildlife-adapter] wrote {wildlife_request_path}")

    return contract


def main() -> None:
    bbox = BBox(-78.102209, 41.891092, -78.074925, 41.909235)
    run_root = Path("runs") / f"run_{int(time.time())}"
    run_root.mkdir(parents=True, exist_ok=True)
    contract = build_terrain_truth_run(
        bbox,
        run_root,
        operator_context={"wind_direction": "NW", "notes": "", "mode": "hunter"},
    )
    print(
        json.dumps(
            {
                "run_id": contract.run_id,
                "terrain": contract.terrain.path,
                "decision": contract.decision.path,
                "command_surface": contract.command_surface.path,
                "vegetation": contract.vegetation.classification,
                "vegetation_provider": contract.vegetation.provider,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
