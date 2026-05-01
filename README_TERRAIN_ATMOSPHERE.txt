Monahinga Terrain Atmosphere Layer replacement package

This package replaces:
engine/command_surface/template.py

What changed:
- Adds a BBOX-driven terrain wallpaper layer behind the command surface.
- Uses the current run's terrain texture when available.
- Keeps the Three.js terrain viewer untouched.
- Uses existing region identity classes to shift the atmosphere for Appalachian, mountain/Rockies, plains, and southern timber boxes.

Install:
1. Back up your current template.py.
2. Unzip this package into your HUNTER project root.
3. Allow it to replace engine/command_surface/template.py.
4. Start with START_MONAHINGA_SERVER.bat.
