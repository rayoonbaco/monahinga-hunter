from __future__ import annotations

from pathlib import Path
import json
import numpy as np
from PIL import Image

from engine.terrain_truth.bbox import BBox

try:
    import rasterio
except Exception:
    rasterio = None


# =========================
# SANITY GATE (SAFE INSERT)
# =========================
def _sanity_gate(bbox: BBox) -> BBox:
    if bbox is None:
        raise ValueError("Sanity gate failed: bbox is None")

    if bbox.min_lat >= bbox.max_lat:
        raise ValueError("Sanity gate failed: invalid latitude range")

    if bbox.min_lon >= bbox.max_lon:
        raise ValueError("Sanity gate failed: invalid longitude range")

    return bbox


# =========================
# EXISTING HELPERS
# =========================
def _load_dem(path: Path):
    if rasterio:
        with rasterio.open(path) as ds:
            return ds.read(1)
    return np.array(Image.open(path))


def _resolve_dem_path(root: Path) -> Path:
    contract = root / "terrain_contract.json"
    if contract.exists():
        data = json.loads(contract.read_text())
        rel = data.get("terrain", {}).get("path")
        if rel:
            p = root.parent / rel
            if p.exists():
                return p
    return root / "terrain" / "dem.tif"


# =========================
# ORIGINAL ENTRY (PRESERVED)
# =========================
def build_decision_artifact(terrain_truth_root: Path):
    """
    Original entrypoint preserved.
    Only change: sanity gate inserted after bbox load.
    """

    # BBOX LOAD (existing behavior)
    bbox = BBox.from_contract(terrain_truth_root)

    # NEW: SANITY GATE (non-breaking)
    bbox = _sanity_gate(bbox)

    # EXISTING LOGIC CONTINUES UNCHANGED
    dem_path = _resolve_dem_path(terrain_truth_root)
    dem = _load_dem(dem_path)

    mean = float(np.mean(dem))
    std = float(np.std(dem))

    return {
        "summary": "Decision computed",
        "elevation_mean": mean,
        "terrain_variability": std,
    }