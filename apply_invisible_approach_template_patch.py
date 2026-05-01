from pathlib import Path

path = Path('engine/command_surface/template.py')
text = path.read_text(encoding='utf-8')

def repl(old, new):
    global text
    if old not in text:
        raise SystemExit(f'Missing target:\n{old[:200]}')
    text = text.replace(old, new, 1)

# 1) CSS active button + approach HUD accent
repl(
".scene-tools{position:absolute;top:10px;right:10px;z-index:5;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:40%}.scene-tool-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:12px;border:1px solid rgba(255,255,255,.1);background:rgba(8,15,25,.82);color:var(--text);text-decoration:none;cursor:pointer;backdrop-filter:blur(10px)}.scene-tool-btn:hover{background:rgba(20,30,44,.92)}.cursor-hud",
".scene-tools{position:absolute;top:10px;right:10px;z-index:5;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:40%}.scene-tool-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:12px;border:1px solid rgba(255,255,255,.1);background:rgba(8,15,25,.82);color:var(--text);text-decoration:none;cursor:pointer;backdrop-filter:blur(10px)}.scene-tool-btn:hover{background:rgba(20,30,44,.92)}.scene-tool-btn.active{background:rgba(174,241,134,.16);border-color:rgba(174,241,134,.36);box-shadow:0 0 0 1px rgba(174,241,134,.10) inset}.approach-hud{display:none;border-color:rgba(174,241,134,.20);background:rgba(5,18,12,.74)}.approach-hud.visible{display:block}.approach-risk-low{color:#bdf6a7}.approach-risk-caution{color:#f3d58a}.approach-risk-high{color:#ffb08e}.cursor-hud"
)

# 2) Scene tool button + HUD card
repl(
'<button id="resetViewBtn" class="scene-tool-btn" type="button">Reset View</button><button id="saveViewHelpBtn" class="scene-tool-btn" type="button">How to Save View</button><button id="downloadSummaryBtn" class="scene-tool-btn" type="button">Download Summary</button>',
'<button id="resetViewBtn" class="scene-tool-btn" type="button">Reset View</button><button id="invisibleApproachBtn" class="scene-tool-btn" type="button">Invisible Approach</button><button id="saveViewHelpBtn" class="scene-tool-btn" type="button">How to Save View</button><button id="downloadSummaryBtn" class="scene-tool-btn" type="button">Download Summary</button>'
)
repl(
'<div class="hud-card" id="liveWindHud"><span class="label">Live wind near primary sit</span><strong id="liveWindHudSummary">Loading live wind…</strong><div id="liveWindHudMeta" class="micro-copy">Fetching current direction and speed.</div></div></div></div></main>',
'<div class="hud-card" id="liveWindHud"><span class="label">Live wind near primary sit</span><strong id="liveWindHudSummary">Loading live wind…</strong><div id="liveWindHudMeta" class="micro-copy">Fetching current direction and speed.</div></div><div class="hud-card approach-hud" id="invisibleApproachHud"><span class="label">Invisible Approach</span><strong id="invisibleApproachSummary">Layer off</strong><div id="invisibleApproachMeta" class="micro-copy">Toggle to show approach risk from Access Entry to the selected sit.</div></div></div></div></main>'
)

# 3) DOM hooks
repl(
"  const resetViewBtn = document.getElementById('resetViewBtn');\n  const saveViewHelpBtn = document.getElementById('saveViewHelpBtn');",
"  const resetViewBtn = document.getElementById('resetViewBtn');\n  const invisibleApproachBtn = document.getElementById('invisibleApproachBtn');\n  const saveViewHelpBtn = document.getElementById('saveViewHelpBtn');"
)
repl(
"  const liveWindHudSummary = document.getElementById('liveWindHudSummary');\n  const liveWindHudMeta = document.getElementById('liveWindHudMeta');",
"  const liveWindHudSummary = document.getElementById('liveWindHudSummary');\n  const liveWindHudMeta = document.getElementById('liveWindHudMeta');\n  const invisibleApproachHud = document.getElementById('invisibleApproachHud');\n  const invisibleApproachSummary = document.getElementById('invisibleApproachSummary');\n  const invisibleApproachMeta = document.getElementById('invisibleApproachMeta');"
)

# 4) State expansion
repl(
"currentPadusMode: payload.defaultPadusMode || 'hybrid', widthWorld: 24, depthWorld: 24, rotationY: -0.92, tiltDeg: Number(tiltSlider.value || 30), cameraRadius: 18, pinControlMode: null, pinControlIndex: -1, pinControlLabel: ''",
"currentPadusMode: payload.defaultPadusMode || 'hybrid', widthWorld: 24, depthWorld: 24, rotationY: -0.92, tiltDeg: Number(tiltSlider.value || 30), cameraRadius: 18, pinControlMode: null, pinControlIndex: -1, pinControlLabel: '', invisibleApproachVisible: false, invisibleApproachRank: 1"
)

# 5) Update selected card hook to refresh current approach
repl(
"function updateSelectedSiteCard(site) { if (!site) return; if (selectedSiteTitle) selectedSiteTitle.textContent = site.title || 'Selected sit'; if (selectedSiteCoords) selectedSiteCoords.textContent = formatSiteCoords(site); if (copyCoordsBtn) copyCoordsBtn.dataset.copyText = site.lat.toFixed(6) + ', ' + site.lon.toFixed(6); updateExecutiveSummaryForSite(site); updateFocusOverlay(site); }",
"function updateSelectedSiteCard(site) { if (!site) return; state.invisibleApproachRank = Number(site.rank || state.invisibleApproachRank || 1); if (selectedSiteTitle) selectedSiteTitle.textContent = site.title || 'Selected sit'; if (selectedSiteCoords) selectedSiteCoords.textContent = formatSiteCoords(site); if (copyCoordsBtn) copyCoordsBtn.dataset.copyText = site.lat.toFixed(6) + ', ' + site.lon.toFixed(6); updateExecutiveSummaryForSite(site); updateFocusOverlay(site); if (typeof rebuildInvisibleApproachOverlay === 'function') rebuildInvisibleApproachOverlay(site); }"
)

# 6) Add invisible approach group
repl(
"const fillGroup = new THREE.Group(), boundaryGroup = new THREE.Group(), corridorGroup = new THREE.Group(), markerGroup = new THREE.Group(), windGroup = new THREE.Group(), focusGroup = new THREE.Group(), coverOverlayGroup = new THREE.Group();\n      scene.add(fillGroup); scene.add(boundaryGroup); scene.add(corridorGroup); scene.add(markerGroup); scene.add(windGroup); scene.add(focusGroup); scene.add(coverOverlayGroup);",
"const fillGroup = new THREE.Group(), boundaryGroup = new THREE.Group(), corridorGroup = new THREE.Group(), markerGroup = new THREE.Group(), windGroup = new THREE.Group(), focusGroup = new THREE.Group(), coverOverlayGroup = new THREE.Group(), invisibleApproachGroup = new THREE.Group();\n      scene.add(fillGroup); scene.add(boundaryGroup); scene.add(corridorGroup); scene.add(markerGroup); scene.add(windGroup); scene.add(focusGroup); scene.add(coverOverlayGroup); scene.add(invisibleApproachGroup);\n      invisibleApproachGroup.visible = false;"
)

# 7) Insert functions after drawWindOverlay
invisible_js = r'''      function windLabelToHeading(label) {
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
      function approachRiskClass(score) {
        if (score >= 68) return { label: 'High', css: 'approach-risk-high', color: 0xff5f45 };
        if (score >= 38) return { label: 'Caution', css: 'approach-risk-caution', color: 0xffd166 };
        return { label: 'Low', css: 'approach-risk-low', color: 0xaef186 };
      }
      function routeDotRisk(t, nx, ny, site, scentHeadingDeg) {
        const centerPull = 1 - Math.min(1, Math.hypot(nx - 0.5, ny - 0.5) * 1.6);
        const exposure = Math.abs(currentHeight(nx, ny) - currentHeight(clamp(nx + 0.025, 0, 1), clamp(ny + 0.025, 0, 1))) * 3.0;
        const p = sitePoint(site);
        const dx = nx - p.nx;
        const dy = ny - p.ny;
        const angleToDot = (THREE.MathUtils.radToDeg(Math.atan2(dx, dy)) + 360) % 360;
        const delta = Math.abs((((angleToDot - scentHeadingDeg) + 540) % 360) - 180);
        const downwindRisk = delta < 38 ? 34 * (1 - delta / 38) : 0;
        const sitPressure = t > 0.72 ? 18 * ((t - 0.72) / 0.28) : 0;
        const corridorPressure = (payload.corridors || []).length ? 7 * centerPull : 3 * centerPull;
        return clamp(18 + exposure + downwindRisk + sitPressure + corridorPressure, 8, 92);
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
        const count = 18;
        for (let i = 0; i <= count; i += 1) {
          const t = i / count;
          const bend = Math.sin(t * Math.PI) * 0.055;
          const terrainBias = (currentHeight(clamp(start.nx + dx * t + px * 0.04, 0, 1), clamp(start.ny + dy * t + py * 0.04, 0, 1)) > currentHeight(clamp(start.nx + dx * t - px * 0.04, 0, 1), clamp(start.ny + dy * t - py * 0.04, 0, 1))) ? -1 : 1;
          const meander = Math.sin(t * Math.PI * 2.0) * 0.018 + bend * terrainBias;
          points.push({
            nx: clamp(start.nx + dx * t + px * meander, 0.02, 0.98),
            ny: clamp(start.ny + dy * t + py * meander, 0.02, 0.98),
            t,
          });
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
          const radius = idx === route.points.length - 1 ? 0.13 : 0.095;
          const dot = new THREE.Mesh(
            new THREE.SphereGeometry(radius, 12, 12),
            new THREE.MeshStandardMaterial({ color: dotRisk.color, emissive: dotRisk.color, emissiveIntensity: 0.20, roughness:0.48, metalness:0.02, transparent:true, opacity:0.94 })
          );
          dot.position.copy(worldPoint(pt.nx, pt.ny, 0.34));
          invisibleApproachGroup.add(dot);
        });
        const linePoints = route.points.map((pt) => worldPoint(pt.nx, pt.ny, 0.23));
        if (linePoints.length > 1) invisibleApproachGroup.add(makeTerrainLine(linePoints, new THREE.Color(0xaef186), 0.34));
        addScentCone(activeSite, scentHeading, avgRisk);
        invisibleApproachGroup.visible = !!state.invisibleApproachVisible;
        if (invisibleApproachSummary) {
          invisibleApproachSummary.className = risk.css;
          invisibleApproachSummary.textContent = Math.round(avgRisk) + ' / 100 — ' + risk.label;
        }
        if (invisibleApproachMeta) {
          invisibleApproachMeta.textContent = 'Dotted route from Access Entry to selected sit. Red scent wedge shows estimated downwind danger. Field verify before using.';
        }
      }
      function setInvisibleApproachVisible(visible) {
        state.invisibleApproachVisible = !!visible;
        invisibleApproachGroup.visible = state.invisibleApproachVisible;
        if (invisibleApproachBtn) invisibleApproachBtn.classList.toggle('active', state.invisibleApproachVisible);
        if (invisibleApproachHud) invisibleApproachHud.classList.toggle('visible', state.invisibleApproachVisible);
        if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite());
      }
'''
repl(
"      function drawWindOverlay(read) { while (windGroup.children.length) windGroup.remove(windGroup.children[0]); const primarySite = siteByRank(1) || (payload.sites || [])[0]; if (!primarySite || !read || !read.ok || typeof read.arrow_heading_deg !== 'number') return; const p = sitePoint(primarySite); const origin = worldPoint(p.nx, p.ny, 0.9); const heading = THREE.MathUtils.degToRad(Number(read.arrow_heading_deg)); const dirVec = new THREE.Vector3(Math.sin(heading), 0, Math.cos(heading)).normalize(); const speed = Math.max(4, Number(read.speed_mph || 0)); const len = clamp(1.8 + speed * 0.08, 1.8, 4.2); const arrow = new THREE.ArrowHelper(dirVec, origin, len, 0xbde79b, 0.48, 0.24); windGroup.add(arrow); }",
"      function drawWindOverlay(read) { while (windGroup.children.length) windGroup.remove(windGroup.children[0]); const primarySite = siteByRank(1) || (payload.sites || [])[0]; if (!primarySite || !read || !read.ok || typeof read.arrow_heading_deg !== 'number') return; const p = sitePoint(primarySite); const origin = worldPoint(p.nx, p.ny, 0.9); const heading = THREE.MathUtils.degToRad(Number(read.arrow_heading_deg)); const dirVec = new THREE.Vector3(Math.sin(heading), 0, Math.cos(heading)).normalize(); const speed = Math.max(4, Number(read.speed_mph || 0)); const len = clamp(1.8 + speed * 0.08, 1.8, 4.2); const arrow = new THREE.ArrowHelper(dirVec, origin, len, 0xbde79b, 0.48, 0.24); windGroup.add(arrow); }\n" + invisible_js
)

# 8) Reset should turn layer off; focus already rebuilds through selected card
repl(
"function resetView() { clearPinControlMode(); state.rotationY = initialView.rotationY;",
"function resetView() { clearPinControlMode(); setInvisibleApproachVisible(false); state.rotationY = initialView.rotationY;"
)

# 9) After anchor/pin placement updates, refresh approach overlay if visible
text = text.replace("rebuildOverlays();\n          updateExecutiveSummaryForAnchor('Access Entry'", "rebuildOverlays();\n          if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite());\n          updateExecutiveSummaryForAnchor('Access Entry'", 1)
text = text.replace("rebuildOverlays();\n          updateExecutiveSummaryForAnchor('Base Camp'", "rebuildOverlays();\n          if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite());\n          updateExecutiveSummaryForAnchor('Base Camp'", 1)

# 10) Button listener
repl(
"      if (resetViewBtn) resetViewBtn.addEventListener('click', resetView);\n      if (saveViewHelpBtn) saveViewHelpBtn.addEventListener('click', showSaveViewHelp);",
"      if (resetViewBtn) resetViewBtn.addEventListener('click', resetView);\n      if (invisibleApproachBtn) invisibleApproachBtn.addEventListener('click', () => setInvisibleApproachVisible(!state.invisibleApproachVisible));\n      if (saveViewHelpBtn) saveViewHelpBtn.addEventListener('click', showSaveViewHelp);"
)

# 11) Live wind refresh also updates overlay
repl(
"drawWindOverlay(read); const current = siteByRank(1); if (current) updateExecutiveSummaryForSite(current);",
"drawWindOverlay(read); if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite()); const current = siteByRank(1); if (current) updateExecutiveSummaryForSite(current);"
)

backup = path.with_suffix(path.suffix + '.before_invisible_approach')
if not backup.exists():
    backup.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
path.write_text(text, encoding='utf-8')
print('[OK] patched engine/command_surface/template.py')
print('[OK] backup saved as engine/command_surface/template.py.before_invisible_approach')
