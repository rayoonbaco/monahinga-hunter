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


.inline-land-layers{
  display:flex;
  align-items:center;
  flex-wrap:wrap;
  gap:10px;
  margin:10px 0 12px;
  padding:9px 11px;
  border-radius:14px;
  border:1px solid rgba(255,255,255,.12);
  background:rgba(10,16,22,.72);
  color:#dce8e5;
  font-size:12px;
  line-height:1.3;
}
.inline-land-layers strong{
  font-size:11px;
  letter-spacing:.13em;
  text-transform:uppercase;
  color:#eef7f2;
  margin-right:2px;
}
.inline-land-layers label{
  display:flex;
  align-items:center;
  gap:5px;
  font-weight:800;
  cursor:pointer;
  white-space:nowrap;
}
.inline-land-layers input{
  accent-color:#a8f183;
}

.inline-land-layers button{
  border:1px solid rgba(168,241,131,.28);
  background:rgba(168,241,131,.10);
  color:#eaffd6;
  border-radius:10px;
  padding:5px 9px;
  font-size:11px;
  font-weight:900;
  cursor:pointer;
}
.inline-land-layers button:hover{
  background:rgba(168,241,131,.18);
}
.inline-land-layers span{
  color:#9fb0bc;
  font-size:11px;
  flex-basis:100%;
}

.inline-land-layers .layer-pending{
  flex-basis:auto;
  font-size:10px;
  color:#ffd98a;
  margin-left:2px;
}

.inline-land-layers .parcel-file-label{
  border:1px solid rgba(255,184,77,.28);
  background:rgba(255,184,77,.08);
  border-radius:10px;
  padding:5px 9px;
  color:#ffe0ad;
}
.inline-land-layers .parcel-file-label input{
  display:none;
}

.parcel-help-note{
  margin-top:8px;
  font-size:11px;
  line-height:1.4;
  color:#cdbd95;
  opacity:.92;
}

/* MONAHINGA_WILDLIFE_IDENTITY_POLISH_V1_2026_05_10: compact selected-species card on launch page. */
.species-identity-card{
  margin-top:8px;
  padding:9px 10px;
  border-radius:14px;
  border:1px solid rgba(174,241,134,.24);
  background:linear-gradient(135deg, rgba(20,44,29,.72), rgba(7,15,22,.84));
  display:flex;
  gap:10px;
  align-items:flex-start;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04);
}
.species-identity-icon{
  flex:0 0 38px;
  height:38px;
  border-radius:13px;
  display:grid;
  place-items:center;
  font-size:24px;
  background:rgba(255,209,102,.12);
  border:1px solid rgba(255,209,102,.18);
}
.species-identity-copy{min-width:0;}
.species-identity-copy strong{
  display:block;
  font-size:13px;
  color:#fff4dc;
  line-height:1.1;
}
.species-identity-copy span{
  display:block;
  margin-top:4px;
  font-size:11px;
  line-height:1.35;
  color:#cbd8dc;
}
.species-identity-copy em{
  display:block;
  margin-top:5px;
  font-style:normal;
  font-size:10px;
  line-height:1.35;
  color:#f5d38a;
}

/* MONAHINGA_PAGE1_PARCEL_SOURCE_STATUS_V2_2026_05_06 */
.parcel-source-status{
  flex-basis:100%;
  margin-top:8px;
  padding:8px 10px;
  border-radius:12px;
  border:1px solid rgba(255,255,255,.16);
  background:rgba(5,9,12,.72);
  color:#e4edf0;
  font-size:11px;
  line-height:1.35;
  font-weight:850;
  letter-spacing:.02em;
}
.parcel-source-status strong{
  color:#ffe29a;
}
.parcel-source-status.demo{
  border-color:rgba(255,184,77,.62);
  background:rgba(72,42,7,.50);
}
.parcel-source-status.imported{
  border-color:rgba(126,240,151,.55);
  background:rgba(11,55,28,.44);
}
.parcel-source-status.provider{
  border-color:rgba(131,201,255,.62);
  background:rgba(9,36,58,.48);
}
.parcel-source-status.none{
  color:#aebbc4;
}
.parcel-source-summary{
  margin-top:7px;
  padding:7px 8px;
  border:1px solid rgba(155,255,179,.25);
  border-radius:9px;
  background:rgba(17,44,34,.35);
  color:#dfffe9;
  font-size:10px;
  line-height:1.35;
}
.parcel-source-summary strong{
  display:block;
  color:#9dffb3;
  margin-bottom:3px;
  letter-spacing:.04em;
  text-transform:uppercase;
}
.parcel-source-summary div{
  display:flex;
  gap:8px;
  justify-content:space-between;
  border-top:1px solid rgba(255,255,255,.08);
  padding-top:3px;
  margin-top:3px;
}
.parcel-source-summary span{
  color:#aebbc4;
  flex:0 0 auto;
}
.parcel-source-summary b{
  color:#effff4;
  text-align:right;
  font-weight:850;
  overflow-wrap:anywhere;
}

.parcel-source-attempts{
  margin-top:6px;
  padding-top:5px;
  border-top:1px solid rgba(255,255,255,.16);
  font-size:10px;
  line-height:1.35;
  font-weight:750;
  letter-spacing:0;
  max-height:86px;
  overflow:auto;
  color:#d8e5ea;
}
.parcel-source-attempts div{
  margin-top:2px;
}
.parcel-source-attempts .attempt-ok{
  color:#9dffb3;
}
.parcel-source-attempts .attempt-warn{
  color:#ffe29a;
}
.parcel-source-attempts .attempt-fail{
  color:#ffb0a6;
}


.demo-parcels-btn{
  border:1px solid rgba(255,184,77,.30);
  background:rgba(255,184,77,.10);
  color:#ffe0ad;
  border-radius:10px;
  padding:6px 10px;
  font-size:11px;
  font-weight:700;
  cursor:pointer;
}

/* MONAHINGA_PAGE1_PARCEL_CONTROLS_CLEANUP_V1_2026_05_08: Chris-facing parcel control cleanup */
.parcel-primary-fetch-btn{
  border:1px solid rgba(126,240,151,.55);
  background:rgba(35,98,48,.88);
  color:#f3ffe8;
  border-radius:10px;
  padding:8px 12px;
  font-weight:900;
  cursor:pointer;
  box-shadow:0 0 0 1px rgba(0,0,0,.25) inset;
}
.parcel-primary-fetch-btn:hover{
  background:rgba(51,132,64,.95);
}
#load_demo_parcels_btn[hidden]{
  display:none !important;
}

.demo-parcels-btn:hover{
  background:rgba(255,184,77,.18);
}


/* MONAHINGA_PAGE1_PARCEL_CONTROLS_CLEANUP_V2_2026_05_08: one-button Chris-facing parcel controls */
.parcel-advanced-tools{
  display:inline-block;
  margin-left:8px;
  vertical-align:middle;
}
.parcel-advanced-tools summary{
  cursor:pointer;
  color:#b8c6be;
  font-weight:800;
  font-size:12px;
  border:1px solid rgba(170,185,172,.28);
  border-radius:10px;
  padding:7px 10px;
  background:rgba(10,16,18,.58);
}
.parcel-advanced-tools[open]{
  display:block;
  margin:10px 0 0 0;
}
.parcel-file-label-advanced{
  margin-top:8px;
  display:inline-block;
}
#load_demo_parcels_btn{
  display:none !important;
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
        <input id="place_search" type="search" name="monahinga_lookup_area" autocomplete="off" autocapitalize="off" spellcheck="false" aria-autocomplete="none" data-form-type="other" placeholder="Search address, town, road, camp, or landmark">
        <button class="secondary" type="button" onclick="searchPlace()">Find place</button>
        <button class="ghost" type="button" onclick="clearSearchResult()">Clear result</button>
      </div>
      <div class="search-meta" id="search_meta">Topo is now the default scouting layer. Search jumps you to a place first, then you draw the hunt box exactly where you want it.</div>
      <div class="map-toolbar">
        <button class="ghost" type="button" onclick="goDefaultView()">Monahinga™ view</button>
        <button class="ghost" type="button" onclick="clearDrawnBox()">Clear Current Selection</button>
        <button class="ghost" type="button" onclick="applyPastedBBox()">Use pasted coordinates</button>
        <button class="ghost" type="button" onclick="applyKnownParcelBox('spearfish')">Spearfish parcels</button>
        <button class="ghost" type="button" onclick="applyKnownParcelBox('shinglehouse')">Shinglehouse parcels</button>
        <button class="ghost" type="button" onclick="applyKnownParcelBox('alleganyny')">Allegany NY parcels</button>
        <button class="ghost" type="button" onclick="applyKnownParcelBox('summitco')">Summit CO hybrid/public box</button>
        <button class="ghost" type="button" onclick="applyKnownParcelBox('summitco_town')">Summit CO town parcel test</button>
        <span class="toolbar-note">Clear the current selection first, then draw a BBox rectangle or polygon. Polygon currently launches using its bounding envelope while exact polygon scoring is built.</span>
      </div>
      <div class="field full" style="margin-bottom:12px;">
        <label>Paste bbox coordinates</label>
        <textarea id="bbox_text" class="coord-input" placeholder="Example: -78.102209, 41.891092, -78.074925, 41.909235">__DEFAULT_BBOX_TEXT__</textarea>
        <small>Format: min lon, min lat, max lon, max lat. Commas, spaces, brackets, and line breaks are all fine.</small>
      </div>
      
      <div class="inline-land-layers" data-created-by="MONAHINGA_INLINE_LAND_LAYER_CONTROL_2026_05_06">
        <strong>Land Layers</strong>
        <label><input id="padus_layer_toggle" type="checkbox"> PAD-US signal</label>
        <button id="padus_refresh_btn" type="button">Refresh PAD-US</button>
        <label><input id="parcel_layer_toggle" type="checkbox"> Private parcels <span class="layer-pending">(GeoJSON)</span></label>
        <details class="parcel-advanced-tools" data-created-by="MONAHINGA_PAGE1_PARCEL_CONTROLS_CLEANUP_V2_2026_05_08"><summary>Advanced parcel tools</summary><label style="display:block;font-size:11px;font-weight:900;color:#d8e5ea;margin:7px 0 4px;">Manual ArcGIS parcel service URL</label><input id="manual_arcgis_url" type="text" placeholder="Paste county/Regrid/ReportAll ArcGIS MapServer or FeatureServer URL" style="width:100%;box-sizing:border-box;background:#050b10;color:#eaf3f4;border:1px solid #2f4454;border-radius:8px;padding:8px;font-size:12px;margin-bottom:5px;"><div style="font-size:10px;color:#b8c5c9;margin:0 0 8px;line-height:1.35;">Optional. BBox-scoped only. Accepts MapServer, FeatureServer, layer URLs, or /query URLs. Verify ownership/access before field use.</div><label class="parcel-file-label parcel-file-label-advanced">Load GeoJSON <input id="parcel_geojson_file" type="file" accept=".geojson,.json,application/geo+json,application/json"></label></details>
        <button id="parcel_fetch_btn" class="parcel-primary-fetch-btn" type="button">Fetch private parcels</button>
        <!-- legacy duplicate Fetch parcels button hidden by MONAHINGA_FREE_PARCEL_LADDER_V2 -->
<button id="load_demo_parcels_btn" class="demo-parcels-btn" type="button" hidden data-hidden-by="MONAHINGA_PAGE1_PARCEL_CONTROLS_CLEANUP_V1_2026_05_08" style="display:none !important;">Demo parcels</button>


<div class="parcel-help-note">
  Use Fetch private parcels for the selected area. Advanced tools are only for manual GeoJSON fallback.
</div>

<div id="parcel_source_status" class="parcel-source-status none" data-created-by="MONAHINGA_PAGE1_PARCEL_SOURCE_STATUS_V2_2026_05_06">
  <strong>PRIVATE PARCELS: NO SOURCE LOADED</strong><br>
  Demo parcels are visual scaffolding only. Use Fetch parcels after a server parcel source is configured, or Load parcels for manual GeoJSON.
</div>

<!-- MONAHINGA_PARCEL_HELP_TEXT_2026_05_06 -->
        <span>Scouting context only. Verify access, ownership, permission, and regulations.</span>
      </div>
      <input id="selection_polygon_json" type="hidden" value="">
      <!-- MONAHINGA_PAGE1_PARCEL_CONTROLS_CLEANUP_V2_2026_05_08: Fetch private parcels is primary; manual GeoJSON is advanced; demo hidden. -->
      <!-- MONAHINGA_AUTO_PRIVATE_PARCEL_RENDER_BRIDGE_V1_2026_05_08: automatic parcel fetch bridge with advanced manual fallback. -->
      <!-- MONAHINGA_REGRID_SOURCE_READY_PASS1_2026_05_08: Regrid chosen as first real parcel source. Demo remains not-real until token/API pass. -->
      <!-- MONAHINGA_FREE_PARCEL_LADDER_V2_2026_05_08: Page 1 uses one fetch button and shows source attempts. -->
      <input id="parcel_geojson_json" type="hidden" value="">
      <div id="bbox-map"></div>
      <div class="bbox-readout">Current selection bounds: <code id="bbox_readout">not drawn yet</code></div>
      <div class="search-meta" id="polygon_envelope_note" style="margin-top:8px;">Polygon mode is selection-first scaffolding: Page 2 still renders the bounding envelope until exact polygon terrain masking is added. Use Clear Current Selection before changing shapes.</div>
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
          <div id="species_identity_card" class="species-identity-card" data-created-by="MONAHINGA_WILDLIFE_IDENTITY_POLISH_V1_2026_05_10">
            <div id="species_identity_icon" class="species-identity-icon" aria-hidden="true">◇</div>
            <div class="species-identity-copy">
              <strong id="species_identity_title">Regional game context</strong>
              <span id="species_identity_body">Choose a species after the BBox is set. The list is gated by state and local plausibility.</span>
              <em id="species_identity_tip">Seasons, tags, weapons, and permission still require verification.</em>
            </div>
          </div>
        </div>

        <!-- MONAHINGA_FUTURE_HUNT_PLANNER_V2: future-hunt planning context. -->
        <div class="field">
          <label>Hunt Timing Plan</label>
          <select id="hunt_plan_window">
            <option value="now">Current / live conditions</option>
            <option value="today_evening">Today evening / last light forecast check</option>
            <option value="tomorrow_morning">Tomorrow morning / first light forecast check</option>
            <option value="tomorrow_evening">Tomorrow evening / last light forecast check</option>
            <option value="custom">Custom date/time forecast check</option>
          </select>
        </div>
        <div class="field">
          <label>Custom Hunt Date/Time</label>
          <input id="hunt_plan_datetime" type="datetime-local" autocomplete="off">
          <small class="micro-copy">Example: 05/13/2026 05:30 AM. This v2 pass frames the hunt plan around the selected window; verify live forecast before field use.</small>
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

const map = L.map('bbox-map' /* MONAHINGA_REPAIR_AFTER_PADUS_AUTOREFRESH_2026_05_06 */ /* MONAHINGA_REPAIR_PAGE1_MAP_AFTER_PADUS_SCAFFOLD_2026_05_06 */, { zoomControl:true, worldCopyJump:false });
const drawLayer = new L.FeatureGroup().addTo(map); // MONAHINGA_AUTO_CLEAR_BEFORE_DRAW_2026_05_06 // MONAHINGA_KEEP_POLYGON_AS_POLYGON_2026_05_06

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

const drawControl = new L.Control.Draw({ // MONAHINGA_DRAW_UX_CLEANUP_2026_05_06
  position: 'topleft',
  draw: {
    polygon: {
  allowIntersection: false,
  showArea: true,
  shapeOptions: {
    color: '#83c9ff',
    weight: 2,
    fillOpacity: 0.12
  }
},
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
    edit: false,
    remove: false
  }
});
map.addControl(drawControl);



map.on(L.Draw.Event.DRAWSTART, function () {
  if (activeRect || drawLayer.getLayers().length) {
    drawLayer.clearLayers();
    activeRect = null;
    const readout = document.getElementById('bbox_readout');
    if (readout) readout.textContent = 'not drawn yet';
    setStatus('Previous selection cleared. Draw the new BBox rectangle or polygon.');
  }
});

function setStatus(message) {
  document.getElementById('status').textContent = message;
}

// Inline land-layer scaffold toggles.
// These groups are intentionally empty until real BBox/viewport-based PAD-US and parcel data are wired in.
const padusSignalLayer = window.padusSignalLayer || L.layerGroup();
const privateParcelLayer = window.privateParcelLayer || L.layerGroup();
window.padusSignalLayer = padusSignalLayer;
window.privateParcelLayer = privateParcelLayer;

// MONAHINGA_PADUS_PREVIEW_LAYER_2026_05_06
let activePadusGeoJsonLayer = null;

function currentBBoxPreviewQuery() {
  const minLon = Number(document.getElementById('min_lon').value);
  const minLat = Number(document.getElementById('min_lat').value);
  const maxLon = Number(document.getElementById('max_lon').value);
  const maxLat = Number(document.getElementById('max_lat').value);
  if (![minLon, minLat, maxLon, maxLat].every(Number.isFinite)) {
    throw new Error('Draw or paste a valid BBox before loading PAD-US.');
  }
  const params = new URLSearchParams({
    min_lon: String(minLon),
    min_lat: String(minLat),
    max_lon: String(maxLon),
    max_lat: String(maxLat)
  });
  return '/padus-preview?' + params.toString();
}

// MONAHINGA_AUTO_PRIVATE_PARCEL_FETCH_PAGE1_2026_05_08
function currentParcelPreviewQuery() {
  const minLon = Number(document.getElementById('min_lon').value);
  const minLat = Number(document.getElementById('min_lat').value);
  const maxLon = Number(document.getElementById('max_lon').value);
  const maxLat = Number(document.getElementById('max_lat').value);
  if (![minLon, minLat, maxLon, maxLat].every(Number.isFinite)) {
    throw new Error('Draw or paste a valid BBox before fetching private parcels.');
  }
  const params = new URLSearchParams({
    min_lon: String(minLon),
    min_lat: String(minLat),
    max_lon: String(maxLon),
    max_lat: String(maxLat)
  });
  const manualArcgisInput = document.getElementById('manual_arcgis_url');
  const manualArcgisUrl = manualArcgisInput ? String(manualArcgisInput.value || '').trim() : '';
  if (manualArcgisUrl) {
    params.set('manual_arcgis_url', manualArcgisUrl);
    try { localStorage.setItem('monahinga_manual_arcgis_url', manualArcgisUrl); } catch(e) {}
  }
  return '/parcel-preview?' + params.toString();
}

async function refreshPrivateParcelSourceLayer() {
  if (!map.hasLayer(privateParcelLayer)) map.addLayer(privateParcelLayer);
  setStatus('Fetching automatic private parcels for the current selection...');

  const url = currentParcelPreviewQuery();
  const res = await fetch(url);
  const payload = await res.json().catch(function () { return {}; });

  if (!res.ok || !payload.ok) {
    const detail = payload && payload.detail ? String(payload.detail) : 'Private parcel source fetch failed.';
    throw new Error(detail);
  }

  const geojson = payload.geojson || { type:'FeatureCollection', features:[] };
  const label = payload.source_label || 'Configured private parcel source';
  loadPrivateParcelGeoJson(geojson, label);
  updateParcelSourceStatus('provider', Number(payload.feature_count || 0), label);
  setStatus('Automatic private parcels loaded: ' + String(payload.feature_count || 0) + ' feature(s). Verify ownership, access, permission, and county records.');
}


async function refreshPadusSignalLayer() {
  if (!map.hasLayer(padusSignalLayer)) map.addLayer(padusSignalLayer);
  padusSignalLayer.clearLayers();
  setStatus('Loading PAD-US signal for the current selection...');

  const url = currentBBoxPreviewQuery();
  const res = await fetch(url);
  const payload = await res.json().catch(function () { return {}; });

  if (!res.ok || !payload.ok) {
    const detail = payload && payload.detail ? String(payload.detail) : 'PAD-US preview failed.';
    throw new Error(detail);
  }

  const geojson = payload.geojson || { type:'FeatureCollection', features:[] };
  const featureCount = Number(payload.feature_count || (geojson.features ? geojson.features.length : 0));

  activePadusGeoJsonLayer = L.geoJSON(geojson, {
    style: function () {
      return {
        color:'#1f7a32',
        weight:2,
        fillColor:'#2fc94f',
        fillOpacity:0.32
      };
    },
    onEachFeature: function (feature, layer) {
      const props = feature && feature.properties ? feature.properties : {};
      const name = props.Unit_Nm || props.Name || props.Loc_Nm || props.Own_Name || props.Manage_Name || 'PAD-US signal area';
      layer.bindPopup(String(name) + '<br>Scouting signal only. Verify access, ownership, permission, and regulations.');
    }
  });

  padusSignalLayer.addLayer(activePadusGeoJsonLayer);

  if (featureCount > 0) {
    setStatus('PAD-US signal loaded for this selection: ' + featureCount + ' feature(s). Verify access, permission, seasons, and local regulations.');
  } else {
    setStatus('PAD-US returned no signal features inside this selection. Land status may be private, unknown, outside coverage, or weakly classified.');
  }
}

// MONAHINGA_MANUAL_PADUS_REFRESH_2026_05_06
// MONAHINGA_PRIVATE_PARCELS_SOURCE_NEEDED_2026_05_06
// MONAHINGA_LOCAL_PARCEL_GEOJSON_IMPORT_2026_05_06
let activePrivateParcelGeoJsonLayer = null;
let activePrivateParcelFeatureCount = 0;

function parcelGeoJsonStoreEl() {
  return document.getElementById('parcel_geojson_json');
}

// MONAHINGA_RENDER_PARCEL_HANDOFF_V24_2026_05_09:
function monahingaRoundParcelCoord(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Number(n.toFixed(6)) : value;
}

function monahingaCompactParcelCoords(coords) {
  if (!Array.isArray(coords)) return coords;
  if (coords.length >= 2 && typeof coords[0] === 'number' && typeof coords[1] === 'number') {
    return [monahingaRoundParcelCoord(coords[0]), monahingaRoundParcelCoord(coords[1])];
  }
  return coords.map(monahingaCompactParcelCoords);
}

function monahingaCompactParcelProperties(props) {
  const source = props && typeof props === 'object' ? props : {};
  const keep = [
    'OWNER','Owner','owner','OWNER_NAME','OWNER_NAME1','owner_name','OWNER1','Owner_Name_1','Owner_Name_2',
    'CURRENT_OW','Owner2','TAXPAYER','MAIL_NAME',
    'PARCEL_ID','PIN','APN','OBJECTID','FID','ACCOUNT','TAXPIN','PID','PARCELNO','PropertyNu','Map_Number','Join1',
    'SITUS','SITE_ADDR','SITUS_ADDRESS','PROPERTY_ADDRESS','ADDRESS','ADDR','PHYSICAL_ADDRESS',
    'Street_Number','Situs_Street','Situs_Suffix','Situs_Direction',
    'Acres','ACRES','Acreage','ACREAGE','Year_Built','YEAR_BUILT','fyrblt',
    'monahinga_parcel_source','monahinga_parcel_source_label','monahinga_parcel_source_ref','monahinga_parcel_warning','monahinga_render_ready'
  ];
  const out = {};
  keep.forEach(function(key) {
    if (Object.prototype.hasOwnProperty.call(source, key) && source[key] !== null && source[key] !== undefined && String(source[key]).length <= 140) {
      out[key] = source[key];
    }
  });
  return out;
}

function monahingaCompactParcelGeoJsonForPayload(geojson) {
  if (!geojson || typeof geojson !== 'object') return null;
  const rawFeatures = Array.isArray(geojson.features) ? geojson.features : [];
  const maxFeatures = 180;
  const features = rawFeatures.slice(0, maxFeatures).map(function(feature) {
    const geom = feature && feature.geometry ? feature.geometry : null;
    return {
      type: 'Feature',
      properties: monahingaCompactParcelProperties((feature && feature.properties) || {}),
      geometry: geom ? {
        type: geom.type,
        coordinates: monahingaCompactParcelCoords(geom.coordinates)
      } : null
    };
  }).filter(function(feature) {
    return feature.geometry && feature.geometry.coordinates;
  });

  const properties = monahingaCompactParcelProperties(geojson.properties || {});
  properties.monahinga_payload_compacted = true;
  properties.monahinga_payload_feature_count = features.length;

  return {
    type: 'FeatureCollection',
    properties: properties,
    features: features
  };
}

function storeParcelGeoJsonForPayload(geojson) {
  const el = parcelGeoJsonStoreEl();
  if (!el) return;
  try {
    const compact = monahingaCompactParcelGeoJsonForPayload(geojson || null);
    const serialized = JSON.stringify(compact || null);
    if (serialized.length > 850000) {
      el.value = '';
      setStatus('Parcel source loaded on Page 1, but the compact run payload is still too large for Page 2. Draw a smaller box and fetch parcels again.');
      return;
    }
    el.value = serialized;
    if (compact && compact.features && compact.features.length) {
      try {
        console.log('[monahinga] stored compact parcel payload features=', compact.features.length, 'bytes=', serialized.length);
      } catch (_logErr) {}
    }
  } catch (err) {
    el.value = '';
    setStatus('Parcel source loaded on Page 1, but compacting it for Page 2 failed: ' + String(err && err.message ? err.message : err));
  }
}

function clearStoredParcelGeoJson() {
  const el = parcelGeoJsonStoreEl();
  if (el) el.value = '';
}

function parcelGeoJsonForPayload() {
  const el = parcelGeoJsonStoreEl();
  if (!el || !el.value) return null;
  try {
    const parsed = JSON.parse(el.value);
    if (!parsed || typeof parsed !== 'object') return null;
    return parsed;
  } catch (_err) {
    return null;
  }
}

function parcelPropertyLabel(props) {
  if (!props) return 'Parcel boundary';
  const keys = [
    'OWNER', 'Owner', 'owner', 'OWNER_NAME', 'owner_name',
    'NAME', 'Name', 'name', 'PARCEL_ID', 'parcel_id',
    'PIN', 'APN', 'MAPBLKLOT', 'ACCOUNT'
  ];
  for (const key of keys) {
    if (props[key]) return String(props[key]);
  }
  return 'Parcel boundary';
}

// MONAHINGA_REAL_PARCEL_NORMALIZATION_V2_2026_05_06
const MONAHINGA_OWNER_FIELD_CANDIDATES = [
  'OWNER', 'Owner', 'owner', 'OWNER_NAME', 'owner_name',
  'PARCEL_OWNER', 'parcel_owner', 'OWN_NAME', 'OWNERNME1',
  'NAME', 'Name', 'name'
];

const MONAHINGA_PARCEL_ID_FIELD_CANDIDATES = [
  'PARCEL_ID', 'parcel_id', 'PIN', 'pin', 'APN', 'apn',
  'OBJECTID', 'FID', 'ACCOUNT', 'MAPBLKLOT', 'TAXPIN'
];

function firstParcelValue(props, keys) {
  props = props || {};
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(props, key)) {
      const value = props[key];
      if (value !== null && value !== undefined && String(value).trim() !== '') {
        return String(value).trim();
      }
    }
  }
  return '';
}

function normalizeParcelFeatureProperties(feature, sourceKind) {
  if (!feature || typeof feature !== 'object') return;
  feature.properties = feature.properties || {};
  const props = feature.properties;

  const owner = firstParcelValue(props, MONAHINGA_OWNER_FIELD_CANDIDATES);
  const parcelId = firstParcelValue(props, MONAHINGA_PARCEL_ID_FIELD_CANDIDATES);

  const normalizedSource = sourceKind === 'demo'
    ? 'DEMO'
    : (sourceKind === 'provider' ? 'AUTO_SOURCE' : 'IMPORTED_GEOJSON');
  props.MONAHINGA_PARCEL_SOURCE = normalizedSource;
  props.MONAHINGA_OWNER_NORMALIZED = owner || 'Unknown owner / verify county records';
  props.MONAHINGA_PARCEL_ID_NORMALIZED = parcelId || 'Unknown parcel ID';
}

function normalizeParcelGeoJsonForMonahinga(geojson, sourceKind, sourceLabel) {
  if (!geojson || typeof geojson !== 'object') return geojson;

  const normalized = geojson;
  normalized.properties = normalized.properties || {};

  if (sourceKind === 'demo') {
    normalized.properties.monahinga_parcel_source = 'demo';
    normalized.properties.monahinga_parcel_source_label = sourceLabel || 'Demo parcel mosaic';
    normalized.properties.monahinga_parcel_warning = 'DEMO VISUAL ONLY. Not real ownership data.';
  } else if (sourceKind === 'provider') {
    normalized.properties.monahinga_parcel_source = 'auto_source';
    normalized.properties.monahinga_parcel_source_label = sourceLabel || 'Configured private parcel source';
    normalized.properties.monahinga_parcel_warning = 'AUTO PARCEL SOURCE. Ownership context only; verify county records, access, permission, and regulations.';
  } else {
    normalized.properties.monahinga_parcel_source = 'imported_geojson';
    normalized.properties.monahinga_parcel_source_label = sourceLabel || 'Imported parcel GeoJSON';
    normalized.properties.monahinga_parcel_warning = 'IMPORTED GEOJSON. Ownership context only; verify county records and permission.';
  }

  const features = Array.isArray(normalized.features)
    ? normalized.features
    : (normalized.type === 'Feature' ? [normalized] : []);

  features.forEach((feature) => normalizeParcelFeatureProperties(feature, sourceKind));
  return normalized;
}

function updateParcelSourceStatus(kind, featureCount, label, message) {
  const el = document.getElementById('parcel_source_status');
  if (!el) return;

  const safeCount = Number.isFinite(Number(featureCount)) ? Number(featureCount) : 0;
  el.className = 'parcel-source-status ' + String(kind || 'none');

  if (kind === 'imported') {
    el.innerHTML =
      '<strong>PRIVATE PARCELS: IMPORTED GEOJSON ACTIVE</strong><br>' +
      String(label || 'Imported parcel GeoJSON') + ' · ' + safeCount + ' feature(s). ' +
      'This imported file will replace demo parcels in the run payload. Verify ownership, permission, access, and county records.';
    return;
  }

  if (kind === 'provider') {
    el.innerHTML =
      '<strong>PRIVATE PARCELS: AUTO SOURCE ACTIVE</strong><br>' +
      String(label || 'Configured private parcel source') + ' · ' + safeCount + ' feature(s). ' +
      'This BBox-scoped source will replace demo parcels in the run payload. Verify ownership, permission, access, and county records.';
    return;
  }

  if (kind === 'demo') {
    el.innerHTML =
      '<strong>PRIVATE PARCELS: DEMO VISUAL ONLY</strong><br>' +
      String(label || 'Demo parcel mosaic') + ' · ' + safeCount + ' placeholder feature(s). ' +
      'These shapes are not real ownership data.';
    return;
  }

  el.innerHTML =
    '<strong>PRIVATE PARCELS: NO SOURCE LOADED</strong><br>' +
    String(message || 'Load imported GeoJSON for real parcel context, or use demo parcels only as visual scaffolding.');
}

function clearPrivateParcelLayer() {
  privateParcelLayer.clearLayers();
  activePrivateParcelGeoJsonLayer = null;
  activePrivateParcelFeatureCount = 0;
  clearStoredParcelGeoJson();
  updateParcelSourceStatus('none', 0, '', 'Load imported GeoJSON for real parcel context, or use demo parcels only as visual scaffolding.');
}

function loadPrivateParcelGeoJson(geojson, label) {
  clearPrivateParcelLayer();

  if (!geojson || typeof geojson !== 'object') {
    throw new Error('Parcel file was not valid GeoJSON.');
  }

  const rawSourceKind = String((geojson.properties && geojson.properties.monahinga_parcel_source) || '').toLowerCase();
  const sourceKind = rawSourceKind === 'demo'
    ? 'demo'
    : (rawSourceKind === 'auto_source' || rawSourceKind === 'provider' ? 'provider' : 'imported_geojson');
  geojson = normalizeParcelGeoJsonForMonahinga(geojson, sourceKind === 'demo' ? 'demo' : (sourceKind === 'provider' ? 'provider' : 'imported'), label);

  const layer = L.geoJSON(geojson, {
    style: function () {
      return {
        color: '#ffd27a',
        weight: 2.2,
        opacity: 0.95,
        fillColor: '#ff9900',
        fillOpacity: 0.38
      };
    },
    onEachFeature: function (feature, layer) {
      const props = feature && feature.properties ? feature.properties : {};
      const name = parcelPropertyLabel(props);
      layer.bindPopup(
        '<strong>Private parcel context</strong><br>' +
        String(name) + '<br>' +
        'Verify ownership, permission, access, and local records before entering.'
      );
    }
  });

  activePrivateParcelGeoJsonLayer = layer;
  storeParcelGeoJsonForPayload(geojson);
  privateParcelLayer.addLayer(layer);

  try {
    layer.bringToFront();
  } catch (_err) {}

  activePrivateParcelFeatureCount = Array.isArray(geojson.features)
    ? geojson.features.length
    : 1;

  const parcelToggle = document.getElementById('parcel_layer_toggle');
  if (parcelToggle) parcelToggle.checked = true;
  if (!map.hasLayer(privateParcelLayer)) map.addLayer(privateParcelLayer);

  const sourceTruthRaw = String((geojson.properties && geojson.properties.monahinga_parcel_source) || '').toLowerCase();
  const sourceTruthKind = sourceTruthRaw === 'demo'
    ? 'demo'
    : (sourceTruthRaw === 'auto_source' || sourceTruthRaw === 'provider' ? 'provider' : 'imported');

  updateParcelSourceStatus(sourceTruthKind, activePrivateParcelFeatureCount, label || 'GeoJSON');

  if (sourceTruthKind === 'demo') {
    setStatus(
      'DEMO VISUAL ONLY parcel mosaic loaded: ' + activePrivateParcelFeatureCount +
      ' placeholder feature(s). This is not real ownership data.'
    );
  } else if (sourceTruthKind === 'provider') {
    setStatus(
      'AUTO private parcel source active: ' + String(label || 'Configured source') +
      ' with ' + activePrivateParcelFeatureCount +
      ' feature(s). This replaces demo parcels in the run payload. Verify permission and county records.'
    );
  } else {
    setStatus(
      'IMPORTED GEOJSON parcel source active: ' + String(label || 'GeoJSON') +
      ' with ' + activePrivateParcelFeatureCount +
      ' feature(s). This replaces demo parcels in the run payload. Verify permission and county records.'
    );
  }

  try {
    const bounds = layer.getBounds();
    if (bounds && bounds.isValid && bounds.isValid()) {
      map.fitBounds(bounds, { padding:[20,20] });
    }
  } catch (_err) {}
}


// MONAHINGA_DEMO_PARCELS_2026_05_06
function buildDemoParcelGeoJson() {
  const bbox = getCurrentBBox();

  if (!bbox) {
    setStatus('Draw a box first before loading demo parcels.');
    return null;
  }

  const minLon = Number(bbox.minLon);
  const minLat = Number(bbox.minLat);
  const maxLon = Number(bbox.maxLon);
  const maxLat = Number(bbox.maxLat);

  const w = maxLon - minLon;
  const h = maxLat - minLat;

  const features = [];

  function rectFeature(id, x1, y1, x2, y2) {
    return {
      type: 'Feature',
      properties: {
        OWNER: 'Demo Parcel ' + id,
        PARCEL_ID: 'DEMO-' + id
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [minLon + (w * x1), minLat + (h * y1)],
          [minLon + (w * x2), minLat + (h * y1)],
          [minLon + (w * x2), minLat + (h * y2)],
          [minLon + (w * x1), minLat + (h * y2)],
          [minLon + (w * x1), minLat + (h * y1)]
        ]]
      }
    };
  }

  features.push(rectFeature(1, 0.08, 0.12, 0.32, 0.36));
  features.push(rectFeature(2, 0.36, 0.14, 0.58, 0.33));
  features.push(rectFeature(3, 0.62, 0.18, 0.88, 0.41));
  features.push(rectFeature(4, 0.12, 0.52, 0.34, 0.78));
  features.push(rectFeature(5, 0.42, 0.56, 0.72, 0.86));

  return {
    type: 'FeatureCollection',
    features: features
  };
}

function loadDemoParcels() {
  try {
    if (!map) {
      setStatus('Map not ready for demo parcels.');
      return;
    }

    const bounds = map.getBounds();

    const west = bounds.getWest();
    const east = bounds.getEast();
    const south = bounds.getSouth();
    const north = bounds.getNorth();

    const width = east - west;
    const height = north - south;

    if (![west, east, south, north, width, height].every(Number.isFinite) || width <= 0 || height <= 0) {
      setStatus('Demo parcel generation failed: map bounds are not ready.');
      return;
    }

    const xCuts = [0.08, 0.27, 0.44, 0.63, 0.82, 0.94];
    const yCuts = [0.10, 0.31, 0.53, 0.75, 0.91];

    const features = [];
    let id = 1;

    function lon(x) { return west + (width * x); }
    function lat(y) { return south + (height * y); }

    function jitterX(row, col, base) {
      const delta = (((row + 1) * (col + 3)) % 5 - 2) * 0.008;
      return Math.max(0.04, Math.min(0.96, base + delta));
    }

    function jitterY(row, col, base) {
      const delta = (((row + 2) * (col + 5)) % 5 - 2) * 0.008;
      return Math.max(0.04, Math.min(0.96, base + delta));
    }

    function parcelFeature(points, label) {
      const coords = points.map((p) => [lon(p[0]), lat(p[1])]);
      coords.push(coords[0]);
      return {
        type: 'Feature',
        properties: {
          OWNER: label,
          PARCEL_ID: 'DEMO-PARCEL-' + String(id).padStart(2, '0')
        },
        geometry: {
          type: 'Polygon',
          coordinates: [coords]
        }
      };
    }

    for (let r = 0; r < yCuts.length - 1; r++) {
      for (let c = 0; c < xCuts.length - 1; c++) {
        const x1 = jitterX(r, c, xCuts[c]);
        const x2 = jitterX(r + 1, c, xCuts[c + 1]);
        const y1 = jitterY(r, c, yCuts[r]);
        const y2 = jitterY(r, c + 1, yCuts[r + 1]);

        // Leave a few natural-looking gaps so the layer reads like rural parcel context,
        // not a perfect spreadsheet grid.
        if ((r === 0 && c === 4) || (r === 3 && c === 0) || (r === 2 && c === 3)) {
          continue;
        }

        let points;
        if ((r + c) % 3 === 0) {
          points = [
            [x1, y1],
            [x2, y1 + 0.015],
            [x2 - 0.018, y2],
            [x1 + 0.01, y2 - 0.014]
          ];
        } else if ((r + c) % 3 === 1) {
          points = [
            [x1 + 0.012, y1],
            [x2, y1],
            [x2, y2 - 0.012],
            [x1, y2],
            [x1, y1 + 0.018]
          ];
        } else {
          points = [
            [x1, y1],
            [x2 - 0.012, y1],
            [x2, y1 + ((y2 - y1) * 0.52)],
            [x2 - 0.020, y2],
            [x1 + 0.014, y2],
            [x1, y1 + ((y2 - y1) * 0.42)]
          ];
        }

        features.push(parcelFeature(points, 'Demo Rural Parcel ' + id));
        id += 1;
      }
    }

    const geojson = normalizeParcelGeoJsonForMonahinga({
      type: 'FeatureCollection',
      properties: {
        monahinga_parcel_source: 'demo',
        monahinga_parcel_source_label: 'Demo parcel mosaic',
        monahinga_parcel_warning: 'DEMO VISUAL ONLY. Not real ownership data.'
      },
      features: features
    }, 'demo', 'Demo parcel mosaic');

    loadPrivateParcelGeoJson(geojson, 'Demo parcel mosaic');

    const parcelToggle = document.getElementById('parcel_layer_toggle');
    if (parcelToggle) {
      parcelToggle.checked = true;
    }

    if (!map.hasLayer(privateParcelLayer)) {
      map.addLayer(privateParcelLayer);
    }

    try {
      privateParcelLayer.bringToFront();
    } catch (_err) {}

    console.log('[MONAHINGA] Demo parcel mosaic rendered:', geojson.features.length);

    setStatus(
      'Demo parcel mosaic rendered: ' + geojson.features.length +
      ' parcel-style features. This proves the private-property overlay path.'
    );

  } catch (err) {
    console.error('[MONAHINGA] Demo parcel failure', err);
    setStatus(
      'Demo parcel render failed: ' +
      String(err && err.message ? err.message : err)
    );
  }
}

// MONAHINGA_REAL_PARCEL_IMPORT_VALIDATOR_V1_2026_05_06

// MONAHINGA_PASS1_IMPORTED_PARCEL_TRUTH_CONFIRMATION_2026_05_07
function analyzeParcelGeoJsonForImport(geojson, fileName, byteSize) {
  const result = {
    ok: false,
    featureCount: 0,
    geometryTypes: {},
    ownerFields: [],
    idFields: [],
    ownerValueCount: 0,
    idValueCount: 0,
    warning: '',
    label: fileName || 'parcel GeoJSON'
  };

  if (!geojson || typeof geojson !== 'object') {
    result.warning = 'File was not valid GeoJSON.';
    return result;
  }

  let features = [];
  if (geojson.type === 'FeatureCollection' && Array.isArray(geojson.features)) {
    features = geojson.features;
  } else if (geojson.type === 'Feature') {
    features = [geojson];
  } else {
    result.warning = 'GeoJSON must be a FeatureCollection or Feature.';
    return result;
  }

  result.featureCount = features.length;

  const ownerFound = new Set();
  const idFound = new Set();

  features.forEach((feature) => {
    const geomType = feature && feature.geometry && feature.geometry.type
      ? String(feature.geometry.type)
      : 'Unknown';

    result.geometryTypes[geomType] = (result.geometryTypes[geomType] || 0) + 1;

    const props = feature && feature.properties ? feature.properties : {};
    let hasOwnerValue = false;
    let hasIdValue = false;

    MONAHINGA_OWNER_FIELD_CANDIDATES.forEach((key) => {
      if (Object.prototype.hasOwnProperty.call(props, key)) {
        ownerFound.add(key);
        const value = props[key];
        if (value !== null && value !== undefined && String(value).trim() !== '') {
          hasOwnerValue = true;
        }
      }
    });

    MONAHINGA_PARCEL_ID_FIELD_CANDIDATES.forEach((key) => {
      if (Object.prototype.hasOwnProperty.call(props, key)) {
        idFound.add(key);
        const value = props[key];
        if (value !== null && value !== undefined && String(value).trim() !== '') {
          hasIdValue = true;
        }
      }
    });

    if (hasOwnerValue) result.ownerValueCount += 1;
    if (hasIdValue) result.idValueCount += 1;
  });

  result.ownerFields = Array.from(ownerFound);
  result.idFields = Array.from(idFound);

  if (result.featureCount <= 0) {
    result.warning = 'No parcel features found.';
    return result;
  }

  if (byteSize && byteSize > 1800000) {
    result.warning = 'Large parcel file. It may display on Page 1, but may be too large to carry into Page 2. Use a smaller AOI/export if needed.';
  }

  result.ok = true;
  return result;
}

function parcelImportStatusMessage(report) {
  if (!report || !report.ok) {
    return 'Parcel import failed. ' + String((report && report.warning) || 'Unknown error.');
  }

  const geometryBits = Object.entries(report.geometryTypes || {})
    .map(([key, value]) => key + ':' + value)
    .join(', ') || 'unknown geometry';

  const ownerBit = report.ownerFields.length
    ? report.ownerFields.join('/')
    : 'no obvious owner field';

  const idBit = report.idFields.length
    ? report.idFields.join('/')
    : 'no obvious parcel ID field';

  let msg =
    'IMPORTED GEOJSON ACTIVE: ' +
    report.featureCount + ' feature(s), ' +
    geometryBits +
    '. Owner fields detected: ' + ownerBit +
    ' (' + report.ownerValueCount + ' feature(s) with owner value).' +
    ' Parcel ID fields detected: ' + idBit +
    ' (' + report.idValueCount + ' feature(s) with parcel ID value).' +
    ' Demo parcels have been replaced in the run payload.';

  if (report.warning) msg += ' Warning: ' + report.warning;

  return msg;
}

function applyParcelImportReportMetadata(geojson, report) {
  if (!geojson || typeof geojson !== 'object' || !report) return geojson;

  geojson.properties = geojson.properties || {};
  geojson.properties.monahinga_parcel_source = 'imported_geojson';
  geojson.properties.monahinga_parcel_source_label = report.label || 'Imported parcel GeoJSON';
  geojson.properties.monahinga_parcel_warning = 'IMPORTED GEOJSON. Ownership context only; verify county records and permission.';
  geojson.properties.monahinga_feature_count = report.featureCount || 0;
  geojson.properties.monahinga_detected_owner_fields = report.ownerFields || [];
  geojson.properties.monahinga_detected_parcel_id_fields = report.idFields || [];
  geojson.properties.monahinga_owner_value_count = report.ownerValueCount || 0;
  geojson.properties.monahinga_parcel_id_value_count = report.idValueCount || 0;

  return geojson;
}

function updateParcelSourceStatusFromImportReport(report) {
  const el = document.getElementById('parcel_source_status');
  if (!el || !report || !report.ok) return;

  const ownerBit = report.ownerFields && report.ownerFields.length
    ? report.ownerFields.join(' / ')
    : 'none detected';

  const idBit = report.idFields && report.idFields.length
    ? report.idFields.join(' / ')
    : 'none detected';

  el.className = 'parcel-source-status imported';
  el.innerHTML =
    '<strong>PRIVATE PARCELS: IMPORTED GEOJSON ACTIVE</strong><br>' +
    String(report.label || 'Imported parcel GeoJSON') + ' · ' +
    String(report.featureCount || 0) + ' feature(s). Demo parcels are replaced in the run payload.<br>' +
    'Owner fields: ' + ownerBit + ' · owner values on ' + String(report.ownerValueCount || 0) + ' feature(s).<br>' +
    'Parcel ID fields: ' + idBit + ' · parcel IDs on ' + String(report.idValueCount || 0) + ' feature(s).<br>' +
    'Ownership context only. Verify county records, access, permission, and regulations.';
}


// MONAHINGA_AUTO_PRIVATE_PARCEL_FETCH_V2_2026_05_08
async function fetchPrivateParcelsForSelectedArea() {
  const btn = document.getElementById('fetch_private_parcels_btn');
  try {
    if (btn) btn.disabled = true;
    setStatus('Fetching automatic private parcel preview for selected area...');

    const minLon = parseFloat(document.getElementById('min_lon').value);
    const minLat = parseFloat(document.getElementById('min_lat').value);
    const maxLon = parseFloat(document.getElementById('max_lon').value);
    const maxLat = parseFloat(document.getElementById('max_lat').value);
    if (![minLon, minLat, maxLon, maxLat].every(Number.isFinite)) {
      throw new Error('Draw or paste a valid selected box first.');
    }

    const params = new URLSearchParams({
      min_lon: String(minLon),
      min_lat: String(minLat),
      max_lon: String(maxLon),
      max_lat: String(maxLat),
    });

    const resp = await fetch('/parcel-preview?' + params.toString());
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data || data.ok === false) {
      throw new Error((data && (data.detail || data.message)) || 'Automatic parcel preview failed.');
    }
    if (!data.geojson || !Array.isArray(data.geojson.features)) {
      throw new Error('Automatic parcel preview returned no GeoJSON features.');
    }

    const label = data.source_label || data.source || 'Automatic parcel preview';
    const normalized = normalizeParcelGeoJsonForMonahinga(data.geojson, 'imported', label);
    loadPrivateParcelGeoJson(normalized, label);
    updateParcelSourceStatus('imported', normalized.features.length, label, data.message || 'Automatic parcels loaded.');

    const parcelToggle = document.getElementById('parcel_layer_toggle');
    if (parcelToggle) parcelToggle.checked = true;
    if (!map.hasLayer(privateParcelLayer)) map.addLayer(privateParcelLayer);

    setStatus((data.message || 'Automatic parcels loaded.') + ' Feature count: ' + String(normalized.features.length) + '.');
  } catch (err) {
    setStatus('Automatic parcel fetch failed. ' + String(err && err.message ? err.message : err));
  } finally {
    if (btn) btn.disabled = false;
  }
}



function escapeParcelSummaryHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatParcelSourceSummaryForPanel(summary) {
  if (!summary || typeof summary !== 'object') return '';
  const sample = summary.sample || {};
  const rows = [];
  if (sample.owner) rows.push('<div><span>Owner field</span><b>' + escapeParcelSummaryHtml(sample.owner) + '</b></div>');
  if (sample.parcel_id) rows.push('<div><span>Parcel ID</span><b>' + escapeParcelSummaryHtml(sample.parcel_id) + '</b></div>');
  if (sample.situs) rows.push('<div><span>Situs</span><b>' + escapeParcelSummaryHtml(sample.situs) + '</b></div>');
  const extras = [];
  if (sample.acres) extras.push('Acres: ' + escapeParcelSummaryHtml(sample.acres));
  if (sample.year_built) extras.push('Built: ' + escapeParcelSummaryHtml(sample.year_built));
  if (extras.length) rows.push('<div><span>Extra</span><b>' + extras.join(' · ') + '</b></div>');
  if (!rows.length) return '';
  return '<div class="parcel-source-summary"><strong>Detected parcel proof fields</strong>' + rows.join('') + '</div>';
}


function parcelAttemptStatusClassForPanel(statusText) {
  const s = String(statusText || '').toLowerCase();
  if (s.includes('ok') || s.includes('success') || s.includes('features=')) return 'attempt-ok';
  if (s.includes('skipped') || s.includes('zero usable') || s.includes('returned zero') || s.includes('fallback')) return 'attempt-warn';
  return 'attempt-fail';
}

function shortenParcelAttemptForPanel(statusText) {
  let s = String(statusText || '').replace(/\s+/g, ' ').trim();
  s = s.replace(/ValueError:\s*/g, '');
  s = s.replace(/identify failed:\s*/g, 'identify: ');
  s = s.replace(/query failed:\s*/g, 'query: ');
  s = s.replace(/returned zero usable private parcel polygon geometries after rejecting county\/state\/road layers/g, 'zero usable parcel polygons after filtering county/state/road layers');
  s = s.replace(/identify returned zero usable private parcel geometries after rejecting county\/state\/road layers/g, 'identify found zero usable parcel polygons after filtering county/state/road layers');
  if (s.length > 150) s = s.slice(0, 147) + '...';
  return s || 'no detail';
}

function formatParcelSourceAttemptsForPanel(sourceAttempts) {
  if (!Array.isArray(sourceAttempts) || !sourceAttempts.length) return '';
  const rows = sourceAttempts.slice(0, 6).map(function(attempt) {
    const source = String((attempt && attempt.source) || 'source');
    const status = String((attempt && attempt.status) || '');
    const klass = parcelAttemptStatusClassForPanel(status);
    return '<div><span class="' + klass + '">• ' + source + '</span>: ' + shortenParcelAttemptForPanel(status) + '</div>';
  }).join('');
  const extra = sourceAttempts.length > 6
    ? '<div class="attempt-warn">• +' + String(sourceAttempts.length - 6) + ' more source attempt(s)</div>'
    : '';
  return '<div class="parcel-source-attempts"><strong>Source attempts</strong>' + rows + extra + '</div>';
}

function summarizeParcelSourceAttemptsForStatus(sourceAttempts) {
  if (!Array.isArray(sourceAttempts) || !sourceAttempts.length) return '';
  const failed = sourceAttempts.filter(function(a) {
    const s = String((a && a.status) || '').toLowerCase();
    return !(s.includes('ok') || s.includes('success') || s.includes('features='));
  }).length;
  return ' Source attempts checked: ' + String(sourceAttempts.length) + '; needing fallback/filtering: ' + String(failed) + '.';
}

async function fetchPrivateParcelsForCurrentSelection() {
  try {
    const bounds = normalizeBoundsFromInputs();
    if (!bounds) throw new Error('Draw or paste a valid selected box first.');
    applyBBoxToForm(bounds);
    const payload = {
      min_lon: Number(document.getElementById('min_lon').value),
      min_lat: Number(document.getElementById('min_lat').value),
      max_lon: Number(document.getElementById('max_lon').value),
      max_lat: Number(document.getElementById('max_lat').value),
      selection_polygon: storedSelectionPolygonForPayload() || selectionPolygonForPayload(bounds) || null
    };
    const manualArcgisInput = document.getElementById('manual_arcgis_url');
    const manualArcgisUrl = manualArcgisInput ? String(manualArcgisInput.value || '').trim() : '';
    if (manualArcgisUrl) {
      payload.manual_arcgis_url = manualArcgisUrl;
      try { localStorage.setItem('monahinga_manual_arcgis_url', manualArcgisUrl); } catch(e) {}
    }
    setStatus('Fetching private parcel source for selected area...');
    const res = await fetch('/parcel-preview', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    let data = null;
    try { data = await res.json(); } catch (_) { data = null; }
    if (!res.ok || !data || !data.ok || !data.geojson) {
      const detail = data && (data.detail || data.message) ? (data.detail || data.message) : ('HTTP ' + res.status);
      throw new Error(String(detail));
    }
    const label = data.source_label || data.source || 'Automatic parcel source';
    const sourceKindRaw = String(data.source || '').toLowerCase();
    const isDemoSource = sourceKindRaw.includes('demo');
    const isProviderSource = !isDemoSource && (
      data.render_ready === true ||
      sourceKindRaw.includes('arcgis') ||
      sourceKindRaw.includes('pasda') ||
      sourceKindRaw.includes('configured') ||
      sourceKindRaw.includes('regrid') ||
      sourceKindRaw.includes('public') ||
      sourceKindRaw.includes('parcel')
    );
    const monahingaSourceKind = isDemoSource ? 'demo' : (isProviderSource ? 'provider' : 'imported');
    let geojson = normalizeParcelGeoJsonForMonahinga(data.geojson, monahingaSourceKind, label);
    const report = analyzeParcelGeoJsonForImport(geojson, label, 0);
    applyParcelImportReportMetadata(geojson, report);
    geojson.properties = geojson.properties || {};
    geojson.properties.monahinga_parcel_source = monahingaSourceKind === 'provider'
      ? 'auto_source'
      : (monahingaSourceKind === 'demo' ? 'demo' : 'imported_geojson');
    geojson.properties.monahinga_parcel_source_ref = data.source || '';
    geojson.properties.monahinga_parcel_source_label = label;
    geojson.properties.monahinga_parcel_warning = data.message || geojson.properties.monahinga_parcel_warning || 'Verify county records, access, permission, and regulations.';
    geojson.properties.monahinga_render_ready = !!data.render_ready;
    loadPrivateParcelGeoJson(geojson, label);
    const parcelToggle = document.getElementById('parcel_layer_toggle');
    if (parcelToggle) parcelToggle.checked = true;
    const statusEl = document.getElementById('parcel_source_status');
    if (statusEl) {
      const sourceKind = String(data.source || '').toLowerCase();
      const isDemo = sourceKind.includes('demo');
      const isProvider = !isDemo && (
        data.render_ready === true ||
        sourceKind.includes('arcgis') ||
        sourceKind.includes('pasda') ||
        sourceKind.includes('configured') ||
        sourceKind.includes('regrid') ||
        sourceKind.includes('public') ||
        sourceKind.includes('parcel')
      );
      const statusClass = isDemo ? 'demo' : (isProvider ? 'provider' : 'imported');
      const headline = isDemo
        ? 'PRIVATE PARCELS: DEMO VISUAL ONLY'
        : (isProvider ? 'PRIVATE PARCELS: BBOX-SCOPED SOURCE ACTIVE' : 'PRIVATE PARCELS: IMPORTED SOURCE ACTIVE');
      const proofLine = isDemo
        ? 'Demo only — not real ownership. Do not use this as parcel truth.'
        : 'Ownership context only. Verify county records, access, permission, and local regulations before field use.';
      const summaryLine = formatParcelSourceSummaryForPanel(data.source_summary);
      const attemptLine = formatParcelSourceAttemptsForPanel(data.source_attempts);
      statusEl.className = 'parcel-source-status ' + statusClass;
      statusEl.innerHTML =
        '<strong>' + headline + '</strong><br>' +
        String(label) + ' · ' + String(data.feature_count || 0) + ' feature(s).<br>' +
        proofLine + summaryLine + attemptLine;
    }
    const attemptText = summarizeParcelSourceAttemptsForStatus(data.source_attempts);
    setStatus(String(data.message || ('Private parcels loaded: ' + label)) + attemptText);
  } catch (err) {
    setStatus('Automatic private parcel fetch failed. ' + String(err && err.message ? err.message : err));
  }
}

function wirePrivateParcelFileInput() {
  const input = document.getElementById('parcel_geojson_file');
  // Legacy duplicate fetch button intentionally disabled by MONAHINGA_FREE_PARCEL_LADDER_V2.
const demoBtn = document.getElementById('load_demo_parcels_btn');
  if (demoBtn && demoBtn.dataset.wired !== 'yes') {
    demoBtn.dataset.wired = 'yes';
    demoBtn.addEventListener('click', function () {
      console.log('[MONAHINGA] Demo parcels button clicked');
      setStatus('Loading demo parcel overlays...');
      loadDemoParcels();

      const parcelToggle = document.getElementById('parcel_layer_toggle');
      if (parcelToggle) {
        parcelToggle.checked = true;
      }
    });
  }

  if (!input || input.dataset.wired === 'yes') return;
  input.dataset.wired = 'yes';

  input.addEventListener('change', function () {
    const file = input.files && input.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function () {
      try {
        let geojson = JSON.parse(String(reader.result || ''));
        geojson = normalizeParcelGeoJsonForMonahinga(geojson, 'imported', file.name || 'Imported parcel GeoJSON');
        const report = analyzeParcelGeoJsonForImport(geojson, file.name, file.size || 0);
        if (!report.ok) {
          throw new Error(report.warning || 'Parcel GeoJSON did not pass validation.');
        }
        applyParcelImportReportMetadata(geojson, report);
        loadPrivateParcelGeoJson(geojson, file.name);
        updateParcelSourceStatusFromImportReport(report);
        setStatus(parcelImportStatusMessage(report));
      } catch (err) {
        clearPrivateParcelLayer();
        const parcelToggle = document.getElementById('parcel_layer_toggle');
        if (parcelToggle) parcelToggle.checked = false;
        if (map.hasLayer(privateParcelLayer)) map.removeLayer(privateParcelLayer);
        setStatus('Private parcel GeoJSON load failed. ' + String(err && err.message ? err.message : err));
      }
    };
    reader.onerror = function () {
      setStatus('Private parcel GeoJSON load failed. Could not read file.');
    };
    reader.readAsText(file);
  });
}

function wireLandLayerToggles() {
  const padusToggle = document.getElementById('padus_layer_toggle');
  const parcelToggle = document.getElementById('parcel_layer_toggle');
  const padusRefreshBtn = document.getElementById('padus_refresh_btn');
  const parcelFetchBtn = document.getElementById('parcel_fetch_btn');

  wirePrivateParcelFileInput();


  if (parcelFetchBtn && !parcelFetchBtn.dataset.wired) {
    parcelFetchBtn.dataset.wired = 'yes';
    parcelFetchBtn.addEventListener('click', async function () {
      try {
        if (parcelToggle) parcelToggle.checked = true;
        await fetchPrivateParcelsForCurrentSelection();
      } catch (err) {
        if (parcelToggle) parcelToggle.checked = false;
        if (map.hasLayer(privateParcelLayer)) map.removeLayer(privateParcelLayer);
        updateParcelSourceStatus('none', 0, '', 'Real parcel source is not configured yet. Regrid is selected for Pass 2. Use demo/GeoJSON only as visual proof until MONAHINGA_REGRID_TOKEN is wired and verified.');
        setStatus('Automatic private parcel fetch failed. ' + String(err && err.message ? err.message : err));
      }
    });
  }

  if (padusRefreshBtn && !padusRefreshBtn.dataset.wired) {
    padusRefreshBtn.dataset.wired = 'yes';
    padusRefreshBtn.addEventListener('click', async function () {
      try {
        if (padusToggle) padusToggle.checked = true;
        await refreshPadusSignalLayer();
      } catch (err) {
        setStatus('PAD-US refresh failed. ' + String(err && err.message ? err.message : err));
      }
    });
  }

  if (padusToggle && !padusToggle.dataset.wired) {
    padusToggle.dataset.wired = 'yes';
    padusToggle.addEventListener('change', async function () {
      if (padusToggle.checked) {
        try {
          await refreshPadusSignalLayer();
        } catch (err) {
          padusToggle.checked = false;
          if (map.hasLayer(padusSignalLayer)) map.removeLayer(padusSignalLayer);
          setStatus('PAD-US preview failed. ' + String(err && err.message ? err.message : err));
        }
      } else {
        padusSignalLayer.clearLayers();
        if (map.hasLayer(padusSignalLayer)) map.removeLayer(padusSignalLayer);
        setStatus('PAD-US signal layer hidden.');
      }
    });
  }

  if (parcelToggle && !parcelToggle.dataset.wired) {
    parcelToggle.dataset.wired = 'yes';
    parcelToggle.addEventListener('change', function () {
      if (parcelToggle.checked) {
        if (activePrivateParcelGeoJsonLayer) {
          if (!map.hasLayer(privateParcelLayer)) map.addLayer(privateParcelLayer);
          setStatus('Private parcels layer shown: ' + activePrivateParcelFeatureCount + ' feature(s). Verify permission and county records.');
        } else {
          parcelToggle.checked = false;
          if (map.hasLayer(privateParcelLayer)) map.removeLayer(privateParcelLayer);
          setStatus('Private parcels need a source first. Click Fetch private parcels, or Load GeoJSON and choose a county GIS/Regrid/ReportAll parcel GeoJSON export.');
        }
      } else {
        if (map.hasLayer(privateParcelLayer)) map.removeLayer(privateParcelLayer);
        setStatus('Private parcels layer hidden.');
      }
    });
  }
}

setTimeout(wireLandLayerToggles, 0);

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
// MONAHINGA_SPECIES_GATE_V1: conservative BBox/state species filter.
const MONAHINGA_SPECIES_BY_STATE = {
  PA: ['default','whitetail','black_bear','turkey','coyote'],
  NY: ['default','whitetail','black_bear','turkey','coyote'],
  WY: ['default','whitetail','mule_deer','elk','moose','bighorn','pronghorn','black_bear','turkey','coyote'],
  CO: ['default','whitetail','mule_deer','elk','moose','bighorn','pronghorn','black_bear','turkey','coyote'],
  SD: ['default','whitetail','mule_deer','pronghorn','turkey','coyote'],
  MT: ['default','whitetail','mule_deer','elk','moose','bighorn','pronghorn','black_bear','turkey','coyote']
};
function monahingaStateFromBBox(bbox) {
  const lon = (Number(bbox.minLon) + Number(bbox.maxLon)) / 2;
  const lat = (Number(bbox.minLat) + Number(bbox.maxLat)) / 2;
  if (!Number.isFinite(lon) || !Number.isFinite(lat)) return '';
  if (lon >= -80.7 && lon <= -74.6 && lat >= 39.6 && lat <= 42.6) return 'PA';
  if (lon >= -79.9 && lon <= -71.7 && lat >= 40.3 && lat <= 45.1) return 'NY';
  if (lon >= -111.2 && lon <= -104.0 && lat >= 40.9 && lat <= 45.1) return 'WY';
  if (lon >= -109.2 && lon <= -101.9 && lat >= 36.8 && lat <= 41.1) return 'CO';
  if (lon >= -104.2 && lon <= -96.3 && lat >= 42.3 && lat <= 46.1) return 'SD';
  if (lon >= -116.2 && lon <= -104.0 && lat >= 44.2 && lat <= 49.1) return 'MT';
  return '';
}
// MONAHINGA_WILDLIFE_IDENTITY_POLISH_V1_2026_05_10: species identity card helpers.
const MONAHINGA_SPECIES_IDENTITY = {
  default: {icon:'◇', title:'General terrain read', body:'Reads terrain, access, cover, wind, and legal-land context without locking to one animal.', tip:'Good for scouting a new BBox before choosing a species.'},
  whitetail: {icon:'🦌', title:'Whitetail deer', body:'Prioritizes bedding edges, side-hill travel, cover transitions, and low-pressure access.', tip:'Best when wind, entry route, and evening or morning movement all agree.'},
  mule_deer: {icon:'🦌', title:'Mule deer', body:'Looks for broken slopes, benches, open-to-cover transitions, and glassable terrain.', tip:'Western terrain read: visibility and escape cover matter.'},
  elk: {icon:'🫎', title:'Elk', body:'Favors saddles, benches, timber edges, escape cover, and wind-safe approaches.', tip:'Keep thermals, pressure, and daylight movement windows in mind.'},
  moose: {icon:'🫎', title:'Moose', body:'Wet cover, browse edges, and low-pressure corridors matter where this species is legal and present.', tip:'Only appears where the state gate allows it.'},
  bighorn: {icon:'🐏', title:'Bighorn sheep', body:'Steep escape terrain, open visibility, and approach discipline drive the read.', tip:'Highly location-specific; verify unit, tags, and regulations.'},
  pronghorn: {icon:'🦌', title:'Pronghorn', body:'Open-country visibility, approach concealment, and wind exposure dominate the read.', tip:'Use terrain breaks and avoid skyline exposure.'},
  black_bear: {icon:'🐻', title:'Black bear', body:'Food edges, shaded drainages, thick cover, and quiet access become more important.', tip:'Verify season, bait rules, weapons, and local restrictions.'},
  turkey: {icon:'🦃', title:'Wild turkey', body:'Roost-to-feed movement, ridge benches, field edges, and open timber shape the setup.', tip:'PA turkey specialist: morning setups should protect the roost, avoid crowding birds, and keep calling disciplined.'},
  hog: {icon:'🐗', title:'Feral hog', body:'Water, cover, disturbed ground, and food edges matter only where hogs are realistically present.', tip:'State gate should hide this where not locally relevant.'},
  coyote: {icon:'🐺', title:'Coyote', body:'Travel seams, downwind approach control, visibility, and human-pressure edges matter.', tip:'Keep wind and shooting lanes honest.'},
  javelina: {icon:'🐗', title:'Javelina', body:'Arid cover, washes, food patches, and warm-country habitat matter where present.', tip:'State gate should hide this outside plausible range.'}
};
function monahingaUpdateSpeciesIdentityCard() {
  const select = document.getElementById('target_species');
  const card = document.getElementById('species_identity_card');
  if (!select || !card) return;
  const bbox = currentBBox();
  const state = monahingaStateFromBBox(bbox);
  const key = select.value || 'default';
  const info = MONAHINGA_SPECIES_IDENTITY[key] || MONAHINGA_SPECIES_IDENTITY.default;
  const icon = document.getElementById('species_identity_icon');
  const title = document.getElementById('species_identity_title');
  const body = document.getElementById('species_identity_body');
  const tip = document.getElementById('species_identity_tip');
  if (icon) icon.textContent = info.icon;
  if (title) title.textContent = info.title + (state ? ' · ' + state : '');
  if (body) body.textContent = info.body;
  if (tip) {
    const stateNote = state ? ' Species gate is active for ' + state + '.' : ' Species gate could not confidently identify the state from this BBox.';
    tip.textContent = info.tip + stateNote + ' Verify seasons, tags, permission, and local rules.';
  }
}

function monahingaApplySpeciesGate() {
  const select = document.getElementById('target_species');
  if (!select) return;
  const bbox = currentBBox();
  const state = monahingaStateFromBBox(bbox);
  const allowedList = MONAHINGA_SPECIES_BY_STATE[state] || null;
  let note = document.getElementById('species_gate_note');
  if (!note && select.parentNode) {
    note = document.createElement('div');
    note.id = 'species_gate_note';
    note.className = 'helper';
    note.style.marginTop = '6px';
    select.parentNode.appendChild(note);
  }
  if (!allowedList) {
    Array.from(select.options).forEach(function(opt) { opt.disabled = false; opt.hidden = false; });
    if (note) note.textContent = 'Species gate: state not confidently identified from this BBox. Verify local seasons, tags, and species availability.';
    monahingaUpdateSpeciesIdentityCard();
    return;
  }
  const allowed = new Set(allowedList);
  Array.from(select.options).forEach(function(opt) {
    const ok = allowed.has(opt.value);
    opt.disabled = !ok;
    opt.hidden = !ok;
  });
  if (!allowed.has(select.value)) select.value = allowed.has('whitetail') ? 'whitetail' : 'default';
  if (note) note.textContent = 'Species gate: ' + state + ' BBox. Showing conservative in-state target options only. Seasons, tags, weapons, and permission still require verification.';
  monahingaUpdateSpeciesIdentityCard();
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
  monahingaApplySpeciesGate();
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

// MONAHINGA_ALLEGANY_SUMMIT_PRESETS_2026_05_09: county parcel quick tests for Chris/Tom requests.
function applyKnownParcelBox(kind) {
  const presets = {
    spearfish: {
      label: 'Spearfish / Lawrence County SD',
      bbox: '-103.870979, 44.491702, -103.866728, 44.493386'
    },
    shinglehouse: {
      label: 'Shinglehouse / Potter County PA',
      bbox: '-78.205500, 41.948500, -78.175500, 41.969500'
    },
    alleganyny: {
      label: 'Allegany County NY',
      bbox: '-78.365000, 42.205000, -78.245000, 42.285000'
    },
    summitco: {
      label: 'Summit County CO hybrid/public-land box',
      bbox: '-106.110000, 39.550000, -106.020000, 39.620000'
    },
    summitco_town: {
      label: 'Summit County CO town parcel detail test - Frisco/Silverthorne edge',
      bbox: '-106.085000, 39.570000, -106.035000, 39.610000'
    }
  };
  const preset = presets[kind];
  if (!preset) {
    setStatus('Unknown parcel preset.');
    return;
  }
  const manualArcgisInput = document.getElementById('manual_arcgis_url');
  if (manualArcgisInput) {
    manualArcgisInput.value = '';
    try { localStorage.setItem('monahinga_manual_arcgis_url', ''); } catch(e) {}
  }
  const bboxText = document.getElementById('bbox_text');
  if (bboxText) bboxText.value = preset.bbox;
  applyPastedBBox();
  const parcelToggle = document.getElementById('parcel_layer_toggle');
  if (parcelToggle) parcelToggle.checked = true;
  setStatus(preset.label + ' preset applied. Manual ArcGIS URL cleared so Fetch private parcels proves automatic county-source mode.');
  if (typeof fetchPrivateParcelsForCurrentSelection === 'function') {
    window.setTimeout(function() {
      fetchPrivateParcelsForCurrentSelection();
    }, 250);
  }
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

function monahingaSearchUnique(list) {
  const out = [];
  const seen = new Set();
  (list || []).forEach(function(item) {
    const value = String(item || '').replace(/\s+/g, ' ').trim();
    const key = value.toLowerCase();
    if (value && !seen.has(key)) {
      seen.add(key);
      out.push(value);
    }
  });
  return out;
}

function monahingaAddressSearchVariants(rawQuery) {
  const q = String(rawQuery || '').replace(/\s+/g, ' ').trim();
  const variants = [q];

  const srMatch = q.match(/\bSR\s*([0-9]+)\s*([NSEW])?\b/i);
  if (srMatch) {
    const num = srMatch[1];
    const dir = srMatch[2] ? (' ' + srMatch[2].toUpperCase()) : '';
    variants.push(q.replace(/\bSR\s*[0-9]+\s*[NSEW]?\b/i, 'State Route ' + num + dir));
    variants.push(q.replace(/\bSR\s*[0-9]+\s*[NSEW]?\b/i, 'Route ' + num + dir));
    variants.push(q.replace(/\bSR\s*[0-9]+\s*[NSEW]?\b/i, 'PA-' + num));
    variants.push(q.replace(/\bSR\s*[0-9]+\s*[NSEW]?\b/i, 'PA ' + num));
    variants.push(q.replace(/\bSR\s*[0-9]+\s*[NSEW]?\b/i, 'Pennsylvania ' + num));
    variants.push(q.replace(/\bSR\s*[0-9]+\s*[NSEW]?\b/i, 'Pennsylvania Route ' + num + dir));
  }

  const paMatch = q.match(/\bPA[-\s]*([0-9]+)\s*([NSEW])?\b/i);
  if (paMatch) {
    const num = paMatch[1];
    const dir = paMatch[2] ? (' ' + paMatch[2].toUpperCase()) : '';
    variants.push(q.replace(/\bPA[-\s]*[0-9]+\s*[NSEW]?\b/i, 'State Route ' + num + dir));
    variants.push(q.replace(/\bPA[-\s]*[0-9]+\s*[NSEW]?\b/i, 'Route ' + num + dir));
    variants.push(q.replace(/\bPA[-\s]*[0-9]+\s*[NSEW]?\b/i, 'Pennsylvania Route ' + num + dir));
  }

  if (/shinglehouse/i.test(q) && /44/.test(q)) {
    variants.push('1854 State Route 44 N, Shinglehouse, Potter County, PA 16748');
    variants.push('1854 Pennsylvania Route 44, Shinglehouse, Potter County, PA 16748');
    variants.push('1854 PA-44, Shinglehouse, PA 16748');
    variants.push('1854 Route 44, Shinglehouse, PA 16748');
    variants.push('1854 State Route 44, Shinglehouse, PA 16748');
  }

  return monahingaSearchUnique(variants).slice(0, 10);
}


async function monahingaFetchParcelAddressLookup(query) {
  const url = '/parcel-address-lookup?query=' + encodeURIComponent(query);
  const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
  if (!res.ok) return null;
  const data = await res.json();
  if (!data || data.ok !== true) return null;
  const lat = Number(data.lat);
  const lon = Number(data.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || !pointLooksLower48(lat, lon)) return null;
  return data;
}

function monahingaApplyParcelAddressLookup(hit, originalQuery) {
  const lat = Number(hit.lat);
  const lon = Number(hit.lon);
  if (searchMarker) map.removeLayer(searchMarker);
  searchMarker = L.marker([lat, lon]).addTo(map);
  const name = String(hit.display_name || originalQuery || 'Parcel address match');
  searchMarker.bindPopup(name).openPopup();

  if (Array.isArray(hit.bbox) && hit.bbox.length === 4) {
    const west = Number(hit.bbox[0]);
    const south = Number(hit.bbox[1]);
    const east = Number(hit.bbox[2]);
    const north = Number(hit.bbox[3]);
    if ([south, north, west, east].every(Number.isFinite)) {
      map.fitBounds([[south, west], [north, east]], { padding:[36,36] });
      const bboxText = document.getElementById('bbox_text');
      if (bboxText) {
        bboxText.value = [west, south, east, north].map(function(v){ return Number(v).toFixed(6); }).join(', ');
        applyPastedBBox();
      }
    } else {
      map.setView([lat, lon], 16);
    }
  } else {
    map.setView([lat, lon], 16);
  }

  setSearchMeta('Found by Potter County parcel lookup: ' + name + '. Parcel ID: ' + String(hit.parcel_id || 'unknown') + '. Draw or adjust your hunt box.');
  setStatus('Place found from county parcel data. The map jumped to the matching parcel/address area.');
}


async function monahingaFetchSearchResults(query) {
  const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&dedupe=1&limit=5&countrycodes=us&q=' + encodeURIComponent(query);
  const res = await fetch(url, {
    headers: { 'Accept': 'application/json' }
  });
  if (!res.ok) throw new Error('Place search failed for: ' + query);
  const results = await res.json();
  return Array.isArray(results) ? results : [];
}

function monahingaPickLower48SearchHit(results) {
  for (const hit of (results || [])) {
    const lat = Number(hit && hit.lat);
    const lon = Number(hit && hit.lon);
    if (Number.isFinite(lat) && Number.isFinite(lon) && pointLooksLower48(lat, lon)) {
      return hit;
    }
  }
  return null;
}



// MONAHINGA_ADDRESS_PRIVACY_V26_2026_05_09
function monahingaIsAddressLikeForPrivacy(value) {
  const q = String(value || '').trim();
  return /\d/.test(q) && /(street|st\b|road|rd\b|route|rt\b|sr\b|state|highway|hwy|pa[-\s]*\d+|us[-\s]*\d+|\d{5})/i.test(q);
}

function monahingaSafeSearchLabel(rawLabel, originalQuery, fallback) {
  const original = String(originalQuery || '');
  const label = String(rawLabel || fallback || 'Located area');
  if (monahingaIsAddressLikeForPrivacy(original) || monahingaIsAddressLikeForPrivacy(label)) {
    if (/shinglehouse|potter/i.test(label + ' ' + original)) return 'Known Shinglehouse parcel area';
    return 'Located parcel/search area';
  }
  return label;
}

function monahingaScrubPlaceSearchInput() {
  try {
    const input = document.getElementById('place_search');
    if (!input) return;
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('autocapitalize', 'off');
    input.setAttribute('spellcheck', 'false');
    input.setAttribute('aria-autocomplete', 'none');
    input.setAttribute('data-form-type', 'other');
    input.value = '';
    input.blur();
  } catch (_err) {}
}

async function monahingaFetchKnownAddressLookup(query) {
  const url = '/known-address-lookup?query=' + encodeURIComponent(query);
  try {
    const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
    if (!res.ok) return null;
    const data = await res.json();
    if (!data || data.ok !== true) return null;
    const lat = Number(data.lat);
    const lon = Number(data.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || !pointLooksLower48(lat, lon)) return null;
    return data;
  } catch (e) {
    return null;
  }
}

function monahingaApplyKnownAddressLookup(hit, originalQuery) {
  const lat = Number(hit.lat);
  const lon = Number(hit.lon);
  if (searchMarker) map.removeLayer(searchMarker);
  searchMarker = L.marker([lat, lon]).addTo(map);
  const name = monahingaSafeSearchLabel(hit.display_name, originalQuery, 'Known address match');
  searchMarker.bindPopup(name).openPopup();

  if (Array.isArray(hit.bbox) && hit.bbox.length === 4) {
    const west = Number(hit.bbox[0]);
    const south = Number(hit.bbox[1]);
    const east = Number(hit.bbox[2]);
    const north = Number(hit.bbox[3]);
    if ([south, north, west, east].every(Number.isFinite)) {
      map.fitBounds([[south, west], [north, east]], { padding:[44,44] });
    } else {
      map.setView([lat, lon], 16);
    }
  } else {
    map.setView([lat, lon], 16);
  }

  setSearchMeta('Found known Potter County parcel area. Parcel ID: ' + String(hit.parcel_id || 'verify county records') + '. Now draw your bbox around the property/terrain. Exact private address is not retained in the search box.');
  setStatus('Place found from known Potter County parcel record. The map moved only; now draw the bbox.');
  monahingaScrubPlaceSearchInput();
}



function monahingaLooksLikeStreetAddress(query) {
  const q = String(query || '').trim();
  return /\d/.test(q) && /(street|st\b|road|rd\b|route|rt\b|sr\b|state|highway|hwy|pa[-\s]*\d+|us[-\s]*\d+)/i.test(q);
}

function monahingaAddressRouteToken(query) {
  const q = String(query || '').toUpperCase();
  const sr = q.match(/\bSR\s*([0-9]+)\b/);
  if (sr) return sr[1];
  const pa = q.match(/\bPA[-\s]*([0-9]+)\b/);
  if (pa) return pa[1];
  const route = q.match(/\bROUTE\s*([0-9]+)\b/);
  if (route) return route[1];
  const stateRoute = q.match(/\bSTATE\s+ROUTE\s*([0-9]+)\b/);
  if (stateRoute) return stateRoute[1];
  return '';
}

function monahingaRejectWrongStreetHit(query, label) {
  const q = String(query || '').toUpperCase();
  const name = String(label || '').toUpperCase();
  const house = (q.match(/\b\d{2,6}\b/) || [''])[0];
  const route = monahingaAddressRouteToken(q);

  if (house && route) {
    const hasHouse = name.includes(house);
    const hasRoute = name.includes(route) || name.includes('STATE ROUTE') || name.includes('ROUTE') || name.includes('PA-') || name.includes('PA ');
    if (!hasHouse && !hasRoute) return true;
  }
  return false;
}

async function monahingaFetchArcgisAddressHit(query) {
  if (!monahingaLooksLikeStreetAddress(query)) return null;

  const variants = (typeof monahingaAddressSearchVariants === 'function')
    ? monahingaAddressSearchVariants(query)
    : [String(query || '')];

  for (const candidate of variants) {
    const url = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?f=json&maxLocations=5&countryCode=USA&outFields=*&SingleLine=' + encodeURIComponent(candidate);
    try {
      const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (!res.ok) continue;
      const data = await res.json();
      const candidates = Array.isArray(data && data.candidates) ? data.candidates : [];
      for (const item of candidates) {
        const loc = item.location || {};
        const lon = Number(loc.x);
        const lat = Number(loc.y);
        const label = String(item.address || candidate);
        const score = Number(item.score || 0);
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
        if (!pointLooksLower48(lat, lon)) continue;
        if (score < 70) continue;
        if (monahingaRejectWrongStreetHit(query, label)) continue;
        return {
          lat: lat,
          lon: lon,
          display_name: label,
          used_query: candidate,
          score: score,
          source: 'ArcGIS World Geocoder'
        };
      }
    } catch (e) {
      // Keep trying variants / fallback geocoders.
    }
  }
  return null;
}

function monahingaApplyAddressHit(hit, originalQuery) {
  const lat = Number(hit.lat);
  const lon = Number(hit.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return false;
  if (!pointLooksLower48(lat, lon)) return false;

  if (searchMarker) map.removeLayer(searchMarker);
  searchMarker = L.marker([lat, lon]).addTo(map);
  const name = monahingaSafeSearchLabel(hit.display_name, originalQuery, 'Address match');
  searchMarker.bindPopup(name).openPopup();
  map.setView([lat, lon], 16);

  setSearchMeta('Found: ' + name + '. Source: ' + String(hit.source || 'address geocoder') + '. Draw your bbox around the property/terrain. Exact private address is not retained in the search box.');
  setStatus('Place found. The map moved to the searched area; now draw the bbox.');
  monahingaScrubPlaceSearchInput();
  return true;
}


async function searchPlace() {
  const input = document.getElementById('place_search');
  const query = String(input && input.value || '').trim();
  if (!query) {
    setStatus('Type an address, town, road, or landmark first.');
    return;
  }
  const variants = monahingaAddressSearchVariants(query);
  setStatus('Searching for place... Please wait.');
  setSearchMeta(monahingaIsAddressLikeForPrivacy(query) ? 'Searching rural road/address variants...' : 'Searching for "' + query + '" with rural road variants...');
  try {
    const arcgisAddressHit = await monahingaFetchArcgisAddressHit(query);
    if (arcgisAddressHit && monahingaApplyAddressHit(arcgisAddressHit, query)) {
      return;
    }
    const knownAddressHit = await monahingaFetchKnownAddressLookup(query);
    if (knownAddressHit) {
      monahingaApplyKnownAddressLookup(knownAddressHit, query);
      return;
    }
    const parcelLookupHit = await monahingaFetchParcelAddressLookup(query);
    if (parcelLookupHit) {
      monahingaApplyParcelAddressLookup(parcelLookupHit, query);
      return;
    }
    let hit = null;
    let usedQuery = '';
    let searched = 0;
    for (const candidate of variants) {
      searched += 1;
      const results = await monahingaFetchSearchResults(candidate);
      hit = monahingaPickLower48SearchHit(results);
      if (hit) {
        usedQuery = candidate;
        break;
      }
    }

    if (!hit) {
      throw new Error('No matching place found after trying ' + String(searched) + ' address variant(s). Try State Route, PA-44, Route 44, town, county, and ZIP spelling.');
    }

    const lat = Number(hit.lat);
    const lon = Number(hit.lon);
    if (!pointLooksLower48(lat, lon)) throw new Error('Place was found, but it falls outside the lower-48 hunting footprint.');
    if (searchMarker) map.removeLayer(searchMarker);
    searchMarker = L.marker([lat, lon]).addTo(map);
    const name = monahingaSafeSearchLabel(hit.display_name || usedQuery, query, 'Search match');
    searchMarker.bindPopup(name).openPopup();

    const isAddressLike = /\d/.test(query);
    if (isAddressLike) {
      map.setView([lat, lon], 16);
    } else if (Array.isArray(hit.boundingbox) && hit.boundingbox.length === 4) {
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

    setSearchMeta('Found: ' + name + '. Draw your bbox around the terrain you want to hunt. Exact private address is not retained in the search box.');
    setStatus('Place found. The map jumped to the searched location; now draw the hunt box.');
    monahingaScrubPlaceSearchInput();
  } catch (err) {
    setSearchMeta('Search failed after trying rural address variants. You can still paste coordinates or draw the box manually.');
    setStatus('FAILED\\n\\n' + String(err && err.message ? err.message : err));
  }
}

function clearDrawnBox() {
  drawLayer.clearLayers();
  activeRect = null;
  clearStoredSelectionPolygon();
  document.getElementById('bbox_readout').textContent = 'not drawn yet';
  document.getElementById('bbox_hint').className = 'inline-warning info';
  document.getElementById('bbox_hint').textContent = 'Draw a BBox rectangle or polygon fully inside the lower 48. Use Clear Current Selection as the reliable reset.';
  applyRegionIdentityFromCurrent();
  setStatus('Current selection cleared. Draw a new BBox rectangle or polygon when ready.');
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

function applySelectionLayer(layer, fit=true) {
  drawLayer.clearLayers();
  activeRect = layer;
  drawLayer.addLayer(activeRect);
  applyBBoxToForm(activeRect.getBounds());
  updateBBoxTextFromCurrent();
  storeSelectionPolygonFromLayer(activeRect);
  if (fit) map.fitBounds(activeRect.getBounds(), { padding:[20,20] });
}

function selectedShapeName(layer) {
  if (layer instanceof L.Polygon && !(layer instanceof L.Rectangle)) return 'Polygon';
  return 'BBox rectangle';
}

function drawRectangleFromBounds(bounds, fit=true) {
  clearStoredSelectionPolygon();
  const rect = L.rectangle(bounds, { color:'#a8f183', weight:2, fillOpacity:0.08 });
  applySelectionLayer(rect, fit);
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

// MONAHINGA_SEND_SELECTION_POLYGON_2026_05_06
function selectionPolygonForPayload(bounds) {
  if (!activeRect) return null;
  if (!(activeRect instanceof L.Polygon) || activeRect instanceof L.Rectangle) return null;

  const rings = activeRect.getLatLngs();
  const ring = Array.isArray(rings) && Array.isArray(rings[0]) ? rings[0] : [];
  if (!ring || ring.length < 3) return null;

  const minLon = Number(bounds.minLon);
  const minLat = Number(bounds.minLat);
  const maxLon = Number(bounds.maxLon);
  const maxLat = Number(bounds.maxLat);
  const width = maxLon - minLon;
  const height = maxLat - minLat;

  if (!Number.isFinite(width) || !Number.isFinite(height) || width === 0 || height === 0) return null;

  const points = ring
    .map((pt) => {
      const lng = Number(pt.lng);
      const lat = Number(pt.lat);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
      const x = (lng - minLon) / width;
      const y = (lat - minLat) / height;
      if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
      return [
        Math.max(0, Math.min(1, x)),
        Math.max(0, Math.min(1, y))
      ];
    })
    .filter(Boolean);

  return points.length >= 3 ? points : null;
}

// MONAHINGA_FINAL_POLYGON_STORE_2026_05_06
function polygonStoreEl() {
  return document.getElementById('selection_polygon_json');
}

function clearStoredSelectionPolygon() {
  const el = polygonStoreEl();
  if (el) el.value = '';
}

function polygonBoundsObjectFromLayer(layer) {
  const b = layer.getBounds();
  const sw = b.getSouthWest();
  const ne = b.getNorthEast();
  return {
    minLon: Number(sw.lng),
    minLat: Number(sw.lat),
    maxLon: Number(ne.lng),
    maxLat: Number(ne.lat)
  };
}

function selectionPolygonForLayer(layer) {
  if (!layer) return null;
  if (!(layer instanceof L.Polygon) || layer instanceof L.Rectangle) return null;

  const bounds = polygonBoundsObjectFromLayer(layer);
  const width = bounds.maxLon - bounds.minLon;
  const height = bounds.maxLat - bounds.minLat;
  if (!Number.isFinite(width) || !Number.isFinite(height) || width === 0 || height === 0) return null;

  const rings = layer.getLatLngs();
  const ring = Array.isArray(rings) && Array.isArray(rings[0]) ? rings[0] : [];
  if (!ring || ring.length < 3) return null;

  const points = ring.map((pt) => {
    const lng = Number(pt.lng);
    const lat = Number(pt.lat);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

    return [
      Math.max(0, Math.min(1, (lng - bounds.minLon) / width)),
      Math.max(0, Math.min(1, (lat - bounds.minLat) / height))
    ];
  }).filter(Boolean);

  return points.length >= 3 ? points : null;
}

function storeSelectionPolygonFromLayer(layer) {
  const el = polygonStoreEl();
  if (!el) return;

  const points = selectionPolygonForLayer(layer);
  el.value = points ? JSON.stringify(points) : '';
}

function storedSelectionPolygonForPayload() {
  const el = polygonStoreEl();
  if (!el || !el.value) return null;

  try {
    const parsed = JSON.parse(el.value);
    if (!Array.isArray(parsed) || parsed.length < 3) return null;

    const points = parsed.map((pt) => {
      if (!Array.isArray(pt) || pt.length < 2) return null;
      const x = Number(pt[0]);
      const y = Number(pt[1]);
      if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
      return [
        Math.max(0, Math.min(1, x)),
        Math.max(0, Math.min(1, y))
      ];
    }).filter(Boolean);

    return points.length >= 3 ? points : null;
  } catch (err) {
    return null;
  }
}

function payloadFromForm() {
  monahingaApplySpeciesGate();
  const bounds = normalizeBoundsFromInputs();
  if (!bounds) throw new Error('Please enter or draw a valid bbox before running.');
  applyBBoxToForm(bounds);
  const payload = {
    min_lon: Number(document.getElementById('min_lon').value),
    min_lat: Number(document.getElementById('min_lat').value),
    max_lon: Number(document.getElementById('max_lon').value),
    max_lat: Number(document.getElementById('max_lat').value),
    width: Number(document.getElementById('width').value),
    height: Number(document.getElementById('height').value),
    wind_direction: String(document.getElementById('wind_direction').value || '').trim(),
    notes: String(document.getElementById('notes').value || '').trim(),
    mode: String(document.getElementById('mode').value || 'hunter').trim(),
    selected_species: document.getElementById('target_species')?.value || 'default',
    hunt_plan_window: String(document.getElementById('hunt_plan_window')?.value || 'now').trim(),
    hunt_plan_datetime: String(document.getElementById('hunt_plan_datetime')?.value || '').trim()
  };

  const selectionPolygon = storedSelectionPolygonForPayload() || selectionPolygonForPayload(bounds);
  if (selectionPolygon && selectionPolygon.length >= 3) {
    payload.selection_polygon = selectionPolygon;
  }

  const parcelGeoJson = parcelGeoJsonForPayload();
  if (parcelGeoJson) {
    payload.parcel_geojson = parcelGeoJson;
  }

  return payload;
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
  const layer = event.layer;
  applySelectionLayer(layer, true);
  const shapeName = selectedShapeName(layer);
  if (shapeName === 'Polygon') {
    setStatus('Polygon captured and stored. Page 2 should now show the exact polygon boundary while terrain remains BBox-stable.');
  } else {
    setStatus('BBox rectangle captured. The form fields now match the selected hunting box exactly.');
  }
});

map.on(L.Draw.Event.EDITED, function () {
  const layer = drawLayer.getLayers()[0];
  if (!layer) return;
  activeRect = layer;
  storeSelectionPolygonFromLayer(layer);
  applyBBoxToForm(layer.getBounds());
  updateBBoxTextFromCurrent();
  setStatus(selectedShapeName(layer) + ' edited. The form fields were updated from the current selection bounds.');
});

map.on(L.Draw.Event.DELETED, function () {
  activeRect = null;
  document.getElementById('bbox_readout').textContent = 'not drawn yet';
  setStatus('Selection cleared. Draw a new rectangle or polygon when ready.');
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
    monahingaApplySpeciesGate();
    monahingaUpdateSpeciesIdentityCard();
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




# MONAHINGA_FORCE_VISIBLE_DEMO_PARCEL_2026_05_06


# MONAHINGA_PARCEL_VIS_ENGINE_V1_2026_05_06


# MONAHINGA_CARRY_PARCEL_GEOJSON_PAGE1_2026_05_06


# MONAHINGA_REAL_PARCEL_IMPORT_VALIDATOR_V1_2026_05_06


# MONAHINGA_PARCEL_SOURCE_TRUTH_LABELS_V1_2026_05_06
