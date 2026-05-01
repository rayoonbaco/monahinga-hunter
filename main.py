from __future__ import annotations

from pathlib import Path
import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from engine.launch_surface import render_home_page
from engine.launch_surface.instructions_page import render_instructions_page
from engine.live.wind import OpenMeteoWindClient, format_observed_at, wind_arrow_heading_deg
from engine.terrain_truth.bbox import BBox
from engine.terrain_truth.orchestrator import build_terrain_truth_run
from engine.wildlife_atmosphere import build_wildlife_atmosphere  # ✅ NEW


# Run system
RUN_COUNT = 0
MAX_RUNS = 6  # 1 free + 5 paid


DEFAULT_BBOX = BBox(
    min_lon=-78.089916,
    min_lat=41.884358,
    max_lon=-78.058737,
    max_lat=41.907102,
)


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


def _run(bbox: BBox, width: int, height: int, operator_context: dict | None = None) -> dict:
    global RUN_COUNT

    if RUN_COUNT >= MAX_RUNS:
        return {"redirect": "/checkout"}

    RUN_COUNT += 1

    bbox.validate_us_hunting_box()

    run_id = f"run_{uuid4().hex[:10]}"
    run_root = RUNS_DIR / run_id

    contract = build_terrain_truth_run(
        bbox,
        run_root,
        width=width,
        height=height,
        operator_context=operator_context or {},
    )

    return {
        "ok": True,
        "run_id": run_id,
        "run_folder": str(run_root),
        "decision_contract": f"/runs/{run_id}/terrain_truth/decision/decision_contract.json",
        "command_surface_url": f"/runs/{run_id}/{contract.command_surface.path}",
        "runs_remaining": MAX_RUNS - RUN_COUNT,
    }


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


# ✅ NEW: Wildlife preview endpoint (THIS FIXES YOUR PROBLEM)
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
            },
        )

        if isinstance(result, dict) and result.get("redirect"):
            return RedirectResponse(result["redirect"], status_code=303)

        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))