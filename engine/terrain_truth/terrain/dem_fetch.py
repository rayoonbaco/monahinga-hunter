from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

import requests

from ..bbox import BBox


class CopernicusAuthError(RuntimeError):
    pass


class CopernicusProcessError(RuntimeError):
    pass


class DEMFetchError(RuntimeError):
    pass


@dataclass
class DEMFetchResult:
    path: Path
    pixel_dimensions: list[int]
    provider: str
    format: str = "image/tiff"


def bbox_looks_like_usa(bbox: BBox) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox.as_list()
    return (
        15.0 <= min_lat <= 75.0
        and 15.0 <= max_lat <= 75.0
        and -180.0 <= min_lon <= -60.0
        and -180.0 <= max_lon <= -60.0
    )


def fetch_usgs_dem(
    bbox: BBox,
    out_path: Path,
    *,
    width: int = 1024,
    height: int = 1024,
    session: requests.Session | None = None,
) -> DEMFetchResult:
    url = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage"
    params = {
        "f": "image",
        "bbox": ",".join(str(v) for v in bbox.as_list()),
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": f"{width},{height}",
        "format": "tiff",
        "pixelType": "F32",
        "noDataInterpretation": "esriNoDataMatchAny",
        "interpolation": "RSP_BilinearInterpolation",
    }

    sess = session or requests.Session()
    resp = sess.get(url, params=params, timeout=90)
    if resp.status_code != 200:
        raise DEMFetchError(f"USGS DEM request failed with {resp.status_code}.")

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "tiff" not in content_type and "geotiff" not in content_type and "application/octet-stream" not in content_type:
        snippet = (resp.text or "")[:220].replace("\n", " ")
        raise DEMFetchError(f"USGS returned non-TIFF content: {snippet}")

    if not resp.content or len(resp.content) < 1024:
        raise DEMFetchError("USGS returned an empty DEM response.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(resp.content)
    return DEMFetchResult(
        path=out_path,
        pixel_dimensions=[width, height],
        provider="usgs_3dep",
    )


class CopernicusDEMClient:
    _ALIASES = {
        "DEM_COPERNICUS_30": "COPERNICUS_30",
        "DEM_COPERNICUS_90": "COPERNICUS_90",
        "COPERNICUS30": "COPERNICUS_30",
        "COPERNICUS90": "COPERNICUS_90",
    }

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_url: str = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        process_url: str = "https://sh.dataspace.copernicus.eu/api/v1/process",
        dem_collection: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.client_id = client_id or os.getenv("CDSE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("CDSE_CLIENT_SECRET")
        self.token_url = token_url
        self.process_url = process_url
        raw_collection = dem_collection or os.getenv("CDSE_DEM_COLLECTION") or "COPERNICUS_30"
        self.dem_collection = self._ALIASES.get(raw_collection, raw_collection)
        self.session = session or requests.Session()
        self._token: str | None = None

    def _get_token(self) -> str:
        if self._token:
            return self._token
        if not self.client_id or not self.client_secret:
            raise CopernicusAuthError(
                "Copernicus credentials missing. Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET."
            )
        resp = self.session.post(
            self.token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            raise CopernicusAuthError(
                f"Copernicus token request failed with {resp.status_code}: {resp.text[:300]}"
            )
        body = resp.json()
        token = body.get("access_token")
        if not token:
            raise CopernicusAuthError("Copernicus token response did not include access_token.")
        self._token = token
        return token

    def fetch_dem(
        self,
        bbox: BBox,
        out_path: Path,
        *,
        width: int = 1024,
        height: int = 1024,
    ) -> DEMFetchResult:
        token = self._get_token()
        payload: dict[str, Any] = {
            "input": {
                "bounds": {
                    "bbox": bbox.as_list(),
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
                },
                "data": [
                    {
                        "type": "dem",
                        "dataFilter": {"demInstance": self.dem_collection},
                    }
                ],
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}],
            },
            "evalscript": """
                //VERSION=3
                function setup() {
                  return {
                    input: ["DEM"],
                    output: { bands: 1, sampleType: "FLOAT32" }
                  };
                }
                function evaluatePixel(sample) {
                  return [sample.DEM];
                }
            """,
        }
        resp = self.session.post(
            self.process_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "image/tiff",
            },
            data=json.dumps(payload),
            timeout=120,
        )
        if resp.status_code >= 400:
            raise CopernicusProcessError(
                f"Copernicus DEM request failed with {resp.status_code}: {resp.text[:500]}"
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(resp.content)
        return DEMFetchResult(
            path=out_path,
            pixel_dimensions=[width, height],
            provider="copernicus_cdse",
        )


class AutoDEMClient:
    def __init__(self) -> None:
        self.copernicus = CopernicusDEMClient()

    def fetch_dem(
        self,
        bbox: BBox,
        out_path: Path,
        *,
        width: int = 1024,
        height: int = 1024,
    ) -> DEMFetchResult:
        errors: list[str] = []

        if bbox_looks_like_usa(bbox):
            try:
                return fetch_usgs_dem(bbox, out_path, width=width, height=height)
            except Exception as exc:
                errors.append(f"USGS failed: {exc}")

        try:
            return self.copernicus.fetch_dem(bbox, out_path, width=width, height=height)
        except Exception as exc:
            errors.append(f"Copernicus failed: {exc}")

        raise DEMFetchError(" ; ".join(errors) if errors else "No DEM provider succeeded.")