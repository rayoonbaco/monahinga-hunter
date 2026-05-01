MONAHINGA VERSION 1 CHECKOUT PACKAGE

Current launch offer:
- 5 terrain intelligence views for $7

What this build uses:
- Isolated /checkout route
- Right-rail Monahinga Launch Offer button on the 3D command surface
- Stripe Payment Link stored through environment configuration when available

Environment variable options:
- MONAHINGA_STRIPE_PAYMENT_LINK=https://your-live-stripe-payment-link
- STRIPE_PAYMENT_LINK=https://your-live-stripe-payment-link

Safety note:
Stripe secret keys must stay in .env or server environment variables. Do not paste secret keys into Python files, HTML, JavaScript, README files, or public repos.

Test:
1. Start the app.
2. Open /
3. Open /instructions
4. Open /checkout and confirm it redirects to Stripe.
5. Run a terrain view and confirm Page 2 still opens.
6. Confirm the right rail says: Unlock 5 terrain intelligence views for $7.
