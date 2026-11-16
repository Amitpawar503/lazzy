# Family Safety — Orchestration Layer: Upstream ↔ Downstream Mapping (OPTIMIZED)

**What this is:** the **Channel BE / Family Safety BFF** contract — how the **upstream** (Airtel app + other services) binds to the two **downstream** systems, **Network** and **Whalebone**, with API surface **optimized** (duplicates collapsed via `action`/`type`/`eventType` enums + query params).

**Companion doc:** `Orchestration-Layer-Mapping-Detailed.md` = same mapping **without** optimization (every intent as its own endpoint, field-level, with sequences).

**Date:** 2026-11-16 · **Status:** Draft for Network + Whalebone binding review

```
        UPSTREAM (GET/POST/consume)                         DOWNSTREAM
┌───────────────────────────────┐        ┌───────────────────────────────────────────┐
│ Airtel App / Thanks App        │        │ NETWORK                                     │
│ user-data-aggregator (UDA)     │  REST  │  • FSC family/member CRUD   (/fsc)          │
│ other Airtel services          │◄──────►│  • OTA event engine (check-in/SOS/alarm/    │
└───────────────┬───────────────┘        │    device-status/safety-report, IVR, Kafka) │
                │                         ├───────────────────────────────────────────┤
     ┌──────────▼───────────┐   REST/     │ WHALEBONE  (via Propositions BE for billing)│
     │  CHANNEL BE / FS BFF  │──provision─►│  • Management /3 (subscription, filter,     │
     │  orchestration layer  │             │    applications, scheduled-filter, lists,   │
     └──────────┬───────────┘             │    reports, pair-app, suspend/activate)     │
                │                          │  • Public API v2 (/events stats & timeline) │
                │  async                   ├───────────────────────────────────────────┤
                └─────────────────────────►│ Propositions BE · BumbleBee (notify/IVR)    │
                                           └───────────────────────────────────────────┘
```

---

## 1. Downstream systems in play

| # | Downstream | Base | Owns | Does NOT own |
|---|---|---|---|---|
| D1 | **Network — FSC** | `/fsc` | Family + member CRUD, roles | invite lifecycle states (only Active/Inactive) |
| D2 | **Network — OTA event engine** | JSON sync + Kafka | Check-in, SOS, alarms/notifications, device-status store/retrieve, safety report, IVR | **parental, content filter, geofencing, device safety, app install/uninstall, ad blocking** (explicit note) |
| D3 | **Whalebone — Management** | Retail API `/3` → `/management` | Subscription lifecycle, threat/content filter, app blocking, scheduled filter, allow/deny lists, email/SMS reports, SDK pairing | — |
| D4 | **Whalebone — Public API v2** | `/whalebone/2` → `/events` | Block stats, timelines, recent-events | writes |
| D5 | **Propositions BE** | — | Billing/eligibility → triggers Whalebone subscription create/suspend/activate | — |
| D6 | **BumbleBee / IVR** | — | Push/SMS/voice dispatch | — |

> **ID convention (Whalebone):** `deviceID == subscriptionID == MSISDN`. Whalebone **auto-creates** device + user on subscription create; Airtel **never** calls `POST /management/devices`, `POST /management/users`, or any `DELETE`.

---

## 2. Optimized upstream contract (freeze this for the App)

Collapse related operations into **one contract + enum**. 10 app intents → **~9 upstream contracts**.

| # | Optimized upstream API | Enum / params | Replaces | Primary downstream |
|---|---|---|---|---|
| **U0** | *(UDA field)* profile returns `familySafetyFlag` + `fcId` | — | separate "am I in a circle?" hop | Network FSC lookup (⚠ by-MSISDN gap) |
| **U1** | `GET /familyCircle/{fcId}` | — | — | `GET /fsc/.../family/get` |
| **U2** | `POST /familyCircle` | — | create (don't hide in GET) | `POST /fsc/.../family/create` |
| **U3** | `POST /familyCircle/{fcId}/members` | `action: INVITE \| RESEND \| REMIND` | 3 invite APIs | `POST /fsc/.../member/add` + BFF invite-state + notify |
| **U4** | `POST /familyCircle/statusUpdate` | `action: ACCEPT \| DECLINE \| LEFT \| REMOVE` (+`ROLE_UPDATE`) | 4–5 lifecycle APIs | `member/update \| delete \| role/update` |
| **U5** | `GET /family-safety/protection-status?msisdn=` | — | — | Whalebone GET device/subscription + Public API |
| **U6** | `POST /family-safety/protection` | `type: DEVICE_PROTECTION \| NETWORK_PROTECTION` + `action: ENABLE \| DISABLE` | 2 toggle APIs | Whalebone subscription + `PUT device/{id}/filter` / Network cfg |
| **U7** | `POST /safety-events` | `eventType: CHECK_IN \| SOS \| FRAUD \| GEOFENCE \| INACTIVITY` + body | 5 path variants | Network OTA Check-in/SOS/Alarm create |
| **U8** | `POST /safety-events/{id}/responses` | `action: REPLY \| ACKNOWLEDGE \| END \| CANCEL \| NOTIFY \| ESCALATE` | 6 APIs | Network OTA Check-in Response / SOS Update/Cancel/Kill / Outgoing Alarm |
| **U9** | `GET /safety-events` | `?id=` \| `?circleId=` \| `?msisdn=` | 3 GET shapes | Network OTA Check-in / SOS / Device-status retrieve |

### Parental & Device-Safety group (all → Whalebone) — optimized

| # | Optimized upstream API | Enum / params | Whalebone downstream |
|---|---|---|---|
| **U10** | `PUT /family-safety/parental/{msisdn}/content` | `contents[]{type, blocked}` | `PUT /management/devices/{id}/filter` (GET-merge-PUT; threats stay true) |
| **U11** | `PUT /family-safety/parental/{msisdn}/apps` | `applications[]{app_id, blocked}` | `PUT /management/devices/{id}/applications` |
| **U12** | `PUT /family-safety/parental/{msisdn}/schedule` | `contents[]{type, blocking_schedule}` | `PUT /management/devices/{id}/scheduled-filter` |
| **U13** | `POST /family-safety/parental/{msisdn}/list` | `listType: WHITELIST \| BLACKLIST` + `op: ADD \| REMOVE` + `domains[]` | `POST /management/subscriptions/{id}/{listType}[/delete]` |
| **U14** | `PUT /family-safety/parental/{msisdn}/reports` | `reports{}, alerts{}` | `PUT /management/users/{id}/reports` |
| **U15** | `GET /family-safety/stats?msisdn=` | `view: THREATS \| PER_MEMBER \| TOP_SITES \| TREND \| RECENT` | Public API v2 `/events/stats` · `/events/timeline` · `/events/search` |
| **U16** | `POST /family-safety/device/{msisdn}/pair` | — | `POST /management/devices/{id}/pair-app` → `{token}` |

**Net optimized surface: ~17 upstream contracts** covering the full App + parental suite across both downstreams (vs ~35+ naive).

---

## 3. Optimized binding detail (U0–U9)

### U0 — UDA enrichment: `familySafetyFlag` + `fcId`
- **Upstream:** additive fields on the existing user-data-aggregator profile response — `familySafetyFlag: boolean`, `fcId: string|null`, optional `role`, `membershipStatus`.
- **Downstream:** needs **MSISDN → familyId** on Network FSC. **⚠ GAP G1** — FSC Swagger only has `GET /family/get?familyId=`. Ask Network for `GET /api/v1/family/getByMsisdn?msisdn=` (or resolve via Digital Profile / UCM party index) before UDA can set the flag.

### U1 — `GET /familyCircle/{fcId}`
- → `GET /fsc/api/v1/family/get?familyId={fcId}` (response embeds `familyMemberPojos`); optional compose `GET /fsc/api/v1/member/getAll?familyId={fcId}`.
- **BFF maps:** `familyId ↔ fcId`; roles `ADMIN/SUB_ADMIN/SPONSER/MEMBER`; status `Active/Inactive`.

### U2 — `POST /familyCircle`
- → `POST /fsc/api/v1/family/create` body `RequestFamilyPojo{familyName, familyDescription, familyStatus:"Active", familyMemberPojos?[]}`.
- **Idempotent-create:** pre-check "already in a circle" (needs G1); if exists, return existing `fcId`. Do **not** create inside a GET.

### U3 — `POST /familyCircle/{fcId}/members` + `action`
| action | BFF rule | Network FSC | Side effect |
|---|---|---|---|
| `INVITE` | not in circle · size < max · not already INVITED | `POST /member/add` (membershipStatus pending-equivalent) | Push+SMS via BumbleBee / Network alarm |
| `RESEND` | prior EXPIRED/stale, or declined-then-reinvite | `member/update` + new token | new token; invalidate old |
| `REMIND` | still INVITED within validity | **no FSC write** (or soft `member/update` touch) | notify only; **do not restart** validity window |

**⚠ GAP G2/G3:** FSC `membershipStatus` only allows `Active/Inactive` — no `INVITED/PENDING/DECLINED/LEFT`. Either Network extends the enum, or the **BFF owns the invite-state store** and writes FSC only as `Active` after `ACCEPT`.

### U4 — `POST /familyCircle/statusUpdate` + `action`
| action | Network FSC |
|---|---|
| `ACCEPT` | `POST /member/update` → `membershipStatus=Active` (or `member/add` if invite was BFF-only) |
| `DECLINE` | `member/update → Inactive` or `member/delete` (prefer soft if Network adds DECLINED) |
| `LEFT` | `member/delete` or update + leave workflow (admin-approval path may sit in BFF under parental lock) |
| `REMOVE` | `POST /member/delete?familyId&memberId` (admin force; de-provision protection via Propositions BE/Whalebone as 2nd hop) |
| `ROLE_UPDATE` *(optional, same API)* | `POST /member/role/update?familyId&familyMemberRole&memberId` |

### U5 — `GET /family-safety/protection-status?msisdn=`
- Compose `{ deviceProtection: ON|OFF|SUSPENDED, networkProtection: ON|OFF|SUSPENDED, licenseValid, devicePaired }`.
- **Downstream:** Whalebone `GET /management/devices/{msisdn}` (+ subscription state) and, if separate, the Network safety-toggle state. Live protection state also inferable from Public API v2.

### U6 — `POST /family-safety/protection` + `type` + `action`
| type + action | Downstream |
|---|---|
| `DEVICE_PROTECTION` + `ENABLE` | Propositions BE → Whalebone `POST /management/subscriptions` (first enablement; auto-creates device+user) → then `PUT /management/devices/{id}/filter` with all 7 threats `true` |
| `DEVICE_PROTECTION` + `DISABLE` | Whalebone `POST /management/subscriptions/{id}/suspend` (no body) |
| `NETWORK_PROTECTION` + `ENABLE/DISABLE` | Network safety config (fraud/reachability signal enablement) |
- **Toggle = config, not a product order** (EA decision). Re-enable on renewal = `POST /management/subscriptions/{id}/activate`.

### U7 — `POST /safety-events` + `eventType`
| eventType | Network OTA downstream |
|---|---|
| `CHECK_IN` | **Check-in Create** {TriggerID, FamilyID, InitiatorMSISDN, TargetMSISDN, ScheduleType(OneTime/Periodic), ScheduleTime} |
| `SOS` | **SOS Creation** {TriggerID, FamilyID, InitiatorMSISDN} |
| `FRAUD` | **Incoming Alarm** {AlarmID, InitiatedBy, TargetType, Target MSISDN/FamilyID, AlarmType} (Network fraud/Presidential-alert feed) |
| `GEOFENCE` / `INACTIVITY` | **⚠ GAP G7** — Network PPT explicitly excludes geofencing & device-status-driven alerts. Owner TBD (BFF-computed from device-status, or out of MVP). |
- Prefer **body fields** over `POST /safety-event/{msisdn}/{targetId}` path params so one route serves all types.

### U8 — `POST /safety-events/{id}/responses` + `action`
| action | Meaning | Network OTA downstream |
|---|---|---|
| `REPLY` | check-in response (IM_OK/NEED_HELP/CALL_ME) | **Check-in Response** {TriggerID, CheckInTimestamp, CheckInResponse} |
| `ACKNOWLEDGE` | SOS acknowledged | **SOS Update** {TriggerID, AcknowledgedBy, Timestamp} |
| `END` | SOS "I'm safe" / resolved | **SOS Update** {ResolvedBy, Timestamp} |
| `CANCEL` | accidental SOS | **SOS Cancellation** {TriggerID} |
| `NOTIFY` | fan-out | **Outgoing Alarm (Kafka)** / BumbleBee |
| `ESCALATE` | force next step | **Outgoing Alarm** / IVR; **SOS Alarm Kill (Kafka)** to stop |
- BFF validates which `action` is legal for the event's `eventType` + current state.

### U9 — `GET /safety-events?id|circleId|msisdn`
| scope | Network OTA downstream |
|---|---|
| `?id=` | Check-in Status Check / SOS Status Check by TriggerID |
| `?circleId=` | …by FamilyID (history) |
| `?msisdn=` | …by Initiator MSISDN, or **Device Status Retrieve** {MSISDN/FamilyID} |
- Exactly one scope param; BFF validates mutual exclusivity.

---

## 4. Optimization summary (what we collapsed)

| Before (naive) | After | Saving |
|---|---|---|
| invite + resend + remind | 1 `POST …/members` + `action` | −2 |
| accept + decline + leave + remove (+role) | 1 `statusUpdate` + `action` | −3 (−4) |
| device-protection + network-protection | 1 `POST /protection` + `type` | −1 |
| safety create per type (×5 paths) | 1 `POST /safety-events` + `eventType` | −4 |
| reply/ack/end/cancel/notify/escalate | 1 `/responses` + `action` | −5 |
| get by id / circle / msisdn | 1 `GET /safety-events` + query | −2 |
| whitelist add/remove + blacklist add/remove | 1 `POST …/list` + `listType`+`op` | −3 |

---

## 5. Gaps / asks to close with Network & Whalebone

| # | Gap | Owner |
|---|---|---|
| G1 | No **MSISDN → familyId** lookup in FSC Swagger (blocks UDA flag) | Network — add `GET /family/getByMsisdn` |
| G2 | FSC `membershipStatus` only `Active/Inactive` — no invite lifecycle | Network enum **or** BFF-owned invite store |
| G3 | No first-class INVITE/REMIND/RESEND on FSC | BFF orchestration + BumbleBee; FSC add/update only |
| G4 | Whalebone **live swagger** (`apidocs.whalebone.io/devicemanagement`) not reachable here; contract reconstructed from SDK HLD — confirm exact request/response schemas & error codes | Whalebone / PBE |
| G5 | Safety-event host: Network OTA engine vs separate Safety service — confirm single owner | Network / Architecture |
| G6 | Role enum typo **SPONSER** — confirm intended `SPONSOR` | Network |
| G7 | `GEOFENCE` / `INACTIVITY` have **no Network owner** (PPT excludes them) | Product / Architecture |
| G8 | Whalebone Public API v2 auth (`Wb-Access-Key` + `Wb-Secret-Key`) held by Airtel BE only — confirm key custody & 429 limits | Whalebone / Airtel BE |

---

## 6. Appendix — downstream API reference (as consumed)

### 6A. Network FSC (`/fsc`) — Swagger 2.0
| Method | Path | Body / query |
|---|---|---|
| POST | `/api/v1/family/create` | `RequestFamilyPojo` |
| GET | `/api/v1/family/get` | `?familyId=` → `ResponseFamilyPojo` |
| POST | `/api/v1/family/update` | `?familyId=` + `RequestFamilyPojo` |
| POST | `/api/v1/member/add` | `RequestFamilyMemberPojo` |
| POST | `/api/v1/member/delete` | `?familyId=&memberId=` |
| GET | `/api/v1/member/get` | `?familyId=&memberId=` |
| GET | `/api/v1/member/getAll` | `?familyId=` |
| POST | `/api/v1/member/role/update` | `?familyId=&familyMemberRole=&memberId=` (ADMIN/SUB_ADMIN/SPONSER/MEMBER) |
| POST | `/api/v1/member/update` | `?memberId=` + `RequestFamilyMemberPojo` |

`RequestFamilyMemberPojo`: `airtelCustomer(0=Airtel,1=other)`, `circleMemberRole`, `familyId?`, `membershipId(0=new)`, `membershipStatus(Active/Inactive)`, `msisdn`. Envelope: `responseCode`, `responseMessage`, `transactionId`.

### 6B. Network OTA event engine (JSON sync + Kafka) — from API PPT
Sync: Circle Create/End · Member Add/Del/Update/Active/Inactive · Role Mod. Events: Incoming Alarm (Presidential) · Outgoing Alarm (Kafka) · SOS Alarm Kill (Kafka) · Check-in Create/Status-Update/Response/Status-Check · SOS Creation/Cancellation/Update/Status-Check · Device Status Store/Retrieve · Safety Report Retrieve · IVR. **Excludes:** device-status notifications, parental, content filter, geofencing, device safety, app install/uninstall, ad blocking.

### 6C. Whalebone — Management (Retail API `/3`) — from SDK HLD
`deviceID == subscriptionID == MSISDN`. Auth: Airtel tenant API keys (BE only).
| Method | Path | Purpose |
|---|---|---|
| POST | `/management/subscriptions` | First enablement — body `{subscription_id: MSISDN}` → 201; auto-creates device+user |
| POST | `/management/subscriptions/{id}/suspend` | Disable (no body) |
| POST | `/management/subscriptions/{id}/activate` | Re-enable on renewal (no body) |
| GET | `/management/devices/{id}` | Device details |
| GET/PUT | `/management/devices/{id}/filter` | Threat+content filter (7 threats; GET-merge-PUT; omitted types → unblocked) |
| GET/PUT | `/management/devices/{id}/applications` | App blocking `[{application_id, blocked}]` |
| GET/PUT | `/management/devices/{id}/scheduled-filter` | `contents[].blocking_schedule.{day:[{start,end}]}` |
| GET/POST | `/management/subscriptions/{id}/{listType}` | Allow/deny read/add (`whitelist`\|`blacklist`), `?page=0&page_size=200`, body `{domains:[]}` |
| POST | `/management/subscriptions/{id}/{listType}/delete` | Remove domains `{domains:[]}` |
| GET/PUT | `/management/users/{id}/reports` | Email/SMS `{reports{enabled,period,email,phone}, alerts{…}}` |
| POST | `/management/devices/{id}/pair-app` | One-time SDK pairing token → `{pairing_response:{token}}` |

Airtel **never** calls `POST /management/devices`, `POST /management/users`, or `DELETE` (Whalebone auto-creates and auto-deletes after retention).

### 6D. Whalebone — Public API v2 (stats) — from SDK HLD
Base `https://[Airtel-hosted]/whalebone/2` · headers `Wb-Access-Key` + `Wb-Secret-Key` · `{MSISDN}=device_id`.
| Method | Path | Portal widget |
|---|---|---|
| GET | `/events/stats?device_id={M}&action=block&aggregate=threat_type&days=30` | Threats blocked by type |
| GET | `/events/stats?device_id={A}&device_id={B}&action=block&aggregate=device_id&days=30` | Per-member number |
| GET | `/events/stats?device_id={M}&action=block&aggregate=domain&days=30` | Top blocked sites (10) |
| GET | `/events/timeline?device_id={M}&action=block&interval=day&days=30` | Trend chart |
| GET | `/events/search?device_id={M}&action=block&days=7&sort=desc` | Recent blocked (scroll=true) |

Rules: always pass `days` (max 220); cache 24 h per MSISDN; back off on 429.
**Live swagger:** `https://apidocs.whalebone.io/devicemanagement/#/` (confirm schemas — not reachable from this build).

---

*Reconstructed from Family_Member_API_Documentation (Network FSC), API_Doc.pptx (Network OTA engine) and Airtel_SDK_HLD (Whalebone Aura). Whalebone paths are HLD-derived; validate against the live device-management swagger before coding. Optimized surface is a recommended freeze — see the Detailed companion for the 1:1 un-optimized mapping.*
