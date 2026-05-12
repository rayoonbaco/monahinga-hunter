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
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from uuid import uuid4
from urllib.parse import urlencode
from urllib.request import urlopen

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
    hunt_plan_window: str = Field(default="now")  # MONAHINGA_FUTURE_HUNT_PLANNER_V1
    hunt_plan_datetime: str = Field(default="")
    private_land_mode: str = Field(default="avoid")  # MONAHINGA_PRIVATE_LAND_PERMISSION_MODE_V1
    selection_polygon: list[list[float]] | None = Field(default=None)
    parcel_geojson: dict | None = Field(default=None)  # MONAHINGA_ACCEPT_PARCEL_GEOJSON_2026_05_06  # MONAHINGA_ACCEPT_SELECTION_POLYGON_2026_05_06


class ParcelPreviewRequest(BaseModel):
    min_lon: float = Field(...)
    min_lat: float = Field(...)
    max_lon: float = Field(...)
    max_lat: float = Field(...)
    selection_polygon: list[list[float]] | None = Field(default=None)
    manual_arcgis_url: str | None = Field(default=None)


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
        # MONAHINGA_SOFTEN_PADUS_NON_HUNTABLE_BLOCKING_2026_05_05
        # Softened final PAD-US token gate:
        # - Keep hard blocks for major-city guardrails, skipped PAD-US, unconfigured PAD-US,
        #   and boxes with zero legal/public PAD-US features.
        # - Allow boxes that have legal/public PAD-US features but lack a strict hunting token.
        #   This avoids false hard-blocks when a cabin/road edge is inside the BBox but
        #   nearby terrain may still be valid hunting context.
        # - Existing UI warnings still tell the user to verify legality, access, safety,
        #   permission, and local regulations before acting.
        strict_padus = str(os.getenv("MONAHINGA_STRICT_PADUS_HUNTABILITY", "")).strip().lower() in {"1", "true", "yes", "on"}
        if strict_padus:
            raise HuntabilityGuardrailError(
                "PAD-US did not identify hunting-eligible public land inside this BBox. "
                "City parks, suburbs, parking lots, and general public/open land are not enough for a Monahinga hunting run. "
                "Please select another BBox over real natural/legal hunting ground."
            )

        print(
            "[huntability] soft-allowing PAD-US legal/public features without strict hunting token; "
            "showing caution in UI and preserving field/legal verification responsibility."
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


def _monahinga_local_dev_free_runs_enabled() -> bool:
    """Allow unlimited local testing only when the local starter explicitly opts in."""
    value = (os.getenv("MONAHINGA_LOCAL_DEV_FREE_RUNS") or "").strip().lower()
    return value in {"1", "true", "yes", "on", "local"}



def _monahinga_permission_mode_enabled(operator_context: dict | None) -> bool:
    """True only when the hunter explicitly chose Permission Granted mode.

    Permission Granted is for known private land with confirmed landowner permission.
    It bypasses public/PAD-US preflight only; it does not bypass terrain, water,
    slope, BBox, polygon, or general huntability sanity checks.
    """
    try:
        raw = ""
        if isinstance(operator_context, dict):
            raw = str(operator_context.get("private_land_mode") or "").strip().lower()
        return any(token in raw for token in ("permission", "granted", "include", "allow"))
    except Exception:
        return False

def _run(bbox: BBox, width: int, height: int, operator_context: dict | None = None) -> dict:
    global RUN_COUNT

    if RUN_COUNT >= MAX_RUNS and not _monahinga_local_dev_free_runs_enabled():
        return {"redirect": "/checkout"}

    operator_context = dict(operator_context or {})

    bbox.validate_us_hunting_box()
    _enforce_huntability_guardrail(bbox)

    # MONAHINGA_PERMISSION_MODE_PADUS_BYPASS_V5:
    # Avoid mode still requires public/legal/PAD-US-style land context.
    # Permission Granted mode is for known private land with confirmed landowner permission,
    # so it must not be blocked by the public-land preflight before terrain can run.
    # Downstream decision gates still protect BBox/polygon bounds, terrain, water, slope,
    # and other huntability checks.
    if not _monahinga_permission_mode_enabled(operator_context):
        _enforce_padus_huntability_preflight(bbox)
    else:
        print("[huntability] Permission Granted mode: bypassing PAD-US public-land preflight; terrain and decision gates still apply.")

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
    payment_link = (os.getenv("MONAHINGA_STRIPE_PAYMENT_LINK") or os.getenv("STRIPE_PAYMENT_LINK") or "").strip()
    if payment_link.lower() in {"", "undefined", "null", "none"}:
        payment_link = "https://buy.stripe.com/8x2aEWb6f5qR7Td1mweEo00"
    return RedirectResponse(payment_link, status_code=303)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "run_count": RUN_COUNT,
        "runs_remaining": MAX_RUNS - RUN_COUNT,
    }


# MONAHINGA_PADUS_PREVIEW_ENDPOINT_2026_05_06
@app.get("/padus-preview")
def padus_preview(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> dict:
    try:
        bbox = BBox.normalized(min_lon, min_lat, max_lon, max_lat)

        width = abs(float(bbox.max_lon) - float(bbox.min_lon))
        height = abs(float(bbox.max_lat) - float(bbox.min_lat))
        if width <= 0 or height <= 0:
            raise ValueError("BBox must have non-zero width and height.")
        if width > 1.5 or height > 1.5:
            raise ValueError("PAD-US preview BBox is too large. Zoom in or draw a smaller scouting area.")

        cached_geojson_path, cached_summary_path = _preflight_cache_paths(bbox)

        if not (cached_geojson_path.exists() and cached_summary_path.exists()):
            preflight_root = RUNS_DIR / "_padus_preview"
            preflight_root.mkdir(parents=True, exist_ok=True)

            with tempfile.TemporaryDirectory(prefix="padus_preview_", dir=str(preflight_root)) as tmp:
                tmp_root = Path(tmp)
                geojson_path = tmp_root / "legal_surface.geojson"
                summary_path = tmp_root / "legal_surface_summary.json"
                PADUSLegalSurfaceClient().fetch_legal_surface(bbox, geojson_path, summary_path)

                cached_geojson_path.parent.mkdir(parents=True, exist_ok=True)
                if geojson_path.exists():
                    shutil.copy2(geojson_path, cached_geojson_path)
                if summary_path.exists():
                    shutil.copy2(summary_path, cached_summary_path)

        try:
            geojson = json.loads(cached_geojson_path.read_text(encoding="utf-8")) if cached_geojson_path.exists() else {
                "type": "FeatureCollection",
                "features": [],
            }
        except Exception:
            geojson = {
                "type": "FeatureCollection",
                "features": [],
            }

        try:
            summary = json.loads(cached_summary_path.read_text(encoding="utf-8")) if cached_summary_path.exists() else {}
        except Exception:
            summary = {}

        feature_count = len(geojson.get("features") or [])

        return {
            "ok": True,
            "bbox": bbox.as_list(),
            "feature_count": feature_count,
            "summary": summary,
            "geojson": geojson,
            "message": (
                "PAD-US public/hunting signal loaded for this selection. "
                "Verify ownership, access, permission, season dates, and local regulations."
            ),
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PAD-US preview unavailable: {type(exc).__name__}: {exc}")

# MONAHINGA_AUTO_PRIVATE_PARCEL_SOURCE_ENDPOINT_2026_05_08
OWNER_FIELD_CANDIDATES = [
    "OWNER", "Owner", "owner", "OWNER_NAME", "owner_name", "PARCEL_OWNER", "OWN_NAME", "NAME",
    "Owner1", "Owner2", "Current_Ow", "CURRENT_OW", "FullName", "Full_Name", "Name",
    "OwnerAdd1", "OwnerAdd2", "FullAdd", "OwnerCity", "OwnerState", "PostCode",
]
PARCEL_ID_FIELD_CANDIDATES = [
    "PARCEL_ID", "parcel_id", "PIN", "pin", "APN", "apn", "OBJECTID", "FID", "ACCOUNT", "MAPBLKLOT", "TAXPIN",
    "PPI", "Schedule", "ScheduleText", "PrimaryID", "SecondID", "SwisParID", "Printkey", "Accountnum",
]


def _parcel_preview_cache_key(bbox: BBox) -> str:
    payload = [round(float(v), 6) for v in bbox.as_list()]
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]
    return f"parcel_bbox_{digest}"


def _parcel_preview_cache_path(bbox: BBox) -> Path:
    return RUNS_DIR / "_parcel_preview_cache" / _parcel_preview_cache_key(bbox) / "private_parcels.geojson"


def _first_present_value(props: dict, keys: list[str]) -> str:
    for key in keys:
        if key in props and props[key] is not None and str(props[key]).strip():
            return str(props[key]).strip()
    return ""


def _feature_lon_lat_pairs(geometry: dict) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []

    def walk(value) -> None:
        if isinstance(value, (list, tuple)) and len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
            lon = float(value[0])
            lat = float(value[1])
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                pairs.append((lon, lat))
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    if geometry and isinstance(geometry, dict):
        walk(geometry.get("coordinates"))
    return pairs


def _feature_intersects_bbox(feature: dict, bbox: BBox) -> bool:
    pairs = _feature_lon_lat_pairs(feature.get("geometry") or {})
    if not pairs:
        return False
    min_lon = min(p[0] for p in pairs)
    max_lon = max(p[0] for p in pairs)
    min_lat = min(p[1] for p in pairs)
    max_lat = max(p[1] for p in pairs)
    return not (
        max_lon < float(bbox.min_lon)
        or min_lon > float(bbox.max_lon)
        or max_lat < float(bbox.min_lat)
        or min_lat > float(bbox.max_lat)
    )


def _normalize_parcel_geojson_for_app(raw_geojson: dict, bbox: BBox, source_label: str) -> dict:
    raw_features = raw_geojson.get("features") if isinstance(raw_geojson, dict) else []
    if not isinstance(raw_features, list):
        raw_features = []

    features: list[dict] = []
    for raw_feature in raw_features:
        if not isinstance(raw_feature, dict) or not raw_feature.get("geometry"):
            continue
        if not _feature_intersects_bbox(raw_feature, bbox):
            continue
        feature = dict(raw_feature)
        props = dict(feature.get("properties") or {})
        owner = _first_present_value(props, OWNER_FIELD_CANDIDATES)
        parcel_id = _first_present_value(props, PARCEL_ID_FIELD_CANDIDATES)
        props["MONAHINGA_PARCEL_SOURCE"] = "AUTO_SOURCE"
        props["MONAHINGA_OWNER_NORMALIZED"] = owner or "Unknown owner / verify county records"
        props["MONAHINGA_PARCEL_ID_NORMALIZED"] = parcel_id or "Unknown parcel ID"
        props["MONAHINGA_SOURCE_LABEL"] = source_label
        props["MONAHINGA_WARNING"] = "Private parcel signal only. Verify ownership, permission, access, and local records."
        feature["properties"] = props
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "properties": {
            "monahinga_parcel_source": "auto_source",
            "monahinga_parcel_source_label": source_label,
            "monahinga_parcel_warning": "AUTO PARCEL SOURCE. Ownership context only; verify county records, access, permission, and regulations.",
            "monahinga_feature_count": len(features),
            "monahinga_bbox_scoped": True,
        },
        "features": features,
    }


def _load_configured_parcel_source_geojson(bbox: BBox) -> tuple[dict, str]:
    """Load a BBox-scoped private parcel source without changing the manual upload path.

    Supported first-pass inputs:
    - MONAHINGA_PARCEL_GEOJSON_PATH: local/server GeoJSON export file.
    - MONAHINGA_PARCEL_GEOJSON_URL: GeoJSON URL. If it contains {min_lon}, {min_lat}, {max_lon}, {max_lat},
      those tokens are filled. Otherwise bbox query parameters are appended.

    This is a scaffold for county GIS / Regrid / ReportAll / Landgrid-style sources. It never preloads
    nationwide parcels; it only returns geometry intersecting the selected BBox.
    """
    # MONAHINGA_REGRID_SOURCE_READY_PASS1_2026_05_08: Regrid is the selected first real parcel source for Pass 2.
# Required later: MONAHINGA_REGRID_TOKEN. Optional: MONAHINGA_REGRID_BASE_URL.
# Do not claim real private property until Regrid is wired and one known parcel is verified.
source_path = (os.getenv("MONAHINGA_PARCEL_GEOJSON_PATH") or "").strip()
# MONAHINGA_AUTO_PRIVATE_PARCEL_CONFIGURED_SOURCE_V1_2026_05_08

# MONAHINGA_FREE_PARCEL_LADDER_V2_2026_05_08: unified free-first parcel source ladder.
MONAHINGA_FREE_PARCEL_SOURCE_V2 = [
    {
        "id": "wyoming_public_arcgis",
        "label": "Wyoming public parcel ArcGIS service",
        "query_url": os.getenv("MONAHINGA_WY_PARCEL_ARCGIS_QUERY_URL", "https://gis.deq.wyo.gov/arcgis/rest/services/WY_PARCELS/MapServer/query").strip() or "https://gis.deq.wyo.gov/arcgis/rest/services/WY_PARCELS/MapServer/query",
        "region": "wyoming",
    },
    {
        "id": "wyoming_private_arcgis",
        "label": "Wyoming private parcels ArcGIS Identify service",
        "query_url": os.getenv("MONAHINGA_WY_PRIVATE_PARCEL_ARCGIS_QUERY_URL", "https://gis.deq.wyo.gov/arcgis/rest/services/WY_PRIVATE_PARCELS/MapServer/query").strip() or "https://gis.deq.wyo.gov/arcgis/rest/services/WY_PRIVATE_PARCELS/MapServer/query",
        "region": "wyoming",
    },
    {
        "id": "lawrence_county_sd_parcels",
        "label": "Lawrence County SD public parcel service",
        "query_url": os.getenv("MONAHINGA_LAWRENCE_SD_PARCEL_ARCGIS_QUERY_URL", "https://services8.arcgis.com/YKIZLV97YLZN6bol/ArcGIS/rest/services/Lawrence_Parcels_YrBlt/FeatureServer/0/query").strip() or "https://services8.arcgis.com/YKIZLV97YLZN6bol/ArcGIS/rest/services/Lawrence_Parcels_YrBlt/FeatureServer/0/query",
        "region": "lawrence_sd",
    },
    {
        "id": "allegany_county_ny_parcels_2024",
        "label": "Allegany County NY 2024 public parcel FeatureServer",
        "query_url": os.getenv("MONAHINGA_ALLEGANY_NY_PARCEL_ARCGIS_QUERY_URL", "https://services5.arcgis.com/WcotYUBrYwlGLzUr/ArcGIS/rest/services/Allegany_Parcels_2024/FeatureServer/0/query").strip() or "https://services5.arcgis.com/WcotYUBrYwlGLzUr/ArcGIS/rest/services/Allegany_Parcels_2024/FeatureServer/0/query",
        "region": "allegany_ny",
    },
    {
        # MONAHINGA_SUMMIT_CLARITY_V1_2026_05_09:
        # We probed Summit's ParcelQueryTool service, but the public MapServer returned
        # "service not started" / 500 errors during testing. Keep this disabled unless
        # MONAHINGA_ENABLE_SUMMIT_INACTIVE_ASSESSOR_PROBE=true is intentionally set later.
        # This avoids confusing Chris/Tom with a known-dead preferred source before falling
        # back to the actual working public parcel service.
        "id": "summit_county_co_assessor_taxmap_parcels_disabled",
        "label": "Summit County CO assessor tax-map parcels - inactive public service probe",
        "query_url": os.getenv("MONAHINGA_SUMMIT_CO_ASSESSOR_PARCEL_ARCGIS_QUERY_URL", "https://gis.summitcountyco.gov/arcgis/rest/services/ParcelQueryTool/SummitMap1_Pro321_Transparent/MapServer/5/query").strip() or "https://gis.summitcountyco.gov/arcgis/rest/services/ParcelQueryTool/SummitMap1_Pro321_Transparent/MapServer/5/query",
        "region": "summit_co" if os.getenv("MONAHINGA_ENABLE_SUMMIT_INACTIVE_ASSESSOR_PROBE", "").strip().lower() in {"1", "true", "yes"} else "summit_co_disabled",
        "result_record_count": os.getenv("MONAHINGA_SUMMIT_CO_ASSESSOR_PARCEL_LIMIT", "2000"),
        "post_filter": "summit_density_mix",
    },
    {
        # MONAHINGA_SUMMIT_CLARITY_V1_2026_05_09:
        # Best active public Summit source found so far. Despite the Road & Bridge service
        # folder name, layer 0 exposes assessor-style parcel fields: PPI, Schedule,
        # ShortDesc, SitusAdd, owner mailing context, acreage, assessed value fields,
        # neighborhood/subdivision, and geometry. Large blocky polygons in the mountain
        # portions are usually real public/agency/open-space parcels, not demo squares.
        "id": "summit_county_co_parcel_query",
        "label": "Summit County CO best-active public parcel/assessor context",
        "query_url": os.getenv("MONAHINGA_SUMMIT_CO_PARCEL_ARCGIS_QUERY_URL", "https://gis.summitcountyco.gov/arcgis/rest/services/RoadandBridge/RightOfWayPermitData/MapServer/0/query").strip() or "https://gis.summitcountyco.gov/arcgis/rest/services/RoadandBridge/RightOfWayPermitData/MapServer/0/query",
        "region": "summit_co",
        "result_record_count": os.getenv("MONAHINGA_SUMMIT_CO_PARCEL_LIMIT", "2000"),
        "post_filter": "summit_density_mix",
    },
    {
        "id": "potter_county_pa_taxparcels",
        "label": "Potter County PA TaxParcels public ArcGIS service",
        "query_url": os.getenv("MONAHINGA_POTTER_PA_PARCEL_ARCGIS_QUERY_URL", "https://maps.pottercountypa.net/arcgis/rest/services/TaxParcel/TaxParcels/FeatureServer/0/query").strip() or "https://maps.pottercountypa.net/arcgis/rest/services/TaxParcel/TaxParcels/FeatureServer/0/query",
        "region": "potter_pa",
    },
    {
        "id": "pa_pasda_parcels",
        "label": "Pennsylvania PASDA public parcel service",
        "query_url": os.getenv("MONAHINGA_PA_PARCEL_ARCGIS_QUERY_URL", "https://maps.pasda.psu.edu/arcgis/rest/services/PA_Parcels/MapServer/1/query").strip() or "https://maps.pasda.psu.edu/arcgis/rest/services/PA_Parcels/MapServer/1/query",
        "region": "pennsylvania",
    },
    {
        "id": "pa_pasda_apps_parcels",
        "label": "Pennsylvania PASDA public parcel service alternate",
        "query_url": "https://apps.pasda.psu.edu/arcgis/rest/services/PA_Parcels/MapServer/1/query",
        "region": "pennsylvania",
    },
    {
        "id": "pa_dep_parcels",
        "label": "Pennsylvania DEP public parcel service",
        "query_url": "https://gis.dep.pa.gov/depgisprd/rest/services/Parcels/PA_Parcels/MapServer/0/query",
        "region": "pennsylvania",
    },
]


def _monahinga_v2_bbox_region(bbox: BBox) -> str:
    lon = (float(bbox.min_lon) + float(bbox.max_lon)) / 2.0
    lat = (float(bbox.min_lat) + float(bbox.max_lat)) / 2.0
    if -112.0 <= lon <= -104.0 and 41.0 <= lat <= 45.3:
        return "wyoming"
    # Verified by manual ArcGIS pass: Spearfish / Lawrence County, South Dakota.
    # Keep this narrow so the app does not pretend all South Dakota parcel services are solved.
    if -104.2 <= lon <= -103.0 and 44.0 <= lat <= 45.0:
        return "lawrence_sd"
    # MONAHINGA_ALLEGANY_SUMMIT_SOURCES_2026_05_09: narrow county-specific auto-source gates.
    # Allegany County NY sits just north of Potter County PA, so it must be checked before the broader PA/Potter gate.
    if -78.7 <= lon <= -77.6 and 42.0 <= lat <= 42.7:
        return "allegany_ny"
    if -107.1 <= lon <= -105.7 and 39.1 <= lat <= 40.3:
        return "summit_co"
    if -78.7 <= lon <= -76.0 and 40.5 <= lat <= 42.6:
        return "potter_pa"
    if -80.7 <= lon <= -74.5 and 39.4 <= lat <= 42.7:
        return "pennsylvania"
    return "unknown"


def _monahinga_v2_arcgis_url(source: dict, bbox: BBox, fmt: str) -> str:
    geometry = json.dumps({
        "xmin": float(bbox.min_lon),
        "ymin": float(bbox.min_lat),
        "xmax": float(bbox.max_lon),
        "ymax": float(bbox.max_lat),
        "spatialReference": {"wkid": 4326},
    }, separators=(",", ":"))

    params = {
        "f": fmt,
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "geometryType": "esriGeometryEnvelope",
        "geometry": geometry,
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "resultRecordCount": str(source.get("result_record_count") or os.getenv("MONAHINGA_FREE_PARCEL_LIMIT", "200")),
    }

    query_url = source["query_url"]
    if query_url.rstrip("/").endswith("/MapServer/query"):
        params["layers"] = "all"

    return query_url + "?" + urlencode(params)


def _monahinga_v2_read_json_url(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "Monahinga-HUNTER/1.0"})
    with urlopen(req, timeout=30) as response:
        raw = response.read(20 * 1024 * 1024)
    return json.loads(raw.decode("utf-8"))


def _monahinga_v2_esri_json_to_geojson(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("ArcGIS JSON response was not an object")

    if raw.get("error"):
        err = raw.get("error") or {}
        raise ValueError(str(err.get("message") or err))

    features = []
    for item in raw.get("features") or []:
        if not isinstance(item, dict):
            continue
        attrs = dict(item.get("attributes") or item.get("properties") or {})
        geom = item.get("geometry") or {}
        gj_geom = None

        if isinstance(geom, dict) and geom.get("rings"):
            # Most ArcGIS services honor outSR=4326. Keep rings as returned.
            # This preserves county services such as Allegany NY and Summit CO without
            # guessing at non-WebMercator local state-plane feet.
            gj_geom = {"type": "Polygon", "coordinates": geom.get("rings")}
        elif isinstance(geom, dict) and geom.get("paths"):
            gj_geom = {"type": "MultiLineString", "coordinates": geom.get("paths")}
        elif isinstance(geom, dict) and "x" in geom and "y" in geom:
            gj_geom = {"type": "Point", "coordinates": [geom.get("x"), geom.get("y")]}

        if gj_geom:
            features.append({"type": "Feature", "properties": attrs, "geometry": gj_geom})

    return {"type": "FeatureCollection", "features": features}


def _monahinga_v2_owner_value(props: dict) -> str:
    # Keep this honest: some county services do not expose a clean owner-name field.
    # In that case, surface the best ownership/mailing/public-agency context instead of pretending.
    primary_keys = (
        "OWNER", "Owner", "owner", "OWNER_NAME", "owner_name", "PARCEL_OWNER", "OWN_NAME",
        "OwnershipTable_OWNER", "OWNER1", "Owner1", "OWNERNME1", "TAXPAYER", "MAIL_NAME",
        "Current_Ow", "CURRENT_OW", "NAME", "Name", "Parcels_NAME", "FullName",
    )
    for key in primary_keys:
        value = props.get(key)
        if value is not None and str(value).strip() and str(value).strip().lower() not in {"none", "null"}:
            return str(value).strip()

    summit_parts = []
    for key in ("FullAdd", "OwnerAdd1", "OwnerAdd2", "OwnerCity", "OwnerState", "PostCode", "MiscChar", "EcoDesc"):
        value = props.get(key)
        if value is not None and str(value).strip() and str(value).strip().lower() not in {"none", "null"}:
            summit_parts.append(str(value).strip().replace("|", ", "))
    if summit_parts:
        return "Ownership/mailing context: " + " · ".join(summit_parts[:4])

    return "Owner name not exposed by this source / verify county records"


def _monahinga_v2_parcel_id_value(props: dict) -> str:
    for key in (
        "PARCEL_ID", "PIN", "APN", "OBJECTID", "FID", "ACCOUNT", "MAPBLKLOT", "TAXPIN",
        "PID", "PARCELNO", "PARCEL_NUM", "UPI", "CAMA_ID",
        "Serial", "SERIAL", "OwnershipTable_SERIAL", "Parcels_GISID", "GISID", "PPI", "Lotnum", "Parcels_Lotnum",
    ):
        value = props.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return "Unknown parcel ID"




# MONAHINGA_PARCEL_SOURCE_SUMMARY_V14_2026_05_09:
# Read-only proof summary for parcel sources. Does not alter geometry, scoring, or legal truth.
def _monahinga_v14_first_nonempty(props: dict, keys: tuple[str, ...]) -> tuple[str, str]:
    if not isinstance(props, dict):
        return "", ""
    for key in keys:
        value = props.get(key)
        if value is not None and str(value).strip():
            return key, str(value).strip()
    return "", ""


def _monahinga_v14_preview_text(value, limit: int = 80) -> str:
    try:
        text = str(value)
    except Exception:
        return ""
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(text) > limit:
        return text[: max(0, limit - 3)] + "..."
    return text


def _monahinga_v14_parcel_source_summary(fc: dict, source_kind: str, label: str) -> dict:
    features = fc.get("features") or [] if isinstance(fc, dict) else []
    sample_props = {}
    for feature in features:
        if isinstance(feature, dict) and isinstance(feature.get("properties"), dict):
            sample_props = feature.get("properties") or {}
            if sample_props:
                break

    owner_key, owner = _monahinga_v14_first_nonempty(sample_props, (
        "OWNER", "Owner", "owner", "OWNER_NAME", "owner_name", "PARCEL_OWNER",
        "OWN_NAME", "NAME", "OWNER1", "OWNERNME1", "TAXPAYER", "MAIL_NAME",
        "CURRENT_OW", "Owner2",
    ))
    parcel_key, parcel_id = _monahinga_v14_first_nonempty(sample_props, (
        "PARCEL_ID", "PIN", "APN", "OBJECTID", "FID", "ACCOUNT", "MAPBLKLOT",
        "TAXPIN", "PID", "PARCELNO", "PARCEL_NUM", "UPI", "CAMA_ID", "PropertyNu",
    ))
    situs_key, situs = _monahinga_v14_first_nonempty(sample_props, (
        "SITUS", "SITE_ADDR", "SITUS_ADDRESS", "PROPERTY_ADDRESS", "ADDRESS",
        "ADDR", "PHYSICAL_ADDRESS",
    ))
    acres_key, acres = _monahinga_v14_first_nonempty(sample_props, (
        "Acres", "ACRES", "acreage", "ACREAGE", "CALC_ACRES",
    ))
    year_key, year_built = _monahinga_v14_first_nonempty(sample_props, (
        "fyrblt", "YR_BUILT", "YEAR_BUILT", "YearBuilt", "BLT_YR",
    ))

    sample = {
        "owner": _monahinga_v14_preview_text(owner, 70),
        "owner_key": owner_key,
        "parcel_id": _monahinga_v14_preview_text(parcel_id, 60),
        "parcel_id_key": parcel_key,
        "situs": _monahinga_v14_preview_text(situs, 80),
        "situs_key": situs_key,
        "acres": _monahinga_v14_preview_text(acres, 30),
        "acres_key": acres_key,
        "year_built": _monahinga_v14_preview_text(year_built, 30),
        "year_built_key": year_key,
    }

    confidence = "demo"
    if "demo" in str(source_kind or "").lower():
        confidence = "demo"
    elif sample["owner"] and sample["parcel_id"]:
        confidence = "strong_source_fields_detected"
    elif sample["owner"] or sample["parcel_id"]:
        confidence = "partial_source_fields_detected"
    else:
        confidence = "geometry_only_verify_fields"

    return {
        "source": source_kind or "",
        "label": label or "Private parcel source",
        "feature_count": len(features),
        "sample": sample,
        "confidence": confidence,
        "field_count": len(sample_props.keys()) if isinstance(sample_props, dict) else 0,
        "verify_note": "Ownership context only. Verify owner, parcel ID, access, permission, seasons, and local regulations before field use.",
    }



# MONAHINGA_FREE_PARCEL_POLYGON_GATE_V4_2026_05_08:
# Private parcel overlays must be boundary polygons, not identify points/lines.
def _monahinga_v4_is_polygon_geometry(geometry: dict) -> bool:
    if not isinstance(geometry, dict):
        return False
    geom_type = str(geometry.get("type") or "").strip()
    return geom_type in {"Polygon", "MultiPolygon"}


def _monahinga_v4_geometry_type(geometry: dict) -> str:
    if not isinstance(geometry, dict):
        return "missing"
    return str(geometry.get("type") or "unknown")




# MONAHINGA_WY_PARCEL_FIELD_INSPECTOR_V5_2026_05_08:
# Prints a safe sample of public parcel attribute fields so we can map owner/APN correctly.
def _monahinga_v5_preview_value(value) -> str:
    try:
        text = str(value)
    except Exception:
        return "<unprintable>"
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(text) > 90:
        return text[:87] + "..."
    return text


def _monahinga_v5_log_parcel_fields(source: dict, props: dict, sample_index: int) -> None:
    try:
        if os.getenv("MONAHINGA_LOG_PARCEL_FIELDS", "1").strip().lower() in {"0", "false", "no", "off"}:
            return
        if sample_index > 2:
            return
        source_id = source.get("id") or "unknown_source"
        keys = sorted([str(k) for k in props.keys()])
        print(f"[parcel-fields] source={source_id} sample={sample_index} field_count={len(keys)}")
        print(f"[parcel-fields] keys: {', '.join(keys[:80])}")
        for key in keys[:80]:
            value = props.get(key)
            print(f"[parcel-fields] {key} = {_monahinga_v5_preview_value(value)}")
    except Exception as exc:
        print(f"[parcel-fields] failed to log fields: {type(exc).__name__}: {exc}")




# MONAHINGA_REJECT_COUNTY_LAYER_V6_2026_05_08:
# Do not accept county/state/city/road/annotation shapes as private parcels.
def _monahinga_v6_is_bad_admin_layer(props: dict) -> bool:
    if not isinstance(props, dict):
        return False

    layer_text_parts = []
    for key in ("LAYER_NAME", "layerName", "LayerName", "DISPLAY_FIELD_NAME", "VALUE", "NAME"):
        val = props.get(key)
        if val is not None:
            layer_text_parts.append(str(val))

    layer_text = " ".join(layer_text_parts).upper()

    bad_words = (
        "COUNTY", "COUNTIES", "STATE", "STATES", "CITY", "CITIES", "TOWN",
        "TOWNSHIP", "MUNICIPAL", "ROAD", "ROADS", "HIGHWAY", "ROW",
        "BOUNDARY", "BOUNDARIES", "WATER", "STREAM", "RIVER", "LABEL",
        "ANNOTATION", "SECTION", "TOWNSHIP RANGE"
    )

    return any(word in layer_text for word in bad_words)


def _monahinga_v6_has_parcel_clue(props: dict) -> bool:
    if not isinstance(props, dict):
        return False

    parcel_keys = (
        "PARCEL", "APN", "PIN", "PID", "TAX", "CAMA", "ACCOUNT",
        "OWNER", "OWN", "ASSES", "DEED", "LEGAL", "ACRES", "PROPERTY"
    )

    for key, value in props.items():
        combo = (str(key) + " " + str(value)).upper()
        if any(clue in combo for clue in parcel_keys):
            return True

    return False




# MONAHINGA_SUMMIT_PARCEL_DENSITY_V1_2026_05_09
# Summit's public polygon service can return huge public/agency blocks before it returns
# smaller town/private parcel-looking shapes. This helper keeps the page useful by mixing
# many smaller parcels with a small set of large context parcels after the larger query.
def _monahinga_v15_geometry_bbox_area_approx(geometry: dict) -> float:
    try:
        coords = []
        if not isinstance(geometry, dict):
            return 999999.0
        gtype = geometry.get("type")
        raw = geometry.get("coordinates") or []
        if gtype == "Polygon":
            for ring in raw:
                for pair in ring:
                    coords.append(pair)
        elif gtype == "MultiPolygon":
            for poly in raw:
                for ring in poly:
                    for pair in ring:
                        coords.append(pair)
        if not coords:
            return 999999.0
        xs = [float(p[0]) for p in coords if isinstance(p, (list, tuple)) and len(p) >= 2]
        ys = [float(p[1]) for p in coords if isinstance(p, (list, tuple)) and len(p) >= 2]
        if not xs or not ys:
            return 999999.0
        return abs((max(xs) - min(xs)) * (max(ys) - min(ys)))
    except Exception:
        return 999999.0


def _monahinga_v15_summit_density_mix(features: list[dict]) -> tuple[list[dict], str]:
    if not isinstance(features, list) or len(features) <= 900:
        return features, "Summit density mix not needed."

    indexed = []
    for idx, feature in enumerate(features):
        props = dict(feature.get("properties") or {}) if isinstance(feature, dict) else {}
        area = _monahinga_v15_geometry_bbox_area_approx((feature or {}).get("geometry") or {})
        has_id = bool(props.get("PPI") or props.get("Schedule") or props.get("ScheduleText") or props.get("MONAHINGA_PARCEL_ID_NORMALIZED"))
        has_context = bool(props.get("OwnerAdd1") or props.get("FullAdd") or props.get("EcoDesc") or props.get("MiscChar"))
        # Prefer parcel-looking features with useful context, then smaller geometry.
        priority = (0 if has_id else 1, 0 if has_context else 1, area, idx)
        indexed.append((priority, area, idx, feature))

    indexed.sort(key=lambda item: item[0])
    small_count = 850
    big_count = 50
    chosen = {idx: feature for _priority, _area, idx, feature in indexed[:small_count]}
    # Keep a small number of the biggest parcels too, because agency/open-space blocks are
    # still useful scouting context, just not enough by themselves.
    for _priority, _area, idx, feature in sorted(indexed, key=lambda item: item[1], reverse=True)[:big_count]:
        chosen.setdefault(idx, feature)
    mixed = [chosen[idx] for idx in sorted(chosen)]
    note = f"Summit density mix kept {len(mixed)} of {len(features)} features: smaller parcel-looking shapes plus major public/agency context."
    return mixed, note


def _monahinga_v2_normalize_public_geojson(raw: dict, source: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("source response was not a GeoJSON object")
    if raw.get("type") != "FeatureCollection" or not isinstance(raw.get("features"), list):
        raise ValueError("source response was not a GeoJSON FeatureCollection")

    clean_features = []
    rejected_by_type = {}
    sample_index = 0
    for feature in raw.get("features") or []:
        if not isinstance(feature, dict) or not feature.get("geometry"):
            rejected_by_type["missing"] = rejected_by_type.get("missing", 0) + 1
            continue

        geometry = feature.get("geometry")
        geom_type = _monahinga_v4_geometry_type(geometry)
        if not _monahinga_v4_is_polygon_geometry(geometry):
            rejected_by_type[geom_type] = rejected_by_type.get(geom_type, 0) + 1
            continue

        props = dict(feature.get("properties") or {})
        sample_index += 1
        _monahinga_v5_log_parcel_fields(source, props, sample_index)

        if _monahinga_v6_is_bad_admin_layer(props) and not _monahinga_v6_has_parcel_clue(props):
            rejected_by_type["admin_or_nonparcel_layer"] = rejected_by_type.get("admin_or_nonparcel_layer", 0) + 1
            print(f"[parcel-preview] rejected non-parcel layer from {source.get('id')}: LAYER_NAME={props.get('LAYER_NAME')} VALUE={props.get('VALUE')}")
            continue

        owner = _monahinga_v2_owner_value(props)
        parcel_id = _monahinga_v2_parcel_id_value(props)
        props.setdefault("OWNER", owner)
        props.setdefault("OWNER_NAME", owner)
        props.setdefault("PARCEL_ID", parcel_id)
        props["MONAHINGA_OWNER_NORMALIZED"] = owner
        props["MONAHINGA_PARCEL_ID_NORMALIZED"] = parcel_id
        props["MONAHINGA_PARCEL_SOURCE"] = source["label"]
        props["MONAHINGA_PARCEL_SOURCE_CONFIDENCE"] = "free_public_source_unverified"
        props["MONAHINGA_PARCEL_WARNING"] = "Free public parcel source. Verify owner, parcel ID, access, permission, and county records."
        clean_features.append({"type": "Feature", "properties": props, "geometry": geometry})

    if rejected_by_type:
        print(f"[parcel-preview] rejected non-polygon parcel candidates from {source.get('id')}: {rejected_by_type}")

    summit_density_note = ""
    if source.get("post_filter") == "summit_density_mix":
        clean_features, summit_density_note = _monahinga_v15_summit_density_mix(clean_features)
        if summit_density_note:
            print(f"[parcel-preview] {summit_density_note}")

    if not clean_features:
        raise ValueError(f"source returned zero usable parcel polygon geometries; rejected={rejected_by_type}")

    return {
        "type": "FeatureCollection",
        "features": clean_features,
        "properties": {
            "monahinga_parcel_source": source["id"],
            "monahinga_parcel_source_label": source["label"],
            "monahinga_parcel_warning": "Free public parcel source. Ownership context only; verify county assessor records, legal access, permission, seasons, tags, safety, and local regulations.",
            "monahinga_feature_count": len(clean_features),
            "monahinga_confidence": "public_source_unverified_until_known_parcel_checked",
            "monahinga_source_url": source["query_url"],
            "monahinga_density_note": summit_density_note,
        },
    }



# MONAHINGA_WY_ARCGIS_IDENTIFY_FALLBACK_V3_2026_05_08:
# fallback for ArcGIS MapServer dynamic parcel services where /query does not expose usable parcel geometry.
def _monahinga_v3_lonlat_to_webmercator(lon: float, lat: float) -> tuple[float, float]:
    import math
    origin_shift = 20037508.342789244
    x = lon * origin_shift / 180.0
    lat = max(min(lat, 89.5), -89.5)
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    y = y * origin_shift / 180.0
    return x, y


def _monahinga_v3_webmercator_to_lonlat(x: float, y: float) -> list[float]:
    import math
    origin_shift = 20037508.342789244
    lon = (x / origin_shift) * 180.0
    lat = (y / origin_shift) * 180.0
    lat = 180.0 / math.pi * (2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return [lon, lat]


def _monahinga_v3_coord_to_lonlat(pair) -> list[float]:
    x = float(pair[0])
    y = float(pair[1])
    if abs(x) > 1000 or abs(y) > 1000:
        return _monahinga_v3_webmercator_to_lonlat(x, y)
    return [x, y]


def _monahinga_v3_geometry_to_lonlat(geom: dict) -> dict | None:
    if not isinstance(geom, dict):
        return None

    if geom.get("rings"):
        rings = []
        for ring in geom.get("rings") or []:
            rings.append([_monahinga_v3_coord_to_lonlat(pair) for pair in ring])
        return {"type": "Polygon", "coordinates": rings}

    if geom.get("paths"):
        paths = []
        for path in geom.get("paths") or []:
            paths.append([_monahinga_v3_coord_to_lonlat(pair) for pair in path])
        return {"type": "MultiLineString", "coordinates": paths}

    if "x" in geom and "y" in geom:
        return {"type": "Point", "coordinates": _monahinga_v3_coord_to_lonlat([geom["x"], geom["y"]])}

    return None


def _monahinga_v3_identify_url(source: dict, bbox: BBox) -> str:
    query_url = str(source["query_url"])
    if "/MapServer/query" in query_url:
        base = query_url.replace("/MapServer/query", "/MapServer/identify")
    elif query_url.rstrip("/").endswith("/query"):
        base = query_url.rsplit("/", 1)[0] + "/identify"
    elif query_url.rstrip("/").endswith("/MapServer"):
        base = query_url.rstrip("/") + "/identify"
    else:
        raise ValueError("identify fallback only applies to MapServer-style sources")

    x1, y1 = _monahinga_v3_lonlat_to_webmercator(float(bbox.min_lon), float(bbox.min_lat))
    x2, y2 = _monahinga_v3_lonlat_to_webmercator(float(bbox.max_lon), float(bbox.max_lat))
    xmin, xmax = sorted([x1, x2])
    ymin, ymax = sorted([y1, y2])

    map_extent = {
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
        "spatialReference": {"wkid": 102100},
    }

    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0

    params = {
        "f": "json",
        "tolerance": os.getenv("MONAHINGA_FREE_PARCEL_IDENTIFY_TOLERANCE", "12"),
        "returnGeometry": "true",
        "imageDisplay": "1000,1000,96",
        "mapExtent": json.dumps(map_extent, separators=(",", ":")),
        "geometryType": "esriGeometryPoint",
        "geometry": json.dumps({"x": cx, "y": cy, "spatialReference": {"wkid": 102100}}, separators=(",", ":")),
        "sr": "102100",
        "layers": os.getenv("MONAHINGA_FREE_PARCEL_IDENTIFY_LAYERS", "all:0,1,2,3,4,5,6,7,8,9,10"),
    }

    return base + "?" + urlencode(params)



# MONAHINGA_WY_COUNTIES_HARD_STOP_V8_2026_05_08:
# Reject obvious non-parcel Identify results before they become parcel GeoJSON.
def _monahinga_v8_identify_result_is_nonparcel(result: dict, props: dict) -> bool:
    layer_name = str(result.get("layerName") or props.get("LAYER_NAME") or "").upper()
    display_name = str(result.get("displayFieldName") or props.get("DISPLAY_FIELD_NAME") or "").upper()
    value_name = str(result.get("value") or props.get("VALUE") or "").upper()
    joined = " ".join([layer_name, display_name, value_name])

    hard_bad = (
        "COUNTY", "COUNTIES", "STATE", "STATES", "CITY", "CITIES",
        "ROAD", "ROADS", "HIGHWAY", "ROW", "BOUNDARY", "BOUNDARIES",
        "WATER", "STREAM", "RIVER", "LABEL", "ANNOTATION"
    )

    if any(word in joined for word in hard_bad):
        return True

    return False


def _monahinga_v8_identify_result_has_parcel_word(result: dict, props: dict) -> bool:
    layer_name = str(result.get("layerName") or props.get("LAYER_NAME") or "").upper()
    display_name = str(result.get("displayFieldName") or props.get("DISPLAY_FIELD_NAME") or "").upper()
    value_name = str(result.get("value") or props.get("VALUE") or "").upper()
    keys = " ".join(str(k).upper() for k in props.keys())
    joined = " ".join([layer_name, display_name, value_name, keys])

    good_words = (
        "PARCEL", "PRIVATE", "TAX", "CADASTRAL", "OWNERSHIP",
        "PROPERTY", "PIN", "APN", "ACCOUNT", "OWNER"
    )

    return any(word in joined for word in good_words)



def _monahinga_v3_identify_to_geojson(raw: dict, source: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("identify response was not an object")
    if raw.get("error"):
        err = raw.get("error") or {}
        raise ValueError(str(err.get("message") or err))

    features = []
    for result in raw.get("results") or []:
        if not isinstance(result, dict):
            continue
        geom = _monahinga_v3_geometry_to_lonlat(result.get("geometry") or {})
        if not geom:
            continue
        props = dict(result.get("attributes") or {})
        props.setdefault("LAYER_NAME", result.get("layerName") or "")
        props.setdefault("LAYER_ID", result.get("layerId") or "")
        props.setdefault("DISPLAY_FIELD_NAME", result.get("displayFieldName") or "")
        props.setdefault("VALUE", result.get("value") or "")

        if _monahinga_v8_identify_result_is_nonparcel(result, props):
            print(
                "[parcel-preview] HARD REJECT identify non-parcel layer: "
                f"LAYER_NAME={props.get('LAYER_NAME')} VALUE={props.get('VALUE')}"
            )
            continue

        if not _monahinga_v8_identify_result_has_parcel_word(result, props):
            print(
                "[parcel-preview] HARD REJECT identify result with no parcel clues: "
                f"LAYER_NAME={props.get('LAYER_NAME')} VALUE={props.get('VALUE')}"
            )
            continue

        features.append({"type": "Feature", "properties": props, "geometry": geom})

    if not features:
        raise ValueError("identify returned zero usable private parcel geometries after rejecting county/state/road layers")

    return {"type": "FeatureCollection", "features": features}


def _monahinga_v3_try_identify_source(source: dict, bbox: BBox) -> tuple[dict | None, str]:
    if "/MapServer" not in str(source.get("query_url", "")):
        return None, "identify skipped: not a MapServer source"

    try:
        url = _monahinga_v3_identify_url(source, bbox)
        raw = _monahinga_v2_read_json_url(url)
        fc_raw = _monahinga_v3_identify_to_geojson(raw, source)
        fc = _monahinga_v2_normalize_public_geojson(fc_raw, source)
        return fc, f"ok identify features={len(fc.get('features') or [])}"
    except Exception as exc:
        return None, f"identify failed: {type(exc).__name__}: {exc}"




# MONAHINGA_WY_LAYER_DISCOVERY_V9_2026_05_09:
# Some ArcGIS MapServer roots do not return usable parcel polygons from /MapServer/query.
# This fallback discovers likely parcel layers and queries /MapServer/{layer_id}/query BBox-scoped.
def _monahinga_v9_mapserver_root_url(source: dict) -> str:
    query_url = str(source.get("query_url") or "").strip()
    if "/MapServer/query" in query_url:
        return query_url.replace("/MapServer/query", "/MapServer")
    if query_url.rstrip("/").endswith("/MapServer"):
        return query_url.rstrip("/")
    if "/MapServer/" in query_url:
        return query_url.split("/MapServer/", 1)[0] + "/MapServer"
    raise ValueError("not a MapServer source")


def _monahinga_v9_layer_score(layer: dict) -> int:
    name = str(layer.get("name") or layer.get("title") or "").upper()
    layer_id = str(layer.get("id") or "")
    joined = " ".join([name, layer_id])

    hard_bad = (
        "COUNTY", "COUNTIES", "STATE", "STATES", "CITY", "CITIES",
        "ROAD", "ROADS", "HIGHWAY", "ROW", "RIGHT OF WAY", "BOUNDARY",
        "BOUNDARIES", "WATER", "STREAM", "RIVER", "LABEL", "ANNOTATION",
        "SECTION", "TOWNSHIP", "TOWNSHIP RANGE", "PLSS"
    )
    if any(word in joined for word in hard_bad):
        return -100

    score = 0
    for word, weight in (
        ("PARCEL", 100),
        ("CADASTRAL", 80),
        ("PROPERTY", 70),
        ("OWNERSHIP", 70),
        ("OWNER", 60),
        ("TAX", 55),
        ("ASSESS", 45),
        ("CAMA", 45),
        ("PRIVATE", 35),
        ("LAND", 15),
    ):
        if word in joined:
            score += weight

    return score


def _monahinga_v9_discover_candidate_layers(source: dict) -> tuple[list[dict], str]:
    try:
        root = _monahinga_v9_mapserver_root_url(source)
        raw = _monahinga_v2_read_json_url(root + "?f=json")
        layers = raw.get("layers") or []
        if not isinstance(layers, list):
            return [], "layer discovery: no layers list"

        scored = []
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            if "id" not in layer:
                continue
            score = _monahinga_v9_layer_score(layer)
            if score > 0:
                scored.append((score, layer))

        scored.sort(key=lambda item: item[0], reverse=True)
        limit = int(os.getenv("MONAHINGA_FREE_PARCEL_LAYER_DISCOVERY_LIMIT", "8"))
        chosen = [layer for _score, layer in scored[:max(1, limit)]]
        names = ", ".join(str(layer.get("id")) + ":" + str(layer.get("name") or "") for layer in chosen[:6])
        if not chosen:
            return [], "layer discovery: no likely parcel layers"
        return chosen, "layer discovery candidates: " + names
    except Exception as exc:
        return [], f"layer discovery failed: {type(exc).__name__}: {exc}"


def _monahinga_v9_layer_query_url(source: dict, bbox: BBox, layer_id, fmt: str) -> str:
    root = _monahinga_v9_mapserver_root_url(source)
    query_url = root.rstrip("/") + "/" + str(layer_id) + "/query"

    geometry = json.dumps({
        "xmin": float(bbox.min_lon),
        "ymin": float(bbox.min_lat),
        "xmax": float(bbox.max_lon),
        "ymax": float(bbox.max_lat),
        "spatialReference": {"wkid": 4326},
    }, separators=(",", ":"))

    params = {
        "f": fmt,
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "geometryType": "esriGeometryEnvelope",
        "geometry": geometry,
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "resultRecordCount": str(source.get("result_record_count") or os.getenv("MONAHINGA_FREE_PARCEL_LIMIT", "200")),
    }

    return query_url + "?" + urlencode(params)


def _monahinga_v9_try_discovered_layers(source: dict, bbox: BBox) -> tuple[dict | None, str]:
    if "/MapServer" not in str(source.get("query_url", "")):
        return None, "layer discovery skipped: not a MapServer source"

    layers, discovery_status = _monahinga_v9_discover_candidate_layers(source)
    if not layers:
        print(f"[parcel-preview] source attempt {source.get('id')} {discovery_status}")
        return None, discovery_status

    statuses = [discovery_status]
    for layer in layers:
        layer_id = layer.get("id")
        layer_name = str(layer.get("name") or "")
        layer_source = dict(source)
        layer_source["id"] = str(source.get("id") or "source") + "_layer_" + str(layer_id)
        layer_source["label"] = str(source.get("label") or "ArcGIS parcel source") + " layer " + str(layer_id) + (" " + layer_name if layer_name else "")
        layer_source["query_url"] = _monahinga_v9_mapserver_root_url(source).rstrip("/") + "/" + str(layer_id) + "/query"

        for fmt in ("geojson", "json"):
            try:
                url = _monahinga_v9_layer_query_url(source, bbox, layer_id, fmt)
                raw = _monahinga_v2_read_json_url(url)
                if fmt == "json" and (raw.get("type") != "FeatureCollection"):
                    raw = _monahinga_v2_esri_json_to_geojson(raw)
                fc = _monahinga_v2_normalize_public_geojson(raw, layer_source)
                status = f"ok layer={layer_id} fmt={fmt} features={len(fc.get('features') or [])}"
                print(f"[parcel-preview] FREE LAYER SOURCE SUCCESS {source.get('id')} {status}")
                return fc, status
            except Exception as exc:
                status = f"layer={layer_id} fmt={fmt} failed: {type(exc).__name__}: {exc}"
                statuses.append(status)
                print(f"[parcel-preview] source attempt {source.get('id')} {status}")

    return None, " | ".join(statuses[-4:])


def _monahinga_v2_try_source(source: dict, bbox: BBox) -> tuple[dict | None, str]:
    last = "not attempted"
    for fmt in ("geojson", "json"):
        url = _monahinga_v2_arcgis_url(source, bbox, fmt)
        try:
            raw = _monahinga_v2_read_json_url(url)
            if fmt == "json" and (raw.get("type") != "FeatureCollection"):
                raw = _monahinga_v2_esri_json_to_geojson(raw)
            fc = _monahinga_v2_normalize_public_geojson(raw, source)
            return fc, f"ok fmt={fmt} features={len(fc.get('features') or [])}"
        except Exception as exc:
            last = f"fmt={fmt} failed: {type(exc).__name__}: {exc}"
            print(f"[parcel-preview] source attempt {source['id']} {last}")

    layer_fc, layer_status = _monahinga_v9_try_discovered_layers(source, bbox)
    print(f"[parcel-preview] source attempt {source['id']} {layer_status}")
    if layer_fc:
        return layer_fc, layer_status

    identify_fc, identify_status = _monahinga_v3_try_identify_source(source, bbox)
    print(f"[parcel-preview] source attempt {source['id']} {identify_status}")
    if identify_fc:
        return identify_fc, identify_status

    return None, last + " | " + layer_status + " | " + identify_status


# MONAHINGA_MANUAL_ARCGIS_URL_V12_2026_05_09:
# Manual county/provider ArcGIS override. Always queried only against the current BBox.
def _monahinga_v12_normalize_manual_arcgis_url(raw_url: str) -> str:
    url = str(raw_url or "").strip()
    if not url:
        raise ValueError("manual ArcGIS URL is empty")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("manual ArcGIS URL must start with http:// or https://")

    url = url.split("#", 1)[0].split("?", 1)[0].rstrip("/")

    if url.endswith("/query"):
        return url

    parts = url.split("/")
    if len(parts) >= 2 and parts[-1].isdigit() and parts[-2] in ("MapServer", "FeatureServer"):
        return url + "/query"

    if url.endswith("/MapServer") or url.endswith("/FeatureServer"):
        return url + "/query"

    if "/MapServer/" in url:
        return url.split("/MapServer/", 1)[0] + "/MapServer/query"

    if "/FeatureServer/" in url:
        return url.split("/FeatureServer/", 1)[0] + "/FeatureServer/query"

    raise ValueError("manual ArcGIS URL must contain MapServer or FeatureServer")


def _monahinga_v12_source_from_manual_url(raw_url: str) -> dict:
    query_url = _monahinga_v12_normalize_manual_arcgis_url(raw_url)
    label = "Manual ArcGIS parcel service"
    if "/FeatureServer/" in query_url or query_url.endswith("/FeatureServer/query"):
        label = "Manual ArcGIS FeatureServer parcel service"
    elif "/MapServer/" in query_url or query_url.endswith("/MapServer/query"):
        label = "Manual ArcGIS MapServer parcel service"

    return {
        "id": "manual_arcgis_url",
        "label": label,
        "region": "manual",
        "bbox_scoped": True,
        "query_url": query_url,
    }


def _monahinga_v12_try_manual_arcgis_url(raw_url: str, bbox: BBox) -> tuple[dict | None, str]:
    if not str(raw_url or "").strip():
        return None, "manual ArcGIS URL not provided"

    source = _monahinga_v12_source_from_manual_url(raw_url)
    fc, status = _monahinga_v2_try_source(source, bbox)

    if fc:
        fc.setdefault("properties", {})
        fc["properties"]["monahinga_parcel_source"] = "manual_arcgis_url"
        fc["properties"]["monahinga_parcel_source_label"] = source["label"]
        fc["properties"]["monahinga_manual_arcgis_url"] = str(raw_url or "").strip()
        fc["properties"]["monahinga_source_note"] = "Manual ArcGIS parcel source; verify ownership/access against county/provider records."
        return fc, "manual ArcGIS source loaded: " + status

    return None, "manual ArcGIS source failed: " + status


def _monahinga_v2_free_public_ladder(bbox: BBox) -> tuple[dict | None, str, str, list[dict]]:
    if os.getenv("MONAHINGA_FREE_PUBLIC_PARCELS", "1").strip().lower() in {"0", "false", "no", "off"}:
        return None, "", "", [{"source": "free_public", "status": "disabled"}]

    region = _monahinga_v2_bbox_region(bbox)
    sources = []
    for source in MONAHINGA_FREE_PARCEL_SOURCE_V2:
        if source["region"] == region:
            sources.append(source)
    if region == "potter_pa":
        sources.extend([s for s in MONAHINGA_FREE_PARCEL_SOURCE_V2 if s["region"] == "pennsylvania"])

    if not sources:
        print(f"[parcel-preview] free ladder skipped: no source for region={region}")
        return None, "", "", [{"source": "free_public", "status": f"no source for region {region}"}]

    attempts = []
    for source in sources:
        fc, status = _monahinga_v2_try_source(source, bbox)
        attempts.append({"source": source["id"], "label": source["label"], "status": status})
        if fc:
            print(f"[parcel-preview] FREE POLYGON SOURCE SUCCESS {source['id']}: {status}")
            return fc, source["id"], source["label"], attempts

    print("[parcel-preview] FREE SOURCES FAILED: " + " | ".join(a["source"] + "=" + a["status"] for a in attempts))
    return None, "", "", attempts


def _monahinga_v2_preview_payload(bbox: BBox, manual_arcgis_url: str | None = None) -> dict:
    manual_attempts = []
    if manual_arcgis_url and str(manual_arcgis_url).strip():
        try:
            configured, manual_status = _monahinga_v12_try_manual_arcgis_url(manual_arcgis_url, bbox)
            manual_attempts.append({"source": "manual_arcgis_url", "label": "Manual ArcGIS parcel service", "status": manual_status})
            if configured is not None:
                source_kind = "manual_arcgis_url"
                source_ref = "Manual ArcGIS parcel service"
                attempts = manual_attempts
            else:
                configured, source_kind, source_ref, free_attempts = _monahinga_v2_free_public_ladder(bbox)
                attempts = manual_attempts + free_attempts
        except Exception as exc:
            manual_attempts.append({"source": "manual_arcgis_url", "label": "Manual ArcGIS parcel service", "status": f"failed: {type(exc).__name__}: {exc}"})
            configured, source_kind, source_ref, free_attempts = _monahinga_v2_free_public_ladder(bbox)
            attempts = manual_attempts + free_attempts
    else:
        configured, source_kind, source_ref, attempts = _monahinga_v2_free_public_ladder(bbox)

    if configured is None:
        try:
            configured, source_kind, source_ref = _monahinga_configured_parcel_geojson()
            if configured is not None:
                attempts.append({"source": source_kind, "label": source_ref, "status": "configured source loaded"})
        except Exception as exc:
            attempts.append({"source": "configured", "status": f"failed: {type(exc).__name__}: {exc}"})
            print(f"[parcel-preview] configured source failed: {exc}")

    if configured is None:
        configured = _monahinga_demo_parcel_geojson_for_bbox(bbox)
        source_kind = "auto_demo"
        source_ref = "generated_from_selected_bbox"
        attempts.append({"source": "auto_demo", "label": "DEMO FALLBACK - NOT REAL PARCELS", "status": "real parcel source failed; visual grid only"})

    props = configured.get("properties") or {}
    feature_count = len(configured.get("features") or [])
    label = props.get("monahinga_parcel_source_label") or source_ref or "Private parcels"
    warning = props.get("monahinga_parcel_warning") or "Verify county records, access, permission, and regulations."
    render_ready_sources = {"manual_arcgis_url", "lawrence_county_sd_parcels", "wyoming_public_arcgis", "wyoming_private_arcgis", "potter_county_pa_taxparcels", "allegany_county_ny_parcels_2024", "summit_county_co_assessor_taxmap_parcels", "summit_county_co_assessor_taxmap_parcels_disabled", "summit_county_co_parcel_query", "pa_pasda_parcels", "pa_pasda_apps_parcels", "pa_dep_parcels", "configured_path", "configured_url", "regrid"}

    return {
        "ok": True,
        "bbox": bbox.as_list(),
        "source": source_kind,
        "source_ref": source_ref,
        "source_label": label,
        "feature_count": feature_count,
        "geojson": configured,
        "message": f"{label} loaded for this selected area. {warning}",
        "render_ready": source_kind in render_ready_sources,
        "source_attempts": attempts,
        "source_summary": _monahinga_v14_parcel_source_summary(configured, source_kind, label),
        "proof_required": "Verify one known owner/parcel ID against the public/county source before calling this confirmed real private-property truth.",
    }


@app.get("/parcel-preview")
def parcel_preview_get(min_lon: float, min_lat: float, max_lon: float, max_lat: float, manual_arcgis_url: str | None = None) -> dict:
    try:
        bbox = BBox.normalized(min_lon, min_lat, max_lon, max_lat)
        return _monahinga_v2_preview_payload(bbox, manual_arcgis_url=manual_arcgis_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Parcel preview unavailable: {type(exc).__name__}: {exc}")


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



# MONAHINGA_AUTO_PRIVATE_PARCEL_RENDER_BRIDGE_V1_2026_05_08: automatic private parcel source bridge.
def _monahinga_read_json_file(path_value: str) -> dict:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    if not path.exists():
        raise FileNotFoundError(f"Parcel GeoJSON path does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _monahinga_read_json_url(url_value: str) -> dict:
    parsed = urlparse(url_value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Parcel GeoJSON URL must start with http:// or https://")
    req = Request(url_value, headers={"User-Agent": "Monahinga-HUNTER/1.0"})
    with urlopen(req, timeout=20) as response:
        raw = response.read(8 * 1024 * 1024)
    return json.loads(raw.decode("utf-8"))


def _monahinga_bbox_demo_cells(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> list[dict]:
    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat
    x0 = min_lon + lon_span * 0.18
    x1 = min_lon + lon_span * 0.50
    x2 = min_lon + lon_span * 0.82
    y0 = min_lat + lat_span * 0.30
    y1 = min_lat + lat_span * 0.54
    y2 = min_lat + lat_span * 0.76
    boxes = [
        ("AUTO-DEMO-001", "DEMO OWNER A - NOT REAL", [[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]]),
        ("AUTO-DEMO-002", "DEMO OWNER B - NOT REAL", [[x1,y0],[x2,y0],[x2,y1],[x1,y1],[x1,y0]]),
        ("AUTO-DEMO-003", "DEMO OWNER C - NOT REAL", [[x0,y1],[x1,y1],[x1,y2],[x0,y2],[x0,y1]]),
        ("AUTO-DEMO-004", "DEMO OWNER D - NOT REAL", [[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]),
    ]
    features = []
    for parcel_id, owner, coords in boxes:
        features.append({
            "type": "Feature",
            "properties": {"PARCEL_ID": parcel_id, "OWNER": owner, "monahinga_demo": True},
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        })
    return features


def _monahinga_demo_parcel_geojson_for_bbox(bbox: BBox) -> dict:
    return {
        "type": "FeatureCollection",
        "features": _monahinga_bbox_demo_cells(float(bbox.min_lon), float(bbox.min_lat), float(bbox.max_lon), float(bbox.max_lat)),
        "properties": {
            "monahinga_parcel_source": "auto_demo",
            "monahinga_parcel_source_label": "DEMO FALLBACK - NOT REAL PARCELS",
            "monahinga_parcel_warning": "DEMO FALLBACK ONLY. These big square cells are visual placeholders, not real parcels, not ownership, and not parcel truth. Fix or configure a county parcel source before relying on parcel boundaries.",
            "monahinga_feature_count": 4,
            "monahinga_confidence": "demo_only",
        },
    }


def _monahinga_normalize_parcel_geojson(geojson: dict, source: str, label: str, warning: str) -> dict:
    if not isinstance(geojson, dict):
        raise ValueError("Parcel source did not return a GeoJSON object.")
    if geojson.get("type") != "FeatureCollection":
        raise ValueError("Parcel source must be a GeoJSON FeatureCollection.")
    features = geojson.get("features")
    if not isinstance(features, list):
        raise ValueError("Parcel source FeatureCollection is missing features[].")
    geojson.setdefault("properties", {})
    geojson["properties"]["monahinga_parcel_source"] = source
    geojson["properties"]["monahinga_parcel_source_label"] = label
    geojson["properties"]["monahinga_parcel_warning"] = warning
    geojson["properties"]["monahinga_feature_count"] = len(features)
    return geojson


def _monahinga_configured_parcel_geojson() -> tuple[dict | None, str, str]:
    path_value = os.getenv("MONAHINGA_PARCEL_GEOJSON_PATH", "").strip()
    url_value = os.getenv("MONAHINGA_PARCEL_GEOJSON_URL", "").strip()
    if path_value:
        geojson = _monahinga_read_json_file(path_value)
        return (_monahinga_normalize_parcel_geojson(geojson, "configured_path", f"Configured parcel GeoJSON path: {Path(path_value).name}", "Configured parcel GeoJSON. Ownership context only; verify county records, access, permission, and regulations."), "configured_path", path_value)
    if url_value:
        geojson = _monahinga_read_json_url(url_value)
        return (_monahinga_normalize_parcel_geojson(geojson, "configured_url", "Configured parcel GeoJSON URL", "Configured parcel GeoJSON URL. Ownership context only; verify county records, access, permission, and regulations."), "configured_url", url_value)
    return None, "", ""




# MONAHINGA_REGRID_READINESS_SELF_CHECK_PASS4_2026_05_08: safe source status endpoint. Does not expose secrets.

# MONAHINGA_LAND_SOURCE_READINESS_STATUS_V1_2026_05_08: parcels + PAD-US truth/readiness endpoint.

# MONAHINGA_POTTER_ADDRESS_LOOKUP_V17_2026_05_09:
# Exact rural-address fallback for Potter County parcel searches.
def _monahinga_v17_geojson_bounds_and_center(fc: dict) -> tuple[list[float], float, float]:
    xs = []
    ys = []

    def walk(obj):
        if isinstance(obj, (list, tuple)):
            if len(obj) >= 2 and isinstance(obj[0], (int, float)) and isinstance(obj[1], (int, float)):
                xs.append(float(obj[0]))
                ys.append(float(obj[1]))
            else:
                for child in obj:
                    walk(child)

    for feature in (fc.get("features") or []):
        geom = feature.get("geometry") or {}
        walk(geom.get("coordinates"))

    if not xs or not ys:
        raise ValueError("parcel lookup returned no usable coordinates")

    min_lon, max_lon = min(xs), max(xs)
    min_lat, max_lat = min(ys), max(ys)
    pad_lon = max(0.0015, (max_lon - min_lon) * 1.8)
    pad_lat = max(0.0015, (max_lat - min_lat) * 1.8)
    bbox = [min_lon - pad_lon, min_lat - pad_lat, max_lon + pad_lon, max_lat + pad_lat]
    return bbox, (min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0


def _monahinga_v17_first_feature_collection(raw: dict) -> dict:
    if raw.get("type") == "FeatureCollection":
        return raw
    return _monahinga_v2_esri_json_to_geojson(raw)


def _monahinga_v17_potter_address_candidates(query: str) -> list[str]:
    q = str(query or "").strip()
    candidates = []
    if "1854" in q and re.search(r"(sr\s*44|state route\s*44|pa[-\s]*44|route\s*44)", q, re.I):
        candidates.extend([
            "Street_Number = '1854'",
            "Street_Number = '1854' AND Situs_Street LIKE '%44%'",
            "Street_Number = '1854' AND Situs_Street LIKE '%ROUTE%'",
        ])
    return candidates


def _monahinga_v17_potter_feature_score(props: dict, query: str) -> int:
    joined = " ".join(str(props.get(k, "")) for k in (
        "Street_Number", "Situs_Street", "Situs_Suffix", "Situs_Direction",
        "Situs_Description_1", "Situs_Description_2", "Map_Number",
        "Owner_Name_1", "Owner_Name_2",
    )).upper()
    q = str(query or "").upper()
    score = 0
    if "1854" in joined:
        score += 100
    if "44" in joined:
        score += 60
    if "STATE" in joined or "ROUTE" in joined or "SR" in joined or "PA" in joined:
        score += 20
    if "SHINGLEHOUSE" in q:
        score += 10
    return score


@app.get("/parcel-address-lookup")
def parcel_address_lookup(query: str) -> dict:
    q = str(query or "").strip()
    if not q:
        return {"ok": False, "message": "No address query provided."}

    # Keep this deliberately narrow for now. It is a surgical fallback for the
    # known Shinglehouse / Potter County rural route problem.
    if not re.search(r"(shinglehouse|potter|sr\s*44|state route\s*44|pa[-\s]*44|route\s*44)", q, re.I):
        return {"ok": False, "message": "No supported county parcel lookup for this query."}

    source = next((s for s in MONAHINGA_FREE_PARCEL_SOURCE_V2 if s.get("id") == "potter_county_pa_taxparcels"), None)
    if not source:
        return {"ok": False, "message": "Potter County parcel source is not configured."}

    attempts = []
    best = None
    best_score = -1

    for where in _monahinga_v17_potter_address_candidates(q):
        try:
            url = source["query_url"] + "?" + urlencode({
                "f": "geojson",
                "where": where,
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultRecordCount": "25",
            })
            raw = _monahinga_v2_read_json_url(url)
            fc = _monahinga_v17_first_feature_collection(raw)
            for feature in (fc.get("features") or []):
                props = dict(feature.get("properties") or {})
                score = _monahinga_v17_potter_feature_score(props, q)
                if score > best_score:
                    best_score = score
                    best = {"feature": feature, "props": props, "where": where}
            attempts.append({"where": where, "status": f"ok features={len(fc.get('features') or [])}"})
        except Exception as exc:
            attempts.append({"where": where, "status": f"failed: {type(exc).__name__}: {exc}"})

    if not best:
        return {"ok": False, "message": "No matching Potter County parcel found.", "attempts": attempts}

    fc_one = {"type": "FeatureCollection", "features": [best["feature"]]}
    bbox, lat, lon = _monahinga_v17_geojson_bounds_and_center(fc_one)
    props = best["props"]
    display = "1854 State Route 44 N, Shinglehouse, Potter County, PA 16748"

    return {
        "ok": True,
        "source": "potter_county_pa_taxparcels",
        "display_name": display,
        "lat": lat,
        "lon": lon,
        "bbox": bbox,
        "parcel_id": props.get("Map_Number") or props.get("Join1") or "",
        "owner": props.get("Owner_Name_1") or "",
        "situs": " ".join(str(props.get(k, "")).strip() for k in ("Street_Number", "Situs_Street", "Situs_Suffix", "Situs_Direction") if str(props.get(k, "")).strip()),
        "acres": props.get("Acreage"),
        "year_built": props.get("Year_Built"),
        "attempts": attempts,
        "note": "Parcel-based address match. Verify against county records before field use.",
    }




# MONAHINGA_KNOWN_ADDRESS_LOOKUP_V18_2026_05_09:
# Exact known-address fallback. This is intentionally narrow: it only handles
# the verified Shinglehouse/Potter County address that Nominatim misroutes.
def _monahinga_v18_fc_bounds_and_center(fc: dict) -> tuple[list[float], float, float]:
    xs = []
    ys = []

    def walk(coords):
        if isinstance(coords, (list, tuple)):
            if len(coords) >= 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
                xs.append(float(coords[0]))
                ys.append(float(coords[1]))
            else:
                for child in coords:
                    walk(child)

    for feature in (fc.get("features") or []):
        geom = feature.get("geometry") or {}
        walk(geom.get("coordinates"))

    if not xs or not ys:
        raise ValueError("no geometry coordinates returned for known address")

    min_lon, max_lon = min(xs), max(xs)
    min_lat, max_lat = min(ys), max(ys)
    pad_lon = max(0.0015, (max_lon - min_lon) * 2.0)
    pad_lat = max(0.0015, (max_lat - min_lat) * 2.0)
    return [min_lon - pad_lon, min_lat - pad_lat, max_lon + pad_lon, max_lat + pad_lat], (min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0


def _monahinga_v18_esri_or_geojson_to_fc(raw: dict) -> dict:
    if isinstance(raw, dict) and raw.get("type") == "FeatureCollection":
        return raw
    return _monahinga_v2_esri_json_to_geojson(raw)


def _monahinga_v18_is_known_shinglehouse_address(query: str) -> bool:
    q = str(query or "").upper()
    return ("1854" in q and "44" in q and ("SHINGLEHOUSE" in q or "16748" in q))


def _monahinga_v18_query_potter_known_address(source: dict) -> tuple[dict | None, str]:
    # Public records shown by real-estate/public-record pages identify this
    # property as APN 120 43315 / parcel number 1200060221. Try those stable
    # identifiers first, then common Potter/PASDA field names.
    candidates = [
        "Map_Number = '120 43315'",
        "Map_Number = '12043315'",
        "Join1 = '1200060221'",
        "PARCEL_ID = '1200060221'",
        "PARCEL_ID = '120 43315'",
        "PIN = '1200060221'",
        "APN = '120 43315'",
    ]
    errors = []
    for where in candidates:
        try:
            url = source["query_url"] + "?" + urlencode({
                "f": "geojson",
                "where": where,
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultRecordCount": "5",
            })
            raw = _monahinga_v2_read_json_url(url)
            fc = _monahinga_v18_esri_or_geojson_to_fc(raw)
            features = fc.get("features") or []
            if features:
                return {"type": "FeatureCollection", "features": features[:1]}, f"ok where={where} features={len(features)}"
            errors.append(f"{where}: zero features")
        except Exception as exc:
            errors.append(f"{where}: {type(exc).__name__}: {exc}")
    return None, " | ".join(errors[-3:])


@app.get("/known-address-lookup")
def known_address_lookup(query: str) -> dict:
    q = str(query or "").strip()
    if not _monahinga_v18_is_known_shinglehouse_address(q):
        return {"ok": False, "message": "No exact known-address fallback for this query."}

    source = next((s for s in MONAHINGA_FREE_PARCEL_SOURCE_V2 if s.get("id") == "potter_county_pa_taxparcels"), None)
    if not source:
        return {"ok": False, "message": "Potter County parcel source is not configured."}

    try:
        fc, status = _monahinga_v18_query_potter_known_address(source)
        if not fc:
            return {"ok": False, "message": "Known address parcel lookup failed.", "status": status}

        bbox, lat, lon = _monahinga_v18_fc_bounds_and_center(fc)
        props = dict((fc.get("features") or [{}])[0].get("properties") or {})
        return {
            "ok": True,
            "display_name": "1854 State Route 44 N, Shinglehouse, Potter County, PA 16748",
            "lat": lat,
            "lon": lon,
            "bbox": bbox,
            "source": "potter_county_pa_taxparcels",
            "status": status,
            "parcel_id": props.get("Map_Number") or props.get("Join1") or props.get("PARCEL_ID") or "120 43315",
            "owner": props.get("Owner_Name_1") or props.get("OWNER") or "",
            "note": "Known address matched using Potter County parcel identifiers. Search moves the map only; draw the bbox after confirming the location.",
        }
    except Exception as exc:
        return {"ok": False, "message": f"Known address lookup failed: {type(exc).__name__}: {exc}"}



@app.get("/parcel-source-status")
def parcel_source_status():
    """Report land-source readiness without exposing secrets or changing run behavior.

    This endpoint is intentionally read-only. It helps the operator distinguish:
    - PAD-US public/hunting signal readiness
    - real parcel source readiness
    - demo parcel fallback

    It must not claim permission, legal access, or confirmed private ownership.
    """
    padus_env_name = "PADUS_PUBLIC_ACCESS_FEATURESERVER_URL"
    padus_url = (os.getenv(padus_env_name) or "").strip()
    parcel_path = (os.getenv("MONAHINGA_PARCEL_GEOJSON_PATH") or "").strip()
    parcel_url = (os.getenv("MONAHINGA_PARCEL_GEOJSON_URL") or "").strip()
    regrid_token_present = bool((os.getenv("MONAHINGA_REGRID_TOKEN") or "").strip())
    regrid_base_url = (os.getenv("MONAHINGA_REGRID_BASE_URL") or "").strip()

    configured_sources = []
    if parcel_path:
        configured_sources.append({
            "kind": "configured_geojson_path",
            "configured": True,
            "label": Path(parcel_path).name or "configured GeoJSON path",
            "secret_exposed": False,
        })
    if parcel_url:
        parsed = urlparse(parcel_url)
        configured_sources.append({
            "kind": "configured_geojson_url",
            "configured": True,
            "label": parsed.netloc or "configured GeoJSON URL",
            "secret_exposed": False,
        })
    if regrid_token_present or regrid_base_url:
        configured_sources.append({
            "kind": "regrid",
            "configured": regrid_token_present,
            "label": "Regrid token present" if regrid_token_present else "Regrid base URL present but token missing",
            "secret_exposed": False,
        })

    free_sources = []
    for source in MONAHINGA_FREE_PARCEL_SOURCE_V2:
        free_sources.append({
            "id": source.get("id"),
            "label": source.get("label"),
            "region": source.get("region"),
            "bbox_scoped": True,
        })

    parcel_mode = "demo_fallback_only"
    if configured_sources:
        parcel_mode = "configured_or_regrid_available"
    elif free_sources:
        parcel_mode = "free_public_ladder_available"

    return {
        "ok": True,
        "active_mode": "land_source_readiness",
        "headline": "Parcels / PAD-US readiness",
        "padus": {
            "configured": bool(padus_url),
            "env_var": padus_env_name,
            "source_label": "PAD-US public/hunting signal",
            "bbox_scoped": True,
            "secret_exposed": False,
            "status": "configured" if padus_url else "not configured",
            "warning": "PAD-US is a public/hunting signal, not permission or guaranteed legal access.",
        },
        "parcels": {
            "mode": parcel_mode,
            "configured_sources": configured_sources,
            "free_public_sources": free_sources,
            "demo_fallback_available": True,
            "bbox_scoped": True,
            "safe_to_claim_real_private_property": False,
            "warning": "Parcel overlays are ownership context only until one known parcel/owner is verified against county or provider records.",
        },
        "protected_systems_untouched": [
            "BBox terrain envelope",
            "selection_polygon transport",
            "parcel_geojson payload flow",
            "PAD-US preview flow",
            "DEM generation",
            "scoring stack",
            "2D/3D orientation",
        ],
        "proof_required": [
            "Confirm the selected BBox is small and local enough for PAD-US/parcel lookup.",
            "Verify one known owner or parcel ID against the county/provider source before calling parcel truth confirmed.",
            "Verify ownership, permission, access, season dates, tags, safety, and local regulations before field use.",
        ],
    }


@app.post("/parcel-preview")
def parcel_preview_post(req: ParcelPreviewRequest):
    try:
        bbox = BBox.normalized(req.min_lon, req.min_lat, req.max_lon, req.max_lat)
        return _monahinga_v2_preview_payload(bbox, manual_arcgis_url=req.manual_arcgis_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Private parcel preview unavailable: {type(exc).__name__}: {exc}")


@app.post("/preview-wildlife")
def preview_wildlife(req: RunRequest):
    try:
        bbox = BBox.normalized(req.min_lon, req.min_lat, req.max_lon, req.max_lat)
        result = build_wildlife_atmosphere(bbox)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))



# MONAHINGA_RENDER_PAGE2_AUTO_PARCEL_CARRY_V25_2026_05_09:
# Backend safety net: if Page 1 preview parcels did not survive the browser run payload,
# fetch a compact BBox-scoped real parcel subset during /run-terrain-truth.
def _monahinga_v25_round_coord(value):
    try:
        return round(float(value), 6)
    except Exception:
        return value


def _monahinga_v25_compact_coords(coords):
    if isinstance(coords, (list, tuple)):
        if len(coords) >= 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
            return [_monahinga_v25_round_coord(coords[0]), _monahinga_v25_round_coord(coords[1])]
        return [_monahinga_v25_compact_coords(item) for item in coords]
    return coords


def _monahinga_v25_prop_value(props: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = props.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _monahinga_v25_detect_fields(features: list[dict], keys: tuple[str, ...]) -> tuple[list[str], int]:
    found: list[str] = []
    value_count = 0
    seen = set()
    for feature in features:
        props = feature.get("properties") or {}
        hit_this_feature = False
        for key in keys:
            value = props.get(key)
            if value is not None and str(value).strip():
                if key not in seen:
                    seen.add(key)
                    found.append(key)
                hit_this_feature = True
        if hit_this_feature:
            value_count += 1
    return found, value_count


def _monahinga_v25_compact_props(props: dict) -> dict:
    props = dict(props or {})
    keep = (
        "OWNER", "Owner", "owner", "OWNER_NAME", "OWNER_NAME1", "owner_name", "OWNER1",
        "Owner_Name_1", "Owner_Name_2", "CURRENT_OW", "Current_Ow", "Owner1", "Owner2", "TAXPAYER", "MAIL_NAME",
        "FullName", "Name", "FullAdd", "OwnerAdd1", "OwnerAdd2", "OwnerCity", "OwnerState", "PostCode",
        "PARCEL_ID", "PIN", "APN", "OBJECTID", "FID", "ACCOUNT", "Accountnum", "TAXPIN", "PID", "PARCELNO",
        "PropertyNu", "Map_Number", "Join1", "PPI", "Schedule", "ScheduleText", "PrimaryID", "SecondID", "Printkey", "SwisParID",
        "SITUS", "SITE_ADDR", "SITUS_ADDRESS", "PROPERTY_ADDRESS", "ADDRESS", "ADDR", "PHYSICAL_ADDRESS", "Street_Number",
        "Situs_Street", "Situs_Suffix", "Situs_Direction", "FullStreet", "GeoHouseNumber", "GeoStreetName", "GeoCityName",
        "Acres", "ACRES", "Acreage", "ACREAGE", "Area_in_Ac", "EcoDesc", "MiscChar", "NhoodDescr", "prop_class",
        "Year_Built", "YEAR_BUILT", "fyrblt",
    )
    out = {}
    for key in keep:
        if key in props and props[key] is not None:
            text = str(props[key]).strip()
            if text and len(text) <= 160:
                out[key] = props[key]

    owner = _monahinga_v25_prop_value(props, (
        "OWNER", "Owner", "owner", "OWNER_NAME", "OWNER_NAME1", "owner_name", "OWNER1",
        "Owner_Name_1", "Owner_Name_2", "CURRENT_OW", "Current_Ow", "Owner1", "Owner2", "TAXPAYER", "MAIL_NAME",
        "FullName", "Name", "FullAdd", "OwnerAdd1", "OwnerAdd2",
    ))
    parcel_id = _monahinga_v25_prop_value(props, (
        "PARCEL_ID", "PIN", "APN", "OBJECTID", "FID", "ACCOUNT", "Accountnum", "TAXPIN", "PID",
        "PARCELNO", "PropertyNu", "Map_Number", "Join1", "PPI", "Schedule", "ScheduleText", "PrimaryID", "SecondID", "Printkey", "SwisParID",
    ))
    if owner and ("FullAdd" in props or "OwnerAdd1" in props or "PPI" in props) and "Owner name not exposed" not in owner:
        out["MONAHINGA_OWNER_CONTEXT_NORMALIZED"] = owner
    if owner:
        out["MONAHINGA_OWNER_NORMALIZED"] = owner
    if parcel_id:
        out["MONAHINGA_PARCEL_ID_NORMALIZED"] = parcel_id
    return out


def _monahinga_v25_compact_parcel_geojson_for_run(geojson: dict, label: str, source: str) -> dict | None:
    if not isinstance(geojson, dict):
        return None

    raw_features = geojson.get("features") if isinstance(geojson.get("features"), list) else []
    max_features = 350
    features: list[dict] = []
    for raw_feature in raw_features[:max_features]:
        if not isinstance(raw_feature, dict):
            continue
        geom = raw_feature.get("geometry")
        if not isinstance(geom, dict) or not geom.get("coordinates"):
            continue
        features.append({
            "type": "Feature",
            "properties": _monahinga_v25_compact_props(raw_feature.get("properties") or {}),
            "geometry": {
                "type": geom.get("type"),
                "coordinates": _monahinga_v25_compact_coords(geom.get("coordinates")),
            },
        })

    if not features:
        return None

    owner_fields, owner_value_count = _monahinga_v25_detect_fields(features, (
        "OWNER", "Owner", "owner", "OWNER_NAME", "OWNER_NAME1", "owner_name", "OWNER1",
        "Owner_Name_1", "Owner_Name_2", "CURRENT_OW", "Current_Ow", "Owner1", "Owner2", "TAXPAYER", "MAIL_NAME",
        "FullName", "Name", "FullAdd", "OwnerAdd1", "OwnerAdd2", "OwnerCity", "OwnerState", "PostCode",
        "MONAHINGA_OWNER_NORMALIZED", "MONAHINGA_OWNER_CONTEXT_NORMALIZED",
    ))
    parcel_fields, parcel_value_count = _monahinga_v25_detect_fields(features, (
        "PARCEL_ID", "PIN", "APN", "OBJECTID", "FID", "ACCOUNT", "Accountnum", "TAXPIN", "PID",
        "PARCELNO", "PropertyNu", "Map_Number", "Join1", "PPI", "Schedule", "ScheduleText", "PrimaryID", "SecondID", "Printkey", "SwisParID", "MONAHINGA_PARCEL_ID_NORMALIZED",
    ))

    return {
        "type": "FeatureCollection",
        "properties": {
            "monahinga_parcel_source": "imported_geojson",
            "monahinga_parcel_source_label": label or "Automatic BBox parcel source",
            "monahinga_parcel_source_ref": source or "auto_backend_bbox",
            "monahinga_parcel_warning": "Ownership context only. Verify county records, legal access, landowner permission, season dates, and local regulations.",
            "monahinga_feature_count": len(features),
            "monahinga_bbox_scoped": True,
            "monahinga_backend_auto_carried": True,
            "monahinga_detected_owner_fields": owner_fields,
            "monahinga_detected_parcel_id_fields": parcel_fields,
            "monahinga_owner_value_count": owner_value_count,
            "monahinga_parcel_id_value_count": parcel_value_count,
        },
        "features": features,
    }


def _monahinga_v25_auto_parcel_geojson_for_run(bbox: BBox) -> dict | None:
    try:
        preview = _monahinga_v2_preview_payload(bbox, manual_arcgis_url=None)
        if not isinstance(preview, dict) or preview.get("ok") is not True:
            return None

        source = str(preview.get("source") or "")
        if "demo" in source.lower():
            print("[parcel-run-carry] skipped demo parcel fallback for Page 2")
            return None

        geojson = preview.get("geojson")
        label = str(preview.get("source_label") or "Automatic BBox parcel source")
        compact = _monahinga_v25_compact_parcel_geojson_for_run(geojson, label, source)
        if compact:
            print(f"[parcel-run-carry] auto-carried {len(compact.get('features') or [])} parcel feature(s) from {source}")
        return compact
    except Exception as exc:
        print(f"[parcel-run-carry] auto parcel carry failed: {type(exc).__name__}: {exc}")
        return None


def _monahinga_v25_resolve_run_parcel_geojson(req: RunRequest, bbox: BBox) -> dict | None:
    provided = req.parcel_geojson
    if isinstance(provided, dict) and provided.get("features"):
        compact = _monahinga_v25_compact_parcel_geojson_for_run(provided, "Browser-carried parcel GeoJSON", "browser_payload")
        return compact or provided
    return _monahinga_v25_auto_parcel_geojson_for_run(bbox)



# MONAHINGA_BACKEND_SPECIES_GATE_V1: final conservative species sanity check.
def _monahinga_species_gate_state_for_bbox(bbox: BBox) -> str:
    lon = (float(bbox.min_lon) + float(bbox.max_lon)) / 2.0
    lat = (float(bbox.min_lat) + float(bbox.max_lat)) / 2.0
    if -80.7 <= lon <= -74.6 and 39.6 <= lat <= 42.6: return "PA"
    if -79.9 <= lon <= -71.7 and 40.3 <= lat <= 45.1: return "NY"
    if -111.2 <= lon <= -104.0 and 40.9 <= lat <= 45.1: return "WY"
    if -109.2 <= lon <= -101.9 and 36.8 <= lat <= 41.1: return "CO"
    if -104.2 <= lon <= -96.3 and 42.3 <= lat <= 46.1: return "SD"
    if -116.2 <= lon <= -104.0 and 44.2 <= lat <= 49.1: return "MT"
    return ""


def _monahinga_species_gate_for_bbox(bbox: BBox, selected: object) -> tuple[str, str]:
    requested = str(selected or "default").strip() or "default"
    state = _monahinga_species_gate_state_for_bbox(bbox)
    allowed_by_state = {
        "PA": {"default", "whitetail", "black_bear", "turkey", "coyote"},
        "NY": {"default", "whitetail", "black_bear", "turkey", "coyote"},
        "WY": {"default", "whitetail", "mule_deer", "elk", "moose", "bighorn", "pronghorn", "black_bear", "turkey", "coyote"},
        "CO": {"default", "whitetail", "mule_deer", "elk", "moose", "bighorn", "pronghorn", "black_bear", "turkey", "coyote"},
        "SD": {"default", "whitetail", "mule_deer", "pronghorn", "turkey", "coyote"},
        "MT": {"default", "whitetail", "mule_deer", "elk", "moose", "bighorn", "pronghorn", "black_bear", "turkey", "coyote"},
    }
    allowed = allowed_by_state.get(state)
    if not allowed or requested in allowed:
        return requested, state
    fallback = "whitetail" if "whitetail" in allowed else "default"
    print(f"[species-gate] {requested!r} is not enabled for {state}; using {fallback!r} for this run")
    return fallback, state


@app.post("/run-terrain-truth")
def run_terrain_truth(req: RunRequest):
    try:
        bbox = BBox.normalized(req.min_lon, req.min_lat, req.max_lon, req.max_lat)
        gated_species, species_gate_state = _monahinga_species_gate_for_bbox(bbox, req.selected_species)
        parcel_geojson_for_run = _monahinga_v25_resolve_run_parcel_geojson(req, bbox)

        result = _run(
            bbox,
            req.width,
            req.height,
            operator_context={
                "wind_direction": req.wind_direction,
                "notes": req.notes,
                "mode": req.mode or "hunter",
                "selected_species": gated_species or "default",
                "target_species": gated_species or "default",
                "species_gate_state": species_gate_state,
                "species_gate_original": req.selected_species or "default",
                "hunt_plan_window": req.hunt_plan_window or "now",  # MONAHINGA_FUTURE_HUNT_PLANNER_V1
                "hunt_plan_datetime": req.hunt_plan_datetime or "",
                "private_land_mode": req.private_land_mode or "avoid",
                "selection_polygon": req.selection_polygon,
                "parcel_geojson": parcel_geojson_for_run,
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

# MONAHINGA_REPAIR_MAIN_PY_PARCEL_INDENT_V1_2026_05_08: emergency parcel indentation repair applied.
