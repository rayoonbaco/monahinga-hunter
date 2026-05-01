from fastapi.testclient import TestClient

from apps.api.main import app
from engine.launch_surface.home_page import render_home_page
from engine.terrain_truth.bbox import BBox


def test_launch_surface_describes_us_only_hunting_product() -> None:
    html = render_home_page(BBox(-78.102209, 41.891092, -78.074925, 41.909235))
    assert "lower 48 only" in html.lower()
    assert "Draw one U.S. box and get a truthful stand answer" in html
    assert "worldwide terrain testing" not in html
    assert "World view" not in html


def test_bbox_validation_blocks_non_us_hunting_box() -> None:
    bbox = BBox.normalized(10.0, 45.0, 11.0, 46.0)
    try:
        bbox.validate_us_hunting_box()
    except ValueError as exc:
        assert "U.S.-only" in str(exc)
    else:
        raise AssertionError("Expected a ValueError for a non-U.S. hunting box")


def test_api_rejects_non_us_hunting_run() -> None:
    client = TestClient(app)
    response = client.post(
        "/run-terrain-truth",
        json={
            "min_lon": 10.0,
            "min_lat": 45.0,
            "max_lon": 11.0,
            "max_lat": 46.0,
            "width": 768,
            "height": 768,
            "wind_direction": "NW",
            "notes": "",
            "mode": "hunter",
        },
    )
    assert response.status_code == 400
    assert "U.S.-only" in response.json()["detail"]


def test_launch_surface_bbox_paste_button_and_safe_error_string() -> None:
    html = render_home_page(BBox(-78.102209, 41.891092, -78.074925, 41.909235))
    assert "Paste bbox coordinates" in html
    assert "Use pasted coordinates" in html
    assert "setStatus('FAILED\\n\\n' + String(err));" in html


def test_launch_surface_contains_run_trigger() -> None:
    """
    Locks baseline: launch surface must still expose a runnable entry point.
    """

    html = render_home_page(BBox(-78.102209, 41.891092, -78.074925, 41.909235))

    # Confirm front-end launch trigger still exists
    assert "runDefault()" in html or "/run-terrain-truth" in html

    # Confirm this is still a hunting-mode launch
    assert "mode" in html
    assert "hunter" in html.lower()