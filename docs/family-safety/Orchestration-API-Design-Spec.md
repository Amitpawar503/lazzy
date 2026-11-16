# Family Safety — Orchestration API Design Spec (methods · enums · request contracts · principles)

**What this is:** the design-hardened version of the fan-out mapping — **which HTTP methods to club vs keep separate**, **whether DELETE is ever needed**, the **full enum catalogue per API** (and how each enum value switches the downstream flow), **proper upstream request contracts** (path / query / body with naming) and the **downstream request** each drives, the **single-API + internal-switch** pattern you proposed, and the **design principles that must not be compromised**.

**Date:** 2026-11-16 · Companions: `…-Optimized`, `…-Detailed`, `…-Enhanced-FanOut`
**Conventions:** upstream base `/family-safety/v1`; upstream JSON = **camelCase**; path params `{resourceId}`; `MSISDN = deviceID = subscriptionID` (Whalebone), `circleId = familyId` (FSC). BFF is an **anti-corruption layer** — it translates naming/IDs; downstream quirks never leak upstream.

---

## 1. HTTP method strategy — club where safe, split where required

| Intent class | Method | Club? | Rule |
|---|---|---|---|
| **Read** | `GET` | **Never clubbed with writes** | side-effect-free; all retrieval stays GET. Scope via query param. |
| **Create / command / action** | `POST` | club many actions via `action`/`eventType` enum | non-idempotent operations, events, invites, lifecycle, pairing, list-edit, subscription activate/suspend |
| **Set desired state (config)** | `PUT` | **club POST+PUT → PUT** | idempotent upsert — protection, parental filter, apps, schedule, lists, reports, circle settings. Body carries full intended state. |
| **Remove** | — | **folded, no separate DELETE** | see §2 |

**Why club POST+PUT into PUT for config:** toggles/filters/reports are *"make the state be X"* — idempotent, safe to retry, naturally a `PUT`. A separate `POST` to create + `PUT` to update is redundant when the resource is a singleton per MSISDN (there is always exactly one filter/report/protection state per line). One `PUT` upserts it.
**Why GET stays separate:** folding a read into a write endpoint breaks caching, safety and idempotency — a non-negotiable (see §7).

---

## 2. Is a separate DELETE needed? → **No, nowhere.**

Every "removal" folds into an existing POST(action) or PUT(state). Checked case by case:

| "Delete" case | Downstream reality | Folded into | Separate DELETE? |
|---|---|---|---|
| Remove member | FSC `POST /member/delete?familyId&memberId` (already a POST) | `POST /circles/{id}/members/{mid}/status {action:REMOVE}` | ❌ no |
| Member leaves | same FSC delete | same status endpoint `{action:LEFT}` | ❌ no |
| Decline invite | FSC `member/update→Inactive` | `…/status {action:DECLINE}` | ❌ no |
| Close circle | FSC has **no delete family**; `family/update→Inactive` | `PUT /circles/{id} {status:"Inactive"}` | ❌ no |
| Remove allow/deny domain | Whalebone `POST .../{listType}/delete` (a POST) | `PUT /parental/{msisdn}/lists {op:REMOVE}` | ❌ no |
| Remove a schedule / app rule | part of full-state `PUT scheduled-filter` / `PUT applications` | the same PUT (omit the entry) | ❌ no |
| Delete subscription/device | **Airtel never calls DELETE** — Whalebone auto-deletes after retention | `POST /protection {action:DISABLE}` → suspend | ❌ no |

> **Verdict:** the upstream surface needs **GET + POST + PUT only**. DELETE adds nothing because downstream removals are themselves POST-based or state-sets, and lifecycle removals belong in the member state-machine (one surface, auditable).

---

## 3. Enum catalogue — every enum and the flow it switches

> Pattern: **one endpoint, enum in body/query switches the downstream call** — "path explosion" avoided, but the BFF **must validate enum × current-state legality** (§7).

| API | Enum field | Values | What each value switches (downstream) |
|---|---|---|---|
| `POST /safety-events` | `eventType` | `CHECK_IN` / `SOS` / `FRAUD` / `GEOFENCE` / `INACTIVITY` | 🔵 OTA Check-in Create / SOS Creation / Incoming Alarm / *(gap)* / *(gap)* |
| ″ | `scheduleType` | `ONE_TIME` / `PERIODIC` | shapes OTA Check-in `ScheduleType` |
| ″ | `targetType` | `INDIVIDUAL` / `RESPONDER` / `BROADCAST` | OTA Alarm target (MSISDN vs FamilyID) |
| `POST /safety-events/{id}/actions` | `action` | `REPLY` / `ACKNOWLEDGE` / `END` / `CANCEL` / `NOTIFY` / `ESCALATE` / `DISMISS` / `PAUSE` / `RESUME` | 🔵 Check-in Response / SOS Update(ack) / SOS Update(resolve) / SOS Cancellation / Outgoing Alarm / SOS Kill+IVR / Check-in Status Update(×3) |
| ″ | `messageCode` | `IM_OK` / `NEED_HELP` / `CALL_ME` | check-in reply payload |
| `GET /safety-events` | `scope` *(by param)* | `id` / `circleId` / `msisdn` | 🔵 Status Check by Trigger / by Family / Device-Status Retrieve |
| `POST /circles/{id}/members` | `action` | `INVITE` / `RESEND` / `REMIND` | 🔵 FSC member/add / member/update(new token) / **no write** + notify |
| `POST /circles/{id}/members/{mid}/status` | `action` | `ACCEPT` / `DECLINE` / `LEFT` / `REMOVE` / `ROLE_UPDATE` | 🔵 FSC member/update→Active / update→Inactive\|delete / delete / delete(+🟣 suspend) / role/update |
| ″ | `role` | `ADMIN` / `SUB_ADMIN` / `SPONSER`* / `MEMBER` | FSC `familyMemberRole` (*confirm `SPONSOR` typo, G6) |
| ″ | `airtelCustomer` | `0` (Airtel) / `1` (other) | FSC `airtelCustomer`; `1` ⇒ app/SMS-only degradation |
| `PUT /family-safety/protection/{msisdn}` | `type` | `DEVICE` / `NETWORK` | 🟣 Whalebone resource / 🔵 Network safety config |
| ″ | `action` | `ENABLE` / `DISABLE` / `REACTIVATE` | subscribe+filter+pair / suspend / activate |
| `PUT /parental/{msisdn}/lists` | `listType` | `WHITELIST` / `BLACKLIST` | 🟣 `/subscriptions/{id}/whitelist` vs `/blacklist` |
| ″ | `op` | `ADD` / `REMOVE` | 🟣 `POST …/{listType}` vs `POST …/{listType}/delete` |
| `PUT /parental/{msisdn}/filter` | `threats[].threatType` | `MALWARE`/`PHISHING`/`C_AND_C`/`BLACKLIST`/`COMPROMISED`/`COINMINER`/`SPAM` (7) | 🟣 filter `threats[]` (all stay `true`) |
| ″ | `contents[].contentType` | `PORN`/`GAMBLING`/`ADVERTISEMENT`/`SOCIAL_NETWORKS`/… | 🟣 filter `contents[]` |
| ″ | `blocked` | `true` / `false` | per-type block flag |
| `GET /family-safety/stats` | `view` | `THREATS` / `PER_MEMBER` / `TOP_SITES` / `TREND` / `RECENT` | 🟣 `/events/stats(threat_type)` / `(device_id)` / `(domain)` / `/events/timeline` / `/events/search` |
| (downstream) | `membershipStatus` | `Active` / `Inactive` | FSC only states (G2) |
| (device-status) | `propertyName` | `BATTERY`/`RINGER`/`NETWORK_TYPE`/`NETWORK_STRENGTH`/`LOCATION`/`LOCK_STATE` | OTA Device-Status array |

---

## 4. Upstream request contracts (proper naming: path / query / body)

> Method chosen per §1. All bodies camelCase. `transactionId` echoed through.

### 4.1 Circle & membership (→ Network FSC)
| Method | Path | Path params | Query params | Body (camelCase) |
|---|---|---|---|---|
| `POST` | `/circles` | — | — | `{ name, description, members:[{ msisdn, role, airtelCustomer }] }` |
| `GET` | `/circles/{circleId}` | `circleId` | `includeMembers?=true` | — |
| `PUT` | `/circles/{circleId}` | `circleId` | — | `{ name?, description?, status? }` |
| `GET` | `/circles` | — | `msisdn` *(availability — G1)* | — |
| `GET` | `/circles/{circleId}/members` | `circleId` | — | — |
| `GET` | `/circles/{circleId}/members/{memberId}` | `circleId,memberId` | — | — |
| `POST` | `/circles/{circleId}/members` | `circleId` | — | `{ action, members:[{ msisdn, role, airtelCustomer }] }` |
| `POST` | `/circles/{circleId}/members/{memberId}/status` | `circleId,memberId` | — | `{ action, role? }` |

### 4.2 Protection (→ Whalebone + Network) — **single API, internal switch** (see §6.1)
| Method | Path | Path params | Body |
|---|---|---|---|
| `PUT` | `/family-safety/protection/{msisdn}` | `msisdn` | `{ type, action }` |
| `GET` | `/family-safety/protection/{msisdn}` | `msisdn` | — |

### 4.3 Parental (→ Whalebone) — PUT upserts, GET reads
| Method | Path | Body |
|---|---|---|
| `GET/PUT` | `/family-safety/parental/{msisdn}/filter` | `{ threats:[{ threatType, blocked }], contents:[{ contentType, blocked }] }` |
| `GET/PUT` | `/family-safety/parental/{msisdn}/applications` | `{ applications:[{ applicationId, blocked }] }` |
| `GET/PUT` | `/family-safety/parental/{msisdn}/schedule` | `{ contents:[{ contentType, blockingSchedule:{ mon:[{ start, end }] } }] }` |
| `GET` | `/family-safety/parental/{msisdn}/lists` | query `?listType=WHITELIST` |
| `PUT` | `/family-safety/parental/{msisdn}/lists` | `{ listType, op, domains:[] }` |
| `GET/PUT` | `/family-safety/parental/{msisdn}/reports` | `{ reports:{ enabled, period, email, phone }, alerts:{ enabled, email, phone } }` |

### 4.4 Safety events (→ Network OTA)
| Method | Path | Query | Body |
|---|---|---|---|
| `POST` | `/safety-events` | — | `{ eventType, initiatorMsisdn, targetMsisdn?, circleId, scheduleType?, scheduleTime?, targetType?, additionalData? }` |
| `POST` | `/safety-events/{eventId}/actions` | — | `{ action, messageCode?, reason? }` |
| `GET` | `/safety-events/{eventId}` | — | — |
| `GET` | `/safety-events` | `scope` via `id` \| `circleId` \| `msisdn` (exactly one) | — |
| `POST` | `/device-status` | — | `{ msisdn, circleId, status:[{ propertyName, value }] }` |
| `GET` | `/device-status` | `msisdn` \| `circleId` | — |
| `GET` | `/safety-report` | `msisdn` \| `circleId` | — |

### 4.5 Stats & pairing (→ Whalebone)
| Method | Path | Query | Body |
|---|---|---|---|
| `GET` | `/family-safety/stats` | `msisdn, view, days?=30` | — |
| `POST` | `/family-safety/devices/{msisdn}/pair` | — | — → `{ token }` |

**Final upstream surface:** ~15 `GET` · ~7 `POST` · ~7 `PUT` · **0 `DELETE`**.

---

## 5. Downstream request contracts (as each system consumes)

| System | Endpoint | Method | Request (verbatim shape) |
|---|---|---|---|
| 🔵 FSC | `/api/v1/family/create` | POST | `RequestFamilyPojo{ familyName, familyDescription, familyStatus, familyMemberPojos[] }` |
| 🔵 FSC | `/api/v1/family/get` | GET | `?familyId=` |
| 🔵 FSC | `/api/v1/family/update` | POST | `?familyId=` + `RequestFamilyPojo` |
| 🔵 FSC | `/api/v1/member/add` | POST | `RequestFamilyMemberPojo{ airtelCustomer, circleMemberRole, familyId, membershipId, membershipStatus, msisdn }` |
| 🔵 FSC | `/api/v1/member/update` | POST | `?memberId=` + `RequestFamilyMemberPojo` |
| 🔵 FSC | `/api/v1/member/delete` | POST | `?familyId=&memberId=` |
| 🔵 FSC | `/api/v1/member/role/update` | POST | `?familyId=&familyMemberRole=&memberId=` |
| 🔵 FSC | `/api/v1/member/get` · `/getAll` | GET | `?familyId=[&memberId=]` |
| 🔵 OTA | Check-in Create | POST(JSON) | `{ TriggerID, FamilyID, InitiatorMSISDN, TargetMSISDN, ScheduleType, ScheduleTime }` |
| 🔵 OTA | Check-in Status Update | POST | `{ TriggerID, Action(Dismiss/Pause/Resume) }` |
| 🔵 OTA | Check-in Response | POST | `{ TriggerID, CheckInTimestamp, CheckInResponse }` |
| 🔵 OTA | SOS Creation / Cancellation | POST | `{ TriggerID, FamilyID?, InitiatorMSISDN? }` |
| 🔵 OTA | SOS Update | POST | `{ TriggerID, AcknowledgedBy?, AcknowledgementTimestamp?, ResolvedBy?, ResolvedTimestamp? }` |
| 🔵 OTA | Incoming / Outgoing Alarm | POST/Kafka | `{ AlarmID, (InitiatedBy,TargetType,)TargetMSISDN, FamilyID, AlarmType }` |
| 🔵 OTA | SOS Alarm Kill | Kafka | `{ SOSAlarmID, Action:"Kill" }` |
| 🔵 OTA | Device Status Store / Retrieve | POST | `{ (DataID,) MSISDN, FamilyID, StatusArray[] }` |
| 🟣 WB | `/management/subscriptions` | POST | `{ "subscription_id":"{MSISDN}" }` → 201 |
| 🟣 WB | `/management/subscriptions/{id}/suspend` · `/activate` | POST | *(no body)* → 200 |
| 🟣 WB | `/management/devices/{id}/filter` | GET/PUT | `{ "threats":[{ "threat_type","blocked" }×7], "contents":[{ "content_type","blocked" }] }` |
| 🟣 WB | `/management/devices/{id}/applications` | GET/PUT | `{ "applications":[{ "application_id","blocked" }] }` |
| 🟣 WB | `/management/devices/{id}/scheduled-filter` | GET/PUT | `{ "contents":[{ "content_type","blocking_schedule":{ "mon":[{ "start","end" }] } }] }` |
| 🟣 WB | `/management/subscriptions/{id}/{listType}` | GET/POST | `{ "domains":[] }` · read `?page=0&page_size=200` |
| 🟣 WB | `/management/subscriptions/{id}/{listType}/delete` | POST | `{ "domains":[] }` |
| 🟣 WB | `/management/users/{id}/reports` | GET/PUT | `{ "reports":{…}, "alerts":{…} }` |
| 🟣 WB | `/management/devices/{id}/pair-app` | POST | *(no body)* → `{ "pairing_response":{ "token" } }` |
| 🟣 WB v2 | `/events/stats` · `/events/timeline` · `/events/search` | GET | query `device_id,action=block,aggregate/interval,days,sort` + headers `Wb-Access-Key`,`Wb-Secret-Key` |

---

## 6. Single-API + internal-switch patterns (your proposal, generalized)

### 6.1 Protection — one `PUT /family-safety/protection/{msisdn}` → internal resource switch
Upstream stays clean (`{ type, action }`); the BFF **internally** decides subscription-vs-device resource and orders the calls. The `subscription`/`device` choice is a **downstream detail — keep it out of the app contract** (ACL principle).

| `type` + `action` | BFF internal routing (ordered) |
|---|---|
| `DEVICE` + `ENABLE` | 1) `POST /management/subscriptions {subscription_id}` → 2) `PUT /management/devices/{id}/filter` (7 threats true) → 3) `POST /management/devices/{id}/pair-app` |
| `DEVICE` + `DISABLE` | `POST /management/subscriptions/{id}/suspend` |
| `DEVICE` + `REACTIVATE` | `POST /management/subscriptions/{id}/activate` → re-PUT filter |
| `NETWORK` + `ENABLE`/`DISABLE` | Network safety-config enable/disable |

> If you *do* want the resource exposed, make it a **query hint** `?resource=subscription|device` that only narrows a diagnostic/admin call — never the primary app flow. Recommended: don't expose it.

### 6.2 Other single-API consolidations
| One upstream endpoint | Internal switch key | Collapses |
|---|---|---|
| `POST /safety-events` | `eventType` | 3 OTA create calls (+2 gap) |
| `POST /safety-events/{id}/actions` | `action` | 7 OTA response/update/cancel/kill/control calls |
| `POST /circles/{id}/members` | `action` | invite / resend / remind |
| `POST /circles/{id}/members/{mid}/status` | `action` | accept / decline / leave / remove / role |
| `PUT /parental/{msisdn}/lists` | `listType` + `op` | 4 Whalebone list calls |
| `GET /family-safety/stats` | `view` | 3 Public-API endpoints |

---

## 7. Design principles that must NOT be compromised

| # | Principle | Applied here |
|---|---|---|
| 1 | **GET is safe & idempotent** | all reads are `GET`; never fold a read into a write; reads cacheable |
| 2 | **Idempotency** | config via `PUT` (safe retry); `POST` creates are pre-checked/idempotency-keyed; retries per failed step |
| 3 | **Resource modeling over RPC soup** | enums switch behavior *within one resource*; unrelated resources never merged |
| 4 | **Bounded, validated enums** | BFF validates `enum × current-state` legality (e.g. `ACKNOWLEDGE` illegal on a check-in); reject early |
| 5 | **Anti-corruption layer (ACL)** | BFF maps camelCase ↔ snake_case ↔ query-POJO; `circleId↔familyId`, `msisdn=deviceID=subscriptionID`; downstream (subscription vs device) hidden |
| 6 | **GET-merge-PUT for Whalebone** | every `filter/applications/scheduled-filter` write sends the *full* intended state (omitted ⇒ unblocked) |
| 7 | **Versioning & backward-compat** | `/v1` prefix; changes additive; new enum values are non-breaking |
| 8 | **Least privilege / consent** | Whalebone keys (`Wb-*`) live in BE only; protection enabled only after consent; non-Airtel ⇒ degraded set |
| 9 | **Resilience** | retry failed step not whole journey; 429 backoff; 409 → GET existing; graceful "unable to check" over wrong state |
| 10 | **Observability** | `transactionId` propagated end-to-end across both downstreams |
| 11 | **Statelessness (+ one explicit store)** | BFF stateless except the **owned invite-state store** (FSC lacks invite states) |
| 12 | **Single writer / serialize per line** | serialize concurrent policy writes per MSISDN to avoid lost updates |

**Trade-off we accept (and mitigate):** enum-routing + POST/PUT clubbing shrinks the surface but adds **payload polymorphism + validation load** — mitigated with OpenAPI discriminators, a documented state machine, and strict enum×state checks. We do **not** compromise GET-safety, idempotency, the ACL, or GET-merge-PUT to save endpoints.

---

## 8. Net effect

| | Before | After |
|---|---|---|
| Upstream endpoints | ~56 (1:1) | **~29** (GET+POST+PUT) |
| DELETE endpoints | several | **0** |
| Methods used | GET/POST/PUT/DELETE | **GET/POST/PUT** |
| Downstream calls reachable | ~40 | ~40 (unchanged — same coverage) |

*Request shapes: Network FSC from Family_Member_API Swagger; Network OTA from API_Doc.pptx; Whalebone from Airtel_SDK_HLD — validate against `apidocs.whalebone.io/devicemanagement` before coding.*
