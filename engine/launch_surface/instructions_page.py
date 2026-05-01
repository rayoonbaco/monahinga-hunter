from __future__ import annotations

FEEDBACK_EMAIL = "rayoonbaco@yahoo.com"

INSTRUCTIONS_PAGE_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Monahinga™ Instructions</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#061018;--bg2:#020509;--panel:rgba(9,16,23,.94);--line:rgba(255,255,255,.09);--text:#e9e2d4;--muted:#a9b6bf;--green:#a8f183;--gold:#f3d78b;--blue:#83c9ff}
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text)}
body:before{content:"";position:fixed;inset:0;background:radial-gradient(circle at 18% 10%,rgba(168,241,131,.13),transparent 24%),radial-gradient(circle at 82% 16%,rgba(131,201,255,.11),transparent 25%),radial-gradient(circle at 50% 100%,rgba(243,215,139,.08),transparent 30%);pointer-events:none}.shell{position:relative;max-width:1120px;margin:0 auto;padding:28px 20px 42px}.top{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:18px}.brand{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#b3c1ca}.nav{display:flex;gap:10px;flex-wrap:wrap}.nav a{color:var(--text);text-decoration:none;border:1px solid var(--line);background:rgba(255,255,255,.04);border-radius:999px;padding:10px 13px;font-size:13px}.hero{padding:24px;border:1px solid var(--line);border-radius:26px;background:linear-gradient(180deg,rgba(12,24,34,.94),rgba(6,11,17,.96));box-shadow:0 24px 80px rgba(0,0,0,.34)}h1{font-size:42px;line-height:1.03;margin:8px 0 10px}.sub{max-width:860px;color:var(--muted);font-size:17px;line-height:1.55}.version{margin-top:16px;padding:14px 16px;border-radius:18px;border:1px solid rgba(243,215,139,.22);background:rgba(243,215,139,.07);color:#f2e6c5;line-height:1.45}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:18px}.card{padding:20px;border-radius:22px;border:1px solid var(--line);background:var(--panel)}h2{margin:0 0 12px;font-size:20px}.copy{color:#d8e1e7;line-height:1.55}.copy strong{color:#fff0d0}.list{margin:10px 0 0;padding-left:20px;color:#d8e1e7;line-height:1.55}.cta{display:inline-block;margin-top:12px;padding:12px 15px;border-radius:14px;background:var(--green);color:#07110a;text-decoration:none;font-weight:800}.soft{color:var(--muted);font-size:13px;line-height:1.45}.wide{grid-column:1/-1}.mini-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}.mini{padding:14px;border-radius:18px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.035)}.mini strong{display:block;color:#fff0d0;margin-bottom:5px}.accordion{display:grid;gap:10px;margin-top:12px}details{border:1px solid rgba(255,255,255,.09);border-radius:18px;background:rgba(255,255,255,.035);overflow:hidden}summary{cursor:pointer;padding:15px 16px;font-weight:800;color:#fff0d0;list-style:none}summary::-webkit-details-marker{display:none}summary:after{content:"+";float:right;color:var(--green)}details[open] summary:after{content:"–"}.detail-body{padding:0 16px 16px;color:#d8e1e7;line-height:1.55}.detail-body ul{margin:8px 0 0;padding-left:20px}.logo-mark{width:76px;height:76px;border-radius:22px;border:1px solid rgba(255,255,255,.12);background:radial-gradient(circle at 52% 26%,rgba(243,215,139,.95),rgba(243,215,139,.25) 18%,transparent 20%),linear-gradient(145deg,rgba(168,241,131,.25),rgba(131,201,255,.14)),#07111a;position:relative;box-shadow:inset 0 1px 0 rgba(255,255,255,.08)}.logo-mark:before{content:"";position:absolute;left:15px;right:15px;bottom:18px;height:28px;background:linear-gradient(135deg,transparent 0 23%,rgba(168,241,131,.95) 24% 48%,transparent 49%),linear-gradient(45deg,transparent 0 42%,rgba(131,201,255,.7) 43% 54%,transparent 55%);clip-path:polygon(0 100%,25% 40%,42% 75%,62% 22%,100% 100%)}.logo-row{display:flex;gap:15px;align-items:center}.brand-note{margin-top:16px;border-top:1px solid rgba(255,255,255,.08);padding-top:14px;color:#aebbc4;font-size:13px;line-height:1.45}@media(max-width:820px){.grid,.mini-grid{grid-template-columns:1fr}h1{font-size:34px}.shell{padding:22px 14px 32px}}
</style>
</head>
<body>
<div class="shell">
  <div class="top">
    <div class="brand">Monahinga™ · Instructions</div>
    <div class="nav"><a href="/">Launch app</a><a href="/checkout">Unlock 5 views</a><a href="mailto:__FEEDBACK_EMAIL__?subject=Monahinga%20Version%201%20Feedback">Send feedback</a></div>
  </div>
  <section class="hero">
    <div class="brand">Version 1 — Built for hunters. Evolving with you.</div>
    <h1>Use Monahinga™ like a disciplined scouting partner.</h1>
    <div class="sub">Draw one honest hunting box, run the terrain intelligence, then use the 3D command surface to compare legal access, terrain pull, cover, wind fit, and stand options without pretending the tool replaces field judgment.</div>
    <div class="version"><strong>Launch flow:</strong> your first terrain view is free. After that, unlock <strong>5 terrain intelligence views for $7</strong>. Version 1 is intentionally clean and direct; Version 2 will improve through hunter feedback and move toward personalized terrain intelligence.</div>
    <div class="mini-grid">
      <div class="mini"><strong>1. Draw</strong><span class="soft">Search, paste coordinates, or draw the box over the country you want evaluated.</span></div>
      <div class="mini"><strong>2. Run</strong><span class="soft">Launch the terrain read and let Monahinga™ build the 3D command surface.</span></div>
      <div class="mini"><strong>3. Save</strong><span class="soft">Use download buttons, snapshot/report buttons, or desktop screenshots for your scouting files.</span></div>
    </div>
  </section>
  <div class="grid">
    <section class="card wide">
      <h2>Sequential field guide</h2>
      <div class="accordion">
        <details open><summary>1. Start with your free first view</summary><div class="detail-body">The first terrain view is meant to prove the flow: draw a box, launch the run, and inspect the 3D command surface. If it gives you value, use the checkout button to unlock 5 more views for $7.</div></details>
        <details><summary>2. Search, draw, or paste coordinates</summary><div class="detail-body"><ul><li>Use the search box to jump near a town, road, camp, public parcel, creek, or landmark.</li><li>Draw a rectangle around only the terrain you want studied.</li><li>Use pasted bbox coordinates when you already know the exact min lon, min lat, max lon, max lat.</li><li>Keep the box inside the lower 48 so the legal-land and terrain checks stay truthful.</li></ul></div></details>
        <details><summary>3. Read the bbox fields before launch</summary><div class="detail-body">The four bbox fields are the exact coordinates the app will study. If you edit the rectangle, those fields update. If you paste or type coordinates, the rectangle updates. The goal is simple: the map, the fields, and the terrain run should all point to the same hunting box.</div></details>
        <details><summary>4. Set Base Camp</summary><div class="detail-body">Use Base Camp for the place you want to reference while studying access. This can be your camp, parking area, truck location, cabin, or starting point. Base Camp is not automatically a stand recommendation; it is a navigation anchor for comparing access routes and terrain movement.</div></details>
        <details><summary>5. Use pins, move them, and name them</summary><div class="detail-body"><ul><li>Ranked sit pins show the app's best terrain reads for the selected box.</li><li>Use the pin labels as scouting language, not as a command to hunt a spot.</li><li>Move or rename your own field-reference pins when you want to track places like bedding edge, creek crossing, glassing point, scrape line, access trail, or backup sit.</li><li>Keep names short so screenshots and reports stay readable.</li></ul></div></details>
        <details><summary>6. Watch the 3D cursor GPS readout</summary><div class="detail-body">On the 3D terrain page, moving your cursor across the terrain can expose useful GPS-style readings near the surface. Use that readout to connect what you see on the 3D terrain with real-world map locations, screenshots, and scouting notes.</div></details>
        <details><summary>7. Toggle terrain layers and overlays</summary><div class="detail-body"><ul><li><strong>Terrain</strong> gives the broad 3D shape.</li><li><strong>Hillshade</strong> helps reveal folds, benches, bowls, saddles, and shaded sides.</li><li><strong>Slope</strong> helps identify steep access problems and possible movement funnels.</li><li><strong>Relief</strong> helps exaggerate subtle land changes that may matter to animals and hunters.</li><li>Legal and cover overlays should be treated as decision support, not permission to hunt.</li></ul></div></details>
        <details><summary>8. Use buttons, downloads, and screenshots</summary><div class="detail-body">The app includes practical buttons such as Back to Box / Launch, Reset View, Snapshot Report, Download Summary, layer buttons, PAD-US display buttons, copy-coordinate buttons, and checkout buttons. Use the download buttons when available. You are also welcome to use Print Screen, Snipping Tool, or browser screenshots to save desktop scouting files for your own trip folder.</div></details>
        <details><summary>9. Read Page 2 like a hunter</summary><div class="detail-body">Start with legal coverage and the ranked stand options. Then inspect terrain shape, access, wind fit, cover, and whether the move is actually huntable. The tool is strongest when you compare the output against field judgment, local rules, fresh sign, pressure, season timing, and your own experience.</div></details>
      </div>
    </section>
    <section class="card">
      <h2>Unlock more views</h2>
      <div class="copy">The launch offer is simple: <strong>first view free, then 5 terrain intelligence views for $7</strong>.</div>
      <a class="cta" href="/checkout">Unlock 5 views</a>
      <p class="soft">Checkout is isolated from the terrain viewer so monetization does not risk the Page 2 3D surface.</p>
    </section>
    <section class="card">
      <h2>Logo concept</h2>
      <div class="logo-row"><div class="logo-mark" aria-hidden="true"></div><div class="copy"><strong>Concept:</strong> moon over folded terrain, with a subtle route/edge line. It should feel premium, quiet, field-tested, and unmistakably Monahinga™.</div></div>
    </section>
    <section class="card wide">
      <h2>Version 1 & Future Development</h2>
      <div class="copy">This is <strong>Version 1 of Monahinga™</strong>. The tool will evolve with real hunter input. Future updates are aimed at personalized terrain intelligence: letting hunters influence how the algorithm thinks by weighting variables like access routes, wind assumptions, terrain preferences, pressure tolerance, movement assumptions, and what each hunter personally considers a huntable spot.</div>
      <ul class="list"><li>What features would make Monahinga™ more useful in the field?</li><li>How would you tweak the terrain analysis?</li><li>What makes a spot huntable to you?</li></ul>
      <a class="cta" href="mailto:__FEEDBACK_EMAIL__?subject=Monahinga%20Version%201%20Feedback&body=Feature%20ideas:%0A%0ATerrain%20analysis%20feedback:%0A%0AWhat%20makes%20a%20spot%20huntable%20to%20me:%0A">Help shape Monahinga™</a>
      <div class="brand-note">Monahinga™ is a protected brand name of its owner. monahinga.com is the official website property. Keep the brand capitalization exactly as Monahinga™ in public-facing material.</div>
    </section>
    <section class="card wide">
      <h2>Instagram Reel launch idea</h2>
      <div class="copy">Open with the 3D terrain reveal, cut to drawing a hunting box, show wildlife changing by region, flash the ranked sit pins, and end with: <strong>Version 1 is live — help shape the future of personalized hunting intelligence.</strong> Use cinematic outdoor music with tasteful wildlife ambience such as buck snorts, scraping, turkey calls, hog sounds, and deep woods atmosphere.</div>
    </section>
  </div>
</div>
</body>
</html>'''


def render_instructions_page() -> str:
    return INSTRUCTIONS_PAGE_TEMPLATE.replace("__FEEDBACK_EMAIL__", FEEDBACK_EMAIL)
