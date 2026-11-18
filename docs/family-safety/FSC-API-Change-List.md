# FSC API — Change List for Review

**To:** Network team · **Spec:** `1.5-merged` (from `1.0`) · **Base path:** `/fsc` · **Date:** 18 Nov 2026
**Attached:** `fsc-swagger-merged.html` (open in browser — Swagger UI) · `fsc-swagger-merged.json` (import into Swagger/Postman)

Summary of requested changes: **5 merges**, **2 method fixes**, **1 new API**, **1 removal**, plus **field-level enhancements** from the 17 Nov review. Net: **21 → 15 paths**.

## A. API changes

| # | Type | Old API(s) | New / Updated API | Method | What changes |
|---|---|---|---|---|---|
| 1 | Merge | `POST /family/create` + `POST /family/update` | `POST /family/save` | POST | Upsert — omit `familyId` = create, provide = update |
| 2 | Merge | `POST /member/add` + `POST /member/update` | `POST /member/save` | POST | Upsert — omit `memberId` = add, provide = update |
| 3 | Merge | `GET /member/get` + `GET /member/getAll` | `GET /member/get` | GET | `familyId` required, `memberId` optional (omit = all members) |
| 4 | Merge | `POST /trigger/checkin/create` + `/response` + `/status/update` | `POST /trigger/checkin` | POST | Body `action` = CREATE / RESPONSE / DISMISS / PAUSE / RESUME |
| 5 | Merge | `POST /trigger/sos/create` + `/update` | `POST /trigger/sos` | POST | Body `action` = CREATE / ACKNOWLEDGE / RESOLVE |
| 6 | Method fix | `POST /member/delete` | `DELETE /member/delete` | **DELETE** | `familyId`, `memberId` query |
| 7 | Method fix | `POST /trigger/sos/cancel` | `DELETE /trigger/sos/cancel` | **DELETE** | `triggerId` query; initiator-only |
| 8 | New API | — | `GET /history/fetch` | GET | Consolidated alert & activity history; filters `familyId` (req), `msisdn`, `eventType`, `fromDate`, `toDate` |
| 9 | Removed | `POST /device/status/store` | — | — | Orchestrator is consume-only; telemetry stored via SDK → Kafka → Network hub |

## B. Field-level enhancements (17 Nov review)

| Ref | API | Added / changed |
|---|---|---|
| E1 | `POST /family/save` | Members added only via `member/save` (not the family path) |
| E2 | `POST /trigger/checkin` (CREATE) | `message`; `scheduleDays` (MON–SUN); `scheduleTime` as **HH:mm** (time-only); `startDate` / `endDate` (duration); one check-in per day |
| E3 | `GET /trigger/checkin/status/check` | `targetMsisdn` filter; `fromDate` / `toDate` range |
| E4 | `POST /trigger/checkin` (DISMISS/PAUSE/RESUME) | `initiatorMsisdn` → Network validates admin |
| E5 | `DELETE /trigger/sos/cancel` | `initiatorMsisdn` → cancel only by initiator |
| E6 | `POST /trigger/sos` (RESOLVE) | `resolvedBy` may be initiator **or** responder |
| E7 | `POST /trigger/sos` (CREATE) | `location` ('lat,long'); Network LBS fallback during SOS |
| E8 | `GET /device/status/fetch` | `lastUpdatedOn` timestamp per property |

## C. Resulting API list (15 paths)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/family/save` | Create / update family (upsert) |
| GET | `/api/v1/family/get` | Get family by `familyId` |
| POST | `/api/v1/member/save` | Add / update member (upsert) |
| GET | `/api/v1/member/get` | Get one member or all (merged) |
| DELETE | `/api/v1/member/delete` | Delete member |
| POST | `/api/v1/member/role/update` | Update member role |
| POST | `/api/v1/trigger/checkin` | Check-in — create / response / dismiss / pause / resume |
| GET | `/api/v1/trigger/checkin/status/check` | Check-in status / history |
| POST | `/api/v1/trigger/sos` | SOS — create / acknowledge / resolve |
| DELETE | `/api/v1/trigger/sos/cancel` | Cancel SOS |
| GET | `/api/v1/trigger/sos/status/check` | SOS status |
| GET | `/api/v1/device/status/fetch` | Fetch device status (last value + `lastUpdatedOn`) |
| GET | `/api/v1/history/fetch` | Consolidated alert & activity history (new) |
| POST | `/api/v1/alarm/incoming` | Incoming alarm / notification |
| POST | `/api/v1/alarm/sos/kill` | Kill an active SOS alarm |

**Unchanged envelope:** every response carries `responseCode`, `responseMessage`, `transactionId`.
**Model note:** `ResponseFamilyMemberPojo` is now list-capable (`familyMemberInfos[]`) so the merged `member/get` returns one or many.
