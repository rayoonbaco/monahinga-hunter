from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.terrain_truth.bbox import BBox
from engine.terrain_truth.orchestrator import build_terrain_truth_run


DEFAULT_BBOX = BBox(
    min_lon=-78.102209,
    min_lat=41.891092,
    max_lon=-78.074925,
    max_lat=41.909235,
)

REQUIRED_ENV_KEYS = [
    "CDSE_CLIENT_ID",
    "CDSE_CLIENT_SECRET",
    "PADUS_PUBLIC_ACCESS_FEATURESERVER_URL",
]


def load_env_file() -> Path | None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return None
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
    return env_path


def fail(message: str) -> int:
    print("\n============================================", flush=True)
    print("SMOKE TEST FAILED", flush=True)
    print("============================================", flush=True)
    print(message, flush=True)
    print("", flush=True)
    return 1


def main() -> int:
    print("Monahinga vNext smoke test starting...\n", flush=True)
    env_path = load_env_file()
    if env_path is None:
        return fail(".env file not found in the project root.")
    missing = [key for key in REQUIRED_ENV_KEYS if not os.getenv(key)]
    if missing:
        return fail("Missing required .env value(s):\n- " + "\n- ".join(missing))

    run_id = f"run_smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_root = ROOT / "runs" / run_id
    try:
        contract = build_terrain_truth_run(DEFAULT_BBOX, run_root, width=768, height=768)
    except Exception as exc:
        return fail(f"Live run crashed.\n\n{exc}")

    required_paths = [
        run_root / "terrain_truth" / "terrain" / "copernicus_dem.tif",
        run_root / "terrain_truth" / "terrain_derivatives" / "hillshade.png",
        run_root / "terrain_truth" / "legal" / "legal_surface.geojson",
        run_root / "terrain_truth" / "decision" / "decision_contract.json",
        run_root / "command_surface" / "index.html",
        run_root / "terrain_truth" / "terrain_contract.json",
    ]
    missing_files = [str(path) for path in required_paths if not path.exists()]
    if missing_files:
        return fail("Required output file(s) missing:\n- " + "\n- ".join(missing_files))

    print("============================================", flush=True)
    print("SMOKE TEST PASSED", flush=True)
    print("============================================", flush=True)
    print(f"Run folder: {run_root}", flush=True)
    print("", flush=True)
    print("What was created:", flush=True)
    print(f"- DEM: {run_root / 'terrain_truth' / 'terrain' / 'copernicus_dem.tif'}", flush=True)
    print(f"- Hillshade: {run_root / 'terrain_truth' / 'terrain_derivatives' / 'hillshade.png'}", flush=True)
    print(f"- Decision contract: {run_root / 'terrain_truth' / 'decision' / 'decision_contract.json'}", flush=True)
    print(f"- Command surface: {run_root / 'command_surface' / 'index.html'}", flush=True)
    print("", flush=True)
    print(f"Primary sit: {contract.decision.primary.title} (score {contract.decision.primary.score})", flush=True)
    print("", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
