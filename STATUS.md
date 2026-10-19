# Status

Last updated: 2026-10-19

## Done (verified in this repo)

- [x] Flask server with `/`, `/redirect`, `POST /api/sessions`, `POST /api/webhooks/notifications`, `GET /api/webhooks/received`, `/healthz`
- [x] `/sessions` request builder with validation (minor units, generated reference)
- [x] HMAC verification matching Adyen's published example (`coqCmt/IZ4E3CzPvMY8zTjQVL5hYJUiBRg8UU+iCWo0=`) and cross-checked against an independent stdlib computation
- [x] Drop-in v6 from the CDN (6.46.0), Sessions flow, `onPaymentCompleted` / `onPaymentFailed` / `onError`
- [x] Redirect landing page using `submitDetails({ details: { redirectResult } })`
- [x] 15 passing tests (`python -m pytest -q`)
- [x] Server boots and serves the checkout page without credentials (session creation fails loudly with the missing variable named)

## Not yet done (needs a live Adyen test account)

- [ ] One real test-card payment through Drop-in with `resultCode: Authorised`
- [ ] A real AUTHORISATION webhook received through a tunnel and accepted by the HMAC check
- [ ] A redirect method (iDEAL) round trip through `/redirect`
- [ ] Screenshots of the above in the README
- [ ] Refund flow and idempotent webhook handling (dedupe by `pspReference` + `eventCode`)
- [ ] Fill the "Live run" section of FRICTION_LOG.md
- [ ] Push to a public GitHub repo
