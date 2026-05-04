from __future__ import annotations

import json
from engine.terrain_truth.bbox import BBox

HOME_PAGE_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Monahinga™ Launch Surface</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  crossorigin=""
/>
<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css"
  crossorigin=""
/>
<style>
:root {
  --bg:#07111a;
  --bg2:#03060b;
  --panel:rgba(8,14,20,.92);
  --line:rgba(255,255,255,.08);
  --text:#e7e0d2;
  --muted:#a5b3bd;
  --green:#a8f183;
  --gold:#f3d78b;
  --blue:#83c9ff;
  --danger:#ff8f8f;
}
.header-row{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:12px}
.header-links{display:flex;gap:10px;flex-wrap:wrap}
.header-links a{color:var(--text);text-decoration:none;border:1px solid var(--line);background:rgba(255,255,255,.04);border-radius:999px;padding:9px 12px;font-size:13px}
.version-line{display:inline-flex;align-items:center;gap:8px;margin-top:12px;padding:10px 12px;border-radius:999px;border:1px solid rgba(243,215,139,.25);background:rgba(243,215,139,.07);color:#f5e7c4;font-size:13px}
.version-line:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 14px rgba(168,241,131,.8)}
*{box-sizing:border-box}
body {
  margin:0;
  font-family:Segoe UI,Arial,sans-serif;
  background:linear-gradient(180deg,var(--bg) 0%,var(--bg2) 100%);
  color:var(--text);
}

body::before{
  content:'';
  position:fixed;
  inset:0;
  background:
    radial-gradient(circle at 18% 12%, rgba(137,191,121,.16), transparent 22%),
    radial-gradient(circle at 82% 10%, rgba(131,201,255,.12), transparent 24%),
    radial-gradient(circle at 50% 100%, rgba(243,215,139,.08), transparent 30%),
    linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,0));
  pointer-events:none;
}
.shell {
  position:relative;

  max-width:1320px;
  margin:0 auto;
  padding:26px 20px 32px;
}
.kicker {
  font-size:12px;
  letter-spacing:.18em;
  color:#97abbb;
  text-transform:uppercase;
}
h1 {
  margin:10px 0 8px;
  font-size:46px;
  line-height:1.02;
}
.sub {
  color:var(--muted);
  line-height:1.5;
  max-width:1000px;
  font-size:17px;
}
.layout {
  display:grid;
  grid-template-columns: minmax(0,1.15fr) minmax(340px,.85fr);
  gap:18px;
  margin-top:22px;
  align-items:start; /* MONAHINGA_PAGE1_STOP_GRID_CARD_STRETCH_2026_05_04: prevent right cards from stretching to map height */
}
.card {
  padding:20px;
  border-radius:22px;
  border:1px solid var(--line);
  background:var(--panel);
}
h2 {
  margin:0 0 14px;
  font-size:20px;
}
.grid {
  display:grid;
  grid-template-columns:repeat(2, minmax(0,1fr));
  gap:12px;
}
.field {
  display:flex;
  flex-direction:column;
  gap:7px;
}
.field.full { grid-column:1 / -1; }
.coord-input { min-height:56px; resize:vertical; }
label {
  font-size:12px;
  letter-spacing:.08em;
  text-transform:uppercase;
  color:#91a4b1;
}
input, textarea, select {
  width:100%;
  border-radius:14px;
  border:1px solid rgba(255,255,255,.08);
  background:#0a1118;
  color:var(--text);
  padding:13px 14px;
  font:inherit;
}
textarea { min-height:92px; resize:vertical; }
.buttons {
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-top:16px;
}
button {
  border:0;
  border-radius:16px;
  padding:14px 18px;
  font-size:15px;
  font-weight:700;
  cursor:pointer;
}
.primary { background:var(--green); color:#08110b; }
.secondary { background:var(--gold); color:#101010; }
.ghost { background:rgba(255,255,255,.06); color:var(--text); }
.map-toolbar {
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin:10px 0 10px;
  align-items:center;
}
.map-toolbar .ghost { padding:10px 14px; border-radius:12px; }
.toolbar-note { color:#9fb0bc; font-size:13px; }
.search-row{
  display:grid;
  grid-template-columns:minmax(0,1fr) auto auto;
  gap:10px;
  margin:0 0 12px;
  align-items:center;
}
.search-row input{
  min-height:48px;
}
.search-meta{
  margin-top:8px;
  color:#9fb0bc;
  font-size:13px;
  line-height:1.4;
}
#bbox-map {
  height:430px;
  border-radius:18px;
  overflow:hidden;
  border:1px solid rgba(255,255,255,.08);
}
pre {
  white-space:pre-wrap;
  background:#05090f;
  color:#dfe7ec;
  padding:18px;
  border-radius:16px;
  border:1px solid rgba(255,255,255,.08);
  min-height:260px;
  margin:0;
}
.pillrow {
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin:12px 0 18px;
}
.pill {
  padding:10px 12px;
  border-radius:999px;
  background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.08);
  color:#d7e1e8;
  font-size:13px;
}
.helper {
  color:#8ea0ac;
  font-size:13px;
  line-height:1.45;
}
.helper strong { color:#d9e4ea; }
.disclaimer {
  margin-top:14px;
  padding:13px 14px;
  border-radius:16px;
  border:1px solid rgba(243,215,139,.20);
  background:rgba(243,215,139,.06);
  color:#d7d0c1;
  font-size:12.5px;
  line-height:1.5;
}
.disclaimer strong { color:#f3d78b; }
.bbox-readout {
  margin-top:10px;
  color:#c9d6de;
  font-size:13px;
}
.bbox-readout code {
  font-family:Consolas, monospace;
  background:rgba(255,255,255,.04);
  padding:2px 6px;
  border-radius:8px;
}
.inline-warning {
  margin-top:10px;
  padding:12px 14px;
  border-radius:14px;
  border:1px solid rgba(255,255,255,.08);
  background:rgba(255,255,255,.03);
  color:#d9e4ea;
  font-size:13px;
}
.inline-warning.warn {
  border-color:rgba(255,143,143,.35);
  background:rgba(255,143,143,.08);
  color:#ffd1d1;
}
.inline-warning.info {
  border-color:rgba(131,201,255,.35);
  background:rgba(131,201,255,.08);
  color:#d5efff;
}
/* Pass 24B: safe not-huntable overlay */
.not-huntable-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(0,0,0,.72);
}
.not-huntable-overlay.visible {
  display: flex;
}
.not-huntable-box {
  width: min(640px, 94vw);
  border-radius: 24px;
  border: 3px solid rgba(255,70,70,.95);
  background: linear-gradient(180deg, rgba(45,5,8,.98), rgba(8,10,14,.98));
  box-shadow: 0 30px 120px rgba(0,0,0,.8);
  padding: 30px 28px 26px;
  text-align: center;
}
.not-huntable-box h2 {
  margin: 0 0 14px;
  color: #ff4b4b;
  font-size: 42px;
  line-height: 1;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.not-huntable-box p {
  margin: 0 auto 14px;
  max-width: 540px;
  color: #ffe0e0;
  font-size: 19px;
  line-height: 1.38;
}
.not-huntable-box .small-copy {
  color: #d0aaaa;
  font-size: 13px;
  line-height: 1.4;
}
.not-huntable-box button {
  margin-top: 20px;
  background: #ff4b4b;
  color: white;
  font-size: 17px;
  padding: 14px 22px;
  border-radius: 16px;
}

small { color:#8ea0ac; }

.hero-band{
  margin-top:18px;
  padding:22px 22px 20px;
  border-radius:26px;
  border:1px solid rgba(255,255,255,.08);
  background:
    radial-gradient(circle at 18% 14%, rgba(168,241,131,.14), transparent 20%),
    radial-gradient(circle at 84% 16%, rgba(131,201,255,.14), transparent 22%),
    linear-gradient(180deg, rgba(10,20,30,.92), rgba(4,8,14,.96));
  box-shadow:0 26px 90px rgba(0,0,0,.34);
  overflow:hidden;
}
.hero-grid{
  display:grid;
  grid-template-columns:minmax(0,1.15fr) minmax(300px,.85fr);
  gap:18px;
  align-items:stretch;
}
.hero-copy h1{margin-top:8px}
.hero-pills{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 14px}
.hero-pill{
  padding:9px 12px;border-radius:999px;
  border:1px solid rgba(255,255,255,.1);
  background:rgba(255,255,255,.04);
  color:#e6efe8;font-size:13px;
}
.hero-story{max-width:760px;color:#d4dee5;line-height:1.55;font-size:16px}
.hero-visual{
  min-height:330px;border-radius:22px;position:relative;
  border:1px solid rgba(255,255,255,.08);overflow:hidden;
  background:
    radial-gradient(circle at 50% 20%, rgba(255,220,163,.14), transparent 18%),
    linear-gradient(180deg, rgba(47,81,110,.8), rgba(13,27,39,.96) 35%, rgba(5,11,18,.98));
}
.hero-visual::before{
  content:''; position:absolute; inset:0;
  background:
    linear-gradient(180deg, rgba(255,255,255,.04), transparent 24%),
    radial-gradient(circle at 50% 75%, rgba(28,63,36,.48), transparent 30%),
    linear-gradient(160deg, transparent 0 42%, rgba(255,255,255,.08) 42% 43%, transparent 43% 100%),
    linear-gradient(20deg, transparent 0 58%, rgba(255,255,255,.06) 58% 59%, transparent 59% 100%);
  opacity:.95;
}
.hero-visual::after{
  content:''; position:absolute; inset:auto 0 0 0; height:48%;
  background:
    radial-gradient(circle at 24% 70%, rgba(50,86,55,.82), transparent 26%),
    radial-gradient(circle at 58% 80%, rgba(65,102,68,.8), transparent 28%),
    radial-gradient(circle at 80% 72%, rgba(52,76,58,.78), transparent 22%);
}
.hero-overlay{
  position:absolute; inset:16px; display:block; z-index:1;
}
.hero-overlay-top{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.hero-badge{
  padding:8px 11px;border-radius:999px;
  border:1px solid rgba(255,255,255,.12);background:rgba(6,12,18,.52);
  color:#f1ead8;font-size:12px;backdrop-filter:blur(8px)
}
.hero-callout{
  position:absolute; left:0; right:0; bottom:108px; max-width:none; padding:12px 14px; border-radius:16px;
  background:rgba(5,10,16,.72); border:1px solid rgba(255,255,255,.08);
  color:#dce6ec; font-size:13px; line-height:1.42;
}
.hero-callout strong{display:block;color:#fff0d0;font-size:13px;margin-bottom:4px}
.region-emphasis{color:#fff3d6}
.theme-appalachian { --accent-region:#8bd46a; --accent-sky:#6fb0df; --accent-warm:#f0c47f; }
.theme-mountain { --accent-region:#80cfff; --accent-sky:#94b6dd; --accent-warm:#f0d6a0; }
.theme-plains { --accent-region:#cde27a; --accent-sky:#85c5ff; --accent-warm:#f3cb7e; }
.theme-southwoods { --accent-region:#7fd890; --accent-sky:#84b7d1; --accent-warm:#d6b36d; }
.theme-default { --accent-region:#a8f183; --accent-sky:#83c9ff; --accent-warm:#f3d78b; }
.hero-pill.region{border-color:rgba(255,255,255,.16); background:rgba(255,255,255,.06)}
.hero-pill.region strong{color:var(--accent-warm)}
.hero-band .kicker{color:#b6c4cd}
.launch-wildlife-strip{position:absolute;left:16px;right:16px;bottom:16px;z-index:2;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.launch-wildlife-card{min-height:64px;padding:9px;border-radius:15px;border:1px solid rgba(255,255,255,.10);background:linear-gradient(135deg, rgba(5,10,16,.72), rgba(5,10,16,.34));box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
.launch-wildlife-card strong{display:block;color:#fff0d0;font-size:12px;line-height:1.08}.launch-wildlife-card span{display:block;margin-top:4px;color:#c5d1d9;font-size:10.5px;line-height:1.22}.launch-methods{position:absolute;left:16px;right:16px;top:58px;z-index:2;padding:9px 11px;border-radius:14px;background:rgba(5,10,16,.58);border:1px solid rgba(255,255,255,.08);color:#d8c69b;font-size:11px;line-height:1.35}
.brand-stage{
  position:absolute;inset:20px;z-index:3;
  display:grid;grid-template-rows:auto 1fr auto;gap:18px;
}
.brand-topline{
  display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
}
.brand-chip{
  padding:8px 11px;border-radius:999px;
  border:1px solid rgba(243,215,139,.22);
  background:rgba(5,10,16,.58);
  color:#f3d78b;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
}
.brand-core{
  display:flex;align-items:center;justify-content:center;text-align:center;
  padding:12px;border-radius:22px;
  background:radial-gradient(circle at 50% 42%, rgba(168,241,131,.16), transparent 32%);
}
.monahinga-mark{
  width:116px;height:116px;margin:0 auto 14px;border-radius:50%;
  position:relative;border:1px solid rgba(243,215,139,.42);
  background:
    radial-gradient(circle at 50% 50%, rgba(243,215,139,.18), transparent 36%),
    linear-gradient(145deg, rgba(168,241,131,.10), rgba(131,201,255,.10));
  box-shadow:0 0 40px rgba(168,241,131,.10), inset 0 0 35px rgba(0,0,0,.35);
}
.monahinga-mark::before{
  content:'';position:absolute;left:24px;right:24px;top:30px;height:34px;
  border-radius:50% 50% 45% 45%;
  border-top:3px solid rgba(243,215,139,.78);
  border-left:2px solid rgba(168,241,131,.55);
  transform:rotate(-8deg);
}
.monahinga-mark::after{
  content:'';position:absolute;left:28px;right:28px;bottom:28px;height:38px;
  background:
    linear-gradient(135deg, transparent 0 46%, rgba(131,201,255,.42) 47% 53%, transparent 54%),
    linear-gradient(25deg, transparent 0 42%, rgba(243,215,139,.55) 43% 49%, transparent 50%);
  opacity:.9;
}
.brand-word{
  margin:0;
  font-size:38px;line-height:1;letter-spacing:.14em;text-transform:uppercase;
  color:#f6ead6;font-weight:900;
  text-shadow:0 8px 32px rgba(0,0,0,.45);
}
.brand-word sup{font-size:13px;letter-spacing:0;margin-left:4px;color:#f3d78b}
.brand-line{
  margin:12px auto 0;max-width:420px;color:#d7e1e8;
  font-size:18px;line-height:1.35;font-weight:700;
}
.brand-subline{
  margin:8px auto 0;max-width:430px;color:#9fb0bc;
  font-size:13px;line-height:1.45;
}
.brand-bottom{
  display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;
}
.brand-proof{
  min-height:62px;padding:10px;border-radius:15px;
  border:1px solid rgba(255,255,255,.10);
  background:linear-gradient(135deg, rgba(5,10,16,.76), rgba(5,10,16,.38));
}
.brand-proof strong{display:block;color:#fff0d0;font-size:12px;line-height:1.1}
.brand-proof span{display:block;margin-top:4px;color:#c5d1d9;font-size:10.5px;line-height:1.22}

@media (max-width: 980px){.launch-wildlife-strip{grid-template-columns:1fr}.launch-methods{position:relative;top:auto;left:auto;right:auto;margin:10px 16px 0}.hero-callout{position:relative;left:auto;right:auto;bottom:auto;margin-top:12px}.hero-overlay{display:flex;flex-direction:column;gap:10px}.hero-visual{min-height:430px}}
@media (max-width: 980px) {
  .hero-grid{grid-template-columns:1fr}
  .hero-visual{min-height:200px}
}

@media (max-width: 980px) {
  .layout { grid-template-columns:1fr; }
  h1 { font-size:38px; }
  #bbox-map { height:360px; }
}

/* MONAHINGA_PAGE1_REMOVE_BRAND_CARD_2026_05_04
   Page 1 visual simplification only.
   Removed the oversized brand card and lets the launch intro use the available space.
   Does not touch BBox, PAD-US/legal checks, species selector, map, run launch, backend, or Render config.
*/
.hero-grid{
  grid-template-columns: 1fr !important;
}
.hero-copy{
  max-width: 980px !important;
}
.hero-band{
  padding-bottom: 18px !important;
}
@media (max-width: 900px){
  .hero-copy{
    max-width: none !important;
  }
}


/* MONAHINGA_PAGE1_RESTORE_HIDE_OPERATOR_FIELDS_2026_05_04
   Repair pass: keep operator coordinate/wind/mode fields in the DOM for map/default-BBox scripts,
   but hide those repetitive fields visually. Species selector remains visible.
*/
.monahinga-hidden-operator-field{
  display:none !important;
}


/* MONAHINGA_PAGE1_REMOVE_DUPLICATE_INSTRUCTION_NOTES_2026_05_04
   Page 1 visual cleanup only.
   Hide duplicate bottom Instructions button and Operator Notes field.
   Keep top Instructions button, species selector, map, BBox workflow, and launch logic.
*/
.monahinga-page1-hidden-control{
  display:none !important;
}

button,
a,
[role="button"]{
  text-rendering: geometricPrecision;
}

.monahinga-top-instructions-strong{
  font-weight: 950 !important;
  font-size: 15px !important;
  letter-spacing: -.01em !important;
  padding: 12px 16px !important;
}


/* MONAHINGA_PAGE1_DIRECT_HERO_CLEANUP_2026_05_04
   Direct page-1 hero cleanup.
   Top product header gets stronger; deprecated U.S.-only sub-kicker and chip/story cluster are removed from source.
   Does not touch map logic, BBox logic, species selector, PAD-US/legal checks, terrain generation, backend, or Render config.
*/
.header-row > .kicker{
  color:#ffffff !important;
  font-weight:950 !important;
  font-size:clamp(20px, 1.55vw, 28px) !important;
  letter-spacing:.08em !important;
  line-height:1.15 !important;
}
.hero-copy h1{
  margin-top:4px !important;
}
.hero-copy .sub{
  margin-top:10px !important;
}


/* MONAHINGA_REDUCE_H1_2026_05_04 */
.hero-copy h1 {
  font-size: clamp(16px, 1.2vw, 22px) !important;
  line-height: 1.2 !important;
  font-weight: 700 !important;
}


/* MONAHINGA_PAGE1_RIGHT_COLUMN_STACK_2026_05_04
   Page 1 layout-only pass.
   Uses the blank right-side space by stacking lower info cards under the run setup column.
   Does not touch map logic, BBox logic, species selector, run buttons, backend, terrain, PAD-US, or Render config.
*/
.monahinga-right-stack-card{
  max-width: 100% !important;
  margin-top: 16px !important;
}

.monahinga-right-stack-card h3{
  font-size: 18px !important;
  margin-bottom: 12px !important;
}

.monahinga-right-stack-card p,
.monahinga-right-stack-card div,
.monahinga-right-stack-card span{
  font-size: 13px !important;
  line-height: 1.35 !important;
}

.monahinga-right-stack-card pre,
.monahinga-right-stack-card code{
  white-space: pre-wrap !important;
  word-break: break-word !important;
  font-size: 12px !important;
  max-height: 180px !important;
  overflow: auto !important;
}

.monahinga-right-stack-card .disclaimer,
.monahinga-right-stack-card [class*="disclaimer"]{
  margin-top: 12px !important;
  padding: 12px !important;
}

/* Keep map side dominant while the right column carries compact supporting info. */
@media (min-width: 901px){
  .monahinga-right-stack-card{
    width: 100% !important;
  }
}

@media (max-width: 900px){
  .monahinga-right-stack-card{
    margin-top: 14px !important;
  }
}


/* MONAHINGA_PAGE1_SHRINK_OPERATOR_CARD_2026_05_04
   Page 1 layout-only fix.
   Prevents the Operator Run Setup card from stretching far below its tip text.
   Does not touch species selector, buttons, map, BBox logic, backend, terrain, PAD-US, or Render config.
*/
.card:has(h3),
.panel:has(h3){
  align-self: start !important;
}

.card:has(h3:nth-child(1)),
.panel:has(h3:nth-child(1)){
  min-height: 0 !important;
}

.card:has(h3),
.panel:has(h3){
  height: auto !important;
  max-height: none !important;
}

section:has(h3),
div:has(> h3){
  align-self: start !important;
}

h3 + * {
  margin-top: 10px;
}

/* Narrower direct targeting: the card containing Operator Run Setup should end after its content. */
h3{
  scroll-margin-top: 12px;
}

@supports selector(:has(*)){
  div:has(> h3:first-child){
    min-height: 0 !important;
    height: auto !important;
  }

  div:has(> h3:first-child) p:last-child{
    margin-bottom: 0 !important;
  }
}


/* MONAHINGA_PAGE1_STOP_GRID_CARD_STRETCH_2026_05_04
   Layout-only fix: CSS Grid normally stretches cards to match the tallest card in the row.
   This lets Operator Run Setup end after its own content instead of matching the map height.
   Does not touch map logic, BBox logic, species selector, run buttons, backend, terrain, PAD-US, or Render config.
*/
.layout > .card{
  align-self:start !important;
}


/* MONAHINGA_PAGE1_MOVE_INFO_CARDS_RIGHT_2026_05_04
   Page 1 layout-only pass.
   Moves Status and How this launch works into the right column under Operator Run Setup.
   Compacts both cards so the map remains the dominant work area.
   Does not touch map logic, BBox logic, species selector, run buttons, backend, terrain, PAD-US, or Render config.
*/
.monahinga-right-info-stack{
  display:flex !important;
  flex-direction:column !important;
  gap:14px !important;
  margin-top:14px !important;
}

.monahinga-right-info-stack .card{
  width:100% !important;
  min-height:0 !important;
  height:auto !important;
  padding:16px !important;
  border-radius:18px !important;
}

.monahinga-right-info-stack h2,
.monahinga-right-info-stack h3{
  font-size:18px !important;
  line-height:1.15 !important;
  margin:0 0 10px 0 !important;
}

.monahinga-right-info-stack p,
.monahinga-right-info-stack div,
.monahinga-right-info-stack span{
  font-size:12px !important;
  line-height:1.33 !important;
}

.monahinga-right-info-stack pre,
.monahinga-right-info-stack code,
.monahinga-right-info-stack textarea{
  font-size:11px !important;
  line-height:1.28 !important;
  white-space:pre-wrap !important;
  word-break:break-word !important;
  max-height:115px !important;
  overflow:auto !important;
}

.monahinga-right-info-stack .disclaimer,
.monahinga-right-info-stack [class*="disclaimer"]{
  margin-top:10px !important;
  padding:10px 12px !important;
  font-size:11px !important;
  line-height:1.3 !important;
}

@media (max-width: 900px){
  .monahinga-right-info-stack{
    margin-top:14px !important;
  }
}


/* MONAHINGA_PAGE1_INFO_BLOCKS_RIGHT_CARD_2026_05_04
   Source layout fix: move selected-box hint, Status, and How this launch works into the right column.
   Keep them compact so they fit under Operator Run Setup beside the map.
   Does not touch map logic, BBox logic, species selector, run buttons, backend, terrain, PAD-US, or Render config.
*/
.monahinga-right-info-stack{
  display:flex;
  flex-direction:column;
  gap:10px;
  margin-top:14px;
}

.monahinga-right-info-stack .inline-warning{
  margin-top:0 !important;
  padding:10px 12px !important;
  font-size:12px !important;
  line-height:1.3 !important;
}

.mini-card{
  border:1px solid var(--line);
  background:rgba(255,255,255,.025);
  border-radius:16px;
  padding:12px;
  min-height:0 !important;
  height:auto !important;
}

.mini-card h2{
  font-size:16px !important;
  line-height:1.15 !important;
  margin:0 0 8px 0 !important;
}

.mini-card .helper,
.mini-card .helper *,
.mini-card .disclaimer,
.mini-card .disclaimer *{
  font-size:11px !important;
  line-height:1.28 !important;
}

.compact-status-card pre#status{
  min-height:70px !important;
  height:90px !important;
  max-height:90px !important;
  overflow:auto !important;
  font-size:11px !important;
  line-height:1.3 !important;
  padding:10px !important;
}

.compact-launch-card .disclaimer{
  margin-top:9px !important;
  padding:9px 10px !important;
}

@media (max-width:900px){
  .monahinga-right-info-stack{
    margin-top:12px;
  }
  .compact-status-card pre#status{
    height:76px !important;
    max-height:76px !important;
  }
}


/* MONAHINGA_PAGE1_TIGHTEN_SPACING_2026_05_04 */
/* Tighten spacing between:
   1) top MONAHINGA header and first card
   2) first card and map card
*/

.hero {
  margin-bottom: 10px !important;
}

.hero + .card {
  margin-top: 10px !important;
}

.card + .layout {
  margin-top: 10px !important;
}

/* fallback if class names differ */
h1 + .card {
  margin-top: 10px !important;
}


</style>
</head>
<body>
<div id="not_huntable_overlay" class="not-huntable-overlay" role="alertdialog" aria-modal="true" aria-labelledby="not_huntable_title">
  <div class="not-huntable-box">
    <h2 id="not_huntable_title">NOT HUNTABLE LAND</h2>
    <p>Please select another BBox over real natural/legal hunting ground.</p>
    <div class="small-copy">Monahinga blocks city blocks, suburbs, parking lots, roads, and non-hunting land so it does not generate a fake terrain read.</div>
    <button type="button" onclick="hideNotHuntableOverlay()">Return to BBox</button>
  </div>
</div>
<div class="shell theme-default" id="launch_shell">
  <div class="header-row">
    <div class="kicker">Monahinga™ · AI-powered terrain intelligence</div>
    <div class="header-links"><a href="/instructions">Instructions</a></div>
  </div>
  <div class="hero-band">
    <div class="hero-grid">
      <div class="hero-copy">
        <h1>Draw one U.S. box and get a truthful stand answer</h1>
        <div class="sub">
          This build is for the lower 48 only. Draw one box, keep the analysis inside that exact box, and launch a cleaner hunting run with legal-land messaging, hillshade terrain, and top-ranked stand options.
        </div>
        <!-- MONAHINGA_PAGE1_DIRECT_HERO_CLEANUP_2026_05_04: removed version chips and regional marketing story. -->
      </div>
      <!-- MONAHINGA_PAGE1_REMOVE_BRAND_CARD_2026_05_04: removed oversized launch brand card to simplify page 1. -->
    </div>
  </div>

  <div class="layout">
    <div class="card">
      <h2>Draw your hunting box <span style="font-size:14px; opacity:0.7;">(3D render may take 5–10 seconds)</span></h2>
      <div class="search-row">
        <input id="place_search" type="text" placeholder="Search address, town, road, camp, or landmark">
        <button class="secondary" type="button" onclick="searchPlace()">Find place</button>
        <button class="ghost" type="button" onclick="clearSearchResult()">Clear result</button>
      </div>
      <div class="search-meta" id="search_meta">Topo is now the default scouting layer. Search jumps you to a place first, then you draw the hunt box exactly where you want it.</div>
      <div class="map-toolbar">
        <button class="ghost" type="button" onclick="goDefaultView()">Monahinga™ view</button>
        <button class="ghost" type="button" onclick="clearDrawnBox()">Clear box</button>
        <button class="ghost" type="button" onclick="applyPastedBBox()">Use pasted coordinates</button>
        <span class="toolbar-note">Draw the rectangle, or paste min lon, min lat, max lon, max lat and let the map build the box for you.</span>
      </div>
      <div class="field full" style="margin-bottom:12px;">
        <label>Paste bbox coordinates</label>
        <textarea id="bbox_text" class="coord-input" placeholder="Example: -78.102209, 41.891092, -78.074925, 41.909235">__DEFAULT_BBOX_TEXT__</textarea>
        <small>Format: min lon, min lat, max lon, max lat. Commas, spaces, brackets, and line breaks are all fine.</small>
      </div>
      <div id="bbox-map"></div>
      <div class="bbox-readout">Current bbox: <code id="bbox_readout">not drawn yet</code></div>
    </div>

    <div class="card">
      <h2>Operator Run Setup</h2>
      <div class="grid">
        <div class="field">
          <label>Min Lon</label>
          <input id="min_lon" value="__DEFAULT_MIN_LON__">
        </div>
        <div class="field">
          <label>Min Lat</label>
          <input id="min_lat" value="__DEFAULT_MIN_LAT__">
        </div>
        <div class="field">
          <label>Max Lon</label>
          <input id="max_lon" value="__DEFAULT_MAX_LON__">
        </div>
        <div class="field">
          <label>Max Lat</label>
          <input id="max_lat" value="__DEFAULT_MAX_LAT__">
        </div>
        <div class="field">
          <label>Width</label>
          <input id="width" value="512">
        </div>
        <div class="field">
          <label>Height</label>
          <input id="height" value="512">
        </div>
        <div class="field">
          <label>Wind Direction</label>
          <input id="wind_direction" placeholder="Example: NW">
        </div>
        <div class="field">
          <label>Mode</label>
          <input id="mode" value="hunter" readonly>
        </div>
        <div class="field">
          <label>Target Species (optional)</label>
<select id="target_species">
  <option value="default">General Terrain Read</option>

  <!-- Core deer -->
  <option value="whitetail">Whitetail Deer</option>
  <option value="mule_deer">Mule Deer</option>

  <!-- Western big game -->
  <option value="elk">Elk</option>
  <option value="moose">Moose</option>
  <option value="bighorn">Bighorn Sheep</option>
  <option value="pronghorn">Pronghorn</option>

  <!-- Mid / universal -->
  <option value="black_bear">Black Bear</option>
  <option value="turkey">Wild Turkey</option>

  <!-- Opportunistic / niche -->
  <option value="hog">Feral Hog</option>
  <option value="coyote">Coyote</option>
  <option value="javelina">Javelina</option>
</select>
        </div>

        <div class="field full">
          <label>Operator Notes</label>
          <textarea id="notes" placeholder="Examples: trail cam near creek, suspected bedding on east shoulder, keep access low pressure"></textarea>
        </div>
      </div>

      <div class="buttons">
        <button class="primary" type="button" onclick="runDefault()">Run default Monahinga™ box</button>
        <button class="secondary" type="button" onclick="runCustom()">Run selected box</button>
        <button class="ghost" type="button" onclick="applyDefault()">Reset to default box</button>
        <button class="ghost" type="button" onclick="window.location='/instructions'">Open instructions</button>
      </div>
      <div style="margin-top:12px"><small>Tip: keep width and height at 512 for public web speed; use 768 only for slower high-detail testing. Wind is optional. Mode stays locked to hunter so the output stays focused.</small></div>

      <div class="monahinga-right-info-stack" data-monahinga-created-by="MONAHINGA_PAGE1_INFO_BLOCKS_RIGHT_CARD_2026_05_04">
        <div id="bbox_hint" class="inline-warning info">Draw a box fully inside the lower 48, or paste one exact bbox and apply it. That keeps the legal check and stand ranking truthful.</div>

        <div class="mini-card compact-status-card">
          <h2>Status</h2>
          <pre id="status">Ready.</pre>
        </div>

        <div class="mini-card compact-launch-card">
          <h2>How this launch works</h2>
          <div class="helper">
            <strong>U.S.-only guardrail:</strong> the run only accepts boxes fully inside the lower 48.<br>
            <strong>Legal truth:</strong> PAD-US is used as a land-status signal inside the selected box.<br>
            <strong>Truthful sync:</strong> draw rectangle → bbox fields update → launch uses those exact values.<br>
            <strong>Manual fallback:</strong> typing into the fields or pasting one bbox redraws the rectangle so the map and form stay aligned.
          </div>
          <div class="disclaimer">
            <strong>Field-use disclaimer:</strong> Monahinga™ is an AI-assisted terrain intelligence and decision-support tool. It is not legal, safety, hunting, land access, firearm, or wildlife-regulation advice. Always verify land access, seasons, tags, weapon rules, safety conditions, and local regulations before entering or hunting any area.
          </div>
        </div>
      </div>
    </div>
  </div>

</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js" crossorigin=""></script>
<script>
const defaults = __DEFAULTS_JSON__;
const defaultBounds = [
  [defaults.min_lat, defaults.min_lon],
  [defaults.max_lat, defaults.max_lon]
];
const formIds = ['min_lon', 'min_lat', 'max_lon', 'max_lat'];
let suppressFieldSync = false;
let activeRect = null;
let searchMarker = null;

const map = L.map('bbox-map', { zoomControl:true, worldCopyJump:false });
const drawLayer = new L.FeatureGroup().addTo(map);

const street = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
});
const topo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
  maxZoom: 17,
  attribution: '&copy; OpenTopoMap contributors'
});
const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  maxZoom: 19,
  attribution: 'Tiles &copy; Esri'
});

topo.addTo(map);
L.control.layers(
  { 'Topo': topo, 'Street map': street, 'Satellite': satellite },
  {},
  { position:'topright' }
).addTo(map);

const drawControl = new L.Control.Draw({
  position: 'topleft',
  draw: {
    polygon: false,
    polyline: false,
    circle: false,
    circlemarker: false,
    marker: false,
    rectangle: {
      shapeOptions: {
        color: '#a8f183',
        weight: 2,
        fillOpacity: 0.08
      }
    }
  },
  edit: {
    featureGroup: drawLayer,
    edit: true,
    remove: true
  }
});
map.addControl(drawControl);

function setStatus(message) {
  document.getElementById('status').textContent = message;
}

function showNotHuntableOverlay() {
  const overlay = document.getElementById('not_huntable_overlay');
  if (overlay) overlay.classList.add('visible');
}

function hideNotHuntableOverlay() {
  const overlay = document.getElementById('not_huntable_overlay');
  if (overlay) overlay.classList.remove('visible');
  const mapBox = document.getElementById('bbox-map');
  if (mapBox && mapBox.scrollIntoView) {
    mapBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

function hasUsedFreeTerrainView() {
  return window.localStorage && localStorage.getItem('monahinga_free_view_used') === 'yes';
}

function markFreeTerrainViewUsed() {
  if (window.localStorage) localStorage.setItem('monahinga_free_view_used', 'yes');
}

function explainPaidViewsGate() {
  setStatus('Paid access is paused in this local polish build. Keep testing the core terrain flow first.');
}


function deriveRegionIdentity(b) {
  const centerLon = (Number(b.minLon) + Number(b.maxLon)) / 2;
  const centerLat = (Number(b.minLat) + Number(b.maxLat)) / 2;
  if (!Number.isFinite(centerLon) || !Number.isFinite(centerLat)) {
    return { key:'default', label:'U.S. hunting terrain', animals:'Regional game', mood:'Terrain mood · scouting country', story:'Draw a lower-48 box to see a region-aware hunt identity.' };
  }
  if (centerLon < -108 && centerLat > 36) {
    return { key:'mountain', label:'Mountain big-game terrain', animals:'Elk · Mule deer country', mood:'Terrain mood · alpine shadow and ridge light', story:'This box reads like western mountain country: bigger relief, cooler tones, and hunt setups that feel more exposed, wind-sensitive, and terrain-driven.' };
  }
  if (centerLon > -90 && centerLat < 37) {
    return { key:'southwoods', label:'Southern timber terrain', animals:'Whitetail · Turkey country', mood:'Terrain mood · humid timber and creek travel', story:'This box reads like southern timber country: thicker cover, warmer understory tones, and setup value that often comes from quiet access and shaded movement.' };
  }
  if (centerLon > -104 && centerLon < -92 && centerLat > 35 && centerLat < 47) {
    return { key:'plains', label:'Plains edge terrain', animals:'Whitetail · Mule deer country', mood:'Terrain mood · open edge and shelter breaks', story:'This box reads like plains-edge hunting ground: cleaner horizon lines, sharper exposure decisions, and travel shaped by cover islands and sheltered breaks.' };
  }
  return { key:'appalachian', label:'Appalachian whitetail terrain', animals:'Whitetail · Turkey country', mood:'Terrain mood · shaded timber folds', story:'This box reads like Appalachian whitetail country: broken hills, shaded side-slopes, and decision points that reward disciplined access and terrain-aware setups.' };
}
function applyRegionIdentityFromCurrent() {
  const bbox = currentBBox();
  const identity = deriveRegionIdentity({
    minLon:bbox.minLon, minLat:bbox.minLat, maxLon:bbox.maxLon, maxLat:bbox.maxLat
  });
  const shell = document.getElementById('launch_shell');
  if (shell) {
    shell.classList.remove('theme-default','theme-appalachian','theme-mountain','theme-plains','theme-southwoods');
    shell.classList.add('theme-' + identity.key);
  }
  const regionBadge = document.getElementById('region_badge');
  const gameBadge = document.getElementById('game_badge');
  const regionStory = document.getElementById('region_story');
  const heroMood = document.getElementById('hero_mood_badge');
  const heroSpecies = document.getElementById('hero_species_badge');
  if (regionBadge) regionBadge.textContent = identity.label;
  if (gameBadge) gameBadge.textContent = identity.animals;
  if (regionStory) regionStory.innerHTML = '<span class="region-emphasis">' + identity.label + '</span>: ' + identity.story;
  if (heroMood) heroMood.textContent = identity.mood;
  if (heroSpecies) heroSpecies.textContent = 'Primary species · ' + identity.animals;
  const launchMethods = document.getElementById('launch_methods_badge');
  const wildlifeStrip = document.getElementById('launch_wildlife_strip');
  const wildlifeCards = identity.key === 'mountain'
    ? [['Elk','Benches, saddles, timber edge, and escape cover.'], ['Mule Deer','Broken slopes and open-to-cover transitions.'], ['Black Bear','Food edges, shaded drainages, and thick cover.']]
    : identity.key === 'plains'
      ? [['White-tailed Deer','Cover islands and creek breaks.'], ['Mule Deer','Draws, breaks, and open-country cover.'], ['Wild Turkey','Roost cover and field-edge timing.']]
      : identity.key === 'southwoods'
        ? [['White-tailed Deer','Bedding cover, shaded edge, quiet access.'], ['Wild Turkey','Roost-to-feed movement and open timber.'], ['Feral Hog','Water, cover, and disturbed ground where present.']]
        : [['White-tailed Deer','Side-hill benches and bedding edges.'], ['Wild Turkey','Roost-to-feed movement and ridge transitions.'], ['Black Bear','Thick cover, food, and shaded drainages.']];
  if (launchMethods) launchMethods.textContent = identity.key === 'southwoods' ? 'Common context · rifle / shotgun / muzzleloader / archery where legal' : 'Common context · centerfire rifle / .30-06-class rifle / muzzleloader / archery where legal';
  if (wildlifeStrip) {
    wildlifeStrip.innerHTML = wildlifeCards.map(function(item) {
      return '<div class="launch-wildlife-card"><strong>' + item[0] + '</strong><span>' + item[1] + '</span></div>';
    }).join('');
  }
// --- Auto-suggest species based on region ---
const speciesSelect = document.getElementById('target_species');
if (speciesSelect) {
  // Only auto-set if user has not manually chosen a species
  if (!speciesSelect.dataset.userSelected) {
    if (identity.key === 'mountain') {
      speciesSelect.value = 'elk';
    } else if (identity.key === 'plains') {
      speciesSelect.value = 'mule_deer';
    } else if (identity.key === 'southwoods') {
      speciesSelect.value = 'hog';
    } else {
      speciesSelect.value = 'whitetail';
    }
  }
}
}

function toFixedCoord(value) {
  return Number(value).toFixed(6);
}

function getFormNumber(id) {
  return Number(document.getElementById(id).value);
}

function currentBBox() {
  const minLon = getFormNumber('min_lon');
  const minLat = getFormNumber('min_lat');
  const maxLon = getFormNumber('max_lon');
  const maxLat = getFormNumber('max_lat');
  return { minLon, minLat, maxLon, maxLat };
}

function bboxLooksUsa(b) {
  return (
    b.minLon >= -125 && b.maxLon <= -66 &&
    b.minLat >= 24 && b.maxLat <= 50
  );
}

function pointLooksLower48(lat, lon) {
  return Number.isFinite(lat) && Number.isFinite(lon) &&
    lon >= -125 && lon <= -66 &&
    lat >= 24 && lat <= 50;
}

function updateBboxReadout() {
  const b = currentBBox();
  const readout = `${toFixedCoord(b.minLon)}, ${toFixedCoord(b.minLat)}, ${toFixedCoord(b.maxLon)}, ${toFixedCoord(b.maxLat)}`;
  document.getElementById('bbox_readout').textContent = readout;
  updateBBoxTextFromCurrent();
  applyRegionIdentityFromCurrent();
  const hint = document.getElementById('bbox_hint');
  if (!isFinite(b.minLon) || !isFinite(b.minLat) || !isFinite(b.maxLon) || !isFinite(b.maxLat)) {
    hint.className = 'inline-warning warn';
    hint.textContent = 'BBox values are incomplete or invalid.';
    return;
  }
  if (bboxLooksUsa(b)) {
    hint.className = 'inline-warning info';
    hint.textContent = 'Selected box appears to be inside the lower 48 hunting footprint. Legal-land checks can participate in the run.';
  } else {
    hint.className = 'inline-warning warn';
    hint.textContent = 'Selected box appears outside the lower 48 hunting footprint. This build should be kept inside the contiguous U.S. before you run it.';
  }
}


function updateBBoxTextFromCurrent() {
  const b = currentBBox();
  if (!Object.values(b).every(Number.isFinite)) return;
  document.getElementById('bbox_text').value = `${toFixedCoord(b.minLon)}, ${toFixedCoord(b.minLat)}, ${toFixedCoord(b.maxLon)}, ${toFixedCoord(b.maxLat)}`;
}

function parseBBoxText(raw) {
  const cleaned = String(raw || '').trim();
  if (!cleaned) throw new Error('Paste four bbox numbers first: min lon, min lat, max lon, max lat.');
  const matches = cleaned.match(/-?\d+(?:\.\d+)?/g) || [];
  if (matches.length !== 4) {
    throw new Error('BBox paste expects exactly four numbers: min lon, min lat, max lon, max lat.');
  }
  const [lonA, latA, lonB, latB] = matches.map(Number);
  if (![lonA, latA, lonB, latB].every(Number.isFinite)) {
    throw new Error('BBox paste contains invalid numbers.');
  }
  return {
    minLon: Math.min(lonA, lonB),
    minLat: Math.min(latA, latB),
    maxLon: Math.max(lonA, lonB),
    maxLat: Math.max(latA, latB)
  };
}

function applyPastedBBox() {
  try {
    const parsed = parseBBoxText(document.getElementById('bbox_text').value);
    suppressFieldSync = true;
    document.getElementById('min_lon').value = toFixedCoord(parsed.minLon);
    document.getElementById('min_lat').value = toFixedCoord(parsed.minLat);
    document.getElementById('max_lon').value = toFixedCoord(parsed.maxLon);
    document.getElementById('max_lat').value = toFixedCoord(parsed.maxLat);
    suppressFieldSync = false;
    syncRectangleFromInputs(true);
    applyRegionIdentityFromCurrent();
    setStatus('Pasted bbox applied. The map rectangle and run fields now match those exact coordinates.');
  } catch (err) {
    const message = String(err && err.message ? err.message : err);
    const lower = message.toLowerCase();
    const blockedLand =
      lower.includes('urban') ||
      lower.includes('huntable') ||
      lower.includes('natural/legal') ||
      lower.includes('city') ||
      lower.includes('suburb') ||
      lower.includes('parking') ||
      lower.includes('400') ||
      lower.includes('bad request');

    if (blockedLand) {
      showNotHuntableOverlay();
      setStatus(
        'NOT HUNTABLE LAND\n\n' +
        'Please select another BBox over real natural/legal hunting ground.\n\n' +
        message
      );
    } else {
      setStatus('FAILED\n\n' + message);
    }
  }
}


function setSearchMeta(message) {
  const meta = document.getElementById('search_meta');
  if (meta) meta.textContent = message;
}

function clearSearchResult() {
  if (searchMarker) {
    map.removeLayer(searchMarker);
    searchMarker = null;
  }
  setSearchMeta('Topo is now the default scouting layer. Search jumps you to a place first, then you draw the hunt box exactly where you want it.');
  const input = document.getElementById('place_search');
  if (input) input.value = '';
}

async function searchPlace() {
  const input = document.getElementById('place_search');
  const query = String(input && input.value || '').trim();
  if (!query) {
    setStatus('Type an address, town, road, or landmark first.');
    return;
  }
  setStatus('Searching for place... Please wait.');
  setSearchMeta('Searching for "' + query + '"...');
  try {
    const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=us&q=' + encodeURIComponent(query);
    const res = await fetch(url, {
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error('Place search failed.');
    const results = await res.json();
    if (!Array.isArray(results) || !results.length) throw new Error('No matching place found.');
    const hit = results[0];
    const lat = Number(hit.lat);
    const lon = Number(hit.lon);
    if (!pointLooksLower48(lat, lon)) throw new Error('Place was found, but it falls outside the lower-48 hunting footprint.');
    if (searchMarker) map.removeLayer(searchMarker);
    searchMarker = L.marker([lat, lon]).addTo(map);
    const name = String(hit.display_name || query);
    searchMarker.bindPopup(name).openPopup();
    if (Array.isArray(hit.boundingbox) && hit.boundingbox.length === 4) {
      const south = Number(hit.boundingbox[0]), north = Number(hit.boundingbox[1]);
      const west = Number(hit.boundingbox[2]), east = Number(hit.boundingbox[3]);
      if ([south, north, west, east].every(Number.isFinite)) {
        map.fitBounds([[south, west], [north, east]], { padding:[30,30] });
      } else {
        map.setView([lat, lon], 14);
      }
    } else {
      map.setView([lat, lon], 14);
    }
    setSearchMeta('Found: ' + name + '. Draw your bbox around the terrain you want to hunt.');
    setStatus('Place found. The map jumped to the searched location; now draw the hunt box.');
  } catch (err) {
    setSearchMeta('Search failed. You can still paste coordinates or draw the box manually.');
    setStatus('FAILED\n\n' + String(err && err.message ? err.message : err));
  }
}

function clearDrawnBox() {
  drawLayer.clearLayers();
  activeRect = null;
  document.getElementById('bbox_readout').textContent = 'not drawn yet';
  document.getElementById('bbox_hint').className = 'inline-warning info';
  document.getElementById('bbox_hint').textContent = 'Draw a box fully inside the lower 48. Form values stay until you reset or redraw.';
  applyRegionIdentityFromCurrent();
  setStatus('Map rectangle cleared. Form values remain as-is until you reset or redraw.');
}

function applyBBoxToForm(bounds) {
  const sw = bounds.getSouthWest();
  const ne = bounds.getNorthEast();
  suppressFieldSync = true;
  document.getElementById('min_lon').value = toFixedCoord(sw.lng);
  document.getElementById('min_lat').value = toFixedCoord(sw.lat);
  document.getElementById('max_lon').value = toFixedCoord(ne.lng);
  document.getElementById('max_lat').value = toFixedCoord(ne.lat);
  suppressFieldSync = false;
  updateBboxReadout();
}

function drawRectangleFromBounds(bounds, fit=true) {
  drawLayer.clearLayers();
  activeRect = L.rectangle(bounds, { color:'#a8f183', weight:2, fillOpacity:0.08 });
  drawLayer.addLayer(activeRect);
  applyBBoxToForm(activeRect.getBounds());
  updateBBoxTextFromCurrent();
  if (fit) map.fitBounds(activeRect.getBounds(), { padding:[20,20] });
}

function normalizeBoundsFromInputs() {
  const values = currentBBox();
  if (!Object.values(values).every(Number.isFinite)) return null;
  const minLon = Math.max(-180, Math.min(values.minLon, values.maxLon));
  const maxLon = Math.min(180, Math.max(values.minLon, values.maxLon));
  const minLat = Math.max(-90, Math.min(values.minLat, values.maxLat));
  const maxLat = Math.min(90, Math.max(values.minLat, values.maxLat));
  if (maxLon <= minLon || maxLat <= minLat) return null;
  return L.latLngBounds([minLat, minLon], [maxLat, maxLon]);
}

function syncRectangleFromInputs(fit=false) {
  if (suppressFieldSync) return;
  const bounds = normalizeBoundsFromInputs();
  updateBboxReadout();
  if (!bounds) return;
  drawRectangleFromBounds(bounds, fit);
}

function goDefaultView() {
  map.fitBounds(defaultBounds, { padding:[20,20] });
  setStatus('Returned to the public Monahinga™ demo box inside the lower 48.');
}

function applyDefault() {
  for (const [k, v] of Object.entries(defaults)) {
    const el = document.getElementById(k);
    if (el) el.value = v;
  }
  drawRectangleFromBounds(defaultBounds, true);
  updateBBoxTextFromCurrent();
  applyRegionIdentityFromCurrent();
  setStatus('Reset to the public default lower-48 demo box and run settings.');
}


const bboxTextEl = document.getElementById('bbox_text');
if (bboxTextEl) {
  bboxTextEl.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      applyPastedBBox();
    }
  });
  bboxTextEl.addEventListener('paste', () => {
    window.setTimeout(() => {
      try {
        const parsed = parseBBoxText(bboxTextEl.value);
        if (parsed) applyPastedBBox();
      } catch (err) {
        // Ignore partial paste states and let manual apply remain available.
      }
    }, 0);
  });
  bboxTextEl.addEventListener('blur', () => {
    try {
      const parsed = parseBBoxText(bboxTextEl.value);
      if (parsed) applyPastedBBox();
    } catch (err) {
      // Ignore invalid or partial text on blur.
    }
  });
}

function payloadFromForm() {
  const bounds = normalizeBoundsFromInputs();
  if (!bounds) throw new Error('Please enter or draw a valid bbox before running.');
  applyBBoxToForm(bounds);
  return {
    min_lon: Number(document.getElementById('min_lon').value),
    min_lat: Number(document.getElementById('min_lat').value),
    max_lon: Number(document.getElementById('max_lon').value),
    max_lat: Number(document.getElementById('max_lat').value),
    width: Number(document.getElementById('width').value),
    height: Number(document.getElementById('height').value),
    wind_direction: String(document.getElementById('wind_direction').value || '').trim(),
    notes: String(document.getElementById('notes').value || '').trim(),
    mode: String(document.getElementById('mode').value || 'hunter').trim(),
    selected_species: document.getElementById('target_species')?.value || 'default'
  };
}

function isNotHuntableRunError(message, statusCode) {
  const lower = String(message || '').toLowerCase();
  return (
    Number(statusCode) === 400 && (
      lower.includes('urban') ||
      lower.includes('natural/legal') ||
      lower.includes('downtown') ||
      lower.includes('suburb') ||
      lower.includes('parking') ||
      lower.includes('city block') ||
      lower.includes('non-hunting') ||
      lower.includes('not huntable') ||
      lower.includes('huntable')
    )
  );
}

async function readRunResponse(res) {
  try {
    return await res.json();
  } catch (err) {
    return { detail: 'Server returned an unreadable response.' };
  }
}

async function runCustom() {
// Server-side gate now controls access
// Frontend gate disabled intentionally
  let progressTimer = null;
  try {
    const payload = payloadFromForm();
    const bbox = currentBBox();
    if (!bboxLooksUsa(bbox)) {
      setStatus('FAILED\n\nMove the hunt box back inside the lower-48 hunting footprint before running.');
      return;
    }
    setStatus('Reading terrain, elevation, wind, and cover...\nBuilding your 3D hunting intelligence (5–10 seconds)');

    progressTimer = window.setTimeout(() => {
      setStatus('Analyzing terrain structure and movement patterns...\nSelecting optimal stand locations...');
    }, 1800);

    const res = await fetch('/run-terrain-truth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await readRunResponse(res);

    if (!res.ok) {
      const detail = data && data.detail ? String(data.detail) : JSON.stringify(data);
      if (isNotHuntableRunError(detail, res.status)) {
        showNotHuntableOverlay();
        setStatus(
          'NOT HUNTABLE LAND\n\n' +
          'Please select another BBox over real natural/legal hunting ground.\n\n' +
          detail
        );
        return;
      }
      throw new Error(detail);
    }

    setStatus(
      'PASS - first free terrain view used.\n\n' +
      'Run folder: ' + data.run_folder + '\n' +
      'Decision contract: ' + data.decision_contract + '\n' +
      'Opening command surface...'
    );
    window.location = data.command_surface_url;
  } catch (err) {
    const message = String(err && err.message ? err.message : err);
    if (isNotHuntableRunError(message, 400)) {
      showNotHuntableOverlay();
      setStatus(
        'NOT HUNTABLE LAND\n\n' +
        'Please select another BBox over real natural/legal hunting ground.\n\n' +
        message
      );
      return;
    }
    setStatus('FAILED\n\n' + message);
  } finally {
    if (progressTimer !== null) {
      window.clearTimeout(progressTimer);
    }
  }
}

async function runDefault() {
  applyDefault();
  await runCustom();
}

map.on(L.Draw.Event.CREATED, function (event) {
  drawRectangleFromBounds(event.layer.getBounds(), true);
  setStatus('Rectangle captured. The form fields now match the selected hunting box exactly.');
});

map.on(L.Draw.Event.EDITED, function () {
  const layer = drawLayer.getLayers()[0];
  if (!layer) return;
  drawRectangleFromBounds(layer.getBounds(), false);
  setStatus('Rectangle edited. The form fields were updated.');
});

map.on(L.Draw.Event.DELETED, function () {
  activeRect = null;
  document.getElementById('bbox_readout').textContent = 'not drawn yet';
  setStatus('Rectangle deleted. Form values remain until you reset, paste a bbox, or type a new lower-48 box.');
});

for (const id of formIds) {
  document.getElementById(id).addEventListener('change', () => syncRectangleFromInputs(false));
  document.getElementById(id).addEventListener('blur', () => syncRectangleFromInputs(false));
}

const placeSearchEl = document.getElementById('place_search');
if (placeSearchEl) {
  placeSearchEl.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      searchPlace();
    }
  });
}

applyDefault();
goDefaultView();
const speciesSelect = document.getElementById('target_species');
if (speciesSelect) {
  speciesSelect.addEventListener('change', () => {
    speciesSelect.dataset.userSelected = "true";
  });
}
</script>

<script>
(function(){
  const marker = "MONAHINGA_PAGE1_RESTORE_HIDE_OPERATOR_FIELDS_2026_05_04";
  const hiddenLabels = new Set([
    'min lon',
    'min lat',
    'max lon',
    'max lat',
    'width',
    'height',
    'wind direction',
    'mode'
  ]);

  function hideRedundantOperatorFields(){
    const labels = Array.from(document.querySelectorAll('label'));
    labels.forEach((label) => {
      const labelText = (label.textContent || '').trim().replace(/\s+/g, ' ').toLowerCase();
      if (!hiddenLabels.has(labelText)) return;

      let node = label.closest('.field, .form-field, .input-field, .control, .form-control, .input-group, div');
      if (!node) node = label.parentElement;
      if (!node) return;

      node.classList.add('monahinga-hidden-operator-field');
      node.setAttribute('data-monahinga-hidden-by', marker);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hideRedundantOperatorFields);
  } else {
    hideRedundantOperatorFields();
  }
  window.addEventListener('load', hideRedundantOperatorFields);
})();
</script>


<script>
(function(){
  const marker = "MONAHINGA_PAGE1_REMOVE_DUPLICATE_INSTRUCTION_NOTES_2026_05_04";

  function closestField(el){
    return el.closest('.field, .form-field, .input-field, .control, .form-control, .input-group, label, div') || el;
  }

  function cleanPageOne(){
    // Keep the first/top Instructions control; hide later duplicate Open instructions controls.
    const instructionControls = Array.from(document.querySelectorAll('button, a, [role="button"]'))
      .filter(el => {
        const t = (el.textContent || '').trim().replace(/\s+/g, ' ').toLowerCase();
        return t === 'instructions' || t === 'open instructions';
      });

    if (instructionControls.length > 0) {
      instructionControls[0].classList.add('monahinga-top-instructions-strong');
    }

    instructionControls.slice(1).forEach(el => {
      el.classList.add('monahinga-page1-hidden-control');
      el.setAttribute('aria-hidden', 'true');
      el.setAttribute('data-monahinga-hidden-by', marker);
    });

    // Hide only the Operator Notes label + textarea field. Do not hide parent cards.
    const labels = Array.from(document.querySelectorAll('label'));
    labels.forEach(label => {
      const t = (label.textContent || '').trim().replace(/\s+/g, ' ').toLowerCase();
      if (t !== 'operator notes') return;

      const field = closestField(label);
      field.classList.add('monahinga-page1-hidden-control');
      field.setAttribute('aria-hidden', 'true');
      field.setAttribute('data-monahinga-hidden-by', marker);

      // If the textarea is not inside the same field wrapper, hide the closest following textarea too.
      let next = field.nextElementSibling;
      for (let i = 0; next && i < 3; i++, next = next.nextElementSibling) {
        if (next.matches && next.matches('textarea, .field, .form-field, .input-field, .control, .form-control, .input-group')) {
          const textArea = next.matches('textarea') ? next : next.querySelector('textarea');
          if (textArea) {
            next.classList.add('monahinga-page1-hidden-control');
            next.setAttribute('aria-hidden', 'true');
            next.setAttribute('data-monahinga-hidden-by', marker);
            break;
          }
        }
      }
    });

    // Extra narrow fallback: hide standalone textarea with the exact operator-notes placeholder.
    Array.from(document.querySelectorAll('textarea')).forEach(area => {
      const p = (area.getAttribute('placeholder') || '').toLowerCase();
      if (p.includes('trail cam') && p.includes('access low pressure')) {
        const field = closestField(area);
        field.classList.add('monahinga-page1-hidden-control');
        field.setAttribute('aria-hidden', 'true');
        field.setAttribute('data-monahinga-hidden-by', marker);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', cleanPageOne);
  } else {
    cleanPageOne();
  }
  window.addEventListener('load', cleanPageOne);
})();
</script>


<script>
(function(){
  const marker = "MONAHINGA_PAGE1_RIGHT_COLUMN_STACK_2026_05_04";

  function findCardByHeading(textNeedle){
    const headings = Array.from(document.querySelectorAll('h2, h3, h4'));
    const heading = headings.find(h => (h.textContent || '').trim().toLowerCase() === textNeedle);
    if (!heading) return null;
    return heading.closest('.card, .panel, section, div') || heading.parentElement;
  }

  function findOperatorCard(){
    const headings = Array.from(document.querySelectorAll('h2, h3, h4'));
    const heading = headings.find(h => (h.textContent || '').trim().toLowerCase() === 'operator run setup');
    if (!heading) return null;
    return heading.closest('.card, .panel, section, div') || heading.parentElement;
  }

  function moveCards(){
    const operatorCard = findOperatorCard();
    if (!operatorCard) return;

    const cardsToMove = [
      findCardByHeading('how this launch works'),
      findCardByHeading('status')
    ].filter(Boolean);

    cardsToMove.forEach(card => {
      if (card === operatorCard) return;
      if (card.getAttribute('data-monahinga-moved-by') === marker) return;

      card.classList.add('monahinga-right-stack-card');
      card.setAttribute('data-monahinga-moved-by', marker);
      operatorCard.insertAdjacentElement('afterend', card);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', moveCards);
  } else {
    moveCards();
  }
  window.addEventListener('load', moveCards);
})();
</script>


<script>
(function(){
  const marker = "MONAHINGA_PAGE1_MOVE_INFO_CARDS_RIGHT_2026_05_04";

  function cardForHeading(exactText){
    const heading = Array.from(document.querySelectorAll('h1,h2,h3,h4')).find(h =>
      (h.textContent || '').trim().toLowerCase() === exactText
    );
    if (!heading) return null;
    return heading.closest('.card, section, .panel, div') || heading.parentElement;
  }

  function moveInfoCards(){
    const operator = cardForHeading('operator run setup');
    const status = cardForHeading('status');
    const how = cardForHeading('how this launch works');

    if (!operator || !status || !how) return;

    let stack = operator.parentElement.querySelector('.monahinga-right-info-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'monahinga-right-info-stack';
      stack.setAttribute('data-monahinga-created-by', marker);
      operator.insertAdjacentElement('afterend', stack);
    }

    [status, how].forEach(card => {
      if (!card || card === operator || card.parentElement === stack) return;
      card.setAttribute('data-monahinga-moved-by', marker);
      stack.appendChild(card);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', moveInfoCards);
  } else {
    moveInfoCards();
  }
  window.addEventListener('load', moveInfoCards);
})();
</script>

</body>
</html>'''


def render_home_page(default_bbox: BBox) -> str:
    defaults = {
        **default_bbox.to_form_defaults(),
        "width": 512,
        "height": 512,
        "wind_direction": "",
        "notes": "",
        "mode": "hunter",
    }
    return (
        HOME_PAGE_TEMPLATE
        .replace('__DEFAULT_MIN_LON__', str(default_bbox.min_lon))
        .replace('__DEFAULT_MIN_LAT__', str(default_bbox.min_lat))
        .replace('__DEFAULT_MAX_LON__', str(default_bbox.max_lon))
        .replace('__DEFAULT_MAX_LAT__', str(default_bbox.max_lat))
        .replace('__DEFAULT_BBOX_TEXT__', f"{default_bbox.min_lon}, {default_bbox.min_lat}, {default_bbox.max_lon}, {default_bbox.max_lat}")
        .replace('__DEFAULTS_JSON__', json.dumps(defaults))
    )
