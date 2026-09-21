# Postpaid Advantage Club — Digital Membership & Event Access

Engineering design notes for the **Postpaid Advantage Club — Digital Membership, Fastlane Branding & Exclusive Access** initiative.

These documents translate the PRD, the Figma flows, and the review meeting into a buildable design, and — more importantly — surface the decisions that were *not* closed in the PRD so we don't discover them at the gate.

| Doc | What it covers |
|-----|----------------|
| [`01-open-questions.md`](./01-open-questions.md) | Every open decision, including the ones the PRD states as settled but the meeting left open (TTL, refresh throttle, iOS screenshot, PII-to-staff, etc.). Each with a recommendation. |
| [`02-loopholes-and-mitigations.md`](./02-loopholes-and-mitigations.md) | The abuse/failure surface (screenshot replay, shared QR, concurrent double-scan, forged QR, retries, staff account sharing, offline) and how the design closes each. |
| [`03-hld.md`](./03-hld.md) | High-level design: components, boundaries, the core "identity-QR + session-bound event" model, and the main sequence flows. |
| [`04-lld.md`](./04-lld.md) | Low-level design: token schema, data model, API contracts, the atomic-redemption + idempotency mechanics, callback matrix, and the validation state machine. |

## The one idea the whole design rests on

> **The Membership QR is a customer *identity* credential, not an event ticket.**
> It carries **who** (customer), never **which event**. The event and the checkpoint come
> from the **authenticated staff session**, and entitlement is resolved **server-side at scan
> time** against that session's event.

This is exactly what Tushar landed on in the meeting ("*we will generate it for all postpaid
customers … basis that Ankur resolve … customer is particular event ABC eligible*"). It is why a
single, always-available QR can serve every event, every online activity, and goodie
distribution without the app ever knowing about events.

## Scope split

- **Customer side** — inside the Airtel Thanks app (native iOS/Android): app icon, hamburger animation, membership tile, QR card, splash, walkthrough.
- **Staff side** — a **standalone microsite** (e.g. `airtel-events.example`), *not* inside the Airtel app, used by on-ground staff on their own phone browsers.
- **Backend** — the QR/token service, the validation & entitlement service, and the admin/setup + audit surface used by the engineering team.
