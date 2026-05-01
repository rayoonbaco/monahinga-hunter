from engine.command_surface.config import resolve_default_layer
from pathlib import Path
import json

from engine.command_surface.render import render_command_surface
from engine.launch_surface.home_page import render_home_page
from engine.terrain_truth.bbox import BBox
from engine.terrain_truth.contract import (
    CommandSurfaceArtifact,
    CorridorArtifact,
    DecisionArtifact,
    LegalArtifact,
    SiteArtifact,
    TerrainArtifact,
    TerrainDerivativeArtifact,
    TerrainTruthContract,
    VegetationArtifact,
)


def _build_contract(run_root: Path) -> TerrainTruthContract:
    primary = SiteArtifact(
        rank=1,
        tier="primary",
        title="Primary Sit — Core Converge",
        score=88,
        lon=-78.095,
        lat=41.902,
        elevation_m=420.0,
        slope_bias="shoulder",
        legality_status="legal",
        source_name="Test Ground",
        reasoning="Primary reasoning.",
    )
    alternate = SiteArtifact(
        rank=2,
        tier="alternate",
        title="Alternate Sit #2 — West Shoulder",
        score=81,
        lon=-78.089,
        lat=41.898,
        elevation_m=410.0,
        slope_bias="bench",
        legality_status="legal",
        source_name="Test Ground",
        reasoning="Alternate reasoning.",
    )
    near_miss = SiteArtifact(
        rank=3,
        tier="near-miss",
        title="Near-Miss #3 — South Bench",
        score=61,
        lon=-78.083,
        lat=41.895,
        elevation_m=405.0,
        slope_bias="bench",
        legality_status="unknown",
        source_name="Suppressed Ground",
        reasoning="Near-miss reasoning.",
    )
    decision = DecisionArtifact(
        path="terrain_truth/decision/decision_contract.json",
        primary=primary,
        alternates=[alternate],
        near_misses=[near_miss],
        corridors=[
            CorridorArtifact(
                name="Dominant Corridor",
                strength="dominant",
                points=[[-78.095, 41.902], [-78.092, 41.900], [-78.089, 41.898]],
                reasoning="Corridor reasoning.",
            )
        ],
        notes=["note"],
        summary={
            "analysis_mode": "legal_hunt",
            "legal_state": "strong",
            "preferred_wind": "NW",
            "current_wind": "NW",
            "readiness": "Strike Ready",
            "best_time_label": "Travel corridor window",
            "best_time_window": "Last two hours before sunset",
            "confidence": 84,
            "confidence_label": "High",
            "cluster_summary": [{"title": primary.title, "why": "Travel 80 · Bedding 76 · Feeding 70"}],
            "invalidators": ["Wind drifts."],
        },
    )
    return TerrainTruthContract(
        run_id="run_test",
        bbox=[-78.102209, 41.891092, -78.074925, 41.909235],
        crs="EPSG:4326",
        terrain=TerrainArtifact(provider="copernicus", path="terrain_truth/dem.tif", format="tif", pixel_dimensions=[64, 64]),
        terrain_derivatives=TerrainDerivativeArtifact(
            hillshade_path="terrain_truth/terrain_derivatives/hillshade.png",
            summary_path="terrain_truth/terrain_derivatives/terrain_summary.json",
            structure_bias="balanced",
            elevation_min_m=350.0,
            elevation_max_m=470.0,
        ),
        vegetation=VegetationArtifact(
            provider="nlcd_test",
            classification="forest",
            notes=["Test vegetation artifact."],
        ),
        legal_surface=LegalArtifact(
            provider="padus",
            path="terrain_truth/legal/legal_surface.geojson",
            summary_path="terrain_truth/legal/legal_surface_summary.json",
            legal_feature_count=1,
            restricted_feature_count=0,
            unknown_feature_count=0,
        ),
        decision=decision,
        command_surface=CommandSurfaceArtifact(path="command_surface/index.html"),
        notes=["ok"],
        operator_context={"mode": "hunter", "notes": "test notes"},
    )


def test_launch_surface_renders_real_leaflet_js():
    html = render_home_page(BBox(-78.102209, 41.891092, -78.074925, 41.909235))
    assert "L.map('bbox-map', { zoomControl:true, worldCopyJump:false })" in html
    assert "new L.Control.Draw({" in html
    assert 'onclick="runDefault()"' in html
    assert 'Draw one U.S. box and get a truthful stand answer' in html
    assert 'World view' not in html
    assert "{{" not in html
    assert "}}" not in html


def test_command_surface_renders_rank_and_focus_hooks(tmp_path: Path):
    run_root = tmp_path / "run_test"
    derivative_dir = run_root / "terrain_truth" / "terrain_derivatives"
    legal_dir = run_root / "terrain_truth" / "legal"
    derivative_dir.mkdir(parents=True)
    legal_dir.mkdir(parents=True)

    for name in ["terrain_render.png", "hillshade.png", "slope.png", "local_relief.png"]:
        (derivative_dir / name).write_bytes(b"png")

    (derivative_dir / "heightmap.json").write_text(
        json.dumps({"rows": 2, "cols": 2, "values": [0, 0, 0, 0]}),
        encoding="utf-8",
    )

    (derivative_dir / "terrain_summary.json").write_text(
        json.dumps({"width": 64, "height": 64, "terrain_strength": "good", "surface_trust": "high"}),
        encoding="utf-8",
    )

    (legal_dir / "legal_surface.geojson").write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"monahinga_legal_class": "legal"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-78.10, 41.892], [-78.09, 41.892], [-78.09, 41.901], [-78.10, 41.901], [-78.10, 41.892]]]
                    },
                }
            ],
        }),
        encoding="utf-8",
    )

    contract = _build_contract(run_root)
    out = render_command_surface(run_root, contract)
    html = out.read_text(encoding="utf-8")

    assert 'class="block status-block tone-strong"' in html
    assert 'class="row row-button active"' in html
    assert 'focusSiteByRank' in html
    assert 'rowButtons.forEach' in html
    assert 'renderer.domElement.addEventListener(\'click\'' in html
    assert '"nx":' in html
    assert '"ny":' in html
    assert "Primary Sit" in html
    assert "Confidence" in html
    assert "Copy coordinates" in html
    assert "Travel corridor window" in html or "Travel" in html
    assert "Wind" in html


def test_viewer_defaults_to_terrain_first_layer():
    assert resolve_default_layer({"terrain": "x", "hillshade": "y", "relief": "z"}) == "terrain"