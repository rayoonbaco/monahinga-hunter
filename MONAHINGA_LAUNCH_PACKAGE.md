# Monahinga Version 1 Launch Package

## Positioning
Monahinga is AI-powered terrain intelligence for hunters. Version 1 is built to give hunters a clean first read on terrain, legal context, cover, wind fit, and stand options without replacing field judgment.

Core launch line:
> Version 1 — Built for hunters. Evolving with you.

Offer:
> 5 terrain intelligence views for $7

Feedback CTA:
> Help shape Monahinga. Tell us what features you want, how you would tweak the terrain analysis, and what makes a spot huntable to you.

## Instagram Reel Concept

### Hook, 0-3 seconds
Text on screen:
> Stop guessing what the terrain is telling you.

Voiceover:
> I built Monahinga for hunters who want a sharper terrain read before they burn a sit.

### Product reveal, 3-8 seconds
Show the launch page, draw a hunting box, and click Run selected box.

Text on screen:
> Draw a box. Run the terrain. Read the hunt.

Voiceover:
> Draw one hunting box and Monahinga turns it into legal-aware terrain intelligence, 3D terrain, cover context, wind read, and ranked stand options.

### Version 1 message, 8-15 seconds
Show Page 2 and the right-rail offer.

Text on screen:
> Version 1 is live.

Voiceover:
> This is Version 1. It is built for hunters, and it is going to evolve with real feedback from hunters who know what makes a spot huntable.

### Future tease, 15-23 seconds
Show terrain viewer movement, pins, and cover toggles.

Text on screen:
> Future: personalized hunting intelligence.

Voiceover:
> The next evolution is personal: weighting access routes, wind assumptions, pressure tolerance, movement assumptions, terrain preferences, and your own hunting style.

### CTA, 23-30 seconds
Show checkout/instructions/feedback link.

Text on screen:
> Early users shape the tool.

Voiceover:
> Unlock 5 terrain intelligence views for $7 and send feedback on how you think through terrain. Early users help shape Monahinga.

Caption:
> Monahinga Version 1 is live. Draw a box, run the terrain, and get a sharper hunting read. Future versions will move toward personalized hunting intelligence shaped by real hunter feedback. Early users help build the tool. 5 terrain intelligence views for $7.

Hashtags:
#Monahinga #DeerHunting #WhitetailHunting #PublicLandHunting #HuntingApp #TerrainIntelligence #Scouting #HuntSmarter #Bowhunting #TurkeyHunting

## GoDaddy Deployment Checklist

1. Confirm `.env` is present on the server and contains real production values only on the server.
2. Add one of these variables for checkout:
   - `MONAHINGA_STRIPE_PAYMENT_LINK=https://your-live-stripe-payment-link`
   - or `STRIPE_PAYMENT_LINK=https://your-live-stripe-payment-link`
3. Do not commit or upload Stripe secret keys into public code.
4. Confirm install dependencies:
   - `pip install -e .`
5. Start locally before deployment:
   - `python -m uvicorn main:app --host 127.0.0.1 --port 8000`
6. Test these URLs:
   - `/`
   - `/instructions`
   - `/checkout`
   - `/health`
   - `/run-default`
7. Confirm Page 2 opens from the run output and the 3D terrain viewer still loads.
8. Confirm offer copy says `5 terrain intelligence views for $7`.
9. Confirm the feedback email link opens a message template.
10. Only after local success, push/upload the same files to GoDaddy.

## Files Changed in This Pass

- `main.py`: added isolated `/instructions` and `/checkout` routes.
- `apps/api/main.py`: mirrored the same routes for API-platform deployment parity.
- `engine/launch_surface/home_page.py`: added premium Version 1 header line, instructions link, and checkout link without changing run logic.
- `engine/launch_surface/instructions_page.py`: new standalone instruction page with Version 1 and feedback messaging.
- `engine/launch_surface/__init__.py`: exported the new instruction renderer.
- `engine/command_surface/render.py`: updated right-rail offer copy to 5 views for $7 and made checkout URL environment-safe.
- `MONAHINGA_LAUNCH_PACKAGE.md`: this launch/reel/deployment checklist.

## Rollback Plan

If anything unexpected happens, restore these files from the previous zip:

- `main.py`
- `apps/api/main.py`
- `engine/launch_surface/home_page.py`
- `engine/launch_surface/__init__.py`
- `engine/command_surface/render.py`

Then delete:

- `engine/launch_surface/instructions_page.py`
- `MONAHINGA_LAUNCH_PACKAGE.md`

Page 2 terrain code was not changed in this pass.
