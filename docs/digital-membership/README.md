# Postpaid Advantage Club — Digital Membership & Event Access

Engineering design notes for the **Postpaid Advantage Club — Digital Membership, Fastlane Branding & Exclusive Access** initiative.

These documents translate the PRD, the Figma flows, and the review meeting into a buildable design, and — more importantly — surface the decisions that were *not* closed in the PRD so we don't discover them at the gate.

| Doc | What it covers |
|-----|----------------|
| [`01-open-questions.md`](./01-open-questions.md) | Every open decision, including the ones the PRD states as settled but the meeting left open (TTL, refresh throttle, iOS screenshot, PII-to-staff, etc.). Each with a recommendation. |
| [`02-loopholes-and-mitigations.md`](./02-loopholes-and-mitigations.md) | The abuse/failure surface (screenshot replay, shared QR, concurrent double-scan, forged QR, retries, staff account sharing, offline) and how the design closes each. |
| [`03-hld.md`](./03-hld.md) | High-level design: components, boundaries, the core "identity-QR + session-bound event" model, and the main sequence flows. |
| [`04-lld.md`](./04-lld.md) | Low-level design: token schema, data model, API contracts, the atomic-redemption + idempotency mechanics, callback matrix, and the validation state machine. |
| [`05-detailed-lld-eventpass.md`](./05-detailed-lld-eventpass.md) | Build-ready, code-level LLD matching the existing `contest` module conventions, with the reference implementation in [`reference-impl/eventpass/`](./reference-impl/eventpass) (atomic entry save + contest winner check). |

## The one idea the whole design rests on

> **The Membership QR is a customer *identity + won-events* credential, not an event ticket.**
> It carries **who** (customer + deviceId) and **which events they have won** — the winning
> `eventId`s are read from the **Contest Service** at generation and **signed into the token** by
> the **User Profile Service**, then shown in the Airtel Thanks App. The **checkpoint**
> (ENTRY / GOODIE) and the **event being scanned** come from the **agent's validated scanning
> session** (the agent scans *inside the same Thanks App*). Entry is allowed when
> `session.eventId ∈ token.wonEvents` **and** that `(customer, event, checkpoint)` hasn't already
> been redeemed.

This grows from what Tushar landed on in the meeting ("*we will generate it for all postpaid
customers … basis that Ankur resolve … customer is particular event ABC eligible*"). A single,
always-available QR serves every event the customer has won, plus goodie distribution, without the
app ever driving event logic. **Agents authenticate by their Thanks App login + the User Profile
Service whitelist (which events + checkpoints); no OTP, no microsite** — see Q10.

## Scope split

- **Customer side** — inside the Airtel Thanks app (native iOS/Android): app icon, hamburger animation, membership tile, QR card, splash, walkthrough.
- **Agent side** — **inside the same Airtel Thanks App**, in an *agent mode* unlocked only for MSISDNs whitelisted for an event. The agent scans customer QRs from the app — **there is no separate microsite**.
- **Backend** — the **User Profile Service** (eligibility, agent whitelist + session, and QR generation/signing), the **Contest Service** (winner source of truth), the **Entry Validation Service** (scan verification, redemption, audit), plus the admin/setup surface used by engineering.
