from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import json


@dataclass
class TerrainArtifact:
    provider: str
    path: str
    format: str
    pixel_dimensions: list[int]


@dataclass
class TerrainDerivativeArtifact:
    hillshade_path: str
    summary_path: str
    structure_bias: str
    elevation_min_m: float
    elevation_max_m: float


@dataclass
class VegetationArtifact:
    provider: str
    classification: str
    notes: list[str] = field(default_factory=list)


def _default_vegetation() -> VegetationArtifact:
    return VegetationArtifact(
        provider="unknown",
        classification="unknown",
        notes=["Vegetation not provided in this contract build."],
    )


@dataclass
class LegalArtifact:
    provider: str
    path: str
    summary_path: str
    legal_feature_count: int
    restricted_feature_count: int
    unknown_feature_count: int


@dataclass
class SiteArtifact:
    rank: int
    tier: str
    title: str
    score: int
    lon: float
    lat: float
    elevation_m: float
    slope_bias: str
    legality_status: str
    source_name: str
    reasoning: str


@dataclass
class CorridorArtifact:
    name: str
    strength: str
    points: list[list[float]]
    reasoning: str


@dataclass
class DecisionArtifact:
    path: str
    primary: SiteArtifact
    alternates: list[SiteArtifact]
    near_misses: list[SiteArtifact]
    corridors: list[CorridorArtifact]
    notes: list[str]
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandSurfaceArtifact:
    path: str
    format: str = "text/html"


@dataclass
class TerrainTruthContract:
    run_id: str
    bbox: list[float]
    crs: str
    terrain: TerrainArtifact
    terrain_derivatives: TerrainDerivativeArtifact
    vegetation: VegetationArtifact = field(default_factory=_default_vegetation)
    legal_surface: LegalArtifact = None
    decision: DecisionArtifact = None
    command_surface: CommandSurfaceArtifact = None
    notes: list[str] = field(default_factory=list)
    operator_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")