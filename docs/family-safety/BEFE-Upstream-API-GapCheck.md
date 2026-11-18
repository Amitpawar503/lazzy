# Upstream (BEFE / Guardian) API — Gap Check & Swagger

**Date:** 18 Nov 2026 · **Base path:** `/befe/fsc/v1` · **Layer:** App-facing orchestrator (upstream)
**Checked:** `FSC_BEFE_API_Requirements.md` (B01–B74) and `FSC_API_Documentation_-_Swagger_UI.txt` (downstream) **against** `Family-Safety-API-Binding-Leadership.pdf`.
**Deliverable:** `befe-upstream-swagger.html` (open in browser — Swagger UI, Try-it-out) · `befe-upstream-swagger.json` (import into Swagger/Postman).

---

## 1. What was checked

- **Binding (leadership PDF)** documents the orchestrator's **downstream** contract — how ~24 app-facing calls fan out to **Network** (`/fsc`) and **Whalebone**. It is a mapping doc, not an upstream API spec.
- **FSC swagger** is the **downstream** Network contract (`/fsc` family/member/trigger/device/alarm). It is *consumed* by the BEFE, not exposed to the app.
- **FSC_BEFE_API_Requirements** is the full **upstream** ask-list — 74 endpoints (B01–B74) across the 13 Figma pages — i.e. everything the app actually calls.

**Finding:** the binding covers the *core* upstream flows only. It is **missing the majority of the upstream surface** the app needs. None of those were wrong in the binding — they simply were never enumerated there. They are now all included in the upstream swagger.

## 2. Upstream APIs the binding already covered

Circle create/get, member list/add/status, safety-events (check-in / SOS / fraud create + action + list), protection (device/network safety) get/set, parental get/set, stats, device pairing. ~24 endpoints.

## 3. Upstream APIs that were MISSING — now added

| Area | Added upstream endpoints | B-ref |
|---|---|---|
| Eligibility & onboarding | `/eligibility`, `/onboarding/content`, `/how-it-works` | B01, B02, B67 |
| Subscription | offers, purchase, status, resume | B03–B05, B66 |
| Circle & home | circle create, bootstrap, **home aggregate**, refresh-signals | B06, B07, B19, B20 |
| Members & invites | candidates, validate, **full invite lifecycle** (send/list/resend/detail/respond + web), features catalog | B08–B16 |
| Permissions | permission status, ack | B17, B18 |
| Member page | member detail, member features get/set, safety-report, notify-back-online, advanced-feature request | B21–B25 |
| Check-ins | list, create, get, respond, dismiss, connected, **schedules** (get/create/update) | B26–B32 |
| SOS | create, active, get, respond, dissolve, location ping | B33–B38 |
| Fraud alerts | active list, warn, end-call | B39–B41 |
| Device safety | status, activate, deactivate, **SDK bootstrap**, scan, events | B43–B48 |
| Parental (full hub) | hub, activate, schedules, screen-time, apps, pause, requests (+decide), content-filter, places, usage, location | B49–B59 |
| Settings & roles | settings hub, roles, responders, remove, leave, close-preview | B60–B65 |
| Alerts & history | **alerts list** (active+history), alert detail, weekly report | B68–B70 |
| Signals & lifecycle | signals, subscribe-back-online, **lifecycle events** (port-out/SIM-swap/uninstall), consent reconfirm | B71–B74 |

## 4. The upstream swagger (`befe-upstream-swagger.json`)

- **Swagger 2.0**, host `guardian.airtel.com`, basePath `/befe/fsc/v1`.
- **77 paths · 86 operations · 99 models**, grouped into 14 tags (one per Figma domain).
- **Every operation has request + response with mandatory fields** — `required` arrays on request bodies (e.g. `familyId`, `initiatorMsisdn`, `action`), query params flagged `required: true` where mandatory (e.g. `msisdn` on eligibility, `familyId` on home/alerts), and response DTOs carry the standard envelope (`responseCode`, `responseMessage`, `transactionId`) as required.
- **Optimizations kept** (matching the binding's design principles): upsert-style saves, **enum-based action routing** (check-in `action` CREATE/RESPONSE/DISMISS/PAUSE/RESUME; SOS CREATE/ACKNOWLEDGE/RESOLVE), **resource-style query params**, method-correct DELETE semantics, and GET+PUT pairs on the same path for hub resources.

## 5. Notes / open items (unchanged from downstream reality)

- Routes under `/befe/fsc/v1` are **proposals** pending Guardian registration — final prefix is Channel's to assign.
- **GEOFENCE / INACTIVITY** alerts (B57 places, signals) have **no Network owner** today (gap G7 from the mapping) — BEFE exposes them upstream but the downstream source is TBD.
- History (B68) and lifecycle (B73) compose **Network events + Whalebone fraud + UCM titles** — same multi-source note as the FSC `history/fetch` work.
- BEFE is **stateless / consume-only** (no DP persist now), consistent with the ADR.

---

*Upstream swagger generated from the BEFE requirements; request/response and mandatory fields included per operation.*
