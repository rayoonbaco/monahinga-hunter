from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import os
import shutil
import tempfile
import threading
import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from engine.launch_surface import render_home_page
from engine.launch_surface.instructions_page import render_instructions_page
from engine.terrain_truth.bbox import BBox
from engine.terrain_truth.orchestrator import build_terrain_truth_run
from engine.terrain_truth.legal.padus_fetch import PADUSLegalSurfaceClient
from engine.wildlife_atmosphere import build_wildlife_atmosphere
from engine.live.wind import OpenMeteoWindClient, format_observed_at, wind_arrow_heading_deg


# Run system
RUN_COUNT = 0
MAX_RUNS = 6  # 1 free + 5 paid


DEFAULT_BBOX = BBox(
    min_lon=-104.40645,
    min_lat=44.495664,
    max_lon=-104.357929,
    max_lat=44.510845,
)


def _bbox_cache_key(bbox: BBox) -> str:
    payload = [round(float(v), 6) for v in bbox.as_list()]
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]
    return f"bbox_{digest}"


def _preflight_cache_paths(bbox: BBox) -> tuple[Path, Path]:
    cache_dir = RUNS_DIR / "_padus_preflight_cache" / _bbox_cache_key(bbox)
    return cache_dir / "legal_surface.geojson", cache_dir / "legal_surface_summary.json"


def _prewarm_default_bbox() -> None:
    """Build default terrain and PAD-US cache in the background after startup.

    This makes the default BBox much faster after Render boots. It does not
    increment RUN_COUNT, does not touch payment limits, and does not change the
    public launch flow. If prewarm fails, the app still starts normally.
    """
    try:
        if os.getenv("MONAHINGA_DISABLE_PREWARM", "0").strip().lower() in {"1", "true", "yes", "on"}:
            print("[prewarm] skipped because MONAHINGA_DISABLE_PREWARM is enabled")
            return

        time.sleep(2.0)
        prewarm_root = RUNS_DIR / "_prewarm" / "default_bbox"

        if prewarm_root.exists():
            shutil.rmtree(prewarm_root, ignore_errors=True)

        print("[prewarm] starting default BBox PAD-US + terrain cache build")

        # Fill the PAD-US preflight cache first. The visible run still enforces
        # the same huntability rule, but it can reuse this result instead of
        # making the user wait for the first PAD-US lookup.
        _enforce_padus_huntability_preflight(DEFAULT_BBOX)

        # Fill DEM, legal surface, derivative, vegetation, decision, and command
        # surface caches through the existing orchestrator path.
        build_terrain_truth_run(
            DEFAULT_BBOX,
            prewarm_root,
            width=512,
            height=512,
            operator_context={
                "wind_direction": "",
                "notes": "Startup prewarm cache build.",
                "mode": "hunter",
                "selected_species": "default",
                "target_species": "default",
            },
        )

        print("[prewarm] default BBox cache build complete")

    except Exception as exc:
        print(f"[prewarm] default BBox cache build failed: {type(exc).__name__}: {exc}")


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

app = FastAPI(title="Monahinga", version="1.0.0")
RUNS_DIR = Path(__file__).resolve().parents[2] / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/runs", StaticFiles(directory=RUNS_DIR), name="runs")


class RunRequest(BaseModel):
    min_lon: float = Field(...)
    min_lat: float = Field(...)
    max_lon: float = Field(...)
    max_lat: float = Field(...)
    width: int = Field(768, ge=256, le=2048)
    height: int = Field(768, ge=256, le=2048)
    wind_direction: str = Field(default="")
    notes: str = Field(default="")
    mode: str = Field(default="hunter")
    selected_species: str = Field(default="default")


class TerrainValidationError(RuntimeError):
    """Raised when generated terrain files exist but are not physically usable."""


class HuntabilityGuardrailError(ValueError):
    """Raised when the selected box is obviously urban or not suitable for hunting review."""


MAJOR_URBAN_GUARDRAILS = [
    ("Cleveland, OH", 41.4993, -81.6944, 14.0),
    ("Pittsburgh, PA", 40.4406, -79.9959, 14.0),
    ("Philadelphia, PA", 39.9526, -75.1652, 18.0),
    ("Erie, PA", 42.1292, -80.0851, 10.0),
    ("Harrisburg, PA", 40.2732, -76.8867, 9.0),
    ("Buffalo, NY", 42.8864, -78.8784, 14.0),
    ("Columbus, OH", 39.9612, -82.9988, 16.0),
    ("Cincinnati, OH", 39.1031, -84.5120, 14.0),
    ("Detroit, MI", 42.3314, -83.0458, 18.0),
    ("New York City, NY", 40.7128, -74.0060, 25.0),
]


def _distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 3958.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(min(1, math.sqrt(a)))


def _enforce_huntability_guardrail(bbox: BBox) -> None:
    """Block obvious city/urban boxes before the app creates a fake hunting read.

    This is a conservative emergency trust guardrail. It catches major-city boxes
    that should never be labeled huntable. Natural/legal hunting land still runs.
    """
    center_lat = (float(bbox.min_lat) + float(bbox.max_lat)) / 2
    center_lon = (float(bbox.min_lon) + float(bbox.max_lon)) / 2

    for city, city_lat, city_lon, radius_miles in MAJOR_URBAN_GUARDRAILS:
        if _distance_miles(center_lat, center_lon, city_lat, city_lon) <= radius_miles:
            raise HuntabilityGuardrailError(
                f"Selected box appears to be inside or too close to the {city} urban area. "
                "Monahinga is for natural/legal hunting terrain, not downtown, suburbs, parking lots, or city blocks. "
                "Move the box onto actual public/legal hunting ground and verify access before using any recommendation."
            )



HUNTING_ELIGIBLE_PADUS_TOKENS = [
    "state game land",
    "game land",
    "wildlife management",
    "wildlife area",
    "wildlife refuge",
    "fish and wildlife",
    "national forest",
    "forest service",
    "blm",
    "bureau of land management",
    "state forest",
    "hunt",
    "hunting",
]

NON_HUNTABLE_PADUS_TOKENS = [
    "city park",
    "county park",
    "municipal park",
    "urban park",
    "neighborhood park",
    "school",
    "cemetery",
    "parking",
    "golf",
    "zoo",
    "museum",
    "downtown",
    "recreation center",
    "playground",
]


def _padus_props_text(props: dict) -> str:
    values = []
    for key, value in props.items():
        if isinstance(value, (str, int, float)) and value is not None:
            values.append(str(value))
    return " ".join(values).lower()


def _padus_feature_is_hunting_eligible(props: dict) -> bool:
    """Emergency trust rule: public/open is not enough for a huntable 3D run.

    PAD-US can include city parks and other public protected lands. For Monahinga,
    the run should continue only when the PAD-US feature looks like hunting-eligible
    public land, such as BLM, National Forest, State Forest, State Game Land, or
    wildlife-management land. Anything merely public/park-like stays blocked.
    """
    cls = str(props.get("monahinga_legal_class") or "").strip().lower()
    if cls != "legal":
        return False

    text = _padus_props_text(props)
    if any(token in text for token in NON_HUNTABLE_PADUS_TOKENS):
        return False
    return any(token in text for token in HUNTING_ELIGIBLE_PADUS_TOKENS)


def _enforce_padus_huntability_preflight(bbox: BBox) -> None:
    """Run PAD-US before expensive terrain generation and fail closed.

    This prevents city/non-huntable boxes from producing a polished but misleading
    3D hunting scene. Frontend catches this 400 and shows the NOT HUNTABLE LAND modal.

    Speed note:
    - Results are cached by exact BBox.
    - Startup prewarm fills the default BBox cache.
    - The same huntability test still runs on cached features.
    """
    cached_geojson_path, cached_summary_path = _preflight_cache_paths(bbox)

    if cached_geojson_path.exists() and cached_summary_path.exists():
        geojson_path = cached_geojson_path
        summary_path = cached_summary_path
        legal_feature_count = None
    else:
        preflight_root = RUNS_DIR / "_padus_preflight"
        preflight_root.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="padus_", dir=str(preflight_root)) as tmp:
            tmp_root = Path(tmp)
            geojson_path = tmp_root / "legal_surface.geojson"
            summary_path = tmp_root / "legal_surface_summary.json"
            legal = PADUSLegalSurfaceClient().fetch_legal_surface(bbox, geojson_path, summary_path)
            legal_feature_count = int(getattr(legal, "legal_feature_count", 0) or 0)

            cached_geojson_path.parent.mkdir(parents=True, exist_ok=True)
            if geojson_path.exists():
                shutil.copy2(geojson_path, cached_geojson_path)
            if summary_path.exists():
                shutil.copy2(summary_path, cached_summary_path)

            geojson_path = cached_geojson_path
            summary_path = cached_summary_path

    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    except Exception:
        summary = {}

    if summary.get("configured") is False:
        raise HuntabilityGuardrailError(
            "PAD-US huntability check is not configured, so Monahinga cannot safely verify this BBox as huntable land. "
            "Please select another BBox over real natural/legal hunting ground after PAD-US is configured."
        )

    if summary.get("skipped"):
        raise HuntabilityGuardrailError(
            "PAD-US huntability check does not cover this BBox. Please select another BBox over real natural/legal hunting ground."
        )

    if legal_feature_count is None:
        legal_feature_count = int(summary.get("legal_feature_count") or 0)

    if int(legal_feature_count or 0) <= 0:
        raise HuntabilityGuardrailError(
            "PAD-US found no verified hunting-eligible legal land inside this BBox. "
            "Please select another BBox over real natural/legal hunting ground."
        )

    try:
        feature_collection = json.loads(geojson_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HuntabilityGuardrailError(
            "PAD-US huntability check could not read the legal surface safely. "
            "Please select another BBox over real natural/legal hunting ground."
        ) from exc

    eligible = 0
    for feat in feature_collection.get("features", []):
        props = feat.get("properties") or {}
        if _padus_feature_is_hunting_eligible(props):
            eligible += 1

    if eligible <= 0:
        raise HuntabilityGuardrailError(
            "PAD-US did not identify hunting-eligible public land inside this BBox. "
            "City parks, suburbs, parking lots, and general public/open land are not enough for a Monahinga hunting run. "
            "Please select another BBox over real natural/legal hunting ground."
        )


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise TerrainValidationError(f"Could not read JSON file: {path.name}") from exc


def _flatten_numeric_values(value: object, *, limit: int = 250000) -> list[float]:
    """Extract finite numeric values from nested heightmap structures."""
    out: list[float] = []
    stack = [value]

    while stack and len(out) < limit:
        item = stack.pop()
        if isinstance(item, bool) or item is None:
            continue
        if isinstance(item, (int, float)):
            number = float(item)
            if math.isfinite(number):
                out.append(number)
            continue
        if isinstance(item, list):
            stack.extend(item)
            continue
        if isinstance(item, tuple):
            stack.extend(item)
            continue

    return out


def _bbox_close(a: list[float], b: list[float], tolerance: float = 0.0002) -> bool:
    if len(a) != 4 or len(b) != 4:
        return False
    try:
        return all(abs(float(x) - float(y)) <= tolerance for x, y in zip(a, b))
    except Exception:
        return False


def _first_number(payload: dict, keys: list[str]) -> float | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        try:
            number = float(value)
            if math.isfinite(number):
                return number
        except Exception:
            continue
    return None


def _validate_terrain_run(run_root: Path, requested_bbox: BBox) -> dict:
    """Hard gate: files existing is not enough; terrain must be believable.

    Pass 13 is unit-aware:
    - heightmap geometry values may be normalized/render-space values, not meters.
    - terrain_summary elevation fields are treated as meter-like when present.
    - zero/flat output is still blocked.
    """
    terrain_truth_root = run_root / "terrain_truth"
    derivative_dir = terrain_truth_root / "terrain_derivatives"

    heightmap_path = derivative_dir / "heightmap.json"
    summary_path = derivative_dir / "terrain_summary.json"
    contract_path = terrain_truth_root / "terrain_contract.json"

    required_files = [
        heightmap_path,
        summary_path,
        derivative_dir / "terrain_render.png",
        derivative_dir / "hillshade.png",
        derivative_dir / "local_relief.png",
        derivative_dir / "slope.png",
    ]

    missing = [str(path.relative_to(run_root)) for path in required_files if not path.exists()]
    if missing:
        raise TerrainValidationError("Terrain run is missing required output files: " + ", ".join(missing))

    heightmap = _read_json(heightmap_path)
    summary = _read_json(summary_path)

    requested = [float(v) for v in requested_bbox.as_list()]

    heightmap_bbox = heightmap.get("bbox") or heightmap.get("bounds")
    if isinstance(heightmap_bbox, list) and not _bbox_close([float(v) for v in heightmap_bbox[:4]], requested):
        raise TerrainValidationError("Heightmap bbox does not match the requested terrain box.")

    if contract_path.exists():
        contract = _read_json(contract_path)
        contract_bbox = contract.get("bbox")
        if isinstance(contract_bbox, list) and not _bbox_close([float(v) for v in contract_bbox[:4]], requested):
            raise TerrainValidationError("Terrain contract bbox does not match the requested terrain box.")

    values_source = (
        heightmap.get("geometry_values")
        or heightmap.get("values")
        or heightmap.get("elevations")
        or heightmap.get("heightmap")
        or heightmap.get("grid")
    )
    values = _flatten_numeric_values(values_source)

    if len(values) < 64:
        raise TerrainValidationError("Heightmap does not contain enough numeric elevation samples.")

    render_min = min(values)
    render_max = max(values)
    render_relief = render_max - render_min

    if not math.isfinite(render_min) or not math.isfinite(render_max):
        raise TerrainValidationError("Heightmap elevation range is not finite.")

    if abs(render_max) < 0.001 and abs(render_min) < 0.001:
        raise TerrainValidationError("Heightmap appears zeroed; terrain generation did not produce real elevation data.")

    # Render-space relief threshold. This catches dead-flat mesh data without
    # pretending normalized geometry values are meters.
    min_render_relief = float(os.getenv("MONAHINGA_MIN_RENDER_RELIEF", "0.10"))
    if render_relief < min_render_relief:
        raise TerrainValidationError(
            f"Terrain render relief is too flat to trust: {render_relief:.3f} found, {min_render_relief:.3f} required."
        )

    # Meter-like summary validation when available. Support several possible key names.
    summary_min = _first_number(summary, ["elevation_min_m", "min_elevation_m", "min_elevation", "elevation_min"])
    summary_max = _first_number(summary, ["elevation_max_m", "max_elevation_m", "max_elevation", "elevation_max"])
    summary_relief = None

    if summary_min is not None and summary_max is not None:
        summary_relief = summary_max - summary_min
        min_meter_relief = float(os.getenv("MONAHINGA_MIN_SUMMARY_RELIEF_M", "1.0"))
        if not math.isfinite(summary_relief):
            raise TerrainValidationError("Terrain summary elevation relief is not finite.")
        if abs(summary_max) < 0.001 and abs(summary_min) < 0.001:
            raise TerrainValidationError("Terrain summary appears zeroed.")
        if summary_relief < min_meter_relief:
            raise TerrainValidationError(
                f"Terrain summary relief is too flat to trust: {summary_relief:.2f} m found, {min_meter_relief:.2f} m required."
            )

    for path in required_files:
        if path.stat().st_size <= 0:
            raise TerrainValidationError(f"Terrain output file is empty: {path.name}")

    return {
        "ok": True,
        "samples": len(values),
        "render_min": round(render_min, 4),
        "render_max": round(render_max, 4),
        "render_relief": round(render_relief, 4),
        "min_render_relief": min_render_relief,
        "summary_min_elevation_m": round(summary_min, 3) if summary_min is not None else None,
        "summary_max_elevation_m": round(summary_max, 3) if summary_max is not None else None,
        "summary_relief_m": round(summary_relief, 3) if summary_relief is not None else None,
    }


def _quarantine_bad_run(run_root: Path, reason: str) -> None:
    """Move bad runs out of the normal runs folder when possible."""
    try:
        if not run_root.exists():
            return
        quarantine_root = RUNS_DIR / "_invalid_runs"
        quarantine_root.mkdir(parents=True, exist_ok=True)
        marker = run_root / "TERRAIN_VALIDATION_FAILED.txt"
        marker.write_text(reason, encoding="utf-8")
        destination = quarantine_root / run_root.name
        if destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        shutil.move(str(run_root), str(destination))
    except Exception:
        pass


def _build_and_validate_once(
    *,
    bbox: BBox,
    run_root: Path,
    width: int,
    height: int,
    operator_context: dict,
) -> tuple[object, dict]:
    contract = build_terrain_truth_run(
        bbox,
        run_root,
        width=width,
        height=height,
        operator_context=operator_context,
    )
    terrain_validation = _validate_terrain_run(run_root, bbox)
    return contract, terrain_validation


def _run(bbox: BBox, width: int, height: int, operator_context: dict | None = None) -> dict:
    global RUN_COUNT

    if RUN_COUNT >= MAX_RUNS:
        return {"redirect": "/checkout"}

    bbox.validate_us_hunting_box()
    _enforce_huntability_guardrail(bbox)
    _enforce_padus_huntability_preflight(bbox)
    operator_context = dict(operator_context or {})

    first_run_id = f"run_{uuid4().hex[:10]}"
    first_run_root = RUNS_DIR / first_run_id

    retry_notes: list[str] = []

    try:
        contract, terrain_validation = _build_and_validate_once(
            bbox=bbox,
            run_root=first_run_root,
            width=width,
            height=height,
            operator_context=operator_context,
        )
        run_id = first_run_id
        run_root = first_run_root

    except TerrainValidationError as first_exc:
        retry_notes.append(f"Initial terrain validation failed: {str(first_exc)}")
        _quarantine_bad_run(first_run_root, str(first_exc))

        previous_cache_setting = os.environ.get("MONAHINGA_DISABLE_CACHE")
        os.environ["MONAHINGA_DISABLE_CACHE"] = "1"

        retry_run_id = f"run_{uuid4().hex[:10]}"
        retry_run_root = RUNS_DIR / retry_run_id

        try:
            contract, terrain_validation = _build_and_validate_once(
                bbox=bbox,
                run_root=retry_run_root,
                width=width,
                height=height,
                operator_context=operator_context,
            )
            terrain_validation["retry_used"] = True
            terrain_validation["retry_reason"] = str(first_exc)
            run_id = retry_run_id
            run_root = retry_run_root

        except TerrainValidationError as retry_exc:
            _quarantine_bad_run(retry_run_root, str(retry_exc))
            raise HTTPException(
                status_code=502,
                detail=(
                    "Terrain generation failed validation even after a fresh no-cache retry. "
                    f"First failure: {str(first_exc)} Retry failure: {str(retry_exc)}"
                ),
            ) from retry_exc

        finally:
            if previous_cache_setting is None:
                os.environ.pop("MONAHINGA_DISABLE_CACHE", None)
            else:
                os.environ["MONAHINGA_DISABLE_CACHE"] = previous_cache_setting

    except Exception:
        if first_run_root.exists() and not any(first_run_root.iterdir()):
            shutil.rmtree(first_run_root, ignore_errors=True)
        raise

    RUN_COUNT += 1

    if retry_notes:
        terrain_validation["retry_notes"] = retry_notes

    return {
        "ok": True,
        "run_id": run_id,
        "run_folder": str(run_root),
        "decision_contract": f"/runs/{run_id}/terrain_truth/decision/decision_contract.json",
        "command_surface_url": f"/runs/{run_id}/{contract.command_surface.path}",
        "runs_remaining": MAX_RUNS - RUN_COUNT,
        "terrain_validation": terrain_validation,
    }


@app.on_event("startup")
def startup_event() -> None:
    thread = threading.Thread(target=_prewarm_default_bbox, daemon=True)
    thread.start()


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return render_home_page(DEFAULT_BBOX)


@app.get("/instructions", response_class=HTMLResponse)
def instructions() -> str:
    return render_instructions_page()


@app.get("/checkout")
def checkout() -> RedirectResponse:
    payment_link = os.getenv("MONAHINGA_STRIPE_PAYMENT_LINK") or os.getenv("STRIPE_PAYMENT_LINK")
    if not payment_link:
        payment_link = "https://buy.stripe.com/8x2aEWb6f5qR7Td1mweEo00"
    return RedirectResponse(payment_link, status_code=303)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "run_count": RUN_COUNT,
        "runs_remaining": MAX_RUNS - RUN_COUNT,
    }


@app.get("/live-wind")
def live_wind(lat: float, lon: float) -> dict:
    """Return live wind for the command surface.

    Pass 14 restores the endpoint expected by the 3D command-surface viewer.
    It is intentionally non-fatal: if Open-Meteo fails, the endpoint still
    returns a JSON payload the UI can understand instead of a 404.
    """
    try:
        if not math.isfinite(float(lat)) or not math.isfinite(float(lon)):
            raise ValueError("Latitude and longitude must be finite numbers.")

        read = OpenMeteoWindClient().fetch_live_wind(float(lat), float(lon))
        payload = read.to_dict()
        payload["observed_at_label"] = format_observed_at(payload.get("observed_at"))
        payload["arrow_heading_deg"] = wind_arrow_heading_deg(payload.get("direction_deg"))

        return payload

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        return {
            "ok": False,
            "lat": float(lat),
            "lon": float(lon),
            "source": "Open-Meteo",
            "summary": "Live wind unavailable right now.",
            "note": f"{type(exc).__name__}: {exc}",
            "observed_at_label": "",
            "arrow_heading_deg": None,
        }


@app.post("/preview-wildlife")
def preview_wildlife(req: RunRequest):
    try:
        bbox = BBox.normalized(req.min_lon, req.min_lat, req.max_lon, req.max_lat)
        result = build_wildlife_atmosphere(bbox)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/run-terrain-truth")
def run_terrain_truth(req: RunRequest):
    try:
        bbox = BBox.normalized(req.min_lon, req.min_lat, req.max_lon, req.max_lat)
        result = _run(
            bbox,
            req.width,
            req.height,
            operator_context={
                "wind_direction": req.wind_direction,
                "notes": req.notes,
                "mode": req.mode or "hunter",
                "selected_species": req.selected_species or "default",
                "target_species": req.selected_species or "default",
            },
        )

        if isinstance(result, dict) and result.get("redirect"):
            return RedirectResponse(result["redirect"], status_code=303)

        return result

    except HTTPException:
        raise
    except HuntabilityGuardrailError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
