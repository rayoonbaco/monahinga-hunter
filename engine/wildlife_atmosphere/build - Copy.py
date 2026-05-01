from __future__ import annotations

from dataclasses import dataclass
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


def _bbox_center(bbox: BBox) -> tuple[float, float]:
    min_lon, min_lat, max_lon, max_lat = bbox.as_list()
    return ((min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0)


def _region_key(lon: float, lat: float) -> str:
    if lon < -110 and lat >= 43:
        return "northern_rockies"
    if lon < -108 and lat > 36:
        return "mountain"
    if lon > -90 and lat < 37:
        return "southwoods"
    if lon > -104 and lon < -92 and lat > 35 and lat < 47:
        return "plains"
    return "appalachian"


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

    if region == "northern_rockies":
        return (
            "Northern Rockies big-game atmosphere",
            "High relief, cold light, and predator-aware scouting context",
            "alpine shadow, dark timber, snowline ridges",
            (
                SpeciesProfile("Elk", "Primary big-game read", "Ridge benches, dark timber edges, and wind-sensitive travel corridors.", (common_rifle, "muzzleloader season", "archery season"), "cinematic mature bull elk in cold Rocky Mountain timber, realistic hunting scouting atmosphere"),
                SpeciesProfile("Mule Deer", "Secondary big-game read", "Broken slopes, open-to-cover transitions, and glassing-friendly terrain.", methods_deer, "realistic mule deer buck on sage and timber edge, western hunting terrain, cinematic light"),
                SpeciesProfile("Black Bear", "Bear-country read", "Food edges, dark timber, berry slopes, and access discipline.", methods_bear, "realistic black bear in mountain forest edge, serious scouting visual, no cartoon style"),
            ),
        )

    if region == "mountain":
        return (
            "Western mountain big-game atmosphere",
            "Bigger relief, exposed approaches, and wind-driven movement",
            "ridge light, alpine timber, steep basin shadow",
            (
                SpeciesProfile("Elk", "Primary big-game read", "Travel often keys on benches, saddles, timber edge, and pressure escape routes.", (common_rifle, "muzzleloader season", "archery season"), "realistic elk in western mountain timber, dramatic hunting intelligence background"),
                SpeciesProfile("Mule Deer", "Secondary big-game read", "Open slope to cover transitions and glassing terrain matter most.", methods_deer, "realistic mule deer buck on mountain sage edge, cinematic scouting report style"),
                SpeciesProfile("Black Bear", "Bear-country read", "Food sources, shaded drainages, and thick timber edges drive the read.", methods_bear, "realistic black bear in rocky mountain timber edge, mature hunter-focused visual"),
            ),
        )

    if region == "plains":
        return (
            "Plains-edge wildlife atmosphere",
            "Open exposure, shelter breaks, and cover islands",
            "wide horizon, grass breaks, cottonwood draws",
            (
                SpeciesProfile("White-tailed Deer", "Primary edge read", "Cover islands and creek breaks can compress daylight movement.", methods_deer, "realistic whitetail buck near prairie shelter belt, dramatic scouting visual"),
                SpeciesProfile("Mule Deer", "Secondary open-country read", "Breaks, draws, and open-to-cover movement deserve priority.", methods_deer, "realistic mule deer buck in prairie breaks and sage, cinematic hunter atmosphere"),
                SpeciesProfile("Wild Turkey", "Flock movement read", "Roost cover, field edges, and creek corridors can define timing.", methods_turkey, "realistic wild turkey in grassland edge, serious outdoor scouting background"),
            ),
        )

    if region == "southwoods":
        return (
            "Southern timber wildlife atmosphere",
            "Dense cover, humid timber, and quiet access pressure",
            "humid understory, creek bottoms, warm timber shade",
            (
                SpeciesProfile("White-tailed Deer", "Primary timber read", "Bedding cover, shaded edges, and low-pressure access drive the read.", methods_deer, "realistic whitetail buck in southern hardwood timber, cinematic hunting intelligence visual"),
                SpeciesProfile("Wild Turkey", "Secondary flock read", "Roost-to-feed travel and open timber edges matter.", methods_turkey, "realistic wild turkey in southern timber, mature outdoors visual"),
                SpeciesProfile("Feral Hog", "Regional opportunity read", "Thick cover, water, and disturbed ground can matter where hogs are present.", ("centerfire rifle where legal", "shotgun where legal", "archery where legal"), "realistic feral hog in southern brush, gritty hunter scouting atmosphere"),
            ),
        )

    return (
        "Appalachian wildlife atmosphere",
        "Timber folds, side-hill cover, and disciplined access",
        "dark hardwood ridges, laurel cover, cold creek bottoms",
        (
            SpeciesProfile("White-tailed Deer", "Primary terrain read", "Side-hill benches, bedding edges, and access discipline drive the setup.", methods_deer, "realistic mature whitetail buck in Appalachian hardwood ridge, cinematic hunting scouting background"),
            SpeciesProfile("Wild Turkey", "Secondary flock read", "Open timber, roost-to-feed movement, and ridge transitions matter.", methods_turkey, "realistic wild turkey in Appalachian hardwood forest, mature outdoor visual"),
            SpeciesProfile("Black Bear", "Bear-country read", "Thick cover, food sources, and shaded drainages shape the read.", methods_bear, "realistic black bear in Appalachian timber, serious hunter-focused scouting visual"),
        ),
    )


def build_wildlife_atmosphere(
    bbox: BBox,
    vegetation_classification: str | None = None,
) -> dict[str, Any]:
    lon, lat = _bbox_center(bbox)
    region = _region_key(lon, lat)
    label, story, mood, profiles = _profiles_for_region(region)
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
    return {
        "version": "wildlife_atmosphere_v1",
        "region_key": region,
        "label": label,
        "species_label": primary_names,
        "mood": mood,
        "story": f"{story}. Current cover signal suggests {cover_read}.",
        "cover_read": cover_read,
        "species": species,
        "method_summary": method_summary[:5],
        "legal_note": "Hunting method labels are general context only. Always verify state, season, tag, weapon, access, and safety rules before hunting.",
        "visual_style": "mature cinematic hunter scouting atmosphere; realistic animals; no cartoon icons; dark textured background; subtle weapon-category context",
    }
