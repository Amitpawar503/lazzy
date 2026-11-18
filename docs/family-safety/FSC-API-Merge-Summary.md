# FSC API — Merge Summary (for Network team)

**Base:** `/fsc` · **Swagger:** `1.2-merged` (from `1.0`) · **Date:** 18 Nov 2026
**Artifacts:** `fsc-swagger-merged.html` (open in a browser — Swagger UI) · `fsc-swagger-merged.json` (import into Swagger/Postman/codegen)

Requested changes: **5 merges** (combine create/update/action into one endpoint each) + **2 HTTP-method fixes** (delete/cancel → `DELETE`). All read/status endpoints stay as-is.

## Merges requested

| # | Old endpoints (removed) | New merged endpoint | How it switches |
|---|---|---|---|
| 1 | `POST /family/create` + `POST /family/update` | **`POST /family/save`** | `familyId` query optional — **omit = create, provide = update** (upsert) |
| 2 | `POST /member/add` + `POST /member/update` | **`POST /member/save`** | `memberId` query optional — **omit = add, provide = update** (upsert) |
| 3 | `GET /member/get` + `GET /member/getAll` | **`GET /member/get`** | `familyId` required, `memberId` optional — **provide = one member, omit = all** |
| 4 | `POST /trigger/checkin/create` + `/response` + `/status/update` | **`POST /trigger/checkin`** | body `action` enum = **CREATE / RESPONSE / DISMISS / PAUSE / RESUME** |
| 5 | `POST /trigger/sos/create` + `/update` | **`POST /trigger/sos`** | body `action` enum = **CREATE / ACKNOWLEDGE / RESOLVE** |

## HTTP method fixes (delete/cancel must be DELETE, not POST)

| # | Old | New |
|---|---|---|
| 6 | `POST /member/delete` | **`DELETE /member/delete`** (`familyId`, `memberId` query) |
| 7 | `POST /trigger/sos/cancel` | **`DELETE /trigger/sos/cancel`** (`triggerId` query) |

## Model changes

- **`ResponseFamilyMemberPojo`** is now **list-capable** (so the merged read returns one or many): `{ familyMemberInfos: [ResponseFamilyMemberInfo], responseCode, responseMessage, transactionId }`. New `ResponseFamilyMemberInfo` holds the member fields. Single-member query returns a one-element list.
- **`RequestTriggerCheckinPojo`** (new) — unified check-in body with `action` + the union of fields; each field tagged `[CREATE]` / `[RESPONSE]` in its description.
- **`RequestTriggerSosPojo`** (new) — unified SOS body with `action` + union of fields tagged `[CREATE]` / `[ACKNOWLEDGE]` / `[RESOLVE]`.
- Removed now-unused request POJOs: `RequestTriggerCheckin{Create,Response,Update}Pojo`, `RequestTriggerSos{Create,Update,Cancel}Pojo`.

## Net effect

| | Before | After |
|---|---|---|
| Family write | create + update | **save** |
| Member write | add + update | **save** |
| Member read | get + getAll | **get** |
| Check-in write | create + response + status/update | **trigger/checkin (action)** |
| SOS write | create + update | **trigger/sos (action)** |
| Delete/cancel method | POST | **DELETE** (member/delete, sos/cancel) |
| Total FSC paths | 21 | **15** |

**Unchanged:** `family/get`, `member/get`, `member/role/update`, `trigger/checkin/status/check`, `trigger/sos/status/check`, `device/status/*`, `alarm/*`. Response envelope (`responseCode`, `responseMessage`, `transactionId`) unchanged.

> Note (17 Nov review): on `family/save`, members should **not** be added via the family path — use `member/save`. `familyMemberPojos` on `RequestFamilyPojo` is for the create case only.
