# Family Safety — BEFE Layer-1 API Specification

> **Space:** Family Safety · **Status:** Draft for review · **Owner:** Channel / BEFE · **Last updated:** 26 Nov 2026
> **Related:** FSC v2.0 swagger (`/fsc`) · Whalebone API-flow HLD · End-to-End API-flow HLD · Device-Info Requirements

## 1. Overview

The **BEFE (Guardian) Layer-1** is the app-facing contract. The app makes **one aggregate call per screen**; BEFE lands the call on **Channel BE**, which fans out to the downstream reads (**FSC `family/get`, `member/get`, `device/status/fetch`, `history/fetch`** + UCM titles + Network active-services) and returns one merged response.

**Three reads cover the Safety Circle:**

| API | Screen | Returns |
|---|---|---|
| `GET /home` | Home (04), Settings (11) | Family + members (relation, role, responder) + **signals** + **active services** + subscription + recent history |
| `GET /members/{membershipId}` | Member page (05), Phone/network (13) | Member services + full **device status** + check-ins + safety report |
| `GET /history` | Alerts & history (12) | Role-scoped alert/activity history |

- **Base path:** `/befe/fsc/v1`
- **Identity:** `familyId = circleId`, `msisdn = deviceId = subscriptionId`.
- **Envelope (all responses):** `responseCode`, `responseMessage`, `transactionId`, `traceId`.

## 2. Architecture

```
App ──(Layer-1)──▶ BEFE / Guardian ──▶ Channel BE (orchestrator) ──▶ FSC (family/get, member/get, device/status/fetch, history/fetch)
                                                                   ├─▶ UCM (relationship titles)
                                                                   └─▶ Network (active-services, reachability)
```

Channel BE is **stateless, consume-only** (no DP persist); it holds the membership↔subscriptionId linkage and the service→feature map.

---

## 3. API 1 — `GET /home`

**Purpose:** the Home/Family screen in one call.
**Query params:** `familyId` (required), `msisdn` (caller, for role scoping).

**Fans out to:** `family/get` + `member/get`(all) + `device/status/fetch`(familyId) + `history/fetch`(count/recent) + UCM titles + Network active-services.

**Response — top level**

| Field | Type | Notes |
|---|---|---|
| `familyId`, `familyName` | string | circle identity |
| `circleStatus` | enum | Active / Expiring / Paused / Closing |
| `me` | MemberCard | the caller's own card |
| `members[]` | MemberCard | other members |
| `responders[]` | string[] | responder MSISDNs |
| `activeAlertsCount` | int | badge on Alerts & history |

> **Note:** `subscription`, `recentHistory` (history) and per-member `activeServices` are **not** on `/home` — history comes from `/history`, services from `/members/{id}`.

**MemberCard**

| Field | Type | Source |
|---|---|---|
| `membershipId`, `msisdn`, `displayName` | string | FSC member |
| `relationship` | string | **UCM** (Mom/Dad) |
| `airtelCustomer` | int | 0 Airtel else 1 |
| `role` | enum | ADMIN / CO_ADMIN / SUB_ADMIN / SPONSER / MEMBER |
| `isResponder` | bool | — |
| `membershipStatus` | enum | Active / InvitePending / Paused / Inactive |
| `signals` | Signals | FSC device/status + Network |
| `latestCheckInSummary` | string | FSC check-in |
| `activeAlert` | AlertSummary | highest-priority |
| `featuresBrokenHint` | string | e.g. "Location off, SOS won't share location" |

**Example** — see swagger "Example Value" or §6.1 below.

---

## 4. API 2 — `GET /members/{membershipId}`

**Purpose:** member detail page in one call.
**Path:** `membershipId`. **Query:** `familyId` (required).

**Fans out to:** `member/get`(one) + `device/status/fetch`(msisdn) + `trigger/checkin/status/check` (+ Whalebone status if advanced).

**Response**

| Field | Type | Notes |
|---|---|---|
| `member` | MemberInfo | **identity only** (relation, role, status) — **no signals** |
| `deviceDetail` | DeviceDetail | **external** device + signal data (battery, ringer, phoneOff, reachable, signal, SIM, checkinWorking, sosWorking, location). Signals live here only — not duplicated inside `member`. |
| `services[]` | ServiceStatus | per-service availability/health |
| `latestCheckIn`, `checkInHistory[]` | CheckInEntry | FSC check-in |
| `activeAlert` | AlertSummary | — |
| `safetyReportUrl` | string | 3-month Safety Report deep link |
| `deviceSafety` | object | status + protections (if advanced; Whalebone) |
| `parental` | object | activated + screen-time (if advanced) |

---

## 5. API 3 — `GET /history`

**Purpose:** alerts & activity history.
**Query:** `familyId` (required), `msisdn`, `eventType` (CHECK_IN/SOS/FRAUD/ALARM/DEVICE_STATUS), `scope` (active/history/all), `role`, `fromDate`, `toDate`.

**Fans out to:** `history/fetch` (+ UCM titles). **Role-scoped:** fraud & low-battery visible to responders only.

**Response:** `historyInfos[]` of `HistoryItem { eventId, eventType, eventTimestamp, memberMsisdn, displayName, status, message, additionalData }`.

---

## 6. Example responses

### 6.1 `GET /home`
```json
{ "familyId":"FAM1024","circleStatus":"Active",
  "me":{ "membershipId":"M001","displayName":"Vaibhav","role":"ADMIN","isResponder":true,
    "signals":{"reachabilityReason":"REACHABLE","batteryPercent":82,"ringerMode":"SILENT","networkStrength":"STRONG","available":true} },
  "members":[
    {"membershipId":"M003","displayName":"Dad","relationship":"Father","role":"MEMBER",
     "signals":{"reachabilityReason":"SWITCHED_OFF","lastBatteryLevel":6,"networkStrength":"NONE","lastOnNetworkAt":"2026-11-25T18:40:00Z"},
     "latestCheckInSummary":"Paused until phone is back on"},
    {"membershipId":"M004","displayName":"Riya","relationship":"Daughter","role":"MEMBER",
     "signals":{"reachabilityReason":"REACHABLE","batteryPercent":58,"ringerMode":"VIBRATE"},
     "featuresBrokenHint":"Location off, SOS won't share location"}],
  "responders":["919812300001","919812300002"],"activeAlertsCount":1,
  "responseCode":"0","responseMessage":"SUCCESS","transactionId":"txn-7f3a" }
```

### 6.2 `GET /members/M003` (Dad offline)
```json
{ "member":{"membershipId":"M003","displayName":"Dad","relationship":"Father","role":"MEMBER","membershipStatus":"Active","latestCheckInSummary":"Paused until phone is back on"},
  "services":[{"service":"SOS","working":false,"status":"NOT_WORKING","missingPermission":"LOCATION"}],
  "deviceDetail":{"lastBatteryLevel":6,"phoneOff":true,"reachable":false,"reachabilityReason":"SWITCHED_OFF",
    "ringerMode":"NORMAL","networkStrength":"NONE","simStatus":"ACTIVE","checkinWorking":false,"sosWorking":false,
    "appInstalled":true,"lastOnNetworkAt":"2026-11-25T18:40:00Z"},
  "deviceSafety":{"status":"ON","protections":["Dangerous websites","Scam links","Ads"]},
  "safetyReportUrl":"https://airtel.in/safety-report/919812300003",
  "responseCode":"0","responseMessage":"SUCCESS","transactionId":"txn-7f3b" }
```

### 6.3 `GET /history`
```json
{ "historyInfos":[
   {"eventId":"H101","eventType":"CHECK_IN","memberMsisdn":"919812300002","displayName":"Mom","status":"Received","message":"Mom replied 'I'm fine' to the 9:00 am check-in","eventTimestamp":"2026-11-26T09:04:00Z"},
   {"eventId":"H099","eventType":"FRAUD","displayName":"Mom","status":"Warned","message":"Mom got a spam call — you sent her a warning","eventTimestamp":"2026-11-25T13:42:00Z"}],
  "responseCode":"0","responseMessage":"SUCCESS","transactionId":"txn-7f3c" }
```

---

## 7. Enumerations

| Enum | Values |
|---|---|
| `circleStatus` | Active, Expiring, Paused, Closing |
| `role` | ADMIN, CO_ADMIN, SUB_ADMIN, SPONSER, MEMBER |
| `membershipStatus` | Active, InvitePending, Paused, Inactive |
| `service` | CHECKIN, SOS, FRAUD_SPAM, REACHABILITY, SAFE_TRIP, DEVICE_SAFETY, PARENTAL_CONTROLS |
| `ServiceStatus.status` | WORKING, NOT_WORKING, MISSING_PERMISSION, NOT_SUBSCRIBED, NOT_AVAILABLE |
| `reachabilityReason` | REACHABLE, SWITCHED_OFF, NO_COVERAGE, SWITCHED_OFF_OR_FLIGHT, BATTERY_DEAD, INACTIVE_NUMBER |
| `ringerMode` | NORMAL, VIBRATE, SILENT |
| `simStatus` | ACTIVE, INACTIVE, RECHARGE_LAPSED, NEW_OWNER, PORTED_OUT |
| `alertType` | SOS, CHECKIN, CHECKIN_NEED_HELP, FRAUD_SPAM, LOW_BATTERY, BACK_ONLINE, GEOFENCE, DEVICE_SAFETY, CIRCLE_EVENT, PARENTAL_REQUEST |
| `eventType` (history) | CHECK_IN, SOS, FRAUD, ALARM, DEVICE_STATUS |

## 8. Error codes (envelope)

| responseCode | HTTP | Meaning |
|---|---|---|
| `0` | 200 | Success |
| `SH-40001` | 400 | Missing/invalid `familyId` |
| `SH-40301` | 403 | Caller not a member of the circle (BOLA) |
| `SH-40401` | 404 | Family / member not found |
| `SH-50302` | 502 | Downstream (FSC/UCM/Network) failure |

## 9. Non-functional

- **Caching:** `/home` is a heavy fan-out — cache per family ~1–2 min; signals are hourly-cadence, SOS/live read fresh.
- **Role scoping:** pass caller `msisdn`/`role`; fraud & low-battery are responder-only in `/history`.
- **Non-Airtel members:** network signals absent → `Signals.available=false`; app shows the fixed "unavailable features" message.
- **Tracing:** `X-Request-ID` propagated App → BEFE → Channel BE → downstream; returned as `traceId`.

## 10. Downstream mapping (quick reference)

| BEFE API | FSC | UCM | Network/Whalebone |
|---|---|---|---|
| `/home` | family/get, member/get, device/status/fetch, history/fetch | titles | active-services; Whalebone DS status |
| `/members/{id}` | member/get, device/status/fetch, trigger/checkin/status/check | title | Whalebone DS/parental (if advanced) |
| `/history` | history/fetch | titles | — |

## 11. Change log

| Date | Version | Change |
|---|---|---|
| 26 Nov 2026 | 1.0 | Initial Layer-1 spec: `/home`, `/members/{id}`, `/history` with aggregate DTOs + examples |

---

*Attachments: `befe-layer1-swagger.html` (Swagger UI, Try-it-out), `befe-layer1-swagger.json` (import to Postman). This page is the source of truth for the App ↔ BEFE contract.*
