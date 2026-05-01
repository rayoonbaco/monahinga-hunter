from __future__ import annotations

from dataclasses import dataclass


CONTIGUOUS_USA_BOUNDS = (-125.0, 24.0, -66.5, 49.5)


@dataclass(frozen=True)
class BBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def as_list(self) -> list[float]:
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]

    def to_esri_envelope(self) -> dict[str, float]:
        return {
            "xmin": self.min_lon,
            "ymin": self.min_lat,
            "xmax": self.max_lon,
            "ymax": self.max_lat,
            "spatialReference": {"wkid": 4326},
        }

    @property
    def width_degrees(self) -> float:
        return self.max_lon - self.min_lon

    @property
    def height_degrees(self) -> float:
        return self.max_lat - self.min_lat

    @classmethod
    def normalized(cls, lon_a: float, lat_a: float, lon_b: float, lat_b: float) -> "BBox":
        return cls(
            min_lon=min(float(lon_a), float(lon_b)),
            min_lat=min(float(lat_a), float(lat_b)),
            max_lon=max(float(lon_a), float(lon_b)),
            max_lat=max(float(lat_a), float(lat_b)),
        )

    def validate_worldwide(self) -> None:
        if not (-180.0 <= self.min_lon <= 180.0 and -180.0 <= self.max_lon <= 180.0):
            raise ValueError("Longitude must stay between -180 and 180.")
        if not (-90.0 <= self.min_lat <= 90.0 and -90.0 <= self.max_lat <= 90.0):
            raise ValueError("Latitude must stay between -90 and 90.")
        if self.max_lon <= self.min_lon:
            raise ValueError("Max longitude must be greater than min longitude.")
        if self.max_lat <= self.min_lat:
            raise ValueError("Max latitude must be greater than min latitude.")
        if self.width_degrees <= 0 or self.height_degrees <= 0:
            raise ValueError("Bounding box width and height must be positive.")

    def validate_us_hunting_box(self) -> None:
        self.validate_worldwide()
        usa = BBox(*CONTIGUOUS_USA_BOUNDS)
        if not usa.contains(self.min_lon, self.min_lat) or not usa.contains(self.max_lon, self.max_lat):
            raise ValueError(
                "This hunting build is U.S.-only right now. Draw the box fully inside the lower 48 so legal land checks and stand ranking stay truthful."
            )

    def contains(self, lon: float, lat: float, *, pad: float = 0.0) -> bool:
        return (
            self.min_lon - pad <= float(lon) <= self.max_lon + pad
            and self.min_lat - pad <= float(lat) <= self.max_lat + pad
        )

    def clamp_point(self, lon: float, lat: float) -> tuple[float, float]:
        clamped_lon = min(self.max_lon, max(self.min_lon, float(lon)))
        clamped_lat = min(self.max_lat, max(self.min_lat, float(lat)))
        return clamped_lon, clamped_lat

    def intersects(self, other: "BBox") -> bool:
        return not (
            self.max_lon < other.min_lon
            or self.min_lon > other.max_lon
            or self.max_lat < other.min_lat
            or self.min_lat > other.max_lat
        )

    def intersects_contiguous_usa(self) -> bool:
        return self.intersects(BBox(*CONTIGUOUS_USA_BOUNDS))

    def to_form_defaults(self) -> dict[str, float]:
        return {
            "min_lon": self.min_lon,
            "min_lat": self.min_lat,
            "max_lon": self.max_lon,
            "max_lat": self.max_lat,
        }
