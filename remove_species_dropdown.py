import re
from pathlib import Path

file_path = Path("engine/command_surface/template.py")
text = file_path.read_text(encoding="utf-8")

# --- Remove <select id="viewer_species">...</select> block ---
text = re.sub(
    r"<select id=\"viewer_species\"[\s\S]*?</select>",
    "",
    text,
    flags=re.MULTILINE
)

# --- Remove any JS lines referencing viewer_species ---
text = re.sub(
    r".*viewer_species.*\n?",
    "",
    text
)

# --- Clean up excessive blank lines ---
text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

file_path.write_text(text, encoding="utf-8")

print("✅ viewer_species removed cleanly.")