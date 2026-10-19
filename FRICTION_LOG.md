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

## Live run

To be filled after the first run against a test account. Capture: the first error returned by
`/sessions` with real credentials, how long from account creation to first `Authorised`, whether
the HMAC key from Customer Area worked first time, and anything the Customer Area UI made hard to find.

## What went well

- The Sessions flow really is two calls for the server (create session, receive webhook); the browser does the rest.
- `/sessions` error bodies include `errorCode` and a human-readable `message`, which is more than most payments APIs offer.
- The published HMAC test vector exists at all. Most providers make you discover the signing string by trial and error.
