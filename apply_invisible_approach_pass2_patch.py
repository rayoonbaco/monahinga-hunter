from __future__ import annotations

from pathlib import Path
import shutil
import sys

TARGET = Path("engine/command_surface/template.py")
BACKUP = Path("engine/command_surface/template.py.bak_invisible_approach_pass2")

START_MARKER = "      function approachRiskClass(score) {"
END_MARKER = "      function polygonShape(rings) {"

NEW_BLOCK = r'''      function approachRiskClass(score) {
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
      function scoreApproachCandidate(nx, ny, t, site, scentHeadingDeg) {
        const slope = localSlopeSignal(nx, ny);
        const p = sitePoint(site);
        const dx = nx - p.nx;
        const dy = ny - p.ny;
        const angleToPoint = (THREE.MathUtils.radToDeg(Math.atan2(dx, dy)) + 360) % 360;
        const scentPenalty = angleDeltaDeg(angleToPoint, scentHeadingDeg) < 48 ? 18 : 0;
        const edgePenalty = (nx < 0.035 || nx > 0.965 || ny < 0.035 || ny > 0.965) ? 8 : 0;
        const finalApproachPenalty = t > 0.76 ? 7 : 0;
        return slope * 1.55 + scentPenalty + edgePenalty + finalApproachPenalty;
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
        const highCount = risks.filter((item) => item >= 68).length;
        const cautionCount = risks.filter((item) => item >= 38 && item < 68).length;
        const windText = liveWindState && liveWindState.summary ? liveWindState.summary : ((operatorWindValue && operatorWindValue.textContent) || 'wind unavailable');
        if (highCount >= 4 || avgRisk >= 68) return 'High blowout risk: route or scent path likely crosses too much danger ground. Wind: ' + windText + '.';
        if (cautionCount >= 5 || avgRisk >= 38) return 'Caution: dotted path uses terrain bias, but verify wind, exposure, and final approach before committing. Wind: ' + windText + '.';
        return 'Low-risk read: route favors terrain shadow and keeps scent pressure limited on this first-pass model. Wind: ' + windText + '.';
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

'''

DEPTH_OLD = "      depthSlider.addEventListener('input', () => { applyHeights(); rebuildOverlays(); updateCamera(); });"
DEPTH_NEW = "      depthSlider.addEventListener('input', () => { applyHeights(); rebuildOverlays(); if (state.invisibleApproachVisible) rebuildInvisibleApproachOverlay(currentApproachSite()); updateCamera(); });"


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: Could not find {TARGET}. Run this from the project root folder.")
        return 1

    text = TARGET.read_text(encoding="utf-8")
    required = [
        "function buildApproachRoute(site)",
        "function routeDotRisk(t, nx, ny, site, scentHeadingDeg)",
        "function rebuildInvisibleApproachOverlay(site)",
        "id=\"invisibleApproachBtn\"",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        print("ERROR: This does not look like the Pass 1 Invisible Approach template.py.")
        print("Missing markers:", ", ".join(missing))
        return 1

    start = text.find(START_MARKER)
    end = text.find(END_MARKER, start)
    if start < 0 or end < 0 or end <= start:
        print("ERROR: Could not locate the Invisible Approach function block safely.")
        return 1

    if not BACKUP.exists():
        shutil.copy2(TARGET, BACKUP)
        print(f"Backup created: {BACKUP}")
    else:
        print(f"Backup already exists: {BACKUP}")

    text = text[:start] + NEW_BLOCK + text[end:]

    if DEPTH_OLD in text:
        text = text.replace(DEPTH_OLD, DEPTH_NEW, 1)
    else:
        print("Note: depth-slider listener was not changed because the exact old line was not found.")

    TARGET.write_text(text, encoding="utf-8")
    print("PASS 2 applied: smarter Invisible Approach route/risk/explanation logic installed.")
    print("Next: run python -m py_compile engine\\command_surface\\template.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
