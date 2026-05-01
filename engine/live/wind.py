from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class LiveWindRead:
    ok: bool
    lat: float
    lon: float
    source: str
    direction_deg: float | None = None
    direction_label: str | None = None
    speed_mph: float | None = None
    gust_mph: float | None = None
    observed_at: str | None = None
    summary: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "lat": self.lat,
            "lon": self.lon,
            "source": self.source,
            "direction_deg": self.direction_deg,
            "direction_label": self.direction_label,
            "speed_mph": self.speed_mph,
            "gust_mph": self.gust_mph,
            "observed_at": self.observed_at,
            "summary": self.summary,
            "note": self.note,
        }


class OpenMeteoWindClient:
    def __init__(self, session: requests.sessions.Session | None = None):
        self.session = session or requests.Session()

    def fetch_live_wind(self, lat: float, lon: float) -> LiveWindRead:
        params = {
            "latitude": f"{lat:.6f}",
            "longitude": f"{lon:.6f}",
            "current": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "wind_speed_unit": "mph",
            "timezone": "auto",
        }
        try:
            response = self.session.get(OPEN_METEO_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json() or {}
            current = data.get("current") or {}
            direction_deg = _safe_float(current.get("wind_direction_10m"))
            speed_mph = _safe_float(current.get("wind_speed_10m"))
            gust_mph = _safe_float(current.get("wind_gusts_10m"))
            observed_at = str(current.get("time") or "").strip() or None
            direction_label = _direction_label(direction_deg) if direction_deg is not None else None
            summary = _summary(direction_label, speed_mph, gust_mph)
            return LiveWindRead(
                ok=direction_deg is not None or speed_mph is not None,
                lat=float(lat),
                lon=float(lon),
                source="Open-Meteo",
                direction_deg=direction_deg,
                direction_label=direction_label,
                speed_mph=speed_mph,
                gust_mph=gust_mph,
                observed_at=observed_at,
                summary=summary,
                note="Live wind is a regional weather read near this point, not a promise of every swirl or thermal on the slope.",
            )
        except Exception as exc:
            return LiveWindRead(
                ok=False,
                lat=float(lat),
                lon=float(lon),
                source="Open-Meteo",
                summary="Live wind unavailable right now.",
                note=f"{type(exc).__name__}: {exc}",
            )


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _direction_label(direction_deg: float | None) -> str | None:
    if direction_deg is None:
        return None
    labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int(((float(direction_deg) + 22.5) % 360.0) // 45.0)
    return labels[idx]


def _summary(direction_label: str | None, speed_mph: float | None, gust_mph: float | None) -> str:
    if direction_label and speed_mph is not None and gust_mph is not None:
        return f"Wind from {direction_label} at {round(speed_mph)} mph, gusting to {round(gust_mph)} mph."
    if direction_label and speed_mph is not None:
        return f"Wind from {direction_label} at {round(speed_mph)} mph."
    if speed_mph is not None:
        return f"Wind speed near this point is about {round(speed_mph)} mph."
    return "Live wind read unavailable."


def wind_arrow_heading_deg(direction_from_deg: float | None) -> float | None:
    if direction_from_deg is None:
        return None
    return (float(direction_from_deg) + 180.0) % 360.0


def format_observed_at(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%b %d, %I:%M %p")
    except Exception:
        return value
