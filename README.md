# Monahinga vNext

This build now turns the live provider foundation into the first real operator-visible command surface.

## What this version does

- runs the real Copernicus DEM fetch
- runs the real PAD-US legal-surface fetch
- builds a terrain derivative layer from the DEM
- builds a deterministic decision contract
- renders a visible command-surface page automatically
- removes Swagger from the normal workflow
- removes manual bbox entry from the normal workflow

## Standard Windows workflow

### First time only

1. Put the project folder on your Desktop.
2. Open the project folder.
3. Double-click `FIRST_TIME_SETUP.bat`
4. Wait for setup to finish.

### Normal use

1. Double-click `START_MONAHINGA_SERVER.bat`
2. Your browser should open automatically to:

`http://127.0.0.1:8010/`

3. Click:

**Run default Monahinga command surface**

That will run the default Chris Monahinga bbox automatically and open the generated command-surface page.

## Smoke test

1. Double-click `SMOKE_TEST_MONAHINGA.bat`
2. Wait for the result window.

## Default bbox

-78.102209, 41.891092, -78.074925, 41.909235

## What should now be visible

- a mountain representation from the real DEM
- legal land on top of that terrain
- one dominant primary sit
- multiple alternates
- visible near-misses that are suppressed
- dominant and secondary corridors
- a right-side ranked decision ladder

## Main outputs

Each run creates a folder under `runs\run_<id>\`

Important files:
- `terrain_truth\terrain\copernicus_dem.tif`
- `terrain_truth\terrain_derivatives\hillshade.png`
- `terrain_truth\legal\legal_surface.geojson`
- `terrain_truth\decision\decision_contract.json`
- `terrain_truth\terrain_contract.json`
- `command_surface\index.html`

## Command routes

- `/` = operator launch page
- `/run-default` = default-run authority
- `/health` = simple health check
- `/run-terrain-truth` = optional technical POST path if needed
