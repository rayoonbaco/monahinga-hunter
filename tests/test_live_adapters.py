from pathlib import Path
import json

from fastapi.testclient import TestClient

from apps.api.main import app
from engine.live.wind import OpenMeteoWindClient, wind_arrow_heading_deg
from engine.terrain_truth.bbox import BBox
from engine.terrain_truth.legal.padus_fetch import PADUSLegalSurfaceClient
from engine.terrain_truth.terrain.dem_fetch import CopernicusDEMClient


class FakeResponse:
    def __init__(self, status_code=200, json_body=None, content=b"", text=""):
        self.status_code = status_code
        self._json = json_body or {}
        self.content = content
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, headers=None, data=None, timeout=None):
        self.calls.append(("POST", url))
        if "openid-connect/token" in url:
            return FakeResponse(json_body={"access_token": "abc123"})
        return FakeResponse(content=b"FAKE_TIFF_BYTES")

    def get(self, url, params=None, timeout=None):
        self.calls.append(("GET", url, params))
        if "open-meteo.com" in url:
            return FakeResponse(
                json_body={
                    "current": {
                        "time": "2026-04-03T17:15",
                        "wind_speed_10m": 8.4,
                        "wind_direction_10m": 135,
                        "wind_gusts_10m": 14.2,
                    }
                }
            )
        return FakeResponse(
            json_body={
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Polygon", "coordinates": [[[-78.1, 41.89], [-78.09, 41.89], [-78.09, 41.9], [-78.1, 41.9], [-78.1, 41.89]]]},
                        "properties": {"PublicAccess": "Open", "ManagerName": "USFS"},
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Polygon", "coordinates": [[[-78.08, 41.89], [-78.07, 41.89], [-78.07, 41.9], [-78.08, 41.9], [-78.08, 41.89]]]},
                        "properties": {"PublicAccess": "Closed"},
                    },
                ],
            }
        )


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


def test_copernicus_dem_client_writes_tiff(tmp_path: Path):
    client = CopernicusDEMClient(client_id="id", client_secret="secret", session=FakeSession())
    out = client.fetch_dem(BBox(-78.1, 41.89, -78.07, 41.9), tmp_path / "dem.tif", width=64, height=64)
    assert out.path.exists()
    assert out.path.read_bytes() == b"FAKE_TIFF_BYTES"
    assert out.pixel_dimensions == [64, 64]


def test_padus_client_writes_geojson_and_summary(tmp_path: Path):
    client = PADUSLegalSurfaceClient(feature_server_url="https://example.com/FeatureServer/0", session=FakeSession())
    result = client.fetch_legal_surface(
        BBox(-78.1, 41.89, -78.07, 41.9),
        tmp_path / "legal_surface.geojson",
        tmp_path / "legal_surface_summary.json",
    )
    geo = json.loads(result.geojson_path.read_text())
    summary = json.loads(result.summary_path.read_text())
    assert len(geo["features"]) == 2
    assert summary["legal_feature_count"] == 1
    assert summary["restricted_feature_count"] == 1


def test_open_meteo_wind_client_parses_live_read():
    read = OpenMeteoWindClient(session=FakeSession()).fetch_live_wind(41.9, -78.09)
    assert read.ok is True
    assert read.direction_label == "SE"
    assert round(read.speed_mph or 0) == 8
    assert round(read.gust_mph or 0) == 14
    assert "Wind from SE" in read.summary
    assert wind_arrow_heading_deg(read.direction_deg) == 315.0


def test_live_wind_endpoint_returns_arrow_heading(monkeypatch):
    from apps.api import main as api_main

    monkeypatch.setattr(api_main, "OpenMeteoWindClient", lambda: OpenMeteoWindClient(session=FakeSession()))
    client = TestClient(app)
    response = client.get("/live-wind", params={"lat": 41.9, "lon": -78.09})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["direction_label"] == "SE"
    assert data["arrow_heading_deg"] == 315.0


def test_wildlife_adapter_request_has_real_structure():
    """
    Locks baseline using real observed keys from the latest complete wildlife-enabled run.
    """

    runs_dir = Path("runs")
    assert runs_dir.exists()

    latest_run = _find_latest_run_with_wildlife(runs_dir)

    wildlife_file = latest_run / "terrain_truth" / "wildlife" / "wildlife_adapter_request.json"
    assert wildlife_file.exists()

    data = json.loads(wildlife_file.read_text(encoding="utf-8"))

    assert isinstance(data, dict)
    assert len(data) > 0

    expected_keys = [
        "adapter_version",
        "source_system",
        "bbox_authority",
        "terrain_bundle",
        "derived_layers",
        "legal_context",
    ]

    for key in expected_keys:
        assert key in data, f"Missing expected key: {key}"