from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
candidates = [
    ROOT / "apps" / "api" / "template.py",
    ROOT / "apps" / "template.py",
    ROOT / "template.py",
]
template_path = next((p for p in candidates if p.exists()), None)

if not template_path:
    matches = list(ROOT.rglob("template.py"))
    if len(matches) == 1:
        template_path = matches[0]
    else:
        print("Could not uniquely find template.py.")
        print("Run this from the project root, likely:")
        print(r'cd /d "%USERPROFILE%\Desktop\ENOUGH\HUNTER"')
        print("Found:", [str(m) for m in matches])
        sys.exit(1)

text = template_path.read_text(encoding="utf-8")
backup = template_path.with_suffix(".py.backup_button_cleanup")
shutil.copy2(template_path, backup)

old_css = """.scene-tools{position:absolute;top:10px;right:10px;z-index:5;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:40%}.scene-tool-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:12px;border:1px solid rgba(255,255,255,.1);background:rgba(8,15,25,.82);color:var(--text);text-decoration:none;cursor:pointer;backdrop-filter:blur(10px)}.scene-tool-btn:hover{background:rgba(20,30,44,.92)}.scene-tool-btn.active{background:rgba(174,241,134,.16);border-color:rgba(174,241,134,.36);box-shadow:0 0 0 1px rgba(174,241,134,.10) inset}"""
new_css = """.command-tools{margin-top:8px;display:flex;flex-direction:column;align-items:center;gap:7px}.command-tools-row{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}.command-tool-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:8px 10px;border-radius:12px;border:1px solid rgba(255,255,255,.10);background:rgba(8,15,25,.82);color:var(--text);text-decoration:none;cursor:pointer;backdrop-filter:blur(10px)}.command-tool-btn:hover{background:rgba(20,30,44,.92)}.command-tool-btn.active{background:rgba(174,241,134,.16);border-color:rgba(174,241,134,.36);box-shadow:0 0 0 1px rgba(174,241,134,.10) inset}.scene-tools{position:absolute;top:10px;right:10px;z-index:5;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:34%}.scene-tool-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:12px;border:1px solid rgba(255,255,255,.1);background:rgba(8,15,25,.82);color:var(--text);text-decoration:none;cursor:pointer;backdrop-filter:blur(10px)}.scene-tool-btn:hover{background:rgba(20,30,44,.92)}.scene-tool-btn.active{background:rgba(174,241,134,.16);border-color:rgba(174,241,134,.36);box-shadow:0 0 0 1px rgba(174,241,134,.10) inset}"""

old_topbar = """<div style="margin-top:8px">
  <button id="saveViewHelpBtn" class="mode-btn" type="button">How to Save View</button>
</div>"""
new_topbar = """<div class="command-tools">
  <button id="saveViewHelpBtn" class="mode-btn" type="button">How to Save View</button>
  <div class="command-tools-row" aria-label="Viewer utility controls">
    <button id="resetViewBtn" class="command-tool-btn" type="button">Reset View</button>
    <button id="downloadSummaryBtn" class="command-tool-btn" type="button">Download Summary</button>
    <button id="invisibleApproachBtn" class="command-tool-btn" type="button">Invisible Approach</button>
  </div>
</div>"""

old_scene = """</select>
</div><a class="scene-tool-btn" href="/">Back to Box / Launch</a><button id="resetViewBtn" class="scene-tool-btn" type="button">Reset View</button><button id="downloadSummaryBtn" class="scene-tool-btn" type="button">Download Summary</button><button id="invisibleApproachBtn" class="scene-tool-btn" type="button">Invisible Approach</button></div><div id="viewer"></div>"""
new_scene = """</select>
</div><a class="scene-tool-btn" href="/">Back to Box / Launch</a></div><div id="viewer"></div>"""

for label, old, new in [
    ("CSS scene-tools block", old_css, new_css),
    ("topbar save controls", old_topbar, new_topbar),
    ("scene floating utility buttons", old_scene, new_scene),
]:
    if old not in text:
        print(f"FAILED: could not find {label}.")
        print(f"Backup left at: {backup}")
        sys.exit(1)
    text = text.replace(old, new, 1)

template_path.write_text(text, encoding="utf-8")
print("OK: patched", template_path)
print("Backup:", backup)
print("Next: restart server, delete runs if needed, and generate a fresh terrain run.")
