# Loopholes, Abuse Cases & How the Flow Manages Them

This is the threat/failure surface for the QR + gate flow, and how the design closes each hole.
Much of this maps directly to the meeting's worries (screenshot sharing, duplicate entry,
timestamp reuse, "photo leaking").

Each row: **the hole → what stops it → residual risk**.

Legend for controls (defined once, referenced throughout):
- **C1 — Short TTL:** token valid ~5 min from issue (server clock authoritative).
- **C2 — Single-active token:** only the *latest* issued token per customer is accepted; issuing/refreshing a QR supersedes all previous ones.
- **C3 — Signature:** token is signed by the backend; the signing key never leaves the server, so tokens can't be forged or edited.
- **C4 — Atomic single redemption:** redemption is a single conditional DB write, unique per `(event_id, msisdn, checkpoint)`; concurrent scans → exactly one winner.
- **C5 — Idempotency key:** `scanRequestId` makes a retried scan return the *original* result, never a second redemption.
- **C6 — Server-only decision:** only the backend admits; the client/UI can never manufacture an allow; redemption is committed *before* `ENTRY_ALLOWED` is returned.
- **C7 — Agent session binding:** scans carry a server-side agent session → the event, checkpoint, and agent identity are derived server-side, never trusted from the client.
- **C8 — FLAG_SECURE / screenshot mitigation:** Android blocks screenshots; iOS detects + obscures.
- **C9 — App login + agent whitelist + single-active session:** the agent scans inside the Thanks App, so their MSISDN is proven by app login; the **User Profile Service whitelist** then grants scanning authority for specific events + checkpoints; single active agent session per number. No OTP, no microsite (see Q10).

---

## 1. Screenshot / photo of the QR is shared and reused later
*The meeting's #1 concern ("photo leaking … screenshot … duplicate customer").*

- **Stops it:** **C1** (a shared screenshot is dead within ~5 min) + **C2** (the moment the real customer opens/refreshes their card, the screenshotted token is superseded) + **C4/C6** (even a *live* copy can be redeemed only once per checkpoint, server-side) + **C8** (Android can't even take the shot).
- **Residual risk:** iOS screenshot within the live 5-min window, at the *same* checkpoint, *before* the real customer scans → see #2.

## 2. Two people present the same *live* QR at the same checkpoint (real + impostor within TTL)
- **Stops it:** **C4** — the first scan redeems `(event, msisdn, ENTRY)`; the second returns **`DUPLICATE_ENTRY`** (same deviceId) or **`ALREADY_ENTERED_OTHER_DEVICE`** (different deviceId) with the first-claim timestamp. Only **one** admission happens. This is the exact "duplicate customer, first scan allowed" behavior Tushar described.
- **Residual risk:** if the **impostor scans first**, the real customer is the one who gets the already-claimed result. The system prevents *double* entry but not *wrong-person* entry within a live window.
  - **Mitigations:** (a) staff see a **masked holder identity** on the result (Q14) to eyeball the person; (b) the already-claimed result shows first-claim time (and, for a different device, the first `deviceId`) so a wronged genuine customer is a clean dispute (scan-history API, FR35); (c) short TTL shrinks the window. Accept as a known residual — true elimination needs live customer↔device binding, which is out of scope.

## 3. Concurrent double-scan on two gates/devices (race condition)
- **Stops it:** **C4** implemented as an atomic conditional write / unique constraint on `(event_id, msisdn, checkpoint)` (see LLD). Two simultaneous claims → exactly one wins (`ENTRY_ALLOWED`), the other reads the existing row (`DUPLICATE_ENTRY` / `ALREADY_ENTERED_OTHER_DEVICE`). No lost update, no double admit. Directly satisfies FR25.

## 4. Network timeout → staff retries → customer redeemed twice
- **Stops it:** **C5** — the scanner sends a stable `scanRequestId`; the backend stores result keyed by it and **replays the original decision** on retry. A timeout after the DB committed → retry returns the same `ENTRY_ALLOWED` (not a second redemption); a timeout before commit → retry proceeds normally. Satisfies the AC "retried request with same `scanRequestId` returns the original result."
- **Contract:** scanner MUST reuse the same `scanRequestId` for a genuine retry (Q20).

## 5. Forged / edited / non-Airtel QR
- **Stops it:** **C3** — signature verification fails → **`INVALID_QR`**. A tampered token (changed subject, extended timestamp) breaks the signature. Distinguished from `NOT_ENTITLED` so staff message differs (fake vs. legit-but-not-a-winner).

## 6. Replay of an old but genuine token
- **Stops it:** **C1** (past TTL → `QR_EXPIRED`, refresh & re-present) + **C2** (superseded by any newer issue). The customer's own refresh is the "reset the window" behavior from the meeting.

## 7. Cross-event reuse (win Event A, try to get into Event B)
- **Stops it:** the QR carries **only the events the customer has actually won** (`token.events`, from the contest tables, inside the signature); the event being scanned comes from the staff **session**. If `session.eventId ∉ token.events` → **`NOT_ENTITLED`**. A win at Event A never puts Event B in the token. Satisfies FR31.

## 8. Client tampering — faking `ENTRY_ALLOWED` in the scanner UI
- **Stops it:** **C6** — the decision and the redemption are server-side; the UI only renders what the backend returned. Staff are trained: a green screen is meaningless unless it's the server's response (and the redemption is already committed when it's returned). No client state, callback, or DOM edit can admit anyone or flip entitlement status. Satisfies FR27.

## 9. Unauthorized person accesses the scanner / agent account sharing
- **Stops it:** **C9** — agent mode opens only inside the Thanks App for a **logged-in MSISDN that is whitelisted** for the event; a non-whitelisted agent gets a generic "not an event agent" with no event data (Q11). Single active agent session per number (FR21) limits sharing; a fresh session elsewhere invalidates the old one (`STAFF_SESSION_INVALID`).
- **Residual:** a whitelisted agent could still hand their unlocked phone to someone. Bounded by session TTL (Q13), audit trail (every scan carries the agent MSISDN), and checkpoint-scoping. Because identity is proven by app login, a *leaked number alone* is **not** enough — a real improvement over the earlier microsite plan.

## 10. Scanning the wrong checkpoint / claiming goodie as entry
- **Stops it:** **C7** — checkpoint is bound to the agent session and sent on every scan; redemption is tracked **per checkpoint**. An agent only sees ingresses they're whitelisted for (ENTRY / GOODIE / both). ENTRY and GOODIE are independent single-redemptions, so one QR = one entry **and** one goodie, never two entries. Satisfies FR28–FR29.

## 11. MITM / replayed scan API calls
- **Stops it:** TLS everywhere + **C7** (agent session, not client-supplied identity) + **C1** (short token life) + **C5** (idempotency dedups replays) + **server-authoritative timestamp** (client time is ignored for TTL — closes clock-skew and client-clock-tampering).

## 12. Agent-access abuse (enumeration / session spam)
- **Stops it:** **C9** — only a logged-in, whitelisted MSISDN opens agent mode; non-whitelisted attempts get a generic "not an event agent" (no enumeration) + per-IP/per-number rate limits. A leaked whitelisted number cannot by itself open a session, since app login proves identity (Q10).

## 13. Contest-winner list not loaded (or partially loaded) at event start
- **Stops it:** **default-deny** — no `contest_winner` row ⇒ the event isn't in `token.events` ⇒ `NOT_ENTITLED`. The system fails safe (no accidental admits), never fails open. Ops mitigations: a pre-event **readiness check** (list loaded? counts match?) and support for **mid-event appends**, which customers pick up on their next QR refresh (Q15).

## 14. Backend down / venue connectivity drops at the gate
- **Stops it:** `SERVICE_UNAVAILABLE` — **never auto-allow**, entitlement **not** marked used from the client, staff retries; final call is a **manual, recorded** on-ground Airtel decision (Q19). We never trade the exactly-once guarantee for uptime.

## 15. Token / customer enumeration or PII leakage via the QR
- **Stops it:** **C3** + opaque subject (no raw MSISDN in the token, Q3) + short TTL. Staff-facing screens show only **masked** identity (Q14). Dispute API is access-controlled and audited (Q21).

---

## Coverage → PRD acceptance criteria

| PRD acceptance criterion | Control(s) |
|---|---|
| Non-winner → `NOT_ENTITLED`, not `INVALID_QR` | `session.eventId ∉ token.events` (contest tables) |
| One event's win not admissible at another | token carries only won events + C7 session |
| First scan `ENTRY_ALLOWED` + atomic mark; subsequent duplicate/other-device | C4, C6 |
| Entry-redeemed QR still valid for first Goodie scan | per-checkpoint C4 |
| Two devices, same QR, simultaneously → exactly one admission | C4 |
| Expired → `QR_EXPIRED`, works after refresh; forged → `INVALID_QR` | C1, C2, C3 |
| Technical failure → `SERVICE_UNAVAILABLE`, never auto-allow | C6, Q19 |
| Same `scanRequestId` retried → original result, no 2nd admit | C5 |
| Only whitelisted `(event, MSISDN)` opens a session; new login kills old session | C9 |
| Every scan logged; history API returns full chronological trail | audit log (LLD) |
