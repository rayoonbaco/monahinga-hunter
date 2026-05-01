from __future__ import annotations

from dataclasses import dataclass

DEFAULT_LAYER_PREFERENCE: tuple[str, ...] = ("terrain", "hillshade", "relief", "slope")
DEFAULT_PADUS_MODE = "hybrid"
PADUS_LINE_HEAVY_COVERAGE_RATIO = 0.18
PADUS_FORCE_LINES_IF_CROPPED = True


@dataclass(frozen=True)
class ViewerDefaults:
    default_layer: str
    default_padus_mode: str = DEFAULT_PADUS_MODE


def resolve_default_layer(available_layers: dict[str, str]) -> str:
    for key in DEFAULT_LAYER_PREFERENCE:
        if key in available_layers:
            return key
    return next(iter(available_layers), "terrain")


def resolve_default_padus_mode(coverage_ratio: float, cropped: bool) -> str:
    if PADUS_FORCE_LINES_IF_CROPPED and cropped:
        return "lines"
    if coverage_ratio >= PADUS_LINE_HEAVY_COVERAGE_RATIO:
        return "lines"
    return DEFAULT_PADUS_MODE
