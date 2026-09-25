# Detailed LLD — `eventpass` module (code)

This is the build-ready, code-level LLD for the event-access feature, written to match the
**existing `contest` module** conventions (package `com.airtel.userprofile.*`, Lombok Mongo
`@Document`s, DAO + `MongoTemplate`, `DuplicateKeyException` for atomic uniqueness, the
`com.airtel.core.dto.genericResponse.Response` wrapper, `@AuditLog`, `IV_USER` header for the
caller MSISDN).

The reference implementation lives in [`reference-impl/eventpass/`](./reference-impl/eventpass)
in the **same folder layout** as `contest` (`document/`, `dto/request|response/`, `service/`,
`service/impl/`, `dao/`, `dao/impl/`, `controller/`, `exception/`, `enums/`, `converter/`,
`config/`). Drop it under `com.airtel.userprofile.eventpass` in the User Profile Service.

> **How it reuses `contest`.** A live event maps to a contest **`programId`**. A *winner* is a
> `contest_entries` document whose **`winnerInfo` is set** — exactly how `DrawServiceImpl` marks
> winners. So the "draw winner check" is a read over `contest_entries`; no new winner store.

---

## 1. Package layout

```
com.airtel.userprofile.eventpass
├── enums/            Checkpoint, EntryCallback
├── document/         EventRedemptionDocument, AgentWhitelistDocument, AgentSessionDocument, ScanLogDocument
├── dto/request/      QrGenerateRequest, EntryScanRequest, WhitelistUpsertRequest
├── dto/response/     QrGenerateResponse, EntryScanResponse, AgentValidateResponse, AgentEventAccess
├── dao/              EventRedemptionDao, RedeemOutcome, ScanLogDao, AgentWhitelistDao, AgentSessionDao
│   └── impl/         EventRedemptionDaoImpl, ScanLogDaoImpl, AgentWhitelistDaoImpl, AgentSessionDaoImpl
├── service/          MembershipQrService, EventEntryService, AgentAccessService, WinnerLookupService,
│                     QrTokenService, QrIssuanceStore, MembershipEligibilityService, QrClaims
│   └── impl/         MembershipQrServiceImpl, EventEntryServiceImpl, AgentAccessServiceImpl,
│                     WinnerLookupServiceImpl, QrTokenServiceImpl, QrIssuanceStoreImpl
├── controller/       MembershipQrController, AgentController, EventEntryController
├── exception/        QrInvalidException, QrExpiredException, AgentSessionInvalidException, EventPassExceptionHandler
├── converter/        CheckpointConverter
└── config/           EventPassProperties
```

## 2. API → class map

| API | Endpoint | Controller | Service | Persistence |
|---|---|---|---|---|
| 1 | `POST /v1/agents/whitelist` | `AgentController` | `AgentAccessService.upsertWhitelist` | `AgentWhitelistDao` → `event_agent_whitelist` |
| 2 | `GET /v1/agents/validate` · `POST /v1/agents/session` | `AgentController` | `AgentAccessService.validate` / `openSession` | `AgentWhitelistDao`, `AgentSessionDao` |
| 3 | `POST /v1/entry` | `EventEntryController` | `EventEntryService.recordEntry` | `EventRedemptionDao` (redeem) + `ScanLogDao` (audit) |
| 4 | `POST /v1/membership/qr` | `MembershipQrController` | `MembershipQrService.generate` | `WinnerLookupService` (read `contest_entries`) + `QrTokenService` |
| — | `GET /v1/admin/scan-history` | `EventEntryController` | `EventEntryService.scanHistory` | `ScanLogDao` |

## 3. Collections & indexes (MongoDB)

| Collection | Key index | Purpose |
|---|---|---|
| `event_redemptions` | **unique** `(eventId, msisdn, checkpoint)`; unique sparse `scanRequestId` | exactly-once redemption + idempotency |
| `event_agent_whitelist` | **unique** `(eventId, msisdn)` | agent authority (events + checkpoints) |
| `event_agent_sessions` | `msisdn` | single-active scanning session |
| `event_scan_logs` | unique sparse `scanRequestId`; `customerMsisdn`; `agentMsisdn`; `eventId` | audit + idempotency + history API |
| `contest_entries` *(existing)* | reuse `winnerInfo` presence + `programId` | winner source of truth (read-only here) |

The unique indexes are declared on the documents (`@CompoundIndex` / `@Indexed(unique=true)`) so
Spring Data auto-creates them, same as `EntryDocument.orderId` in `contest`.

---

## 4. How we **save an entry** (atomic, exactly-once) — the hero path

Redemption is one conditional insert; the DB's unique index is the concurrency guarantee (no
read-then-write). This is the same `DuplicateKeyException` trick `ContestEngineServiceImpl` uses
for `orderId`.

**`dao/impl/EventRedemptionDaoImpl.java`**
```java
public RedeemOutcome tryRedeem(String eventId, String msisdn, Checkpoint checkpoint,
                               String deviceId, String agentMsisdn, String scanRequestId) {
    EventRedemptionDocument doc = EventRedemptionDocument.builder()
            .id(UUID.randomUUID().toString())
            .eventId(eventId).msisdn(msisdn).checkpoint(checkpoint)
            .deviceId(deviceId).redeemedByAgentMsisdn(agentMsisdn)
            .scanRequestId(scanRequestId).redeemedAt(Instant.now())
            .build();
    try {
        mongoTemplate.insert(doc);
        return new RedeemOutcome(true, doc);                 // won the race → ENTRY_ALLOWED
    } catch (DuplicateKeyException dup) {
        EventRedemptionDocument existing = find(eventId, msisdn, checkpoint).orElseThrow(() -> dup);
        return new RedeemOutcome(false, existing);           // already claimed → device split
    }
}
```

**`service/impl/EventEntryServiceImpl.java`** turns that into the callback, including the
device-aware split and idempotent replay (full chain in the file):
```java
RedeemOutcome outcome = redemptionDao.tryRedeem(eventId, claims.getMsisdn(), checkpoint,
        claims.getDeviceId(), agentMsisdn, request.getScanRequestId());

if (outcome.isFirstClaim()) {
    response = EntryScanResponse.of(EntryCallback.ENTRY_ALLOWED);
} else {
    EventRedemptionDocument first = outcome.getRow();
    boolean sameDevice = first.getDeviceId() != null && first.getDeviceId().equals(claims.getDeviceId());
    response = EntryScanResponse.of(sameDevice
            ? EntryCallback.DUPLICATE_ENTRY : EntryCallback.ALREADY_ENTERED_OTHER_DEVICE);
    response.setFirstClaimAt(first.getRedeemedAt());
    if (!sameDevice) response.setOtherDeviceId(first.getDeviceId());
}
```

**Guarantees**
- Two concurrent scans of the same QR at the same checkpoint → exactly one `ENTRY_ALLOWED`, one already-claimed result (FR25).
- ENTRY and GOODIE are different `checkpoint` values → different rows → one QR redeems once at each (FR28).
- **Idempotency:** `EventEntryServiceImpl.recordEntry` first checks `ScanLogDao.findByScanRequestId`; a retried `scanRequestId` replays the original decision. A crash between redeem-commit and response is safe — the retry finds the log (or re-derives from the redemption row) and never double-admits.
- **Never auto-allow:** the whole body is wrapped so any unexpected fault returns `SERVICE_UNAVAILABLE`; nothing that committed is lost.

## 5. How we do the **draw winner check** — reusing contest data

**`service/impl/WinnerLookupServiceImpl.java`**
```java
private static Query winningEntriesOf(String msisdn) {
    // winnerInfo present == winner (mirrors DrawServiceImpl.upsertWinnerInfoOnEntries)
    return new Query(Criteria.where("msisdn").is(msisdn).and("winnerInfo").exists(true));
}

public Set<String> findWonEventIds(String msisdn) {          // used at QR generation (API 4)
    Query q = winningEntriesOf(msisdn);
    q.fields().include("programId");
    return mongoTemplate.find(q, EntryDocument.class).stream()
            .map(EntryDocument::getProgramId).filter(Objects::nonNull)
            .collect(Collectors.toSet());
}

public boolean isWinner(String msisdn, String eventId) {      // optional re-check at entry
    Query q = winningEntriesOf(msisdn);
    q.addCriteria(Criteria.where("programId").is(eventId));
    return mongoTemplate.exists(q, EntryDocument.class);
}
```

- At **QR generation** (API 4), `findWonEventIds` builds the token's signed `events[]`.
- At **entry** (API 3), the primary winner check is `session.eventId ∈ token.events`; `isWinner`
  is available as a server-side re-check (defense in depth) if the token is old.

## 6. QR token (mint / verify, single-active)

`QrTokenServiceImpl` (jjwt, ES256): claims `sub` = **opaque** (encrypted via the existing
`PiiEncryptionDecryption`, never raw MSISDN — Q3), `dev` = deviceId, `events` = won programIds,
`ver`, `jti`, `iat`, `exp`. Single-active is enforced by `QrIssuanceStore` (Aerospike, mirroring
`UsedOrderCacheServiceImpl`): `issue` records the latest `jti` per customer; `verify` requires the
token to still be the latest, so a refresh or an old screenshot fails as `QR_EXPIRED` even within
TTL. Expired signature → `QrExpiredException`; bad/forged → `QrInvalidException`.

## 7. Validation chain (as coded in `EventEntryServiceImpl.recordEntry`)

1. **Idempotency** — replay if `scanRequestId` already logged.
2. **Agent session** — `AgentAccessService.requireAuthorizedSession(sessionId, checkpoint)`; else `STAFF_SESSION_INVALID`.
3. **Token** — `QrTokenService.verify` → `INVALID_QR` / `QR_EXPIRED`.
4. **Winner** — `session.eventId ∈ claims.wonEventIds` → else `NOT_ENTITLED`.
5. **Atomic redeem** — `EventRedemptionDao.tryRedeem` → `ENTRY_ALLOWED` / `DUPLICATE_ENTRY` / `ALREADY_ENTERED_OTHER_DEVICE`.
6. **Audit** — `ScanLogDao.save` (always, allow and deny).
7. Any exception → `SERVICE_UNAVAILABLE` (never auto-allow).

Event, checkpoint, and agent identity are taken from the **session**, never the request body.

## 8. Config (`EventPassProperties`, `eventpass.*` — `@RefreshScope`)

| Property | Default | Notes |
|---|---|---|
| `eventpass.qrTtlSeconds` | `300` | Q1 — shared by API 3 & API 4; recommend 5 min |
| `eventpass.agentSessionTtlSeconds` | `86400` | 24h |
| `eventpass.tokenVersion` | `1` | verifier accepts this and older supported versions |
| `eventpass.issuer` | `airtel-userprofile-eventpass` | JWT `iss` |
| `eventpass.signingKeyId` | — | KMS/HSM key alias (`kid` for rotation) |

## 9. Dependencies / platform wiring to confirm

- **jjwt** (`io.jsonwebtoken:jjwt-api/impl/jackson`, 0.12.x) for JWS — add to `pom.xml` if not already present.
- **Signing keys**: a `@Configuration` must provide `PrivateKey` (KMS/HSM) + `PublicKey` beans for `QrTokenServiceImpl`.
- **`MembershipEligibilityService`**: wire to the platform's existing Advantage-Club eligibility bean.
- **`QrIssuanceStoreImpl`**: add `AerospikeDetails.EVENT_QR_LATEST` + a TTL-aware `putDetails` overload, matching the existing Aerospike helper conventions.
- **`AgentEventAccess.eventName/venue`**: enrich from event/program metadata where available (left null otherwise).

## 10. Not built here (out of scope for this module)
The customer-app surfaces (icon, hamburger, tile, splash, walkthrough) are client-side (see
[`04-lld.md`](./04-lld.md) §9); this module is the **backend** for QR generation, agent access,
and entry validation.
