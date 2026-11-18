# FSC API — Merge Summary (for Network team)

**Base:** `/fsc` · **Swagger version:** `1.1-merged` (from `1.0`) · **Date:** 18 Nov 2026
**Artifacts:** `fsc-swagger-merged.html` (open in a browser — Swagger UI) · `fsc-swagger-merged.json` (import into Swagger/Postman/codegen)

We request **3 merges** — combine create+update into one upsert, and get+getAll into one read. No other endpoints change.

## Merges requested

| # | Old endpoints (to remove) | New merged endpoint | How it switches |
|---|---|---|---|
| 1 | `POST /api/v1/family/create` + `POST /api/v1/family/update` | **`POST /api/v1/family/save`** | `familyId` query is **optional** — **omit = create**, **provide = update** (upsert). Body `RequestFamilyPojo` unchanged. |
| 2 | `POST /api/v1/member/add` + `POST /api/v1/member/update` | **`POST /api/v1/member/save`** | `memberId` query is **optional** — **omit = add**, **provide = update** (upsert). Body `RequestFamilyMemberPojo` unchanged. |
| 3 | `GET /api/v1/member/get` + `GET /api/v1/member/getAll` | **`GET /api/v1/member/get`** | `familyId` **required**, `memberId` **optional** — **provide memberId = one member**, **omit = all members** of the family. |

## Model change (only one)

To let the single merged read return **one or many** members, `ResponseFamilyMemberPojo` becomes **list-capable**:

- New `ResponseFamilyMemberInfo` = the member fields (airtelCustomer, circleMemberRole, familyId, memberId, membershipId, membershipStatus, msisdn).
- `ResponseFamilyMemberPojo` = `{ familyMemberInfos: [ResponseFamilyMemberInfo], responseCode, responseMessage, transactionId }`.
- A single-member query returns `familyMemberInfos` with exactly one element.

## Net effect

| | Before | After |
|---|---|---|
| Family write APIs | 2 (create, update) | **1** (save) |
| Member write APIs | 2 (add, update) | **1** (save) |
| Member read APIs | 2 (get, getAll) | **1** (get) |
| Total FSC paths | 21 | **18** |

**Unchanged:** `family/get`, `member/delete`, `member/role/update`, all `trigger/checkin/*`, `trigger/sos/*`, `alarm/*`, `device/status/*`. Response envelope (`responseCode`, `responseMessage`, `transactionId`) unchanged.

> Note (from 17 Nov review): on the **family save** path, per the agreed decision, member **addition should not** happen via family update — add members only via `member/save`. The `familyMemberPojos` array in `RequestFamilyPojo` is intended for the **create** case; on update it should carry family-level fields only.
