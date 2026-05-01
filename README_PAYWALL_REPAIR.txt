Monahinga Paywall Repair - Right Rail Only

This repair restores the stable 3D command surface behavior by removing the blocking paywall modal/overlay behavior.
It keeps monetization visible in the right rail as a simple Stripe checkout offer.

Replace:
  engine\command_surface\render.py

Recommended backup first:
  copy engine\command_surface\render.py BACKUP_RENDER_BROKEN_PAYWALL_MODAL.py

Then start:
  START_MONAHINGA_SERVER.bat

Live Stripe link embedded:
  https://buy.stripe.com/8x2aEWb6f5qR7Td1mweEo00
