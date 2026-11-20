# Family Safety — Data & Content needed from the Network team (for the frontend)

**Sources:** Safety Circle PRD (MVP) · FSC BEFE API Requirements (B01–B74) · Airtel Secure HLD (Whalebone) · FSC swagger v1.6-merged
**Date:** 20 Nov 2026 · **Scope:** what the **app frontend renders** that must be sourced from the **Network team**

## 0. Ownership boundary (who this doc is addressed to)

| Owns | Systems | In this doc? |
|---|---|---|
| **Network team** (this ask) | FSC circle domain, OTA engine (SOS / check-in / alarm), device telemetry (battery / ringer / network / location), **Safe Network** (spam / OTP / fraud + Safety Report), reachability / HLR, LBS, MNP / lifecycle events | **Yes — all sections** |
| Whalebone (partner) | Device Safety + Parental content-filter / app-rules / events | Only the **membership ↔ subscriptionID link** FSC must hold |
| Billing / CRM | Packs, eligibility, subscription status, grace/pause | Flagged where the FE needs it; **not a Network ask** |

**Status key:** ✅ exists in FSC swagger · 🟡 exists, must extend · 🔴 GAP (Network to build/share).

---

## 1. Family Dashboard — Home & Member cards (US 24, 27, 28)

Every member card and detail page renders live signals. **The FE needs, per member, from Network:**

| Data the FE shows | Field(s) | Status |
|---|---|---|
| Reachability state + reason | `reachabilityReason` = REACHABLE / SWITCHED_OFF / NO_COVERAGE / FLIGHT_MODE / INACTIVE_NUMBER | 🔴 reachability API |
| Last seen on network | `lastOnNetworkAt` (timestamp) | 🔴 |
| Battery | `batteryPercent` (current) + `lastBatteryLevel` (before going offline) | 🟡 typed device-status |
| Ringer (Android only) | `ringerMode` = NORMAL / VIBRATE / SILENT | 🟡 |
| Network | `networkType`, `networkStrength` | 🟡 |
| Per-signal freshness | `lastUpdatedOn` **per signal** (so the card can show "last updated 10:05") | ✅ (E8) |
| Feature health | `checkinWorking`, `sosWorking`, missing-permission flags per feature | 🔴 feature-health model |
| Latest check-in summary | one-line status (see §3) | 🟡 |
| Active alert (highest priority) | SOS > Fall > Safe Trip > Check-in > Fraud > Unreachability | 🔴 alert feed |

**Asks:** (1) typed device-status fetch returning battery / ringer / network / location / reachability **with `lastUpdatedOn` per property**; (2) **refresh semantics** — signals refresh within ~1–2 min when any member opens the page; (3) **flight-mode vs switched-off** — can Network tell them apart, or must the FE show "Switched off or in flight mode"?; (4) **iPhone availability list** — which signals are N/A on iOS (ringer, network strength, continuous battery).

---

## 2. SOS (US 15–17)

| Data the FE shows | Field(s) | Status |
|---|---|---|
| Create SOS (after client countdown) | `triggerId`, snapshot `location` (lat,long), `battery`, `networkStrength` | 🟡 extend trigger/sos/create |
| Live SOS state | `status` (Active/Resolved/Cancelled), `responders[]` (who is responding), `acknowledgementStatus` | 🟡 richer live DTO |
| Live location stream while active | periodic `location` pings | 🔴 location pings / stream |
| LBS fallback | network location when app location missing — **during SOS only** | 🔴 LBS lookup API |
| Phone offline during SOS | "last connected at `lastOnNetworkAt`" + last-known location | 🟡 |
| Dissolve / mistake / auto-24h | initiator-only cancel (`initiatorMsisdn`), auto-expire 24h | 🟡 clarify cancel vs kill |
| No-internet SOS | SMS short-code (e.g. "SOS" → 52263) registers SOS; no-network → native 112 dial | 🔴 short-code registration |

**Asks:** richer SOS live DTO (responders, ack, location-stream meta, battery); **LBS location API** for SOS; **SMS short-code SOS** registration path; clarify **`alarm/incoming` vs `trigger/sos`** payloads; confirm **who owns escalation** (IVR at 2 min, presidential + SMS, whole-circle at 5/7 min).

---

## 3. Safety Check-in (US 20–23)

| Data the FE shows | Field(s) | Status |
|---|---|---|
| Create (1+ targets) | `familyId`, `targets[]`, `message`, `scheduleType` | 🟡 extend multi-target |
| Reply | `checkinResponse` = I'M_OKAY / NEED_HELP + status text | 🟡 extend reply channel |
| Status on card | per target: Awaiting / Replied-okay / Need-help / Dismissed / Expired + timestamps | 🟡 |
| Schedules | days (MON–SUN), time (HH:mm), start/end date, pause/resume | 🟡 (folded in v1.6) |
| Rules the FE enforces with Network | one open per target, **≤3/day**, IVR at 15 min, expire 24h, **unreachable-at-send short-circuit** | 🟡 / 🔴 |
| "I've connected with her" ack (post need-help) | `connected` action | 🔴 connected-ack |

**Asks:** check-in **list** API, **schedules CRUD**, **daily-limit** + one-open enforcement, **need-help → connected** flow, and **IVR/SMS escalation** owner (messaging platform, orchestrated by FSC).

---

## 4. Fraud & Spam alerts — Safe Network (US 18–19)

The headline Airtel differentiator — **all from Network / Safe Network.**

| Data the FE shows | Field(s) | Status |
|---|---|---|
| Live alert triggers | spam-flagged incoming call ≥ 1 min; **bank OTP during spam call**; bank OTP during **unknown-number** call | 🔴 typed fraud feed |
| Alert data (responder view) | `memberMsisdn`, `alertType` = SPAM / OTP, **`callTimerSeconds`** (duration so far), **`otpCount`**, `callActive`, `status`, `riskLevel` | 🔴 (added in v1.6 fraud/alert/fetch) |
| **Never** exposed | caller's number — must not be in payload or history | — |
| Call-ended summary | "Call ended after 6 min · OTP received (count)" | 🔴 |
| Responder actions | **send warning** (flash / USSD, no reply needed), **call**, **remote end-call** (pending Legal) | 🔴 warn + end-call APIs |
| Safety Report | last **3 months** spam calls / spam SMS / fraud links — **admin/co-admin only**, works **without app** (network data) | 🟡 reuse + family-access auth |

**Asks:** typed **fraud alert feed** (SPAM / OTP, with call timer + OTP count, no caller number); **warn (flash/USSD)** API; **remote end-call** feasibility + legal; **Safety Report** family-access authorization (per-member, responders only, revoke on leave).

---

## 5. Alerts & History (US 29)

| Data the FE shows | Field(s) | Status |
|---|---|---|
| Consolidated history | types: SOS, CHECKIN, CHECKIN_NEED_HELP, FRAUD_SPAM, LOW_BATTERY, BACK_ONLINE, GEOFENCE, DEVICE_SAFETY, CIRCLE_EVENT, PARENTAL_REQUEST | 🟡 (history/fetch added) |
| Filters | by member (`msisdn`), `eventType`, date range (**7 or 30 days**) | 🟡 |
| Role-scoped visibility | fraud / low-battery → responders only; who-resolved/dismissed recorded | 🔴 role scoping |
| Retention | **7–30 days — confirm with Network/eng** | 🔴 decision |

**Asks:** unified **alert/history** list with **role-scoped filters** + agreed **retention** (7 vs 30). Note: FRAUD rows originate from Safe Network / Whalebone; titles (mom/dad) are mapped by Channel via UCM.

---

## 6. Reachability, lifecycle & number events (US 10, 11, 25, 26)

| Data the FE shows | Event / field | Status |
|---|---|---|
| Low-battery alert | battery ≤ 20% → responders; **once per discharge**; resets on charge | 🔴 eventing |
| Back-online | "Mom is back on network" after unreachable (works like today's back-on-network SMS, in-app) | 🔴 back-online subscription |
| Port-out | **start** (porting code requested — early warning) **and complete** | 🔴 MNP events |
| SIM-swap / new SIM same number | re-confirm prompt (SIM-swap guard) | 🔴 |
| Ownership change (Airtel only) | pause membership + re-consent | 🔴 |
| Number inactive / barred | prepaid lapsed, bill-barred, permanent disconnect → "Number inactive" vs "not reachable" | 🔴 / 🟡 |
| App-uninstall | reduce to non-app features; notify admin | 🔴 app telemetry |
| Non-Airtel re-consent | 3-month cycle (app / SMS / IVR) | 🔴 consent cycle |

**Asks:** **reachability/HLR** API (off vs no-coverage vs inactive, last-on-network); **back-online** subscription; **low-battery fanout**; **MNP / ownership / permanent-disconnect** event stream to FSC.

---

## 7. Circle & membership (FSC foundation — supporting the above)

| Need | Field(s) | Status |
|---|---|---|
| MSISDN → circle lookup (one-circle rule) | `getCircleByMsisdn` | 🔴 |
| Member list / roles / responders | ADMIN / CO_ADMIN / MEMBER + responder flags | 🟡 responders GAP |
| Invite lifecycle | create / get / respond / resend / expire / list (2-day TTL, 3-per-30-day cap) | 🔴 |
| Feature flags + relationship on membership | per-member feature state, relationship label | 🔴 |
| Membership ↔ Whalebone `subscriptionID` (= MSISDN) | linkage FSC must store for Device Safety / Parental | 🔴 |

---

## 8. Not a Network ask (flagged for completeness)

- **Subscription / eligibility / banners** (US 12–14): Billing/CRM — eligibility (Airtel? LOB? corporate? in-circle? pack active?), status (Active/Trial/Expiring/Paused/Closing), grace/resume. Network only supplies the `getCircleByMsisdn` piece of eligibility.
- **Device Safety / Parental content** (§09–10): Whalebone `/management` + `/events`. Network's part is only the FSC linkage and device telemetry.

---

## 9. Consolidated ask list to the Network team (priority)

| # | Ask | Feature | Status | Priority |
|---|---|---|---|---|
| 1 | Typed **device-status** (battery/ringer/network/location/reachability + `lastUpdatedOn`/property) | Dashboard, SOS | 🟡 | P0 |
| 2 | **Reachability/HLR** API (off vs no-coverage vs inactive; flight-vs-off) | Dashboard | 🔴 | P0 |
| 3 | **SOS** live DTO + **LBS** fallback + no-internet short-code | SOS | 🟡/🔴 | P0 |
| 4 | **Fraud/spam** typed feed (call timer, OTP count, no caller no.) + **warn**/**end-call** | Fraud | 🔴 | P0 |
| 5 | **Safety Report** family-access authorization | Fraud | 🟡 | P0 |
| 6 | **Check-in** schedules/list/limits + need-help→connected | Check-in | 🟡/🔴 | P0 |
| 7 | **Alert/history** unified list, role-scoped, 7/30-day retention | History | 🔴 | P0 |
| 8 | **Back-online**, **low-battery**, **MNP/ownership/disconnect** events | Reachability | 🔴 | P1 |
| 9 | **Invite lifecycle** + `getCircleByMsisdn` + responder/feature flags | Circle | 🔴 | P0 |
| 10 | Membership ↔ Whalebone subscriptionID linkage | Device Safety/Parental | 🔴 | P1 |

---

## 10. Open questions for Network (from PRD callouts)

1. **Flight mode vs switched off** — distinguishable at network level? (US 24)
2. **Presidential alert** — can it carry an "Open Airtel App" button/link on Android + iOS? (US 16)
3. **Remote call disconnect** — technically + legally feasible? (US 18)
4. **Back-online** detection feasibility (US 26)
5. **SOS without app/internet** — SMS short-code + native 112 (US 15 CFT)
6. **iPhone signal availability** — which signals are N/A (US 24 callout)
7. **History retention** — 7 vs 30 days (US 9/29)
8. **LBS** accuracy/latency during SOS (US 15)
9. **Port-out early warning** — alert when porting code requested, before completion (US 11)
10. **Device telemetry pipeline** owner — SDK → Kafka → Network hub (confirm with Ajay Saini)

---

*Prepared for the Network ask meeting. Field names reference FSC swagger v1.6-merged and the BEFE requirements; routes are proposals pending Network/Guardian confirmation.*
