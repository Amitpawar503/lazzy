# Family Safety — Upstream (BEFE/Guardian) API Change List

**To:** Leadership / Channel · **Base path:** `/befe/fsc/v1` · **Date:** 18 Nov 2026
**Attached:** `befe-upstream-swagger.html` (Swagger UI) · `befe-upstream-swagger.json` (import to Swagger/Postman)

## Verdict

Checked **FSC_BEFE_API_Requirements** (B01–B74) and the **FSC downstream swagger** against **Family-Safety-API-Binding-Leadership.pdf**.

- The binding documented only the **~24 core app flows** (older naming: `/circles`, `/safety-events`, `/family-safety/*`). It is a *downstream mapping* doc, not an upstream API spec.
- The upstream app surface is **72 endpoints / 86 operations**. **~50 were missing** from the binding — all now specified.
- **Result: 0 upstream APIs still missing.** Full coverage, with request + response + mandatory fields per operation.

> **Summary: 32 core (already mapped) · 54 ADDED · 86 total operations.**

**Legend:** ✓ = core flow already in the binding (orchestrates existing FSC) · **＋ = ADDED** (was a gap / never enumerated upstream).

## Eligibility & Onboarding

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| **＋** | GET | `/eligibility` | msisdn (q) | Can user create a circle? (Airtel? LOB? corporate? already in circle? pack active?) |
| **＋** | GET | `/onboarding/content` | — | CMS feature tiles / FAQ / how-it-works |
| **＋** | GET | `/how-it-works` | — | Revisit onboarding content |

## Subscription

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| **＋** | GET | `/subscription/offers` | — | Plans (prepaid/postpaid/family) |
| **＋** | POST | `/subscription/purchase` | planId, channel | Start prepaid buy / postpaid trial / rewards claim |
| **＋** | GET | `/subscription/status` | msisdn (q) | Active/trial/expiring/paused/closing + banners |
| **＋** | POST | `/subscription/resume` | familyId, msisdn | Member takes over pack in grace |

## Circle & Home

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| ✓ | POST | `/circle/create` | consentVersion | Create circle after pack success (admin=self) |
| ✓ | GET | `/circle/bootstrap` | familyId (q) | Empty-state landing after create |
| ✓ | GET | `/home` | familyId (q) | Primary home aggregate (circle status, me, members, alerts, responders) |
| **＋** | POST | `/home/refresh-signals` | familyId (q) | Trigger signal refresh |

## Settings & Roles

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| **＋** | GET | `/settings` | familyId (q) | Settings hub (role-aware) |
| ✓ | POST | `/roles` | membershipId, role | Make/demote co-admin |
| **＋** | PUT | `/responders` | responders | Set responder list |
| ✓ | POST | `/members/{membershipId}/remove` | membershipId (path) | Remove member |
| **＋** | POST | `/circle/leave` | familyId, msisdn | Leave (parental lock) |
| **＋** | GET | `/circle/close-preview` | familyId (q) | Admin-leave / closing consequences |

## Members & Invites

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| **＋** | GET | `/members/candidates` | familyId (q) | Family Mode members + app-installed + Airtel flag |
| **＋** | POST | `/members/validate` | familyId, msisdn | Validate MSISDN before invite |
| ✓ | POST | `/invites/send` | familyId, invites | Send invite(s) with features + relationship |
| **＋** | GET | `/invites/list` | familyId (q) | Pending invites with expiry |
| **＋** | POST | `/invites/resend` | inviteId | Resend (max 3/30d) |
| **＋** | GET | `/features/catalog` | — | Default vs advanced feature catalog |
| **＋** | GET | `/invites/{inviteId}` | inviteId (path) | Invite detail for app |
| ✓ | POST | `/invites/{inviteId}/respond` | inviteId (path), action | Accept/decline (+switch-circle confirm) |
| **＋** | GET | `/invites/web/{token}` | token (path) | Non-app invite page |
| **＋** | POST | `/invites/web/{token}/respond` | token (path), action | Non-app accept/decline |

## Permissions

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| **＋** | GET | `/permissions/status` | membershipId (q) | Feature-permission matrix |
| **＋** | POST | `/permissions/ack` | items | Record granted/denied permissions |

## Member Page

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| **＋** | GET | `/members/{membershipId}` | membershipId (path) | Member detail aggregate |
| **＋** | GET | `/members/{membershipId}/features` | membershipId (path) | Feature enablement + health |
| **＋** | PUT | `/members/{membershipId}/features` | membershipId (path), feature, enabled | Toggle a feature |
| **＋** | GET | `/members/{membershipId}/safety-report` | membershipId (path) | Safety report (3 months) |
| **＋** | POST | `/members/{membershipId}/notify-back-online` | membershipId (path) | Subscribe back-online |
| **＋** | POST | `/advanced-features/request` | membershipId, feature | Request Device Safety/Parental activation |

## Check-ins

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| ✓ | GET | `/checkins` | — | List open + recent |
| ✓ | POST | `/checkins` | familyId, targets | Create ad-hoc check-in (1+ targets) |
| ✓ | GET | `/checkins/{id}` | id (path) | Status / escalation stage |
| ✓ | POST | `/checkins/{id}/respond` | id (path), response | I'm okay / need help |
| ✓ | POST | `/checkins/{id}/dismiss` | id (path) | Sender dismisses |
| **＋** | POST | `/checkins/{id}/connected` | id (path) | I've connected with her (after need-help) |
| **＋** | GET | `/checkins/schedules` | — | List schedules |
| **＋** | POST | `/checkins/schedules` | targetMsisdn, action | Create schedule |
| **＋** | PUT | `/checkins/schedules/{scheduleId}` | scheduleId (path), targetMsisdn, action | Update/pause/resume schedule |

## SOS

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| ✓ | POST | `/sos` | familyId, initiatorMsisdn | Create SOS + location snapshot |
| **＋** | GET | `/sos/active` | familyId (q) | Active SOS for home takeover/widget |
| **＋** | GET | `/sos/{sosId}` | sosId (path) | Live SOS state |
| ✓ | POST | `/sos/{sosId}/respond` | sosId (path), responderMsisdn | I'm responding |
| ✓ | POST | `/sos/{sosId}/dissolve` | sosId (path) | Dissolve / sent-by-mistake (sender only) |
| **＋** | POST | `/sos/{sosId}/location` | sosId (path), location | Location pings while active |

## Fraud Alerts

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| ✓ | GET | `/fraud/alerts/active` | familyId (q) | Active fraud alerts for responders |
| **＋** | POST | `/fraud/alerts/{alertId}/warn` | alertId (path) | Send flash/USSD warning |
| **＋** | POST | `/fraud/alerts/{alertId}/end-call` | alertId (path) | Remote disconnect (pending Legal) |

## Device Safety

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| ✓ | GET | `/device-safety/{membershipId}` | membershipId (path) | Status, findings, missing permissions |
| ✓ | POST | `/device-safety/{membershipId}/activate` | membershipId (path) | Admin activate -> request to member |
| ✓ | POST | `/device-safety/{membershipId}/deactivate` | membershipId (path) | Admin/co-admin off |
| ✓ | POST | `/device-safety/sdk/bootstrap` | msisdn | Pairing token for Whalebone SDK |
| **＋** | POST | `/device-safety/scan` | membershipId | Trigger/report Scan Now |
| **＋** | GET | `/device-safety/events` | membershipId (q) | Blocked URLs / app findings history |

## Parental Controls

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| ✓ | GET | `/parental/{membershipId}` | membershipId (path) | Parental hub aggregate |
| **＋** | POST | `/parental/{membershipId}/activate` | membershipId (path), membershipId | Activate + device-code pairing |
| ✓ | GET | `/parental/{membershipId}/schedules` | membershipId (path) | List schedules |
| ✓ | POST | `/parental/{membershipId}/schedules` | membershipId (path), type, action | Create schedule |
| **＋** | PUT | `/parental/{membershipId}/schedules/{scheduleId}` | membershipId (path), scheduleId (path), type, action | Update schedule |
| ✓ | GET | `/parental/{membershipId}/screen-time` | membershipId (path) | Daily limit + today-only + bonus |
| ✓ | PUT | `/parental/{membershipId}/screen-time` | membershipId (path) | Set screen time |
| ✓ | GET | `/parental/{membershipId}/apps` | membershipId (path) | App/category rules |
| ✓ | PUT | `/parental/{membershipId}/apps` | membershipId (path), rules | Set app rules |
| **＋** | POST | `/parental/{membershipId}/pause` | membershipId (path), action | Pause / resume phone |
| **＋** | GET | `/parental/requests` | familyId (q) | More-time / unblock asks |
| **＋** | POST | `/parental/requests` | membershipId, type | Create request |
| **＋** | POST | `/parental/requests/{requestId}/decide` | requestId (path), decision | Approve/decline |
| ✓ | GET | `/parental/{membershipId}/content-filter` | membershipId (path) | Level, categories, allow/block, safe search |
| ✓ | PUT | `/parental/{membershipId}/content-filter` | membershipId (path) | Set content filter |
| ✓ | GET | `/parental/{membershipId}/places` | membershipId (path) | Geofences |
| ✓ | POST | `/parental/{membershipId}/places` | membershipId (path), name, lat, lng | Create place |
| **＋** | PUT | `/parental/{membershipId}/places/{placeId}` | membershipId (path), placeId (path), name, lat, lng | Update place |
| **＋** | GET | `/parental/{membershipId}/usage` | membershipId (path) | Today usage + trends |
| **＋** | GET | `/parental/{membershipId}/location` | membershipId (path) | Live location (no history) |

## Alerts & History

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| **＋** | GET | `/alerts` | familyId (q), days (q) | Active + history, role-scoped filters |
| **＋** | GET | `/alerts/{alertId}` | alertId (path) | Alert detail |
| ✓ | GET | `/reports/weekly` | familyId (q) | Weekly summary (future) |

## Signals & Lifecycle

| ± | Method | Path | Mandatory fields | Purpose |
|---|---|---|---|---|
| **＋** | GET | `/signals/{membershipId}` | membershipId (path) | Reachability + battery + ringer + last-on-network |
| **＋** | POST | `/signals/subscribe-back-online` | membershipId | Subscribe back-online (alias B24) |
| **＋** | GET | `/lifecycle/events` | familyId (q) | Port-out / SIM-swap / ownership / uninstall |
| **＋** | POST | `/consent/reconfirm` | membershipId, consentVersion | Non-Airtel periodic re-consent |

## Finer-grained additions beyond the raw list

These 5 sub-resources were split out so updates are RESTful (not new scope, just method-correct):

- `PUT /checkins/schedules/{scheduleId}` — update one schedule
- `POST /invites/web/{token}/respond` — non-app accept/decline
- `POST /parental/requests/{requestId}/decide` — approve/decline a child request
- `PUT /parental/{membershipId}/places/{placeId}` — update one geofence
- `PUT /parental/{membershipId}/schedules/{scheduleId}` — update one parental schedule

## Open items (unchanged)

- Routes under `/befe/fsc/v1` are **proposals** pending Guardian registration.
- **GEOFENCE / INACTIVITY** (places, signals) still has **no Network owner** downstream (gap G7).
- History (`/alerts`) + lifecycle compose **Network events + Whalebone fraud + UCM titles**.
- BEFE is **stateless / consume-only** (no DP persist), per the ADR.

*Generated from `befe-upstream-swagger.json`; mandatory fields are the `required` request params/bodies per operation.*