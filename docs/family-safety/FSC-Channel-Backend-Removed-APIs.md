# FSC API — Channel Backend view (removed endpoints)

**From:** `1.5-merged` → **`1.6-channel-backend`** · **Base:** `/fsc` · **Date:** 18 Nov 2026
**Files:** `fsc-swagger-channel-backend.html` (Swagger UI) · `fsc-swagger-channel-backend.json`

The Channel Backend (orchestrator) does **not** call these right now, so they are removed from its view. **15 → 10 paths.**

## Removed

| # | Method | Path | Why removed |
|---|---|---|---|
| 1 | POST | `/api/v1/family/save` | Family create/update is owned by the **provisioning** path, not the orchestrator |
| 2 | POST | `/api/v1/member/save` | Member add/update owned by provisioning, not the orchestrator |
| 3 | DELETE | `/api/v1/member/delete` | Member churn handled by provisioning (member/delete) — not an orchestrator call |
| 4 | POST | `/api/v1/member/role/update` | Role changes owned by provisioning / settings path, not the orchestrator |
| 5 | POST | `/api/v1/alarm/sos/kill` | **Network-internal** — per 17-Nov decision #8 (orchestrator does not persist) |

Orphaned models pruned: `RequestFamilyPojo`, `RequestSosAlarmKillPojo`.

## Remaining (10 — what the Channel Backend consumes)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/alarm/incoming` | Receive incoming alarm (no-internet push, e.g. presidential alert) |
| GET | `/api/v1/device/status/fetch` | Device status (last value + `lastUpdatedOn`) |
| GET | `/api/v1/family/get` | Read family by `familyId` |
| GET | `/api/v1/member/get` | Read one member or all (merged) |
| GET | `/api/v1/trigger/checkin/status/check` | Check-in status / history |
| GET | `/api/v1/trigger/sos/status/check` | SOS status |
| POST | `/api/v1/trigger/checkin` | Check-in — create / response / dismiss / pause / resume |
| POST | `/api/v1/trigger/sos` | SOS — create / acknowledge / resolve |
| DELETE | `/api/v1/trigger/sos/cancel` | Cancel SOS (initiator-only) |
| GET | `/api/v1/history/fetch` | Consolidated alert & activity history |

**Note:** removal is from the *Channel Backend view* only — these endpoints still exist on the Network FSC service for the provisioning path and Network-internal use. Response envelope unchanged.
