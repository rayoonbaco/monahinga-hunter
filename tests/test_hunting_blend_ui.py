from pathlib import Path


def test_template_contains_hunting_read_and_focus_controls():
    text = Path("engine/command_surface/template.py").read_text(encoding="utf-8")
    assert "Back to Box / Launch" in text
    assert "Hunting Read" in text
    assert "data-focus-rank=\"1\"" in text
    assert "PAD-US glow follows the terrain" in text


def test_render_includes_hunting_read_markup_placeholder():
    text = Path("engine/command_surface/render.py").read_text(encoding="utf-8")
    assert "hunting_read_markup" in text
    assert "Legal coverage inside box" in text
    assert "Wind read" in text
