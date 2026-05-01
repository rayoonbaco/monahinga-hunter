from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

import requests

from ..bbox import BBox


class PADUSConfigError(RuntimeError):
    pass


class PADUSQueryError(RuntimeError):
    pass


@dataclass
class PADUSFetchResult:
    geojson_path: Path
    summary_path: Path
    legal_feature_count: int
    restricted_feature_count: int
    unknown_feature_count: int
    provider: str = "padus_arcgis"


class PADUSLegalSurfaceClient:
    def __init__(
        self,
        feature_server_url: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.feature_server_url = feature_server_url or os.getenv("PADUS_PUBLIC_ACCESS_FEATURESERVER_URL")
        self.session = session or requests.Session()

    def _classify_feature(self, props: dict[str, Any]) -> str:
        values = []
        for key in [
            "AccessType",
            "ACCESS",
            "Access",
            "PublicAccess",
            "PUBLIC_ACCESS",
            "Pub_Access",
            "GAP_Sts",
            "GAP_STS",
            "GapStatus",
            "ManagerName",
            "MANAGER_NAME",
            "MngNm_Desc",
            "MngTp_Desc",
            "Unit_Nm",
            "DesTp_Desc",
            "Category",
            "FeatClass",
        ]:
            values.append(str(props.get(key, "")))
        text = " ".join(values).lower()

        restricted_tokens = [
            "closed",
            "restricted",
            "no public access",
            "private",
            "military",
            "reservation only",
            "permit required",
            "special use",
        ]
        legal_tokens = [
            "oa",
            "open access",
            "public",
            "state game land",
            "fish and wildlife",
            "wildlife management",
            "national forest",
            "forest service",
            "blm",
            "state forest",
            "state park",
            "county park",
            "fee",
            "easement",
        ]

        if any(token in text for token in restricted_tokens):
            return "restricted"
        if any(token in text for token in legal_tokens):
            return "legal"

        gap = str(props.get("GAP_Sts", props.get("GAP_STS", props.get("GapStatus", "")))).strip()
        pub_access = str(props.get("Pub_Access", props.get("PublicAccess", props.get("PUBLIC_ACCESS", "")))).strip().lower()

        if pub_access in {"oa", "open", "yes", "y", "public"}:
            return "legal"
        if gap in {"1", "2", "3"}:
            return "legal"

        return "unknown"

    def _normalize_geojson(self, body: dict[str, Any]) -> dict[str, Any]:
        if body.get("type") == "FeatureCollection":
            features = body.get("features", [])
            out_features: list[dict[str, Any]] = []
            for feat in features:
                props = dict(feat.get("properties") or {})
                props["monahinga_legal_class"] = self._classify_feature(props)
                out_features.append(
                    {
                        "type": "Feature",
                        "geometry": feat.get("geometry"),
                        "properties": props,
                    }
                )
            return {"type": "FeatureCollection", "features": out_features}

        esri_features = body.get("features", [])
        out_features: list[dict[str, Any]] = []
        for feat in esri_features:
            attrs = dict(feat.get("attributes") or {})
            geometry = feat.get("geometry") or {}
            rings = geometry.get("rings")
            if not rings:
                continue
            geom = {"type": "Polygon", "coordinates": rings}
            attrs["monahinga_legal_class"] = self._classify_feature(attrs)
            out_features.append(
                {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": attrs,
                }
            )
        return {"type": "FeatureCollection", "features": out_features}

    def _write_empty_result(
        self,
        out_geojson_path: Path,
        out_summary_path: Path,
        *,
        reason: str,
        configured: bool,
        skipped: bool = False,
    ) -> PADUSFetchResult:
        feature_collection = {"type": "FeatureCollection", "features": []}
        summary = {
            "provider": "padus_arcgis",
            "feature_count": 0,
            "legal_feature_count": 0,
            "restricted_feature_count": 0,
            "unknown_feature_count": 0,
            "configured": configured,
            "skipped": skipped,
            "reason": reason,
        }
        out_geojson_path.parent.mkdir(parents=True, exist_ok=True)
        out_summary_path.parent.mkdir(parents=True, exist_ok=True)
        out_geojson_path.write_text(json.dumps(feature_collection, indent=2), encoding="utf-8")
        out_summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return PADUSFetchResult(
            geojson_path=out_geojson_path,
            summary_path=out_summary_path,
            legal_feature_count=0,
            restricted_feature_count=0,
            unknown_feature_count=0,
        )

    def fetch_legal_surface(self, bbox: BBox, out_geojson_path: Path, out_summary_path: Path) -> PADUSFetchResult:
        if not bbox.intersects_contiguous_usa():
            return self._write_empty_result(
                out_geojson_path,
                out_summary_path,
                reason="bbox_outside_padus_coverage",
                configured=bool(self.feature_server_url),
                skipped=True,
            )

        if not self.feature_server_url:
            return self._write_empty_result(
                out_geojson_path,
                out_summary_path,
                reason="padus_feature_server_missing",
                configured=False,
            )

        url = self.feature_server_url.rstrip("/") + "/query"
        params = {
            "f": "geojson",
            "where": "1=1",
            "geometry": json.dumps(bbox.to_esri_envelope()),
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
            "resultRecordCount": 2000,
        }

        try:
            resp = self.session.get(url, params=params, timeout=120)
            if resp.status_code >= 400:
                raise PADUSQueryError(f"PAD-US query failed with {resp.status_code}: {resp.text[:500]}")
            body = resp.json()

            if body.get("error") and params["f"] == "geojson":
                params["f"] = "json"
                resp = self.session.get(url, params=params, timeout=120)
                if resp.status_code >= 400:
                    raise PADUSQueryError(f"PAD-US query retry failed with {resp.status_code}: {resp.text[:500]}")
                body = resp.json()
        except (requests.RequestException, ValueError, PADUSQueryError) as exc:
            return self._write_empty_result(
                out_geojson_path,
                out_summary_path,
                reason=f"padus_query_unavailable: {exc}",
                configured=True,
            )

        feature_collection = self._normalize_geojson(body)
        out_geojson_path.parent.mkdir(parents=True, exist_ok=True)
        out_summary_path.parent.mkdir(parents=True, exist_ok=True)
        out_geojson_path.write_text(json.dumps(feature_collection, indent=2), encoding="utf-8")

        legal = restricted = unknown = 0
        for feat in feature_collection["features"]:
            cls = feat["properties"].get("monahinga_legal_class")
            if cls == "legal":
                legal += 1
            elif cls == "restricted":
                restricted += 1
            else:
                unknown += 1

        summary = {
            "provider": "padus_arcgis",
            "feature_count": len(feature_collection["features"]),
            "legal_feature_count": legal,
            "restricted_feature_count": restricted,
            "unknown_feature_count": unknown,
            "configured": True,
            "skipped": False,
        }
        out_summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        return PADUSFetchResult(
            geojson_path=out_geojson_path,
            summary_path=out_summary_path,
            legal_feature_count=legal,
            restricted_feature_count=restricted,
            unknown_feature_count=unknown,
        )
