# Family Safety — Enhanced Fan-out Mapping (Upstream API → many Downstream APIs)

**What this is:** for every **upstream** API the app/services call on the BFF, the **fan-out** to the one-or-many **downstream** APIs it drives, showing **both sides' request payloads** — the request the BFF **takes** from upstream, and the request each downstream API **consumes** (from the Network FSC Swagger, Network OTA API doc, and Whalebone SDK HLD / device-management swagger).

**How to read each block**
- **Upstream API** + **Upstream request** (what the BFF receives) are stated once per block.
- The table fans out: **Variant (enum)** → **Downstream request (from swagger/docs)** → **System** (🔵 Network / 🟣 Whalebone) → **Downstream API** it delivers to.
- One upstream API can deliver to **3–4+ downstream APIs across both systems**.

**Date:** 2026-11-16 · Companions: `…-Optimized`, `…-Detailed`

**ID rule:** `MSISDN = deviceID = subscriptionID` (Whalebone). FSC `familyId = fcId`. Every downstream carries an `AdditionalData{}` + returns `transactionId/responseCode/responseMessage`.

---

## 1. `POST /safety-events/{msisdn}/{targetId}` — eventType fan-out
**Upstream request (BFF takes):** `{ msisdn (path), targetId (path), eventType, initiatorMsisdn, familyId, scheduleType?, scheduleTime?, additionalData{} }`

| Variant (`eventType`) | Downstream request (consumed, from docs) | System | Downstream API (delivers to) |
|---|---|---|---|
| `CHECK_IN` | `{ TriggerID, FamilyID, InitiatorMSISDN, TargetMSISDN, ScheduleType(OneTime/Periodic), ScheduleTime, AdditionalData }` | 🔵 Network OTA | **Check-in Create** |
| `SOS` | `{ TriggerID, FamilyID, InitiatorMSISDN, AdditionalData }` | 🔵 Network OTA | **SOS Creation** |
| `FRAUD` | `{ AlarmID, InitiatedBy(MSISDN/System), TargetType(Individual/Responder/Broadcast), TargetMSISDN, TargetFamilyID, AlarmType, AdditionalData }` | 🔵 Network OTA | **Incoming Alarm / Notification** |
| `GEOFENCE` | *(no downstream owner — Network PPT excludes geofencing)* | ⚠ GAP G7 | BFF-computed from Device-Status, or out of MVP |
| `INACTIVITY` | *(no downstream owner — Network excludes device-status alerts)* | ⚠ GAP G7 | BFF-computed, or out of MVP |

> Delivers to **3 Network APIs** (+2 gaps). Prefer body fields over path params so one route serves all types.

---

## 2. `POST /safety-events/{id}/responses` — action fan-out
**Upstream request:** `{ id (path), action, messageCode?(IM_OK/NEED_HELP/CALL_ME), reason?, by, timestamp, additionalData{} }`

| Variant (`action`) | Downstream request (from docs) | System | Downstream API |
|---|---|---|---|
| `REPLY` | `{ TriggerID, CheckInTimestamp, CheckInResponse, AdditionalData }` | 🔵 Network OTA | **Check-in Response** |
| `ACKNOWLEDGE` | `{ TriggerID, AcknowledgedBy, AcknowledgementTimestamp }` | 🔵 Network OTA | **SOS Update** (ack) |
| `END` / `RESOLVE` | `{ TriggerID, ResolvedBy, ResolvedTimestamp }` | 🔵 Network OTA | **SOS Update** (resolve) |
| `CANCEL` | `{ TriggerID, AdditionalData }` | 🔵 Network OTA | **SOS Cancellation** |
| `NOTIFY` | `{ AlarmID, TargetMSISDN, FamilyID, AlarmType, AdditionalData }` | 🔵 Network OTA (Kafka) | **Outgoing Alarm / Notification** |
| `ESCALATE` | `{ SOSAlarmID, Action: "Kill", AdditionalData }` *(stop)* **or** Outgoing Alarm + IVR | 🔵 Network OTA (Kafka) + IVR | **SOS Alarm Kill** / **Outgoing Alarm** |

> Delivers to **5–6 Network APIs**. BFF validates which `action` is legal for the event's type + state.

---

## 3. `GET /safety-events` — scope fan-out
**Upstream request:** exactly one of `?id=` | `?circleId=` | `?msisdn=`

| Variant (scope) | Downstream request (from docs) | System | Downstream API |
|---|---|---|---|
| `?id=` (SOS) | `{ TriggerID }` → SOS Data array | 🔵 Network OTA | **SOS Status Check** |
| `?id=` (check-in) | `{ TriggerID }` → Check-in Data + Response arrays | 🔵 Network OTA | **Check-in Status Check** |
| `?circleId=` | `{ FamilyID }` → arrays (history) | 🔵 Network OTA | **Check-in / SOS Status Check** |
| `?msisdn=` | `{ MSISDN, FamilyID }` → Status array (Battery/Ringer/NetworkType/Strength/Location/Lock) | 🔵 Network OTA | **Device Status Retrieve** |
| `?msisdn=` (report) | `{ MSISDN, FamilyID }` → Safety array | 🔵 Network OTA | **Safety Report Retrieve** |

> Delivers to **4 Network read APIs**. Exactly one scope param (BFF enforces mutual exclusivity).

---

## 4. `POST /familyCircle/{fcId}/members` — action (invite) fan-out
**Upstream request:** `{ fcId (path), action, members:[{ msisdn, role, airtelCustomer }] }`

| Variant (`action`) | Downstream request (from Swagger) | System | Downstream API |
|---|---|---|---|
| `INVITE` | `RequestFamilyMemberPojo { airtelCustomer(0/1), circleMemberRole, familyId, membershipId:0, membershipStatus:"Active"*, msisdn }` | 🔵 Network FSC | **POST /api/v1/member/add** |
| `INVITE` (notify) | `{ AlarmID, TargetMSISDN, AlarmType:"INVITE", AdditionalData }` + Push/SMS | 🔵 Network OTA / BumbleBee | **Outgoing Alarm** + SMS |
| `RESEND` | `RequestFamilyMemberPojo` (new token) via `?memberId=` | 🔵 Network FSC | **POST /api/v1/member/update** |
| `RESEND` (notify) | Push/SMS with new link | 🟢 BumbleBee | SMS/Push |
| `REMIND` | *(no FSC write)* — notify only, **no window reset** | 🟢 BumbleBee | Push/SMS |

> *Invite lifecycle states are **not** in FSC (`Active/Inactive` only) — BFF owns `INVITED/DECLINED/EXPIRED` and writes FSC `Active` on ACCEPT (Gap G2/G3). Delivers to **FSC + OTA/BumbleBee** (2–3 targets).

---

## 5. `POST /familyCircle/statusUpdate` — lifecycle fan-out
**Upstream request:** `{ fcId, msisdn, memberId, action, newRole? }`

| Variant (`action`) | Downstream request (from Swagger) | System | Downstream API |
|---|---|---|---|
| `ACCEPT` | `RequestFamilyMemberPojo { membershipStatus:"Active", … }` via `?memberId=` | 🔵 Network FSC | **POST /api/v1/member/update** |
| `DECLINE` | `membershipStatus:"Inactive"` **or** `?familyId=&memberId=` | 🔵 Network FSC | **member/update** or **member/delete** |
| `LEFT` | `?familyId=&memberId=` | 🔵 Network FSC | **POST /api/v1/member/delete** |
| `REMOVE` | `?familyId=&memberId=` | 🔵 Network FSC | **POST /api/v1/member/delete** |
| `REMOVE` (2nd hop) | `POST /management/subscriptions/{MSISDN}/suspend` (no body) | 🟣 Whalebone | **suspend** (de-provision protection) |
| `ROLE_UPDATE` | `?familyId=&familyMemberRole=(ADMIN/SUB_ADMIN/SPONSER/MEMBER)&memberId=` | 🔵 Network FSC | **POST /api/v1/member/role/update** |

> Delivers to **FSC (3 ops) + Whalebone suspend** on REMOVE. One lifecycle surface, many downstream.

---

## 6. `POST /familyCircle` + `GET /familyCircle/{fcId}` — circle fan-out
**Create — upstream request:** `{ name, description, members?:[{msisdn, role, airtelCustomer}] }`

| Variant | Downstream request (from Swagger) | System | Downstream API |
|---|---|---|---|
| create | `RequestFamilyPojo { familyName, familyDescription, familyStatus:"Active", familyMemberPojos[] }` | 🔵 Network FSC | **POST /api/v1/family/create** |
| create (sync) | `{ Circle Create, FamilyID, … }` | 🔵 Network OTA | **Sync: Circle Create** |

**Get — upstream request:** `{ fcId (path) }`

| Variant | Downstream request | System | Downstream API |
|---|---|---|---|
| get family | `?familyId={fcId}` → `ResponseFamilyPojo` (embeds `familyMemberPojos`) | 🔵 Network FSC | **GET /api/v1/family/get** |
| compose members | `?familyId={fcId}` → `ResponseFamilyMemberPojo[]` | 🔵 Network FSC | **GET /api/v1/member/getAll** |

---

## 7. `POST /family-safety/protection` — type+action fan-out (commercial)
**Upstream request:** `{ msisdn, type, action }`

| Variant (`type`+`action`) | Downstream request (from HLD) | System | Downstream API |
|---|---|---|---|
| `DEVICE`+`ENABLE` (1) | `{ "subscription_id": "{MSISDN}" }` → 201 (auto-creates device+user) | 🟣 Whalebone | **POST /management/subscriptions** |
| `DEVICE`+`ENABLE` (2) | `{ threats:[{threat_type,blocked:true}×7], contents:[{content_type,blocked}] }` | 🟣 Whalebone | **PUT /management/devices/{id}/filter** |
| `DEVICE`+`ENABLE` (3) | *(no body)* → `{ pairing_response:{ token } }` | 🟣 Whalebone | **POST /management/devices/{id}/pair-app** |
| `DEVICE`+`DISABLE` | *(no body)* → 200 | 🟣 Whalebone | **POST /management/subscriptions/{id}/suspend** |
| `DEVICE`+`REACTIVATE` | *(no body)* → 200 (renewal) | 🟣 Whalebone | **POST /management/subscriptions/{id}/activate** |
| `NETWORK`+`ENABLE/DISABLE` | Network safety-feature config (fraud/reachability signal enablement) | 🔵 Network | **Network safety config** |

> One `ENABLE` delivers to **3 Whalebone calls** in sequence. Toggle = config, **not** a COM product order.

---

## 8. `GET /family-safety/protection-status?msisdn=` — compose fan-out
**Upstream request:** `{ msisdn }` → compose `{ deviceProtection, networkProtection, licenseValid, devicePaired }`

| Source | Downstream request | System | Downstream API |
|---|---|---|---|
| device state | `GET /management/devices/{MSISDN}` | 🟣 Whalebone | **GET /management/devices/{id}** |
| subscription state | subscription status (ACTIVE/SUSPENDED) | 🟣 Whalebone | **subscription state** |
| live protection | `GET /events/stats?device_id={MSISDN}&action=block&days=1` | 🟣 Whalebone Public v2 | **/events/stats** |
| network state | Network safety-toggle state | 🔵 Network | **Network safety state** |

---

## 9. Parental controls (all 🟣 Whalebone) — resource fan-out
**Upstream (per resource):** `PUT/POST /family-safety/parental/{msisdn}/...`

| Upstream resource | Downstream request (from HLD) | Downstream API |
|---|---|---|
| content filter | `{ threats:[…7 true], contents:[{content_type:"porn",blocked:true},…] }` (GET-merge-PUT) | **PUT /management/devices/{id}/filter** |
| app blocking | `{ applications:[{ application_id:"facebook", blocked:true }] }` | **PUT /management/devices/{id}/applications** |
| scheduled filter | `{ contents:[{ content_type:"social-networks", blocking_schedule:{ mon:[{start:"8:00",end:"14:00"}] } }] }` | **PUT /management/devices/{id}/scheduled-filter** |
| allow-list ADD | `{ domains:["example.com"] }` | **POST /management/subscriptions/{id}/whitelist** |
| allow-list REMOVE | `{ domains:["example.com"] }` | **POST /management/subscriptions/{id}/whitelist/delete** |
| allow-list READ | `?page=0&page_size=200` | **GET /management/subscriptions/{id}/whitelist** |
| deny-list ADD / REMOVE / READ | `{ domains:[…] }` / `?page=…` | **POST/GET /management/subscriptions/{id}/blacklist[/delete]** |
| email/SMS reports | `{ reports:{enabled,period:"monthly",email,phone}, alerts:{enabled,email,phone} }` | **PUT /management/users/{id}/reports** |

> Every `filter`/`applications`/`scheduled-filter` write is **GET-merge-PUT** — omitted threat/content types become unblocked.

---

## 10. `GET /family-safety/stats?msisdn=` — view fan-out (🟣 Whalebone Public API v2)
**Upstream request:** `{ msisdn, view, days }` · headers held by Airtel BE: `Wb-Access-Key`, `Wb-Secret-Key`

| Variant (`view`) | Downstream request (from HLD) | Downstream API |
|---|---|---|
| `THREATS` | `?device_id={M}&action=block&aggregate=threat_type&days=30` → `[[threat_type,count]]` | **GET /events/stats** |
| `PER_MEMBER` | `?device_id={A}&device_id={B}&action=block&aggregate=device_id&days=30` → `[[device_id,count]]` | **GET /events/stats** |
| `TOP_SITES` | `?device_id={M}&action=block&aggregate=domain&days=30` → `[[domain,count]]` top 10 | **GET /events/stats** |
| `TREND` | `?device_id={M}&action=block&interval=day&days=30` → `[[timestamp,count]]` | **GET /events/timeline** |
| `RECENT` | `?device_id={M}&action=block&days=7&sort=desc` → `[{timestamp,domain,threat_type,device_id}]` | **GET /events/search** |

> Delivers to **3 Public-API endpoints** (stats/timeline/search). Rules: always pass `days` (max 220); cache 24 h; back off on 429.

---

## 11. Fan-out index (how many downstream each upstream drives)

| Upstream API | # downstream APIs | Systems touched |
|---|---|---|
| `POST /safety-events/{msisdn}/{targetId}` | 3 (+2 gap) | 🔵 Network OTA |
| `POST /safety-events/{id}/responses` | 5–6 | 🔵 Network OTA (+IVR) |
| `GET /safety-events` | 4 | 🔵 Network OTA |
| `POST /familyCircle/{fcId}/members` | 2–3 | 🔵 Network FSC + OTA/🟢 BumbleBee |
| `POST /familyCircle/statusUpdate` | 3–4 | 🔵 Network FSC + 🟣 Whalebone |
| `POST /familyCircle` + `GET /familyCircle/{fcId}` | 2 + 2 | 🔵 Network FSC + OTA |
| `POST /family-safety/protection` | up to 4 | 🟣 Whalebone + 🔵 Network |
| `GET /family-safety/protection-status` | 4 | 🟣 Whalebone + 🔵 Network |
| Parental (content/apps/schedule/lists/reports) | 8 | 🟣 Whalebone |
| `GET /family-safety/stats` | 3 | 🟣 Whalebone Public v2 |
| `POST /device/{msisdn}/pair` | 1 | 🟣 Whalebone |

**Totals:** ~17 upstream contracts → **~40 distinct downstream calls** across 🔵 Network (FSC 9 + OTA 17) and 🟣 Whalebone (Management 11 + Public v2 5).

---

## 12. Gaps (carried from companions)
G1 MSISDN→familyId lookup (FSC) · G2 FSC no invite states → BFF store · G3 no first-class invite/remind/resend · G4 Whalebone live swagger unreachable (HLD-reconstructed) · G5 safety-event host · G6 `SPONSER` typo · G7 **GEOFENCE/INACTIVITY no Network owner** · G8 Public-API key custody + 429.

---

*Request payloads: Network FSC from Family_Member_API Swagger; Network OTA from API_Doc.pptx; Whalebone from Airtel_SDK_HLD — validate against `apidocs.whalebone.io/devicemanagement` before coding.*
