# FSC Swagger v1.7 — Network enhancements (subscription, alerts, CLM, deeplink, permissions)

**Spec:** `1.6-merged` → **`1.7-merged`** · **Base:** `/fsc` · **Date:** 20 Nov 2026
**Files:** `fsc-swagger-merged.html` (Swagger UI) · `fsc-swagger-merged.json` · **23 paths**

## Removed

| Method | Path | Why |
|---|---|---|
| POST | `/api/v1/family/save` | Family add not needed — removed |
| POST | `/api/v1/member/save` | Member add replaced by **Subscription** (pointer 1) |

(`RequestFamilyPojo` pruned as orphaned.)

## Added — pointer APIs

### 1. Subscription (works on MSISDN) — replaces member add
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/subscription` | `action` = **CREATE / CANCEL / SUSPEND / RESUME** on `msisdn` — provisions the member |
| GET | `/api/v1/subscription/features/fetch` | All features enabled for an MSISDN (CHECKIN, SOS, FRAUD_SPAM, …) + `subscriptionStatus` + per-feature `status` |
| POST | `/api/v1/subscription/features/toggle` | Enable / disable a single feature for a member |

### 2. Open alerts + history (contract)
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/alert/fetch` | `scope` = OPEN / HISTORY / ALL, role-scoped (`visibleTo`), filter by member/type/date. `AlertInfo` covers all 10 alert types + `deeplinkId` |

### 3. CLM payload for check-in / SOS
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/clm/payload/fetch` | Network reads the payload configured at CLM (templateId, channels, messageTemplate, escalationConfig) for `eventType` = CHECKIN / SOS |

### 4. Deeplink resolve
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/deeplink/resolve` | `deeplinkId` from the notification url + `msisdn`/`familyId` (group id) → event context (`triggerId`, `eventType`, `action`) to call the checkin/sos/fraud API |

### 5. Permissions + feature status (all members)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/permission/update` | Record a member's granted/denied permissions; Network recomputes feature `status` |
| GET | `/api/v1/permission/fetch` | Permissions on/off + derived feature status for **all family members** (passed to Channel) |

## Enhanced (from the Network-asks findings)

- **`DeviceDetail`** — added `reachabilityReason` (REACHABLE / SWITCHED_OFF / NO_COVERAGE / FLIGHT_MODE / SWITCHED_OFF_OR_FLIGHT / INACTIVE_NUMBER), `lastOnNetworkAt`, `lastBatteryLevel`.
- **`ResponseSosData`** — added live `location`, `lastKnownLocation`, `lastOnNetworkAt`, `battery`, `networkStrength` (SOS takeover DTO).

**Unchanged:** response envelope; trigger/checkin, trigger/sos, device/status/fetch, fraud/alert/*, history/fetch, member/get, member/delete, member/role/update, family/get, alarm/*.

## Full path list (23)

`subscription` · `subscription/features/fetch` · `subscription/features/toggle` · `alert/fetch` · `clm/payload/fetch` · `deeplink/resolve` · `permission/update` · `permission/fetch` · `family/get` · `member/get` · `member/delete` · `member/role/update` · `trigger/checkin` · `trigger/checkin/status/check` · `trigger/sos` · `trigger/sos/cancel` · `trigger/sos/status/check` · `device/status/fetch` · `fraud/alert/fetch` · `fraud/alert/action` · `history/fetch` · `alarm/incoming` · `alarm/sos/kill`
