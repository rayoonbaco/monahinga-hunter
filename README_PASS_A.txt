MONAHINGA PASS A - BACKEND-ONLY SPECIES TUNING

Files included:
- engine/species_profiles.py
- engine/decision/build.py

Purpose:
Adds optional selected_species support to the decision engine only.

Safety rule:
No Page 1 dropdown is added in this pass.
No Page 2 UI is changed in this pass.
No terrain rendering, bbox, startup script, monetization, or template files are touched.

Default behavior:
If selected_species is missing or set to general_terrain_read, scoring remains the normal terrain-first read.

Test:
Run the normal Monahinga start script and verify the app still works with no visible UI change.
