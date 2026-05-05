from __future__ import annotations

from string import Template

HTML_TEMPLATE = Template(r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Monahinga™ Command Surface</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {
  --bg:#03060b; --panel:rgba(6,10,16,.90); --line:rgba(255,255,255,.08); --text:#ece3d5; --muted:#9fb0bc;
  --green:#aef186; --gold:#f3d58a; --amber:#daab63; --shadow:0 24px 80px rgba(0,0,0,.46);
}
*{box-sizing:border-box} html,body{height:100%}
body{margin:0;font-family:Segoe UI,Arial,sans-serif;color:var(--text);background:linear-gradient(180deg,#0a1320 0%, #04070c 28%, #020409 100%);overflow-x:hidden;--terrain-wallpaper-image:linear-gradient(180deg,#0a1320 0%,#03060b 100%);--terrain-wallpaper-opacity:.18;--terrain-wallpaper-saturate:1.02;--terrain-wallpaper-contrast:1.00;--terrain-atmo-warm:rgba(243,213,138,.08);--terrain-atmo-cool:rgba(111,179,218,.10);--terrain-atmo-green:rgba(174,241,134,.10)}
body::before{content:'';position:fixed;inset:-24px;z-index:0;pointer-events:none;background-image:linear-gradient(180deg,rgba(3,6,11,.42),rgba(3,6,11,.82)),radial-gradient(circle at 18% 18%,var(--terrain-atmo-warm),transparent 34%),radial-gradient(circle at 84% 18%,var(--terrain-atmo-cool),transparent 38%),radial-gradient(circle at 50% 90%,var(--terrain-atmo-green),transparent 46%),var(--terrain-wallpaper-image);background-size:cover,cover,cover,cover,cover;background-position:center;filter:blur(13px) saturate(var(--terrain-wallpaper-saturate)) contrast(var(--terrain-wallpaper-contrast));transform:scale(1.06);opacity:var(--terrain-wallpaper-opacity);transition:opacity .55s ease, filter .55s ease}
body::after{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(circle at 50% 0%,rgba(255,232,174,.09),transparent 24%),linear-gradient(90deg,rgba(3,6,11,.86) 0%,rgba(3,6,11,.28) 34%,rgba(3,6,11,.18) 66%,rgba(3,6,11,.88) 100%),linear-gradient(180deg,rgba(3,6,11,.12) 0%,rgba(3,6,11,.76) 100%)}
body.terrain-wallpaper-ready{--terrain-wallpaper-opacity:.30}
body.theme-appalachian{--terrain-atmo-warm:rgba(243,213,138,.07);--terrain-atmo-cool:rgba(93,138,126,.08);--terrain-atmo-green:rgba(91,174,88,.12);--terrain-wallpaper-saturate:1.08;--terrain-wallpaper-contrast:1.03}
body.theme-mountain{--terrain-atmo-warm:rgba(231,208,168,.07);--terrain-atmo-cool:rgba(143,208,255,.14);--terrain-atmo-green:rgba(112,154,128,.07);--terrain-wallpaper-saturate:1.00;--terrain-wallpaper-contrast:1.10}
body.theme-plains{--terrain-atmo-warm:rgba(239,199,123,.14);--terrain-atmo-cool:rgba(141,193,239,.08);--terrain-atmo-green:rgba(200,221,122,.09);--terrain-wallpaper-saturate:1.02;--terrain-wallpaper-contrast:1.02}
body.theme-southwoods{--terrain-atmo-warm:rgba(214,178,109,.09);--terrain-atmo-cool:rgba(124,171,186,.08);--terrain-atmo-green:rgba(104,194,124,.13);--terrain-wallpaper-saturate:1.10;--terrain-wallpaper-contrast:1.03}
button{font:inherit}
.shell{position:relative;z-index:1;padding:10px 12px 12px; min-height:100vh}
.chrome{position:relative;border-radius:24px;border:1px solid rgba(255,255,255,.08);background:linear-gradient(180deg, rgba(10,17,26,.88), rgba(3,6,11,.93));box-shadow:var(--shadow);overflow:hidden}
.topbar{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;padding:10px 12px 8px;border-bottom:1px solid rgba(255,255,255,.06)}
.brandline{display:flex;align-items:center;gap:12px;font-size:12px;letter-spacing:.18em;color:#9eb0bf;text-transform:uppercase}
h1{margin:6px 0 3px;font-size:30px;line-height:1.02}.sub{color:var(--muted);font-size:14px;max-width:720px}
.pills{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end;max-width:720px}.pill{padding:7px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.03);font-size:12px;color:#dce5ea}
.layout{display:grid;grid-template-columns:280px minmax(0,1fr) 320px;min-height:calc(100vh - 92px);align-items:start}
.layout.visual-focus{grid-template-columns:280px minmax(0,1fr) 0px}
.layout.visual-focus .right{display:none}
.visual-focus .center{padding-right:10px}
.visual-focus .scene-shell{height:min(80vh,900px);min-height:640px}
.visual-focus-toggle{position:absolute;right:14px;top:14px;z-index:8;display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:12px;border:1px solid rgba(255,255,255,.14);background:rgba(8,15,25,.86);color:var(--text);cursor:pointer;backdrop-filter:blur(10px);box-shadow:0 8px 26px rgba(0,0,0,.28)}
.visual-focus-toggle:hover{background:rgba(20,30,44,.96)}
.scene-orientation-note{position:absolute;left:12px;top:54px;z-index:5;max-width:430px;padding:8px 10px;border-radius:12px;border:1px solid rgba(143,208,255,.22);background:rgba(8,15,25,.72);backdrop-filter:blur(10px);font-size:11px;line-height:1.35;color:#dceaf2}
.scene-orientation-note strong{color:#eef8ff}
.left{padding:10px;border-right:1px solid rgba(255,255,255,.05);display:flex;flex-direction:column;gap:10px}.center{padding:10px;min-width:0}.right{padding:10px 10px 10px 0;min-height:0}
.block{padding:10px;border-radius:14px;border:1px solid rgba(255,255,255,.08);background:rgba(4,8,14,.78)}.block h3{margin:0 0 6px;font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:#9fb1bf}
.status-block strong{display:block;margin-bottom:4px}.tone-strong{border-color:rgba(174,241,134,.22);background:rgba(174,241,134,.08)}.tone-partial{border-color:rgba(243,213,138,.18);background:rgba(243,213,138,.06)}.tone-none{border-color:rgba(255,255,255,.10);background:rgba(255,255,255,.03)}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:8px}.kv div{padding:8px 10px;border-radius:12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.05)}.kv label{display:block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#90a4b2;margin-bottom:3px}
.note{color:#c4d0d8;line-height:1.38;font-size:13px}.layer-stack,.mode-stack{display:flex;flex-wrap:wrap;gap:8px}
.layer-btn,.mode-btn{border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.04);color:var(--text);padding:8px 10px;border-radius:12px;cursor:pointer}.layer-btn.active,.mode-btn.active{background:rgba(174,241,134,.14);border-color:rgba(174,241,134,.24)}
.slider-group{margin-top:10px}.slider-group label{display:block;font-size:11px;color:#9fb1bf;margin-bottom:5px;text-transform:uppercase;letter-spacing:.12em}.slider-group input{width:100%}
.scene-shell{position:relative;height:min(74vh,820px);min-height:600px;border-radius:22px;overflow:hidden;border:1px solid rgba(255,255,255,.08);background:linear-gradient(180deg, #243b4f 0%, #132331 18%, #08131d 52%, #040a12 100%);box-shadow:var(--shadow)}
#viewer{position:absolute;inset:0} #viewer canvas{display:block;width:100%;height:100%} #viewer .error-card{position:absolute;left:16px;right:16px;top:16px;padding:14px 16px;border-radius:16px;background:rgba(60,12,16,.92);border:1px solid rgba(255,120,120,.35);color:#ffd8d8;z-index:9;white-space:pre-wrap}
.hud-strip{position:absolute;left:12px;right:84px;bottom:0px;display:flex;gap:8px;flex-wrap:wrap;z-index:4;opacity:0.92}
.hud-card{padding:6px 8px;border-radius:12px;border:1px solid rgba(255,255,255,.08);background:rgba(5,10,16,.72);backdrop-filter:blur(10px);max-width:min(30%,260px);font-size:12px}
.side-rail{width:100%;padding:10px;border-radius:18px;border:1px solid rgba(255,255,255,.075);background:linear-gradient(180deg, rgba(4,8,14,.88), rgba(3,6,11,.94));box-shadow:0 18px 56px rgba(0,0,0,.36);height:min(74vh,820px);overflow:auto}.primary-box{padding:10px;border-radius:16px;border:1px solid rgba(173,241,129,.14);background:linear-gradient(180deg, rgba(173,241,129,.055), rgba(173,241,129,.018));margin-bottom:8px}
.primary-title{font-size:10px;letter-spacing:.16em;color:#a4b7c4;text-transform:uppercase;margin-bottom:6px}.primary-name{font-size:20px;line-height:1.04;font-weight:700;margin-bottom:6px}.primary-reason{color:#c8d2d9;line-height:1.28;font-size:13px}.trust-tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.trust-tag{padding:6px 9px;border-radius:999px;border:1px solid rgba(174,241,134,.18);background:rgba(174,241,134,.07);color:#d7ecd7;font-size:11px;letter-spacing:.04em;line-height:1;white-space:nowrap}.trust-tag-primary{border-color:rgba(174,241,134,.28);background:rgba(174,241,134,.12);color:#eef8e5;font-weight:600}.trust-tag-support{border-color:rgba(174,241,134,.14);background:rgba(174,241,134,.05);color:#cfe3cf}.trust-tag-caution{border-color:rgba(243,213,138,.24);background:rgba(243,213,138,.08);color:#f0ddad}
.meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.chip{padding:6px 8px;border-radius:10px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.03);font-size:11px;color:#dae0e5}.section-kicker{font-size:10px;letter-spacing:.16em;color:#9fb2bf;text-transform:uppercase;margin:8px 2px 6px}
.row{display:grid;grid-template-columns:42px 1fr 52px;gap:10px;padding:10px;border:1px solid rgba(255,255,255,.07);border-radius:16px;background:rgba(255,255,255,.02);margin-bottom:8px}.row-button{width:100%;text-align:left;color:var(--text);cursor:pointer}.row-button.active,.row-button:hover{border-color:rgba(174,241,134,.24);background:rgba(174,241,134,.08)}.row-rank{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;font-size:22px;font-weight:700;background:rgba(255,255,255,.05)}.row-tier{font-size:9px;letter-spacing:.16em;color:#9eb1be;margin-bottom:4px}.row-title{font-size:15px;font-weight:700;line-height:1.14;margin-bottom:4px}.row-reason{color:#b7c2ca;line-height:1.28;font-size:12px}.row-score{font-size:20px;font-weight:700;align-self:center;text-align:right;color:#efe6d8}
.intel-row{padding:6px 8px;border-radius:10px;border:1px solid rgba(255,255,255,.07);background:rgba(255,255,255,.02);margin-bottom:5px}
.intel-row.provider-ok{border-color:rgba(174,241,134,.25);background:rgba(174,241,134,.06)}
.intel-row.provider-empty{border-color:rgba(243,213,138,.25);background:rgba(243,213,138,.06)}
.intel-row.provider-failed{border-color:rgba(255,120,120,.35);background:rgba(120,20,20,.35)}
.intel-row strong{display:block;font-size:12px;margin-bottom:2px}
.intel-row span{color:#b7c2ca;font-size:11px;line-height:1.22}
.micro-copy{display:block;color:#88a0af;font-size:11px;line-height:1.35;margin-top:5px}.hud-card .label{display:block;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#93a8b6;margin-bottom:4px}.hud-card button,.copy-btn{margin-top:6px;padding:6px 8px;border-radius:10px;border:1px solid rgba(255,255,255,.10);background:rgba(255,255,255,.05);color:var(--text);cursor:pointer}.hud-card button:hover,.copy-btn:hover{background:rgba(174,241,134,.12)}
ul{margin:8px 0 0 18px;padding:0;color:#c4cfd6}
.legend{position:absolute;top:10px;left:10px;z-index:4;display:flex;gap:8px;flex-wrap:wrap;max-width:72%}.legend .chip{background:rgba(8,15,25,.78);backdrop-filter:blur(10px)}.cover-key{display:none;gap:8px;flex-wrap:wrap}.cover-key.visible{display:flex}.cover-chip{display:inline-flex;align-items:center;gap:8px}.cover-swatch{width:14px;height:14px;border-radius:999px;display:inline-block;border:1px solid rgba(255,255,255,.18)}.cover-swatch-dense{background:#0b6a2f}.cover-swatch-moderate{background:#b8e03a}.cover-swatch-open{background:#f0c36a}.cover-swatch-bowl{background:#2b8ea6}.focus-read-hint{display:none;margin-top:8px;font-size:12px;color:#a7b7c0;line-height:1.35}.focus-read-hint.visible{display:block}
.scene-shell::before{content:'';position:absolute;inset:0;background:linear-gradient(180deg, rgba(110,156,191,.26) 0%, rgba(71,115,148,.14) 16%, rgba(18,31,44,0) 42%);pointer-events:none;z-index:1}.scene-shell::after{content:'';position:absolute;inset:0;background:radial-gradient(circle at 50% 10%, rgba(255,233,176,.18), transparent 20%),radial-gradient(circle at 50% 14%, rgba(187,220,156,.10), transparent 34%),linear-gradient(180deg, rgba(44,68,32,.06), transparent 46%);pointer-events:none;z-index:1}
.command-tools{margin-top:8px;display:flex;flex-direction:column;align-items:center;gap:7px}.command-tools-row{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}.command-tool-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:8px 10px;border-radius:12px;border:1px solid rgba(255,255,255,.10);background:rgba(8,15,25,.82);color:var(--text);text-decoration:none;cursor:pointer;backdrop-filter:blur(10px)}.command-tool-btn:hover{background:rgba(20,30,44,.92)}.command-tool-btn.active{background:rgba(174,241,134,.16);border-color:rgba(174,241,134,.36);box-shadow:0 0 0 1px rgba(174,241,134,.10) inset}.scene-tools{position:absolute;top:10px;right:10px;z-index:5;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:34%}.scene-tool-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:12px;border:1px solid rgba(255,255,255,.1);background:rgba(8,15,25,.82);color:var(--text);text-decoration:none;cursor:pointer;backdrop-filter:blur(10px)}.scene-tool-btn:hover{background:rgba(20,30,44,.92)}.scene-tool-btn.active{background:rgba(174,241,134,.16);border-color:rgba(174,241,134,.36);box-shadow:0 0 0 1px rgba(174,241,134,.10) inset}.approach-hud{display:none;border-color:rgba(174,241,134,.20);background:rgba(5,18,12,.74)}.approach-hud.visible{display:block}.approach-risk-low{color:#bdf6a7}.approach-risk-caution{color:#f3d58a}.approach-risk-high{color:#ffb08e}.cursor-hud{position:absolute;right:10px;bottom:78px;z-index:5;min-width:260px;max-width:330px;padding:9px 11px;border-radius:12px;border:1px solid rgba(255,255,255,.10);background:rgba(8,15,25,.84);color:#eef3f7;font-size:12px;line-height:1.4;backdrop-filter:blur(10px);pointer-events:none}.cursor-hud strong{display:block;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#9fd7ff;margin-bottom:4px}.cursor-hud .micro-copy{margin-top:4px}

body.theme-appalachian{--region-accent:#7fd871;--region-cool:#6fb3da;--region-warm:#f0c47f}
body.theme-mountain{--region-accent:#8fd0ff;--region-cool:#9ab4dd;--region-warm:#e7d0a8}
body.theme-plains{--region-accent:#c8dd7a;--region-cool:#8dc1ef;--region-warm:#efc77b}
body.theme-southwoods{--region-accent:#87d49d;--region-cool:#7cabba;--region-warm:#d6b26d}
body.theme-default{--region-accent:#aef186;--region-cool:#83c9ff;--region-warm:#f3d58a}
.chrome::before{
  content:'';position:absolute;inset:0;pointer-events:none;
  background:
    radial-gradient(circle at 14% 10%, rgba(255,255,255,.03), transparent 18%),
    radial-gradient(circle at 84% 12%, rgba(255,255,255,.02), transparent 22%);
}
.topbar{position:relative}
.region-stack{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.region-chip{
  padding:8px 11px;border-radius:999px;
  border:1px solid rgba(255,255,255,.10);background:rgba(255,255,255,.04);
  color:#e9efe2;font-size:12px
}
.region-chip strong{color:var(--region-warm)}
.region-story{
  margin-top:10px;max-width:760px;padding:10px 12px;border-radius:14px;
  border:1px solid rgba(255,255,255,.08);
  background:rgba(255,255,255,.03);color:#d0dbe2;font-size:13px;line-height:1.45
}
.scene-shell.region-appalachian{
  background:linear-gradient(180deg, #304a5c 0%, #193228 22%, #0a1c1d 58%, #060c12 100%);
}
.scene-shell.region-mountain{
  background:linear-gradient(180deg, #344b66 0%, #182536 24%, #0b1420 58%, #05090f 100%);
}
.scene-shell.region-plains{
  background:linear-gradient(180deg, #51728a 0%, #36473a 22%, #14211c 56%, #070b10 100%);
}
.scene-shell.region-southwoods{
  background:linear-gradient(180deg, #365468 0%, #20372d 24%, #0d1816 58%, #05090d 100%);
}
.scene-shell::before{mix-blend-mode:screen}
.scene-shell::after{opacity:.95}
.atmo-note{
  margin-top:8px;font-size:12px;line-height:1.42;color:#b9c8cf;
}

.pin-help{font-size:12px;color:#9fb0bc;margin-top:8px}
.decision-card{padding:12px 12px 13px;border-radius:16px;border:1px solid rgba(255,209,102,.28);background:linear-gradient(180deg, rgba(255,209,102,.14), rgba(255,209,102,.05));box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
.decision-label{display:block;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#ffd166;margin-bottom:6px}
.decision-title{display:block;font-size:22px;line-height:1.05;font-weight:800;color:#fff3d6;margin-bottom:4px}
.decision-sub{display:block;font-size:13px;line-height:1.35;color:#e4d8bd}
.exec-decision{padding:8px 9px;border-radius:12px;border:1px solid rgba(0,217,255,.20);background:linear-gradient(180deg, rgba(0,217,255,.10), rgba(0,217,255,.03));margin-bottom:8px}
.exec-decision strong{display:block;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#8fe7f6;margin-bottom:4px}
.exec-decision span{display:block;font-size:18px;line-height:1.1;font-weight:800;color:#effcff;margin-bottom:3px}
.exec-decision em{display:block;font-style:normal;color:#cae6ec;font-size:12px;line-height:1.35}
.viewer-micro-note{margin-top:6px;font-size:11px;line-height:1.35;color:#9eb0bf}
.game-context-card{margin-top:8px;padding:9px 10px;border-radius:14px;border:1px solid rgba(127,216,113,.18);background:linear-gradient(180deg, rgba(127,216,113,.10), rgba(127,216,113,.03))}
.game-context-card h3{margin-bottom:6px}
.game-context-kicker{display:block;font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#9fe693;margin-bottom:5px}
.game-context-primary{display:block;font-size:16px;line-height:1.15;font-weight:800;color:#eff8e5;margin-bottom:4px}
.game-context-secondary{display:block;font-size:12px;line-height:1.4;color:#ccdbcf}
.field-map-card{margin-bottom:8px;border-color:rgba(143,208,255,.26);background:linear-gradient(180deg,rgba(8,18,28,.88),rgba(4,8,14,.88))}
.field-map-wrap{position:relative;width:100%;aspect-ratio:1/1;border-radius:14px;overflow:hidden;border:1px solid rgba(255,255,255,.10);background:radial-gradient(circle at 50% 45%,rgba(174,241,134,.10),transparent 34%),linear-gradient(180deg,rgba(16,34,46,.95),rgba(5,14,20,.96))}
.field-map-svg{position:absolute;inset:0;width:100%;height:100%;display:block}
.field-map-grid{stroke:rgba(255,255,255,.08);stroke-width:.35}
.field-map-path{fill:none;stroke:#aef186;stroke-width:1.15;stroke-dasharray:2 1.5;opacity:.92}
.field-map-path-secondary{fill:none;stroke:rgba(255,255,255,.18);stroke-width:.7;stroke-dasharray:1.5 2}
.field-map-ring-primary{fill:rgba(245,211,138,.16);stroke:#f5d38a;stroke-width:1.4}
.field-map-ring-alt{fill:rgba(111,179,218,.14);stroke:#6fb3da;stroke-width:1.1}
.field-map-ring-third{fill:rgba(218,171,99,.13);stroke:#daab63;stroke-width:1.0}
.field-map-base{fill:#5ec8ff;stroke:#eef9ff;stroke-width:.9}
.field-map-entry{fill:#ffb347;stroke:#fff0d2;stroke-width:.9}
.field-map-label{fill:#f7ead8;font-size:4px;font-weight:800;font-family:Segoe UI,Arial,sans-serif;text-shadow:0 1px 2px rgba(0,0,0,.75)}
.field-map-small{fill:#b9c8cf;font-size:3px;font-weight:700;font-family:Segoe UI,Arial,sans-serif}
.field-map-compass{position:absolute;right:8px;top:8px;display:grid;place-items:center;width:42px;height:42px;border-radius:999px;border:1px solid rgba(255,255,255,.16);background:rgba(3,8,13,.68);font-weight:900;color:#eef8ff;font-size:12px}
.field-map-legend{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:7px;font-size:10px;color:#c4d0d8}
.field-map-legend span{display:flex;align-items:center;gap:5px}
.field-map-dot{width:9px;height:9px;border-radius:999px;display:inline-block}
/* monahinga-pass-tiny-h-left-focus
   Goal: simplify LEFT panel to only actionable controls
   - keeps wind, terrain toggles, sliders
   - hides descriptive clutter
*/
.left .note,
.left .block p,
.left .block span{
  display:none !important;
}

.left .block{
  padding:8px !important;
}

.left .block:nth-of-type(1),
.left .block:nth-of-type(2),
.left .block:nth-of-type(3){
  display:block !important;
}

.left .block:nth-of-type(n+4){
  display:none !important;
}

/* Make controls tighter */
.left button,
.left .chip{
  font-size:11px !important;
  padding:6px 8px !important;
}

@media (max-width:760px){
  .left{
    display:none !important;
  }
}

/* monahinga-pass-tiny-g-clean-header
   Safe visual-only page-2 header cleanup:
   - removes trust-reducing explanatory clutter from the command surface header
   - keeps launch/back controls and all active tools
   - does NOT touch scoring, species logic, PAD-US, terrain rendering, backend, or Render setup
   - remove this block to bring the hidden header copy back
*/
.sub,
.region-stack,
.region-story,
.topbar div[style*="AI-optimized guidance"],
.topbar div[style*="Huntability warning"]{
  display:none !important;
}
.topbar{
  padding:7px 10px 6px !important;
  align-items:flex-start !important;
}
.brandline{
  font-size:9px !important;
  letter-spacing:.16em !important;
}
h1{
  font-size:24px !important;
  line-height:1.02 !important;
  margin:3px 0 0 !important;
}
.command-tools{
  margin-top:0 !important;
  gap:6px !important;
}
.command-tools-row{
  justify-content:flex-end !important;
}
.command-tool-btn,
.visual-focus-toggle,
#saveViewHelpBtn{
  font-size:12px !important;
}
@media (max-width:760px){
  .topbar{
    padding:6px !important;
  }
  .brandline{
    display:none !important;
  }
  h1{
    font-size:18px !important;
  }
  .command-tools-row{
    display:grid !important;
    grid-template-columns:1fr 1fr !important;
    width:100% !important;
  }
}

/* monahinga-pass-tiny-d-focus-view
   Safe visual-only focus pass:
   - reduces header/side clutter on page 2
   - keeps the engine, scoring, species, PAD-US, and terrain code untouched
   - hides only presentation layers; remove this block to restore them
*/
.sub,
.region-stack,
.region-story,
.topbar div[style*="AI-optimized guidance"],
.topbar div[style*="Huntability warning"]{
  display:none !important;
}
.topbar{
  padding:8px 12px 6px !important;
  align-items:flex-start !important;
}
h1{
  font-size:26px !important;
  margin:4px 0 0 !important;
}
.command-tools{
  margin-top:2px !important;
}
.layout{
  grid-template-columns:230px minmax(0,1fr) 250px !important;
}
.left{
  gap:8px !important;
}
.left .block{
  padding:8px !important;
}
.left .block:nth-of-type(3) .note,
.left .pin-help,
.left #focusReadHint,
.left .block:nth-of-type(4),
.left .block:nth-of-type(5),
.left .block:nth-of-type(6){
  display:none !important;
}
.scene-shell{
  height:min(78vh,880px) !important;
  min-height:640px !important;
}
.wildlife-atmo-layer{
  display:none !important;
}
.hud-strip{
  left:10px !important;
  right:10px !important;
  bottom:10px !important;
  width:auto !important;
  transform:none !important;
  max-height:92px !important;
  opacity:.86 !important;
}
.hud-card{
  max-width:220px !important;
  font-size:11px !important;
  padding:5px 7px !important;
}
.cursor-hud{
  display:none !important;
}
.right{
  font-size:12px !important;
}
.right .side-rail{
  padding:8px !important;
}
.right .primary-reason,
.right .trust-tags,
.right .meta,
.right .section-kicker,
.right .intel-row,
.right ul,
.right .mode-stack,
.right .row-reason{
  display:none !important;
}
.right .row{
  padding:7px !important;
  grid-template-columns:30px 1fr 38px !important;
  gap:6px !important;
  margin-bottom:6px !important;
}
.right .row-rank{
  width:30px !important;
  height:30px !important;
  font-size:15px !important;
}
.right .row-title{
  font-size:12px !important;
}
.right .row-score{
  font-size:15px !important;
}
@media (max-width:760px){
  .layout{
    display:block !important;
  }
  .left,
  .right{
    display:none !important;
  }
  .center{
    padding:6px !important;
  }
  .scene-shell{
    height:72vh !important;
    min-height:480px !important;
  }
  .hud-strip{
    display:none !important;
  }
}

/* monahinga-pass-tiny-b-mobile-header
   Safe visual-only mobile cleanup:
   - reduces page-2 header height on phone-sized screens
   - hides long explanatory copy on mobile only
   - keeps action buttons visible
   - does NOT alter terrain, scoring, PAD-US, species, or backend logic
*/
@media (max-width:760px){
  .topbar{
    display:block !important;
    padding:8px 8px 6px !important;
  }
  .brandline{
    font-size:9px !important;
    letter-spacing:.14em !important;
    margin-bottom:3px !important;
  }
  h1{
    font-size:20px !important;
    line-height:1.05 !important;
    margin:2px 0 6px !important;
  }
  .sub,
  .region-stack,
  .region-story{
    display:none !important;
  }
  .topbar div[style*="AI-optimized guidance"],
  .topbar div[style*="Huntability warning"]{
    display:none !important;
  }
  .command-tools{
    margin-top:6px !important;
    align-items:stretch !important;
  }
  .command-tools-row{
    display:grid !important;
    grid-template-columns:1fr 1fr !important;
    gap:7px !important;
    width:100% !important;
  }
  .command-tools-row .command-tool-btn,
  .command-tools-row .visual-focus-toggle,
  #saveViewHelpBtn{
    width:100% !important;
    min-height:40px !important;
    font-size:12px !important;
    padding:8px 7px !important;
  }
}

/* monahinga-pass-tiny-a-hide-top-clutter
   Safe visual-only cleanup:
   - hides developer/debug pills, legend chips, and orientation note
   - does NOT delete HTML
   - does NOT change terrain generation, scoring, PAD-US, species, or backend logic
   - remove this block to bring those visual items back
*/
.pills,
.legend,
.scene-orientation-note{
  display:none !important;
}

/* monahinga-pass-debug-clutter-cleanup */
.pills{
  display:none !important;
}
.scene-orientation-note{
  display:none !important;
}
.legend{
  display:none !important;
}
@media (max-width:760px){
  .topbar{
    padding-bottom:6px;
  }
  .scene-shell{
    margin-top:0;
  }
}

/* monahinga-pass-button-cleanup */
.command-tools-row .visual-focus-toggle{
  position:static;
  right:auto;
  top:auto;
  z-index:auto;
  box-shadow:none;
  min-height:38px;
}
.command-tools-row .command-back-link{
  min-height:38px;
  font-weight:700;
  border-color:rgba(243,213,138,.24);
  background:rgba(243,213,138,.10);
}
.command-tools-row .command-back-link:hover{
  background:rgba(243,213,138,.18);
}
.scene-tools[aria-hidden="true"]{
  display:none !important;
}

.wildlife-atmo-layer{position:absolute;inset:0;z-index:2;pointer-events:none;display:flex;justify-content:space-between;align-items:stretch;padding:76px 16px 108px;gap:18px}
.wildlife-atmo-panel{width:min(21%,248px);border-radius:18px;border:1px solid rgba(255,255,255,.065);background:linear-gradient(180deg, rgba(4,8,14,.44), rgba(3,6,11,.20));box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 14px 36px rgba(0,0,0,.18);backdrop-filter:blur(7px);overflow:hidden}
.wildlife-atmo-left{align-self:flex-start;padding:12px 13px 14px;min-height:112px;background:radial-gradient(circle at 20% 20%, rgba(243,213,138,.055), transparent 30%),linear-gradient(180deg, rgba(5,10,16,.50), rgba(5,10,16,.14))}
.wildlife-atmo-right{align-self:stretch;padding:9px;display:flex;flex-direction:column;gap:7px;background:radial-gradient(circle at 80% 10%, rgba(174,241,134,.045), transparent 26%),linear-gradient(180deg, rgba(5,10,16,.40), rgba(5,10,16,.12))}
.wildlife-kicker{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:#9fb1bd;margin-bottom:7px}.wildlife-region{font-size:17px;line-height:1.05;font-weight:800;color:#fff2d3}.wildlife-mood{margin-top:7px;color:#b5c3cb;font-size:11px;line-height:1.35}
.wildlife-card{position:relative;min-height:78px;padding:9px 9px 8px 46px;border-radius:14px;border:1px solid rgba(255,255,255,.065);background:linear-gradient(135deg, rgba(255,255,255,.045), rgba(255,255,255,.012));overflow:hidden}
.wildlife-card::before{content:'';position:absolute;left:-18px;bottom:-22px;width:68px;height:68px;border-radius:50%;background:radial-gradient(circle, rgba(243,213,138,.12), rgba(243,213,138,.02) 56%, transparent 70%)}
.wildlife-rank{position:absolute;left:10px;top:10px;font-size:18px;font-weight:900;color:rgba(255,243,214,.32)}.wildlife-name{font-size:14px;font-weight:900;color:#fff1d4;line-height:1.05}.wildlife-role{margin-top:3px;font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:#9fd6a0}.wildlife-motion{margin-top:5px;color:#c1ccd3;font-size:10.5px;line-height:1.24}.wildlife-methods{margin-top:5px;color:#d2c09a;font-size:9.5px;line-height:1.22}.wildlife-legal-note{margin-top:auto;padding:7px 8px;border-radius:12px;background:rgba(255,209,102,.045);border:1px solid rgba(255,209,102,.13);color:#d2c8aa;font-size:9.5px;line-height:1.32}
@media (max-width: 1280px){.wildlife-atmo-layer{position:relative;z-index:3;padding:8px 0 10px;display:grid;grid-template-columns:1fr}.wildlife-atmo-panel{width:100%}.wildlife-atmo-right{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}.wildlife-legal-note{grid-column:1 / -1}.scene-shell{overflow:auto}}
@media (max-width: 760px){.wildlife-atmo-layer{display:none}}
@media (max-width: 1280px) {.layout{grid-template-columns:1fr} .left{border-right:0;border-bottom:1px solid rgba(255,255,255,.05)} .right{padding:0 10px 10px} .scene-shell{height:min(60vh,620px);min-height:500px} .side-rail{height:auto;max-height:none}}

/* monahinga-pass-tiny-i-right-panel-cleanup
   Safe visual-only cleanup:
   - hides the current synthetic 2D map and field-anchor instruction card
   - restores the cursor terrain/GPS readout
   - keeps Hunter 2.0 Brain and ranked sit intelligence visible
   - does NOT touch terrain generation, scoring, species, PAD-US, backend, or Render
*/
#fieldAnchorGuide,
#fieldOrientationMap{
  display:none !important;
}
.cursor-hud{
  display:block !important;
  visibility:visible !important;
  opacity:.95 !important;
  right:14px !important;
  bottom:94px !important;
  z-index:20 !important;
  pointer-events:none !important;
}
@media (max-width:760px){
  #fieldAnchorGuide,
  #fieldOrientationMap{
    display:none !important;
  }
  .cursor-hud{
    display:block !important;
    left:10px !important;
    right:10px !important;
    bottom:10px !important;
    min-width:0 !important;
    max-width:none !important;
    font-size:11px !important;
    padding:8px 9px !important;
  }
}


/* monahinga-pass-tiny-k-decision-view-polish
   Low-risk visual polish:
   - aligns the live cursor/GPS readout with the bottom HUD rail
   - reduces how much the bottom widgets cover the 3D terrain
   - further compresses the right-side presentation without deleting intelligence
   - keeps all scoring, species, PAD-US, terrain rendering, backend, and Render logic untouched
*/
.hud-strip{
  left:12px !important;
  right:342px !important;
  bottom:10px !important;
  width:auto !important;
  transform:none !important;
  max-height:62px !important;
  min-height:0 !important;
  overflow:hidden !important;
  padding:6px !important;
  border-radius:12px !important;
  background:rgba(0,0,0,.44) !important;
  backdrop-filter:blur(7px) !important;
}
.hud-strip:hover{
  max-height:118px !important;
  overflow-y:auto !important;
}
.hud-card{
  max-width:210px !important;
  min-width:120px !important;
  font-size:10.5px !important;
  padding:5px 7px !important;
  line-height:1.18 !important;
}
.hud-card .label{
  font-size:8px !important;
  margin-bottom:2px !important;
}
.hud-card .micro-copy{
  display:none !important;
}
.hud-card button{
  padding:4px 6px !important;
  font-size:10px !important;
  margin-top:3px !important;
}
.cursor-hud{
  display:block !important;
  right:12px !important;
  bottom:10px !important;
  z-index:22 !important;
  min-width:310px !important;
  max-width:318px !important;
  min-height:62px !important;
  padding:7px 9px !important;
  font-size:10.5px !important;
  line-height:1.25 !important;
  opacity:.94 !important;
  background:rgba(8,15,25,.76) !important;
}
.cursor-hud strong{
  font-size:8.5px !important;
  margin-bottom:2px !important;
}
.cursor-hud .micro-copy{
  display:none !important;
}
#fieldAnchorGuide,
#fieldOrientationMap{
  display:none !important;
}
.right .side-rail{
  padding:8px !important;
}
.right .primary-reason{
  max-height:4.2em !important;
  overflow:hidden !important;
}
.right .trust-tags,
.right .meta,
.right .section-kicker,
.right .intel-row,
.right ul,
.right .mode-stack,
.right .row-reason{
  display:none !important;
}
.right .row{
  padding:7px !important;
  grid-template-columns:28px 1fr 38px !important;
  gap:6px !important;
  margin-bottom:5px !important;
}
.right .row-rank{
  width:28px !important;
  height:28px !important;
  font-size:14px !important;
}
.right .row-title{
  font-size:12px !important;
  line-height:1.08 !important;
}
.right .row-score{
  font-size:14px !important;
}
@media (max-width:1280px){
  .hud-strip{
    right:12px !important;
    bottom:78px !important;
  }
  .cursor-hud{
    bottom:10px !important;
    right:12px !important;
  }
}
@media (max-width:760px){
  .hud-strip{
    display:none !important;
  }
  .cursor-hud{
    left:8px !important;
    right:8px !important;
    bottom:8px !important;
    min-width:0 !important;
    max-width:none !important;
    min-height:0 !important;
    font-size:10.5px !important;
  }
}


/* monahinga-pass-tiny-n-right-panel-summary
   Safe visual-only pass:
   - hides the right panel without deleting it
   - adds a compact bottom decision summary using existing template values
   - keeps all intelligence/scoring data intact in the DOM and backend
   - does NOT touch terrain generation, species logic, PAD-US, backend, or Render
*/
.layout{
  grid-template-columns:210px minmax(0,1fr) 0px !important;
}
.right{
  display:none !important;
}
.center{
  padding-right:10px !important;
}
.scene-shell{
  height:min(82vh,920px) !important;
  min-height:670px !important;
}
.decision-summary-bar{
  /* MONAHINGA_VISUAL_FOCUS_PASS_2026_05_04
     Keep Best Sit / Why / When visible without covering the 3D terrain.
     This is layout-only; scoring, species logic, PAD-US, and terrain generation are untouched.
  */
  position:relative;
  z-index:6;
  display:grid;
  grid-template-columns:1fr 2fr 1fr;
  gap:8px;
  padding:8px;
  margin:0 0 8px 0;
  border-radius:14px;
  border:1px solid rgba(174,241,134,.18);
  background:rgba(3,10,12,.64);
  backdrop-filter:blur(9px);
  box-shadow:0 10px 30px rgba(0,0,0,.18);
}
.decision-summary-bar div{
  min-width:0;
  padding:6px 8px;
  border-radius:11px;
  background:rgba(255,255,255,.045);
  border:1px solid rgba(255,255,255,.07);
}
.decision-summary-bar span{
  display:block;
  font-size:8.5px;
  letter-spacing:.14em;
  text-transform:uppercase;
  color:#9eb1be;
  margin-bottom:2px;
}
.decision-summary-bar strong{
  display:block;
  font-size:11px;
  line-height:1.22;
  color:#f3eadb;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.decision-summary-bar div:nth-child(2) strong{
  white-space:normal;
  max-height:2.5em;
}
.hud-strip{
  bottom:10px !important;
  right:340px !important;
}
.cursor-hud{
  bottom:10px !important;
  right:12px !important;
}
@media (max-width:760px){
  .layout{
    display:block !important;
  }
  .left,
  .right{
    display:none !important;
  }
  .decision-summary-bar{
    grid-template-columns:1fr;
    gap:5px;
    padding:6px;
    margin-bottom:8px;
  }
  .decision-summary-bar div{
    padding:5px 7px;
  }
  .decision-summary-bar span{
    font-size:8px;
  }
  .decision-summary-bar strong{
    font-size:10.5px;
    white-space:normal;
    max-height:2.4em;
  }
  .hud-strip{
    display:none !important;
  }
  .cursor-hud{
    left:8px !important;
    right:8px !important;
    bottom:8px !important;
    max-width:none !important;
    min-width:0 !important;
  }
  .scene-shell{
    height:76vh !important;
    min-height:500px !important;
  }
}


/* MONAHINGA_HIDE_BEST_SIT_MOBILE_LEGIBILITY_2026_05_04
   Visual-only page-2 simplification.
   Hide the Best Sit summary tile because the primary sit is now the only visible sit marker.
   Improve legibility for desktop and phone use without touching scoring, terrain, PAD-US, species, or backend logic.
*/
.decision-summary-bar{
  grid-template-columns: minmax(0, 2fr) minmax(190px, .85fr) !important;
  gap: 10px !important;
  align-items: stretch !important;
}
.decision-summary-bar > div:first-child{
  display: none !important;
}
.decision-summary-bar span{
  font-size: clamp(12px, .9vw, 15px) !important;
  letter-spacing: .08em !important;
  font-weight: 950 !important;
}
.decision-summary-bar strong{
  font-size: clamp(15px, 1.05vw, 18px) !important;
  line-height: 1.28 !important;
  letter-spacing: -.018em !important;
  font-weight: 900 !important;
}
body{
  font-family: "Arial Narrow", "Roboto Condensed", "Inter Tight", "Segoe UI", Arial, sans-serif !important;
  text-rendering: geometricPrecision;
}
.title h1{
  font-size: clamp(28px, 2.1vw, 38px) !important;
  letter-spacing: -.045em !important;
}
.title .eyebrow{
  font-size: clamp(11px, .8vw, 13px) !important;
  letter-spacing: .16em !important;
}
.warning,.guidance{
  font-size: clamp(13px, .88vw, 16px) !important;
  line-height: 1.38 !important;
  font-weight: 850 !important;
  letter-spacing: -.012em !important;
}
.top-actions button,.nav-back{
  font-size: clamp(13px, .88vw, 16px) !important;
  line-height: 1.15 !important;
  font-weight: 950 !important;
  letter-spacing: -.015em !important;
  padding: 13px 15px !important;
}
.card .label,.metric .label,.panel-title{
  font-size: clamp(11px, .8vw, 14px) !important;
  letter-spacing: .10em !important;
  font-weight: 950 !important;
}
.card strong,.metric strong{
  font-size: clamp(17px, 1.1vw, 21px) !important;
  line-height: 1.15 !important;
  letter-spacing: -.025em !important;
  font-weight: 950 !important;
}
.toggle{
  font-size: clamp(12px, .82vw, 15px) !important;
  font-weight: 950 !important;
  padding: 8px 11px !important;
}
.cursor-hud,.hud-strip,.micro-copy{
  font-size: clamp(12px, .82vw, 15px) !important;
  line-height: 1.25 !important;
}
.scene-orientation-note{
  font-size: clamp(12px, .82vw, 15px) !important;
  line-height: 1.25 !important;
}

@media (max-width: 760px){
  .decision-summary-bar{
    grid-template-columns: 1fr !important;
    gap: 7px !important;
    padding: 8px !important;
  }
  .decision-summary-bar > div:first-child{
    display: none !important;
  }
  .top-actions{
    gap: 7px !important;
  }
  .top-actions button,.nav-back{
    padding: 11px 12px !important;
    font-size: 14px !important;
  }
  .warning,.guidance{
    font-size: 14px !important;
  }
  .card strong,.metric strong{
    font-size: 18px !important;
  }
}


/* MONAHINGA_PAGE2_GLOBAL_UI_LEGIBILITY_2026_05_04
   Visual-only UI legibility pass.
   Enlarges the small page-2 interface text while preserving layout, scoring, markers, terrain generation, PAD-US, and backend logic.
*/
body{
  font-family: "Arial Narrow", "Roboto Condensed", "Inter Tight", "Segoe UI", Arial, sans-serif !important;
  font-size: 15px !important;
  letter-spacing: -.01em;
}

.title h1{
  font-size: clamp(30px, 2.25vw, 40px) !important;
  line-height: 1.02 !important;
}

.title .eyebrow{
  font-size: clamp(12px, .9vw, 15px) !important;
  letter-spacing: .14em !important;
}

.warning,.guidance{
  font-size: clamp(14px, .95vw, 17px) !important;
  line-height: 1.42 !important;
  padding: 12px 14px !important;
}

.top-actions button,
.nav-back{
  font-size: clamp(14px, .95vw, 17px) !important;
  line-height: 1.15 !important;
  padding: 13px 16px !important;
  min-height: 42px !important;
}

.panel-title,
.section-title,
.card .label,
.metric .label,
.control-label,
.layers-label,
.scene-orientation-note strong{
  font-size: clamp(12px, .86vw, 15px) !important;
  letter-spacing: .09em !important;
  font-weight: 950 !important;
}

.card strong,
.metric strong{
  font-size: clamp(18px, 1.18vw, 22px) !important;
  line-height: 1.12 !important;
}

.toggle,
button,
input,
select{
  font-size: clamp(13px, .9vw, 16px) !important;
}

.toggle{
  padding: 8px 12px !important;
  min-height: 34px !important;
}

label,
small,
.micro-copy,
.cursor-hud,
.cursor-hud strong,
.cursor-hud div,
.hud-strip,
.hud-strip *,
.scene-orientation-note{
  font-size: clamp(13px, .88vw, 16px) !important;
  line-height: 1.32 !important;
}

input[type="range"]{
  min-height: 24px !important;
}

.sidebar,
.left-panel,
.operator-panel,
.setup-panel{
  font-size: 15px !important;
}

@media (max-width: 760px){
  body{
    font-size: 16px !important;
  }

  .title h1{
    font-size: 30px !important;
  }

  .title .eyebrow{
    font-size: 12px !important;
  }

  .warning,.guidance{
    font-size: 15px !important;
    line-height: 1.4 !important;
  }

  .top-actions button,
  .nav-back{
    font-size: 15px !important;
    padding: 12px 13px !important;
    min-height: 42px !important;
  }

  .card .label,
  .metric .label,
  .panel-title{
    font-size: 12px !important;
  }

  .card strong,
  .metric strong{
    font-size: 19px !important;
  }

  .toggle,
  .cursor-hud,
  .hud-strip,
  .micro-copy,
  .scene-orientation-note{
    font-size: 14px !important;
  }
}


/* MONAHINGA_HEADER_SIDEBAR_LEGIBILITY_2026_05_04
   Visual-only pass focused on the top/header controls and left operator sidebar.
   This intentionally avoids terrain, scoring, PAD-US, species logic, backend validation, and Render config.
*/

/* Use a readable condensed stack so larger text fits the same controls. */
body, body *{
  font-family: "Arial Narrow", "Roboto Condensed", "Inter Tight", "Segoe UI", Arial, sans-serif !important;
  text-rendering: geometricPrecision;
}

/* Header/title zone */
header,
.header,
.topbar,
.app-header,
.hero,
.title,
.title *{
  font-size: max(15px, 1vw) !important;
}

.title h1,
h1{
  font-size: clamp(32px, 2.45vw, 44px) !important;
  line-height: 1.02 !important;
  letter-spacing: -.045em !important;
  font-weight: 950 !important;
}

.title .eyebrow,
.eyebrow{
  font-size: clamp(12px, .9vw, 15px) !important;
  letter-spacing: .13em !important;
  font-weight: 950 !important;
}

/* Guidance and warning strips near the top */
.guidance,
.warning,
[class*="guidance"],
[class*="warning"],
[class*="alert"],
[class*="notice"]{
  font-size: clamp(15px, 1vw, 18px) !important;
  line-height: 1.42 !important;
  font-weight: 850 !important;
  letter-spacing: -.014em !important;
}

/* Top-right buttons and nav controls */
.top-actions,
.top-actions *,
nav,
nav *,
button,
.nav-back,
[class*="button"],
[class*="action"]{
  font-size: clamp(14px, .96vw, 17px) !important;
  line-height: 1.16 !important;
  font-weight: 900 !important;
  letter-spacing: -.015em !important;
}

.top-actions button,
.nav-back,
button{
  min-height: 42px !important;
  padding: 12px 15px !important;
}

/* Left setup/sidebar region.
   These selectors are intentionally broad because the current template has several generations of class names. */
aside,
.sidebar,
.left,
.left-panel,
.operator,
.operator-panel,
.setup,
.setup-panel,
.controls,
.control-panel,
.rail,
.panel{
  font-size: 16px !important;
  line-height: 1.25 !important;
}

aside *,
.sidebar *,
.left-panel *,
.operator-panel *,
.setup-panel *,
.controls *,
.control-panel *,
.rail *,
.panel *{
  font-size: clamp(14px, .94vw, 17px) !important;
  line-height: 1.24 !important;
  letter-spacing: -.01em !important;
}

/* Labels inside the left panel */
aside .label,
.sidebar .label,
.left-panel .label,
.operator-panel .label,
.setup-panel .label,
.controls .label,
.control-panel .label,
.metric .label,
.card .label,
.panel-title,
[class*="label"],
[class*="title"]{
  font-size: clamp(12px, .84vw, 15px) !important;
  line-height: 1.15 !important;
  letter-spacing: .08em !important;
  font-weight: 950 !important;
}

/* Values inside cards: Hunter, wind, direction, Huntable, etc. */
aside strong,
.sidebar strong,
.left-panel strong,
.operator-panel strong,
.setup-panel strong,
.controls strong,
.control-panel strong,
.metric strong,
.card strong{
  font-size: clamp(18px, 1.16vw, 22px) !important;
  line-height: 1.12 !important;
  letter-spacing: -.025em !important;
  font-weight: 950 !important;
}

/* Terrain layer pills/buttons and small controls */
.toggle,
.pill,
.chip,
.badge,
[class*="toggle"],
[class*="pill"],
[class*="chip"],
[class*="badge"]{
  font-size: clamp(13px, .9vw, 16px) !important;
  line-height: 1.1 !important;
  font-weight: 950 !important;
  padding: 8px 11px !important;
  min-height: 33px !important;
}

/* Slider labels such as TILT and DEPTH EXAGGERATION */
label,
.control-label,
.slider-label,
[class*="slider"],
input[type="range"] + *,
input[type="range"]{
  font-size: clamp(13px, .9vw, 16px) !important;
  font-weight: 850 !important;
}

/* Phone safety: keep the same readability target without exploding the layout. */
@media (max-width: 760px){
  .title h1,
  h1{
    font-size: 31px !important;
  }

  .guidance,
  .warning,
  [class*="guidance"],
  [class*="warning"],
  [class*="alert"],
  [class*="notice"]{
    font-size: 15px !important;
  }

  .top-actions button,
  .nav-back,
  button{
    font-size: 14px !important;
    padding: 11px 12px !important;
    min-height: 40px !important;
  }

  aside *,
  .sidebar *,
  .left-panel *,
  .operator-panel *,
  .setup-panel *,
  .controls *,
  .control-panel *,
  .rail *,
  .panel *{
    font-size: 14px !important;
  }

  aside strong,
  .sidebar strong,
  .left-panel strong,
  .operator-panel strong,
  .setup-panel strong,
  .metric strong,
  .card strong{
    font-size: 18px !important;
  }
}


/* MONAHINGA_TOP_LEFT_CLEANUP_2026_05_04
   Visual-only top/left cleanup.
   Hides the obsolete Hide AI Panel control, normalizes the Back to Box / Launch button,
   and improves header/sidebar legibility without touching scoring, terrain, PAD-US, species, backend, or Render config.
*/

/* Top button row: consistent readable sizing */
.top-actions button,
.top-actions a,
.nav-back,
a.nav-back,
button.nav-back{
  font-family: "Arial Narrow", "Roboto Condensed", "Inter Tight", "Segoe UI", Arial, sans-serif !important;
  font-size: 16px !important;
  line-height: 1.15 !important;
  font-weight: 950 !important;
  letter-spacing: -.015em !important;
  min-height: 44px !important;
  padding: 13px 16px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  white-space: nowrap !important;
}

/* Specifically stop Back to Box / Launch from looking smaller than the others. */
.nav-back,
a[href*="launch"],
a[href*="box"],
a[href*="index"]{
  font-size: 16px !important;
  font-weight: 950 !important;
}

/* Top title and warning/guidance bars */
.title h1,
h1{
  font-size: clamp(33px, 2.55vw, 45px) !important;
  line-height: 1.02 !important;
  font-weight: 950 !important;
  letter-spacing: -.045em !important;
}

.title .eyebrow,
.eyebrow{
  font-size: clamp(12px, .92vw, 15px) !important;
  letter-spacing: .13em !important;
  font-weight: 950 !important;
}

.guidance,
.warning,
[class*="guidance"],
[class*="warning"]{
  font-size: clamp(15px, 1vw, 18px) !important;
  line-height: 1.42 !important;
  font-weight: 850 !important;
  letter-spacing: -.012em !important;
}

/* Left operator/setup area: stronger readable labels and values */
aside,
.sidebar,
.left-panel,
.operator-panel,
.setup-panel,
.controls,
.control-panel,
.rail,
.panel{
  font-family: "Arial Narrow", "Roboto Condensed", "Inter Tight", "Segoe UI", Arial, sans-serif !important;
  font-size: 16px !important;
  line-height: 1.24 !important;
}

aside .label,
.sidebar .label,
.left-panel .label,
.operator-panel .label,
.setup-panel .label,
.controls .label,
.control-panel .label,
.metric .label,
.card .label,
.panel-title,
[class*="label"]{
  font-size: 13px !important;
  line-height: 1.15 !important;
  letter-spacing: .08em !important;
  font-weight: 950 !important;
}

aside strong,
.sidebar strong,
.left-panel strong,
.operator-panel strong,
.setup-panel strong,
.controls strong,
.control-panel strong,
.metric strong,
.card strong{
  font-size: 20px !important;
  line-height: 1.12 !important;
  letter-spacing: -.025em !important;
  font-weight: 950 !important;
}

.toggle,
.pill,
.chip,
.badge,
[class*="toggle"],
[class*="pill"],
[class*="chip"],
[class*="badge"]{
  font-size: 14px !important;
  line-height: 1.12 !important;
  font-weight: 950 !important;
  padding: 8px 12px !important;
  min-height: 34px !important;
}

@media (max-width: 760px){
  .top-actions button,
  .top-actions a,
  .nav-back,
  a.nav-back,
  button.nav-back{
    font-size: 15px !important;
    min-height: 42px !important;
    padding: 11px 12px !important;
  }

  .title h1,
  h1{
    font-size: 31px !important;
  }

  .guidance,
  .warning,
  [class*="guidance"],
  [class*="warning"]{
    font-size: 15px !important;
  }

  aside .label,
  .sidebar .label,
  .left-panel .label,
  .operator-panel .label,
  .setup-panel .label,
  .metric .label,
  .card .label,
  .panel-title,
  [class*="label"]{
    font-size: 12px !important;
  }

  aside strong,
  .sidebar strong,
  .left-panel strong,
  .operator-panel strong,
  .setup-panel strong,
  .metric strong,
  .card strong{
    font-size: 18px !important;
  }
}


/* MONAHINGA_FINAL_TITLE_LEFT_CLEARANCE_2026_05_04
   Final visual polish only.
   Protects left operator cards from being crowded by the 3D scene and improves upper-left title readability.
   Does not touch scoring, terrain generation, markers, PAD-US, species logic, backend, or Render config.
*/

/* Upper-left product/title text */
.title h1,
h1{
  font-size: clamp(34px, 2.65vw, 46px) !important;
  line-height: 1.02 !important;
  font-weight: 950 !important;
  letter-spacing: -.045em !important;
}

.title .eyebrow,
.eyebrow,
[class*="eyebrow"]{
  font-size: clamp(13px, .96vw, 16px) !important;
  line-height: 1.18 !important;
  letter-spacing: .12em !important;
  font-weight: 950 !important;
  opacity: .98 !important;
}

/* Keep the left operator panel readable and above scene edges. */
aside,
.sidebar,
.left-panel,
.operator-panel,
.setup-panel,
.controls,
.control-panel,
.rail,
.panel:first-child{
  min-width: 205px !important;
  max-width: 245px !important;
  position: relative !important;
  z-index: 18 !important;
  overflow: visible !important;
}

/* Make the left cards themselves stay fully readable. */
aside .card,
.sidebar .card,
.left-panel .card,
.operator-panel .card,
.setup-panel .card,
.metric,
.card{
  min-width: 78px !important;
  overflow: visible !important;
}

aside strong,
.sidebar strong,
.left-panel strong,
.operator-panel strong,
.setup-panel strong,
.metric strong,
.card strong{
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
}

/* Give the 3D scene a tiny breathing gap from the left panel without changing the engine. */
.scene-shell,
.center,
main.center{
  margin-left: 8px !important;
}

/* If the page uses grid/flex, preserve a safe gutter between left panel and scene. */
.layout,
.app-grid,
.viewer-grid,
.surface-grid,
.main-grid,
.main-layout{
  column-gap: 14px !important;
  gap: 14px !important;
}

/* Phone: avoid forcing a wide sidebar on narrow screens. */
@media (max-width: 760px){
  aside,
  .sidebar,
  .left-panel,
  .operator-panel,
  .setup-panel,
  .controls,
  .control-panel,
  .rail,
  .panel:first-child{
    min-width: 0 !important;
    max-width: none !important;
  }

  .scene-shell,
  .center,
  main.center{
    margin-left: 0 !important;
  }

  .title h1,
  h1{
    font-size: 32px !important;
  }

  .title .eyebrow,
  .eyebrow,
  [class*="eyebrow"]{
    font-size: 13px !important;
  }
}


/* MONAHINGA_PAGE2_TITLE_BALANCE_2026_05_04
   Final title hierarchy balance.
   Reduces the oversized viewer title and strengthens the small brand line.
   CSS-only: no terrain, scoring, marker, PAD-US, species, backend, or Render changes.
*/

.title h1,
h1{
  font-size: clamp(28px, 2.05vw, 36px) !important;
  line-height: 1.04 !important;
  letter-spacing: -.04em !important;
  font-weight: 950 !important;
  margin-top: 4px !important;
  margin-bottom: 8px !important;
}

.title .eyebrow,
.eyebrow,
[class*="eyebrow"]{
  font-size: clamp(12px, .9vw, 14px) !important;
  line-height: 1.18 !important;
  letter-spacing: .15em !important;
  font-weight: 950 !important;
  opacity: .98 !important;
  margin-bottom: 2px !important;
}

@media (max-width: 760px){
  .title h1,
  h1{
    font-size: 29px !important;
    line-height: 1.05 !important;
  }

  .title .eyebrow,
  .eyebrow,
  [class*="eyebrow"]{
    font-size: 12px !important;
  }
}


/* MONAHINGA_TITLE_RATIO_ADJUST_2026_05_04
   Adjust title hierarchy per request:
   - Main viewer title ~50% size
   - Eyebrow + guidance/warnings ~2x stronger
   CSS only.
*/

/* Main title smaller */
.title h1,
h1{
  font-size: clamp(18px, 1.3vw, 24px) !important;
  line-height: 1.05 !important;
  letter-spacing: -.03em !important;
  font-weight: 900 !important;
}

/* Brand line bigger */
.title .eyebrow,
.eyebrow,
[class*="eyebrow"]{
  font-size: clamp(14px, 1.1vw, 18px) !important;
  letter-spacing: .16em !important;
  font-weight: 950 !important;
}

/* Guidance + warning bigger */
.guidance,
.warning,
[class*="guidance"],
[class*="warning"]{
  font-size: clamp(16px, 1.2vw, 20px) !important;
  line-height: 1.4 !important;
  font-weight: 900 !important;
  letter-spacing: -.01em !important;
}

@media (max-width: 760px){
  .title h1,
  h1{
    font-size: 20px !important;
  }

  .title .eyebrow,
  .eyebrow{
    font-size: 14px !important;
  }

  .guidance,
  .warning,
  [class*="guidance"],
  [class*="warning"]{
    font-size: 16px !important;
  }
}


/* MONAHINGA_HEADER_AND_SCENE_FIT_2026_05_04
   Visual-only page-2 balance pass.
   Makes the brand/warning text much more readable, reduces the oversized viewer title,
   and tightens the 3D scene into the viewport so the bottom HUD is less buried.
   Does not touch scoring, terrain generation, marker logic, PAD-US, species logic, backend, or Render config.
*/

/* Header hierarchy: small main title, strong supporting lines. */
.title h1,
h1{
  font-size: clamp(16px, 1.05vw, 22px) !important;
  line-height: 1.03 !important;
  letter-spacing: -.025em !important;
  font-weight: 850 !important;
  margin-top: 2px !important;
  margin-bottom: 7px !important;
}

.title .eyebrow,
.eyebrow,
[class*="eyebrow"]{
  font-size: clamp(18px, 1.45vw, 24px) !important;
  line-height: 1.12 !important;
  letter-spacing: .12em !important;
  font-weight: 950 !important;
  opacity: 1 !important;
  margin-bottom: 3px !important;
}

.guidance,
.warning,
[class*="guidance"],
[class*="warning"]{
  font-size: clamp(20px, 1.55vw, 26px) !important;
  line-height: 1.32 !important;
  font-weight: 950 !important;
  letter-spacing: -.018em !important;
  padding: 11px 14px !important;
}

/* Compact the top stack so the 3D view can sit higher and fit better. */
header,
.header,
.topbar,
.app-header,
.hero{
  padding-top: 8px !important;
  padding-bottom: 8px !important;
}

.top-actions{
  gap: 8px !important;
}

.top-actions button,
.top-actions a,
.nav-back,
button.nav-back,
a.nav-back{
  min-height: 38px !important;
  padding: 10px 14px !important;
}

/* Pull the summary and scene upward; reduce wasted gap above terrain. */
.decision-summary-bar{
  margin-top: 3px !important;
  margin-bottom: 6px !important;
  padding: 8px 10px !important;
}

.scene-shell{
  margin-top: 0 !important;
  min-height: 0 !important;
  height: calc(100vh - 285px) !important;
  max-height: 690px !important;
  overflow: hidden !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

/* Make the actual 3D canvas/container fill the centered scene instead of sliding below the fold. */
.scene-shell canvas,
.scene-shell #scene,
.scene-shell #terrain,
.scene-shell [id*="scene"],
.scene-shell [id*="terrain"],
.scene-shell [class*="scene"],
.scene-shell [class*="terrain"]{
  max-height: 100% !important;
}

/* Keep bottom HUD readable but less blocking. */
.hud-strip{
  bottom: 10px !important;
  left: 14px !important;
  right: 280px !important;
  padding: 6px 8px !important;
  opacity: .92 !important;
}

.cursor-hud{
  bottom: 10px !important;
  right: 14px !important;
  max-width: 260px !important;
  padding: 9px 10px !important;
  opacity: .94 !important;
}

/* Main layout should avoid extra vertical creep. */
main.center,
.center{
  margin-top: 0 !important;
  padding-top: 0 !important;
}

@media (max-width: 760px){
  .title h1,
  h1{
    font-size: 18px !important;
  }

  .title .eyebrow,
  .eyebrow,
  [class*="eyebrow"]{
    font-size: 16px !important;
    letter-spacing: .08em !important;
  }

  .guidance,
  .warning,
  [class*="guidance"],
  [class*="warning"]{
    font-size: 17px !important;
    line-height: 1.3 !important;
    padding: 9px 11px !important;
  }

  .scene-shell{
    height: calc(100vh - 330px) !important;
    max-height: none !important;
  }

  .hud-strip{
    right: 12px !important;
    bottom: 58px !important;
  }

  .cursor-hud{
    left: 12px !important;
    right: 12px !important;
    max-width: none !important;
    bottom: 10px !important;
  }
}


/* MONAHINGA_FONT_BALANCE_REFINE_2026_05_04
   Refine font balance:
   - Brand line much bigger
   - Warning/guidance bigger
   - Sidebar values slightly smaller (Hunter, Huntable, etc.)
   CSS only, no logic touched
*/

/* Brand line (top small text) */
.title .eyebrow,
.eyebrow,
[class*="eyebrow"]{
  font-size: clamp(20px, 1.6vw, 26px) !important;
  font-weight: 950 !important;
  letter-spacing: .14em !important;
}

/* Warning + guidance */
.guidance,
.warning,
[class*="guidance"],
[class*="warning"]{
  font-size: clamp(20px, 1.6vw, 26px) !important;
  line-height: 1.35 !important;
  font-weight: 950 !important;
}

/* Sidebar labels slightly refined */
.card .label,
.metric .label,
.panel-title,
[class*="label"]{
  font-size: clamp(11px, .8vw, 13px) !important;
  letter-spacing: .08em !important;
}

/* Sidebar values (Hunter, Huntable, etc.) slightly reduced */
.card strong,
.metric strong,
aside strong,
.sidebar strong,
.left-panel strong{
  font-size: clamp(16px, 1vw, 18px) !important;
  font-weight: 900 !important;
}

/* WHY / WHEN text slightly more readable but not oversized */
.decision-summary-bar strong{
  font-size: clamp(15px, 1.05vw, 18px) !important;
}

@media (max-width: 760px){
  .title .eyebrow,
  .eyebrow{
    font-size: 18px !important;
  }

  .guidance,
  .warning{
    font-size: 17px !important;
  }

  .card strong,
  .metric strong{
    font-size: 16px !important;
  }
}


/* MONAHINGA_PAGE2_DUAL_2D_3D_FOUNDATION_2026_05_04
   Gold-label foundation: real 2D command map beside the 3D terrain.
   The 2D map is north-up and fits the exact same bbox as the 3D run.
   This pass is visual/read-only sync; scoring, terrain generation, PAD-US, backend, and Render config are untouched.
*/
.command-dual-workbench{
  display:grid;
  grid-template-columns:minmax(300px, 40fr) minmax(520px, 60fr); /* MONAHINGA_PAGE2_SPLIT_40_60_SAFE_2026_05_05: left map 40%, right terrain 60% */
  gap:10px;
  align-items:stretch;
  width:100%;
  height:calc(100vh - 285px);
  min-height:520px;
}

.command-map-panel,
.command-terrain-panel{
  min-width:0;
  min-height:0;
  position:relative;
}

.command-map-panel{
  border-radius:18px;
  border:1px solid rgba(255,255,255,.10);
  background:rgba(5,12,18,.88);
  overflow:hidden;
  box-shadow:0 18px 38px rgba(0,0,0,.24);
}

.command-map-header{
  position:absolute;
  top:10px;
  left:10px;
  right:10px;
  z-index:410;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:8px;
  pointer-events:none;
}

.command-map-title,
.command-map-badge{
  border:1px solid rgba(255,255,255,.13);
  background:rgba(6,13,20,.78);
  color:#f3fff0;
  border-radius:999px;
  padding:7px 10px;
  font-size:12px;
  line-height:1.1;
  font-weight:950;
  letter-spacing:.04em;
  text-transform:uppercase;
  backdrop-filter:blur(8px);
}

.command-map-badge{
  color:#9fd7ff;
}

/* MONAHINGA_PAGE2_MAP_GUIDE_LEGEND_2026_05_05:
   Small guide-style legend for the real 2D command map.
   Visual-only. Does not touch scoring, terrain generation, backend, or 3D logic.
*/
.command-map-guide-legend{
  position:absolute;
  left:12px;
  bottom:12px;
  z-index:420;
  width:min(250px, calc(100% - 24px));
  border:1px solid rgba(255,255,255,.13);
  border-radius:16px;
  background:rgba(5,12,18,.84);
  color:#edf7ef;
  box-shadow:0 16px 34px rgba(0,0,0,.26);
  backdrop-filter:blur(10px);
  padding:10px 11px;
  pointer-events:none;
}

.command-map-guide-legend strong{
  display:block;
  font-size:12px;
  line-height:1.1;
  letter-spacing:.06em;
  text-transform:uppercase;
  color:#f4fff0;
  margin-bottom:8px;
}

.command-map-guide-legend-row{
  display:flex;
  align-items:center;
  gap:8px;
  font-size:12px;
  line-height:1.25;
  color:#d8e7de;
  margin-top:6px;
}

.command-map-guide-symbol{
  flex:0 0 auto;
  width:13px;
  height:13px;
  border-radius:999px;
  border:2px solid rgba(255,255,255,.82);
  box-shadow:0 0 0 2px rgba(0,0,0,.24);
}

.command-map-guide-symbol.primary{ background:#aef186; }
.command-map-guide-symbol.base{ background:#5ec8ff; }
.command-map-guide-symbol.entry{ background:#ffb347; }

.command-map-guide-line{
  flex:0 0 auto;
  width:24px;
  height:0;
  border-top:3px dashed #aef186;
  opacity:.95;
}

.command-map-guide-box{
  flex:0 0 auto;
  width:18px;
  height:13px;
  border:2px solid #aef186;
  border-radius:3px;
  background:rgba(174,241,134,.08);
}

.command-map-guide-note{
  margin-top:8px;
  padding-top:7px;
  border-top:1px solid rgba(255,255,255,.10);
  font-size:11px;
  line-height:1.35;
  color:#9fb2a8;
}

#commandLeafletMap{
  width:100%;
  height:100%;
  min-height:520px;
  background:#0b1318;
}

.command-terrain-panel .scene-shell{
  height:100% !important;
  min-height:520px !important;
}

.command-map-pin-label{
  font-size:12px;
  font-weight:950;
  color:#f8fff2;
  text-shadow:0 1px 3px rgba(0,0,0,.75);
}

/* MONAHINGA_PAGE2_PRIMARY_SIT_STRONG_FOCUS_2026_05_05:
   Strong visual emphasis for the Primary Sit marker and invisible approach.
   Leaflet visual-only change. No backend, scoring, 3D terrain generation, or Render setup touched.
*/
.command-map-primary-focus{
  position:relative;
  width:34px;
  height:34px;
  border-radius:999px;
  pointer-events:none;
}

.command-map-primary-focus::before,
.command-map-primary-focus::after{
  content:"";
  position:absolute;
  inset:2px;
  border-radius:999px;
  border:2px solid rgba(174,241,134,.82);
  box-shadow:0 0 18px rgba(174,241,134,.85), 0 0 34px rgba(174,241,134,.42);
  animation:commandPrimaryPulse 1.55s ease-out infinite;
}

.command-map-primary-focus::after{
  inset:7px;
  border-color:rgba(255,255,255,.62);
  animation-duration:2.15s;
  animation-delay:.22s;
}

.command-map-primary-dot{
  position:absolute;
  left:7px;
  top:7px;
  width:20px;
  height:20px;
  border-radius:999px;
  background:#bfff85;
  border:4px solid #111f09;
  box-shadow:
    0 0 0 4px rgba(174,241,134,.34),
    0 0 22px rgba(174,241,134,.95),
    0 0 42px rgba(174,241,134,.52);
  z-index:2;
}

.command-map-approach-glow{
  filter:drop-shadow(0 0 8px rgba(174,241,134,.95)) drop-shadow(0 0 18px rgba(174,241,134,.42));
}

.command-map-approach-line{
  filter:drop-shadow(0 0 5px rgba(174,241,134,.85));
}

.command-map-approach-arrow{
  width:28px;
  height:28px;
  border-radius:999px;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#112006;
  background:rgba(200,255,141,.94);
  border:2px solid rgba(255,255,255,.72);
  box-shadow:0 0 16px rgba(174,241,134,.82), 0 0 32px rgba(174,241,134,.34);
  font-size:18px;
  font-weight:950;
  line-height:1;
  text-shadow:none;
  pointer-events:none;
}

.command-map-approach-arrow span{
  display:block;
  transform:translateY(-1px);
}

.command-map-approach-label{
  border:1px solid rgba(200,255,141,.45);
  border-radius:999px;
  background:rgba(5,12,18,.86);
  color:#eaffd6;
  box-shadow:0 10px 24px rgba(0,0,0,.24), 0 0 18px rgba(174,241,134,.28);
  padding:5px 9px;
  font-size:11px;
  line-height:1;
  font-weight:950;
  letter-spacing:.05em;
  text-transform:uppercase;
  white-space:nowrap;
  pointer-events:none;
}

/* MONAHINGA_PAGE2_ACTION_COMMAND_AFTER_APPROACH_LABEL_2026_05_05:
   Direct field action command placed beside the already-visible approach label.
   Visual-only Leaflet overlay. No backend, scoring, 3D, Render setup, or terrain generation touched.
*/
.command-map-action-command{
  border:2px solid rgba(255,255,255,.20);
  border-radius:14px;
  background:rgba(5,12,18,.94);
  color:#f6fff2;
  box-shadow:0 16px 34px rgba(0,0,0,.36);
  padding:8px 11px;
  min-width:188px;
  max-width:238px;
  font-size:12px;
  line-height:1.18;
  font-weight:950;
  letter-spacing:.035em;
  text-transform:uppercase;
  white-space:normal;
  pointer-events:none;
}

.command-map-action-command.safe{
  border-color:rgba(174,241,134,.95);
  background:rgba(17,44,13,.94);
  color:#eaffd6;
  box-shadow:0 16px 34px rgba(0,0,0,.36), 0 0 28px rgba(174,241,134,.44);
}

.command-map-action-command.risk{
  border-color:rgba(255,207,74,.98);
  background:rgba(66,46,5,.96);
  color:#fff2b8;
  box-shadow:0 16px 34px rgba(0,0,0,.38), 0 0 32px rgba(255,207,74,.54);
}

.command-map-action-command.bad{
  border-color:rgba(255,82,82,1);
  background:rgba(76,8,8,.97);
  color:#ffe1e1;
  box-shadow:0 16px 34px rgba(0,0,0,.40), 0 0 38px rgba(255,82,82,.66);
}

.command-map-action-command.unknown{
  border-color:rgba(159,215,255,.92);
  background:rgba(9,27,42,.95);
  color:#eef8ff;
  box-shadow:0 16px 34px rgba(0,0,0,.38), 0 0 30px rgba(159,215,255,.48);
}

.command-map-action-command small{
  display:block;
  margin-top:4px;
  color:rgba(255,255,255,.72);
  font-size:10px;
  line-height:1.15;
  font-weight:800;
  letter-spacing:.02em;
  text-transform:none;
}

@keyframes commandPrimaryPulse{
  0%{
    transform:scale(.62);
    opacity:.95;
  }
  72%{
    transform:scale(1.22);
    opacity:.20;
  }
  100%{
    transform:scale(1.36);
    opacity:0;
  }
}

.command-map-base-dot{
  width:15px;
  height:15px;
  border-radius:999px;
  background:#5ec8ff;
  border:3px solid #071824;
  box-shadow:0 0 0 3px rgba(94,200,255,.22), 0 0 14px rgba(94,200,255,.42);
}

.command-map-entry-dot{
  width:15px;
  height:15px;
  border-radius:999px;
  background:#ffb347;
  border:3px solid #271807;
  box-shadow:0 0 0 3px rgba(255,179,71,.24), 0 0 14px rgba(255,179,71,.40);
}

.command-map-fallback{
  position:absolute;
  inset:0;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:24px;
  color:#d7e3da;
  text-align:center;
  font-weight:850;
  background:rgba(5,12,18,.92);
  z-index:405;
}

@media (max-width: 980px){
  .command-dual-workbench{
    grid-template-columns:1fr;
    height:auto;
    min-height:0;
  }
  .command-map-panel,
  .command-terrain-panel .scene-shell,
  #commandLeafletMap{
    min-height:420px !important;
  }
}

</style>

<!-- MONAHINGA_PAGE2_DUAL_2D_3D_FOUNDATION_2026_05_04: Leaflet assets for real 2D command map -->
<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  crossorigin=""
>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>

</head>
<body>
<div class="shell"><div class="chrome"><div class="topbar"><div><div class="brandline">Monahinga™ · Terrain-First Hunter Surface</div><h1>3D Terrain Intelligence Viewer</h1><div class="sub">Real heightmap mesh, clean viewer authority, PAD-US display modes, and ranked hunting intelligence in one operator-facing surface.</div><div style="margin-top:8px;padding:8px 12px;border-radius:10px;background:rgba(255,209,102,.08);border:1px solid rgba(255,209,102,.24);color:#ffd166;font-size:12px;line-height:1.4;max-width:760px">AI-optimized guidance: confirm legality, access, safety, and field conditions before acting on any recommendation.</div><div style="margin-top:8px;padding:8px 12px;border-radius:10px;background:rgba(255,120,120,.08);border:1px solid rgba(255,120,120,.28);color:#ffd1d1;font-size:12px;line-height:1.4;max-width:760px"><strong>Huntability warning:</strong> Do not use city blocks, suburbs, parking lots, houses, roads, or non-hunting land. Draw boxes only over real natural/legal hunting ground and verify permission before entering.</div><div class="region-stack"><div class="region-chip"><strong id="regionIdentityLabel">Appalachian whitetail terrain</strong></div><div class="region-chip" id="regionSpeciesLabel">Whitetail · Turkey country</div><div class="region-chip" id="regionMoodLabel">Shaded timber folds</div></div><div id="regionStory" class="region-story">This box reads like Appalachian whitetail country: layered timber folds, protected side-hill movement, and setup value that rewards disciplined access.</div></div>

<div class="command-tools">
  <button id="saveViewHelpBtn" class="mode-btn" type="button">How to Save View</button>
  <div class="command-tools-row" aria-label="Viewer utility controls">
    <button id="resetViewBtn" class="command-tool-btn" type="button">Reset View</button>
    <button id="downloadSummaryBtn" class="command-tool-btn" type="button">Download Summary</button>
    <button id="invisibleApproachBtn" class="command-tool-btn" type="button">Invisible Approach</button>
    <button id="visualFocusToggle" class="visual-focus-toggle" type="button">Hide AI Panel</button>
    <a class="command-tool-btn command-back-link" href="/">Back to Box / Launch</a>
  </div>
</div>

<div class="pills"><div class="pill">Provider: $provider</div><div class="pill">Legal: $legal_provider</div><div class="pill">BBox: $min_lon, $min_lat → $max_lon, $max_lat</div><div class="pill">Mesh source: $mesh_w×$mesh_h</div><div class="pill">Default layer: $default_layer_label</div><div class="pill">Default legal view: $default_padus_label</div><div class="pill">$legal_badge</div></div></div>
<div class="layout">
<aside class="left">
  <div class="block"><h3>Operator Setup</h3><div class="kv"><div><label>Mode</label><strong>$mode</strong></div><div><label>Wind</label><strong id="operatorWindValue">$current_wind</strong></div><div><label>Preferred Wind</label><strong>$preferred_wind</strong></div><div><label>Readiness</label><strong>$readiness</strong></div></div></div>
  $selected_box_status_markup
  <div class="block"><h3>Terrain Layers</h3><div class="layer-stack" id="terrainLayerStack">$layer_buttons</div><div class="note" style="margin-top:8px">Terrain stays realistic. Cover is now blended into the mountain as a soft read layer that influences movement instead of acting like a separate mode.</div><div class="slider-group"><label>Tilt</label><input id="tiltSlider" type="range" min="12" max="42" value="28"></div><div class="slider-group"><label>Depth Exaggeration</label><input id="depthSlider" type="range" min="70" max="145" value="90"></div><div class="pin-help">Click a ranked row or a 3D pin to focus the terrain.</div><div id="focusReadHint" class="focus-read-hint">Focus read: terrain stays live while the cover overlay quietly shows concealment pockets, edges, and exposed crossings.</div></div>
  <div class="block"><h3>PAD-US Display</h3><div class="mode-stack"><button class="mode-btn" data-padus-mode="hybrid">Hybrid</button><button class="mode-btn" data-padus-mode="lines">Lines</button><button class="mode-btn" data-padus-mode="fill">Fill</button></div><div class="note" style="margin-top:10px">Legal geometry is clipped to the terrain box before it reaches the viewer, and the viewer clamps any stray points as a final guardrail.</div></div>
  <div class="block"><h3>Operator Notes</h3><div class="note">$operator_notes</div></div>
  <div class="block decision-card"><span class="decision-label">Hunt window</span><strong id="bestTimeLabel" class="decision-title">$best_time_label</strong><span id="bestTimeWindow" class="decision-sub">$best_time_window</span><div class="viewer-micro-note">Use this as the fast decision read first, then verify with wind, legality, access, and field sign.</div><div class="atmo-note" id="terrainIdentityNote">Regional terrain identity helps the scene feel grounded, but your sit decision still comes from the live run data.</div></div>
  <div class="block"><h3>Cover Intelligence</h3><div class="intel-row provider-ok"><strong>Terrain + Cover Read Active</strong><span>Movement bias: reading concealed lower-shelf routes first.</span></div><div class="intel-row"><strong>Exposure watch</strong><span>Open ridge crossings and crest-top travel stay higher risk.</span></div><div class="intel-row"><strong>How cover factors in</strong><span>Cover now supports the movement read, not a separate button mode.</span></div></div>
</aside>
<main class="center"><div class="decision-summary-bar" id="decisionSummaryBar"><div><span>Best sit</span><strong>$primary_title</strong></div><div><span>Why</span><strong>$primary_reason</strong></div><div><span>When</span><strong>$best_time_window</strong></div></div><div class="command-dual-workbench" data-monahinga-created-by="MONAHINGA_PAGE2_DUAL_2D_3D_FOUNDATION_2026_05_04">
  <section class="command-map-panel" aria-label="2D command map aligned with 3D terrain">
    <div class="command-map-header">
      <div class="command-map-title">2D Command Map · North Up</div>
      <div class="command-map-badge">Topo / Satellite / Street</div>
    </div>
    <div id="commandLeafletMap" role="application" aria-label="Interactive 2D map showing the same bbox, primary sit, base camp, and invisible approach"></div>
    <div class="command-map-guide-legend" aria-hidden="true">
      <strong>Guide Map Read</strong>
      <div class="command-map-guide-legend-row"><span class="command-map-guide-symbol primary"></span><span>Primary Sit</span></div>
      <div class="command-map-guide-legend-row"><span class="command-map-guide-symbol base"></span><span>Base Camp</span></div>
      <div class="command-map-guide-legend-row"><span class="command-map-guide-symbol entry"></span><span>Access Entry</span></div>
      <div class="command-map-guide-legend-row"><span class="command-map-guide-line"></span><span>Invisible Approach</span></div>
      <div class="command-map-guide-legend-row"><span class="command-map-guide-box"></span><span>Same BBox Boundary</span></div>
      <div class="command-map-guide-note">North-up 2D map uses the same bbox and sit data as the 3D terrain.</div>
    </div>
  </section>
  <section class="command-terrain-panel" aria-label="3D terrain view">
    <div class="scene-shell"><div class="scene-orientation-note"><strong>Orientation:</strong> Starting view is intended to read north/south from above. You can rotate, tilt, and explore the terrain after launch.</div>$wildlife_atmosphere_markup<div class="legend"><div class="chip">Green ring = best sit</div><div class="chip">Gold ring = backup sit</div><div class="chip">Amber ring = fringe option</div><div class="chip">PAD-US glow follows the terrain</div><div id="modeStatusChip" class="chip">Terrain + Cover Read</div><div id="coverKeyLegend" class="cover-key"><div class="chip cover-chip"><span class="cover-swatch cover-swatch-dense"></span>Dense cover</div><div class="chip cover-chip"><span class="cover-swatch cover-swatch-moderate"></span>Moderate cover</div><div class="chip cover-chip"><span class="cover-swatch cover-swatch-open"></span>Open / exposed</div><div class="chip cover-chip"><span class="cover-swatch cover-swatch-bowl"></span>Sheltered bowl</div></div></div><div class="scene-tools" aria-hidden="true" style="display:none"></div><div id="viewer"></div>
<style>
.hud-strip {
    position: absolute !important;
    bottom: 20px !important;
    left: 50%;
    transform: translateX(-50%);
    width: 85%;
    max-height: 140px;
    overflow: hidden;
    background: rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(6px);
    border-radius: 12px;
    padding: 8px;
}
.hud-strip:hover {
    max-height: 320px;
    overflow-y: auto;
}
</style>

<div class="cursor-hud" id="cursorHud"><strong>Cursor terrain read</strong><div id="cursorCoords">Move over the terrain to read live GPS.</div><div class="micro-copy">Reads the current terrain point under your cursor.</div></div><div class="hud-strip"><div class="hud-card"><span class="label">Primary sit</span><strong>$primary_title</strong></div><div class="hud-card"><span class="label">Confidence</span><strong>$confidence_label</strong> · $confidence</div><div class="hud-card" id="selectedSiteHud"><span class="label">Selected sit coordinates</span><strong id="selectedSiteTitle">$primary_title</strong><div id="selectedSiteCoords">Loading coordinates…</div><button id="copyCoordsBtn" type="button">Copy coordinates</button></div><div class="hud-card" id="liveWindHud"><span class="label">Live wind near primary sit</span><strong id="liveWindHudSummary">Loading live wind…</strong><div id="liveWindHudMeta" class="micro-copy">Fetching current direction and speed.</div></div><div class="hud-card approach-hud" id="invisibleApproachHud"><span class="label">Invisible Approach</span><strong id="invisibleApproachSummary">Layer off</strong><div id="invisibleApproachMeta" class="micro-copy">Toggle to show approach risk from Access Entry to the selected sit.</div></div></div></div></section></div></main>
<aside class="right"><div class="side-rail">$hunter_core_spotlight_markup<div class="block" id="fieldAnchorGuide" style="margin-bottom:8px;border-color:rgba(94,200,255,.22);background:rgba(8,18,28,.78)">
  <h3 style="margin-bottom:6px">Field Anchors</h3>
  <div class="note">
    <strong style="color:#8fd0ff">Blue pin = Base Camp</strong><br>
    <strong style="color:#ffb347">Orange pin = Access Entry</strong><br>
    Invisible Approach routes from Access Entry to the selected sit.
    <br><br>
    To move one: click the pin, type <strong>MOVE</strong>, then click its new spot on the terrain.
  </div>
</div><div class="block field-map-card" id="fieldOrientationMap">
  <h3 style="margin-bottom:6px">2D Field Orientation Map</h3>
  <div class="note" style="margin-bottom:7px">Top-down read for field use. North is up. Use this with the 3D view so the sit stack is not confusing.</div>
  <div class="field-map-wrap">
    <svg id="fieldMapSvg" class="field-map-svg" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="2D field orientation map"></svg>
    <div class="field-map-compass">N ↑</div>
  </div>
  <div class="field-map-legend">
    <span><i class="field-map-dot" style="background:#5ec8ff"></i>Base Camp</span>
    <span><i class="field-map-dot" style="background:#ffb347"></i>Access Entry</span>
    <span><i class="field-map-dot" style="background:#f5d38a"></i>Primary</span>
    <span><i class="field-map-dot" style="background:#6fb3da"></i>Alt sits</span>
  </div>
  <div class="micro-copy">Dotted green line = invisible approach from Access Entry to the selected sit. Click ranked sits to update this map.</div>
</div><div class="primary-box"><div class="primary-title">Primary Sit</div><div class="primary-name">$primary_title</div><div class="primary-reason">$primary_reason</div>
<div class="block" id="executiveSummaryBlock" style="margin-top:8px;padding:8px 9px"><h3 style="margin-bottom:5px">Executive Summary</h3><div id="executiveSummaryContent" class="note">Select a sit, pin, Base Camp, or Access Entry to see the fast decision summary.</div></div>
<div class="game-context-card" id="gameContextBlock"><span class="game-context-kicker">Likely game context</span><div id="gameContextContent" class="note">Select a sit to see the likely target species, movement style, and why this terrain supports that read.</div></div>
<div class="block" style="margin-top:8px;padding:8px 9px">
  <h3 style="margin-bottom:5px">Cover & Exposure</h3>
  $vegetation_signal_markup
</div><div class="trust-tags" id="trustTags" data-title="$primary_title" data-reason="$primary_reason" data-tags="$primary_tags" data-wind="$preferred_wind" data-legal="$legal_badge" aria-label="Why this sit works"></div><div class="meta"><div class="chip">$primary_score score</div><div class="chip">$preferred_wind</div><div class="chip">$best_time_window</div></div></div><div class="section-kicker">Hunting Read</div>$hunting_read_markup<div class="section-kicker">Movement Pattern Snapshot</div>$cluster_markup<div class="section-kicker">Invalidators</div><div class="intel-row"><ul>$invalidators</ul></div><div class="section-kicker">Quick Focus</div><div class="mode-stack"><button class="mode-btn focus-btn" data-focus-rank="1" type="button">Primary</button><button class="mode-btn focus-btn" data-focus-rank="2" type="button">Alt #2</button><button class="mode-btn focus-btn" data-focus-rank="3" type="button">Alt #3</button></div><div class="section-kicker">Ranked Sit Locations</div>$ranked_rows</div></aside>
</div></div></div>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script>
(function() {
  const payload = $payload_json;
  window.__MONAHINGA_COMMAND_PAYLOAD = payload;
  const wildlifeAtmosphere = payload.wildlife_atmosphere || null;
  const viewer = document.getElementById('viewer');
  const tiltSlider = document.getElementById('tiltSlider');
  const depthSlider = document.getElementById('depthSlider');
  const terrainLayerStack = document.getElementById('terrainLayerStack');
  let layerButtons = Array.from(document.querySelectorAll('.layer-btn'));
  const padusButtons = Array.from(document.querySelectorAll('.mode-btn[data-padus-mode]'));
  const focusButtons = Array.from(document.querySelectorAll('.focus-btn'));
  const rowButtons = Array.from(document.querySelectorAll('.row-button'));
  const resetViewBtn = document.getElementById('resetViewBtn');
  const invisibleApproachBtn = document.getElementById('invisibleApproachBtn');
  const saveViewHelpBtn = document.getElementById('saveViewHelpBtn');
  const downloadSummaryBtn = document.getElementById('downloadSummaryBtn');
  const setBaseCampBtn = document.getElementById('setBaseCampBtn');
  const setAccessEntryBtn = document.getElementById('setAccessEntryBtn');
  const placeBaseCampBtn = document.getElementById('placeBaseCampBtn');
  const placeAccessEntryBtn = document.getElementById('placeAccessEntryBtn');
  const pinControlStatus = document.getElementById('pinControlStatus');
  const baseCampSummary = document.getElementById('baseCampSummary');
  const accessEntrySummary = document.getElementById('accessEntrySummary');
  const executiveSummaryContent = document.getElementById('executiveSummaryContent');
  const gameContextContent = document.getElementById('gameContextContent');
  const operatorWindValue = document.getElementById('operatorWindValue');
  const selectedSiteTitle = document.getElementById('selectedSiteTitle');
  const selectedSiteCoords = document.getElementById('selectedSiteCoords');
  const copyCoordsBtn = document.getElementById('copyCoordsBtn');
  const bestTimeLabelEl = document.getElementById('bestTimeLabel');
  const bestTimeWindowEl = document.getElementById('bestTimeWindow');
  const liveWindSummary = document.getElementById('liveWindSummary');
  const liveWindMeta = document.getElementById('liveWindMeta');
  const liveWindHudSummary = document.getElementById('liveWindHudSummary');
  const liveWindHudMeta = document.getElementById('liveWindHudMeta');
  const invisibleApproachHud = document.getElementById('invisibleApproachHud');
  const invisibleApproachSummary = document.getElementById('invisibleApproachSummary');
  const invisibleApproachMeta = document.getElementById('invisibleApproachMeta');
  const trustTags = document.getElementById('trustTags');
  const coverKeyLegend = document.getElementById('coverKeyLegend');
  const focusReadHint = document.getElementById('focusReadHint');
  const modeStatusChip = document.getElementById('modeStatusChip');
  const regionIdentityLabel = document.getElementById('regionIdentityLabel');
  const regionSpeciesLabel = document.getElementById('regionSpeciesLabel');
  const regionMoodLabel = document.getElementById('regionMoodLabel');
  const regionStory = document.getElementById('regionStory');
  const terrainIdentityNote = document.getElementById('terrainIdentityNote');
  const cursorHud = document.getElementById('cursorHud');
  const cursorCoords = document.getElementById('cursorCoords');
  const fieldMapSvg = document.getElementById('fieldMapSvg');
  const visualFocusToggle = document.getElementById('visualFocusToggle');
  const layoutRoot = document.querySelector('.layout');
  let updateFocusOverlay = function() {};
  let liveWindState = null;

  function refreshViewerAfterLayoutChange() {
    try {
      window.dispatchEvent(new Event('resize'));
    } catch (err) {}
  }
  function setVisualFocusMode(enabled) {
    if (!layoutRoot) return;
    layoutRoot.classList.toggle('visual-focus', !!enabled);
    if (visualFocusToggle) {
      visualFocusToggle.textContent = enabled ? 'Show AI Panel' : 'Hide AI Panel';
      visualFocusToggle.setAttribute('aria-pressed', enabled ? 'true' : 'false');
    }
    setTimeout(refreshViewerAfterLayoutChange, 80);
    setTimeout(refreshViewerAfterLayoutChange, 260);
  }
  if (visualFocusToggle) {
    visualFocusToggle.addEventListener('click', function() {
      const enabled = !(layoutRoot && layoutRoot.classList.contains('visual-focus'));
      setVisualFocusMode(enabled);
    });
  }

  function deriveRegionIdentity() {
    if (wildlifeAtmosphere && wildlifeAtmosphere.label) {
      const rawKey = String(wildlifeAtmosphere.region_key || "default");
      const themeKey = rawKey === "northern_rockies" ? "mountain" : rawKey;
      return {
        key: themeKey,
        label: wildlifeAtmosphere.label || "Regional wildlife atmosphere",
        species: wildlifeAtmosphere.species_label || "Regional game context",
        mood: wildlifeAtmosphere.mood || "Region-driven wildlife atmosphere",
        story: wildlifeAtmosphere.story || "Wildlife atmosphere is presentation only; the sit decision still comes from active terrain run data.",
        note: wildlifeAtmosphere.legal_note || "Wildlife atmosphere is presentation only. Verify regulations before hunting.",
      };
    }
    const center = payload.bbox_center || {};
    const lon = Number(center.lon || 0);
    const lat = Number(center.lat || 0);
    if (lon < -108 && lat > 36) {
      return {
        key: 'mountain',
        label: 'Mountain big-game terrain',
        species: 'Elk · Mule deer country',
        mood: 'Alpine shadow and ridge light',
        story: 'This box reads like western mountain country: cooler light, bigger relief, and hunt setups that feel more exposed, wind-sensitive, and terrain-driven.',
        note: 'Mountain presentation is cosmetic. The sit ranking still comes from the current run inputs, legality, cover proxy, and terrain logic.',
      };
    }
    if (lon > -90 && lat < 37) {
      return {
        key: 'southwoods',
        label: 'Southern timber terrain',
        species: 'Whitetail · Turkey country',
        mood: 'Humid timber and creek travel',
        story: 'This box reads like southern timber country: thicker cover, warmer understory tones, and setup value shaped by quiet entry and shaded movement.',
        note: 'Southern timber identity sets the visual mood only. Decision support still follows the live terrain and sit data.',
      };
    }
    if (lon > -104 && lon < -92 && lat > 35 && lat < 47) {
      return {
        key: 'plains',
        label: 'Plains edge terrain',
        species: 'Whitetail · Mule deer country',
        mood: 'Open edge and shelter breaks',
        story: 'This box reads like plains-edge hunting ground: cleaner horizon lines, sharper exposure choices, and movement shaped by cover islands and sheltered breaks.',
        note: 'Plains identity is atmosphere, not scoring. The sit stack still comes from the active hunt run.',
      };
    }
    return {
      key: 'appalachian',
      label: 'Appalachian whitetail terrain',
      species: 'Whitetail · Turkey country',
      mood: 'Shaded timber folds',
      story: 'This box reads like Appalachian whitetail country: layered timber folds, protected side-hill movement, and setup value that rewards disciplined access.',
      note: 'Appalachian identity is presentation only. The recommendation engine still comes from the run data shown on the page.',
    };
  }
  function applyTerrainWallpaper(identity) {
    const body = document.body;
    if (!body || !payload || !payload.layers) return;
    const src = payload.layers.terrain || payload.layers.relief || payload.layers.hillshade || payload.layers.slope;
    if (!src) return;
    const safeSrc = String(src).replace(/\\/g, '/').replace(/"/g, '%22');
    body.style.setProperty('--terrain-wallpaper-image', 'url("' + safeSrc + '")');
    body.classList.add('terrain-wallpaper-ready');
    if (identity && identity.key === 'mountain') {
      body.style.setProperty('--terrain-wallpaper-opacity', '.34');
    } else if (identity && identity.key === 'plains') {
      body.style.setProperty('--terrain-wallpaper-opacity', '.27');
    } else {
      body.style.setProperty('--terrain-wallpaper-opacity', '.30');
    }
  }
  function applyRegionIdentity(identity) {
    const body = document.body;
    if (body) {
      body.classList.remove('theme-default','theme-appalachian','theme-mountain','theme-plains','theme-southwoods');
      body.classList.add('theme-' + identity.key);
      applyTerrainWallpaper(identity);
    }
    const sceneShell = document.querySelector('.scene-shell');
    if (sceneShell) {
      sceneShell.classList.remove('region-appalachian','region-mountain','region-plains','region-southwoods');
      sceneShell.classList.add('region-' + identity.key);
    }
    if (regionIdentityLabel) regionIdentityLabel.textContent = identity.label;
    if (regionSpeciesLabel) regionSpeciesLabel.textContent = identity.species;
    if (regionMoodLabel) regionMoodLabel.textContent = identity.mood;
    if (regionStory) regionStory.textContent = identity.story;
    if (terrainIdentityNote) terrainIdentityNote.textContent = identity.note;
  }
  const state = { baseExaggeration: 1.0, currentTexture: (payload.defaultLayer === 'cover' ? 'terrain' : (payload.defaultLayer || 'terrain')), currentPadusMode: payload.defaultPadusMode || 'hybrid', widthWorld: 24, depthWorld: 24, rotationY: -0.92, tiltDeg: Number(tiltSlider.value || 30), cameraRadius: 18, pinControlMode: null, pinControlIndex: -1, pinControlLabel: '', invisibleApproachVisible: false, invisibleApproachRank: 1 };
  const FEATURE_TYPES = Object.freeze({
    MARKER: 'marker',
    POLYLINE: 'polyline',
    DECAL: 'decal',
    ANALYTICAL: 'analytical',
    DIRECTIONAL: 'directional',
  });
  const overlayRegistry = [];
  const userPinGroups = [];
  const anchorGroups = [];
  let pinControlJustActivated = false;
  const STORAGE_KEYS = Object.freeze({ userPins: "userPins", baseCamp: "baseCampGps", accessEntry: "accessEntryGps" });
  function showError(message) { viewer.innerHTML = '<div class="error-card">Viewer failed to load.\n' + String(message) + '</div>'; }
  if (!window.THREE) { showError('Three.js did not load in the browser.'); return; }
  function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
  function tierColorValue(tier) { if (tier === 'primary') return 0x27e8ff; if (tier === 'alternate') return 0xffc247; return 0xff4a78; }
  function tierColor(tier) { return new THREE.Color(tierColorValue(tier)); }
  function legalColor(cls) { if (cls === 'legal') return new THREE.Color(0x8fe58f); if (cls === 'restricted') return new THREE.Color(0xd98686); return new THREE.Color(0xe4bb74); }
  function hexColor(colorObj) { return Number(colorObj.getHex()); }
  function safeNorm(v) { return clamp(Number(v) || 0, 0, 1); }
  function normToWorld(x, y, width, depth) { const nx = safeNorm(x); const ny = safeNorm(y); return new THREE.Vector3((nx - 0.5) * width, 0, (ny - 0.5) * depth); }
  function sampleHeight(grid, rows, cols, x, y) { const fx = clamp(x,0,1)*(cols-1); const fy = clamp(y,0,1)*(rows-1); const x0=Math.floor(fx), y0=Math.floor(fy), x1=Math.min(cols-1,x0+1), y1=Math.min(rows-1,y0+1); const tx=fx-x0, ty=fy-y0; const q11=grid[y0*cols+x0]||0, q21=grid[y0*cols+x1]||0, q12=grid[y1*cols+x0]||0, q22=grid[y1*cols+x1]||0; const top=q11*(1-tx)+q21*tx; const bot=q12*(1-tx)+q22*tx; return top*(1-ty)+bot*ty; }
  function computeReliefFocus(grid, rows, cols) { let min=Infinity,max=-Infinity,peakIndex=0,total=0,sumX=0,sumY=0; for (let i=0;i<grid.length;i++){const v=Number(grid[i]||0); if(v<min)min=v; if(v>max){max=v; peakIndex=i;}} if(!Number.isFinite(min)||!Number.isFinite(max)||max<=min){return {nx:.5,ny:.5,relief:0};} for(let row=0;row<rows;row++){for(let col=0;col<cols;col++){const idx=row*cols+col; const v=Number(grid[idx]||0); const nx=cols<=1?0.5:col/(cols-1); const ny=rows<=1?0.5:row/(rows-1); const local=Math.max(0,(v-min)/(max-min)); const biasX=1-Math.abs(nx-.5)*.55; const biasY=1-Math.abs(ny-.5)*.55; const w=Math.max(.0001, local*local*biasX*biasY); total+=w; sumX+=nx*w; sumY+=ny*w; }} const peakCol=peakIndex%cols, peakRow=Math.floor(peakIndex/cols); const peakNx=cols<=1?.5:peakCol/(cols-1), peakNy=rows<=1?.5:peakRow/(rows-1); if(total<=0){return {nx:peakNx,ny:peakNy,relief:max-min};} return {nx:clamp((sumX/total)*0.68+peakNx*0.32,0.18,0.82), ny:clamp((sumY/total)*0.68+peakNy*0.32,0.18,0.82), relief:max-min}; }
  function setButtonActive(key) { layerButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.layer === key)); }
  function setCoverReadUi(key) {
    const terrainRead = key === 'terrain';
    if (coverKeyLegend) coverKeyLegend.classList.toggle('visible', terrainRead);
    if (focusReadHint) focusReadHint.classList.toggle('visible', terrainRead);
    if (modeStatusChip) {
      modeStatusChip.textContent = terrainRead ? 'Terrain + Cover Read' : ((key || 'terrain').charAt(0).toUpperCase() + (key || 'terrain').slice(1) + ' View');
      modeStatusChip.style.borderColor = terrainRead ? 'rgba(174,241,134,.24)' : 'rgba(255,255,255,.08)';
      modeStatusChip.style.background = terrainRead ? 'rgba(174,241,134,.10)' : 'rgba(8,15,25,.78)';
      modeStatusChip.style.color = terrainRead ? '#eef8e5' : '#ece3d5';
    }
  }
  function stripCoverLayerButton() {
    if (!terrainLayerStack) return;
    const coverBtn = terrainLayerStack.querySelector('[data-layer="cover"]');
    if (coverBtn && coverBtn.parentNode) coverBtn.parentNode.removeChild(coverBtn);
    layerButtons = Array.from(document.querySelectorAll('.layer-btn')).filter((btn) => btn.dataset.layer !== 'cover');
  }
  function setPadusModeActive(mode) { padusButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.padusMode === mode)); }
  function setFocusActive(rank) { focusButtons.forEach(btn => btn.classList.toggle('active', Number(btn.dataset.focusRank) === Number(rank))); rowButtons.forEach(btn => btn.classList.toggle('active', Number(btn.dataset.rank) === Number(rank))); }
  function sitePoint(site) { return { nx:safeNorm((site.lon-payload.bbox[0])/(payload.bbox[2]-payload.bbox[0])), ny:safeNorm((site.lat-payload.bbox[1])/(payload.bbox[3]-payload.bbox[1])) }; }
  function corridorPoint(pt) { return { nx:safeNorm((pt[0]-payload.bbox[0])/(payload.bbox[2]-payload.bbox[0])), ny:safeNorm((pt[1]-payload.bbox[1])/(payload.bbox[3]-payload.bbox[1])) }; }
  function siteByRank(rank) { return (payload.sites || []).find(item => Number(item.rank) === Number(rank)); }
  function formatSiteCoords(site) { if (!site) return ''; return 'Lat ' + Number(site.lat).toFixed(6) + ' · Lon ' + Number(site.lon).toFixed(6) + ' · ' + Math.round(Number(site.elevation_m) || 0) + ' m'; }

  function fieldMapPointFromNorm(nx, ny) {
    return { x: clamp(safeNorm(nx) * 100, 5, 95), y: clamp((1 - safeNorm(ny)) * 100, 5, 95) };
  }
  function fieldMapPointFromGps(point) {
    const norm = latLonToNormalized(point.lat, point.lon);
    return fieldMapPointFromNorm(norm.nx, norm.ny);
  }
  function escapeSvgText(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function update2DFieldMap(selectedSite) {
    if (!fieldMapSvg || !payload || !payload.bbox) return;
    const sites = (payload.sites || []).slice(0, 3);
    const active = selectedSite || siteByRank(state.invisibleApproachRank || 1) || siteByRank(1) || sites[0] || null;
    const baseCamp = getAnchorPoint('baseCamp');
    const accessEntry = getAnchorPoint('accessEntry') || baseCamp;
    const basePt = baseCamp ? fieldMapPointFromGps(baseCamp) : fieldMapPointFromNorm(0.5, 0.5);
    const entryPt = accessEntry ? fieldMapPointFromGps(accessEntry) : fieldMapPointFromNorm(0.5, 0.92);
    const activePt = active ? fieldMapPointFromNorm(sitePoint(active).nx, sitePoint(active).ny) : null;

    let html = '';
    [25, 50, 75].forEach(function(v) {
      html += '<line class="field-map-grid" x1="' + v + '" y1="0" x2="' + v + '" y2="100"></line>';
      html += '<line class="field-map-grid" x1="0" y1="' + v + '" x2="100" y2="' + v + '"></line>';
    });
    html += '<rect x="1.2" y="1.2" width="97.6" height="97.6" rx="3" fill="none" stroke="rgba(255,255,255,.18)" stroke-width=".7"></rect>';

    if (activePt) {
      html += '<path class="field-map-path" d="M ' + entryPt.x.toFixed(1) + ' ' + entryPt.y.toFixed(1) + ' Q ' + ((entryPt.x + activePt.x) / 2).toFixed(1) + ' ' + Math.max(8, ((entryPt.y + activePt.y) / 2) - 8).toFixed(1) + ' ' + activePt.x.toFixed(1) + ' ' + activePt.y.toFixed(1) + '"></path>';
    }

    sites.forEach(function(site, idx) {
      const p = fieldMapPointFromNorm(sitePoint(site).nx, sitePoint(site).ny);
      const cls = idx === 0 ? 'field-map-ring-primary' : (idx === 1 ? 'field-map-ring-alt' : 'field-map-ring-third');
      const label = idx === 0 ? 'P1' : (idx === 1 ? 'S2' : 'T3');
      html += '<circle class="' + cls + '" cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="' + (idx === 0 ? 4.8 : 4.0) + '"></circle>';
      html += '<text class="field-map-label" x="' + Math.min(90, p.x + 3).toFixed(1) + '" y="' + Math.max(7, p.y - 3).toFixed(1) + '">' + label + '</text>';
      html += '<text class="field-map-small" x="' + Math.min(84, p.x + 3).toFixed(1) + '" y="' + Math.min(96, p.y + 5).toFixed(1) + '">' + escapeSvgText(String(site.title || '').slice(0, 18)) + '</text>';
    });

    html += '<circle class="field-map-base" cx="' + basePt.x.toFixed(1) + '" cy="' + basePt.y.toFixed(1) + '" r="3.4"></circle>';
    html += '<text class="field-map-label" x="' + Math.min(82, basePt.x + 3).toFixed(1) + '" y="' + Math.max(7, basePt.y - 3).toFixed(1) + '">Base</text>';

    html += '<circle class="field-map-entry" cx="' + entryPt.x.toFixed(1) + '" cy="' + entryPt.y.toFixed(1) + '" r="3.4"></circle>';
    html += '<text class="field-map-label" x="' + Math.min(82, entryPt.x + 3).toFixed(1) + '" y="' + Math.min(96, entryPt.y + 5).toFixed(1) + '">Entry</text>';

    html += '<text class="field-map-small" x="47" y="6">NORTH</text>';
    html += '<text class="field-map-small" x="47" y="98">SOUTH</text>';
    html += '<text class="field-map-small" x="3" y="52">W</text>';
    html += '<text class="field-map-small" x="94" y="52">E</text>';

    fieldMapSvg.innerHTML = html;
  }

  function normalizedToLatLon(nx, ny) {
    const minLon = Number(payload.bbox[0] || 0), minLat = Number(payload.bbox[1] || 0), maxLon = Number(payload.bbox[2] || 0), maxLat = Number(payload.bbox[3] || 0);
    return {
      lat: minLat + safeNorm(ny) * (maxLat - minLat),
      lon: minLon + safeNorm(nx) * (maxLon - minLon),
    };
  }
  function latLonToNormalized(lat, lon) {
    const minLon = Number(payload.bbox[0] || 0), minLat = Number(payload.bbox[1] || 0), maxLon = Number(payload.bbox[2] || 0), maxLat = Number(payload.bbox[3] || 0);
    return {
      nx: safeNorm((Number(lon) - minLon) / Math.max(1e-9, (maxLon - minLon))),
      ny: safeNorm((Number(lat) - minLat) / Math.max(1e-9, (maxLat - minLat))),
    };
  }
  function haversineMiles(a, b) {
    const toRad = (deg) => deg * Math.PI / 180;
    const R = 3958.8;
    const dLat = toRad(Number(b.lat) - Number(a.lat));
    const dLon = toRad(Number(b.lon) - Number(a.lon));
    const lat1 = toRad(Number(a.lat));
    const lat2 = toRad(Number(b.lat));
    const sin1 = Math.sin(dLat / 2), sin2 = Math.sin(dLon / 2);
    const h = sin1 * sin1 + Math.cos(lat1) * Math.cos(lat2) * sin2 * sin2;
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
  }
  function bearingLabel(a, b) {
    const toRad = (deg) => deg * Math.PI / 180;
    const toDeg = (rad) => rad * 180 / Math.PI;
    const lat1 = toRad(Number(a.lat)), lat2 = toRad(Number(b.lat));
    const dLon = toRad(Number(b.lon) - Number(a.lon));
    const y = Math.sin(dLon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    const bearing = (toDeg(Math.atan2(y, x)) + 360) % 360;
    const dirs = ['N','NE','E','SE','S','SW','W','NW'];
    return dirs[Math.round(bearing / 45) % 8];
  }
  function inferCoverLabel(site) {
    const corpus = ((site && (site.reason || site.title || '')) + ' ' + JSON.stringify((site && site.tags) || (site && site.primary_tags) || [])).toLowerCase();
    if (/cover|conceal|security|shelter|bedding/.test(corpus)) return 'Strong Cover';
    if (/edge|shoulder|bench|travel/.test(corpus)) return 'Moderate Cover';
    return 'Open / Needs Field Check';
  }
  function inferAccessLabel(site) {
    const corpus = ((site && (site.reason || site.title || '')) + ' ' + JSON.stringify((site && site.tags) || (site && site.primary_tags) || [])).toLowerCase();
    if (/interior|legal access|easy|creek|road/.test(corpus)) return 'Reasonable Access';
    if (/ridge|climb|bench/.test(corpus)) return 'Moderate Access';
    return 'Field Verify Access';
  }
  function inferLegalLabel(site) {
    const corpus = ((site && (site.reason || site.title || '')) + ' ' + JSON.stringify((site && site.tags) || (site && site.primary_tags) || []) + ' ' + String(payload.legal_badge || '')).toLowerCase();
    if (/legal|verified|state game land|pad-us/.test(corpus)) return 'Likely Legal — Verify On Arrival';
    if (/restricted|boundary|edge/.test(corpus)) return 'Boundary / Legality Check';
    return 'Confirm Legality In Field';
  }
  function inferBestTimeLabel(site) {
    return deriveDecisionProfile(site).whenLabel;
  }
  function siteCorpus(site) {
    return ((site && (site.reason || site.title || '')) + ' ' + JSON.stringify((site && site.tags) || (site && site.primary_tags) || []) + ' ' + String(payload.best_time_window || '')).toLowerCase();
  }
  function firstMatchingLabel(corpus, rules, fallback) {
    for (const rule of rules) {
      if (rule.matchers.some((matcher) => corpus.includes(matcher))) return rule.label;
    }
    return fallback;
  }
  function deriveDecisionProfile(site) {
    const corpus = siteCorpus(site);
    const reasons = [];
    const risks = [];
    const priorities = [];
    const addUnique = (arr, value) => { if (value && !arr.includes(value)) arr.push(value); };

    const timingRules = [
      { key: 'morning', matchers: ['bedding', 'security', 'conceal', 'cover', 'bench bedding edge', 'interior security', 'dawn', 'morning'], whenLabel: 'Morning Hunt', whenWindow: 'First light through mid-morning', reason: 'Security cover suggests daylight movement back toward bedding.' },
      { key: 'evening', matchers: ['feeding', 'field edge', 'crop', 'dusk', 'evening', 'destination'], whenLabel: 'Evening Hunt', whenWindow: 'Late afternoon through last legal light', reason: 'Destination-style movement is more likely late in the day.' },
      { key: 'both', matchers: ['funnel', 'convergence', 'travel intercept', 'travel lane', 'ridge funnel', 'shoulder travel lane', 'saddle'], whenLabel: 'Morning + Evening', whenWindow: 'First light and last light both rate well', reason: 'Terrain funneling can pull movement during both ends of the day.' },
    ];

    let chosenTiming = timingRules.find((rule) => rule.matchers.some((matcher) => corpus.includes(matcher)));
    if (!chosenTiming) {
      chosenTiming = site && Number(site.rank) === 1
        ? { whenLabel: 'Morning + Evening', whenWindow: 'Start with first light, then re-check for evening travel', reason: 'Top-ranked sit gets the broadest scouting priority.' }
        : { whenLabel: 'Morning Check', whenWindow: 'Scout first light and verify sign for evening use', reason: 'Needs field confirmation before committing to a narrow window.' };
    }

    addUnique(reasons, chosenTiming.reason);

    const reasonRules = [
      { matchers: ['core converge', 'convergence', 'ridge funnel', 'funnel', 'saddle'], label: 'Terrain funnel concentrates movement through a smaller decision point.' },
      { matchers: ['bench', 'bedding', 'interior security', 'security', 'conceal', 'cover'], label: 'Security cover nearby supports daylight confidence and repeatability.' },
      { matchers: ['travel intercept', 'travel lane', 'shoulder', 'edge', 'bench bedding edge'], label: 'This sit lines up with a natural travel lane or edge transition.' },
      { matchers: ['legal interior access', 'verified legal access', 'legal access', 'state game land', 'pad-us'], label: 'Legal access appears favorable relative to the current box.' },
      { matchers: ['creek', 'water', 'drainage'], label: 'Terrain and drainage features may help hide movement and entry.' },
    ];
    reasonRules.forEach((rule) => {
      if (rule.matchers.some((matcher) => corpus.includes(matcher))) addUnique(reasons, rule.label);
    });

    const riskRules = [
      { matchers: ['boundary', 'restricted', 'edge management', 'coverage edge'], label: 'Boundary or legality edge needs an on-site confirmation before committing.' },
      { matchers: ['open', 'exposure', 'ridge', 'crest'], label: 'Exposure risk rises if wind or visibility shifts the wrong way.' },
      { matchers: ['climb', 'steep', 'ridge'], label: 'Access effort could slow entry and exit timing.' },
    ];
    riskRules.forEach((rule) => {
      if (rule.matchers.some((matcher) => corpus.includes(matcher))) addUnique(risks, rule.label);
    });
    if (!liveWindState || !liveWindState.summary) addUnique(risks, 'Live wind is unavailable, so field confirmation matters more.');
    if (!risks.length) addUnique(risks, 'Main risk is a wind shift or unexpected human pressure on the approach.');

    const priorityRules = [
      { matchers: ['legal interior access', 'verified legal access', 'state game land', 'pad-us'], label: 'Legality / access confidence' },
      { matchers: ['bedding', 'security', 'cover', 'conceal'], label: 'Security cover alignment' },
      { matchers: ['funnel', 'convergence', 'travel intercept', 'travel lane', 'shoulder', 'edge'], label: 'Terrain-driven movement funnel' },
      { matchers: ['creek', 'drainage', 'bench'], label: 'Low-visibility terrain approach' },
    ];
    priorityRules.forEach((rule) => {
      if (rule.matchers.some((matcher) => corpus.includes(matcher))) addUnique(priorities, rule.label);
    });
    if (!priorities.length) {
      addUnique(priorities, 'Terrain shape and current sit rank');
      addUnique(priorities, 'Cover and access read');
    }

    return {
      whenLabel: chosenTiming.whenLabel,
      whenWindow: chosenTiming.whenWindow,
      why: reasons.slice(0, 4),
      risks: risks.slice(0, 3),
      priorities: priorities.slice(0, 4),
    };
  }
  function deriveGameContext(site) {
const speciesControl = document.getElementById('viewer_species') || { value: 'default' };
const selected = speciesControl ? speciesControl.value : 'default';

    if (selected && selected !== 'default') {
      const speciesLabels = {
        whitetail: 'Whitetail Deer',
        mule_deer: 'Mule Deer',
        elk: 'Elk',
        moose: 'Moose',
        bighorn: 'Bighorn Sheep',
        pronghorn: 'Pronghorn',
        black_bear: 'Black Bear',
        turkey: 'Wild Turkey',
        hog: 'Feral Hog',
        coyote: 'Coyote',
        javelina: 'Javelina'
      };

      return {
        primary: speciesLabels[selected] || selected,
        secondary: [],
        movement: 'User-selected species logic is active for this terrain read.',
        confidence: 'Selected',
        why: 'The 3D species selector is driving the live wildlife read and Invisible Approach bias.',
        cover: inferCoverLabel(site)
      };
    }

    const identity = deriveRegionIdentity();
    const corpus = siteCorpus(site);
    const coverLabel = inferCoverLabel(site);
    const wildlifeSpecies = wildlifeAtmosphere && Array.isArray(wildlifeAtmosphere.species) ? wildlifeAtmosphere.species : [];

    const primaryMap = {
      appalachian: 'Whitetail',
      mountain: 'Elk',
      plains: 'Whitetail',
      southwoods: 'Whitetail',
    };

    const secondaryMap = {
      appalachian: ['Turkey', 'Black Bear'],
      mountain: ['Mule Deer', 'Turkey'],
      plains: ['Turkey', 'Mule Deer'],
      southwoods: ['Turkey', 'Feral Hog'],
    };    let movement = 'Edge travel and terrain-led movement are the main read here.';
    if (/bedding|security|conceal|bench/.test(corpus)) movement = 'Security-cover movement near bedding looks most relevant here.';
    else if (/funnel|convergence|travel lane|intercept|saddle|shoulder/.test(corpus)) movement = 'Terrain funnel travel is the strongest movement pattern here.';
    else if (/feeding|destination|field/.test(corpus)) movement = 'Feed-bound evening movement is the strongest pattern here.';

    let confidence = 'Moderate';
    if (site && Number(site.rank) === 1) confidence = 'High';
    else if (/funnel|convergence|bedding|security/.test(corpus)) confidence = 'High';
    else if (/open|exposure/.test(corpus)) confidence = 'Low-Moderate';

    let why = 'This game context comes from region identity, terrain shape, cover proxy, and the current sit explanation.';
    if (/ridge|bench|side-hill|shoulder/.test(corpus)) why = 'Benches, side-hills, and shoulder terrain usually support disciplined deer movement and setup repeatability.';
    else if (/creek|drainage/.test(corpus)) why = 'Drainage and low-visibility terrain often support quieter animal movement and cleaner entry.';
    else if (/funnel|convergence|saddle/.test(corpus)) why = 'Funnels and convergence points increase the odds of movement compressing into a smaller window.';
    else if (/feeding|field/.test(corpus)) why = 'Open-to-cover transitions make this read more relevant for late travel and cautious approach decisions.';

    return {
      primary: (wildlifeSpecies[0] && wildlifeSpecies[0].name) || primaryMap[identity.key] || 'Whitetail',
      secondary: (wildlifeSpecies.length ? wildlifeSpecies.slice(1, 3).map((item) => item.name) : (secondaryMap[identity.key] || ['Turkey'])).slice(0, 2),
      movement,
      confidence,
      why,
      cover: coverLabel,
    };
  }
  function updateGameContextForSite(site) {
    if (!gameContextContent || !site) return;
    const gc = deriveGameContext(site);
    gameContextContent.innerHTML =
      '<span class="game-context-primary">Primary target: ' + gc.primary + '</span>' +
      '<span class="game-context-secondary">Secondary: ' + gc.secondary.join(' · ') + '</span>' +
      '<div class="micro-copy" style="margin-top:6px">Movement: ' + gc.movement + '</div>' +
      '<div class="micro-copy">Confidence: ' + gc.confidence + ' · Cover read: ' + gc.cover + '</div>' +
      '<div class="micro-copy">Why it matters: ' + gc.why + '</div>';
  }
  function updateGameContextForAnchor(label) {
    if (!gameContextContent) return;
    gameContextContent.innerHTML =
      '<span class="game-context-primary">' + label + ' reference</span>' +
      '<span class="game-context-secondary">Use this anchor to judge entry, exit, and distance—not game behavior by itself.</span>';
  }
  function buildExecutiveSummaryHtml(title, rows) {
    return '<div class="intel-row provider-ok"><strong>' + title + '</strong><span>' + rows.join('<br>') + '</span></div>';
  }
  function buildDecisionLeadHtml(label, windowText, whyText) {
    return '<div class="exec-decision"><strong>Best move</strong><span>' + label + '</span><em>' + windowText + (whyText ? '<br>' + whyText : '') + '</em></div>';
  }
  function updateExecutiveSummaryForSite(site) {
    if (!site || !executiveSummaryContent) return;
    const baseCamp = getAnchorPoint('baseCamp');
    const siteCoords = { lat: Number(site.lat), lon: Number(site.lon) };
    const distance = baseCamp ? haversineMiles(baseCamp, siteCoords).toFixed(1) + ' mi ' + bearingLabel(baseCamp, siteCoords) + ' of Base Camp' : 'Base Camp not set';
    const windLine = liveWindState && liveWindState.summary ? liveWindState.summary : 'Live wind loading or unavailable';
    const decision = deriveDecisionProfile(site);
    if (bestTimeLabelEl) bestTimeLabelEl.textContent = decision.whenLabel;
    if (bestTimeWindowEl) bestTimeWindowEl.textContent = decision.whenWindow;
    updateGameContextForSite(site);
    executiveSummaryContent.innerHTML =
      buildDecisionLeadHtml(decision.whenLabel, decision.whenWindow, decision.why[0] || '') +
      buildExecutiveSummaryHtml(
        site.title || 'Selected Sit',
        [
          'Priority Stack: ' + decision.priorities.join(' | '),
          'Why: ' + decision.why.join(' | '),
          'Risk: ' + decision.risks.join(' | '),
          'Legal: ' + inferLegalLabel(site),
          'Access: ' + inferAccessLabel(site),
          'Cover: ' + inferCoverLabel(site),
          'Wind: ' + windLine,
          'GPS: ' + Number(site.lat).toFixed(5) + ', ' + Number(site.lon).toFixed(5),
          'Base Camp Relation: ' + distance,
        ]
      );
  }
  function updateExecutiveSummaryForAnchor(label, point, note) {
    if (!executiveSummaryContent || !point) return;
    updateGameContextForAnchor(label);
    executiveSummaryContent.innerHTML = buildExecutiveSummaryHtml(
      label,
      [
        note || label + ' anchor',
        'GPS: ' + Number(point.lat).toFixed(5) + ', ' + Number(point.lon).toFixed(5),
      ]
    );
    if (bestTimeLabelEl) bestTimeLabelEl.textContent = 'Field Reference';
    if (bestTimeWindowEl) bestTimeWindowEl.textContent = 'Use this anchor to plan access, timing, and exit routes.';
  }
function pointInsideCurrentBbox(point) {
  if (!point || !payload || !payload.bbox) return false;
  const minLon = Number(payload.bbox[0]);
  const minLat = Number(payload.bbox[1]);
  const maxLon = Number(payload.bbox[2]);
  const maxLat = Number(payload.bbox[3]);
  const lat = Number(point.lat);
  const lon = Number(point.lon);
  return Number.isFinite(lat) && Number.isFinite(lon) && lat >= minLat && lat <= maxLat && lon >= minLon && lon <= maxLon;
}

function defaultAnchorPoint(kind) {
  if (kind === 'baseCamp') {
    const center = payload.bbox_center || normalizedToLatLon(0.5, 0.5);
    return { lat: Number(center.lat || normalizedToLatLon(0.5, 0.5).lat), lon: Number(center.lon || normalizedToLatLon(0.5, 0.5).lon), label: 'Base Camp' };
  }

  const primary = siteByRank(1);
  if (primary) {
    const fallback = normalizedToLatLon(sitePoint(primary).nx, 0.92);
    return { lat: fallback.lat, lon: fallback.lon, label: 'Access Entry' };
  }

  const south = normalizedToLatLon(0.5, 0.92);
  return { lat: south.lat, lon: south.lon, label: 'Access Entry' };
}

function getAnchorPoint(kind) {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS[kind]);
    if (raw) {
      const stored = JSON.parse(raw);
      if (pointInsideCurrentBbox(stored)) return stored;
      localStorage.removeItem(STORAGE_KEYS[kind]);
    }
  } catch (err) {
    localStorage.removeItem(STORAGE_KEYS[kind]);
  }

  const fallback = defaultAnchorPoint(kind);
  saveAnchorPoint(kind, fallback);
  return fallback;
}
  function saveAnchorPoint(kind, point) {
    localStorage.setItem(STORAGE_KEYS[kind], JSON.stringify(point));
  }
  function getStoredUserPins() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEYS.userPins) || '[]'); } catch (err) { return []; }
  }
  function saveStoredUserPins(pins) {
    localStorage.setItem(STORAGE_KEYS.userPins, JSON.stringify(pins));
  }
  function updatePinControlStatus() {
    if (!pinControlStatus) return;
    if (!state.pinControlMode) {
      pinControlStatus.textContent = 'Shift + click adds a named field pin. Click any field pin to rename, move, or delete it. Click Base Camp or Access Entry for coordinates and edit options.';
      return;
    }
    if (state.pinControlMode === 'placeBaseCamp') {
      pinControlStatus.textContent = 'Placement mode active: click the terrain to set Base Camp.';
      return;
    }
    if (state.pinControlMode === 'placeAccessEntry') {
      pinControlStatus.textContent = 'Placement mode active: click the terrain to set Access Entry.';
      return;
    }
    if (state.pinControlMode === 'moveUserPin') {
      pinControlStatus.textContent = 'Placement mode active: click the terrain to move ' + (state.pinControlLabel || 'the selected field pin') + '.';
      return;
    }
  }
  function clearPinControlMode() {
    state.pinControlMode = null;
    state.pinControlIndex = -1;
    state.pinControlLabel = '';
    pinControlJustActivated = false;
    updatePinControlStatus();
    [placeBaseCampBtn, placeAccessEntryBtn].forEach((btn) => { if (btn) btn.classList.remove('active'); });
  }
  function beginPinControlMode(mode, index, label) {
    state.pinControlMode = mode;
    state.pinControlIndex = Number.isFinite(Number(index)) ? Number(index) : -1;
    state.pinControlLabel = label || '';
    pinControlJustActivated = true;
    [placeBaseCampBtn, placeAccessEntryBtn].forEach((btn) => { if (btn) btn.classList.remove('active'); });
    if (mode === 'placeBaseCamp' && placeBaseCampBtn) placeBaseCampBtn.classList.add('active');
    if (mode === 'placeAccessEntry' && placeAccessEntryBtn) placeAccessEntryBtn.classList.add('active');
    updatePinControlStatus();
  }
  function promptForAnchor(kind, label) {
    const current = getAnchorPoint(kind);
    const latInput = window.prompt(label + ' latitude', current ? Number(current.lat).toFixed(6) : '');
    if (latInput === null) return;
    const lonInput = window.prompt(label + ' longitude', current ? Number(current.lon).toFixed(6) : '');
    if (lonInput === null) return;
    const lat = Number(latInput), lon = Number(lonInput);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) { window.alert('Enter valid GPS coordinates.'); return; }
    saveAnchorPoint(kind, { lat, lon, label });
    updateAnchorSummaries();
    rebuildOverlays();
  }
  function updateAnchorSummaries() {
    const baseCamp = getAnchorPoint('baseCamp');
    const accessEntry = getAnchorPoint('accessEntry');
    if (baseCampSummary && baseCamp) baseCampSummary.textContent = Number(baseCamp.lat).toFixed(5) + ', ' + Number(baseCamp.lon).toFixed(5);
    if (accessEntrySummary && accessEntry) accessEntrySummary.textContent = Number(accessEntry.lat).toFixed(5) + ', ' + Number(accessEntry.lon).toFixed(5);
    update2DFieldMap();
  }
  function escapeSummaryText(value) {
    return String(value == null ? '' : value).replace(/\r?\n/g, ' ').trim();
  }
  function getSelectedSiteForExport() {
    if (selectedSiteTitle && selectedSiteTitle.textContent) {
      const byTitle = (payload.sites || []).find((item) => String(item.title || '') === String(selectedSiteTitle.textContent || ''));
      if (byTitle) return byTitle;
    }
    return siteByRank(1) || (payload.sites || [])[0] || null;
  }
  function currentExecutiveSummaryText() {
    if (!executiveSummaryContent) return '';
    return escapeSummaryText(executiveSummaryContent.innerText || executiveSummaryContent.textContent || '');
  }
  function buildSummaryText() {
    const site = getSelectedSiteForExport();
    const baseCamp = getAnchorPoint('baseCamp');
    const accessEntry = getAnchorPoint('accessEntry');
    const pins = JSON.parse(localStorage.getItem(STORAGE_KEYS.userPins) || '[]');
    const lines = [];
    lines.push('MONAHINGA™ HUNT SUMMARY');
    lines.push('');
    if (site) {
      const decision = deriveDecisionProfile(site);
      lines.push('Selected Sit: ' + escapeSummaryText(site.title || 'Selected Sit'));
      lines.push('Sit GPS: ' + Number(site.lat).toFixed(6) + ', ' + Number(site.lon).toFixed(6));
      lines.push('Elevation: ' + Math.round(Number(site.elevation_m) || 0) + ' m');
      lines.push('Confidence: ' + escapeSummaryText(site.score || 'N/A'));
      lines.push('When: ' + decision.whenLabel + ' — ' + decision.whenWindow);
      lines.push('Why: ' + decision.why.join(' | '));
      lines.push('Priority Stack: ' + decision.priorities.join(' | '));
      lines.push('Risk: ' + decision.risks.join(' | '));
      lines.push('Legal: ' + inferLegalLabel(site));
      lines.push('Access: ' + inferAccessLabel(site));
      lines.push('Cover: ' + inferCoverLabel(site));
      const gameContext = deriveGameContext(site);
      lines.push('Wind: ' + escapeSummaryText(liveWindState && liveWindState.summary ? liveWindState.summary : 'Unavailable'));
      lines.push('Likely Game Context: ' + gameContext.primary + ' primary | ' + gameContext.secondary.join(' / ') + ' secondary');
      lines.push('Movement Read: ' + gameContext.movement);
      if (baseCamp) {
        const siteCoords = { lat: Number(site.lat), lon: Number(site.lon) };
        lines.push('Base Camp Relation: ' + haversineMiles(baseCamp, siteCoords).toFixed(1) + ' mi ' + bearingLabel(baseCamp, siteCoords) + ' of Base Camp');
      }
      lines.push('');
    }
    lines.push('Executive Summary:');
    lines.push(currentExecutiveSummaryText() || 'No executive summary available.');
    lines.push('');
    if (baseCamp) lines.push('Base Camp: ' + Number(baseCamp.lat).toFixed(6) + ', ' + Number(baseCamp.lon).toFixed(6));
    if (accessEntry) lines.push('Access Entry: ' + Number(accessEntry.lat).toFixed(6) + ', ' + Number(accessEntry.lon).toFixed(6));
    lines.push('');
    lines.push('Field Pins:');
    if (pins.length) {
      pins.forEach((pin, idx) => {
        const coords = (Number.isFinite(Number(pin.lat)) && Number.isFinite(Number(pin.lon)))
          ? { lat: Number(pin.lat), lon: Number(pin.lon) }
          : normalizedToLatLon(pin.nx, pin.ny);
        lines.push('- ' + (idx + 1) + '. ' + escapeSummaryText(pin.note || ('Field Pin ' + (idx + 1))) + ' — ' + Number(coords.lat).toFixed(6) + ', ' + Number(coords.lon).toFixed(6));
      });
    } else {
      lines.push('- None saved');
    }
    lines.push('');
    lines.push('AI-optimized guidance: verify legality, safety, access, and field conditions before acting on any recommendation.');
    return lines.join('\n');
  }
  function collectSnapshotPins() {
    const pins = JSON.parse(localStorage.getItem(STORAGE_KEYS.userPins) || '[]');
    return pins.map((pin, idx) => {
      const coords = (Number.isFinite(Number(pin.lat)) && Number.isFinite(Number(pin.lon)))
        ? { lat: Number(pin.lat), lon: Number(pin.lon) }
        : normalizedToLatLon(pin.nx, pin.ny);
      const norm = (Number.isFinite(Number(pin.nx)) && Number.isFinite(Number(pin.ny)))
        ? { nx: Number(pin.nx), ny: Number(pin.ny) }
        : latLonToNormalized(coords.lat, coords.lon);
      return { label: pin.note || ('Field Pin ' + (idx + 1)), lat: coords.lat, lon: coords.lon, nx: norm.nx, ny: norm.ny };
    });
  }
  function loadImageForReport(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src + (src.indexOf('?') >= 0 ? '&' : '?') + 'reportTs=' + Date.now();
    });
  }
  function safeRoundRect(ctx, x, y, w, h, r) {
    const radius = Math.max(0, Math.min(Number(r) || 0, Math.abs(w) / 2, Math.abs(h) / 2));
    if (ctx && typeof ctx.roundRect === 'function') {
      ctx.roundRect(x, y, w, h, radius);
      return;
    }
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + w - radius, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
    ctx.lineTo(x + w, y + h - radius);
    ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
    ctx.lineTo(x + radius, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
  }
  function drawReportMarker(ctx, x, y, color, label, style) {
    ctx.save();
    ctx.translate(x, y);
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.lineWidth = 2;
    ctx.fillStyle = color;
    if (style === 'anchor') {
      ctx.beginPath();
      ctx.arc(0, 0, 12, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, 12);
      ctx.lineTo(0, 28);
      ctx.stroke();
    } else if (style === 'pin') {
      ctx.beginPath();
      ctx.arc(0, 0, 10, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, 10);
      ctx.lineTo(0, 24);
      ctx.stroke();
    } else {
      ctx.beginPath();
      ctx.arc(0, 0, 11, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(0, 0, 18, 0, Math.PI * 2);
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.stroke();
    }
    if (label) {
      ctx.font = '600 16px Segoe UI, Arial, sans-serif';
      ctx.textBaseline = 'middle';
      const text = String(label);
      const tw = ctx.measureText(text).width;
      const boxW = tw + 18;
      const boxH = 26;
      const bx = 16;
      const by = -13;
      ctx.fillStyle = 'rgba(6,10,16,0.86)';
      ctx.strokeStyle = 'rgba(255,255,255,0.16)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      safeRoundRect(ctx, bx, by, boxW, boxH, 10);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#f4ead9';
      ctx.fillText(text, bx + 9, 0);
    }
    ctx.restore();
  }
  function showSaveViewHelp() {
    window.alert(
      'Save your terrain view:\n\n' +
      '1. Rotate and zoom the 3D terrain to the angle you want.\n' +
      '2. Press Windows + Shift + S to snip the screen, or press PrtScn.\n' +
      '3. Paste the image into Word, Google Docs, Paint, or your scouting notes.\n' +
      '4. Use Download Summary for the written Monahinga™ report.\n\n' +
      'Tip: You can save as many terrain angles as you want this way.'
    );
  }

  function downloadSummary() {
    try {
      const blob = new Blob([buildSummaryText()], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = 'monahinga_summary.txt';
      link.href = url;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      window.alert('Summary download failed.');
    }
  }
  function updateSelectedSiteCard(site) { if (!site) return; state.invisibleApproachRank = Number(site.rank || state.invisibleApproachRank || 1); if (selectedSiteTitle) selectedSiteTitle.textContent = site.title || 'Selected sit'; if (selectedSiteCoords) selectedSiteCoords.textContent = formatSiteCoords(site); if (copyCoordsBtn) copyCoordsBtn.dataset.copyText = site.lat.toFixed(6) + ', ' + site.lon.toFixed(6); updateExecutiveSummaryForSite(site); update2DFieldMap(site); updateFocusOverlay(site); if (typeof rebuildInvisibleApproachOverlay === 'function') rebuildInvisibleApproachOverlay(site); }
  async function copySelectedCoords() { const text = (copyCoordsBtn && copyCoordsBtn.dataset.copyText) || ''; if (!text) return; try { if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(text); copyCoordsBtn.textContent = 'Copied'; setTimeout(() => { copyCoordsBtn.textContent = 'Copy coordinates'; }, 1200); } } catch (err) {} }
  function addTrustTag(tags, seen, source, matchers, label) { if (!source) return; for (const matcher of matchers) { if (source.includes(matcher)) { const key = label.toLowerCase(); if (!seen.has(key)) { seen.add(key); tags.push(label); } return; } } }
  function buildTrustTags() {
    if (!trustTags) return;
    const title = String(trustTags.dataset.title || '').toLowerCase();
    const reason = String(trustTags.dataset.reason || '').toLowerCase();
    const wind = String(trustTags.dataset.wind || '').toLowerCase();
    const legal = String(trustTags.dataset.legal || '').toLowerCase();
    const corpus = title + ' ' + reason + ' ' + legal;
    let explicitTags = [];
    try {
      const parsed = JSON.parse(trustTags.dataset.tags || '[]');
      if (Array.isArray(parsed)) explicitTags = parsed.map((item) => String(item || '').trim()).filter(Boolean);
    } catch (err) {}
    const tagRename = {
      'Bench Terrain': 'Bench Bedding Edge',
      'Bedding Overlap': 'Bedding Zone Hold',
      'Verified Legal Access': 'Legal Interior Access',
    };
    explicitTags = explicitTags.map((tag) => tagRename[tag] || tag);

    const ordered = [];
    const seen = new Set();
    const pushTag = (tag) => {
      const clean = String(tag || '').trim();
      const key = clean.toLowerCase();
      if (!clean || seen.has(key)) return;
      seen.add(key);
      ordered.push(clean);
    };

    explicitTags.forEach(pushTag);

    if (!ordered.length) {
      addTrustTag(ordered, seen, corpus, ['core converge', 'convergence'], 'Core Convergence');
      addTrustTag(ordered, seen, corpus, ['ridge funnel', 'funnel'], 'Ridge Funnel');
      addTrustTag(ordered, seen, corpus, ['shoulder travel lane', 'shoulder'], 'Shoulder Travel Lane');
      addTrustTag(ordered, seen, corpus, ['bench bedding edge', 'bench'], 'Bench Bedding Edge');
      addTrustTag(ordered, seen, corpus, ['travel intercept', 'travel'], 'Travel Intercept');
      addTrustTag(ordered, seen, corpus, ['interior security'], 'Interior Security');
      addTrustTag(ordered, seen, corpus, ['legal interior access', 'verified legal access', 'legal', 'state game land', 'pad-us'], 'Legal Interior Access');
      addTrustTag(ordered, seen, corpus, ['slope shelter', 'cover'], 'Slope Shelter');
    }

    const dominance = {
      'core convergence': ['travel intercept', 'interior security', 'legal interior access'],
      'ridge funnel': ['travel intercept', 'interior security', 'legal interior access'],
      'shoulder travel lane': ['travel intercept', 'interior security', 'legal interior access'],
      'bench bedding edge': ['interior security', 'legal interior access'],
    };
    const filtered = [];
    for (const tag of ordered) {
      const lower = tag.toLowerCase();
      let hidden = false;
      for (const chosen of filtered) {
        const covered = dominance[String(chosen).toLowerCase()] || [];
        if (covered.includes(lower)) { hidden = true; break; }
      }
      if (!hidden) filtered.push(tag);
    }

    const cautionTags = [];
    if (/edge exposure|boundary|border/.test(corpus)) cautionTags.push('Edge Management');
    if (/partial|clipped|fringe/.test(corpus)) cautionTags.push('Coverage Edge');
    if (/unknown|unverified/.test(corpus)) cautionTags.push('Viewer Trust Check');
    const visible = filtered.slice(0, 3);
    if (!visible.length) visible.push('Terrain Read');
    const primary = visible[0];
    const supports = visible.slice(1, 3);
    const caution = cautionTags.find((tag) => !visible.includes(tag));
    const chips = [];
    if (primary) chips.push('<span class="trust-tag trust-tag-primary">' + primary + '</span>');
    supports.forEach((tag) => chips.push('<span class="trust-tag trust-tag-support">' + tag + '</span>'));
    if (caution && chips.length < 3) chips.push('<span class="trust-tag trust-tag-caution">' + caution + '</span>');
    trustTags.innerHTML = chips.join('');
  }
  buildTrustTags();
  fetch(payload.heightmap_url + '?ts=' + Date.now(), { cache: 'no-store' }).then(r => r.ok ? r.json() : Promise.reject(new Error('Could not load heightmap.json'))).then((heightmap) => {
    try {
      const rows = Number(heightmap.rows || 0), cols = Number(heightmap.cols || 0);
      const raw = Array.isArray(heightmap.geometry_values) ? heightmap.geometry_values : (Array.isArray(heightmap.values) ? heightmap.values : []);
      const grid = Array.isArray(raw.flat) ? raw.flat() : ([]).concat(...raw);
      if (!rows || !cols || !grid.length) throw new Error('heightmap.json is incomplete.');
      state.baseExaggeration = Number(heightmap.viewer_default_exaggeration || 1.0);
      const baseVerticalScale = Number(heightmap.viewer_vertical_scale || 1.0);
      state.depthWorld = Math.max(10, state.widthWorld * (rows / Math.max(cols, 1)));
      const regionIdentity = deriveRegionIdentity();
      applyRegionIdentity(regionIdentity);
      function getVisualProfile() {
        const hour = new Date().getHours();
        const regionKey = regionIdentity.key;
        const base = (() => {
          if (hour < 6) return { skyTop:'#07111c', skyMid:'#10263b', skyBottom:'#1b3040', fog:0x142130, fogDensity:0.0088, sun:0xe7c08c, hemiSky:0x8aa1b7, hemiGround:0x263223, dir:1.18, hemi:0.72, fill:0.26, rim:0.18 };
          if (hour < 11) return { skyTop:'#88b8de', skyMid:'#6e9abd', skyBottom:'#d9d5c2', fog:0x8da4b8, fogDensity:0.0068, sun:0xffdfb1, hemiSky:0xe7f1fb, hemiGround:0x445736, dir:1.72, hemi:0.96, fill:0.42, rim:0.22 };
          if (hour < 17) return { skyTop:'#79acd7', skyMid:'#8fb3cd', skyBottom:'#d7d9ce', fog:0x95aabd, fogDensity:0.0062, sun:0xfff0cf, hemiSky:0xeaf3fb, hemiGround:0x4d603d, dir:1.86, hemi:1.00, fill:0.40, rim:0.24 };
          if (hour < 20) return { skyTop:'#436d94', skyMid:'#a77f6e', skyBottom:'#e2c7a1', fog:0x6f7e8e, fogDensity:0.0078, sun:0xffc891, hemiSky:0xc9d8e8, hemiGround:0x473b2f, dir:1.52, hemi:0.84, fill:0.30, rim:0.20 };
          return { skyTop:'#08111b', skyMid:'#12253b', skyBottom:'#223041', fog:0x121c28, fogDensity:0.0094, sun:0x9bb0c8, hemiSky:0x7088a2, hemiGround:0x1f2a22, dir:0.96, hemi:0.54, fill:0.18, rim:0.14 };
        })();
        if (regionKey === 'mountain') {
          return Object.assign({}, base, { skyMid: hour < 17 ? '#7e97bb' : '#5a7695', skyBottom: hour < 17 ? '#cdd4d8' : '#9eaab7', fog:0x7f90a4, hemiGround:0x364049 });
        }
        if (regionKey === 'plains') {
          return Object.assign({}, base, { skyMid: hour < 17 ? '#9cc3d9' : '#9a8a68', skyBottom: hour < 17 ? '#e4dcb8' : '#d7b57e', fog:0x97a789, hemiGround:0x5b5a39 });
        }
        if (regionKey === 'southwoods') {
          return Object.assign({}, base, { skyMid: hour < 17 ? '#7ba2b5' : '#6d836c', skyBottom: hour < 17 ? '#cfd2be' : '#ac996d', fog:0x748778, hemiGround:0x31412f });
        }
        return base;
      }
      function createSkyTexture(profile) { const skyCanvas = document.createElement('canvas'); skyCanvas.width = 24; skyCanvas.height = 320; const skyCtx = skyCanvas.getContext('2d'); const grad = skyCtx.createLinearGradient(0, 0, 0, skyCanvas.height); grad.addColorStop(0.0, profile.skyTop); grad.addColorStop(0.44, profile.skyMid); grad.addColorStop(1.0, profile.skyBottom); skyCtx.fillStyle = grad; skyCtx.fillRect(0, 0, skyCanvas.width, skyCanvas.height); const horizonGlow = skyCtx.createRadialGradient(skyCanvas.width * 0.5, skyCanvas.height * 0.26, 8, skyCanvas.width * 0.5, skyCanvas.height * 0.26, skyCanvas.height * 0.45); horizonGlow.addColorStop(0.0, 'rgba(255,232,174,0.26)'); horizonGlow.addColorStop(0.38, 'rgba(251,215,154,0.10)'); horizonGlow.addColorStop(1.0, 'rgba(255,255,255,0)'); skyCtx.fillStyle = horizonGlow; skyCtx.fillRect(0, 0, skyCanvas.width, skyCanvas.height); const tex = new THREE.CanvasTexture(skyCanvas); tex.colorSpace = THREE.SRGBColorSpace; tex.needsUpdate = true; return tex; }
      const visualProfile = getVisualProfile(); const scene = new THREE.Scene(); scene.background = createSkyTexture(visualProfile); scene.fog = new THREE.FogExp2(visualProfile.fog, visualProfile.fogDensity);
      const renderer = new THREE.WebGLRenderer({ antialias:true, alpha:false, powerPreference:'high-performance' });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      const initialWidth = viewer.clientWidth || 1200, initialHeight = viewer.clientHeight || 720;
      renderer.setSize(initialWidth, initialHeight); if (renderer.outputColorSpace) renderer.outputColorSpace = THREE.SRGBColorSpace; viewer.innerHTML=''; viewer.appendChild(renderer.domElement);
      const camera = new THREE.PerspectiveCamera(42, initialWidth / initialHeight, 0.1, 1000);
      const firstSite = (payload.sites || [])[0];
      const reliefFocus = computeReliefFocus(grid, rows, cols);
      const chosenFocus = firstSite ? sitePoint(firstSite) : reliefFocus;
      const target = normToWorld(chosenFocus.nx, chosenFocus.ny, state.widthWorld, state.depthWorld); target.y = 0;
      const sceneSpan = Math.max(state.widthWorld, state.depthWorld);
      // --- smarter terrain-aware camera distance ---
      const reliefNormalized = clamp(reliefFocus.relief * 2.2, 0, 1);
      const baseRadius = sceneSpan * (0.75 + reliefNormalized * 0.65);
      state.cameraRadius = clamp(baseRadius, 14, 42);

      // --- lift camera target slightly (prevents clipping) ---
      target.y = target.y + (1.2 + reliefNormalized * 2.0);

      // --- slightly steeper angle for big terrain ---
      state.tiltDeg = 26 + (reliefNormalized * 6);
      tiltSlider.value = String(Math.round(state.tiltDeg));
      scene.add(new THREE.AmbientLight(0xd8e3eb, 0.92));
      const hemi = new THREE.HemisphereLight(visualProfile.hemiSky, visualProfile.hemiGround, visualProfile.hemi); scene.add(hemi);
      const dir = new THREE.DirectionalLight(visualProfile.sun, visualProfile.dir); dir.position.set(16, 24, 9); scene.add(dir);
      const fill = new THREE.DirectionalLight(0x90aec7, visualProfile.fill); fill.position.set(-12, 10, -14); scene.add(fill);
      const rim = new THREE.DirectionalLight(0xb9d1db, visualProfile.rim); rim.position.set(10, 7, -18); scene.add(rim);
      const geom = new THREE.PlaneGeometry(state.widthWorld, state.depthWorld, cols - 1, rows - 1); geom.rotateX(-Math.PI / 2); const pos = geom.attributes.position;
      function currentHeight(nx, ny) { return sampleHeight(grid, rows, cols, nx, ny) * baseVerticalScale * state.baseExaggeration * (Number(depthSlider.value || 100) / 100) * 6.0; }
      function applyHeights() { const depthScale = Number(depthSlider.value || 100) / 100; for (let row=0; row<rows; row++){ for (let col=0; col<cols; col++){ const idx=row*cols+col; pos.setY(idx, grid[idx] * baseVerticalScale * state.baseExaggeration * depthScale * 6.0); } } pos.needsUpdate = true; geom.computeVertexNormals(); }
      function updateTargetHeight(nx, ny) { target.y = currentHeight(nx, ny) * 0.40 + 0.35; }
      applyHeights(); updateTargetHeight(chosenFocus.nx, chosenFocus.ny);
      const textureLoader = new THREE.TextureLoader();
      const material = new THREE.MeshStandardMaterial({ color:0xffffff, roughness:0.96, metalness:0.01 });
      const layerTextureCache = new Map();
      const terrainMesh = new THREE.Mesh(geom, material); scene.add(terrainMesh);
      const fillGroup = new THREE.Group(), boundaryGroup = new THREE.Group(), corridorGroup = new THREE.Group(), markerGroup = new THREE.Group(), windGroup = new THREE.Group(), focusGroup = new THREE.Group(), coverOverlayGroup = new THREE.Group(), invisibleApproachGroup = new THREE.Group();
      scene.add(fillGroup); scene.add(boundaryGroup); scene.add(corridorGroup); scene.add(markerGroup); scene.add(windGroup); scene.add(focusGroup); scene.add(coverOverlayGroup); scene.add(invisibleApproachGroup);
      invisibleApproachGroup.visible = false;
      const siteGroups = new Map();
      function worldPoint(nx, ny, lift) { const sx = safeNorm(nx); const sy = safeNorm(ny); const p = normToWorld(sx, sy, state.widthWorld, state.depthWorld); p.y = currentHeight(sx, sy) + (lift || 0); return p; }
      function buildNamedFieldMarker(pinData, accentColor) {
        const base = worldPoint(pinData.nx, pinData.ny, 0.28);
        const group = new THREE.Group();
        const color = accentColor;
        const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.32, 8), new THREE.MeshStandardMaterial({ color: 0xf7f7f7, transparent:true, opacity:0.72 }));
        stem.position.y = -0.14;
        const core = new THREE.Mesh(new THREE.SphereGeometry(0.16, 14, 14), new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.35, roughness:0.42, metalness:0.04 }));
        const ring = new THREE.Mesh(new THREE.RingGeometry(0.22, 0.30, 32), new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide, transparent: true, opacity: 0.9 }));
        ring.rotation.x = -Math.PI / 2;
        ring.position.y = -0.10;
        group.add(stem); group.add(core); group.add(ring);
        group.position.copy(base);
        group.userData = Object.assign({}, pinData);
        return group;
      }
      function buildUserPinMarker(pinData) {
        const group = buildNamedFieldMarker(pinData, 0xff4d4d);
        userPinGroups.push(group);
        return group;
      }
function buildAnchorMarker(pinData) {
  const accent = pinData.kind === 'baseCamp' ? 0x5ec8ff : 0xffb347;
  const group = buildNamedFieldMarker(pinData, accent);

  group.scale.set(1.55, 1.55, 1.55);

  anchorGroups.push(group);
  return group;
}
      function buildCoverOverlay() {
        while (coverOverlayGroup.children.length) coverOverlayGroup.remove(coverOverlayGroup.children[0]);
        const colorBuffer = [];
        for (let row = 0; row < rows; row += 1) {
          for (let col = 0; col < cols; col += 1) {
            const idx = row * cols + col;
            const nx = cols <= 1 ? 0.5 : col / (cols - 1);
            const ny = rows <= 1 ? 0.5 : row / (rows - 1);
            const here = Number(grid[idx] || 0);
            const left = Number(grid[row * cols + Math.max(0, col - 1)] || here);
            const right = Number(grid[row * cols + Math.min(cols - 1, col + 1)] || here);
            const up = Number(grid[Math.max(0, row - 1) * cols + col] || here);
            const down = Number(grid[Math.min(rows - 1, row + 1) * cols + col] || here);
            const slopeSignal = Math.min(1, Math.sqrt(((right - left) * (right - left)) + ((down - up) * (down - up))) * 3.4);
            const reliefLocal = here - ((left + right + up + down) * 0.25);
            const sheltered = Math.max(0, -reliefLocal * 3.2);
            const vegetation = Math.max(0, Math.min(1, 1 - slopeSignal * 0.92 + sheltered * 0.34));
            let c;
            if (vegetation >= 0.72) c = new THREE.Color(0x06702f);
            else if (vegetation >= 0.46) c = new THREE.Color(0xb9e63a);
            else c = new THREE.Color(0xf0c067);
            if (sheltered > 0.05) c.lerp(new THREE.Color(0x1d8ea7), Math.min(0.72, sheltered * 1.24));
            if (slopeSignal > 0.34) c.offsetHSL(0, -0.02, -0.06);
            colorBuffer.push(c.r, c.g, c.b);
          }
        }
        geom.setAttribute('color', new THREE.Float32BufferAttribute(colorBuffer, 3));
        const coverMaterial = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.38, depthWrite: false, side: THREE.DoubleSide });
        const coverMesh = new THREE.Mesh(geom, coverMaterial);
        coverMesh.position.y = 0.06;
        coverMesh.renderOrder = 2;
        coverOverlayGroup.add(coverMesh);
      }
      function updateCoverOverlayVisibility(activeTexture) {
        if (!coverOverlayGroup.children.length) return;
        const show = activeTexture === 'terrain';
        const overlay = coverOverlayGroup.children[0];
        overlay.visible = show;
        overlay.material.opacity = show ? 0.30 : 0.0;
      }
      function registerOverlay(entry) {
        if (!entry || typeof entry.build !== 'function') return null;
        const overlayEntry = {
          id: entry.id || ('overlay-' + overlayRegistry.length),
          type: entry.type || FEATURE_TYPES.MARKER,
          group: entry.group || markerGroup,
          data: entry.data || null,
          build: entry.build,
          instance: null,
        };
        overlayRegistry.push(overlayEntry);
        return overlayEntry;
      }
      function removeOverlayEntries(predicate) {
        for (let i = overlayRegistry.length - 1; i >= 0; i -= 1) {
          const entry = overlayRegistry[i];
          if (!predicate(entry)) continue;
          if (entry.instance && entry.group) entry.group.remove(entry.instance);
          overlayRegistry.splice(i, 1);
        }
      }
      function renderOverlays() {
        overlayRegistry.forEach((entry) => {
          if (entry.instance) return;
          const instance = entry.build(entry.data);
          if (!instance) return;
          entry.instance = instance;
          if (entry.group) entry.group.add(instance);
        });
      }
      function buildSiteMarker(site) {
        const p = sitePoint(site);
        const base = worldPoint(p.nx, p.ny, 0.34);
        const group = new THREE.Group();
        const colorObj = tierColor(site.tier);
        const color = hexColor(colorObj);
        const siteScale = site.rank === 1 ? 1.0 : site.rank === 2 ? 0.88 : 0.78;
        const core = new THREE.Mesh(new THREE.SphereGeometry(0.20 * siteScale, 16, 16), new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: site.rank === 1 ? 0.30 : 0.22, roughness:0.44, metalness:0.03 }));
        const halo = new THREE.Mesh(new THREE.SphereGeometry(0.52 * siteScale, 16, 16), new THREE.MeshBasicMaterial({ color, transparent:true, opacity: site.rank === 1 ? 0.24 : 0.15 }));
        const ring = new THREE.Mesh(new THREE.RingGeometry(0.30 * siteScale, 0.48 * siteScale, 42), new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide, transparent: true, opacity: site.rank === 1 ? 1.0 : 0.98 })); ring.rotation.x = -Math.PI / 2; ring.position.y = -0.10;
        const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.34 + (site.rank === 1 ? 0.12 : 0.0), 8), new THREE.MeshStandardMaterial({ color: 0xf0f5f8, emissive: 0x6e8f5e, emissiveIntensity: 0.10, transparent:true, opacity:0.68 })); stem.position.y = -0.18;
        const groundDisc = new THREE.Mesh(new THREE.CircleGeometry(site.rank === 1 ? 0.44 : 0.31, 28), new THREE.MeshBasicMaterial({ color, transparent:true, opacity: site.rank === 1 ? 0.22 : 0.12 })); groundDisc.rotation.x = -Math.PI / 2; groundDisc.position.y = -0.12;
        group.add(groundDisc); group.add(stem); group.add(ring); group.add(halo); group.add(core); group.position.copy(base); group.userData.rank = site.rank; group.userData.site = site; group.userData.kind = 'sit';
        siteGroups.set(Number(site.rank), group);
        return group;
      }
      updateFocusOverlay = function(site) {
        while (focusGroup.children.length) focusGroup.remove(focusGroup.children[0]);
        if (!site) return;
        const p = sitePoint(site);
        const base = worldPoint(p.nx, p.ny, 0.16);
        const outer = new THREE.Mesh(
          new THREE.CircleGeometry(2.25, 48),
          new THREE.MeshBasicMaterial({ color: 0xaef186, transparent: true, opacity: 0.030, side: THREE.DoubleSide })
        );
        outer.rotation.x = -Math.PI / 2;
        outer.position.copy(base);
        const middle = new THREE.Mesh(
          new THREE.CircleGeometry(1.35, 42),
          new THREE.MeshBasicMaterial({ color: 0x7fcb59, transparent: true, opacity: 0.040, side: THREE.DoubleSide })
        );
        middle.rotation.x = -Math.PI / 2;
        middle.position.copy(base.clone().add(new THREE.Vector3(0, 0.01, 0)));
        const ring = new THREE.Mesh(
          new THREE.RingGeometry(1.0, 1.12, 48),
          new THREE.MeshBasicMaterial({ color: 0xe8f6c6, transparent: true, opacity: 0.68, side: THREE.DoubleSide })
        );
        ring.rotation.x = -Math.PI / 2;
        ring.position.copy(base.clone().add(new THREE.Vector3(0, 0.02, 0)));
        focusGroup.add(outer); focusGroup.add(middle); focusGroup.add(ring);
      }
      function makeTerrainLine(points, colorObj, opacity) { const geom = new THREE.BufferGeometry().setFromPoints(points); return new THREE.Line(geom, new THREE.LineBasicMaterial({ color: hexColor(colorObj), transparent:true, opacity, linewidth:1.15 })); }
      function polygonCentroid(rings) { const ring = (rings && rings[0]) || []; if (!ring.length) return { nx:0.5, ny:0.5 }; let sx = 0, sy = 0; ring.forEach((pt) => { sx += safeNorm(pt[0]); sy += safeNorm(pt[1]); }); return { nx: sx / ring.length, ny: sy / ring.length }; }
      function makeTube(points, radius, color, opacity) { const curve = new THREE.CatmullRomCurve3(points); const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, Math.max(16, points.length*10), radius, 10, false), new THREE.MeshStandardMaterial({ color, transparent:true, opacity, emissive: color, emissiveIntensity: 0.07, roughness:0.60, metalness:0.04 })); return tube; }
      function drawWindOverlay(read) { while (windGroup.children.length) windGroup.remove(windGroup.children[0]); const primarySite = siteByRank(1) || (payload.sites || [])[0]; if (!primarySite || !read || !read.ok || typeof read.arrow_heading_deg !== 'number') return; const p = sitePoint(primarySite); const origin = worldPoint(p.nx, p.ny, 0.9); const heading = THREE.MathUtils.degToRad(Number(read.arrow_heading_deg)); const dirVec = new THREE.Vector3(Math.sin(heading), 0, Math.cos(heading)).normalize(); const speed = Math.max(4, Number(read.speed_mph || 0)); const len = clamp(1.8 + speed * 0.08, 1.8, 4.2); const arrow = new THREE.ArrowHelper(dirVec, origin, len, 0xbde79b, 0.48, 0.24); windGroup.add(arrow); }
      function windLabelToHeading(label) {
        const value = String(label || '').toUpperCase();
        const dirs = { N:180, NE:225, E:270, SE:315, S:0, SW:45, W:90, NW:135 };
        const match = value.match(/\b(NW|NE|SW|SE|N|E|S|W)\b/);
        return match ? dirs[match[1]] : 135;
      }
      function currentScentHeadingDeg() {
        if (liveWindState && typeof liveWindState.arrow_heading_deg === 'number') return Number(liveWindState.arrow_heading_deg);
        const label = (operatorWindValue && operatorWindValue.textContent) || '';
        return windLabelToHeading(label);
      }
      function currentApproachSite() {
        return siteByRank(state.invisibleApproachRank || 1) || siteByRank(1) || (payload.sites || [])[0] || null;
      }

      function getSelectedSpecies() {
        const el = document.getElementById('viewer_species');
        if (!el) return null;
        return el.value;
      }

      function approachRiskClass(score) {
        if (score >= 68) return { label: 'High', css: 'approach-risk-high', color: 0xff5f45 };
        if (score >= 38) return { label: 'Caution', css: 'approach-risk-caution', color: 0xffd166 };
        return { label: 'Low', css: 'approach-risk-low', color: 0xaef186 };
      }

      function angleDeltaDeg(a, b) {
        return Math.abs((((Number(a || 0) - Number(b || 0)) + 540) % 360) - 180);
      }

      function localSlopeSignal(nx, ny) {
        const step = 0.026;
        const h = currentHeight(nx, ny);
        const hx = currentHeight(clamp(nx + step, 0, 1), ny);
        const hy = currentHeight(nx, clamp(ny + step, 0, 1));
        return Math.sqrt((h - hx) * (h - hx) + (h - hy) * (h - hy));
      }
      function routeDotRisk(t, nx, ny, site, scentHeadingDeg) {
        const centerPull = 1 - Math.min(1, Math.hypot(nx - 0.5, ny - 0.5) * 1.6);
        const slopeSignal = localSlopeSignal(nx, ny);
        const exposure = clamp(slopeSignal * 2.35, 0, 22);
        const p = sitePoint(site);
        const dx = nx - p.nx;
        const dy = ny - p.ny;
        const angleToDot = (THREE.MathUtils.radToDeg(Math.atan2(dx, dy)) + 360) % 360;
        const delta = angleDeltaDeg(angleToDot, scentHeadingDeg);
        const downwindRisk = delta < 42 ? 36 * (1 - delta / 42) : 0;
        const sitPressure = t > 0.70 ? 22 * ((t - 0.70) / 0.30) : 0;
        const corridorPressure = (payload.corridors || []).length ? 8 * centerPull : 3 * centerPull;
        return clamp(16 + exposure + downwindRisk + sitPressure + corridorPressure, 6, 94);
      }
function speciesApproachBias(site) {
  const context = deriveGameContext(site);
  const primary = String((context && context.primary) || '').toLowerCase();

  if (primary.includes('elk')) {
    return {
      label: 'Elk mountain approach',
      slopeWeight: 1.15,
      scentPenalty: 22,
      edgePenalty: 5,
      latePressure: 9,
      contourBonus: 5,
      coverBonus: 1,
    };
  }

  if (primary.includes('turkey')) {
    return {
      label: 'Turkey visibility approach',
      slopeWeight: 1.25,
      scentPenalty: 10,
      edgePenalty: 6,
      latePressure: 5,
      contourBonus: 2,
      coverBonus: 3,
    };
  }

  if (primary.includes('bear')) {
    return {
      label: 'Bear cover approach',
      slopeWeight: 1.05,
      scentPenalty: 16,
      edgePenalty: 7,
      latePressure: 6,
      contourBonus: 3,
      coverBonus: 6,
    };
  }

  return {
    label: 'Whitetail cover approach',
    slopeWeight: 1.55,
    scentPenalty: 18,
    edgePenalty: 8,
    latePressure: 7,
    contourBonus: 4,
    coverBonus: 7,
  };
}

function scoreApproachCandidate(nx, ny, t, site, scentHeadingDeg) {
  const bias = speciesApproachBias(site);
  const slope = localSlopeSignal(nx, ny);
  const p = sitePoint(site);
  const dx = nx - p.nx;
  const dy = ny - p.ny;
  const angleToPoint = (THREE.MathUtils.radToDeg(Math.atan2(dx, dy)) + 360) % 360;
  const scentPenalty = angleDeltaDeg(angleToPoint, scentHeadingDeg) < 48 ? bias.scentPenalty : 0;
  const edgePenalty = (nx < 0.035 || nx > 0.965 || ny < 0.035 || ny > 0.965) ? bias.edgePenalty : 0;
  const finalApproachPenalty = t > 0.76 ? bias.latePressure : 0;

  const centerPull = 1 - Math.min(1, Math.hypot(nx - 0.5, ny - 0.5) * 1.6);
  const contourReward = centerPull * bias.contourBonus;
  const coverReward = /cover|conceal|security|bedding|bench/.test(siteCorpus(site)) ? bias.coverBonus : 0;

  return slope * bias.slopeWeight + scentPenalty + edgePenalty + finalApproachPenalty - contourReward - coverReward;
}
      function buildApproachRoute(site) {
        const access = getAnchorPoint('accessEntry') || getAnchorPoint('baseCamp');
        if (!site || !access) return null;
        const start = latLonToNormalized(access.lat, access.lon);
        const end = sitePoint(site);
        const dx = end.nx - start.nx;
        const dy = end.ny - start.ny;
        const len = Math.max(0.001, Math.hypot(dx, dy));
        const px = -dy / len;
        const py = dx / len;
        const points = [];
        const count = 22;
        const scentHeading = currentScentHeadingDeg();
        let sideMemory = 0;
        for (let i = 0; i <= count; i += 1) {
          const t = i / count;
          const baseX = start.nx + dx * t;
          const baseY = start.ny + dy * t;
          const width = Math.sin(t * Math.PI) * 0.085;
          const softWander = Math.sin(t * Math.PI * 2.0) * 0.018;
          const candidates = [-1, -0.55, 0, 0.55, 1].map((side) => {
            const continuityPenalty = sideMemory ? Math.abs(side - sideMemory) * 1.7 : 0;
            const nx = clamp(baseX + px * (side * width + softWander), 0.02, 0.98);
            const ny = clamp(baseY + py * (side * width + softWander), 0.02, 0.98);
            return {
              nx,
              ny,
              side,
              score: scoreApproachCandidate(nx, ny, t, site, scentHeading) + continuityPenalty,
            };
          });
          candidates.sort((a, b) => a.score - b.score);
          const chosen = candidates[0];
          sideMemory = chosen.side;
          points.push({ nx: chosen.nx, ny: chosen.ny, t, candidateScore: chosen.score });
        }
        return { start, end, points };
      }
      function addScentCone(site, headingDeg, riskScore) {
        const p = sitePoint(site);
        const origin = worldPoint(p.nx, p.ny, 0.22);
        const heading = THREE.MathUtils.degToRad(headingDeg);
        const dirVec = new THREE.Vector3(Math.sin(heading), 0, Math.cos(heading)).normalize();
        const sideVec = new THREE.Vector3(dirVec.z, 0, -dirVec.x).normalize();
        const length = clamp(2.8 + Number((liveWindState && liveWindState.speed_mph) || 7) * 0.12, 3.0, 5.8);
        const width = length * 0.44;
        const a = origin.clone().add(dirVec.clone().multiplyScalar(0.35));
        const b = origin.clone().add(dirVec.clone().multiplyScalar(length)).add(sideVec.clone().multiplyScalar(width));
        const c = origin.clone().add(dirVec.clone().multiplyScalar(length)).add(sideVec.clone().multiplyScalar(-width));
        const geomCone = new THREE.BufferGeometry().setFromPoints([a, b, c]);
        geomCone.setIndex([0, 1, 2]);
        geomCone.computeVertexNormals();
        const opacity = riskScore >= 68 ? 0.24 : riskScore >= 38 ? 0.16 : 0.10;
        const cone = new THREE.Mesh(geomCone, new THREE.MeshBasicMaterial({ color: riskScore >= 68 ? 0xff5f45 : 0xffd166, transparent:true, opacity, side:THREE.DoubleSide, depthWrite:false }));
        cone.renderOrder = 4;
        invisibleApproachGroup.add(cone);
      }
function approachRiskExplanation(avgRisk, risks) {
  const activeSite = currentApproachSite();
  const bias = speciesApproachBias(activeSite);
  const highCount = risks.filter((item) => item >= 68).length;
  const cautionCount = risks.filter((item) => item >= 38 && item < 68).length;
  const windText = liveWindState && liveWindState.summary ? liveWindState.summary : ((operatorWindValue && operatorWindValue.textContent) || 'wind unavailable');

  if (highCount >= 4 || avgRisk >= 68) {
    return bias.label + ': high blowout risk. Route or scent path likely crosses too much danger ground. Wind: ' + windText + '.';
  }

  if (cautionCount >= 5 || avgRisk >= 38) {
    return bias.label + ': caution. Dotted path is species-aware, but verify wind, exposure, and final approach before committing. Wind: ' + windText + '.';
  }

  return bias.label + ': low-risk read. Route favors species-specific terrain tendencies while limiting scent pressure. Wind: ' + windText + '.';
}
      function rebuildInvisibleApproachOverlay(site) {
        while (invisibleApproachGroup.children.length) invisibleApproachGroup.remove(invisibleApproachGroup.children[0]);
        const activeSite = site || currentApproachSite();
        if (!activeSite) return;
        const route = buildApproachRoute(activeSite);
        if (!route) return;
        const scentHeading = currentScentHeadingDeg();
        const risks = route.points.map((pt) => routeDotRisk(pt.t, pt.nx, pt.ny, activeSite, scentHeading));
        const avgRisk = risks.reduce((a, b) => a + b, 0) / Math.max(1, risks.length);
        const risk = approachRiskClass(avgRisk);
        route.points.forEach((pt, idx) => {
          const dotRisk = approachRiskClass(risks[idx]);
          const radius = idx === route.points.length - 1 ? 0.14 : 0.095;
          const dot = new THREE.Mesh(
            new THREE.SphereGeometry(radius, 12, 12),
            new THREE.MeshStandardMaterial({ color: dotRisk.color, emissive: dotRisk.color, emissiveIntensity: 0.22, roughness:0.48, metalness:0.02, transparent:true, opacity:0.94 })
          );
          dot.position.copy(worldPoint(pt.nx, pt.ny, 0.34));
          invisibleApproachGroup.add(dot);
        });
        const linePoints = route.points.map((pt) => worldPoint(pt.nx, pt.ny, 0.23));
        if (linePoints.length > 1) invisibleApproachGroup.add(makeTerrainLine(linePoints, new THREE.Color(0xaef186), 0.32));
        addScentCone(activeSite, scentHeading, avgRisk);
        invisibleApproachGroup.visible = !!state.invisibleApproachVisible;
        if (invisibleApproachSummary) {
          invisibleApproachSummary.className = risk.css;
          invisibleApproachSummary.textContent = Math.round(avgRisk) + ' / 100 — ' + risk.label;
        }
        if (invisibleApproachMeta) {
          invisibleApproachMeta.textContent = approachRiskExplanation(avgRisk, risks);
        }
      }
      function setInvisibleApproachVisible(visible) {
        state.invisibleApproachVisible = !!visible;
        invisibleApproachGroup.visible = state.invisibleApproachVisible;
        if (invisibleApproachBtn) invisibleApproachBtn.classList.toggle('active', state.invisibleApproachVisible);
        if (invisibleApproachHud) invisibleApproachHud.classList.toggle('visible', state.invisibleApproachVisible);
        if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite());
      }

      function polygonShape(rings) { if (!rings || !rings.length) return null; const outer = (rings[0] || []).map(pt => [safeNorm(pt[0]), safeNorm(pt[1])]); if (!outer || outer.length < 3) return null; const shape = new THREE.Shape(); outer.forEach((pt, idx) => { const x=(pt[0]-0.5)*state.widthWorld, y=(pt[1]-0.5)*state.depthWorld; if (idx===0) shape.moveTo(x,y); else shape.lineTo(x,y); }); shape.lineTo((outer[0][0]-0.5)*state.widthWorld, (outer[0][1]-0.5)*state.depthWorld); for (let i=1; i<rings.length; i++) { const ring = (rings[i] || []).map(pt => [safeNorm(pt[0]), safeNorm(pt[1])]); if (!ring || ring.length < 3) continue; const hole = new THREE.Path(); ring.forEach((pt, idx) => { const x=(pt[0]-0.5)*state.widthWorld, y=(pt[1]-0.5)*state.depthWorld; if (idx===0) hole.moveTo(x,y); else hole.lineTo(x,y); }); hole.lineTo((ring[0][0]-0.5)*state.widthWorld, (ring[0][1]-0.5)*state.depthWorld); shape.holes.push(hole); } return shape; }
      function rebuildOverlays() {
        [fillGroup, boundaryGroup, corridorGroup, markerGroup].forEach(group => { while (group.children.length) group.remove(group.children[0]); });
        siteGroups.clear(); userPinGroups.length = 0; anchorGroups.length = 0;
        removeOverlayEntries((entry) => entry.type === FEATURE_TYPES.MARKER);
        (payload.legal_polygons || []).forEach((poly) => {
          const colorObj = legalColor(poly.class); const color = hexColor(colorObj); const shape = polygonShape(poly.rings || []);
          if (shape) {
            const fillGeom = new THREE.ShapeGeometry(shape); fillGeom.rotateX(-Math.PI / 2);
            const position = fillGeom.attributes.position;
            for (let i = 0; i < position.count; i++) { const x = position.getX(i), z = position.getZ(i); const nx = clamp(x / state.widthWorld + 0.5, 0, 1); const ny = clamp(z / state.depthWorld + 0.5, 0, 1); position.setY(i, currentHeight(nx, ny) + 0.05); }
            fillGeom.computeVertexNormals();
            const fillOpacity = poly.class === 'legal' ? 0.11 : 0.04;
            fillGroup.add(new THREE.Mesh(fillGeom, new THREE.MeshStandardMaterial({ color, transparent:true, opacity: fillOpacity, depthWrite:false, side: THREE.DoubleSide, emissive: color, emissiveIntensity: poly.class === 'legal' ? 0.04 : 0.01, roughness:0.95, metalness:0.0 })));
            if (poly.class === 'legal') { const centroid = polygonCentroid(poly.rings || []); const glow = new THREE.Mesh(new THREE.SphereGeometry(0.46, 14, 14), new THREE.MeshBasicMaterial({ color, transparent:true, opacity:0.018 })); glow.position.copy(worldPoint(centroid.nx, centroid.ny, 0.35)); fillGroup.add(glow); }
          }
          (poly.rings || []).forEach((ring) => { const pts = (ring || []).map(pt => worldPoint(pt[0], pt[1], 0.11)); if (pts.length < 2) return; boundaryGroup.add(makeTerrainLine(pts.concat([pts[0]]), colorObj, poly.class === 'legal' ? 0.50 : 0.26)); });
        });
        (payload.corridors || []).forEach((corridor) => { const pts=(corridor.points || []).map(pt => { const p=corridorPoint(pt); return worldPoint(p.nx,p.ny,0.16);}); if (pts.length < 2) return; corridorGroup.add(makeTube(pts, corridor.strength === 'dominant' ? 0.038 : 0.026, corridor.strength === 'dominant' ? 0xd6ff80 : 0xffd275, corridor.strength === 'dominant' ? 0.34 : 0.24)); });
        (payload.sites || []).forEach((site) => {
          // Visual-only simplification: keep the primary sit marker, but do not draw alternate sit markers.
          // The full payload, scoring, ranked intelligence, and summary text remain intact elsewhere.
          if (Number(site.rank || 0) !== 1) return;
          registerOverlay({
            id: 'site-' + Number(site.rank || 0),
            type: FEATURE_TYPES.MARKER,
            group: markerGroup,
            data: site,
            build: buildSiteMarker,
          });
        });
// BASE CAMP + ACCESS ENTRY (SAFE OVERLAY SYSTEM)
const baseCamp = getAnchorPoint('baseCamp');
const accessEntry = getAnchorPoint('accessEntry');

if (baseCamp) {
  const norm = latLonToNormalized(baseCamp.lat, baseCamp.lon);
  registerOverlay({
    id: 'anchor-base-camp',
    type: FEATURE_TYPES.MARKER,
    group: markerGroup,
    data: { kind: 'baseCamp', label: 'Base Camp', note: 'Base Camp', lat: baseCamp.lat, lon: baseCamp.lon, nx: norm.nx, ny: norm.ny },
    build: buildAnchorMarker,
  });
}

if (accessEntry) {
  const norm = latLonToNormalized(accessEntry.lat, accessEntry.lon);
  registerOverlay({
    id: 'anchor-access-entry',
    type: FEATURE_TYPES.MARKER,
    group: markerGroup,
    data: { kind: 'accessEntry', label: 'Access Entry', note: 'Access Entry', lat: accessEntry.lat, lon: accessEntry.lon, nx: norm.nx, ny: norm.ny },
    build: buildAnchorMarker,
  });
}

// USER PINS (SAFE OVERLAY SYSTEM)
const savedPins = JSON.parse(localStorage.getItem(STORAGE_KEYS.userPins) || '[]');

savedPins.forEach((pin, i) => {
  registerOverlay({
    id: 'user-pin-' + i,
    type: FEATURE_TYPES.MARKER,
    group: markerGroup,
    data: Object.assign({ label: pin.note || ('Field Pin ' + (i + 1)), pinIndex: i }, pin),
    build: buildUserPinMarker
  });
});
        renderOverlays();
        applyPadusMode(state.currentPadusMode);
        update2DFieldMap();
      }
      function applyPadusMode(mode) { state.currentPadusMode = mode; fillGroup.visible = (mode === 'hybrid' || mode === 'fill'); boundaryGroup.visible = (mode === 'hybrid' || mode === 'lines'); setPadusModeActive(mode); }
      function loadTexture(src) {
        const cacheKey = src || '';
        if (layerTextureCache.has(cacheKey)) return Promise.resolve(layerTextureCache.get(cacheKey));
        return new Promise((resolve, reject) => {
          textureLoader.load(src + '?ts=' + Date.now(), (tex) => {
            if (tex.colorSpace) tex.colorSpace = THREE.SRGBColorSpace;
            tex.wrapS = THREE.ClampToEdgeWrapping; tex.wrapT = THREE.ClampToEdgeWrapping;
            tex.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
            tex.needsUpdate = true;
            layerTextureCache.set(cacheKey, tex);
            resolve(tex);
          }, undefined, reject);
        });
      }
      function textureToImage(tex) {
        return new Promise((resolve, reject) => {
          const img = new Image();
              img.onload = () => resolve(img);
          img.onerror = reject;
          img.src = tex.image && tex.image.currentSrc ? tex.image.currentSrc : (tex.image && tex.image.src ? tex.image.src : tex.source && tex.source.data && tex.source.data.src ? tex.source.data.src : '');
        });
      }
      async function buildTerrainFirstTexture() {
        const terrainSrc = payload.layers.terrain || payload.layers[payload.defaultLayer] || payload.layers.hillshade;
        if (!terrainSrc) throw new Error('No terrain texture available');
        const [terrainTex, hillTex, reliefTex, slopeTex] = await Promise.all([
          loadTexture(terrainSrc),
          payload.layers.hillshade ? loadTexture(payload.layers.hillshade) : Promise.resolve(null),
          payload.layers.relief ? loadTexture(payload.layers.relief) : Promise.resolve(null),
          payload.layers.slope ? loadTexture(payload.layers.slope) : Promise.resolve(null),
        ]);
        const [terrainImg, hillImg, reliefImg, slopeImg] = await Promise.all([
          textureToImage(terrainTex),
          hillTex ? textureToImage(hillTex) : Promise.resolve(null),
          reliefTex ? textureToImage(reliefTex) : Promise.resolve(null),
          slopeTex ? textureToImage(slopeTex) : Promise.resolve(null),
        ]);
        const width = terrainImg.naturalWidth || terrainImg.width; const height = terrainImg.naturalHeight || terrainImg.height;
        const canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
        const ctx = canvas.getContext('2d', { willReadFrequently:true });
        const sampleCanvas = document.createElement('canvas'); sampleCanvas.width = width; sampleCanvas.height = height; const sampleCtx = sampleCanvas.getContext('2d', { willReadFrequently:true });
        function readPixels(img) {
          if (!img) return null; sampleCtx.clearRect(0, 0, width, height); sampleCtx.drawImage(img, 0, 0, width, height); return sampleCtx.getImageData(0, 0, width, height).data;
        }
        sampleCtx.drawImage(terrainImg, 0, 0, width, height);
        const imageData = sampleCtx.getImageData(0, 0, width, height);
        const data = imageData.data;
        const hill = readPixels(hillImg); const relief = readPixels(reliefImg); const slope = readPixels(slopeImg);
        for (let i = 0; i < data.length; i += 4) {
          const r = data[i], g = data[i + 1], b = data[i + 2];
          const lum = (r + g + b) / 3;
          const hillShade = hill ? (hill[i] + hill[i + 1] + hill[i + 2]) / 765 : lum / 255;
          const reliefBias = relief ? (((relief[i] + relief[i + 1] + relief[i + 2]) / 3) - 128) / 128 : 0;
          const slopeNorm = slope ? ((slope[i] + slope[i + 1] + slope[i + 2]) / 765) : 0.35;
          const vegetation = Math.max(0, Math.min(1, 1 - slopeNorm * 0.78));
          const hazeLift = 4 + vegetation * 3;
          const ridgeSignal = Math.max(0, reliefBias);
          const bowlSignal = Math.max(0, -reliefBias);
          const coverVariation = Math.sin((i / 4 % width) * 0.065) * 0.5 + Math.cos(Math.floor(i / 4 / width) * 0.082) * 0.5;

          let nr = r, ng = g, nb = b;
          let coverClass;
          if (vegetation > 0.69) coverClass = "dense";
          else if (vegetation > 0.43) coverClass = "moderate";
          else coverClass = "open";

          if (coverClass === "dense") {
            nr *= 0.46;
            ng = ng * 0.92 + 62;
            nb *= 0.42;
          } else if (coverClass === "moderate") {
            nr *= 0.74;
            ng = ng * 1.10 + 28;
            nb *= 0.70;
          } else {
            const gray = (r + g + b) / 3;
            nr = gray * 1.16 + 40;
            ng = gray * 1.00 + 18;
            nb = gray * 0.80 + 2;
          }

          const slopeExposure = Math.max(0, slopeNorm - 0.44);
          nr -= slopeExposure * 24;
          ng -= slopeExposure * 18;
          nb -= slopeExposure * 10;

          if (ridgeSignal > 0.10) {
            nr += 26;
            ng += 16;
            nb -= 6;
          }

          if (bowlSignal > 0.08) {
            nr -= 18;
            ng -= 6;
            nb += 28;
          }

          const benchGlow = Math.max(0, reliefBias - 0.02) * 28;
          nr += benchGlow * 0.48;
          ng += benchGlow * 0.62;
          nb += benchGlow * 0.18;

          nr += coverVariation * 6;
          ng += coverVariation * 9;
          nb += coverVariation * 4;

          const shadeFactor = 0.78 + hillShade * 0.64;
          nr *= shadeFactor;
          ng *= shadeFactor;
          nb *= shadeFactor;

          nr += hazeLift * 0.95;
          ng += hazeLift;
          nb += hazeLift * 0.70;

          const localContrast = (hillShade - 0.5) * 38;
          nr += localContrast * 0.84;
          ng += localContrast * 0.96;
          nb += localContrast * 0.44;

          data[i] = clamp(Math.round(nr), 0, 255);
          data[i + 1] = clamp(Math.round(ng), 0, 255);
          data[i + 2] = clamp(Math.round(nb), 0, 255);
        }
        ctx.putImageData(imageData, 0, 0);
        const outTex = new THREE.CanvasTexture(canvas);
        outTex.colorSpace = THREE.SRGBColorSpace;
        outTex.wrapS = THREE.ClampToEdgeWrapping; outTex.wrapT = THREE.ClampToEdgeWrapping;
        outTex.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
        outTex.needsUpdate = true;
        layerTextureCache.set('terrain:first', outTex);
        return outTex;
      }
      async function buildCoverTexture() {
        const cacheKey = 'cover:high-contrast';
        if (layerTextureCache.has(cacheKey)) return layerTextureCache.get(cacheKey);
        const terrainSrc = payload.layers.terrain || payload.layers[payload.defaultLayer] || payload.layers.hillshade;
        if (!terrainSrc) throw new Error('No terrain texture available');
        const [terrainTex, hillTex, reliefTex, slopeTex] = await Promise.all([
          loadTexture(terrainSrc),
          payload.layers.hillshade ? loadTexture(payload.layers.hillshade) : Promise.resolve(null),
          payload.layers.relief ? loadTexture(payload.layers.relief) : Promise.resolve(null),
          payload.layers.slope ? loadTexture(payload.layers.slope) : Promise.resolve(null),
        ]);
        const [terrainImg, hillImg, reliefImg, slopeImg] = await Promise.all([
          textureToImage(terrainTex),
          hillTex ? textureToImage(hillTex) : Promise.resolve(null),
          reliefTex ? textureToImage(reliefTex) : Promise.resolve(null),
          slopeTex ? textureToImage(slopeTex) : Promise.resolve(null),
        ]);

        const width = terrainImg.naturalWidth || terrainImg.width;
        const height = terrainImg.naturalHeight || terrainImg.height;
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d', { willReadFrequently:true });
        const sampleCanvas = document.createElement('canvas');
        sampleCanvas.width = width;
        sampleCanvas.height = height;
        const sampleCtx = sampleCanvas.getContext('2d', { willReadFrequently:true });

        function readPixels(img) {
          if (!img) return null;
          sampleCtx.clearRect(0, 0, width, height);
          sampleCtx.drawImage(img, 0, 0, width, height);
          return sampleCtx.getImageData(0, 0, width, height).data;
        }

        sampleCtx.drawImage(terrainImg, 0, 0, width, height);
        const imageData = sampleCtx.getImageData(0, 0, width, height);
        const data = imageData.data;
        const hill = readPixels(hillImg);
        const relief = readPixels(reliefImg);
        const slope = readPixels(slopeImg);

        for (let i = 0; i < data.length; i += 4) {
          const lum = (data[i] + data[i + 1] + data[i + 2]) / 3;
          const hillShade = hill ? (hill[i] + hill[i + 1] + hill[i + 2]) / 765 : lum / 255;
          const reliefBias = relief ? (((relief[i] + relief[i + 1] + relief[i + 2]) / 3) - 128) / 128 : 0;
          const slopeNorm = slope ? ((slope[i] + slope[i + 1] + slope[i + 2]) / 765) : 0.35;
          const vegetation = Math.max(0, Math.min(1, 1 - slopeNorm * 0.78));
          const sheltered = Math.max(0, -reliefBias) * 0.85 + Math.max(0, 0.54 - hillShade) * 0.44;
          const ridgeSignal = Math.max(0, reliefBias);
          const bowlSignal = Math.max(0, -reliefBias);
          const openSignal = Math.max(0, slopeNorm - 0.46) * 0.95 + ridgeSignal * 0.25;
          const coverStrength = clamp(vegetation * 0.58 + sheltered * 0.82 - openSignal * 0.40, 0, 1);
          const micro = Math.sin((i / 4 % width) * 0.09) * 0.5 + Math.cos(Math.floor(i / 4 / width) * 0.11) * 0.5;

          let nr, ng, nb;
          if (coverStrength >= 0.72) {
            nr = 8;
            ng = 132 + coverStrength * 98;
            nb = 18;
          } else if (coverStrength >= 0.44) {
            nr = 148;
            ng = 222 + coverStrength * 14;
            nb = 32;
          } else {
            nr = 232 + openSignal * 18;
            ng = 184 - openSignal * 6;
            nb = 74 - openSignal * 14;
          }

          if (bowlSignal > 0.10) {
            nr -= 28;
            ng -= 18;
            nb += 48;
          }

          if (ridgeSignal > 0.10) {
            nr += 34;
            ng += 18;
            nb -= 10;
          }

          nr += micro * 6;
          ng += micro * 7;
          nb += micro * 4;

          const shadeFactor = 0.70 + hillShade * 0.72;
          nr *= shadeFactor;
          ng *= shadeFactor;
          nb *= shadeFactor;

          const poster = coverStrength >= 0.72 ? 10 : (coverStrength >= 0.44 ? 8 : 12);
          nr = Math.round(nr / poster) * poster;
          ng = Math.round(ng / poster) * poster;
          nb = Math.round(nb / poster) * poster;

          data[i] = clamp(Math.round(nr), 0, 255);
          data[i + 1] = clamp(Math.round(ng), 0, 255);
          data[i + 2] = clamp(Math.round(nb), 0, 255);
          data[i + 3] = 255;
        }

        ctx.putImageData(imageData, 0, 0);
        const outTex = new THREE.CanvasTexture(canvas);
        outTex.colorSpace = THREE.SRGBColorSpace;
        outTex.wrapS = THREE.ClampToEdgeWrapping;
        outTex.wrapT = THREE.ClampToEdgeWrapping;
        outTex.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
        outTex.needsUpdate = true;
        layerTextureCache.set(cacheKey, outTex);
        return outTex;
      }

      async function applyTexture(key) {
        const safeKey = key === 'cover' ? 'terrain' : key;
        const isAnalytical = ['hillshade','relief','slope'].includes(safeKey);
        try {
          let tex;
          if (safeKey === 'terrain') {
            tex = layerTextureCache.get('terrain:first') || await buildTerrainFirstTexture();
          } else {
            const src = payload.layers[safeKey] || payload.layers[payload.defaultLayer] || payload.layers.terrain || payload.layers.hillshade;
            if (!src) return;
            tex = await loadTexture(src);
          }

          material.map = tex;
          material.map.needsUpdate = true;
          material.color = new THREE.Color(0xffffff);
          material.emissive = new THREE.Color(0x000000);
          material.emissiveIntensity = 0.0;
          material.roughness = isAnalytical ? 1.0 : 0.98;
          material.metalness = 0.01;
          material.normalScale = new THREE.Vector2(1, 1);
          scene.fog.density = safeKey === 'terrain' ? visualProfile.fogDensity : Math.max(visualProfile.fogDensity, 0.0088);
          fill.intensity = safeKey === 'terrain' ? visualProfile.fill : 0.26;
          hemi.intensity = safeKey === 'terrain' ? visualProfile.hemi : 0.66;
          dir.intensity = safeKey === 'terrain' ? visualProfile.dir : 1.42;
          rim.intensity = safeKey === 'terrain' ? visualProfile.rim : 0.12;
          state.currentTexture = safeKey;
          material.needsUpdate = true;
          setButtonActive(safeKey);
          setCoverReadUi(safeKey);
          updateCoverOverlayVisibility(safeKey);
        } catch (err) {
          material.map = null;
          material.color = new THREE.Color(isAnalytical ? 0x8f9599 : 0x788462);
          material.needsUpdate = true;
          state.currentTexture = safeKey;
          setButtonActive(safeKey);
          setCoverReadUi(safeKey);
          updateCoverOverlayVisibility(safeKey);
        }
      }
      function updateCamera() { const phi = THREE.MathUtils.degToRad(clamp(state.tiltDeg,12,42)); const flat = Math.cos(phi)*state.cameraRadius; const y = Math.sin(phi)*state.cameraRadius + Math.max(3.0, target.y+2.8); camera.position.set(target.x + Math.cos(state.rotationY)*flat, y, target.z + Math.sin(state.rotationY)*flat); camera.lookAt(target); }
      function moveTarget(nx, ny) { target.x = normToWorld(nx, ny, state.widthWorld, state.depthWorld).x; target.z = normToWorld(nx, ny, state.widthWorld, state.depthWorld).z; updateTargetHeight(nx, ny); }
      let dragging=false,lastX=0,lastY=0; renderer.domElement.addEventListener('pointerdown', (event) => { dragging=true; lastX=event.clientX; lastY=event.clientY; renderer.domElement.setPointerCapture(event.pointerId); }); renderer.domElement.addEventListener('pointermove', (event) => { if(!dragging)return; const dx=event.clientX-lastX, dy=event.clientY-lastY; lastX=event.clientX; lastY=event.clientY; state.rotationY -= dx*0.008; state.tiltDeg = clamp(state.tiltDeg + dy*0.08, 12, 42); tiltSlider.value = String(Math.round(state.tiltDeg)); updateCamera(); }); const endDrag=()=>{dragging=false;}; renderer.domElement.addEventListener('pointerup', endDrag); renderer.domElement.addEventListener('pointercancel', endDrag); renderer.domElement.addEventListener('wheel', (event) => { event.preventDefault(); state.cameraRadius = clamp(state.cameraRadius + event.deltaY*0.01, 10, 58); updateCamera(); }, { passive:false });
      const initialView = { rotationY: state.rotationY, tiltDeg: state.tiltDeg, cameraRadius: state.cameraRadius, depthValue: Number(depthSlider.value || 100), currentTexture: state.currentTexture, currentPadusMode: state.currentPadusMode, target: target.clone() };
      function resetView() { clearPinControlMode(); setInvisibleApproachVisible(false); state.rotationY = initialView.rotationY; state.tiltDeg = initialView.tiltDeg; state.cameraRadius = initialView.cameraRadius; tiltSlider.value = String(Math.round(initialView.tiltDeg)); depthSlider.value = String(Math.round(initialView.depthValue)); target.copy(initialView.target.clone()); applyHeights(); rebuildOverlays(); applyTexture(initialView.currentTexture); applyPadusMode(initialView.currentPadusMode); setFocusActive(1); updateSelectedSiteCard(siteByRank(1)); updateCamera(); }
      function focusSiteByRank(rank) { const site = siteByRank(rank); if (!site) return; const p = sitePoint(site); moveTarget(p.nx, p.ny); state.cameraRadius = Number(site.rank) === 1 ? 16.5 : 18.5; state.tiltDeg = Number(site.rank) === 1 ? 24 : 27; tiltSlider.value = String(Math.round(state.tiltDeg)); setFocusActive(rank); updateSelectedSiteCard(site); updateCamera(); }
      const raycaster = new THREE.Raycaster(); const pointer = new THREE.Vector2();

      function updateCursorTerrainRead(event) {
        if (!cursorCoords || dragging) return;
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, camera);
        const terrainHit = raycaster.intersectObject(terrainMesh, true);
        if (!terrainHit.length) {
          cursorCoords.textContent = 'Move over the terrain to read live GPS.';
          return;
        }
        const point = terrainHit[0].point;
        const nx = clamp((point.x / state.widthWorld) + 0.5, 0, 1);
        const ny = clamp((point.z / state.depthWorld) + 0.5, 0, 1);
        const coords = normalizedToLatLon(nx, ny);
        cursorCoords.innerHTML = 'Lat ' + Number(coords.lat).toFixed(6) + ' · Lon ' + Number(coords.lon).toFixed(6) + ' · Elev ' + Math.round(Number(point.y || 0)) + '<br><span class="micro-copy">nx ' + nx.toFixed(3) + ' · ny ' + ny.toFixed(3) + '</span>';
      }
      renderer.domElement.addEventListener('pointermove', updateCursorTerrainRead);
      renderer.domElement.addEventListener('click', (event) => {
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, camera);
        const clickTargets = Array.from(siteGroups.values()).concat(userPinGroups).concat(anchorGroups);
        const intersects = raycaster.intersectObjects(clickTargets, true);
        if (!intersects.length) return;
        const owner = intersects[0].object.parent && intersects[0].object.parent.userData ? intersects[0].object.parent : intersects[0].object;
        if (!owner || !owner.userData) return;
        if (owner.userData.rank) {
          updateSelectedSiteCard(owner.userData.site || siteByRank(owner.userData.rank));
          focusSiteByRank(owner.userData.rank);
          return;
        }
        if (owner.userData.kind === 'baseCamp' || owner.userData.kind === 'accessEntry') {
          const label = owner.userData.label || owner.userData.kind;
          updateExecutiveSummaryForAnchor(label, owner.userData, (owner.userData.kind === 'baseCamp' ? 'Reference point for distance and direction.' : 'Preferred start or parking approach.'));
          const action = window.prompt(label + ' options: type VIEW, MOVE, or GPS', 'VIEW');
          if (action === null) return;
          const choice = String(action || '').trim().toUpperCase();
          if (choice === 'MOVE') {
            beginPinControlMode(owner.userData.kind === 'baseCamp' ? 'placeBaseCamp' : 'placeAccessEntry', -1, label);
            return;
          }
          if (choice === 'GPS') {
            promptForAnchor(owner.userData.kind, label);
            return;
          }
          window.alert(label + '\nLat: ' + Number(owner.userData.lat).toFixed(5) + '\nLon: ' + Number(owner.userData.lon).toFixed(5));
          return;
        }
        if (owner.userData.note) {
          const pins = getStoredUserPins();
          const pinIndex = Number.isFinite(Number(owner.userData.pinIndex)) ? Number(owner.userData.pinIndex) : pins.findIndex((pin) => {
            const lat = Number.isFinite(Number(pin.lat)) ? Number(pin.lat) : normalizedToLatLon(pin.nx, pin.ny).lat;
            const lon = Number.isFinite(Number(pin.lon)) ? Number(pin.lon) : normalizedToLatLon(pin.nx, pin.ny).lon;
            return Math.abs(lat - Number(owner.userData.lat || 0)) < 0.000001 && Math.abs(lon - Number(owner.userData.lon || 0)) < 0.000001;
          });
          const coords = (Number.isFinite(Number(owner.userData.lat)) && Number.isFinite(Number(owner.userData.lon)))
            ? { lat: Number(owner.userData.lat), lon: Number(owner.userData.lon) }
            : normalizedToLatLon(owner.userData.nx, owner.userData.ny);
          updateExecutiveSummaryForAnchor(owner.userData.label || 'Field Pin', coords, owner.userData.note);
          const action = window.prompt((owner.userData.note || 'Field Pin') + ' options: type VIEW, RENAME, MOVE, or DELETE', 'VIEW');
          if (action === null) return;
          const choice = String(action || '').trim().toUpperCase();
          if (choice === 'RENAME' && pinIndex >= 0) {
            const nextNote = window.prompt('Rename this field pin', owner.userData.note || 'Field Pin');
            if (nextNote) {
              pins[pinIndex] = Object.assign({}, pins[pinIndex], { note: nextNote });
              saveStoredUserPins(pins);
              rebuildOverlays();
            }
            return;
          }
          if (choice === 'MOVE' && pinIndex >= 0) {
            beginPinControlMode('moveUserPin', pinIndex, owner.userData.note || 'Field Pin');
            return;
          }
          if (choice === 'DELETE' && pinIndex >= 0) {
            if (window.confirm('Delete ' + (owner.userData.note || 'this field pin') + '?')) {
              pins.splice(pinIndex, 1);
              saveStoredUserPins(pins);
              rebuildOverlays();
              updateExecutiveSummaryForSite(getSelectedSiteForExport() || siteByRank(1));
            }
            return;
          }
          window.alert((owner.userData.note || 'Field Pin') + '\nLat: ' + Number(coords.lat).toFixed(5) + '\nLon: ' + Number(coords.lon).toFixed(5));
        }
      });

      // CLICK TERRAIN TO PLACE OR MOVE ANCHORS / PINS
      renderer.domElement.addEventListener('click', (event) => {
        const awaitingPlacement = !!state.pinControlMode;
        if (awaitingPlacement && pinControlJustActivated) {
          pinControlJustActivated = false;
          return;
        }
        if (!awaitingPlacement && !event.shiftKey) return;
        event.preventDefault();

        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(pointer, camera);

        const terrainHit = raycaster.intersectObject(terrainMesh, true);
        if (!terrainHit.length) return;

        const point = terrainHit[0].point;
        const nx = clamp((point.x / state.widthWorld) + 0.5, 0, 1);
        const ny = clamp((point.z / state.depthWorld) + 0.5, 0, 1);
        const coords = normalizedToLatLon(nx, ny);

        if (state.pinControlMode === 'placeBaseCamp') {
          saveAnchorPoint('baseCamp', { lat: coords.lat, lon: coords.lon, label: 'Base Camp' });
          updateAnchorSummaries();
          rebuildOverlays();
          if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite());
          updateExecutiveSummaryForAnchor('Base Camp', { lat: coords.lat, lon: coords.lon }, 'Reference point for distance and direction.');
          clearPinControlMode();
          return;
        }

        if (state.pinControlMode === 'placeAccessEntry') {
          saveAnchorPoint('accessEntry', { lat: coords.lat, lon: coords.lon, label: 'Access Entry' });
          updateAnchorSummaries();
          rebuildOverlays();
          if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite());
          updateExecutiveSummaryForAnchor('Access Entry', { lat: coords.lat, lon: coords.lon }, 'Preferred start or parking approach.');
          clearPinControlMode();
          return;
        }

        if (state.pinControlMode === 'moveUserPin') {
          const pins = getStoredUserPins();
          if (state.pinControlIndex >= 0 && state.pinControlIndex < pins.length) {
            pins[state.pinControlIndex] = Object.assign({}, pins[state.pinControlIndex], { nx, ny, lat: coords.lat, lon: coords.lon });
            saveStoredUserPins(pins);
            rebuildOverlays();
          }
          clearPinControlMode();
          return;
        }

        const note = window.prompt('Name this field pin', 'Trail Cam / Scrape / Rub Line');
        if (!note) return;

        const pins = getStoredUserPins();
        pins.push({ nx, ny, note, lat: coords.lat, lon: coords.lon });
        saveStoredUserPins(pins);
        rebuildOverlays();
      });
      if (resetViewBtn) resetViewBtn.addEventListener('click', resetView);
      if (invisibleApproachBtn) invisibleApproachBtn.addEventListener('click', () => setInvisibleApproachVisible(!state.invisibleApproachVisible));
      if (saveViewHelpBtn) saveViewHelpBtn.addEventListener('click', showSaveViewHelp);
if (downloadSummaryBtn) downloadSummaryBtn.addEventListener('click', downloadSummary);

const viewerSpecies = document.getElementById('viewer_species');
if (viewerSpecies) {
  viewerSpecies.addEventListener('change', () => {
    const current = getSelectedSiteForExport() || siteByRank(1);
    if (current) updateExecutiveSummaryForSite(current);
    if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite());
  });
}
      if (setBaseCampBtn) setBaseCampBtn.addEventListener('click', () => { clearPinControlMode(); promptForAnchor('baseCamp', 'Base Camp'); });
      if (setAccessEntryBtn) setAccessEntryBtn.addEventListener('click', () => { clearPinControlMode(); promptForAnchor('accessEntry', 'Access Entry'); });
      if (placeBaseCampBtn) placeBaseCampBtn.addEventListener('click', () => beginPinControlMode('placeBaseCamp', -1, 'Base Camp'));
      if (placeAccessEntryBtn) placeAccessEntryBtn.addEventListener('click', () => beginPinControlMode('placeAccessEntry', -1, 'Access Entry'));
      if (copyCoordsBtn) copyCoordsBtn.addEventListener('click', copySelectedCoords);
      focusButtons.forEach(btn => btn.addEventListener('click', () => focusSiteByRank(btn.dataset.focusRank)));
      rowButtons.forEach(btn => btn.addEventListener('click', () => focusSiteByRank(btn.dataset.rank)));
      layerButtons.forEach(btn => btn.addEventListener('click', () => applyTexture(btn.dataset.layer)));
      padusButtons.forEach(btn => btn.addEventListener('click', () => applyPadusMode(btn.dataset.padusMode)));
      tiltSlider.addEventListener('input', () => { state.tiltDeg = Number(tiltSlider.value || 28); updateCamera(); });
      depthSlider.addEventListener('input', () => { applyHeights(); rebuildOverlays(); if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite()); updateCamera(); });
      window.addEventListener('resize', () => { const w=viewer.clientWidth||1200, h=viewer.clientHeight||720; camera.aspect = w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h); });
      async function loadLiveWind() { const primarySite = siteByRank(1) || (payload.sites || [])[0]; const center = payload.bbox_center || {}; const lat = primarySite ? Number(primarySite.lat) : Number(center.lat || 0); const lon = primarySite ? Number(primarySite.lon) : Number(center.lon || 0); if (!lat && !lon) return; try { const resp = await fetch(window.location.origin + '/live-wind?lat=' + encodeURIComponent(lat) + '&lon=' + encodeURIComponent(lon), { cache: 'no-store' }); const read = await resp.json(); if (read && read.ok) { liveWindState = read; const summary = read.summary || 'Live wind loaded.'; const meta = (read.observed_at_label ? 'Updated ' + read.observed_at_label + '. ' : '') + (read.note || ''); if (liveWindSummary) liveWindSummary.textContent = summary; if (liveWindMeta) liveWindMeta.textContent = meta; if (liveWindHudSummary) liveWindHudSummary.textContent = summary; if (liveWindHudMeta) liveWindHudMeta.textContent = meta; if (operatorWindValue) operatorWindValue.textContent = (read.direction_label || 'Wind') + (read.speed_mph ? ' · ' + Math.round(Number(read.speed_mph)) + ' mph' : ''); drawWindOverlay(read); if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite()); const current = siteByRank(1); if (current) updateExecutiveSummaryForSite(current); } else { throw new Error((read && read.note) || 'Live wind unavailable'); } } catch (err) { const fallback = 'Live wind unavailable. Manual wind stays active.'; if (liveWindSummary) liveWindSummary.textContent = fallback; if (liveWindMeta) liveWindMeta.textContent = String(err && err.message ? err.message : err); if (liveWindHudSummary) liveWindHudSummary.textContent = fallback; if (liveWindHudMeta) liveWindHudMeta.textContent = 'Using manual or preferred wind guidance only for this run.'; } }
      stripCoverLayerButton(); buildCoverOverlay(); updateAnchorSummaries(); updatePinControlStatus(); applyTexture(state.currentTexture); rebuildOverlays(); applyPadusMode(payload.defaultPadusMode || state.currentPadusMode); setFocusActive(1); updateSelectedSiteCard(siteByRank(1)); updateCamera(); loadLiveWind();
      function animate() { renderer.render(scene, camera); requestAnimationFrame(animate); }
      animate();
    } catch (err) { showError(err && err.message ? err.message : err); }
  }).catch(err => showError(err && err.message ? err.message : err));
})();
</script>

<script>
(function(){
  const marker = "MONAHINGA_TOP_LEFT_CLEANUP_2026_05_04";
  function hideDeadAiPanelButton(){
    const candidates = Array.from(document.querySelectorAll('button, a, [role="button"]'));
    candidates.forEach((el) => {
      const label = (el.textContent || '').trim().replace(/\s+/g, ' ').toLowerCase();
      if (label === 'hide ai panel') {
        el.style.display = 'none';
        el.setAttribute('aria-hidden', 'true');
        el.setAttribute('data-monahinga-hidden-by', marker);
      }
      if (label === 'back to box / launch' || label === 'back to box/launch') {
        el.style.fontSize = '16px';
        el.style.fontWeight = '950';
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hideDeadAiPanelButton);
  } else {
    hideDeadAiPanelButton();
  }
  window.addEventListener('load', hideDeadAiPanelButton);
})();
</script>


<script>
(function(){
  const marker = "MONAHINGA_PAGE2_DUAL_2D_3D_FOUNDATION_2026_05_04";
  let commandMap = null;
  let mapLayers = null;
  let mapObjects = [];

  function readStoredPoint(key){
    try {
      const raw = window.localStorage.getItem(key);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const lat = Number(parsed.lat);
      const lon = Number(parsed.lon);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
      return { lat, lon, label: parsed.label || key };
    } catch (_err) {
      return null;
    }
  }

  function bboxCenter(bbox){
    return {
      lat: (Number(bbox[1]) + Number(bbox[3])) / 2,
      lon: (Number(bbox[0]) + Number(bbox[2])) / 2
    };
  }

  function pointInsideBbox(point, bbox){
    if (!point || !bbox) return false;
    return point.lon >= Number(bbox[0]) && point.lon <= Number(bbox[2]) &&
           point.lat >= Number(bbox[1]) && point.lat <= Number(bbox[3]);
  }

  function makeIcon(kind){
    const className = kind === 'base' ? 'command-map-base-dot' : (kind === 'entry' ? 'command-map-entry-dot' : 'command-map-primary-dot');
    const isPrimary = kind === 'primary';
    return L.divIcon({
      className: '',
      html: isPrimary ? '<div class="command-map-primary-focus"><div class="' + className + '"></div></div>' : '<div class="' + className + '"></div>',
      iconSize: isPrimary ? [34, 34] : [22, 22],
      iconAnchor: isPrimary ? [17, 17] : [11, 11],
    });
  }

  function addLabel(marker, text){
    marker.bindTooltip(text, {
      permanent: true,
      direction: 'top',
      offset: [0, -12],
      className: 'command-map-pin-label'
    });
  }

  function clearObjects(){
    mapObjects.forEach((obj) => {
      try { obj.remove(); } catch (_err) {}
    });
    mapObjects = [];
  }

  function getPayload(){
    return window.__MONAHINGA_COMMAND_PAYLOAD || null;
  }

  // MONAHINGA_PAGE2_MAP_STRONG_SIT_CAMERA_BIAS_2026_05_05
  // Strong guide-style map bias: start with the bbox, then gently favor the Primary Sit.
  // Front-end Leaflet only. No backend, scoring, terrain generation, or 3D logic touched.
  function commandMapBiasToPrimarySit(payload, bounds){
    try{
      if (!commandMap || !payload || !bounds || !bounds.getCenter) return;
      const primary = (payload.sites || []).find((s) => Number(s.rank) === 1) || (payload.sites || [])[0];
      const lat = Number(primary && primary.lat);
      const lon = Number(primary && (primary.lon ?? primary.lng));
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;

      const center = bounds.getCenter();
      const bias = 0.72;
      const biasedLat = (center.lat * (1 - bias)) + (lat * bias);
      const biasedLon = (center.lng * (1 - bias)) + (lon * bias);

      const currentZoom = Number(commandMap.getZoom());
      const maxZoom = Number(commandMap.getMaxZoom && commandMap.getMaxZoom()) || 19;
      const targetZoom = Number.isFinite(currentZoom) ? Math.min(currentZoom + 1, maxZoom, 16) : undefined;

      if (Number.isFinite(targetZoom)) {
        commandMap.setView([biasedLat, biasedLon], targetZoom, { animate: false });
      } else {
        commandMap.panTo([biasedLat, biasedLon], { animate: false });
      }
    }catch(_err){
      // Stay silent. The 2D camera helper must never block the command surface.
    }
  }

  function initCommandMap(){
    const el = document.getElementById('commandLeafletMap');
    const payload = getPayload();
    if (!el || !payload || !payload.bbox || !window.L) return false;

    const bbox = payload.bbox.map(Number);
    const bounds = L.latLngBounds(
      [bbox[1], bbox[0]],
      [bbox[3], bbox[2]]
    );

    if (!commandMap) {
      commandMap = L.map(el, {
        zoomControl: true,
        attributionControl: true,
        worldCopyJump: false
      });

      const topo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        maxZoom: 17,
        attribution: '&copy; OpenTopoMap contributors'
      });

      const street = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      });

      const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
      });

      topo.addTo(commandMap);
      mapLayers = { 'Topo': topo, 'Street': street, 'Satellite': satellite };
      L.control.layers(mapLayers, null, { collapsed: true }).addTo(commandMap);

      /* MONAHINGA_PAGE2_MAP_GUIDE_LEGEND_2026_05_05:
         Add distance scale to help field-read access and approach.
         Visual-only Leaflet control. Safe for Render and independent of backend.
      */
      if (L.control && L.control.scale) {
        L.control.scale({
          position: 'bottomright',
          imperial: true,
          metric: true
        }).addTo(commandMap);
      }
    }

    commandMap.fitBounds(bounds, { padding: [16, 16] });
    commandMapBiasToPrimarySit(payload, bounds);
    setTimeout(() => {
      commandMap.invalidateSize();
      commandMapBiasToPrimarySit(payload, bounds);
    }, 120);
    renderCommandMapObjects(payload, bbox, bounds);
    return true;
  }

  function renderCommandMapObjects(payload, bbox, bounds){
    if (!commandMap) return;
    clearObjects();

    const bboxRect = L.rectangle(bounds, {
      color: '#aef186',
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.06
    }).addTo(commandMap);
    mapObjects.push(bboxRect);

    const primary = (payload.sites || []).find((s) => Number(s.rank) === 1) || (payload.sites || [])[0] || null;
    const center = bboxCenter(bbox);

    let base = readStoredPoint('baseCampGps') || { lat: Number((payload.bbox_center || {}).lat || center.lat), lon: Number((payload.bbox_center || {}).lon || center.lon), label: 'Base Camp' };
    let entry = readStoredPoint('accessEntryGps') || base;

    if (!pointInsideBbox(base, bbox)) base = { lat: center.lat, lon: center.lon, label: 'Base Camp' };
    if (!pointInsideBbox(entry, bbox)) entry = base;

    if (primary && Number.isFinite(Number(primary.lat)) && Number.isFinite(Number(primary.lon))) {
      const p = [Number(primary.lat), Number(primary.lon)];
      const primaryMarker = L.marker(p, { icon: makeIcon('primary'), title: 'Primary Sit' }).addTo(commandMap);
      addLabel(primaryMarker, 'Primary Sit');
      primaryMarker.bindPopup('<strong>Primary Sit</strong><br>' + (primary.title || 'Core convergence') + '<br>' + Number(primary.lat).toFixed(6) + ', ' + Number(primary.lon).toFixed(6));
      mapObjects.push(primaryMarker);

      const baseMarker = L.marker([base.lat, base.lon], { icon: makeIcon('base'), title: 'Base Camp' }).addTo(commandMap);
      addLabel(baseMarker, 'Base Camp');
      baseMarker.bindPopup('<strong>Base Camp</strong><br>' + base.lat.toFixed(6) + ', ' + base.lon.toFixed(6));
      mapObjects.push(baseMarker);

      const entryMarker = L.marker([entry.lat, entry.lon], { icon: makeIcon('entry'), title: 'Access Entry' }).addTo(commandMap);
      addLabel(entryMarker, 'Access');
      entryMarker.bindPopup('<strong>Access Entry</strong><br>' + entry.lat.toFixed(6) + ', ' + entry.lon.toFixed(6));
      mapObjects.push(entryMarker);

      const approachGlow = L.polyline([[entry.lat, entry.lon], p], {
        color: '#aef186',
        weight: 9,
        opacity: 0.30,
        dashArray: '10 7',
        lineCap: 'round',
        className: 'command-map-approach-glow'
      }).addTo(commandMap);
      mapObjects.push(approachGlow);

      const approach = L.polyline([[entry.lat, entry.lon], p], {
        color: '#c8ff8d',
        weight: 5,
        opacity: 0.98,
        dashArray: '10 7',
        lineCap: 'round',
        className: 'command-map-approach-line'
      }).addTo(commandMap);
      approach.bindPopup('<strong>Invisible Approach</strong><br>Access Entry to Primary Sit');
      mapObjects.push(approach);

      // MONAHINGA_PAGE2_CLEAR_APPROACH_ARROWS_2026_05_05
      // Clear directional approach arrows. Leaflet visual-only; safe if any coordinate is missing.
      try {
        const from = { lat: Number(entry.lat), lon: Number(entry.lon) };
        const to = { lat: Number(p[0]), lon: Number(p[1]) };
        if ([from.lat, from.lon, to.lat, to.lon].every(Number.isFinite)) {
          const bearingRad = Math.atan2(to.lon - from.lon, to.lat - from.lat);
          const bearingDeg = bearingRad * 180 / Math.PI;

          [0.38, 0.62].forEach((t) => {
            const arrowLat = from.lat + ((to.lat - from.lat) * t);
            const arrowLon = from.lon + ((to.lon - from.lon) * t);
            const arrow = L.marker([arrowLat, arrowLon], {
              interactive: false,
              keyboard: false,
              icon: L.divIcon({
                className: '',
                html: '<div class="command-map-approach-arrow" style="transform:rotate(' + bearingDeg.toFixed(2) + 'deg)"><span>↑</span></div>',
                iconSize: [28, 28],
                iconAnchor: [14, 14],
              })
            }).addTo(commandMap);
            mapObjects.push(arrow);
          });

          const labelLat = from.lat + ((to.lat - from.lat) * 0.50);
          const labelLon = from.lon + ((to.lon - from.lon) * 0.50);
          const approachLabel = L.marker([labelLat, labelLon], {
            interactive: false,
            keyboard: false,
            icon: L.divIcon({
              className: '',
              html: '<div class="command-map-approach-label">Approach → Sit</div>',
              iconSize: [112, 24],
              iconAnchor: [56, 34],
            })
          }).addTo(commandMap);
          mapObjects.push(approachLabel);

          // MONAHINGA_PAGE2_ACTION_COMMAND_AFTER_APPROACH_LABEL_2026_05_05
          // Direct action command beside the already-visible APPROACH label.
          // Uses windAssessment if available; otherwise gives a safe verification command.
          try {
            const actionState = (windAssessment && windAssessment.state) ? windAssessment.state : 'unknown';
            const actionText = actionState === 'bad'
              ? 'Do NOT approach from this side'
              : (actionState === 'risk'
                ? 'Shift entry downwind'
                : (actionState === 'safe'
                  ? 'Proceed as planned'
                  : 'Verify wind before approach'));
            const actionNote = actionState === 'bad'
              ? 'Pick a new entry or wait for wind shift.'
              : (actionState === 'risk'
                ? 'Keep scent off the sit funnel.'
                : (actionState === 'safe'
                  ? 'Still verify access, terrain, and permission.'
                  : 'Wind could not be confirmed from payload.'));
            const actionLat = from.lat + ((to.lat - from.lat) * 0.58);
            const actionLon = from.lon + ((to.lon - from.lon) * 0.58);
            const actionCommand = L.marker([actionLat, actionLon], {
              interactive:false,
              keyboard:false,
              icon:L.divIcon({
                className:'',
                html:'<div class="command-map-action-command ' + actionState + '">' + actionText + '<small>' + actionNote + '</small></div>',
                iconSize:[238,58],
                iconAnchor:[30,-6],
              })
            }).addTo(commandMap);
            mapObjects.push(actionCommand);
          } catch (_actionErr) {
            // Stay silent. Action command must never block map or 3D terrain rendering.
          }
        }
      } catch (_err) {
        // Stay silent. Directional helpers must never block map or 3D terrain rendering.
      }
    }

    const fallback = document.querySelector('.command-map-fallback');
    if (fallback) fallback.remove();
  }

  function boot(){
    let attempts = 0;
    const timer = setInterval(() => {
      attempts += 1;
      if (initCommandMap() || attempts > 40) {
        clearInterval(timer);
        if (attempts > 40) {
          const el = document.getElementById('commandLeafletMap');
          if (el && !el.querySelector('.command-map-fallback')) {
            const msg = document.createElement('div');
            msg.className = 'command-map-fallback';
            msg.textContent = '2D map could not load yet. The 3D terrain and run data are unchanged.';
            el.appendChild(msg);
          }
        }
      }
    }, 150);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
  window.addEventListener('resize', () => {
    if (commandMap) setTimeout(() => commandMap.invalidateSize(), 100);
  });
})();
</script>


<!-- MONAHINGA_RUNTIME_FIELD_COMMAND_2026_05_05 -->
<style>
#runtimeFieldCommandBox{
  position:absolute;
  right:16px;
  bottom:90px;
  z-index:9999;
  width:260px;
  border:2px solid rgba(159,215,255,.9);
  border-radius:14px;
  background:rgba(10,25,35,.92);
  color:#eef8ff;
  padding:10px;
  font-weight:900;
  font-size:13px;
  box-shadow:0 12px 30px rgba(0,0,0,.4);
  pointer-events:none;
}
#runtimeFieldCommandBox.safe{border-color:#9fffa0;color:#eaffd6;background:rgba(10,40,15,.9);}
#runtimeFieldCommandBox.risk{border-color:#ffd35a;color:#fff2b8;background:rgba(60,40,5,.92);}
#runtimeFieldCommandBox.bad{border-color:#ff5252;color:#ffe1e1;background:rgba(70,10,10,.95);}
</style>

<script>
(function(){
  function injectBox(){
    const map = document.querySelector("#commandLeafletMap");
    if(!map) return;

    if(document.getElementById("runtimeFieldCommandBox")) return;

    const box = document.createElement("div");
    box.id = "runtimeFieldCommandBox";
    box.innerHTML = "VERIFY WIND BEFORE APPROACH";
    map.parentElement.style.position = "relative";
    map.parentElement.appendChild(box);

    try{
      if(window.commandMapAssessApproachWind && window.lastPayload){
        const p = window.lastPayload;
        const site = (p.sites||[])[0];
        const entry = p.access_entry || p.access || p.entry;

        if(site && entry){
          const res = commandMapAssessApproachWind(
            p,
            {lat:entry.lat, lon:entry.lon},
            {lat:site.lat, lon:(site.lon||site.lng)}
          );

          if(res && res.state){
            box.className = res.state;
            if(res.state==="bad") box.innerHTML="DO NOT APPROACH FROM THIS SIDE";
            else if(res.state==="risk") box.innerHTML="SHIFT ENTRY DOWNWIND";
            else if(res.state==="safe") box.innerHTML="PROCEED AS PLANNED";
          }
        }
      }
    }catch(e){}
  }

  window.addEventListener("load", function(){
    setTimeout(injectBox, 800);
  });
})();
</script>


<!-- MONAHINGA_DEBUG_WIND_OUTPUT_2026_05_05 -->
<style>
#debugWindBox{
  position:absolute;
  right:16px;
  bottom:150px;
  z-index:9999;
  width:260px;
  border:2px solid rgba(159,215,255,.9);
  border-radius:12px;
  background:rgba(15,20,30,.95);
  color:#e8f4ff;
  padding:10px;
  font-size:12px;
  font-weight:900;
  box-shadow:0 10px 28px rgba(0,0,0,.5);
  pointer-events:none;
  white-space:pre-line;
}
</style>

<script>
(function(){
  function injectDebug(){
    const map = document.querySelector("#commandLeafletMap");
    if(!map) return;

    if(document.getElementById("debugWindBox")) return;

    const box = document.createElement("div");
    box.id = "debugWindBox";
    box.innerHTML = "DEBUG: WAITING...";
    map.parentElement.style.position = "relative";
    map.parentElement.appendChild(box);

    try{
      const p = window.lastPayload || window.lastCommandPayload || window.__MONAHINGA_COMMAND_PAYLOAD || null;

      if(!p){
        box.innerHTML = "NO PAYLOAD FOUND";
        return;
      }

      if(!window.commandMapAssessApproachWind){
        box.innerHTML = "NO WIND FUNCTION";
        return;
      }

      const site = ((p.sites||[]).find(s => Number(s.rank)===1) || (p.sites||[])[0]);
      const entry = p.access_entry || p.access || p.entry || p.base_camp;

      if(!site || !entry){
        box.innerHTML = "MISSING SITE OR ENTRY";
        return;
      }

      const res = window.commandMapAssessApproachWind(
        p,
        {lat:entry.lat, lon:(entry.lon||entry.lng)},
        {lat:site.lat, lon:(site.lon||site.lng)}
      );

      if(!res){
        box.innerHTML = "NO RESULT RETURNED";
        return;
      }

      let out = "";
      out += "STATE: " + (res.state || "none") + "
";
      if(res.angle !== undefined) out += "ANGLE: " + res.angle + "
";
      if(res.type !== undefined) out += "TYPE: " + res.type + "
";
      if(res.reason !== undefined) out += "REASON: " + res.reason + "
";

      box.innerHTML = out;

    }catch(e){
      box.innerHTML = "ERROR:
" + e.message;
    }
  }

  window.addEventListener("load", function(){
    setTimeout(injectDebug, 900);
  });
})();
</script>


<!-- MONAHINGA_FORCE_FIELD_COMMAND_VISIBLE_WIND_2026_05_05 -->
<script>
(function(){
  function cardinalToDeg(value){
    const raw = String(value || "").toUpperCase();
    const match = raw.match(/\b(NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW|NE|SE|SW|NW|N|E|S|W)\b/);
    if(!match) return null;
    const table = {
      N:0, NNE:22.5, NE:45, ENE:67.5,
      E:90, ESE:112.5, SE:135, SSE:157.5,
      S:180, SSW:202.5, SW:225, WSW:247.5,
      W:270, WNW:292.5, NW:315, NNW:337.5
    };
    return table[match[1]];
  }

  function angleDiff(a,b){
    if(a === null || b === null || !Number.isFinite(Number(a)) || !Number.isFinite(Number(b))) return null;
    const d = Math.abs(Number(a) - Number(b)) % 360;
    return d > 180 ? 360 - d : d;
  }

  function ensureBox(){
    const map = document.querySelector("#commandLeafletMap");
    if(!map) return null;

    let box = document.getElementById("runtimeFieldCommandBox");
    if(!box){
      box = document.createElement("div");
      box.id = "runtimeFieldCommandBox";
      map.parentElement.style.position = "relative";
      map.parentElement.appendChild(box);
    }

    box.style.position = "absolute";
    box.style.right = "16px";
    box.style.bottom = "90px";
    box.style.zIndex = "9999";
    box.style.width = "260px";
    box.style.borderRadius = "14px";
    box.style.padding = "10px";
    box.style.fontWeight = "900";
    box.style.fontSize = "13px";
    box.style.boxShadow = "0 12px 30px rgba(0,0,0,.4)";
    box.style.pointerEvents = "none";
    box.style.border = "2px solid rgba(159,215,255,.9)";
    box.style.background = "rgba(10,25,35,.92)";
    box.style.color = "#eef8ff";
    box.style.lineHeight = "1.15";
    return box;
  }

  function preferredWindText(){
    const trust = document.querySelector("#trustTags");
    if(trust && trust.dataset && trust.dataset.wind) return trust.dataset.wind;

    const allStrong = Array.from(document.querySelectorAll("strong"));
    for(const el of allStrong){
      const prev = el.previousElementSibling;
      if(prev && /preferred\s*wind/i.test(prev.textContent || "")) return el.textContent || "";
    }

    return "";
  }

  function currentWindText(){
    const windEl = document.querySelector("#operatorWindValue");
    return windEl ? (windEl.textContent || "") : "";
  }

  function paint(box, state, main, note){
    box.className = state;
    if(state === "safe"){
      box.style.borderColor = "#9fffa0";
      box.style.background = "rgba(10,40,15,.92)";
      box.style.color = "#eaffd6";
    } else if(state === "risk"){
      box.style.borderColor = "#ffd35a";
      box.style.background = "rgba(60,40,5,.94)";
      box.style.color = "#fff2b8";
    } else if(state === "bad"){
      box.style.borderColor = "#ff5252";
      box.style.background = "rgba(70,10,10,.95)";
      box.style.color = "#ffe1e1";
    } else {
      box.style.borderColor = "rgba(159,215,255,.9)";
      box.style.background = "rgba(10,25,35,.92)";
      box.style.color = "#eef8ff";
    }
    box.innerHTML = main + (note ? '<br><small style="display:block;margin-top:4px;font-size:10px;line-height:1.2;color:rgba(255,255,255,.74);font-weight:800;">' + note + '</small>' : '');
  }

  function updateForcedFieldCommand(){
    const box = ensureBox();
    if(!box) return;

    const currentText = currentWindText();
    const preferredText = preferredWindText();

    const currentDeg = cardinalToDeg(currentText);
    const preferredDeg = cardinalToDeg(preferredText);
    const diff = angleDiff(currentDeg, preferredDeg);

    if(diff === null){
      paint(box, "unknown", "VERIFY WIND BEFORE APPROACH", "Wind text not readable yet.");
      return;
    }

    // Product-safe decision rule:
    // close to preferred wind = proceed
    // moderate mismatch = adjust entry
    // major mismatch/opposite = do not commit from this entry
    if(diff <= 45){
      paint(box, "safe", "PROCEED AS PLANNED", "Current wind matches preferred wind. Still verify on site.");
    } else if(diff <= 135){
      paint(box, "risk", "SHIFT ENTRY DOWNWIND", "Current wind differs from preferred. Adjust entry before committing.");
    } else {
      paint(box, "bad", "DO NOT APPROACH FROM THIS SIDE", "Wind is opposite preferred. Pick a new entry or wait.");
    }
  }

  window.addEventListener("load", function(){
    setTimeout(updateForcedFieldCommand, 700);
    setTimeout(updateForcedFieldCommand, 1500);
    setTimeout(updateForcedFieldCommand, 3000);
  });

  // Keep it updated if live wind text changes after fetch.
  setInterval(updateForcedFieldCommand, 2500);
})();
</script>


<!-- MONAHINGA_RENDER_SAFE_WIND_COMMAND_FALLBACK_2026_05_05 -->
<script>
(function(){
  function cardinalFromText(value){
    const raw = String(value || "").toUpperCase();
    if(/NOT\s*SET|UNKNOWN|UNAVAILABLE|LOADING|VERIFY/.test(raw)) return null;
    const match = raw.match(/\b(NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW|NE|SE|SW|NW|N|E|S|W)\b/);
    return match ? match[1] : null;
  }

  function cardinalToDeg(card){
    const table = {
      N:0, NNE:22.5, NE:45, ENE:67.5,
      E:90, ESE:112.5, SE:135, SSE:157.5,
      S:180, SSW:202.5, SW:225, WSW:247.5,
      W:270, WNW:292.5, NW:315, NNW:337.5
    };
    return Object.prototype.hasOwnProperty.call(table, card) ? table[card] : null;
  }

  function angleDiff(a,b){
    if(a === null || b === null) return null;
    const d = Math.abs(Number(a) - Number(b)) % 360;
    return d > 180 ? 360 - d : d;
  }

  function currentWindText(){
    const el = document.querySelector("#operatorWindValue");
    return el ? (el.textContent || "") : "";
  }

  function preferredWindText(){
    const trust = document.querySelector("#trustTags");
    if(trust && trust.dataset && trust.dataset.wind) return trust.dataset.wind;

    const labels = Array.from(document.querySelectorAll("label"));
    for(const label of labels){
      if(/preferred\s*wind/i.test(label.textContent || "")){
        const strong = label.parentElement && label.parentElement.querySelector("strong");
        if(strong) return strong.textContent || "";
      }
    }

    const allStrong = Array.from(document.querySelectorAll("strong"));
    for(const el of allStrong){
      const prev = el.previousElementSibling;
      if(prev && /preferred\s*wind/i.test(prev.textContent || "")) return el.textContent || "";
    }

    return "";
  }

  function ensureBox(){
    const map = document.querySelector("#commandLeafletMap");
    if(!map) return null;

    let box = document.getElementById("runtimeFieldCommandBox");
    if(!box){
      box = document.createElement("div");
      box.id = "runtimeFieldCommandBox";
      map.parentElement.style.position = "relative";
      map.parentElement.appendChild(box);
    }

    box.style.position = "absolute";
    box.style.right = "16px";
    box.style.bottom = "90px";
    box.style.zIndex = "10001";
    box.style.width = "270px";
    box.style.borderRadius = "14px";
    box.style.padding = "10px";
    box.style.fontWeight = "900";
    box.style.fontSize = "13px";
    box.style.boxShadow = "0 12px 30px rgba(0,0,0,.42)";
    box.style.pointerEvents = "none";
    box.style.lineHeight = "1.15";
    return box;
  }

  function paint(box, state, main, note){
    box.className = state;
    if(state === "safe"){
      box.style.border = "2px solid #9fffa0";
      box.style.background = "rgba(10,40,15,.94)";
      box.style.color = "#eaffd6";
    } else if(state === "risk"){
      box.style.border = "2px solid #ffd35a";
      box.style.background = "rgba(60,40,5,.96)";
      box.style.color = "#fff2b8";
    } else if(state === "bad"){
      box.style.border = "2px solid #ff5252";
      box.style.background = "rgba(70,10,10,.96)";
      box.style.color = "#ffe1e1";
    } else {
      box.style.border = "2px solid rgba(159,215,255,.92)";
      box.style.background = "rgba(10,25,35,.94)";
      box.style.color = "#eef8ff";
    }
    box.innerHTML = main + (note ? '<br><small style="display:block;margin-top:4px;font-size:10px;line-height:1.2;color:rgba(255,255,255,.75);font-weight:800;">' + note + '</small>' : '');
  }

  function updateRenderSafeWindCommand(){
    const box = ensureBox();
    if(!box) return;

    const currentCard = cardinalFromText(currentWindText());
    const preferredCard = cardinalFromText(preferredWindText());

    // Render/demo-safe behavior:
    // If current wind is not set but preferred wind exists, do not fake live wind.
    // Give a clear conditional command tied to the planning wind.
    if(!currentCard && preferredCard){
      paint(
        box,
        "risk",
        "HUNT ONLY IF " + preferredCard + " WIND HOLDS",
        "Current wind is not set on Render. Set live wind to upgrade this command."
      );
      return;
    }

    if(!currentCard && !preferredCard){
      paint(box, "unknown", "SET WIND TO ACTIVATE", "No current or preferred wind is readable yet.");
      return;
    }

    if(currentCard && !preferredCard){
      paint(box, "unknown", "SET PREFERRED WIND", "Current wind is readable, but preferred wind is missing.");
      return;
    }

    const diff = angleDiff(cardinalToDeg(currentCard), cardinalToDeg(preferredCard));

    if(diff === null){
      paint(box, "unknown", "VERIFY WIND BEFORE APPROACH", "Wind direction could not be compared.");
      return;
    }

    if(diff <= 45){
      paint(box, "safe", "PROCEED AS PLANNED", "Current wind matches preferred wind. Still verify on site.");
    } else if(diff <= 135){
      paint(box, "risk", "SHIFT ENTRY DOWNWIND", "Current wind differs from preferred. Adjust entry before committing.");
    } else {
      paint(box, "bad", "DO NOT APPROACH FROM THIS SIDE", "Wind is opposite preferred. Pick a new entry or wait.");
    }
  }

  window.addEventListener("load", function(){
    setTimeout(updateRenderSafeWindCommand, 500);
    setTimeout(updateRenderSafeWindCommand, 1200);
    setTimeout(updateRenderSafeWindCommand, 2500);
  });

  setInterval(updateRenderSafeWindCommand, 2500);
})();
</script>

</body>
</html>''')