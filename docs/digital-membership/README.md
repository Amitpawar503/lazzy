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

> **The Membership QR is a customer *identity + won-events* credential, not an event ticket.**
> It carries **who** (customer + deviceId) and **which events they have won** — the winning
> `eventId`s are read from the **contest tables** at generation and **signed into the token**.
> The **checkpoint** (ENTRY / GOODIE) and the **event being scanned** come from the
> **authenticated staff session**. Entry is allowed when `session.eventId ∈ token.wonEvents`
> **and** that `(customer, event, checkpoint)` hasn't already been redeemed.

This grows from what Tushar landed on in the meeting ("*we will generate it for all postpaid
customers … basis that Ankur resolve … customer is particular event ABC eligible*"). A single,
always-available QR serves every event the customer has won, plus goodie distribution, without the
app ever driving event logic. **Staff auth is whitelist-only (MSISDN), no OTP** — see Q10 for the
accepted security tradeoff.

## Scope split

- **Customer side** — inside the Airtel Thanks app (native iOS/Android): app icon, hamburger animation, membership tile, QR card, splash, walkthrough.
- **Staff side** — a **standalone microsite** (e.g. `airtel-events.example`), *not* inside the Airtel app, used by on-ground staff on their own phone browsers.
- **Backend** — the User Profile service, the QR/token service, the Contest service (winner source of truth), the Validation & Entry service, and the admin/setup + audit surface used by the engineering team.
