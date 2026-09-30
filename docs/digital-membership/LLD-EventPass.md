# LLD — Advantage Club Membership QR & Event Entry (Event Pass)

> **Confluence note:** paste via **Confluence → … → Insert Markup → Markdown**, or the Markdown
> macro. ` ```mermaid ` blocks render if the **Mermaid** app/macro is installed (otherwise wrap
> each in a Mermaid macro or export as an image); ` ```java ` blocks render as code blocks. This is
> a single, self-contained page: architecture, data model, all **5 APIs** with conditions and
> sequence diagrams, and the **full code changes**.

| | |
|---|---|
| **Type** | Low-Level Design (single page) |
| **Module** | `com.airtel.userprofile.eventpass` (new, inside the **User Profile Service** microservice) |
| **Store** | MongoDB (reuses existing `contest_entries`); Aerospike for the single-active QR pointer; KMS/HSM for the signing key |
| **Conventions** | Matches the existing `contest` module: Lombok Mongo `@Document`s, DAO + `MongoTemplate`, `DuplicateKeyException` for atomic uniqueness, `com.airtel.core.dto.genericResponse.Response`, `@AuditLog`, `IV_USER` header |
| **Status** | Proposed — for review |
| **Related** | HLD: `03-hld.md`; reference code: `reference-impl/eventpass/` (also embedded in §13) |

---

## Table of Contents
1. [Design principle](#1-design-principle)
2. [Architecture & components](#2-architecture--components)
3. [Service layering (Controller / Service / DAO)](#3-service-layering)
4. [Data model, collections & indexes](#4-data-model-collections--indexes)
5. [QR token](#5-qr-token)
5A. [QR image util — render & validate](#5a-qr-image-util--render--validate)
6. [Callback contract](#6-callback-contract)
7. [API surface — the five endpoints](#7-api-surface--the-five-endpoints)
8. [API sequences & conditions](#8-api-sequences--conditions)
8A. [Sample requests, responses & error responses](#8a-sample-requests-responses--error-responses-per-api)
9. [Atomic redemption — exactly-once](#9-atomic-redemption--exactly-once)
10. [Winner read & write (contest reuse)](#10-winner-read--write-contest-reuse)
11. [Idempotency, exceptions, config](#11-idempotency-exceptions-config)
12. [Module map (all files)](#12-module-map-all-files)
13. [Code changes (full source)](#13-code-changes-full-source)
14. [Open decisions](#14-open-decisions)

---

## 1. Design principle

> **Identity + won-events QR, agent-session-bound checkpoint. One app for both roles.**
> The QR proves **who** the customer is **and which events they have won** — the winning
> `eventId`s are read from the contest data at generation time and **signed into the token** by the
> **User Profile Service**, then shown in the Airtel Thanks App. Scanning is **also inside the same
> Thanks App**, in an *agent mode* unlocked only for **whitelisted MSISDNs** — **no microsite, no
> OTP**. The **checkpoint** (ENTRY / GOODIE) and the **event** come from the **agent's validated
> session**. Entry is allowed when `session.eventId ∈ token.wonEvents` **and** that
> `(customer, event, checkpoint)` has not already been redeemed — an **atomic, exactly-once,
> per-checkpoint** operation.

- One Thanks App, two modes: *customer* (shows QR) and *agent* (scans, whitelisted MSISDNs only).
- Won events resolve from the existing **contest** data (`contest_entries.winnerInfo`, **event = `programId`**).
- All trust decisions on the backend; the signing key is backend-only; the won-events list is inside the token signature.

---

## 2. Architecture & components

One microservice (**User Profile Service**) with internal components. The customer QR and the agent
scanner both live in the Thanks App.

```mermaid
flowchart TB
  subgraph App["Airtel Thanks App"]
    QRC["Customer: QR card"]
    AGT["Agent mode: scan"]
  end
  subgraph UPS["User Profile Service (microservice)"]
    QRG[QR Generation]
    ELIG[Eligibility]
    WLC[Agent Whitelist & Session]
    CTS["Contest (read winnerInfo / write via API 5)"]
    EVS[Entry Validation]
  end
  KMS[("KMS/HSM signing key")]
  DB[(MongoDB)]
  Admin[Admin / Eng]

  QRC -->|API 4 generate| QRG
  AGT -->|API 2 validate/session| WLC
  AGT -->|API 3 entry| EVS
  Admin -->|API 1 whitelist| WLC
  Admin -->|API 5 mark winner| CTS
  QRG --> ELIG
  QRG --> CTS
  EVS --> WLC
  EVS --> CTS
  QRG --- KMS
  EVS --- KMS
  UPS --- DB
```

| Component | Responsibility |
|---|---|
| **Thanks App — Customer mode** | Renders membership surfaces + QR card; requests QR from the User Profile Service; screenshot mitigation. No event/winner logic. |
| **Thanks App — Agent mode** | Whitelisted MSISDNs only; pick authorized event+checkpoint, scan, POST to Entry Validation, render decision. Decides nothing. |
| **QR Generation** | Checks eligibility, reads won events from Contest, mints signed short-TTL token, single-active per customer. |
| **Eligibility** | Active Postpaid + Fastlane / Advantage Club membership. |
| **Agent Whitelist & Session** | Which events + checkpoints each agent MSISDN may scan; single-active scanning session. |
| **Contest** | Existing contest engine; winner source of truth (`contest_entries.winnerInfo`, event=`programId`). Read at API 4 / entry; **written** by API 5. |
| **Entry Validation** | The gate authority: verify token, authorize agent, winner check, atomic redeem, audit, callback. |

**Trust boundaries:** the app is semi-trusted (can request a QR / validate an agent) but **untrusted
for decisions** — Entry Validation decides server-side; event, checkpoint, agent identity and
timestamp come from the session, never the client body.

---

## 3. Service layering

Inside the one microservice, each component is layered Controller → Service → DAO/Repository:

| Layer | Role | Examples |
|---|---|---|
| **Controller (API boundary)** | Accepts/returns **DTOs** only, never DB entities | `MembershipQrController`, `AgentController`, `EventEntryController`, `WinnerAdminController` |
| **Service (business logic)** | Eligibility, whitelist, token mint/verify, redemption, winner read/write | `MembershipQrService`, `AgentAccessService`, `EventEntryService`, `WinnerLookupService`, `WinnerAdminService`, `QrTokenService` |
| **DAO (persistence)** | `MongoTemplate` mapping documents ↔ collections | `EventRedemptionDao`, `ScanLogDao`, `AgentWhitelistDao`, `AgentSessionDao`, `ContestWinnerAdminDao` |

DTOs never cross into the DB layer; the signing key stays behind KMS/HSM.

---

## 4. Data model, collections & indexes

```mermaid
erDiagram
  CONTEST_ENTRIES ||--o{ EVENT_REDEMPTIONS : "winner (winnerInfo) redeems"
  EVENT_AGENT_WHITELIST ||--o| EVENT_AGENT_SESSIONS : opens
  EVENT_AGENT_SESSIONS ||--o{ EVENT_SCAN_LOGS : records
  EVENT_REDEMPTIONS { string eventId  string msisdn  string checkpoint  string deviceId  string scanRequestId  instant redeemedAt }
  EVENT_AGENT_WHITELIST { string eventId  string msisdn  set checkpoints  bool active }
  EVENT_AGENT_SESSIONS { string msisdn  string eventId  string checkpoint  bool revoked  instant expiresAt }
  EVENT_SCAN_LOGS { string scanRequestId  string customerMsisdn  string agentMsisdn  string callback  instant serverTs }
  CONTEST_ENTRIES { string programId  string msisdn  object winnerInfo }
```

| Collection | Key index | Purpose |
|---|---|---|
| `event_redemptions` | **unique** `(eventId, msisdn, checkpoint)`; unique sparse `scanRequestId` | exactly-once redemption + idempotency |
| `event_agent_whitelist` | **unique** `(eventId, msisdn)` | agent authority (events + checkpoints) |
| `event_agent_sessions` | `msisdn` | single-active scanning session |
| `event_scan_logs` | unique sparse `scanRequestId`; `customerMsisdn`, `agentMsisdn`, `eventId` | audit + idempotency + history API |
| `contest_entries` *(existing)* | `winnerInfo` presence + `programId` | winner source (read at API 4; **written** by API 5) |
| Aerospike `qr:latest:{msisdn}` | TTL = QR TTL | single-active QR pointer |

Unique indexes are declared on the documents (`@CompoundIndex` / `@Indexed(unique=true, sparse=true)`)
so Spring Data auto-creates them, same as `EntryDocument.orderId` in `contest`.

---

## 5. QR token

Compact signed JWS (ES256). Claims:

| Claim | Meaning |
|---|---|
| `ver` | schema version (unknown/greater ⇒ `INVALID_QR`) |
| `sub` | **opaque** (encrypted via `PiiEncryptionDecryption`) MSISDN — never raw PII |
| `dev` | customer `deviceId` (powers the duplicate vs other-device split) |
| `events` | won `programId`s (= eventIds), inside the signature |
| `jti` / `iat` / `exp` | single-active id / issued-at / `iat + «TTL»` |

**Two expiry gates:** the JWT `exp` (hard TTL) **and** the single-active `latestJti` pointer
(immediate supersede on refresh). Either failing → `QR_EXPIRED`. Signing key in KMS/HSM (`kid`
rotation); verified with the public key.

---

## 5A. QR image util — render & validate

The `qrToken` above is a **string**; §5 says nothing about how it becomes the *picture* in the
Thanks App. The image util (package `…​eventpass.util`) draws the **styled circular QR** shown in the
Figma — dotted modules under a radial gradient, rounded finder "eyes", a centre badge with the
Advantage-Club logo / changeable text — and reads one back. Styling never touches the encoded bits,
so any payload round-trips unchanged.

**What it carries.** The util is payload-agnostic: pass the signed membership `qrToken`, a deeplink
(`airtelthanks://…` / `https://…`), or any opaque info string as `data`. On scan the app decodes
`data` locally and POSTs it to the backend (e.g. API 3 `/v1/entry`), which is how a scan "publishes"
to the backend — the QR itself is only the carrier.

**Two halves.**

| Half | Class | Does |
|---|---|---|
| generate | `CircularQrGenerator` | `data` (+ resolved `Style`) → styled PNG / `data:image/png;base64,…`. ZXing encodes the bare module matrix (EC level **H**), Java2D paints dots + gradient + finder rings + centre badge. Stateless / thread-safe. |
| validate | `QrImageDecoder` | image bytes → payload string (ZXing decode, `TRY_HARDER`). `decode` throws `QrInvalidException` when unreadable; `tryDecode` returns `Optional`; `matches(bytes, expected)` asserts a clean round-trip. This is **structural** validation only — trust validation (signature / TTL / single-active) stays `QrTokenService.verify`. |

`QrImageService`(+impl) wraps both with the configured defaults and layers per-request overrides.

**Config — `eventpass.qr-style.*`** (`@RefreshScope`; hex `#RRGGBB` / `#AARRGGBB`, or `transparent`):

| Key | Default | Meaning |
|---|---|---|
| `size` | `720` | Output edge in px (square). |
| `quiet-zone-modules` | `2` | Quiet-zone modules around the code. |
| `background-color` | `#FFFFFF` | Canvas fill; `transparent` for overlay. |
| `module-shape` | `DOTS` | `DOTS` / `ROUNDED` / `SQUARE`. |
| `module-size-ratio` | `0.86` | Dot size vs cell (airy gaps < 1.0). |
| `gradient-enabled` | `true` | Radial gradient across the modules. |
| `gradient-inner-color` / `gradient-outer-color` | `#F5A623` / `#C8102E` | Centre → edge gradient stops. |
| `foreground-color` | `#C8102E` | Flat module colour when gradient off. |
| `styled-finder` / `finder-corner-ratio` / `finder-color` | `true` / `0.35` / `#C8102E` | Rounded concentric "eyes". |
| `center-badge-enabled` / `center-badge-ratio` | `true` / `0.24` | Centre disc (needs EC H). |
| `center-badge-inner-color` / `center-badge-outer-color` | `#E4002B` / `#8B0000` | Badge gradient. |
| `center-ring-*` | `true` / `#FFFFFF` / `0.04` | White separator ring. |
| `center-text` | `airtel\nPOSTPAID\nADVANTAGE\nCLUB` | Stacked lines; first is the brand line. **Changeable per request** via `QrRenderRequest.centerText`. |
| `center-text-color` / `center-text-font` | `#FFFFFF` / `SansSerif` | Centre text style. |
| `center-logo-resource` | *(unset)* | Optional `classpath:…` logo drawn in the badge. |
| `error-correction` | `H` | L/M/Q/H — keep **H** while a centre badge covers the middle. |

```yaml
# application.yml (User Profile Service)
eventpass:
  qr-style:
    size: 720
    module-shape: DOTS
    gradient-inner-color: "#F5A623"
    gradient-outer-color: "#C8102E"
    finder-color: "#C8102E"
    center-badge-inner-color: "#E4002B"
    center-badge-outer-color: "#8B0000"
    center-text: "airtel\nPOSTPAID\nADVANTAGE\nCLUB"
    center-text-color: "#FFFFFF"
    error-correction: H
```

**API surface** (`MembershipQrImageController`, util endpoints — member QR string is still API 4):

| Endpoint | Body / param | Returns |
|---|---|---|
| `POST /v1/membership/qr/image` | `QrRenderRequest` (`data` required; optional `centerText`, colour & `size` overrides) | `QrRenderResponse` — `imageDataUri`, `width/height`, `encoded` |
| `POST /v1/membership/qr/image.png` | `QrRenderRequest` | raw `image/png` |
| `POST /v1/membership/qr/validate-image` | multipart `image` | `{ "data": "<decoded payload>" }` |

**pom.xml**

```xml
<dependency>
  <groupId>com.google.zxing</groupId>
  <artifactId>core</artifactId>
  <version>3.5.3</version>
</dependency>
<dependency>
  <groupId>com.google.zxing</groupId>
  <artifactId>javase</artifactId>
  <version>3.5.3</version>
</dependency>
```

---

## 6. Callback contract (API 3)

| Callback | admit | color | resumes | Meaning |
|---|:---:|---|:---:|---|
| `ENTRY_ALLOWED` | ✅ | green | yes | first valid scan at checkpoint |
| `DUPLICATE_ENTRY` | ❌ | red | yes | repeat, same device |
| `ALREADY_ENTERED_OTHER_DEVICE` | ❌ | red | yes | repeat, different device (returns first deviceId) |
| `NOT_ENTITLED` | ❌ | red | yes | `session.eventId ∉ token.events` |
| `QR_EXPIRED` | ❌ | grey | yes | past TTL or superseded |
| `INVALID_QR` | ❌ | red | yes | malformed/forged/unsupported |
| `STAFF_SESSION_INVALID` | ❌ | red | **no** | session missing/revoked/expired/mismatch |
| `SERVICE_UNAVAILABLE` | ❌ | grey | yes | unexpected fault — never auto-allow |

Every entry decision returns **HTTP 200 + callback**; only unexpected faults map to `SERVICE_UNAVAILABLE`.

---

## 7. API surface

All endpoints are on the **User Profile Service**. "Owning component" names the internal module.
The **agent whitelist is a full admin CRUD** (POST/GET/PUT/DELETE); **agent validation is a single
API** (validate + open session); the **membership QR has generate / validate (get-or-create) /
refresh**.

| # | Method / Endpoint | Owning component | Caller | Key inputs | Success output |
|---|---|---|---|---|---|
| 1a | `POST /v1/agents/whitelist` | Agent Whitelist | Admin/eng | `msisdn`, `eventId`, `checkpoints[]`, `active?` | `{whitelistId, status}` |
| 1b | `GET /v1/agents/whitelist?eventId=&msisdn=` | Agent Whitelist | Admin/eng | `eventId`, `msisdn?` | `[{eventId, msisdn, checkpoints[], active}]` |
| 1c | `PUT /v1/agents/whitelist` | Agent Whitelist | Admin/eng | `eventId`, `msisdn`, `checkpoints?`, `active?` | updated row |
| 1d | `DELETE /v1/agents/whitelist?eventId=&msisdn=` | Agent Whitelist | Admin/eng | `eventId`, `msisdn` | `{status:"DELETED"}` |
| 2 | `GET /v1/agents/validate` | Agent Whitelist & Session | Thanks App (agent) | agent `msisdn` (`IV_USER`) | `{authorized, events[], agentSessionId}` |
| 3 | `POST /v1/entry` | Entry Validation | Thanks App (agent) | `qrToken`, `eventId`, `checkpoint`, `scanRequestId` (+ `X-Agent-Session`) | callback |
| 4a | `POST /v1/membership/qr` | QR Generation | Thanks App (customer) | `deviceId`, `timestamp` (+ `IV_USER`) | `{qrToken, expiresAt}` (always new) |
| 4b | `POST /v1/membership/qr/validate` | QR Generation | Thanks App (customer) | `deviceId` (+ `IV_USER`) | cached live QR if present, else new |
| 4c | `POST /v1/membership/qr/refresh` | QR Generation | Thanks App (customer) | `deviceId` (+ `IV_USER`) | new QR (supersedes) |
| 5 | `POST /v1/admin/winners` | Contest (winner write) | Admin/eng | `eventId`, `msisdn`, `rank?`, `drawId?` | `{entriesUpdated, status}` |
| — | `GET /v1/admin/scan-history?msisdn=` | Entry Validation | Admin/eng | `msisdn` | chronological scan log |

**API → class map**

| API | Controller | Service | Persistence |
|---|---|---|---|
| 1a create | `AgentController.createWhitelist` | `AgentAccessService.upsertWhitelist` | `AgentWhitelistDao.upsert` |
| 1b read | `AgentController.getWhitelist` | `AgentAccessService.getWhitelist` | `AgentWhitelistDao.findOne`/`findByEvent` |
| 1c update | `AgentController.updateWhitelist` | `AgentAccessService.updateWhitelist` | `AgentWhitelistDao.update` |
| 1d delete | `AgentController.deleteWhitelist` | `AgentAccessService.deleteWhitelist` | `AgentWhitelistDao.delete` |
| 2 | `AgentController.validate` | `AgentAccessService.validate` (validates + opens session) | `AgentWhitelistDao`, `AgentSessionDao` |
| 3 | `EventEntryController` | `EventEntryService.recordEntry` | `EventRedemptionDao` + `ScanLogDao` |
| 4a/4b/4c | `MembershipQrController` | `MembershipQrService.generate` / `validateOrGenerate` / `refresh` | `WinnerLookupService` (read) + `QrTokenService` + `QrIssuanceStore` (get-or-create) |
| 5 | `WinnerAdminController` | `WinnerAdminService.markWinner` | `ContestWinnerAdminDao` (write `winnerInfo`) |

**Request/response contracts**

```
API 1a POST   /v1/agents/whitelist            body { msisdn, eventId, checkpoints[], active? }
                                              -> 200 { whitelistId, status:"UPSERTED" }
API 1b GET    /v1/agents/whitelist?eventId=&msisdn=   (msisdn optional → all rows for the event)
                                              -> 200 [ { eventId, msisdn, checkpoints[], active, updatedAt } ]
API 1c PUT    /v1/agents/whitelist            body { eventId, msisdn, checkpoints?, active? }
                                              -> 200 { eventId, msisdn, checkpoints[], active }   (400 if absent)
API 1d DELETE /v1/agents/whitelist?eventId=&msisdn=
                                              -> 200 { eventId, msisdn, status:"DELETED" }        (400 if absent)
API 2  GET    /v1/agents/validate             (IV_USER = agent msisdn)   // validates AND opens the session
                                              -> { authorized, events:[{eventId,name?,venue?,checkpoints[]}], agentSessionId }
API 3  POST   /v1/entry                       Header X-Agent-Session; body { qrToken, eventId, checkpoint, scanRequestId }
                                              -> 200 { callback, admit, displayColor, message, holderMasked?, firstClaimAt?, otherDeviceId? }
API 4a POST   /v1/membership/qr               Header IV_USER; body { deviceId, timestamp }   // always new
                                              -> 200 { qrToken, expiresAt }        (else 400 non-member)
API 4b POST   /v1/membership/qr/validate      Header IV_USER; body { deviceId }     // cached-if-live else new
                                              -> 200 { qrToken, expiresAt }
API 4c POST   /v1/membership/qr/refresh       Header IV_USER; body { deviceId }     // force new
                                              -> 200 { qrToken, expiresAt }
API 5  POST   /v1/admin/winners               Header IV_USER; body { eventId, msisdn, rank?, drawId? }
                                              -> 200 { eventId, msisdn, entriesUpdated, status:"WINNER_MARKED" }  (400 if no entry)
```

---

## 8. API sequences & conditions

### API 1 — Whitelist agent (admin)
Idempotent upsert on `(eventId, msisdn)`; one MSISDN may serve many events; mid-event appends supported.

### API 2 — Validate agent + open session (single call; no OTP)
```mermaid
sequenceDiagram
  autonumber
  participant App as Thanks App (agent)
  participant UPS as User Profile Service
  participant DB as whitelist / sessions
  App->>UPS: GET /v1/agents/validate (IV_USER = agent msisdn)
  UPS->>DB: active whitelist rows for msisdn
  alt authorized
    UPS->>DB: revoke prior sessions; insert agent_session (per-agent, TTL 24h)
    UPS-->>App: { authorized:true, events[], agentSessionId }
  else not an agent
    UPS-->>App: { authorized:false }   (no session)
  end
  Note over App: agent picks event + checkpoint per scan (sent in the entry body)
```

### API 3 — Entry after scan (the gate decision)
Ordered conditions (short-circuit on first match):

| Step | Condition | Result |
|---|---|---|
| 0 | `scanRequestId` already logged | replay stored callback (idempotent) |
| 1–2 | session invalid, or agent not whitelisted for `(request.eventId, checkpoint)` | `STAFF_SESSION_INVALID` |
| 3 | signature/version bad, unresolvable subject | `INVALID_QR` |
| 4 | past TTL or superseded | `QR_EXPIRED` |
| 5 | `request.eventId ∉ token.events` | `NOT_ENTITLED` |
| 6a | redeem inserted (won race) | `ENTRY_ALLOWED` |
| 6b | already redeemed, same device | `DUPLICATE_ENTRY` (+ firstClaimAt) |
| 6c | already redeemed, other device | `ALREADY_ENTERED_OTHER_DEVICE` (+ otherDeviceId) |
| 7 | (always) write `event_scan_logs` | audit |
| — | any exception | `SERVICE_UNAVAILABLE` (never auto-allow) |

```mermaid
sequenceDiagram
  autonumber
  participant App as Thanks App (agent)
  participant EVS as Entry Validation
  participant Lg as event_scan_logs
  participant Ag as Agent Session
  participant Tk as QR Token
  participant Rd as event_redemptions
  App->>EVS: POST /v1/entry {qrToken, eventId, checkpoint, scanRequestId} (X-Agent-Session)
  EVS->>Lg: findByScanRequestId
  alt already logged
    EVS-->>App: replay(callback)
  else new
    EVS->>Ag: requireAuthorizedSession(sessionId, eventId, checkpoint)
    alt invalid / not whitelisted
      EVS-->>App: STAFF_SESSION_INVALID
    else ok
      EVS->>Tk: verify(qrToken)
      alt invalid/expired
        EVS-->>App: INVALID_QR / QR_EXPIRED
      else claims ok
        alt request.eventId ∉ events
          EVS-->>App: NOT_ENTITLED
        else winner
          EVS->>Rd: tryRedeem(eventId,msisdn,checkpoint,deviceId,...)
          alt first claim
            EVS-->>App: ENTRY_ALLOWED
          else already claimed
            EVS-->>App: DUPLICATE_ENTRY / ALREADY_ENTERED_OTHER_DEVICE
          end
        end
      end
    end
    EVS->>Lg: save(callback)
  end
```

### API 4a — Generate QR (customer) — always mint
```mermaid
sequenceDiagram
  autonumber
  participant App as Thanks App (customer)
  participant UPS as User Profile Service
  participant CE as contest_entries
  participant KMS as KMS/HSM
  participant AS as Aerospike (active-QR cache)
  App->>UPS: POST /v1/membership/qr { deviceId, timestamp }  (IV_USER)
  UPS->>UPS: eligibility check (member?) else 400
  UPS->>CE: programIds where msisdn has winnerInfo
  CE-->>UPS: wonEventIds[]
  UPS->>KMS: sign { sub=enc(msisdn), dev, events, jti, iat, exp }
  UPS->>AS: store CachedQr{jti, token, deviceId, expiresAt} (TTL, single-active)
  UPS-->>App: { qrToken, expiresAt }
```

### API 4b — Validate QR (get-or-create): return cached if present in Aerospike, else create
```mermaid
sequenceDiagram
  autonumber
  participant App as Thanks App (customer)
  participant UPS as User Profile Service
  participant AS as Aerospike (active-QR cache)
  App->>UPS: POST /v1/membership/qr/validate { deviceId }  (IV_USER)
  UPS->>UPS: eligibility check (member?) else 400
  UPS->>AS: getActive(msisdn)
  alt cached & same device & not expired
    AS-->>UPS: CachedQr{token, expiresAt}
    UPS-->>App: { qrToken, expiresAt }   // returned as-is, no re-mint
  else miss / expired / different device
    UPS->>UPS: generate (mint new + cache) — see 4a
    UPS-->>App: { qrToken, expiresAt }
  end
```

### API 4c — Refresh QR — force new
`POST /v1/membership/qr/refresh` → `MembershipQrService.refresh` → mints a fresh QR (same as 4a),
superseding the cached one. Use when the customer taps **Refresh** (or after a `QR_EXPIRED` at the gate).

### API 5 — Mark/update winner (admin) — writes `contest_entries.winnerInfo`

| # | Condition | Outcome |
|---|---|---|
| 1 | `eventId`/`msisdn` blank | 400 |
| 2 | ≥1 entry for `(programId=eventId, msisdn)` | set `winnerInfo{rank?, drawId?, createdAt}` → `{entriesUpdated, WINNER_MARKED}` |
| 3 | no matching entry (never played) | 400 — do not fabricate an entry |
| 4 | already a winner | idempotent — overwrite rank/drawId |

```mermaid
sequenceDiagram
  autonumber
  participant Ad as Admin
  participant WA as Winner Admin
  participant M as contest_entries
  Ad->>WA: POST /v1/admin/winners { eventId, msisdn, rank?, drawId? }
  WA->>WA: build WinnerInfo{rank, drawId, createdAt}
  WA->>M: updateMulti(programId==eventId, msisdn) set winnerInfo
  alt matched >= 1
    WA-->>Ad: { entriesUpdated, WINNER_MARKED }
  else 0
    WA-->>Ad: 400 (no entry to mark)
  end
  Note over Ad,M: Picked up in the customer's next QR (API 4 reads winnerInfo)
```

**Effect chain:** API 5 writes `winnerInfo` → API 4 embeds the event in the QR on next refresh →
API 3 admits at the gate.

---

## 8A. Sample requests, responses & error responses (per API)

> **Envelope.** All responses use the shared `com.airtel.core.dto.genericResponse.Response<T>`
> wrapper: a success carries the payload under `data`; a failure carries `error.code` +
> `error.message` and the HTTP status. The envelope field names below (`successful`, `data`,
> `error`) follow that shared class; the **payloads** are the DTOs defined in this LLD. Bodies are
> `application/json`. `IV_USER` = the caller's authenticated MSISDN.

### API 1 — `POST /v1/agents/whitelist` (admin)

**Request**
```http
POST /v1/agents/whitelist
IV_USER: 9812300000            # actor (engineering)
Content-Type: application/json

{ "eventId": "ARTLPPAZK", "msisdn": "7023398743", "checkpoints": ["ENTRY", "GOODIE"] }
```
**Success — 200**
```json
{ "successful": true, "data": { "whitelistId": "6f2e1c40-...", "status": "UPSERTED" } }
```
**Errors**

| HTTP | When | Body |
|---|---|---|
| 400 | missing/blank field, empty `checkpoints` | `{ "successful": false, "error": { "code": "bad_request", "message": "checkpoints must not be empty" } }` |
| 400 | unknown checkpoint value | `{ "successful": false, "error": { "code": "bad_request", "message": "Unsupported checkpoint: VIP" } }` |
| 401/403 | caller not engineering (enforced upstream) | `{ "successful": false, "error": { "code": "forbidden", "message": "Not authorized" } }` |

### API 2 — `GET /v1/agents/validate` (agent) — validates **and** opens the session

**Request**
```http
GET /v1/agents/validate
IV_USER: 7000000001            # agent msisdn (from app auth)
```
**Success — 200 (authorized — events + a session, in one call)**
```json
{ "successful": true,
  "data": { "authorized": true,
            "agentSessionId": "sess-3f9ac2b1-...",
            "events": [ { "eventId": "ARTLPPAZK", "eventName": "Advantage Club Live", "venue": "Delhi", "checkpoints": ["ENTRY","GOODIE"] },
                        { "eventId": "ARTLXYZ12", "checkpoints": ["GOODIE"] } ] } }
```
**Success — 200 (not an event agent — no event data, no session)**
```json
{ "successful": true, "data": { "authorized": false } }
```
The agent picks an event + checkpoint in the UI and sends them on each scan (API 3); a new
`validate` call revokes any prior session for the MSISDN (single-active).

### API 3 — `POST /v1/entry` (agent) — every decision is HTTP 200 + callback

**Request**
```http
POST /v1/entry
X-Agent-Session: sess-3f9ac2b1-...
Content-Type: application/json

{ "qrToken": "eyJraWQiOiJrMSIsImFsZyI6IkVTMjU2In0...", "eventId": "ARTLPPAZK", "checkpoint": "ENTRY", "scanRequestId": "7b3d9e2a-..." }
```
**Success — 200 (`ENTRY_ALLOWED`)**
```json
{ "successful": true,
  "data": { "callback": "ENTRY_ALLOWED", "admit": true, "displayColor": "green",
            "message": "Entry allowed. Customer admitted.", "holderMasked": "***** 8743" } }
```
**Deny / exception decisions — also HTTP 200** (the scanner always parses a callback):

| `callback` | admit | Example `data` |
|---|:---:|---|
| `DUPLICATE_ENTRY` | false | `{ "callback":"DUPLICATE_ENTRY","admit":false,"displayColor":"red","message":"Already claimed on this device.","firstClaimAt":"2026-09-28T09:40:12Z" }` |
| `ALREADY_ENTERED_OTHER_DEVICE` | false | `{ "callback":"ALREADY_ENTERED_OTHER_DEVICE","admit":false,"displayColor":"red","message":"Already claimed on another device.","firstClaimAt":"2026-09-28T09:40:12Z","otherDeviceId":"a1b2-first-device" }` |
| `NOT_ENTITLED` | false | `{ "callback":"NOT_ENTITLED","admit":false,"displayColor":"red","message":"Member is not a winner for this event.","holderMasked":"***** 8743" }` |
| `QR_EXPIRED` | false | `{ "callback":"QR_EXPIRED","admit":false,"displayColor":"grey","message":"QR expired. Ask the customer to refresh and re-present." }` |
| `INVALID_QR` | false | `{ "callback":"INVALID_QR","admit":false,"displayColor":"red","message":"Invalid QR. Ask the customer to open it from the Airtel app." }` |
| `STAFF_SESSION_INVALID` | false | `{ "callback":"STAFF_SESSION_INVALID","admit":false,"displayColor":"red","message":"Session expired. Re-open the scanner to continue." }` |
| `SERVICE_UNAVAILABLE` | false | `{ "callback":"SERVICE_UNAVAILABLE","admit":false,"displayColor":"grey","message":"Service error. Retry the scan." }` |

Full body for a deny, e.g. `NOT_ENTITLED`:
```json
{ "successful": true,
  "data": { "callback": "NOT_ENTITLED", "admit": false, "displayColor": "red",
            "message": "Member is not a winner for this event.", "holderMasked": "***** 8743" } }
```
**True HTTP errors** (request never reached a decision):

| HTTP | When | Body |
|---|---|---|
| 400 | missing `qrToken` / `eventId` / `checkpoint` / `scanRequestId` | `{ "successful": false, "error": { "code": "bad_request", "message": "qrToken must not be blank" } }` |
| 400 | missing `X-Agent-Session` header | `{ "successful": false, "error": { "code": "bad_request", "message": "Required header 'X-Agent-Session' is not present" } }` |

> Note: a revoked/expired session is **not** a 4xx — it returns 200 `STAFF_SESSION_INVALID` so the
> scanner renders the "re-open" screen. `SERVICE_UNAVAILABLE` is likewise 200 (never auto-allow).

### API 4 — `POST /v1/membership/qr` (customer)

**Request**
```http
POST /v1/membership/qr
IV_USER: 7023398743
Content-Type: application/json

{ "deviceId": "a1b2c3d4-stable-install-id", "timestamp": 1790000000000 }
```
**Success — 200**
```json
{ "successful": true,
  "data": { "qrToken": "eyJraWQiOiJrMSIsImFsZyI6IkVTMjU2In0.eyJzdWIiOiJ...opaque...",
            "expiresAt": "2026-09-28T10:35:00Z" } }
```
(The customer may have won zero events — the QR is still issued with an empty `events[]`; any gate then returns `NOT_ENTITLED`.)

**Errors**

| HTTP | When | Body |
|---|---|---|
| 400 | not an Advantage Club member | `{ "successful": false, "error": { "code": "bad_request", "message": "Not an Advantage Club member" } }` |
| 400 | missing/blank `deviceId` | `{ "successful": false, "error": { "code": "bad_request", "message": "deviceId must not be blank" } }` |

### API 5 — `POST /v1/admin/winners` (admin) — mark/update winner

**Request**
```http
POST /v1/admin/winners
IV_USER: 9812300000            # actor
Content-Type: application/json

{ "eventId": "ARTLPPAZK", "msisdn": "7023398743", "rank": 1, "drawId": "draw-2026-09-28" }
```
**Success — 200**
```json
{ "successful": true,
  "data": { "eventId": "ARTLPPAZK", "msisdn": "7023398743", "entriesUpdated": 1, "status": "WINNER_MARKED" } }
```
**Errors**

| HTTP | When | Body |
|---|---|---|
| 400 | customer has **no** contest entry for this event (never played) | `{ "successful": false, "error": { "code": "bad_request", "message": "No contest entry found for msisdn in event ARTLPPAZK; cannot mark winner" } }` |
| 400 | missing/blank `eventId` or `msisdn` | `{ "successful": false, "error": { "code": "bad_request", "message": "eventId must not be blank" } }` |

---

## 8B. curl — whitelist CRUD & QR validate/refresh

`$BASE` = service base URL (e.g. `https://userprofile.internal`).

**Whitelist — CREATE (POST)**
```bash
curl -sS -X POST "$BASE/v1/agents/whitelist" \
  -H "IV_USER: 9812300000" -H "Content-Type: application/json" \
  -d '{ "eventId":"ARTLPPAZK", "msisdn":"7000000001", "checkpoints":["ENTRY","GOODIE"] }'
# 200 { "successful": true, "data": { "whitelistId":"6f2e...", "status":"UPSERTED" } }
```
**Whitelist — READ (GET one, or all rows for an event)**
```bash
# one row
curl -sS "$BASE/v1/agents/whitelist?eventId=ARTLPPAZK&msisdn=7000000001" -H "IV_USER: 9812300000"
# all rows for the event (omit msisdn)
curl -sS "$BASE/v1/agents/whitelist?eventId=ARTLPPAZK" -H "IV_USER: 9812300000"
# 200 { "successful": true, "data": [ { "eventId":"ARTLPPAZK","msisdn":"7000000001","checkpoints":["ENTRY","GOODIE"],"active":true,"updatedAt":"2026-09-28T09:00:00Z" } ] }
# 400 (get one, not found) { "successful": false, "error": { "code":"bad_request","message":"No whitelist row for event ARTLPPAZK / msisdn 7000000001" } }
```
**Whitelist — UPDATE (PUT)** — change checkpoints and/or deactivate
```bash
curl -sS -X PUT "$BASE/v1/agents/whitelist" \
  -H "IV_USER: 9812300000" -H "Content-Type: application/json" \
  -d '{ "eventId":"ARTLPPAZK", "msisdn":"7000000001", "checkpoints":["GOODIE"], "active":true }'
# 200 { "successful": true, "data": { "eventId":"ARTLPPAZK","msisdn":"7000000001","checkpoints":["GOODIE"],"active":true } }
# 400 (absent) { "successful": false, "error": { "code":"bad_request","message":"No whitelist row to update ..." } }
```
**Whitelist — DELETE**
```bash
curl -sS -X DELETE "$BASE/v1/agents/whitelist?eventId=ARTLPPAZK&msisdn=7000000001" -H "IV_USER: 9812300000"
# 200 { "successful": true, "data": { "eventId":"ARTLPPAZK","msisdn":"7000000001","status":"DELETED" } }
# 400 (absent) { "successful": false, "error": { "code":"bad_request","message":"No whitelist row to delete ..." } }
```

**QR — VALIDATE (get-or-create)** — returns the cached live QR if present, else mints a new one
```bash
curl -sS -X POST "$BASE/v1/membership/qr/validate" \
  -H "IV_USER: 7023398743" -H "Content-Type: application/json" \
  -d '{ "deviceId":"a1b2c3d4-stable-install-id" }'
# 200 { "successful": true, "data": { "qrToken":"eyJraWQiOiJrMSIsImFsZyI6IkVTMjU2In0...", "expiresAt":"2026-09-28T10:35:00Z" } }
# 400 (non-member) { "successful": false, "error": { "code":"bad_request","message":"Not an Advantage Club member" } }
```
**QR — REFRESH (force new)**
```bash
curl -sS -X POST "$BASE/v1/membership/qr/refresh" \
  -H "IV_USER: 7023398743" -H "Content-Type: application/json" \
  -d '{ "deviceId":"a1b2c3d4-stable-install-id" }'
# 200 { "successful": true, "data": { "qrToken":"<new opaque token>", "expiresAt":"2026-09-28T10:40:00Z" } }
```
**QR — GENERATE (always new)** and the other flows, for reference
```bash
curl -sS -X POST "$BASE/v1/membership/qr" -H "IV_USER: 7023398743" \
  -H "Content-Type: application/json" -d '{ "deviceId":"a1b2c3d4-stable-install-id","timestamp":1790000000000 }'

curl -sS "$BASE/v1/agents/validate" -H "IV_USER: 7000000001"     # validate + open session

curl -sS -X POST "$BASE/v1/entry" -H "X-Agent-Session: sess-3f9ac2b1-..." \
  -H "Content-Type: application/json" \
  -d '{ "qrToken":"eyJ...","eventId":"ARTLPPAZK","checkpoint":"ENTRY","scanRequestId":"7b3d9e2a-..." }'

curl -sS -X POST "$BASE/v1/admin/winners" -H "IV_USER: 9812300000" \
  -H "Content-Type: application/json" \
  -d '{ "eventId":"ARTLPPAZK","msisdn":"7023398743","rank":1,"drawId":"draw-2026-09-28" }'
```

---

## 9. Atomic redemption — exactly-once

**Chosen store: MongoDB.** The redeem is an **insert guarded by the unique compound index**
`(eventId, msisdn, checkpoint)` — the DB, not app logic, is the concurrency guarantee (no
read-then-write window). Same `DuplicateKeyException` pattern `contest` uses for `orderId`.

```java
// EventRedemptionDaoImpl.tryRedeem
try {
    mongoTemplate.insert(redemption);            // unique (eventId, msisdn, checkpoint)
    return new RedeemOutcome(true, redemption);  // inserted → ENTRY_ALLOWED
} catch (DuplicateKeyException dup) {
    var existing = find(eventId, msisdn, checkpoint).orElseThrow(() -> dup);
    return new RedeemOutcome(false, existing);   // conflict → device split from existing.deviceId
}
```

| Scenario | Result |
|---|---|
| First scan | insert succeeds → `ENTRY_ALLOWED` |
| Repeat, same device | conflict → `DUPLICATE_ENTRY` |
| Repeat, different device | conflict → `ALREADY_ENTERED_OTHER_DEVICE` (+ first deviceId) |
| Two devices simultaneously | exactly one insert wins → one admit |
| ENTRY vs GOODIE | different `checkpoint` → different row → each redeems once |

---

## 10. Winner read & write (contest reuse)

A winner is a `contest_entries` document whose **`winnerInfo`** is set (as `DrawServiceImpl` marks
winners); a live **event = contest `programId`**.

- **Read** (`WinnerLookupService`): `findWonEventIds(msisdn)` (build token `events[]` at API 4) and
  `isWinner(msisdn, eventId)` (optional re-check at entry).
- **Write** (`WinnerAdminService` + `ContestWinnerAdminDao`, API 5): `updateMulti(programId==eventId,
  msisdn) set winnerInfo`; **never creates** an entry (400 if the customer never played).

No new winner store; the only write to `contest_entries` is the API 5 override.

---

## 11. Idempotency, exceptions, config

**Idempotency** — `scanRequestId` is the key. API 3 first checks `event_scan_logs.findByScanRequestId`
and replays a prior terminal result; the `event_redemptions.scanRequestId` unique index makes a
crash between redeem-commit and response safe (retry returns the original `ENTRY_ALLOWED`, never a
second admit). `SERVICE_UNAVAILABLE` is not terminal → a genuine retry re-runs the chain. Contract:
the scanner reuses one `scanRequestId` per decoded QR.

**Exception → HTTP / callback**

| Source | Result |
|---|---|
| `QrInvalid` / `QrExpired` / `AgentSessionInvalid` (entry path) | 200 `INVALID_QR` / `QR_EXPIRED` / `STAFF_SESSION_INVALID` |
| any other exception (entry path) | 200 `SERVICE_UNAVAILABLE` |
| `AgentSessionInvalidException` (open session) | 401 |
| `IllegalArgumentException` (bad input / non-member / no entry to mark) | 400 |

**Config** (`eventpass.*`, `@RefreshScope`): `qrTtlSeconds=300` (shared by API 3 & 4),
`agentSessionTtlSeconds=86400`, `tokenVersion=1`, `issuer`, `signingKeyId`. QR **image style** is a
separate `@RefreshScope` block `eventpass.qr-style.*` (see §5A) — colours, module shape, centre text —
so branding is retuned without a redeploy.

**Platform wiring to confirm:** (1) **jjwt** 0.12.x in `pom.xml`; (2) `@Configuration` KMS/HSM
`PrivateKey`/`PublicKey` beans; (3) `MembershipEligibilityService` → existing eligibility bean;
(4) `AerospikeDetails.EVENT_QR_LATEST` + TTL-aware `putDetails`; (5) event name/venue enrichment (optional);
(6) **ZXing** for the image util — `com.google.zxing:core` (encode) and `com.google.zxing:javase`
(decode / `BufferedImageLuminanceSource`), both 3.5.x, in `pom.xml`.

---

## 12. Module map (all files)

Every file is **new** under `com.airtel.userprofile.eventpass`; the `contest` module is not modified
(read for the winner check, `winnerInfo` written by API 5).

| Layer | Files |
|---|---|
| enums | `Checkpoint`, `EntryCallback` |
| document | `EventRedemptionDocument`, `AgentWhitelistDocument`, `AgentSessionDocument`, `ScanLogDocument` |
| dto/request | `QrGenerateRequest`, `EntryScanRequest`, `WhitelistUpsertRequest`, `WinnerUpsertRequest`, `QrRenderRequest` |
| dto/response | `QrGenerateResponse`, `EntryScanResponse`, `AgentValidateResponse`, `AgentEventAccess`, `AgentWhitelistResponse`, `QrRenderResponse` |
| dao | `EventRedemptionDao`(+impl), `RedeemOutcome`, `ScanLogDao`(+impl), `AgentWhitelistDao`(+impl), `AgentSessionDao`(+impl), `ContestWinnerAdminDao`(+impl) |
| service | `MembershipQrService`(+impl), `EventEntryService`(+impl), `AgentAccessService`(+impl), `WinnerLookupService`(+impl), `WinnerAdminService`(+impl), `QrTokenService`(+impl), `QrIssuanceStore`(+impl, caches `CachedQr`), `MembershipEligibilityService`, `QrClaims`, `CachedQr`, `QrImageService`(+impl) |
| util | `CircularQrGenerator` (render styled circular QR), `QrImageDecoder` (decode/validate QR image), `HexColors` (hex→`Color` parsing) |
| controller | `MembershipQrController`, `MembershipQrImageController`, `AgentController`, `EventEntryController`, `WinnerAdminController` |
| exception | `QrInvalidException`, `QrExpiredException`, `AgentSessionInvalidException`, `EventPassExceptionHandler` |
| converter | `CheckpointConverter` |
| config | `EventPassProperties`, `QrStyleProperties` |

---

## 13. Code changes (full source)

The complete reference implementation follows, grouped by layer. Drop into
`src/main/java/com/airtel/userprofile/eventpass/` in the User Profile Service.




### Enums

#### `com/airtel/userprofile/eventpass/enums/Checkpoint.java`

```java
package com.airtel.userprofile.eventpass.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * The two ingresses at a live Advantage Club event. Each is an independent, one-time redemption
 * per (event, customer): a winner is admitted once at {@link #ENTRY} and collects once at
 * {@link #GOODIE}; order does not matter and one does not consume the other.
 */
public enum Checkpoint {

	ENTRY("entry"),
	GOODIE("goodie");

	private final String value;

	Checkpoint(String value) {
		this.value = value;
	}

	@JsonValue
	public String getValue() {
		return value;
	}

	@JsonCreator
	public static Checkpoint fromValue(String value) {
		if (value == null || value.isBlank()) {
			throw new IllegalArgumentException("checkpoint is required");
		}
		String normalized = value.trim();
		for (Checkpoint c : values()) {
			if (c.value.equalsIgnoreCase(normalized) || c.name().equalsIgnoreCase(normalized)) {
				return c;
			}
		}
		throw new IllegalArgumentException("Unsupported checkpoint: " + value);
	}
}
```

#### `com/airtel/userprofile/eventpass/enums/EntryCallback.java`

```java
package com.airtel.userprofile.eventpass.enums;

import lombok.Getter;

/**
 * Authoritative decision codes returned to the agent scanner (Thanks App, agent mode).
 * Only {@link #ENTRY_ALLOWED} admits. {@code color} and {@code admit} drive the result screen;
 * every code also carries explicit text (accessibility — never colour alone).
 */
@Getter
public enum EntryCallback {

	ENTRY_ALLOWED("green", true, true, "Entry allowed. Customer admitted."),
	DUPLICATE_ENTRY("red", false, true, "Already claimed on this device."),
	ALREADY_ENTERED_OTHER_DEVICE("red", false, true, "Already claimed on another device."),
	NOT_ENTITLED("red", false, true, "Member is not a winner for this event."),
	QR_EXPIRED("grey", false, true, "QR expired. Ask the customer to refresh and re-present."),
	INVALID_QR("red", false, true, "Invalid QR. Ask the customer to open it from the Airtel app."),
	STAFF_SESSION_INVALID("red", false, false, "Session expired. Re-open the scanner to continue."),
	SERVICE_UNAVAILABLE("grey", false, true, "Service error. Retry the scan.");

	private final String color;
	private final boolean admit;
	private final boolean scannerResumes;
	private final String defaultMessage;

	EntryCallback(String color, boolean admit, boolean scannerResumes, String defaultMessage) {
		this.color = color;
		this.admit = admit;
		this.scannerResumes = scannerResumes;
		this.defaultMessage = defaultMessage;
	}
}
```

### Documents (Mongo collections)

#### `com/airtel/userprofile/eventpass/document/AgentSessionDocument.java`

```java
package com.airtel.userprofile.eventpass.document;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

/**
 * An active agent scanning session, opened by the single {@code GET /v1/agents/validate} call. It
 * is per-agent (not bound to one event/checkpoint) — the agent may scan any (event, checkpoint) it
 * is whitelisted for, checked live per scan. Single-active per msisdn: opening a new session
 * revokes prior non-expired ones. Identity is already proven by the Thanks App login.
 */
@Data
@Document(collection = "event_agent_sessions")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AgentSessionDocument {

	@Id
	private String id;

	@Indexed
	private String msisdn;
	private boolean revoked;
	private Instant createdAt;
	private Instant expiresAt;
	private String deviceInfo;
}
```

#### `com/airtel/userprofile/eventpass/document/AgentWhitelistDocument.java`

```java
package com.airtel.userprofile.eventpass.document;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import org.springframework.data.mongodb.core.index.CompoundIndexes;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.Set;

/**
 * Which events, and which checkpoints, an agent MSISDN may scan. One agent MSISDN can hold many
 * rows (one per event). {@code checkpoints} is the set the agent is authorized for at that event —
 * {@code ENTRY} only, {@code GOODIE} only, or both. Loaded/appended by engineering (admin API 1).
 */
@Data
@Document(collection = "event_agent_whitelist")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
@CompoundIndexes({
		@CompoundIndex(name = "uq_event_agent", def = "{'eventId': 1, 'msisdn': 1}", unique = true)
})
public class AgentWhitelistDocument {

	@Id
	private String id;

	private String eventId;
	private String msisdn;
	private Set<Checkpoint> checkpoints;
	private boolean active;
	private String createdBy;
	private Instant createdAt;
	private Instant updatedAt;
}
```

#### `com/airtel/userprofile/eventpass/document/EventRedemptionDocument.java`

```java
package com.airtel.userprofile.eventpass.document;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import org.springframework.data.mongodb.core.index.CompoundIndexes;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

/**
 * The exactly-once anchor for event entry / goodie redemption.
 *
 * <p>One row exists per successful redemption. The unique compound index
 * {@code (eventId, msisdn, checkpoint)} is what makes redemption atomic: two concurrent scans of
 * the same QR at the same checkpoint both try to insert this key, exactly one wins, the other gets
 * a {@link org.springframework.dao.DuplicateKeyException} — the same pattern the contest module
 * uses for {@code orderId} uniqueness on {@code contest_entries}.
 *
 * <p>{@code deviceId} stores the customer device of the FIRST redemption, which powers the
 * {@code DUPLICATE_ENTRY} (same device) vs {@code ALREADY_ENTERED_OTHER_DEVICE} (different device)
 * split. {@code scanRequestId} is unique for idempotent retries.
 */
@Data
@Document(collection = "event_redemptions")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
@CompoundIndexes({
		@CompoundIndex(name = "uq_event_msisdn_checkpoint",
				def = "{'eventId': 1, 'msisdn': 1, 'checkpoint': 1}", unique = true)
})
public class EventRedemptionDocument {

	@Id
	private String id;

	private String eventId;
	private String msisdn;
	private Checkpoint checkpoint;

	/** Customer device that generated the QR used for the FIRST successful redemption. */
	private String deviceId;

	/** MSISDN of the agent whose session recorded the redemption. */
	private String redeemedByAgentMsisdn;

	/** Idempotency key from the scanner; unique so a retried scan cannot create a second row. */
	@Indexed(unique = true, sparse = true)
	private String scanRequestId;

	private Instant redeemedAt;
}
```

#### `com/airtel/userprofile/eventpass/document/ScanLogDocument.java`

```java
package com.airtel.userprofile.eventpass.document;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.airtel.userprofile.eventpass.enums.EntryCallback;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

/**
 * Append-only audit of every scan attempt (allow AND deny), for dispute resolution and the
 * scan-history API. Indexed by customer msisdn, agent msisdn, and eventId. {@code scanRequestId}
 * is unique so an idempotent retry replays the original decision instead of re-running the chain.
 */
@Data
@Document(collection = "event_scan_logs")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ScanLogDocument {

	@Id
	private String id;

	@Indexed(unique = true, sparse = true)
	private String scanRequestId;

	private String eventId;
	private Checkpoint checkpoint;

	@Indexed
	private String agentMsisdn;

	/** Customer resolved from the token; null when the token could not be resolved (e.g. INVALID_QR). */
	@Indexed
	private String customerMsisdn;

	private String deviceId;
	private EntryCallback callback;
	private String tokenJti;
	private Instant serverTs;
}
```

### DTOs — request

#### `com/airtel/userprofile/eventpass/dto/request/EntryScanRequest.java`

```java
package com.airtel.userprofile.eventpass.dto.request;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * API 3 — agent posts a decoded QR for a decision. {@code eventId} + {@code checkpoint} are the
 * gate the agent is operating; both are validated against the agent's whitelist (via the session),
 * so a client cannot self-authorize an event it is not whitelisted for. {@code scanRequestId} is
 * the idempotency key (reuse the same value on retry).
 */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EntryScanRequest {

	@NotBlank
	private String qrToken;

	@NotBlank
	private String eventId;

	@NotNull
	private Checkpoint checkpoint;

	@NotBlank
	private String scanRequestId;
}
```

#### `com/airtel/userprofile/eventpass/dto/request/QrGenerateRequest.java`

```java
package com.airtel.userprofile.eventpass.dto.request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.NoArgsConstructor;

/** API 4 — customer app asks the User Profile Service to (re)generate the signed membership QR. */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class QrGenerateRequest {

	/** Stable customer-device identifier (install id / keychain-backed), NOT reset per launch. */
	@NotBlank
	private String deviceId;

	/** Client timestamp (advisory only — the server clock is authoritative for iat/exp). */
	private Long timestamp;
}
```

#### `com/airtel/userprofile/eventpass/dto/request/WhitelistUpsertRequest.java`

```java
package com.airtel.userprofile.eventpass.dto.request;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Set;

/** API 1 — engineering whitelists an agent MSISDN for an event with the checkpoints they may scan. */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class WhitelistUpsertRequest {

	@NotBlank
	private String eventId;

	@NotBlank
	private String msisdn;

	@NotEmpty
	private Set<Checkpoint> checkpoints;

	/** Optional on create (defaults to true). On UPDATE (PUT) it toggles the row active/inactive. */
	private Boolean active;
}
```

#### `com/airtel/userprofile/eventpass/dto/request/WinnerUpsertRequest.java`

```java
package com.airtel.userprofile.eventpass.dto.request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * API 5 — admin marks/updates a winner on the customer's existing {@code contest_entries} document
 * (sets {@code winnerInfo}). {@code eventId} is the contest {@code programId} (Q23). Optional
 * {@code rank}/{@code drawId} let ops record which draw/position produced the win; for a purely
 * manual override they can be omitted.
 */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class WinnerUpsertRequest {

	@NotBlank
	private String eventId;   // == contest programId

	@NotBlank
	private String msisdn;

	private Integer rank;
	private String drawId;
}
```

### DTOs — response

#### `com/airtel/userprofile/eventpass/dto/response/AgentEventAccess.java`

```java
package com.airtel.userprofile.eventpass.dto.response;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Set;

/** One event an agent is authorized to scan, and the checkpoints allowed there. */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AgentEventAccess {

	private String eventId;
	private String eventName;
	private String venue;
	private Set<Checkpoint> checkpoints;
}
```

#### `com/airtel/userprofile/eventpass/dto/response/AgentValidateResponse.java`

```java
package com.airtel.userprofile.eventpass.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * API 2 response — the events + checkpoints this agent MSISDN may scan. Empty {@code events}
 * means "not an event agent" (no data leaked). {@code agentSessionId} is issued once the agent
 * picks an event + checkpoint (single-active per msisdn).
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AgentValidateResponse {

	private boolean authorized;
	private List<AgentEventAccess> events;
	private String agentSessionId;
}
```

#### `com/airtel/userprofile/eventpass/dto/response/AgentWhitelistResponse.java`

```java
package com.airtel.userprofile.eventpass.dto.response;

import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.Set;

/** DTO for whitelist read/update responses — never exposes the raw Mongo document to the API. */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AgentWhitelistResponse {

	private String eventId;
	private String msisdn;
	private Set<Checkpoint> checkpoints;
	private boolean active;
	private Instant updatedAt;

	public static AgentWhitelistResponse from(AgentWhitelistDocument d) {
		return AgentWhitelistResponse.builder()
				.eventId(d.getEventId())
				.msisdn(d.getMsisdn())
				.checkpoints(d.getCheckpoints())
				.active(d.isActive())
				.updatedAt(d.getUpdatedAt())
				.build();
	}
}
```

#### `com/airtel/userprofile/eventpass/dto/response/EntryScanResponse.java`

```java
package com.airtel.userprofile.eventpass.dto.response;

import com.airtel.userprofile.eventpass.enums.EntryCallback;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/** API 3 response — the gate decision. Only {@code ENTRY_ALLOWED} admits. */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EntryScanResponse {

	private EntryCallback callback;
	private boolean admit;
	private String displayColor;
	private String message;

	/** Masked holder identity for the agent to eyeball, e.g. "Amit ***** 3210". Never raw PII. */
	private String holderMasked;

	/** Set on DUPLICATE_ENTRY / ALREADY_ENTERED_OTHER_DEVICE — when the first claim happened. */
	private Instant firstClaimAt;

	/** Set on ALREADY_ENTERED_OTHER_DEVICE — the device that made the first claim. */
	private String otherDeviceId;

	public static EntryScanResponse of(EntryCallback cb) {
		return EntryScanResponse.builder()
				.callback(cb)
				.admit(cb.isAdmit())
				.displayColor(cb.getColor())
				.message(cb.getDefaultMessage())
				.build();
	}
}
```

#### `com/airtel/userprofile/eventpass/dto/response/QrGenerateResponse.java`

```java
package com.airtel.userprofile.eventpass.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/** API 4 response — the signed membership QR string and its expiry. */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class QrGenerateResponse {

	/** Opaque signed token to render as a QR (not a URL). */
	private String qrToken;
	private Instant expiresAt;
}
```

### DAO interfaces

#### `com/airtel/userprofile/eventpass/dao/AgentSessionDao.java`

```java
package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.AgentSessionDocument;

import java.util.Optional;

public interface AgentSessionDao {

	/** Revoke all non-revoked sessions for a msisdn (single-active), then persist the new one. */
	AgentSessionDocument openExclusive(AgentSessionDocument session);

	/** Active (not revoked, not expired) session by id — used to authorize a scan. */
	Optional<AgentSessionDocument> findActiveById(String sessionId);
}
```

#### `com/airtel/userprofile/eventpass/dao/AgentWhitelistDao.java`

```java
package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;

import java.util.List;
import java.util.Optional;
import java.util.Set;

public interface AgentWhitelistDao {

	/** Idempotent upsert on (eventId, msisdn) — admin CREATE (POST). */
	AgentWhitelistDocument upsert(AgentWhitelistDocument doc);

	/** All active whitelist rows for an agent — API 2 lists the events/checkpoints they may scan. */
	List<AgentWhitelistDocument> findActiveByMsisdn(String msisdn);

	/** The active row for a specific (eventId, msisdn) — used to authorize a scan. */
	Optional<AgentWhitelistDocument> findActive(String eventId, String msisdn);

	/** READ: a single row (active or not) for (eventId, msisdn). */
	Optional<AgentWhitelistDocument> findOne(String eventId, String msisdn);

	/** READ: all whitelist rows for an event (admin listing). */
	List<AgentWhitelistDocument> findByEvent(String eventId);

	/** UPDATE: set checkpoints and/or active on an existing (eventId, msisdn) row. @return matched count. */
	long update(String eventId, String msisdn, Set<Checkpoint> checkpoints, Boolean active);

	/** DELETE: hard-delete the (eventId, msisdn) row. @return deleted count. */
	long delete(String eventId, String msisdn);
}
```

#### `com/airtel/userprofile/eventpass/dao/ContestWinnerAdminDao.java`

```java
package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.contest.document.WinnerInfo;

/**
 * Write side of the winner data: sets {@code winnerInfo} on the customer's existing
 * {@code contest_entries} document(s). Read side stays in {@code WinnerLookupService}.
 */
public interface ContestWinnerAdminDao {

	/**
	 * Set {@code winnerInfo} on every {@code contest_entries} row matching
	 * {@code (programId, msisdn)}.
	 * @return number of entry documents updated (0 ⇒ the customer has no entry for this event).
	 */
	long markWinner(String programId, String msisdn, WinnerInfo winnerInfo);
}
```

#### `com/airtel/userprofile/eventpass/dao/EventRedemptionDao.java`

```java
package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.enums.Checkpoint;

import java.util.Optional;

/**
 * Persistence for the exactly-once redemption anchor. The single method that matters is
 * {@link #tryRedeem}: it must be atomic so two concurrent scans of the same QR at the same
 * checkpoint produce exactly one first-claim.
 */
public interface EventRedemptionDao {

	/**
	 * Atomically claim {@code (eventId, msisdn, checkpoint)}.
	 * <p>Implemented as an insert guarded by the unique compound index: the first insert wins
	 * ({@code firstClaim=true}); a concurrent/duplicate insert throws DuplicateKeyException, which
	 * the impl converts into {@code firstClaim=false} + the existing row. No read-then-write race.
	 */
	RedeemOutcome tryRedeem(String eventId, String msisdn, Checkpoint checkpoint,
							String deviceId, String agentMsisdn, String scanRequestId);

	Optional<com.airtel.userprofile.eventpass.document.EventRedemptionDocument> find(
			String eventId, String msisdn, Checkpoint checkpoint);
}
```

#### `com/airtel/userprofile/eventpass/dao/RedeemOutcome.java`

```java
package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.EventRedemptionDocument;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Result of an atomic redeem attempt.
 * <ul>
 *   <li>{@code firstClaim == true}  → this scan won the race; {@code row} is the freshly created redemption.</li>
 *   <li>{@code firstClaim == false} → already redeemed; {@code row} is the EXISTING first-claim record
 *       (used to decide DUPLICATE_ENTRY vs ALREADY_ENTERED_OTHER_DEVICE and to show first-claim time).</li>
 * </ul>
 */
@Getter
@AllArgsConstructor
public class RedeemOutcome {

	private final boolean firstClaim;
	private final EventRedemptionDocument row;
}
```

#### `com/airtel/userprofile/eventpass/dao/ScanLogDao.java`

```java
package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.ScanLogDocument;

import java.util.List;
import java.util.Optional;

public interface ScanLogDao {

	ScanLogDocument save(ScanLogDocument log);

	/** Idempotency lookup: the prior terminal result for this scanRequestId, if any. */
	Optional<ScanLogDocument> findByScanRequestId(String scanRequestId);

	/** Full chronological scan history for a customer (dispute API, FR35). */
	List<ScanLogDocument> findByCustomerMsisdnOrderByServerTs(String customerMsisdn);
}
```

### DAO implementations

#### `com/airtel/userprofile/eventpass/dao/impl/AgentSessionDaoImpl.java`

```java
package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.AgentSessionDao;
import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import lombok.RequiredArgsConstructor;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class AgentSessionDaoImpl implements AgentSessionDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public AgentSessionDocument openExclusive(AgentSessionDocument session) {
		// single-active: revoke any prior live session for this msisdn
		Query prior = new Query(Criteria.where("msisdn").is(session.getMsisdn()).and("revoked").is(false));
		mongoTemplate.updateMulti(prior, new Update().set("revoked", true), AgentSessionDocument.class);
		return mongoTemplate.insert(session);
	}

	@Override
	public Optional<AgentSessionDocument> findActiveById(String sessionId) {
		Query q = new Query(Criteria.where("_id").is(sessionId)
				.and("revoked").is(false)
				.and("expiresAt").gt(Instant.now()));
		return Optional.ofNullable(mongoTemplate.findOne(q, AgentSessionDocument.class));
	}
}
```

#### `com/airtel/userprofile/eventpass/dao/impl/AgentWhitelistDaoImpl.java`

```java
package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.AgentWhitelistDao;
import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import lombok.RequiredArgsConstructor;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;

@Repository
@RequiredArgsConstructor
public class AgentWhitelistDaoImpl implements AgentWhitelistDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public AgentWhitelistDocument upsert(AgentWhitelistDocument doc) {
		Query q = new Query(Criteria.where("eventId").is(doc.getEventId()).and("msisdn").is(doc.getMsisdn()));
		Update u = new Update()
				.set("checkpoints", doc.getCheckpoints())
				.set("active", doc.isActive())
				.set("createdBy", doc.getCreatedBy())
				.set("updatedAt", Instant.now())
				.setOnInsert("createdAt", Instant.now());
		mongoTemplate.upsert(u, q, AgentWhitelistDocument.class);
		return findActive(doc.getEventId(), doc.getMsisdn()).orElse(doc);
	}

	@Override
	public List<AgentWhitelistDocument> findActiveByMsisdn(String msisdn) {
		Query q = new Query(Criteria.where("msisdn").is(msisdn).and("active").is(true));
		return mongoTemplate.find(q, AgentWhitelistDocument.class);
	}

	@Override
	public Optional<AgentWhitelistDocument> findActive(String eventId, String msisdn) {
		Query q = new Query(Criteria.where("eventId").is(eventId).and("msisdn").is(msisdn).and("active").is(true));
		return Optional.ofNullable(mongoTemplate.findOne(q, AgentWhitelistDocument.class));
	}

	@Override
	public Optional<AgentWhitelistDocument> findOne(String eventId, String msisdn) {
		Query q = new Query(Criteria.where("eventId").is(eventId).and("msisdn").is(msisdn));
		return Optional.ofNullable(mongoTemplate.findOne(q, AgentWhitelistDocument.class));
	}

	@Override
	public List<AgentWhitelistDocument> findByEvent(String eventId) {
		return mongoTemplate.find(new Query(Criteria.where("eventId").is(eventId)), AgentWhitelistDocument.class);
	}

	@Override
	public long update(String eventId, String msisdn, Set<Checkpoint> checkpoints, Boolean active) {
		Query q = new Query(Criteria.where("eventId").is(eventId).and("msisdn").is(msisdn));
		Update u = new Update().set("updatedAt", Instant.now());
		if (checkpoints != null) u.set("checkpoints", checkpoints);
		if (active != null) u.set("active", active);
		return mongoTemplate.updateFirst(u, q, AgentWhitelistDocument.class).getMatchedCount();
	}

	@Override
	public long delete(String eventId, String msisdn) {
		Query q = new Query(Criteria.where("eventId").is(eventId).and("msisdn").is(msisdn));
		return mongoTemplate.remove(q, AgentWhitelistDocument.class).getDeletedCount();
	}
}
```

#### `com/airtel/userprofile/eventpass/dao/impl/ContestWinnerAdminDaoImpl.java`

```java
package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.contest.document.EntryDocument;
import com.airtel.userprofile.contest.document.WinnerInfo;
import com.airtel.userprofile.eventpass.dao.ContestWinnerAdminDao;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;

/**
 * Writes {@code winnerInfo} onto existing {@code contest_entries} documents via MongoTemplate —
 * the same field {@code DrawServiceImpl} sets, but as a manual admin override. Never creates an
 * entry: a customer must already have entered the contest to be marked a winner.
 */
@Repository
@Slf4j
@RequiredArgsConstructor
public class ContestWinnerAdminDaoImpl implements ContestWinnerAdminDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public long markWinner(String programId, String msisdn, WinnerInfo winnerInfo) {
		Query q = new Query(Criteria.where("programId").is(programId).and("msisdn").is(msisdn));
		Update u = new Update()
				.set("winnerInfo", winnerInfo)
				.set("updatedAt", Instant.now());
		long matched = mongoTemplate.updateMulti(q, u, EntryDocument.class).getMatchedCount();
		log.info("markWinner: programId={} msisdn={} matchedEntries={}", programId, msisdn, matched);
		return matched;
	}
}
```

#### `com/airtel/userprofile/eventpass/dao/impl/EventRedemptionDaoImpl.java`

```java
package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.EventRedemptionDao;
import com.airtel.userprofile.eventpass.dao.RedeemOutcome;
import com.airtel.userprofile.eventpass.document.EventRedemptionDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

/**
 * MongoTemplate implementation of the atomic redemption.
 *
 * <p>The concurrency guarantee is the DB's, not the app's: the unique compound index
 * {@code (eventId, msisdn, checkpoint)} means an {@code insert} either creates the one row (this
 * scan won) or throws {@link DuplicateKeyException} (someone already claimed). We never
 * read-then-write, so there is no lost-update window — exactly the pattern the contest module uses
 * for {@code orderId} on {@code contest_entries}.
 */
@Repository
@Slf4j
@RequiredArgsConstructor
public class EventRedemptionDaoImpl implements EventRedemptionDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public RedeemOutcome tryRedeem(String eventId, String msisdn, Checkpoint checkpoint,
								   String deviceId, String agentMsisdn, String scanRequestId) {
		EventRedemptionDocument doc = EventRedemptionDocument.builder()
				.id(UUID.randomUUID().toString())
				.eventId(eventId)
				.msisdn(msisdn)
				.checkpoint(checkpoint)
				.deviceId(deviceId)
				.redeemedByAgentMsisdn(agentMsisdn)
				.scanRequestId(scanRequestId)
				.redeemedAt(Instant.now())
				.build();
		try {
			mongoTemplate.insert(doc);
			// won the race — first and only claim for this (event, msisdn, checkpoint)
			return new RedeemOutcome(true, doc);
		} catch (DuplicateKeyException dup) {
			// someone already claimed this checkpoint; return the existing first-claim record so the
			// service can decide DUPLICATE_ENTRY vs ALREADY_ENTERED_OTHER_DEVICE and show first-claim time
			EventRedemptionDocument existing = find(eventId, msisdn, checkpoint)
					.orElseThrow(() -> dup); // unique conflict but no row → surface as infra error (SERVICE_UNAVAILABLE)
			return new RedeemOutcome(false, existing);
		}
	}

	@Override
	public Optional<EventRedemptionDocument> find(String eventId, String msisdn, Checkpoint checkpoint) {
		Query q = new Query(Criteria.where("eventId").is(eventId)
				.and("msisdn").is(msisdn)
				.and("checkpoint").is(checkpoint));
		return Optional.ofNullable(mongoTemplate.findOne(q, EventRedemptionDocument.class));
	}
}
```

#### `com/airtel/userprofile/eventpass/dao/impl/ScanLogDaoImpl.java`

```java
package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.ScanLogDao;
import com.airtel.userprofile.eventpass.document.ScanLogDocument;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class ScanLogDaoImpl implements ScanLogDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public ScanLogDocument save(ScanLogDocument log) {
		return mongoTemplate.save(log);
	}

	@Override
	public Optional<ScanLogDocument> findByScanRequestId(String scanRequestId) {
		if (scanRequestId == null || scanRequestId.isBlank()) {
			return Optional.empty();
		}
		Query q = new Query(Criteria.where("scanRequestId").is(scanRequestId));
		return Optional.ofNullable(mongoTemplate.findOne(q, ScanLogDocument.class));
	}

	@Override
	public List<ScanLogDocument> findByCustomerMsisdnOrderByServerTs(String customerMsisdn) {
		Query q = new Query(Criteria.where("customerMsisdn").is(customerMsisdn))
				.with(Sort.by(Sort.Direction.ASC, "serverTs"));
		return mongoTemplate.find(q, ScanLogDocument.class);
	}
}
```

### Service interfaces

#### `com/airtel/userprofile/eventpass/service/AgentAccessService.java`

```java
package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;

/** Agent whitelist validation + scanning-session lifecycle (all inside the User Profile Service). */
public interface AgentAccessService {

	// ---- Whitelist admin CRUD (API 1) ----

	/** CREATE (POST) — idempotently whitelist an agent MSISDN for an event with its checkpoints. */
	AgentWhitelistDocument upsertWhitelist(WhitelistUpsertRequest request, String actor);

	/** READ (GET) — one whitelist row for (eventId, msisdn), or all rows for an event when msisdn is null. */
	java.util.List<AgentWhitelistDocument> getWhitelist(String eventId, String msisdn);

	/** UPDATE (PUT) — change checkpoints and/or active on an existing row. @throws IllegalArgumentException if absent. */
	AgentWhitelistDocument updateWhitelist(WhitelistUpsertRequest request, String actor);

	/** DELETE — remove the (eventId, msisdn) row. @throws IllegalArgumentException if absent. */
	void deleteWhitelist(String eventId, String msisdn, String actor);

	/**
	 * API 2 (single call) — validate the agent and **open a single-active session** in one shot.
	 * Returns the events + checkpoints the agent may scan plus an {@code agentSessionId}; empty /
	 * {@code authorized=false} (and no session) if the MSISDN is not an event agent.
	 */
	AgentValidateResponse validate(String agentMsisdn, String deviceInfo);

	/**
	 * Resolve an active session and confirm the agent is (still) whitelisted for the requested
	 * (eventId, checkpoint) — checked live against the whitelist, since the session is per-agent.
	 * @throws com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException if missing,
	 *         revoked, expired, or not whitelisted for that event/checkpoint.
	 */
	AgentSessionDocument requireAuthorizedSession(String sessionId, String eventId, Checkpoint requestedCheckpoint);
}
```

#### `com/airtel/userprofile/eventpass/service/CachedQr.java`

```java
package com.airtel.userprofile.eventpass.service;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * The active QR cached per customer in the fast store (Aerospike). Holds enough to (a) enforce
 * single-active via {@code jti}, and (b) <b>return the existing token</b> on validate without
 * re-minting. TTL of the cache record == the token TTL, so it self-expires with the QR.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonIgnoreProperties(ignoreUnknown = true)
public class CachedQr {

	private String jti;
	private String token;
	private String deviceId;
	private Instant expiresAt;
}
```

#### `com/airtel/userprofile/eventpass/service/EventEntryService.java`

```java
package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.document.ScanLogDocument;
import com.airtel.userprofile.eventpass.dto.request.EntryScanRequest;
import com.airtel.userprofile.eventpass.dto.response.EntryScanResponse;

import java.util.List;

/** API 3 — record an entry / goodie redemption after a scan. Returns the gate decision. */
public interface EventEntryService {

	/**
	 * @param agentSessionId the agent's active scanning session (event + checkpoint bound to it)
	 * @param request        decoded qrToken + checkpoint + scanRequestId (idempotency key)
	 */
	EntryScanResponse recordEntry(String agentSessionId, EntryScanRequest request);

	/** Admin (FR35) — full chronological scan history for a customer, for dispute resolution. */
	List<ScanLogDocument> scanHistory(String customerMsisdn);
}
```

#### `com/airtel/userprofile/eventpass/service/MembershipEligibilityService.java`

```java
package com.airtel.userprofile.eventpass.service;

/**
 * Membership eligibility gate for QR generation. Backed by the existing User Profile eligibility
 * logic (active Postpaid + Fastlane / Advantage Club). Wired to the platform's existing bean; the
 * eventpass module only depends on this narrow contract.
 */
public interface MembershipEligibilityService {

	boolean isAdvantageClubMember(String msisdn);
}
```

#### `com/airtel/userprofile/eventpass/service/MembershipQrService.java`

```java
package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.dto.response.QrGenerateResponse;

/** API 4 family — generate / validate (get-or-create) / refresh the signed membership QR. */
public interface MembershipQrService {

	/** Always mint a fresh QR (supersedes any previous one). */
	QrGenerateResponse generate(String msisdn, String deviceId);

	/**
	 * Get-or-create: if a live QR for this customer+device is already cached in the fast store,
	 * return it as-is; otherwise mint a new one. This is the default the app calls on card open.
	 */
	QrGenerateResponse validateOrGenerate(String msisdn, String deviceId);

	/** Force a new QR (explicit refresh); supersedes the previous one immediately. */
	QrGenerateResponse refresh(String msisdn, String deviceId);
}
```

#### `com/airtel/userprofile/eventpass/service/QrClaims.java`

```java
package com.airtel.userprofile.eventpass.service;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.time.Instant;
import java.util.Set;

/** Verified, trusted contents of a membership QR token (all read from inside the signature). */
@Getter
@AllArgsConstructor
public class QrClaims {

	/** Customer MSISDN resolved from the opaque subject. */
	private final String msisdn;
	/** Customer device that generated the QR. */
	private final String deviceId;
	/** Events (programIds) the customer had won at issue time. */
	private final Set<String> wonEventIds;
	private final String jti;
	private final Instant issuedAt;
}
```

#### `com/airtel/userprofile/eventpass/service/QrIssuanceStore.java`

```java
package com.airtel.userprofile.eventpass.service;

import java.util.Optional;

/**
 * Per-customer active-QR cache with a TTL (Aerospike / Redis), shared across service instances.
 * It is both the single-active anchor (a refresh/screenshot older than the stored {@code jti}
 * fails) <b>and</b> the source for QR "validate" (get-or-create): if a live QR is cached, it is
 * returned as-is instead of minting a new one.
 */
public interface QrIssuanceStore {

	/** Store {@code qr} as the active QR for {@code msisdn}, expiring after {@code ttlSeconds}. */
	void store(String msisdn, CachedQr qr, long ttlSeconds);

	/** The active (not-yet-expired) cached QR for {@code msisdn}, if any. */
	Optional<CachedQr> getActive(String msisdn);

	/** True iff {@code jti} is still the active token for {@code msisdn} (single-active check). */
	default boolean isLatest(String msisdn, String jti) {
		return getActive(msisdn).map(c -> jti != null && jti.equals(c.getJti())).orElse(false);
	}
}
```

#### `com/airtel/userprofile/eventpass/service/QrTokenService.java`

```java
package com.airtel.userprofile.eventpass.service;

import java.util.Set;

/** Mints and verifies the signed membership QR token. Signing key lives in KMS/HSM, backend-only. */
public interface QrTokenService {

	/**
	 * Mint a signed token for the customer, embedding the won events, and cache it as the
	 * single-active QR (supersedes any previous QR immediately).
	 * @return the minted {@link CachedQr} (token + jti + expiresAt).
	 */
	CachedQr issue(String msisdn, String deviceId, Set<String> wonEventIds);

	/**
	 * Verify signature, version, TTL and single-active status.
	 * @throws com.airtel.userprofile.eventpass.exception.QrInvalidException malformed/forged/unsupported
	 * @throws com.airtel.userprofile.eventpass.exception.QrExpiredException past TTL or superseded
	 */
	QrClaims verify(String qrToken);
}
```

#### `com/airtel/userprofile/eventpass/service/WinnerAdminService.java`

```java
package com.airtel.userprofile.eventpass.service;

/** API 5 — mark/update a winner on the customer's existing contest entry (writes winnerInfo). */
public interface WinnerAdminService {

	/**
	 * @return number of contest entries updated for (eventId, msisdn).
	 * @throws IllegalArgumentException if the customer has no contest entry for this event.
	 */
	long markWinner(String eventId, String msisdn, Integer rank, String drawId, String actor);
}
```

#### `com/airtel/userprofile/eventpass/service/WinnerLookupService.java`

```java
package com.airtel.userprofile.eventpass.service;

import java.util.Set;

/**
 * The "draw winner check" for event access. Reuses the Contest module's winner data: a winner is a
 * {@code contest_entries} row whose {@code winnerInfo} is set (that is how {@code DrawServiceImpl}
 * marks winners). A live event maps to a contest {@code programId}, so:
 * <ul>
 *   <li>{@link #findWonEventIds(String)} → the programIds this msisdn has won (embedded into the QR at generation).</li>
 *   <li>{@link #isWinner(String, String)} → server-side re-check at entry time (defense in depth).</li>
 * </ul>
 */
public interface WinnerLookupService {

	/** Distinct programIds (= eventIds) where this msisdn has a winning contest entry. */
	Set<String> findWonEventIds(String msisdn);

	/** True if this msisdn has a winning entry for the given event (programId). */
	boolean isWinner(String msisdn, String eventId);
}
```

### Service implementations

#### `com/airtel/userprofile/eventpass/service/impl/AgentAccessServiceImpl.java`

```java
package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.config.EventPassProperties;
import com.airtel.userprofile.eventpass.dao.AgentSessionDao;
import com.airtel.userprofile.eventpass.dao.AgentWhitelistDao;
import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentEventAccess;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class AgentAccessServiceImpl implements AgentAccessService {

	private final AgentWhitelistDao whitelistDao;
	private final AgentSessionDao sessionDao;
	private final EventPassProperties props;

	@Override
	public AgentWhitelistDocument upsertWhitelist(WhitelistUpsertRequest request, String actor) {
		AgentWhitelistDocument doc = AgentWhitelistDocument.builder()
				.eventId(request.getEventId())
				.msisdn(request.getMsisdn())
				.checkpoints(request.getCheckpoints())
				.active(request.getActive() == null || request.getActive())   // defaults active
				.createdBy(actor)
				.build();
		AgentWhitelistDocument saved = whitelistDao.upsert(doc);
		log.info("Whitelist created/upserted by {}: event={} msisdn={} checkpoints={}",
				actor, request.getEventId(), request.getMsisdn(), request.getCheckpoints());
		return saved;
	}

	@Override
	public java.util.List<AgentWhitelistDocument> getWhitelist(String eventId, String msisdn) {
		if (msisdn != null && !msisdn.isBlank()) {
			AgentWhitelistDocument row = whitelistDao.findOne(eventId, msisdn)
					.orElseThrow(() -> new IllegalArgumentException(
							"No whitelist row for event " + eventId + " / msisdn " + msisdn));
			return java.util.List.of(row);
		}
		return whitelistDao.findByEvent(eventId);
	}

	@Override
	public AgentWhitelistDocument updateWhitelist(WhitelistUpsertRequest request, String actor) {
		long matched = whitelistDao.update(
				request.getEventId(), request.getMsisdn(), request.getCheckpoints(), request.getActive());
		if (matched == 0) {
			throw new IllegalArgumentException(
					"No whitelist row to update for event " + request.getEventId() + " / msisdn " + request.getMsisdn());
		}
		log.info("Whitelist updated by {}: event={} msisdn={} checkpoints={} active={}",
				actor, request.getEventId(), request.getMsisdn(), request.getCheckpoints(), request.getActive());
		return whitelistDao.findOne(request.getEventId(), request.getMsisdn()).orElseThrow();
	}

	@Override
	public void deleteWhitelist(String eventId, String msisdn, String actor) {
		long deleted = whitelistDao.delete(eventId, msisdn);
		if (deleted == 0) {
			throw new IllegalArgumentException(
					"No whitelist row to delete for event " + eventId + " / msisdn " + msisdn);
		}
		log.info("Whitelist deleted by {}: event={} msisdn={}", actor, eventId, msisdn);
	}

	@Override
	public AgentValidateResponse validate(String agentMsisdn, String deviceInfo) {
		List<AgentWhitelistDocument> rows = whitelistDao.findActiveByMsisdn(agentMsisdn);
		if (rows.isEmpty()) {
			return AgentValidateResponse.builder().authorized(false).build();  // no event data / no session
		}
		List<AgentEventAccess> events = rows.stream()
				.map(r -> AgentEventAccess.builder()
						.eventId(r.getEventId())
						.checkpoints(r.getCheckpoints())
						// eventName/venue enriched from event/program metadata where available
						.build())
				.collect(Collectors.toList());

		// open a single-active per-agent session in the same call (revokes any prior session)
		Instant now = Instant.now();
		AgentSessionDocument session = AgentSessionDocument.builder()
				.id(UUID.randomUUID().toString())
				.msisdn(agentMsisdn)
				.revoked(false)
				.createdAt(now)
				.expiresAt(now.plusSeconds(props.getAgentSessionTtlSeconds()))
				.deviceInfo(deviceInfo)
				.build();
		sessionDao.openExclusive(session);
		log.info("Agent validated + session opened: msisdn={} events={}", agentMsisdn, events.size());

		return AgentValidateResponse.builder()
				.authorized(true)
				.events(events)
				.agentSessionId(session.getId())
				.build();
	}

	@Override
	public AgentSessionDocument requireAuthorizedSession(String sessionId, String eventId, Checkpoint requestedCheckpoint) {
		AgentSessionDocument session = sessionDao.findActiveById(sessionId)
				.orElseThrow(() -> new AgentSessionInvalidException("Session missing, revoked, or expired"));

		// authorize live against the whitelist for the (eventId, checkpoint) this scan targets
		AgentWhitelistDocument wl = whitelistDao.findActive(eventId, session.getMsisdn())
				.orElseThrow(() -> new AgentSessionInvalidException("Not whitelisted for event " + eventId));
		if (wl.getCheckpoints() == null || !wl.getCheckpoints().contains(requestedCheckpoint)) {
			throw new AgentSessionInvalidException("Not authorized for checkpoint " + requestedCheckpoint);
		}
		return session;
	}
}
```

#### `com/airtel/userprofile/eventpass/service/impl/EventEntryServiceImpl.java`

```java
package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.dao.EventRedemptionDao;
import com.airtel.userprofile.eventpass.dao.RedeemOutcome;
import com.airtel.userprofile.eventpass.dao.ScanLogDao;
import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import com.airtel.userprofile.eventpass.document.EventRedemptionDocument;
import com.airtel.userprofile.eventpass.document.ScanLogDocument;
import com.airtel.userprofile.eventpass.dto.request.EntryScanRequest;
import com.airtel.userprofile.eventpass.dto.response.EntryScanResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.airtel.userprofile.eventpass.enums.EntryCallback;
import com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException;
import com.airtel.userprofile.eventpass.exception.QrExpiredException;
import com.airtel.userprofile.eventpass.exception.QrInvalidException;
import com.airtel.userprofile.eventpass.service.AgentAccessService;
import com.airtel.userprofile.eventpass.service.EventEntryService;
import com.airtel.userprofile.eventpass.service.QrClaims;
import com.airtel.userprofile.eventpass.service.QrTokenService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Optional;

/**
 * The gate authority. Order mirrors the HLD validation chain: session → token → winner → atomic
 * redeem → audit. Every DECISION (allow and deny) is returned as a 200 {@link EntryScanResponse};
 * only unexpected infra faults become {@code SERVICE_UNAVAILABLE} and never auto-allow.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class EventEntryServiceImpl implements EventEntryService {

	private final AgentAccessService agentAccess;
	private final QrTokenService qrTokenService;
	private final EventRedemptionDao redemptionDao;
	private final ScanLogDao scanLogDao;

	@Override
	public EntryScanResponse recordEntry(String agentSessionId, EntryScanRequest request) {
		try {
			// 0) Idempotency: a retried scanRequestId replays the original decision (no re-redeem)
			Optional<ScanLogDocument> prior = scanLogDao.findByScanRequestId(request.getScanRequestId());
			if (prior.isPresent()) {
				log.debug("Idempotent replay for scanRequestId={} -> {}",
						request.getScanRequestId(), prior.get().getCallback());
				return rebuild(prior.get());
			}

			// 1–2) Agent session valid & agent whitelisted for the requested (eventId, checkpoint)
			String eventId = request.getEventId();
			Checkpoint checkpoint = request.getCheckpoint();
			AgentSessionDocument session;
			try {
				session = agentAccess.requireAuthorizedSession(agentSessionId, eventId, checkpoint);
			} catch (AgentSessionInvalidException e) {
				log.warn("Scan rejected — session/authorization invalid: {}", e.getMessage());
				return audit(EntryScanResponse.of(EntryCallback.STAFF_SESSION_INVALID),
						eventId, null, request, null);
			}
			String agentMsisdn = session.getMsisdn();

			// 3–5) Verify token (signature, version, TTL, single-active)
			QrClaims claims;
			try {
				claims = qrTokenService.verify(request.getQrToken());
			} catch (QrExpiredException e) {
				return audit(EntryScanResponse.of(EntryCallback.QR_EXPIRED), eventId, null, request, agentMsisdn);
			} catch (QrInvalidException e) {
				return audit(EntryScanResponse.of(EntryCallback.INVALID_QR), eventId, null, request, agentMsisdn);
			}

			// 6) Winner check — the scanned event must be among the QR's won events
			if (claims.getWonEventIds() == null || !claims.getWonEventIds().contains(eventId)) {
				return audit(EntryScanResponse.of(EntryCallback.NOT_ENTITLED),
						eventId, claims, request, agentMsisdn);
			}

			// 7) Atomic redeem (event, msisdn, checkpoint) — exactly one first-claim
			RedeemOutcome outcome = redemptionDao.tryRedeem(
					eventId, claims.getMsisdn(), checkpoint,
					claims.getDeviceId(), agentMsisdn, request.getScanRequestId());

			EntryScanResponse response;
			if (outcome.isFirstClaim()) {
				response = EntryScanResponse.of(EntryCallback.ENTRY_ALLOWED);
			} else {
				EventRedemptionDocument first = outcome.getRow();
				boolean sameDevice = first.getDeviceId() != null
						&& first.getDeviceId().equals(claims.getDeviceId());
				response = EntryScanResponse.of(
						sameDevice ? EntryCallback.DUPLICATE_ENTRY : EntryCallback.ALREADY_ENTERED_OTHER_DEVICE);
				response.setFirstClaimAt(first.getRedeemedAt());
				if (!sameDevice) {
					response.setOtherDeviceId(first.getDeviceId());
				}
			}
			response.setHolderMasked(mask(claims.getMsisdn()));

			// 8) Audit (always)
			return audit(response, eventId, claims, request, agentMsisdn);

		} catch (Exception e) {
			// Never auto-allow on infra failure; nothing that committed is lost (idempotency replays it)
			log.error("Scan failed unexpectedly for scanRequestId={}", request.getScanRequestId(), e);
			return EntryScanResponse.of(EntryCallback.SERVICE_UNAVAILABLE);
		}
	}

	private EntryScanResponse audit(EntryScanResponse response, String eventId, QrClaims claims,
									EntryScanRequest request, String agentMsisdn) {
		try {
			scanLogDao.save(ScanLogDocument.builder()
					.scanRequestId(request.getScanRequestId())
					.eventId(eventId)
					.checkpoint(request.getCheckpoint())
					.agentMsisdn(agentMsisdn)
					.customerMsisdn(claims != null ? claims.getMsisdn() : null)
					.deviceId(claims != null ? claims.getDeviceId() : null)
					.callback(response.getCallback())
					.tokenJti(claims != null ? claims.getJti() : null)
					.serverTs(Instant.now())
					.build());
		} catch (Exception logEx) {
			// A duplicate scanRequestId here means a concurrent retry already logged it — replay that.
			return scanLogDao.findByScanRequestId(request.getScanRequestId())
					.map(this::rebuild)
					.orElse(response);
		}
		return response;
	}

	@Override
	public java.util.List<ScanLogDocument> scanHistory(String customerMsisdn) {
		return scanLogDao.findByCustomerMsisdnOrderByServerTs(customerMsisdn);
	}

	/** Rebuild a response from a stored log entry (idempotent replay). */
	private EntryScanResponse rebuild(ScanLogDocument log) {
		EntryScanResponse r = EntryScanResponse.of(log.getCallback());
		if (log.getCustomerMsisdn() != null) {
			r.setHolderMasked(mask(log.getCustomerMsisdn()));
		}
		return r;
	}

	/** Mask an MSISDN for the agent screen — never expose the full number. e.g. "***** 3210". */
	private static String mask(String msisdn) {
		if (msisdn == null || msisdn.length() < 4) {
			return "*****";
		}
		return "***** " + msisdn.substring(msisdn.length() - 4);
	}
}
```

#### `com/airtel/userprofile/eventpass/service/impl/MembershipQrServiceImpl.java`

```java
package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.dto.response.QrGenerateResponse;
import com.airtel.userprofile.eventpass.service.CachedQr;
import com.airtel.userprofile.eventpass.service.MembershipEligibilityService;
import com.airtel.userprofile.eventpass.service.MembershipQrService;
import com.airtel.userprofile.eventpass.service.QrIssuanceStore;
import com.airtel.userprofile.eventpass.service.QrTokenService;
import com.airtel.userprofile.eventpass.service.WinnerLookupService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.Set;

@Service
@Slf4j
@RequiredArgsConstructor
public class MembershipQrServiceImpl implements MembershipQrService {

	private final MembershipEligibilityService eligibility;
	private final WinnerLookupService winnerLookup;
	private final QrTokenService qrTokenService;
	private final QrIssuanceStore issuanceStore;

	@Override
	public QrGenerateResponse generate(String msisdn, String deviceId) {
		requireMember(msisdn);
		// Every member gets a QR; the won events (possibly empty) are embedded and signed in.
		Set<String> wonEventIds = winnerLookup.findWonEventIds(msisdn);
		CachedQr issued = qrTokenService.issue(msisdn, deviceId, wonEventIds);
		return toResponse(issued);
	}

	@Override
	public QrGenerateResponse validateOrGenerate(String msisdn, String deviceId) {
		requireMember(msisdn);
		// If a live QR for this same device is cached, return it as-is (no re-mint).
		Optional<CachedQr> cached = issuanceStore.getActive(msisdn);
		if (cached.isPresent() && deviceId != null && deviceId.equals(cached.get().getDeviceId())) {
			log.debug("QR validate: returning cached active QR for msisdn={}", msisdn);
			return toResponse(cached.get());
		}
		// Miss (none cached, expired, or different device) → mint a fresh one.
		return generate(msisdn, deviceId);
	}

	@Override
	public QrGenerateResponse refresh(String msisdn, String deviceId) {
		// Explicit refresh always supersedes the cached QR.
		return generate(msisdn, deviceId);
	}

	private void requireMember(String msisdn) {
		if (!eligibility.isAdvantageClubMember(msisdn)) {
			throw new IllegalArgumentException("Not an Advantage Club member");
		}
	}

	private static QrGenerateResponse toResponse(CachedQr qr) {
		return QrGenerateResponse.builder()
				.qrToken(qr.getToken())
				.expiresAt(qr.getExpiresAt())
				.build();
	}
}
```

#### `com/airtel/userprofile/eventpass/service/impl/QrIssuanceStoreImpl.java`

```java
package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.service.CachedQr;
import com.airtel.userprofile.eventpass.service.QrIssuanceStore;
import com.airtel.userprofile.service.impl.helper.AerospikeManager;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Optional;

/**
 * Aerospike-backed active-QR cache, mirroring how {@code UsedOrderCacheServiceImpl} uses
 * {@link AerospikeManager}. Key = customer msisdn; value = the {@link CachedQr} as JSON; record
 * TTL = QR TTL, so it self-expires with the token.
 *
 * <p>Platform note: add an {@code AerospikeDetails.EVENT_QR_LATEST} namespace/set and a TTL-aware
 * {@code putDetails(key, value, details, ttl, useDisk)} overload; wired here by name.
 */
@Service
@Slf4j
public class QrIssuanceStoreImpl implements QrIssuanceStore {

	private static final boolean USE_DISK = false;
	private final ObjectMapper mapper = new ObjectMapper().findAndRegisterModules();

	@Autowired(required = false)
	private AerospikeManager aerospikeManager;

	@Override
	public void store(String msisdn, CachedQr qr, long ttlSeconds) {
		if (aerospikeManager == null) {
			log.warn("AerospikeManager unavailable; active QR not cached for msisdn={}", msisdn);
			return;
		}
		try {
			String json = mapper.writeValueAsString(qr);
			aerospikeManager.putDetails(key(msisdn), json,
					com.airtel.userprofile.constants.AerospikeDetails.EVENT_QR_LATEST, (int) ttlSeconds, USE_DISK);
		} catch (Exception e) {
			log.warn("Failed to cache active QR for msisdn={}: {}", msisdn, e.getMessage());
		}
	}

	@Override
	public Optional<CachedQr> getActive(String msisdn) {
		if (aerospikeManager == null) {
			return Optional.empty();   // fail safe: cannot confirm → caller mints a fresh QR
		}
		Object raw = aerospikeManager.getDetails(key(msisdn),
				com.airtel.userprofile.constants.AerospikeDetails.EVENT_QR_LATEST, USE_DISK);
		if (raw == null) {
			return Optional.empty();
		}
		try {
			CachedQr qr = mapper.readValue(raw.toString(), CachedQr.class);
			// defensive: honour expiry even if the record has not yet been evicted
			if (qr.getExpiresAt() != null && qr.getExpiresAt().isBefore(Instant.now())) {
				return Optional.empty();
			}
			return Optional.of(qr);
		} catch (Exception e) {
			log.warn("Failed to read cached QR for msisdn={}: {}", msisdn, e.getMessage());
			return Optional.empty();
		}
	}

	private static String key(String msisdn) {
		return "qr:latest:" + msisdn;
	}
}
```

#### `com/airtel/userprofile/eventpass/service/impl/QrTokenServiceImpl.java`

```java
package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.contest.service.PiiEncryptionDecryption;
import com.airtel.userprofile.eventpass.config.EventPassProperties;
import com.airtel.userprofile.eventpass.exception.QrExpiredException;
import com.airtel.userprofile.eventpass.exception.QrInvalidException;
import com.airtel.userprofile.eventpass.service.CachedQr;
import com.airtel.userprofile.eventpass.service.QrClaims;
import com.airtel.userprofile.eventpass.service.QrIssuanceStore;
import com.airtel.userprofile.eventpass.service.QrTokenService;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.Jwts;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.security.PrivateKey;
import java.security.PublicKey;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * Signs/verifies the membership QR (compact JWS, ES256). Claims: {@code sub} = opaque (encrypted)
 * msisdn — never raw PII (Q3); {@code dev} = deviceId; {@code events} = won programIds;
 * {@code ver} = schema version; {@code jti}/{@code iat}/{@code exp} standard.
 *
 * <p>Single-active: {@code issue} registers {@code jti} as the latest for the customer; {@code verify}
 * requires the token to still be the latest, so a refresh (or an old shared screenshot) fails as
 * {@code QR_EXPIRED} even within the TTL.
 *
 * <p>Keys are provided by a KMS/HSM-backed {@code @Configuration}: {@code signingKey} (private,
 * backend-only) and {@code verificationKey} (public), rotated via the {@code kid} header.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class QrTokenServiceImpl implements QrTokenService {

	private static final String CLAIM_VERSION = "ver";
	private static final String CLAIM_DEVICE = "dev";
	private static final String CLAIM_EVENTS = "events";

	private final EventPassProperties props;
	private final QrIssuanceStore issuanceStore;
	private final PiiEncryptionDecryption pii;
	private final PrivateKey signingKey;      // from KMS/HSM config bean
	private final PublicKey verificationKey;  // from KMS/HSM config bean

	@Override
	public CachedQr issue(String msisdn, String deviceId, Set<String> wonEventIds) {
		Instant now = Instant.now();
		Instant exp = now.plusSeconds(props.getQrTtlSeconds());
		String jti = UUID.randomUUID().toString();

		String token = Jwts.builder()
				.header().keyId(props.getSigningKeyId()).and()
				.id(jti)
				.issuer(props.getIssuer())
				.subject(pii.encrypt(msisdn))                 // opaque subject, never raw MSISDN
				.issuedAt(Date.from(now))
				.expiration(Date.from(exp))
				.claim(CLAIM_VERSION, props.getTokenVersion())
				.claim(CLAIM_DEVICE, deviceId)
				.claim(CLAIM_EVENTS, new ArrayList<>(wonEventIds == null ? Set.of() : wonEventIds))
				.signWith(signingKey)
				.compact();

		CachedQr cached = CachedQr.builder()
				.jti(jti).token(token).deviceId(deviceId).expiresAt(exp).build();

		// cache as the single-active QR; TTL matches the token so the record self-expires
		issuanceStore.store(msisdn, cached, props.getQrTtlSeconds());
		log.debug("Issued QR for msisdn={} jti={} events={}", msisdn, jti, wonEventIds);
		return cached;
	}

	@Override
	@SuppressWarnings("unchecked")
	public QrClaims verify(String qrToken) {
		Jws<Claims> jws;
		try {
			jws = Jwts.parser()
					.verifyWith(verificationKey)
					.requireIssuer(props.getIssuer())
					.build()
					.parseSignedClaims(qrToken);
		} catch (ExpiredJwtException e) {
			throw new QrExpiredException("QR token past TTL");
		} catch (JwtException | IllegalArgumentException e) {
			// bad signature, malformed, unsupported alg, wrong issuer, etc.
			throw new QrInvalidException("QR token invalid: " + e.getClass().getSimpleName());
		}

		Claims c = jws.getPayload();

		Integer ver = c.get(CLAIM_VERSION, Integer.class);
		if (ver == null || ver > props.getTokenVersion()) {
			throw new QrInvalidException("Unsupported token version: " + ver);
		}

		String msisdn = pii.decrypt(c.getSubject());
		if (msisdn == null || msisdn.isBlank()) {
			throw new QrInvalidException("Unresolvable subject");
		}

		// single-active: superseded token (older screenshot / pre-refresh) → treat as expired
		if (!issuanceStore.isLatest(msisdn, c.getId())) {
			throw new QrExpiredException("QR superseded by a newer issuance");
		}

		Set<String> events = new HashSet<>();
		Object raw = c.get(CLAIM_EVENTS);
		if (raw instanceof List<?> list) {
			for (Object o : list) {
				if (o != null) events.add(o.toString());
			}
		}

		return new QrClaims(msisdn, c.get(CLAIM_DEVICE, String.class), events,
				c.getId(), c.getIssuedAt().toInstant());
	}
}
```

#### `com/airtel/userprofile/eventpass/service/impl/WinnerAdminServiceImpl.java`

```java
package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.contest.document.WinnerInfo;
import com.airtel.userprofile.eventpass.dao.ContestWinnerAdminDao;
import com.airtel.userprofile.eventpass.service.WinnerAdminService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;

/**
 * Manual winner override. Builds a {@link WinnerInfo} (reusing the contest document) and writes it
 * onto the customer's existing {@code contest_entries} row(s). Because the winner list is embedded
 * into the QR at generation, a customer picks up a newly-marked win on their next QR refresh.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class WinnerAdminServiceImpl implements WinnerAdminService {

	private final ContestWinnerAdminDao winnerAdminDao;

	@Override
	public long markWinner(String eventId, String msisdn, Integer rank, String drawId, String actor) {
		WinnerInfo info = WinnerInfo.builder()
				.rank(rank)
				.drawId(drawId)
				.createdAt(Instant.now())
				.build();

		long updated = winnerAdminDao.markWinner(eventId, msisdn, info);
		if (updated == 0) {
			// Never fabricate an entry — the customer must have played the contest first.
			throw new IllegalArgumentException(
					"No contest entry found for msisdn in event " + eventId + "; cannot mark winner");
		}
		log.info("Winner marked by {}: event={} msisdn={} entriesUpdated={}", actor, eventId, msisdn, updated);
		return updated;
	}
}
```

#### `com/airtel/userprofile/eventpass/service/impl/WinnerLookupServiceImpl.java`

```java
package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.contest.document.EntryDocument;
import com.airtel.userprofile.eventpass.service.WinnerLookupService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Reads winners straight from the contest collection. A winning entry is one where
 * {@code winnerInfo} exists (set by the draw). {@code programId} is treated as the eventId.
 *
 * <p>We query only the fields we need (projection) and never expose PII from here — the caller
 * only receives event ids / a boolean.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class WinnerLookupServiceImpl implements WinnerLookupService {

	private final MongoTemplate mongoTemplate;

	private static Query winningEntriesOf(String msisdn) {
		// winnerInfo present == winner (mirrors DrawServiceImpl.upsertWinnerInfoOnEntries)
		return new Query(Criteria.where("msisdn").is(msisdn).and("winnerInfo").exists(true));
	}

	@Override
	public Set<String> findWonEventIds(String msisdn) {
		if (msisdn == null || msisdn.isBlank()) {
			return Set.of();
		}
		Query q = winningEntriesOf(msisdn);
		q.fields().include("programId");
		List<EntryDocument> entries = mongoTemplate.find(q, EntryDocument.class);
		Set<String> eventIds = new HashSet<>();
		for (EntryDocument e : entries) {
			if (e.getProgramId() != null && !e.getProgramId().isBlank()) {
				eventIds.add(e.getProgramId());
			}
		}
		log.debug("Winner lookup: msisdn={} won {} event(s)", msisdn, eventIds.size());
		return eventIds;
	}

	@Override
	public boolean isWinner(String msisdn, String eventId) {
		if (msisdn == null || msisdn.isBlank() || eventId == null || eventId.isBlank()) {
			return false;
		}
		Query q = winningEntriesOf(msisdn);
		q.addCriteria(Criteria.where("programId").is(eventId));
		return mongoTemplate.exists(q, EntryDocument.class);
	}
}
```

### Controllers

#### `com/airtel/userprofile/eventpass/controller/AgentController.java`

```java
package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.constants.UserProfileConstants;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.dto.response.AgentWhitelistResponse;
import com.airtel.userprofile.eventpass.service.AgentAccessService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * API 1 (admin whitelist) + API 2 (single agent validate — which also opens the scanning session).
 * No OTP, no microsite — the agent uses the Thanks App in agent mode, so {@code IV_USER} is the
 * authenticated agent MSISDN.
 */
@RestController
@Api(value = "Event Pass — Agent")
@Slf4j
@RequiredArgsConstructor
public class AgentController {

	private final AgentAccessService agentAccessService;

	// ---- API 1: admin whitelist CRUD (engineering only; secured upstream) ----

	// CREATE
	@PostMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Create/whitelist an agent MSISDN for an event with checkpoints (admin)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> createWhitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@Valid @RequestBody WhitelistUpsertRequest request) {
		var saved = agentAccessService.upsertWhitelist(request, actor);
		return Response.getSuccessResponse(Map.of("whitelistId", saved.getId(), "status", "UPSERTED"));
	}

	// READ (one when msisdn given, else all rows for the event)
	@GetMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Get whitelist row(s) for an event (all rows, or one when msisdn is given)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<List<AgentWhitelistResponse>> getWhitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@RequestParam String eventId,
			@RequestParam(required = false) String msisdn) {
		List<AgentWhitelistResponse> rows = agentAccessService.getWhitelist(eventId, msisdn).stream()
				.map(AgentWhitelistResponse::from).collect(Collectors.toList());
		return Response.getSuccessResponse(rows);
	}

	// UPDATE
	@PutMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Update checkpoints and/or active flag on an existing whitelist row (admin)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<AgentWhitelistResponse> updateWhitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@Valid @RequestBody WhitelistUpsertRequest request) {
		return Response.getSuccessResponse(
				AgentWhitelistResponse.from(agentAccessService.updateWhitelist(request, actor)));
	}

	// DELETE
	@DeleteMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Delete a whitelist row for (eventId, msisdn) (admin)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> deleteWhitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@RequestParam String eventId,
			@RequestParam String msisdn) {
		agentAccessService.deleteWhitelist(eventId, msisdn, actor);
		return Response.getSuccessResponse(Map.of("eventId", eventId, "msisdn", msisdn, "status", "DELETED"));
	}

	// ---- API 2: validate agent + open session (single call) ----
	@GetMapping("/v1/agents/validate")
	@ApiOperation(value = "Validate the agent and open a scanning session; returns authorized events + checkpoints + agentSessionId")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<AgentValidateResponse> validate(
			@RequestHeader(name = UserProfileConstants.IV_USER) String agentMsisdn,
			@RequestHeader(name = "User-Agent", required = false) String userAgent) {
		return Response.getSuccessResponse(agentAccessService.validate(agentMsisdn, userAgent));
	}
}
```

#### `com/airtel/userprofile/eventpass/controller/EventEntryController.java`

```java
package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.eventpass.document.ScanLogDocument;
import com.airtel.userprofile.eventpass.dto.request.EntryScanRequest;
import com.airtel.userprofile.eventpass.dto.response.EntryScanResponse;
import com.airtel.userprofile.eventpass.service.EventEntryService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;

/**
 * API 3 — record an entry after scanning (agent mode). The event is taken from the agent session
 * (header {@code X-Agent-Session}); the body carries only qrToken + checkpoint + scanRequestId.
 * Also exposes the admin scan-history API (FR35).
 */
@RestController
@Api(value = "Event Pass — Entry")
@Slf4j
@RequiredArgsConstructor
public class EventEntryController {

	public static final String HEADER_AGENT_SESSION = "X-Agent-Session";

	private final EventEntryService eventEntryService;

	@PostMapping("/v1/entry")
	@ApiOperation(value = "Record entry/goodie redemption after scanning a customer QR")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<EntryScanResponse> recordEntry(
			@RequestHeader(name = HEADER_AGENT_SESSION) String agentSessionId,
			@Valid @RequestBody EntryScanRequest request) {
		// Every gate decision (allow/deny) returns 200 with a callback so the scanner always renders.
		return Response.getSuccessResponse(eventEntryService.recordEntry(agentSessionId, request));
	}

	@GetMapping("/v1/admin/scan-history")
	@ApiOperation(value = "Full chronological scan history for a customer (dispute resolution)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<List<ScanLogDocument>> scanHistory(@RequestParam String msisdn) {
		return Response.getSuccessResponse(eventEntryService.scanHistory(msisdn));
	}
}
```

#### `com/airtel/userprofile/eventpass/controller/MembershipQrController.java`

```java
package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.constants.UserProfileConstants;
import com.airtel.userprofile.eventpass.dto.request.QrGenerateRequest;
import com.airtel.userprofile.eventpass.dto.response.QrGenerateResponse;
import com.airtel.userprofile.eventpass.service.MembershipQrService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;

/**
 * API 4 — customer app (User Profile Service). {@code IV_USER} carries the authenticated customer
 * MSISDN, matching the contest controllers' convention.
 */
@RestController
@Api(value = "Event Pass — Membership QR")
@Slf4j
@RequiredArgsConstructor
public class MembershipQrController {

	private final MembershipQrService membershipQrService;

	/** Create a new QR (always mints). */
	@PostMapping("/v1/membership/qr")
	@ApiOperation(value = "Generate the signed membership QR (carries won eventIds)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<QrGenerateResponse> generate(
			@RequestHeader(name = UserProfileConstants.IV_USER) String ivUser,
			@Valid @RequestBody QrGenerateRequest request) {
		return Response.getSuccessResponse(membershipQrService.generate(ivUser, request.getDeviceId()));
	}

	/** Validate / get-or-create: return the cached live QR if present, else mint a new one. */
	@PostMapping("/v1/membership/qr/validate")
	@ApiOperation(value = "Return the cached live QR if present in the fast store, else create a new one")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<QrGenerateResponse> validate(
			@RequestHeader(name = UserProfileConstants.IV_USER) String ivUser,
			@Valid @RequestBody QrGenerateRequest request) {
		return Response.getSuccessResponse(membershipQrService.validateOrGenerate(ivUser, request.getDeviceId()));
	}

	/** Explicit refresh: always mint a new QR, superseding the previous one. */
	@PostMapping("/v1/membership/qr/refresh")
	@ApiOperation(value = "Force a new membership QR (supersedes the previous one)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<QrGenerateResponse> refresh(
			@RequestHeader(name = UserProfileConstants.IV_USER) String ivUser,
			@Valid @RequestBody QrGenerateRequest request) {
		return Response.getSuccessResponse(membershipQrService.refresh(ivUser, request.getDeviceId()));
	}
}
```

#### `com/airtel/userprofile/eventpass/controller/WinnerAdminController.java`

```java
package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.constants.UserProfileConstants;
import com.airtel.userprofile.eventpass.dto.request.WinnerUpsertRequest;
import com.airtel.userprofile.eventpass.service.WinnerAdminService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;
import java.util.Map;

/**
 * API 5 — mark/update a winner on the customer's existing {@code contest_entries} document
 * (admin / engineering only; secured upstream). Sets {@code winnerInfo}; the customer's next QR
 * refresh embeds the new event id.
 */
@RestController
@Api(value = "Event Pass — Winner Admin")
@Slf4j
@RequiredArgsConstructor
public class WinnerAdminController {

	private final WinnerAdminService winnerAdminService;

	@PostMapping("/v1/admin/winners")
	@ApiOperation(value = "Mark/update a winner on the customer's contest entry (writes winnerInfo)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> markWinner(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@Valid @RequestBody WinnerUpsertRequest request) {
		long updated = winnerAdminService.markWinner(
				request.getEventId(), request.getMsisdn(), request.getRank(), request.getDrawId(), actor);
		return Response.getSuccessResponse(Map.of(
				"eventId", request.getEventId(),
				"msisdn", request.getMsisdn(),
				"entriesUpdated", updated,
				"status", "WINNER_MARKED"));
	}
}
```

### Exceptions

#### `com/airtel/userprofile/eventpass/exception/AgentSessionInvalidException.java`

```java
package com.airtel.userprofile.eventpass.exception;

/** Agent session missing, revoked, expired, or not authorized for the event/checkpoint. */
public class AgentSessionInvalidException extends RuntimeException {

	public AgentSessionInvalidException(String message) {
		super(message);
	}
}
```

#### `com/airtel/userprofile/eventpass/exception/EventPassExceptionHandler.java`

```java
package com.airtel.userprofile.eventpass.exception;

import com.airtel.core.dto.genericResponse.Error;
import com.airtel.core.dto.genericResponse.Response;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Mirrors {@code ContestExceptionHandler}. NOTE: on the entry path (API 3) all gate DECISIONS —
 * including {@code INVALID_QR}, {@code QR_EXPIRED}, {@code STAFF_SESSION_INVALID} — are returned by
 * the service as a 200 {@code EntryScanResponse} carrying the callback, so the scanner always
 * parses a decision. This handler covers the admin/validate paths and unexpected failures.
 */
@RestControllerAdvice(basePackages = "com.airtel.userprofile.eventpass.controller")
@Slf4j
public class EventPassExceptionHandler {

	@ExceptionHandler(IllegalArgumentException.class)
	public ResponseEntity<Response<Object>> handleBadRequest(IllegalArgumentException ex) {
		log.warn("EventPass bad request: {}", ex.getMessage());
		return failure(ex.getMessage(), "bad_request", HttpStatus.BAD_REQUEST);
	}

	@ExceptionHandler(AgentSessionInvalidException.class)
	public ResponseEntity<Response<Object>> handleSession(AgentSessionInvalidException ex) {
		log.warn("EventPass agent session invalid: {}", ex.getMessage());
		return failure(ex.getMessage(), "staff_session_invalid", HttpStatus.UNAUTHORIZED);
	}

	private static ResponseEntity<Response<Object>> failure(String message, String code, HttpStatus status) {
		Error error = new Error().setMessage(message).setCode(code);
		return ResponseEntity.status(status).body(Response.getFailureResponseWithError(error, status.value()));
	}
}
```

#### `com/airtel/userprofile/eventpass/exception/QrExpiredException.java`

```java
package com.airtel.userprofile.eventpass.exception;

/** Token is genuine but past its TTL, or superseded by a newer issuance → QR_EXPIRED. */
public class QrExpiredException extends RuntimeException {

	public QrExpiredException(String message) {
		super(message);
	}
}
```

#### `com/airtel/userprofile/eventpass/exception/QrInvalidException.java`

```java
package com.airtel.userprofile.eventpass.exception;

/** Token is malformed, unsupported version, bad signature, or not Airtel-issued → INVALID_QR. */
public class QrInvalidException extends RuntimeException {

	public QrInvalidException(String message) {
		super(message);
	}
}
```

### Converters

#### `com/airtel/userprofile/eventpass/converter/CheckpointConverter.java`

```java
package com.airtel.userprofile.eventpass.converter;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

/** Lets {@code @RequestParam Checkpoint} bind from a string, mirroring ContestEntryTypeConverter. */
@Component
public class CheckpointConverter implements Converter<String, Checkpoint> {

	@Override
	public Checkpoint convert(String source) {
		return Checkpoint.fromValue(source);
	}
}
```

### Config

#### `com/airtel/userprofile/eventpass/config/EventPassProperties.java`

```java
package com.airtel.userprofile.eventpass.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/**
 * Environment-tunable knobs (no redeploy needed). The QR TTL is shared by generation (API 4) and
 * validation (API 3) — issuance and validation MUST read the same value (Q1; recommend 5 min).
 */
@Data
@Component
@RefreshScope
@ConfigurationProperties(prefix = "eventpass")
public class EventPassProperties {

	/** QR token TTL in seconds (Q1 — recommend 300). */
	private long qrTtlSeconds = 300;

	/** Agent scanning session TTL in seconds (24h). */
	private long agentSessionTtlSeconds = 86_400;

	/** Token schema version currently issued; verifier accepts this and older supported versions. */
	private int tokenVersion = 1;

	/** JWT issuer claim. */
	private String issuer = "airtel-userprofile-eventpass";

	/** Active signing key id (KMS/HSM alias) for rotation. */
	private String signingKeyId;
}
```

### QR image util (render & validate) — §5A

New files under `com.airtel.userprofile.eventpass` for the styled circular QR. Full source lives in
the reference tree; the colour/style config is inlined here since it is the tunable surface.

| Path | Role |
|---|---|
| `config/QrStyleProperties.java` | `eventpass.qr-style.*` — colours, module shape, centre text, EC level (inlined below). |
| `util/CircularQrGenerator.java` | `data` → styled PNG / data-URI (ZXing encode + Java2D dots/gradient/finder/badge). Per-call input is an immutable `Style`; a private `Grid` owns the module geometry. |
| `util/QrImageDecoder.java` | image bytes → payload (ZXing decode); `decode` / `tryDecode` / `matches`. |
| `util/HexColors.java` | `#RRGGBB` / `#AARRGGBB` / `transparent` → `Color` (one parser shared by config mapping + overrides). |
| `dto/request/QrRenderRequest.java` | render body — `data` (required) + optional `centerText`, colour & `size` overrides. |
| `dto/response/QrRenderResponse.java` | `imageDataUri`, `width/height`, `encoded`. |
| `service/QrImageService.java` (+`impl`) | config defaults + per-request overrides over the two utils. |
| `controller/MembershipQrImageController.java` | `POST /v1/membership/qr/image`, `…/image.png`, `…/validate-image`. |

```java
package com.airtel.userprofile.eventpass.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/** Visual style for the rendered membership QR — env-tunable via {@code eventpass.qr-style.*}. */
@Data
@Component
@RefreshScope
@ConfigurationProperties(prefix = "eventpass.qr-style")
public class QrStyleProperties {

	public enum ModuleShape { DOTS, ROUNDED, SQUARE }

	private int size = 720;
	private int quietZoneModules = 2;
	private String backgroundColor = "#FFFFFF";

	private ModuleShape moduleShape = ModuleShape.DOTS;
	private double moduleSizeRatio = 0.86;

	private boolean gradientEnabled = true;
	private String gradientInnerColor = "#F5A623";
	private String gradientOuterColor = "#C8102E";
	private String foregroundColor = "#C8102E";

	private boolean styledFinder = true;
	private double finderCornerRatio = 0.35;
	private String finderColor = "#C8102E";

	private boolean centerBadgeEnabled = true;
	private double centerBadgeRatio = 0.24;
	private String centerBadgeInnerColor = "#E4002B";
	private String centerBadgeOuterColor = "#8B0000";
	private boolean centerRingEnabled = true;
	private String centerRingColor = "#FFFFFF";
	private double centerRingRatio = 0.04;

	private String centerText = "airtel\nPOSTPAID\nADVANTAGE\nCLUB";
	private String centerTextColor = "#FFFFFF";
	private String centerTextFont = "SansSerif";
	private String centerLogoResource;

	private String errorCorrection = "H";
}
```

> The generator (`CircularQrGenerator`), decoder (`QrImageDecoder`) and colour parser (`HexColors`)
> live in [`reference-impl/eventpass/util/`](./reference-impl/eventpass/util). The generator/decoder
> are stateless Spring `@Component`s wired through `QrImageService`; `HexColors` is a pure helper. The
> renderer takes an immutable `Style` and knows nothing about the web DTO or Spring config — the
> service resolves config + per-request overrides into a `Style` (SRP), so styling stays pure.

---

## 14. Open decisions

| # | Question |
|---|---|
| Q1 | QR TTL value (recommend 5 min) — one knob for API 3 & 4 |
| Q5 | Screenshot handling — block (Android) vs detect (iOS) |
| Q10 | Agent auth = app login + whitelist (no OTP) — confirm sufficient |
| Q22 | `deviceId` is the customer device; needs a stable id |
| Q23 | Event ↔ contest mapping — event = `programId` (vs `campaignId` / multi-contest)? Affects winner read (API 4) **and** write (API 5) |
