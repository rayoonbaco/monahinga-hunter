from __future__ import annotations

from pathlib import Path
import html
import json
import os

from engine.command_surface.config import (
    ViewerDefaults,
    resolve_default_layer,
    resolve_default_padus_mode,
)
from engine.command_surface.payloads import (
    build_cluster_markup,
    build_invalidators,
    build_layer_buttons,
    build_payload,
    build_ranked_rows,
)
from engine.command_surface.template import HTML_TEMPLATE
from engine.terrain_truth.contract import TerrainTruthContract


def _coverage_sentence(ratio: float) -> str:
    pct = round(max(0.0, min(1.0, ratio)) * 100)
    if pct >= 55:
        tone = "Strong legal spread across this terrain window."
    elif pct >= 25:
        tone = "Useful legal coverage is present, but edge management matters."
    elif pct > 0:
        tone = "Legal land is limited here, so entry and exit discipline matters."
    else:
        tone = "No verified PAD-US legal surface is inside this box."
    return f"{pct}% PAD-US legal coverage in this box. {tone}"


def _terrain_sentence(summary: dict) -> str:
    strength = str(summary.get("terrain_strength") or "unknown").replace("_", " ").title()
    trust = str(summary.get("surface_trust") or "unverified").replace("_", " ").title()
    return f"Terrain read: {strength}. Viewer trust: {trust}."


def _wind_sentence(decision_summary: dict) -> str:
    current = str(decision_summary.get("current_wind") or "Not set")
    preferred = str(decision_summary.get("preferred_wind") or "Unknown")
    wind_fit = str(decision_summary.get("wind_fit") or "unknown").replace("_", " ").title()
    return f"Current wind {current}. Preferred wind {preferred}. Wind fit reads {wind_fit}."


def _vegetation_sentence(contract: TerrainTruthContract) -> str:
    veg = contract.vegetation
    classification = str(veg.classification or "unknown").title()
    provider = str(veg.provider or "unknown")

    if provider == "nlcd_annual":
        source = "NLCD (real data)"
        confidence = "High"
    elif provider == "terrain_heuristic":
        source = "Terrain-based fallback"
        confidence = "Medium"
    else:
        source = "Unavailable / failed"
        confidence = "Low"

    note = ""
    if veg.notes:
        note = veg.notes[0]
        note = note.replace("Heuristic fallback:", "").strip()

    return f"{classification} cover · Source: {source} · Confidence: {confidence}. {note}"


def _vegetation_signal(contract: TerrainTruthContract) -> tuple[str, str, str]:
    veg = contract.vegetation
    classification = str(veg.classification or "unknown").lower()

    if classification == "forest":
        return (
            "Strong Forest Concealment",
            "Boosting bedding reliability",
            "Reduced",
        )
    if classification == "shrub":
        return (
            "Moderate Concealment",
            "Supporting movement and partial bedding",
            "Moderate",
        )
    if classification == "open":
        return (
            "Low Cover / Exposure Risk",
            "Reducing bedding reliability",
            "High",
        )
    if classification == "water":
        return (
            "Non-viable Cover",
            "Blocking bedding and most movement",
            "Extreme",
        )

    return (
        "Unknown Cover",
        "Limited vegetation signal",
        "Unknown",
    )



DEFAULT_STRIPE_PAYMENT_LINK = "https://buy.stripe.com/8x2aEWb6f5qR7Td1mweEo00"


def _checkout_url() -> str:
    return "/checkout"


def _monetization_right_rail_markup() -> str:
    return (
        '<div class="intel-row provider-ok">'
        '<strong>Monahinga™ — Terrain Intelligence</strong>'
        '<span>This run produced a usable terrain read for field planning.</span>'
        '</div>'

        '<div class="intel-row provider-ok">'
        '<strong>Save this scouting run</strong>'
        '<span>Use Download Summary for the written report, copy coordinates for your notes, and use How to Save View for terrain images.</span>'
        '</div>'

        '<div class="intel-row provider-ok">'
        '<strong>Plan more than one move</strong>'
        '<span>Compare your primary sit against backup access, wind shifts, terrain funnels, and pressure changes before stepping into the field.</span>'
        '</div>'

        '<div class="intel-row provider-ok">'
        '<strong>Verify before acting</strong>'
        '<span>Monahinga™ supports scouting decisions, but you must confirm land access, seasons, tags, weapon rules, weather, and safety conditions.</span>'
        '</div>'

        '<div class="intel-row provider-ok">'
        '<strong>Field-ready workflow</strong>'
        '<span>Rotate the terrain, save the view you want, download the summary, and carry both into your scouting notes.</span>'
        '</div>'
    )

def _wildlife_atmosphere_markup(operator_context: dict) -> str:
    wildlife = (operator_context or {}).get("wildlife_atmosphere") or {}
    species = wildlife.get("species") or []
    if not isinstance(species, list) or not species:
        return ""

    def esc(value: object) -> str:
        return html.escape(str(value or ""))

    cards: list[str] = []
    for idx, item in enumerate(species[:3], start=1):
        if not isinstance(item, dict):
            continue
        name = esc(item.get("name"))
        role = esc(item.get("role"))
        movement = esc(item.get("movement_read"))
        methods = item.get("methods") or []
        method_text = " · ".join(esc(method) for method in methods[:3])
        cards.append(
            '<div class="wildlife-card">'
            f'<div class="wildlife-rank">0{idx}</div>'
            f'<div class="wildlife-name">{name}</div>'
            f'<div class="wildlife-role">{role}</div>'
            f'<div class="wildlife-motion">{movement}</div>'
            f'<div class="wildlife-methods">{method_text}</div>'
            '</div>'
        )

    if not cards:
        return ""

    label = esc(wildlife.get("label") or "Wildlife atmosphere")
    mood = esc(wildlife.get("mood") or "Region-driven visual context")
    legal_note = esc(wildlife.get("legal_note") or "Verify state regulations before hunting.")
    return (
        '<div class="wildlife-atmo-layer" aria-hidden="false">'
        '<div class="wildlife-atmo-panel wildlife-atmo-left">'
        '<div class="wildlife-kicker">Wildlife atmosphere</div>'
        f'<div class="wildlife-region">{label}</div>'
        f'<div class="wildlife-mood">{mood}</div>'
        '</div>'
        '<div class="wildlife-atmo-panel wildlife-atmo-right">'
        + "".join(cards) +
        f'<div class="wildlife-legal-note">{legal_note}</div>'
        '</div>'
        '</div>'
    )



def _display_key(value: object) -> str:
    text = str(value or "").strip().replace("_", " ")
    return text.title() if text else "Unknown"


def _hunter_core_markup(operator_context: dict) -> str:
    """Render the detailed HUNTER 2.0 field-intelligence panel.

    Pass 4B intentionally upgrades only language and presentation inside the
    existing right rail. It does not touch the 3D terrain canvas, JavaScript,
    template layout, or map geometry.
    """
    intel = (operator_context or {}).get("hunt_intelligence") or {}
    if not isinstance(intel, dict) or not intel.get("ok"):
        return (
            '<div class="intel-row provider-empty" style="border-color:rgba(245,211,138,.28);background:rgba(80,58,20,.22)">'
            '<strong>HUNTER 2.0 Brain</strong>'
            '<span>Ranked zone intelligence was not found on this run. Re-run after installing the latest pass files.</span>'
            '</div>'
        )

    def esc(value: object) -> str:
        return html.escape(str(value or ""))

    def clean(value: object) -> str:
        return str(value or "").strip().replace("_", " ").title()

    def setup_label(zone: dict, idx: int) -> str:
        raw = str(zone.get("label") or "").strip()
        lowered = raw.lower()
        if "bench" in lowered:
            base = "Mid-Slope Bench"
        elif "saddle" in lowered:
            base = "Saddle Transition"
        elif "ridge" in lowered and "edge" in lowered:
            base = "Leeward Ridge Edge"
        elif "spur" in lowered:
            base = "Spur Convergence"
        elif "bowl" in lowered or "hollow" in lowered or "drain" in lowered:
            base = "Thermal Bowl"
        elif raw:
            base = raw
        else:
            base = f"Field Setup {idx}"
        number = ""
        for part in raw.split():
            if part.isdigit():
                number = part
                break
        return f"{base} {number}".strip()

    def field_read(zone: dict) -> str:
        label = str(zone.get("label") or "").lower()
        setup = str(zone.get("setup_type") or "").lower()
        if "bench" in label or "flat" in setup:
            return "A bench or flatter shelf can slow movement and create a natural staging lane before deer commit to open terrain."
        if "ridge" in label or "edge" in label:
            return "This reads like an edge-travel setup where animals can move with cover while still checking the slope below."
        if "saddle" in label:
            return "A saddle compresses travel and gives the hunter a better chance to cover movement without watching the whole hillside."
        if "spur" in label:
            return "A spur convergence can collect side-hill travel and push movement into a tighter decision point."
        return "This zone scored well because the terrain, cover, wind, and access signals stack better here than in most of the box."

    def hunter_action(zone: dict) -> str:
        best_time = str(zone.get("best_time") or "").lower()
        label = str(zone.get("label") or "").lower()
        if "evening" in best_time:
            time_part = "Treat it as an evening transition setup."
        elif "morning" in best_time:
            time_part = "Treat it as a morning sit."
        else:
            time_part = "Treat it as a flexible setup, then let wind and fresh sign decide timing."
        if "bench" in label:
            return f"{time_part} Set up just off the bench edge, enter from the low-impact side, and avoid walking across the flat shelf."
        if "ridge" in label:
            return f"{time_part} Hunt the downwind edge and stay off the skyline so the ridge does not expose you."
        if "saddle" in label:
            return f"{time_part} Cover the pinch without sitting directly in the trail; keep your scent out of the crossing."
        return f"{time_part} Use this as a primary check spot, then shift only if wind, access, or fresh sign disagrees."

    def fail_condition(zone: dict) -> str:
        risks = zone.get("risks") or []
        if isinstance(risks, list) and risks:
            return str(risks[0])
        label = str(zone.get("label") or "").lower()
        if "bench" in label:
            return "Breaks if thermals rise across the bench or if the approach crosses the staging shelf."
        if "ridge" in label:
            return "Breaks if wind curls over the ridge or pressure pushes animals to the opposite side."
        if "saddle" in label:
            return "Breaks if your entry contaminates the pinch before the movement window opens."
        return "Breaks if the wind changes, access gets exposed, or fresh sign is not present."

    top_zones = intel.get("top_zones") or []
    if not isinstance(top_zones, list):
        top_zones = []

    summary = esc(intel.get("summary") or "Ranked terrain intelligence generated.")
    runtime = esc(intel.get("runtime_ms") or "0")
    zones_considered = esc(intel.get("zones_considered") or len(top_zones))
    version = esc(intel.get("version") or "hunter_core")

    cards: list[str] = []
    for idx, zone in enumerate(top_zones[:5], start=1):
        if not isinstance(zone, dict):
            continue
        label = esc(setup_label(zone, idx))
        score = esc(zone.get("score") or "")
        confidence = esc(zone.get("confidence") or "")
        setup_type = esc(clean(zone.get("setup_type")))
        best_time = esc(clean(zone.get("best_time")))
        lat = zone.get("lat")
        lon = zone.get("lon")
        try:
            coord = f"Lat {float(lat):.6f} - Lon {float(lon):.6f}"
        except Exception:
            coord = "Coordinates unavailable"
        coord = esc(coord)
        read_text = esc(field_read(zone))
        action_text = esc(hunter_action(zone))
        fail_text = esc(fail_condition(zone))

        cards.append(
            '<div style="margin:9px 0;padding:11px;border-radius:16px;'
            'border:1px solid rgba(174,241,134,.24);'
            'background:linear-gradient(135deg,rgba(18,40,28,.82),rgba(8,16,24,.86));">'
            '<div style="display:flex;align-items:flex-start;gap:10px;">'
            f'<div style="min-width:38px;height:38px;border-radius:13px;display:grid;place-items:center;background:rgba(174,241,134,.16);font-weight:900;color:#dfffd2;">{idx}</div>'
            '<div style="min-width:0;flex:1;">'
            f'<div style="font-size:15px;font-weight:950;line-height:1.15;color:#fff4df;">{label}</div>'
            f'<div style="margin-top:3px;font-size:11px;color:#9eb1be;">{setup_type} - {best_time}</div>'
            '</div>'
            f'<div style="font-size:24px;font-weight:950;color:#f5d38a;text-align:right;">{score}</div>'
            '</div>'
            f'<div style="margin-top:9px;font-size:12px;line-height:1.38;color:#cad6dc;"><strong style="color:#bdf6a7;">Field read:</strong> {read_text}</div>'
            f'<div style="margin-top:7px;font-size:12px;line-height:1.38;color:#dfffd2;"><strong style="color:#bdf6a7;">Best move:</strong> {action_text}</div>'
            f'<div style="margin-top:7px;font-size:12px;line-height:1.38;color:#d8c4a0;"><strong style="color:#f5d38a;">When it fails:</strong> {fail_text}</div>'
            f'<div style="margin-top:8px;font-size:11px;color:#9eb1be;">{coord} - Confidence {confidence}</div>'
            '</div>'
        )

    if not cards:
        cards.append(
            '<div class="intel-row provider-empty"><strong>No ranked zones</strong><span>The brain ran, but produced no usable zones from this heightmap.</span></div>'
        )

    return (
        '<div style="margin:8px 0 12px;padding:12px;border-radius:18px;'
        'border:1px solid rgba(174,241,134,.30);'
        'background:radial-gradient(circle at 20% 0%,rgba(174,241,134,.13),transparent 30%),rgba(5,18,14,.74);">'
        '<div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start;">'
        '<div>'
        '<div style="font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#aef186;font-weight:900;">HUNTER 2.0 Field Brain</div>'
        '<div style="font-size:18px;font-weight:950;color:#fff4df;margin-top:2px;">Elite Setup Read</div>'
        '</div>'
        f'<div style="text-align:right;font-size:10px;color:#9eb1be;line-height:1.35;">{zones_considered} zones<br>{runtime} ms</div>'
        '</div>'
        f'<div style="margin-top:8px;font-size:12px;line-height:1.4;color:#c6d2d9;">{summary}</div>'
        + "".join(cards) +
        f'<div style="margin-top:7px;font-size:10px;color:#7f939f;">Engine: {version}. Decision support only. Verify law, land access, sign, wind, and safety before acting.</div>'
        '</div>'
    )


def _provider_status_class(status: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"ok", "healthy", "available", "cache", "cached"}:
        return "provider-ok"
    if normalized in {"empty", "partial", "limited", "unknown", "degraded"}:
        return "provider-empty"
    if normalized in {"failed", "error", "unavailable", "none"}:
        return "provider-failed"
    return "provider-empty"


def _provider_status_markup(notes: list[str]) -> str:
    terrain = "unknown"
    legal = "unknown"
    vegetation = "unknown"
    messages: list[str] = []

    for note in notes:
        if note.startswith("Provider status:"):
            parts = note.replace("Provider status:", "").split(",")
            for part in parts:
                if "terrain=" in part:
                    terrain = part.split("=", 1)[1].strip().lower()
                if "legal=" in part:
                    legal = part.split("=", 1)[1].strip().lower()
                if "vegetation=" in part:
                    vegetation = part.split("=", 1)[1].strip().lower()
        elif "provider failed" in note.lower() or "no accessible features" in note.lower() or "nlcd" in note.lower():
            messages.append(note)

    rows = [
        f'<div class="intel-row {_provider_status_class(terrain)}"><strong>Terrain provider</strong><span>{html.escape(terrain.title())}</span></div>',
        f'<div class="intel-row {_provider_status_class(legal)}"><strong>Legal provider</strong><span>{html.escape(legal.title())}</span></div>',
        f'<div class="intel-row {_provider_status_class(vegetation)}"><strong>Vegetation provider</strong><span>{html.escape(vegetation.title())}</span></div>',
    ]

    for msg in messages:
        rows.append(
            f'<div class="intel-row provider-failed"><strong>Provider note</strong><span>{html.escape(msg)}</span></div>'
        )

    return "".join(rows)



def _hunter_core_spotlight_markup(operator_context: dict) -> str:
    """Compact right-rail card upgraded for field-ready decision language."""
    intel = (operator_context or {}).get("hunt_intelligence") or {}

    def esc(value: object) -> str:
        return html.escape(str(value or ""))

    def clean(value: object) -> str:
        return str(value or "").strip().replace("_", " ").title()

    def setup_label(zone: dict, idx: int = 1) -> str:
        raw = str(zone.get("label") or "").strip()
        lowered = raw.lower()
        if "bench" in lowered:
            base = "Best Setup: Mid-Slope Bench"
        elif "saddle" in lowered:
            base = "Best Setup: Saddle Transition"
        elif "ridge" in lowered and "edge" in lowered:
            base = "Best Setup: Leeward Ridge Edge"
        elif "spur" in lowered:
            base = "Best Setup: Spur Convergence"
        elif "bowl" in lowered or "hollow" in lowered or "drain" in lowered:
            base = "Best Setup: Thermal Bowl"
        elif raw:
            base = f"Best Setup: {raw}"
        else:
            base = "Best Setup: Field Setup"
        number = ""
        for part in raw.split():
            if part.isdigit():
                number = part
                break
        return f"{base} {number}".strip()

    def action_line(zone: dict) -> str:
        best_time = str(zone.get("best_time") or "").lower()
        label = str(zone.get("label") or "").lower()
        if "evening" in best_time:
            opener = "Evening move:"
        elif "morning" in best_time:
            opener = "Morning move:"
        else:
            opener = "Best move:"
        if "bench" in label:
            return f"{opener} enter low, stay off the flat shelf, and hunt the downwind edge of the bench."
        if "ridge" in label:
            return f"{opener} stay below the skyline and let the wind carry scent off the travel edge."
        if "saddle" in label:
            return f"{opener} cover the pinch from the side instead of standing directly in the crossing."
        return f"{opener} use this as the first setup only if wind and fresh sign agree."

    if not isinstance(intel, dict) or not intel.get("ok"):
        return (
            '<div class="block" style="margin-bottom:8px;border-color:rgba(245,211,138,.34);'
            'background:linear-gradient(135deg,rgba(82,58,20,.34),rgba(8,16,24,.88));">'
            '<h3 style="margin-bottom:6px;color:#f5d38a">HUNTER 2.0 Brain</h3>'
            '<div class="note"><strong>Waiting for ranked-zone intelligence.</strong><br>'
            'Run a fresh box after installing this pass. If this message stays, send me the black-window log.</div>'
            '</div>'
        )

    top_zones = intel.get("top_zones") or []
    if not isinstance(top_zones, list):
        top_zones = []
    best = top_zones[0] if top_zones and isinstance(top_zones[0], dict) else {}
    label = esc(setup_label(best))
    score = esc(best.get("score") or "--")
    confidence = esc(best.get("confidence") or "--")
    action = esc(action_line(best))
    zones_considered = esc(intel.get("zones_considered") or len(top_zones))
    runtime = esc(intel.get("runtime_ms") or "0")

    rows: list[str] = []
    for idx, zone in enumerate(top_zones[:3], start=1):
        if not isinstance(zone, dict):
            continue
        zlabel_raw = str(zone.get("label") or f"Zone {idx}")
        if "bench" in zlabel_raw.lower():
            zlabel = "Mid-Slope Bench"
        elif "ridge" in zlabel_raw.lower():
            zlabel = "Leeward Ridge Edge"
        elif "saddle" in zlabel_raw.lower():
            zlabel = "Saddle Transition"
        else:
            zlabel = zlabel_raw
        zlabel = esc(zlabel)
        zscore = esc(zone.get("score") or "--")
        ztime = esc(clean(zone.get("best_time")))
        rows.append(
            '<div style="display:grid;grid-template-columns:28px 1fr 42px;gap:8px;align-items:center;'
            'padding:7px 0;border-top:1px solid rgba(255,255,255,.07);">'
            f'<div style="width:24px;height:24px;border-radius:9px;display:grid;place-items:center;'
            f'background:rgba(174,241,134,.16);color:#dfffd2;font-weight:900;">{idx}</div>'
            f'<div style="min-width:0"><strong style="display:block;color:#fff4df;font-size:12px;line-height:1.15">{zlabel}</strong>'
            f'<span style="font-size:10px;color:#9eb1be">{ztime}</span></div>'
            f'<div style="text-align:right;color:#f5d38a;font-weight:900;font-size:15px">{zscore}</div>'
            '</div>'
        )

    return (
        '<div class="block" id="hunterCoreSpotlight" style="margin-bottom:8px;'
        'border-color:rgba(174,241,134,.34);'
        'background:radial-gradient(circle at 85% 0%,rgba(174,241,134,.16),transparent 34%),'
        'linear-gradient(135deg,rgba(6,32,22,.92),rgba(8,16,24,.92));'
        'box-shadow:0 0 0 1px rgba(174,241,134,.08) inset;">'
        '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:6px">'
        '<div><h3 style="margin-bottom:2px;color:#dfffd2">HUNTER 2.0 Brain</h3>'
        '<div style="font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#9eb1be">Elite field setup read</div></div>'
        f'<div style="text-align:right"><div style="font-size:28px;line-height:1;color:#f5d38a;font-weight:950">{score}</div>'
        f'<div style="font-size:10px;color:#9eb1be">conf {confidence}</div></div>'
        '</div>'
        f'<div class="note"><strong>{label}</strong><br>{action}</div>'
        + ''.join(rows) +
        f'<div style="margin-top:6px;font-size:10px;color:#9eb1be">{zones_considered} zones checked - {runtime} ms - field-verify wind, access, legality, and sign.</div>'
        '</div>'
    )


def _format_coords(lat: float, lon: float) -> str:
    return f"Lat {lat:.6f} · Lon {lon:.6f}"


def _coordinate_rows(primary, alternates: list) -> str:
    rows = [
        f'<div class="intel-row"><strong>Primary sit coordinates</strong><span>{html.escape(_format_coords(primary.lat, primary.lon))} · {int(round(primary.elevation_m))} m</span></div>'
    ]
    for site in alternates[:2]:
        rows.append(
            f'<div class="intel-row"><strong>{html.escape(site.title)} coordinates</strong><span>{html.escape(_format_coords(site.lat, site.lon))} · {int(round(site.elevation_m))} m</span></div>'
        )
    return "".join(rows)


def _box_status(decision_summary: dict, coverage_ratio: float) -> tuple[str, str, str]:
    legal_state = str(decision_summary.get("legal_state") or "none")
    if legal_state == "strong":
        return (
            "Strong verified legal hunting land",
            "Most of the selected box is covered by verified PAD-US legal hunting land.",
            "strong",
        )
    if legal_state == "partial" or coverage_ratio > 0:
        return (
            "Partial verified legal hunting land",
            "Only part of the selected box carries verified PAD-US legal hunting land, so edge discipline matters.",
            "partial",
        )
    return (
        "No verified legal hunting land",
        "No verified PAD-US legal land was found inside the selected box.",
        "none",
    )


def render_command_surface(run_root: Path, contract: TerrainTruthContract) -> Path:
    terrain_truth_root = run_root / "terrain_truth"
    derivative_dir = terrain_truth_root / "terrain_derivatives"
    summary = json.loads((derivative_dir / "terrain_summary.json").read_text(encoding="utf-8"))

    layer_files = {
        "terrain": derivative_dir / "terrain_render.png",
        "hillshade": derivative_dir / "hillshade.png",
        "slope": derivative_dir / "slope.png",
        "relief": derivative_dir / "local_relief.png",
    }
    available_layers = {
        key: f"../{str(path.relative_to(run_root)).replace(chr(92), '/')}"
        for key, path in layer_files.items()
        if path.exists()
    }

    viewer_defaults = ViewerDefaults(default_layer=resolve_default_layer(available_layers))
    payload = build_payload(run_root, contract, available_layers, summary, viewer_defaults)

    legal_summary = payload.get("summary") or {}
    resolved_padus_mode = resolve_default_padus_mode(
        float(legal_summary.get("legal_coverage_ratio") or 0.0),
        bool(legal_summary.get("legal_cropped_to_bbox")),
    )
    viewer_defaults = ViewerDefaults(
        default_layer=viewer_defaults.default_layer,
        default_padus_mode=resolved_padus_mode,
    )
    payload["defaultPadusMode"] = resolved_padus_mode
    payload_json = json.dumps(payload)

    decision_summary = contract.decision.summary or {}
    operator_context = contract.operator_context or {}
    primary = contract.decision.primary
    sites = [contract.decision.primary] + contract.decision.alternates + contract.decision.near_misses
    min_lon, min_lat, max_lon, max_lat = contract.bbox

    legal_badge = (
        "Legal fill clipped to terrain bbox"
        if legal_summary.get("legal_cropped_to_bbox")
        else "Legal fill contained inside terrain bbox"
    )

    primary_elevation_text = (
        f"{primary.title} sits at about {int(round(primary.elevation_m))} meters "
        f"and remains the lead setup."
    )
    box_status_title, box_status_body, box_status_tone = _box_status(
        decision_summary,
        float(legal_summary.get("legal_coverage_ratio") or 0.0),
    )
    pin_mode_text = (
        "Strong verified legal hunting land. Primary and alternate pins are being drawn only from verified legal land inside your selected box."
        if str(decision_summary.get("analysis_mode")) == "legal_hunt"
        else "No verified legal hunting land. Terrain-only review mode is active, so pins are exploration guidance rather than verified legal hunting spots."
    )

    provider_markup = _provider_status_markup(contract.notes or [])
    cover_read, veg_impact, exposure = _vegetation_signal(contract)
    vegetation_signal_markup = "".join(
        [
            f'<div class="intel-row"><strong>Cover</strong><span>{html.escape(cover_read)}</span></div>',
            f'<div class="intel-row"><strong>Impact</strong><span>{html.escape(veg_impact)}</span></div>',
            f'<div class="intel-row"><strong>Exposure</strong><span>{html.escape(exposure)}</span></div>',
        ]
    )

    wildlife_atmosphere_markup = _wildlife_atmosphere_markup(operator_context)

    hunting_read_markup = "".join(
        [
            _monetization_right_rail_markup(),
            _hunter_core_markup(operator_context),
            f'<div class="intel-row"><strong>Analysis mode</strong><span>{html.escape((decision_summary.get("selected_species") or "General Terrain Read").replace("_"," ").title())}</span></div>',
            f'<div class="intel-row"><strong>Species read</strong><span>{html.escape((decision_summary.get("species_profile") or {}).get("positive_hook",""))}</span></div>',
            f'<div class="intel-row"><strong>Cover read</strong><span>{html.escape(cover_read)}</span></div>',
            f'<div class="intel-row"><strong>Vegetation impact</strong><span>{html.escape(veg_impact)}</span></div>',
            f'<div class="intel-row"><strong>Exposure risk</strong><span>{html.escape(exposure)}</span></div>',
            f'<div class="intel-row"><strong>Legal coverage inside box</strong><span>{html.escape(_coverage_sentence(float(legal_summary.get("legal_coverage_ratio") or 0.0)))}</span></div>',
            f'<div class="intel-row"><strong>Legal state</strong><span>{html.escape(pin_mode_text)}</span></div>',
            f'<div class="intel-row"><strong>Terrain pull</strong><span>{html.escape(_terrain_sentence(legal_summary))}</span></div>',
            f'<div class="intel-row"><strong>Vegetation read</strong><span>{html.escape(_vegetation_sentence(contract))}</span></div>',
            f'<div class="intel-row"><strong>Cover layer</strong><span>{html.escape("Toggle Cover to separate dense concealment, moderate cover, and open ground in the 3D viewer. Selected sit glow marks the current read zone.")}</span></div>',
            provider_markup,
            f'<div class="intel-row"><strong>Live wind near primary sit</strong><span id="liveWindSummary">Loading live wind…</span><small id="liveWindMeta" class="micro-copy">Manual fallback remains available if live weather does not load.</small></div>',
            f'<div class="intel-row"><strong>Wind read</strong><span>{html.escape(_wind_sentence(decision_summary))}</span></div>',
            f'<div class="intel-row"><strong>Primary sit elevation</strong><span>{html.escape(primary_elevation_text)}</span></div>',
            _coordinate_rows(primary, contract.decision.alternates),
        ]
    )

    html_doc = HTML_TEMPLATE.substitute(
        provider=html.escape(contract.terrain.provider),
        legal_provider=html.escape(contract.legal_surface.provider),
        min_lon=f"{min_lon:.4f}",
        min_lat=f"{min_lat:.4f}",
        max_lon=f"{max_lon:.4f}",
        max_lat=f"{max_lat:.4f}",
        mesh_w=html.escape(str(summary.get("width"))),
        mesh_h=html.escape(str(summary.get("height"))),
        default_layer_label=html.escape(viewer_defaults.default_layer.title()),
        default_padus_label=html.escape(viewer_defaults.default_padus_mode.title()),
        legal_badge=html.escape(legal_badge),
        mode=html.escape(str(operator_context.get("mode") or "hunter").title()),
        current_wind=html.escape(str(decision_summary.get("current_wind") or "Not set")),
        preferred_wind=html.escape(str(decision_summary.get("preferred_wind") or "Unknown")),
        readiness=html.escape(str(decision_summary.get("readiness") or "Conditional")),
        layer_buttons=build_layer_buttons(available_layers, viewer_defaults.default_layer),
        selected_box_status_markup=f'<div class="block status-block tone-{box_status_tone}"><h3>Selected Box Status</h3><div class="note"><strong>{html.escape(box_status_title)}</strong><br>{html.escape(box_status_body)}</div></div>',
        operator_notes=html.escape(
            str(operator_context.get("notes") or "No operator notes supplied for this run.")
        ),
        best_time_label=html.escape(str(decision_summary.get("best_time_label") or "Prime window")),
        best_time_window=html.escape(str(decision_summary.get("best_time_window") or "Field-check timing.")),
        primary_title=html.escape(primary.title),
        confidence_label=html.escape(str(decision_summary.get("confidence_label") or "Medium")),
        confidence=html.escape(str(decision_summary.get("confidence") or "")),
        primary_reason=html.escape(
            (
                f"{(decision_summary.get('species_profile') or {}).get('positive_hook', '')} {primary.reasoning}"
                if (decision_summary.get('species_profile') or {}).get('positive_hook', '')
                else primary.reasoning
            )
        ),
        primary_tags=html.escape(json.dumps(list(decision_summary.get("trust_tags") or []))),
        primary_score=html.escape(str(primary.score)),
        cluster_markup=build_cluster_markup(decision_summary),
        hunting_read_markup=hunting_read_markup,
        hunter_core_spotlight_markup=_hunter_core_spotlight_markup(operator_context),
        vegetation_signal_markup=vegetation_signal_markup,
        wildlife_atmosphere_markup=wildlife_atmosphere_markup,
        invalidators=build_invalidators(decision_summary),
        ranked_rows=build_ranked_rows(sites),
        payload_json=payload_json,
    )

    output_dir = run_root / "command_surface"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(html_doc, encoding="utf-8")
    return output_path
