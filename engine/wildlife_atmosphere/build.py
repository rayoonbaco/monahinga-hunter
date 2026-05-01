from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any

from engine.terrain_truth.bbox import BBox


@dataclass(frozen=True)
class SpeciesProfile:
    name: str
    role: str
    movement_read: str
    methods: tuple[str, ...]
    visual_prompt: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "movement_read": self.movement_read,
            "methods": list(self.methods),
            "visual_prompt": self.visual_prompt,
        }


@dataclass(frozen=True)
class RegionResult:
    region_key: str
    confidence: float
    classification_method: str
    fallback_explanation: str = ""


LOWER_48_BOUNDS = {
    "min_lon": -125.0,
    "max_lon": -66.0,
    "min_lat": 24.0,
    "max_lat": 49.5,
}

REGION_CENTERS: dict[str, tuple[float, float]] = {
    "appalachian": (39.0, -79.5),
    "southwoods": (32.0, -88.5),
    "midwest_ag_edge": (41.0, -93.0),
    "plains": (39.0, -101.0),
    "mountain": (41.0, -111.0),
    "desert_southwest": (33.0, -110.0),
    "northern_forest": (46.5, -91.0),
}


def _bbox_center(bbox: BBox) -> tuple[float, float]:
    min_lon, min_lat, max_lon, max_lat = bbox.as_list()
    return ((min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0)


def _bbox_is_lower_48(bbox: BBox) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox.as_list()
    return (
        LOWER_48_BOUNDS["min_lon"] <= min_lon < max_lon <= LOWER_48_BOUNDS["max_lon"]
        and LOWER_48_BOUNDS["min_lat"] <= min_lat < max_lat <= LOWER_48_BOUNDS["max_lat"]
    )


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_miles = 3958.8
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    r_lat1 = radians(lat1)
    r_lat2 = radians(lat2)
    a = sin(d_lat / 2) ** 2 + cos(r_lat1) * cos(r_lat2) * sin(d_lon / 2) ** 2
    return earth_radius_miles * 2 * asin(sqrt(a))


def _nearest_region(lat: float, lon: float) -> RegionResult:
    distances = {
        key: _haversine_miles(lat, lon, center_lat, center_lon)
        for key, (center_lat, center_lon) in REGION_CENTERS.items()
    }
    region_key = min(distances, key=distances.get)
    nearest_miles = distances[region_key]
    if nearest_miles <= 250:
        confidence = 0.62
    elif nearest_miles <= 450:
        confidence = 0.52
    else:
        confidence = 0.42
    return RegionResult(
        region_key=region_key,
        confidence=confidence,
        classification_method="nearest_region_haversine_fallback",
        fallback_explanation=(
            f"No coordinate rule matched. Used nearest hunting-region anchor: "
            f"{region_key}, approximately {nearest_miles:.0f} miles from bbox centroid."
        ),
    )


def _region_key(lon: float, lat: float) -> RegionResult:
    # New Mexico needs special handling before broad western rules.
    if 31.2 <= lat <= 37.1 and -109.1 <= lon <= -103.0:
        if lat >= 34.5:
            return RegionResult("mountain", 0.82, "coordinate_rule_nm_northern_mountain")
        return RegionResult("desert_southwest", 0.78, "coordinate_rule_nm_southern_desert")

    # Texas split: west Texas desert/open range vs central/east timber/pine belt.
    if 25.5 <= lat <= 36.6 and -106.7 <= lon <= -93.5:
        if lon <= -101.0:
            return RegionResult("desert_southwest", 0.76, "coordinate_rule_west_texas_desert_basin")
        if lon <= -98.0 and lat >= 31.0:
            return RegionResult("plains", 0.66, "coordinate_rule_northwest_texas_plains_transition")
        return RegionResult("southwoods", 0.79, "coordinate_rule_central_east_texas_southern_timber")

    # Appalachia is a valid region, not a fallback.
    if 34.0 <= lat <= 42.8 and -84.8 <= lon <= -74.0:
        return RegionResult("appalachian", 0.82, "coordinate_rule_appalachian_hardwood")

    # Southern pine/timber belt outside Texas.
    if 29.0 <= lat <= 36.8 and -97.5 <= lon <= -75.0:
        return RegionResult("southwoods", 0.75, "coordinate_rule_southern_pine_belt")

    # Northern forest / boreal edge.
    if 44.0 <= lat <= 49.5 and -97.5 <= lon <= -67.0:
        return RegionResult("northern_forest", 0.77, "coordinate_rule_northern_forest_boreal")

    # Midwest ag edge.
    if 37.0 <= lat <= 44.8 and -98.5 <= lon <= -82.0:
        return RegionResult("midwest_ag_edge", 0.74, "coordinate_rule_midwest_ag_edge")

    # Great Plains.
    if 33.0 <= lat <= 49.5 and -104.5 <= lon <= -96.0:
        return RegionResult("plains", 0.74, "coordinate_rule_great_plains_open_range")

    # Western mountain elk.
    if 34.0 <= lat <= 49.5 and -124.0 <= lon <= -104.0:
        return RegionResult("mountain", 0.73, "coordinate_rule_western_mountain_elk")

    # Desert Southwest.
    if 31.0 <= lat <= 37.5 and -117.5 <= lon <= -103.0:
        return RegionResult("desert_southwest", 0.73, "coordinate_rule_desert_basin_southwest")

    return _nearest_region(lat, lon)


def _cover_modifier(vegetation_classification: str | None) -> str:
    cover = str(vegetation_classification or "unknown").lower()
    if cover == "forest":
        return "heavy timber, shaded cover, and close-range movement pressure"
    if cover == "shrub":
        return "mixed brush, edge cover, and broken visibility"
    if cover == "open":
        return "open exposure, longer sight lines, and edge-dependent movement"
    if cover == "water":
        return "water influence, access constraints, and non-bedding terrain"
    return "mixed cover and field-verified habitat conditions"


def _profiles_for_region(region: str) -> tuple[str, str, str, tuple[SpeciesProfile, ...]]:
    common_rifle = "centerfire rifle / .30-06-class rifle where legal"
    methods_deer = (common_rifle, "muzzleloader season", "archery / crossbow where legal")
    methods_turkey = ("shotgun where legal", "archery", "state-season-specific method rules")
    methods_bear = (common_rifle, "muzzleloader where legal", "archery where legal")

    if region == "northern_forest":
        return (
            "Northern forest and boreal-edge wildlife atmosphere",
            "Mixed conifer-hardwood cover, wet edges, and cold-country scouting context",
            "cedar swamp edges, logging cuts, aspen regrowth, lake-country timber",
            (
                SpeciesProfile("White-tailed Deer", "Primary timber read", "Movement often keys on cedar edges, logging cuts, and sheltered browse routes.", methods_deer, "realistic whitetail deer in northern forest edge, mature hunting scouting atmosphere"),
                SpeciesProfile("Black Bear", "Bear-country read", "Food, thick cover, wet edges, and low-pressure access shape the read.", methods_bear, "realistic black bear in northern mixed forest, serious scouting visual"),
                SpeciesProfile("Ruffed Grouse", "Upland cover read", "Young aspen, logging roads, and edge cover can define movement.", ("shotgun where legal", "state-season-specific method rules"), "realistic ruffed grouse in aspen regrowth, northern hunting context"),
            ),
        )

    if region == "mountain":
        return (
            "Western mountain and elk-country wildlife atmosphere",
            "Bigger relief, exposed approaches, and wind-driven movement",
            "ridge light, alpine timber, steep basin shadow, mountain benches",
            (
                SpeciesProfile("Elk", "Primary big-game read", "Travel often keys on benches, saddles, timber edge, and pressure escape routes.", (common_rifle, "muzzleloader season", "archery season"), "realistic elk in western mountain timber, dramatic hunting intelligence background"),
                SpeciesProfile("Mule Deer", "Secondary big-game read", "Open slope to cover transitions and glassing terrain matter most.", methods_deer, "realistic mule deer buck on mountain sage edge, cinematic scouting report style"),
                SpeciesProfile("Black Bear", "Bear-country read", "Food sources, shaded drainages, and thick timber edges drive the read.", methods_bear, "realistic black bear in rocky mountain timber edge, mature hunter-focused visual"),
            ),
        )

    if region == "desert_southwest":
        return (
            "Desert basin and Southwest wildlife atmosphere",
            "Dry washes, open scrub, rocky breaks, and water-sensitive movement",
            "mesquite flats, arroyos, juniper breaks, canyon edges",
            (
                SpeciesProfile("Mule Deer", "Primary desert-edge read", "Movement often keys on washes, rocky draws, shade pockets, and water-influenced travel.", methods_deer, "realistic mule deer buck in desert basin scrub and rocky draw, cinematic hunting scouting atmosphere"),
                SpeciesProfile("Pronghorn", "Open-country read", "Visibility, distance, and open-range travel shape the scouting context.", (common_rifle, "archery where legal", "state-season-specific method rules"), "realistic pronghorn in Southwest open basin, mature scouting visual"),
                SpeciesProfile("Javelina", "Southwest opportunity read", "Brush, cactus flats, washes, and low desert cover can matter where present.", ("centerfire rifle where legal", "archery where legal", "state-season-specific method rules"), "realistic javelina in desert scrub, hunter scouting context"),
            ),
        )

    if region == "plains":
        return (
            "Great Plains and open-range wildlife atmosphere",
            "Open exposure, shelter breaks, creek bottoms, and cover islands",
            "wide horizon, grass breaks, cottonwood draws, rimrock edges",
            (
                SpeciesProfile("Pronghorn", "Primary open-country read", "Sight lines, wind, and open-range travel dominate the scouting context.", (common_rifle, "archery where legal", "state-season-specific method rules"), "realistic pronghorn in open prairie range, cinematic scouting visual"),
                SpeciesProfile("Mule Deer", "Breaks and draw read", "Breaks, draws, and open-to-cover movement deserve priority.", methods_deer, "realistic mule deer buck in prairie breaks and sage, cinematic hunter atmosphere"),
                SpeciesProfile("White-tailed Deer", "Creek-bottom edge read", "Cover islands, shelterbelts, and cottonwood corridors can compress movement.", methods_deer, "realistic whitetail buck near prairie shelter belt, dramatic scouting visual"),
            ),
        )

    if region == "midwest_ag_edge":
        return (
            "Midwest agriculture and edge-habitat wildlife atmosphere",
            "Crop edges, woodlots, creek corridors, and pressure-sensitive travel",
            "fencerows, creek bottoms, CRP fields, timber islands",
            (
                SpeciesProfile("White-tailed Deer", "Primary ag-edge read", "Field edges, woodlot funnels, and creek corridors often define timing.", methods_deer, "realistic whitetail buck near Midwest crop edge and woodlot, mature scouting visual"),
                SpeciesProfile("Wild Turkey", "Secondary flock read", "Roost cover, field edges, and creek corridors can define movement timing.", methods_turkey, "realistic wild turkey along Midwest field edge, serious outdoor scouting background"),
                SpeciesProfile("Coyote", "Predator-pressure read", "Edges, draws, and travel corridors can reflect predator movement pressure.", ("state-season-specific method rules",), "realistic coyote near Midwest fencerow and field edge, subtle hunting atmosphere"),
            ),
        )

    if region == "southwoods":
        return (
            "Southern timber and pine-belt wildlife atmosphere",
            "Dense cover, humid timber, creek drains, and quiet access pressure",
            "pine flats, hardwood bottoms, cutovers, warm timber shade",
            (
                SpeciesProfile("White-tailed Deer", "Primary timber read", "Bedding cover, shaded edges, and low-pressure access drive the read.", methods_deer, "realistic whitetail buck in southern hardwood timber, cinematic hunting intelligence visual"),
                SpeciesProfile("Wild Turkey", "Secondary flock read", "Roost-to-feed travel and open timber edges matter.", methods_turkey, "realistic wild turkey in southern timber, mature outdoors visual"),
                SpeciesProfile("Feral Hog", "Regional opportunity read", "Thick cover, water, and disturbed ground can matter where hogs are present.", ("centerfire rifle where legal", "shotgun where legal", "archery where legal"), "realistic feral hog in southern brush, gritty hunter scouting atmosphere"),
            ),
        )

    return (
        "Appalachian hardwood wildlife atmosphere",
        "Timber folds, side-hill cover, and disciplined access",
        "dark hardwood ridges, laurel cover, cold creek bottoms",
        (
            SpeciesProfile("White-tailed Deer", "Primary terrain read", "Side-hill benches, bedding edges, and access discipline drive the setup.", methods_deer, "realistic mature whitetail buck in Appalachian hardwood ridge, cinematic hunting scouting background"),
            SpeciesProfile("Wild Turkey", "Secondary flock read", "Open timber, roost-to-feed movement, and ridge transitions matter.", methods_turkey, "realistic wild turkey in Appalachian hardwood forest, mature outdoor visual"),
            SpeciesProfile("Black Bear", "Bear-country read", "Thick cover, food sources, and shaded drainages shape the read.", methods_bear, "realistic black bear in Appalachian timber, serious hunter-focused scouting visual"),
        ),
    )


def _apply_optional_signal_adjustment(
    result: RegionResult,
    vegetation_classification: str | None,
) -> RegionResult:
    # Keep this conservative. Vegetation should enrich the atmosphere, not override the bbox.
    # Future versions can use elevation/slope signals here once they are passed into this module.
    return result


def build_wildlife_atmosphere(
    bbox: BBox,
    vegetation_classification: str | None = None,
) -> dict[str, Any]:
    lon, lat = _bbox_center(bbox)
    if not _bbox_is_lower_48(bbox):
        result = _nearest_region(lat, lon)
    else:
        result = _region_key(lon, lat)
    result = _apply_optional_signal_adjustment(result, vegetation_classification)

    label, story, mood, profiles = _profiles_for_region(result.region_key)
    cover_read = _cover_modifier(vegetation_classification)
    species = [profile.to_dict() for profile in profiles]
    primary_names = " · ".join(item["name"] for item in species[:3])

    method_summary: list[str] = []
    seen: set[str] = set()
    for item in species:
        for method in item["methods"]:
            clean = str(method)
            key = clean.lower()
            if key not in seen:
                seen.add(key)
                method_summary.append(clean)

    fallback_note = ""
    if result.fallback_explanation:
        fallback_note = f" Classification note: {result.fallback_explanation}"

    return {
        "version": "wildlife_atmosphere_v2_bbox_deterministic",
        "region_key": result.region_key,
        "label": label,
        "species_label": primary_names,
        "mood": mood,
        "story": f"{story}. Current cover signal suggests {cover_read}.{fallback_note}",
        "cover_read": cover_read,
        "species": species,
        "method_summary": method_summary[:5],
        "classification_method": result.classification_method,
        "classification_confidence": round(result.confidence, 2),
        "fallback_explanation": result.fallback_explanation,
        "centroid": {"lat": round(lat, 6), "lon": round(lon, 6)},
        "legal_note": "Hunting method labels are general context only. Always verify state, season, tag, weapon, access, and safety rules before hunting.",
        "visual_style": "mature cinematic hunter scouting atmosphere; realistic animals; no cartoon icons; dark textured background; subtle weapon-category context",
    }
