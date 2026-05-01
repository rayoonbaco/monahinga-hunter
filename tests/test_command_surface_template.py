from engine.command_surface.template import HTML_TEMPLATE


def test_command_surface_template_has_safe_tier_color_helper():
    template_text = HTML_TEMPLATE.template
    assert "function tierColorValue(tier)" in template_text
    assert "function tierColor(tier) { return new THREE.Color(tierColorValue(tier)); }" in template_text
    assert ".getHexString" not in template_text


def test_command_surface_template_has_back_to_box_launch_button():
    assert "Back to Box / Launch" in HTML_TEMPLATE.template


def test_command_surface_template_has_selected_site_and_live_wind_hooks():
    template_text = HTML_TEMPLATE.template
    assert 'id="selectedSiteCoords"' in template_text
    assert 'id="copyCoordsBtn"' in template_text
    assert 'id="liveWindHudSummary"' in template_text
    assert 'function drawWindOverlay(read)' in template_text


def test_command_surface_template_has_terrain_first_texture_blend_hook():
    template_text = HTML_TEMPLATE.template
    assert "buildTerrainFirstTexture" in template_text
    assert "terrain:first" in template_text


def test_command_surface_template_has_sky_and_clarity_hooks():
    template_text = HTML_TEMPLATE.template
    assert "function createSkyTexture()" in template_text
    assert "scene.background = createSkyTexture()" in template_text
    assert "const horizonGlow = skyCtx.createRadialGradient" in template_text
    assert "const coverVariation = Math.sin" in template_text
    assert "const hazeLift = 4 + vegetation * 3;" in template_text