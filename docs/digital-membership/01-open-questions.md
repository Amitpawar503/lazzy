# Open Questions & Decisions To Close

These are the questions that must be answered before or during build. They are grouped as:

- **[P0]** blocks build / a wrong default causes an at-the-gate incident
- **[P1]** needed before launch, has a safe interim default
- **[P2]** polish / can follow

Where the PRD and the meeting **disagree**, that is called out explicitly — those are the
dangerous ones, because the PRD reads as "decided" when it is not.

---

## A. QR token & refresh

### Q1 [P0] — What is the QR TTL: 5 or 10 minutes? (PRD ↔ meeting conflict)
- **PRD:** 5-minute TTL, stated as fact in §4, FR11, FR26, AC.
- **Meeting:** Deepanshi explicitly asked "2 min / 10 min?"; Tushar repeatedly said **10-minute window**. Left as "ask the Dev."
- **Impact:** TTL is the single knob that trades screenshot-replay safety (shorter = safer) against gate UX / re-scan friction (longer = smoother). It's baked into token issuance, refresh, and staff messaging.
- **Recommendation:** **TTL = 5 min** as the PRD says (safer, and staff can ask for a refresh in seconds). Make it **server-config per environment**, not a client constant, so we can tune it during pilot without an app release. Whatever we pick, one value across app + backend + staff copy.

### Q2 [P0] — Is refresh throttled, and how? (meeting left open)
- **Meeting:** Deepanshi asked whether there's a **max number of refreshes in the window** and a **cooldown after a refresh** ("ek baar refresh karne ke baad 10 min wait?"). Tushar: "the try is the limit … but count the limit … ask the Dev." Never resolved.
- **Recommendation:**
  - Auto-refresh is unnecessary — **refresh on demand only** (button), plus an automatic re-issue when the card is opened and the current token has expired.
  - Apply a light **rate limit**: e.g. max 1 refresh / 5s (debounce, kills double-taps) and max ~20 refreshes / 10 min per customer (abuse guard), enforced server-side. No hard "one refresh then wait 10 min" lock — that would strand a customer whose QR expired at the gate.
  - Values are config, not code.

### Q3 [P1] — What does the QR actually encode — mobile number, or an opaque ref?
- **Meeting:** Tushar floated "QR code = mobile number + X" and separately "QR = deep link URL." PRD says "bound to RTN/customer ID."
- **Security concern:** a raw MSISDN in a QR is PII leaking onto a screen a stranger scans, and it's guessable/enumerable.
- **Recommendation:** QR encodes a **signed opaque token** whose subject is an **internal customer reference** (or a per-issue random `jti` that resolves to the customer server-side), **never the raw mobile number**. See LLD §Token.

### Q4 [P2] — Is the QR a functional deep link or an opaque string?
- **Meeting:** deep-link idea was discussed and then dropped ("don't want external apps in the chain … staff microsite captures the QR string and posts to backend").
- **Recommendation:** **Opaque string** (not a URL). The staff microsite's scanner reads the string and POSTs it; nothing should "open" when a random camera app scans it. Confirmed direction.

---

## B. Customer app surfaces

### Q5 [P0] — iOS screenshot: "blocked" is not achievable. What's the accepted stance? (PRD ↔ platform reality)
- **PRD:** FR13 / AC: "Screenshot must be blocked on the QR screen on **both** Android and iOS."
- **Reality (and the meeting knew this):** Android can hard-block via `FLAG_SECURE`. **iOS cannot block screenshots** — the OS only lets you *detect* one after the fact (`userDidTakeScreenshot`) or blank content during backgrounding. Tushar: "screenshot restricted on the black screen … I don't think so [we can fully block on iOS]."
- **Recommendation:** Reframe FR13 to **defense-in-depth, not prevention**:
  - Android: `FLAG_SECURE` (true block).
  - iOS: detect screenshot → toast "For your security, refresh the QR before showing it"; obscure QR in app-switcher snapshot.
  - **Primary control is the TTL + single-active token + server-side single redemption**, exactly as the AC already admits ("the 5-minute QR TTL compensates"). Get product to sign off that iOS is "restricted/mitigated," not "blocked."

### Q6 [P1] — App-icon switching platform constraints — is the UX acceptable?
- **iOS:** alternate icons (`setAlternateIconName`) work without reinstall **but always trigger a system alert** ("You have changed the icon…"). Unavoidable.
- **Android:** done via `activity-alias` enable/disable — can cause a **launcher re-draw / the app icon briefly disappearing**, and behavior varies by OEM launcher; the app may be force-relaunched.
- **Recommendation:** Confirm product accepts (a) the iOS system prompt and (b) OEM-dependent Android behavior. Trigger the switch on a **cold start after eligibility sync**, not mid-session. Ship behind a flag; pilot on a device matrix first.

### Q7 [P1] — Launch-count for the hamburger animation: device-local or server-backed?
- **PRD:** show animation "until first click **or** 5 launches, whichever is **later**." NFR asks for consistency across reinstall "where feasible."
- **Tension:** "whichever is later" means the animation persists **at least 5 launches even if clicked earlier** — confirm that's intended (it's an unusual choice; usually "whichever comes first"). **This looks like a wording bug in the PRD — flag it.**
- **Recommendation:** Track `hamburgerSeenClicked` + `launchCount` **locally** for v1 (simple, no cold-start dependency). Mirror a `walkthroughState`/`gtmState` flag **server-side** so reinstalls don't replay it. Resolve the "later vs first" wording with product before build.

### Q8 [P1] — Eligibility: source of truth, sync cadence, and cold-start budget?
- Which system is authoritative for "active Postpaid **and** Fastlane/Advantage Club member"? What's the sync trigger (login + periodic — what period)? NFR says icon/splash eligibility "must not add perceptible delay to cold start."
- **Recommendation:** Eligibility resolved by an **existing profile/entitlement service**, cached locally with a short TTL; icon/splash read the **cached** flag at cold start (never a blocking network call). Re-evaluate on login and on a periodic background sync (propose 24h) and on push if churn/downgrade events exist. Fail **closed to Default** (non-branded) if the flag is stale/unreachable (NFR reliability).

### Q9 [P2] — Walkthrough trigger definition
- "First app open after feature go-live" — tie to **app version + feature flag**, not just "first open," so users who had the app before go-live still see it once. Persist dismissal server-side (see Q7).

---

## C. Staff microsite, auth & sessions

### Q10 [P0] — OTP policy specifics
- **PRD:** FR20 "in line with Airtel app login OTP." That's a pointer, not a spec.
- **Need concrete:** OTP length, validity (propose 5 min), max verify attempts (propose 5 then lock), resend cooldown (propose 30s) + daily cap, and **generic failure messaging** (never reveal whether a number is whitelisted — see Q11).
- **Recommendation:** Reuse the Airtel app's OTP provider/config values verbatim; document the resolved numbers here once confirmed.

### Q11 [P0] — Non-whitelisted (event, mobile): confirm "no OTP initiated" + generic error
- **PRD/AC:** for a non-whitelisted pair, **no OTP is initiated**; a number whitelisted for Event A must not get an OTP for Event B.
- **Loophole if messaging leaks:** distinct errors let an attacker enumerate valid staff numbers/events.
- **Recommendation:** Confirm the response is a **single generic** "If this number is authorized for this event, an OTP has been sent" regardless of whitelist status. (Design already assumes this — needs product sign-off on copy.)

### Q12 [P1] — "One active session per mobile number" vs. staff wanting two devices
- **PRD:** FR21 — a new login **revokes** the prior session (prior session gets `STAFF_SESSION_INVALID`).
- **Operational risk:** a staffer who opens a second tab/phone silently kills their working scanner; at a busy gate this reads as a bug.
- **Recommendation:** Keep single-active (it's a genuine anti-sharing control) but (a) show a clear "you were signed out because this number logged in elsewhere" screen, and (b) decide whether high-throughput gates should instead **whitelist multiple numbers** (one per device) rather than share one. Confirm with Growth/ops.

### Q13 [P1] — Session TTL 24h vs multi-day events
- FR22: 24h session TTL. Multi-day events → daily re-login. Acceptable? Probably yes (also a security refresh). Confirm; optionally make TTL = event window, capped.

### Q14 [P1] — What identity/PII does the staff screen show on a decision?
- **Meeting:** Tushar floated the backend returning "name with the QR" so staff can eyeball the holder. PRD NFR: "must not expose raw customer PII beyond what's needed for on-ground verification."
- **Recommendation:** On `ENTRY_ALLOWED` / `ALREADY_USED` / `NOT_ENTITLED`, show **masked** identity only (e.g. first name + `••••• 3210`) so staff can sanity-check the holder without the screen becoming a PII harvester. Get privacy/legal sign-off on exactly which fields.

### Q15 [P2] — Staff whitelist & winner-list loading: tooling & format
- PRD: engineering-team-only (no UI). Need: file format (CSV columns: `eventId, msisdn, checkpoints[]` for staff; `eventId, customerRef` for winners), upload mechanism (secured internal admin API / runbook), validation, and **late additions during an event** (must be supported — winners get added last-minute in practice).
- **Recommendation:** Secured internal admin API + idempotent bulk upsert; support mid-event appends; log every load with actor + count.

---

## D. Entitlement & event semantics

### Q16 [P1] — Checkpoint independence & ordering
- **PRD:** ENTRY and GOODIE are **independent** per entitlement; GOODIE can be claimed even if ENTRY wasn't scanned, and vice versa. **Confirm** this is desired (meeting supports it: "goodies … it's a different action"). If GOODIE should *require* prior ENTRY, that's a different rule — flag now.

### Q17 [P1] — Same customer, multiple concurrent events
- **Meeting:** confirmed entitlements are **per event/campaign** (`C1` has its own DB entries); winning Event A grants nothing at Event B; a customer holding entitlements for two same-day events is admitted at each. Design handles this natively (entitlement keyed by event). **Confirm no "one event per day per customer" global rule** is wanted.

### Q18 [P2] — Multiple entitlements / multi-admit within one event
- Is an entitlement always "1 admission + 1 goodie," or can a winner have a quantity (e.g. +1 guest)? PRD implies exactly one per checkpoint. Confirm; if guests are ever needed, model entitlement with a **count**, not a boolean, from day one.

---

## E. Reliability & ops

### Q19 [P0] — Offline / degraded connectivity behavior
- **PRD:** connectivity is "guaranteed by Growth Team"; `SERVICE_UNAVAILABLE` must **never auto-allow**; entitlement must **not** be marked used from the client; on-ground Airtel staff take the final manual call.
- **Recommendation:** No offline-allow mode (a queued/optimistic allow would break the exactly-once guarantee). Confirm the **manual-override runbook**: who decides, how it's recorded, and whether a manual admit is later reconciled in the audit log.

### Q20 [P1] — Idempotency retention window for `scanRequestId`
- Retried request with same `scanRequestId` must return the **original** result (AC). Need a retention window (propose ≥ event duration, e.g. 72h) and confirm the scanner **reuses the same** `scanRequestId` on retry (not a fresh one) — this is a scanner contract, not just backend.

### Q21 [P2] — Rate limiting on scan & OTP endpoints; dispute-API auth
- Confirm rate limits (per session, per IP) on scan/OTP. For the scan-history dispute API (FR35): who may call it, authN/authZ, and what PII it returns / how it's logged.

---

## Summary of PRD statements that are actually still open
These read as "decided" in the PRD but were left open (or are platform-infeasible) in the meeting/reality — resolve explicitly before quoting them as committed:

| PRD says | Reality |
|----------|---------|
| QR TTL = 5 min (FR11) | Meeting kept debating 5 vs 10 + refresh throttle (Q1, Q2) |
| Screenshot **blocked** on iOS (FR13) | iOS can only **detect**, not block (Q5) |
| Icon switch with no user friction (FR1) | iOS forces a system alert; Android launcher quirks (Q6) |
| Hamburger: click **or** 5 launches, "whichever **later**" (FR4) | Likely means "whichever **first**"; confirm wording (Q7) |
| OTP "in line with app" (FR20) | No concrete values yet (Q10) |
