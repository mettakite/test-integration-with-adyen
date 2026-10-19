# Friction log: integrating with Adyen as a first-time developer

Kept while building this repo from the public docs, as a developer-experience exercise. Each entry is
something that cost time, with where it happened and what would have prevented it. Findings 1 to 8 come
from reading the docs and building against them without an account. The "Live run" section is for
what a real test-account run adds.

Scale: **High** = blocks progress or causes a wrong integration; **Medium** = costs 10+ minutes;
**Low** = papercut.

| # | Where | What happened | Impact | What would fix it |
| --- | --- | --- | --- | --- |
| 1 | Verify HMAC signatures page | The page lists the eight signed fields and says to join them with colons, but says nothing about escaping. Adyen's own libraries escape `\` and `:` inside values before joining. A developer following the page alone produces a verifier that silently fails on any `merchantReference` containing a colon. | High | One sentence and a two-line example on the docs page; link the library's `util.py` as the reference implementation. |
| 2 | Verify HMAC signatures page | The worked example shows the signing string and the expected signature but not the full `NotificationRequestItem` JSON it came from, so you cannot paste it into a test. The eight values have to be reassembled by hand. | Medium | Publish the example as a complete JSON item that can be copied into a unit test, next to the expected signature. |
| 3 | Sessions flow, Drop-in v6 | Three ways to load Drop-in (npm, CDN, self-hosted) and the v5 to v6 API change (`checkout.create('dropin')` vs. `new Dropin(checkout, {...})`) coexist in search results and sample repos. The official `adyen-components-js-sample-code` repo still shows v5. An agent or a developer copying the first result gets the wrong API. | High | Mark v5 samples as legacy at the top of the file; put the v6 CDN snippet, with the `integrity` attributes, on the Sessions flow page itself. |
| 4 | Drop-in v6, `paymentMethodComponents` | In v6 Drop-in renders nothing unless you pass the component classes you want (`Card`, `Ideal`, ...) in `paymentMethodComponents`. This is a breaking change from v5 and is easy to miss; the symptom is an empty container with no console error. | High | A console warning when `paymentMethodComponents` is empty; call out the requirement in the first v6 code sample. |
| 5 | `/sessions` request | `amount.value` is minor units, `countryCode` is required, and `returnUrl` is required even for card payments that never redirect. None of these produce a clear error if wrong: a bad country code returns a generic 422. | Medium | Field-level validation messages naming the field, and a "minimum viable request" block at the top of the reference with exactly the five required fields. |
| 6 | Webhook response | Older docs and forum answers say to respond with the string `[accepted]`; current docs say HTTP 200 is what matters. Both are still in circulation, so integrators cargo-cult the string. | Low | One line on the webhooks page: "Return HTTP 200. The `[accepted]` body is no longer required but is harmless." |
| 7 | Webhook retries | A webhook that fails HMAC should still get a 200 (otherwise Adyen retries a tampered item for days), but the docs frame HMAC failure as "reject the notification," which reads as "return an error." | Medium | State the retry behavior next to the HMAC guidance: drop the item, log it, return 200. |
| 8 | Test cards page | Test card numbers, expiry rules, and CVC are on a separate page from the integration guide, and the guide does not say which combination yields `Authorised` vs. `Refused`. The first payment attempt is a guess. | Low | Put one known-good card (4111 1111 1111 1111, any future date, CVC 737) inline in the Sessions guide's "Test it" step. |

## Live run (2026-10-19)

From test-account signup to the first `Authorised` took about two hours, and almost none of it was code.
In order:

| # | Where | What happened | Impact | What would fix it |
| --- | --- | --- | --- | --- |
| L1 | Test account signup | The form rejects free-mail domains ("Enter a valid business email address"). A developer evaluating the product on a personal account cannot get in without a custom domain. | High | Say so on the signup page before the form, or allow free-mail for test accounts with a lower limit. |
| L2 | Customer Area, finding the merchant account code | There is no field labeled "merchant account" anywhere a new user looks. The code (`MettakiteECOM`) is the heading of the credentials page and the entry in the account picker, but nothing calls it the value you put in `merchantAccount`. | Medium | A "Use this in `merchantAccount`" copy button next to the code on the API credentials page. |
| L3 | API credentials, generating a key | First `/sessions` call returned `401 Unauthorized, errorCode 000`. Cause: the generated key is not active until **Save changes** at the bottom of the page is clicked. The page gives no hint and the key is shown as if ready. | High | Disable copy until saved, or save on generate. At minimum, a banner: "Not active until you save." |
| L4 | API credentials, client key | Regenerating the API key also produced a new client key and retired the old one. Nothing says the two are paired. Drop-in then failed with a bare browser `NetworkError` on the `/setup` call, which looks like CORS or a network outage, not a dead key. | High | State on the page that the client key changes with the API key; have `/setup` return a 401 with `errorCode` instead of failing the preflight. |
| L5 | Client settings, allowed origins | The same `NetworkError` appears when the page origin is not in Allowed origins. Two different misconfigurations, one indistinguishable symptom, surfaced only as a failed fetch in the console. | High | Return a JSON error naming the origin; put "add `http://localhost:<port>` for local development" in the Sessions guide. |
| L6 | Drop-in v6 lifecycle | Between "session created" and the first callback there is silence. If `AdyenCheckout()` or `mount()` throws, nothing reaches the page unless the integrator wraps both in try/catch. The sample code does not. | Medium | Wrap both calls in the official samples and log to `onError`. |
| L7 | Tunnels for webhooks | The docs assume ngrok; ngrok now requires an account and auth token before it will open a tunnel. | Low | Mention `cloudflared tunnel --url` as the no-account alternative. |

What worked first time: the HMAC key from Customer Area is the hex string the docs describe, and the published
test vector matched our verifier before any live call. `/sessions` with correct credentials returned a usable
session on the first try. Drop-in 6.46.0 from the CDN rendered without a bundler.

## What went well

- The Sessions flow really is two calls for the server (create session, receive webhook); the browser does the rest.
- `/sessions` error bodies include `errorCode` and a human-readable `message`, which is more than most payments APIs offer.
- The published HMAC test vector exists at all. Most providers make you discover the signing string by trial and error.
