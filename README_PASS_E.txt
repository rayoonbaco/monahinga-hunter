MONAHINGA™ PASS E — SPECIES PROFILE LANGUAGE UPGRADE

Replace:
engine\species_profiles.py

What changed:
- Species behavior hooks are more hunter-readable and distinct.
- No scoring keys were changed.
- No API changes.
- No terrain viewer changes.
- No bbox or launch-flow changes.

Safe test:
1. Restart Monahinga.
2. Choose Elk, Turkey, or Whitetail.
3. Run a box.
4. Confirm the app still loads and Analysis Mode still shows the selected species.

Rollback:
Restore the previous engine\species_profiles.py.
