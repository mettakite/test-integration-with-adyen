# Status

Last updated: 2026-10-19 (first live Authorised)

## Done (verified in this repo)

- [x] Flask server with `/`, `/redirect`, `POST /api/sessions`, `POST /api/webhooks/notifications`, `GET /api/webhooks/received`, `/healthz`
- [x] `/sessions` request builder with validation (minor units, generated reference)
- [x] HMAC verification matching Adyen's published example (`coqCmt/IZ4E3CzPvMY8zTjQVL5hYJUiBRg8UU+iCWo0=`) and cross-checked against an independent stdlib computation
- [x] Drop-in v6 from the CDN (6.46.0), Sessions flow, `onPaymentCompleted` / `onPaymentFailed` / `onError`
- [x] Redirect landing page using `submitDetails({ details: { redirectResult } })`
- [x] 16 passing tests (`python -m pytest -q`), including duplicate-delivery handling
- [x] Server boots and serves the checkout page without credentials (session creation fails loudly with the missing variable named)

## Not yet done

- [x] One real test-card payment through Drop-in with `resultCode: Authorised` (2026-10-19, session CS9AB81C4BA110B7B2C751235, merchant account MettakiteECOM, Drop-in 6.46.0 from CDN)
- [x] A real AUTHORISATION webhook received through a cloudflared tunnel and accepted by the HMAC check (2026-10-19, pspReference AKI0AHI5EKPYCFA2 from Customer Area's Test configuration)
- [ ] A redirect method (iDEAL) round trip through `/redirect`
- [x] Authorised screenshot in the README (`docs/authorised.png`)
- [ ] Webhook screenshot (`docs/webhook.png`) in the README
- [x] Idempotent webhook handling: duplicate deliveries of the same `pspReference` + `eventCode` are acknowledged with 200 but recorded once (found the hard way: five Test-configuration clicks produced five identical records)
- [ ] Refund flow
- [x] "Live run" section of FRICTION_LOG.md filled (findings L1 to L7)
- [ ] Push to a public GitHub repo
