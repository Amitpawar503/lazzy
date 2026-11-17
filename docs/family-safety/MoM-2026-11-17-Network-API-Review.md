# Minutes of Meeting — Family Safety × Network API Review

**Date:** 17 Nov 2026 · **Recording/transcript:** enabled (Bhabani) · **Next meeting:** 18 Nov 2026, 2:00 PM

**Purpose:** Walkthrough of the Network (FSC + OTA) APIs shared by Ashiesh — Family/Member, Check-in, SOS, Device-status, Alarm — to align contracts for the Family Safety orchestrator, provisioning, and the app/history screens.

### Attendees
| Name | Side / role |
|---|---|
| Ashiesh Shukla | **Network** — FSC/OTA API owner (presenter) |
| Bhabani Pati | Network (chair) |
| Nitin | Network |
| Gopal Dave | Network (LBS / location) |
| Amit Pawar | Channel / **Family Safety orchestrator** (BFF) |
| Chitranshi Pathak | Channel (reporting / audit) |
| Shubham Garge | Channel |
| Aditi Rastogi | Product |
| Lokesh Kumar | Design (Figma) |
| Salil Kumar | Subscription / Propositions BE (provisioning) |
| *(consulted, not present)* | Ajay Saini — telemetry/architecture · Parshant Verma — Bumblebee SPOC |

---

## 1. Key decisions

1. **No parent/child concept.** The circle has roles only: **Admin, Sub-admin, Sponsor, Member** (+ Responder). Provisioning must map to these, not parent/child.
2. **No family deletion.** There is no delete-family API — set **family status = Inactive**; all members then auto-become inactive. Admin churn / "delete family" is handled the same way.
3. **Member-add will be removed from `family/update`.** Family update keeps family-level fields only (name, status, description); members are added only via `member/add`.
4. **Check-in: one check-in per member per day** (no second check-in if the first is unanswered; no twice-a-day).
5. **SOS cancel only by the initiator** (Network to add the check). SOS has two stages — **acknowledge** (multiple allowed) and **resolve** (one only).
6. **SOS location:** app sends location in `additionalData`; if absent (device off / no internet / no app), **Network falls back to LBS — during SOS only** (confirmed by Bhabani/Gopal).
7. **SOS over no-internet / no-network:** no internet but network → app sends **SMS to a predefined short code** ("SOS" to 52263) and Network registers the SOS; no network at all → device-native emergency dial **112** (platform-112 integration is future/open).
8. **SOS-kill API not needed** — since the orchestrator does **not persist** data, drop it.
9. **Device data: stored but not processed by Network.** Telemetry SDK → Kafka → Network Device-Telemetry hub stores last values; Network serves **last value + last-updated timestamp** only. No processing/intelligence (e.g. "phone off for 4 hrs", offline/online notifications) — out of current plan.
10. **The orchestrator consumes, does not store** device/telemetry data — fetch only.
11. **Relationship titles (mom/dad) are mapped by Channel via UCM**, not by Network. Spam/fraud history comes from **Whalebone**, not Network.
12. **History/audit screen has no API yet** — Ashiesh saw it for the first time; needs a separate design session. Retention: **minimum 7 days, target up to 30 days** (storage-dependent; BRD to confirm).

---

## 2. Discussion by topic

### 2.1 Family & Member controller (circle)
- `family/create` creates the family ID; members optional at create (array, can add later). Fields: circle name, status (Active default), description, per-member {airtelCustomer 0/1, role, familyId, membershipId (optional), membershipStatus, msisdn}.
- `family/update` can change family name/status; **member-add to be removed** from it (decision #3).
- `family/get` returns full family detail by familyId (used by create/update; low direct use for provisioning).
- `member/add` needs familyId + member msisdn + role (no admin msisdn). `member/delete`, `member/get`, `member/getAll`, `member/role/update` (familyId, memberId, role — Admin/Sub-admin/Sponsor/Member), `member/update` (msisdn/status/role).
- **Provisioning (Salil):** member churn → `member/delete`; admin churn / close family → `family/update` status=Inactive (members cascade inactive). Mapping clarified.

### 2.2 Check-in (create / response / status-check / status-update)
- **Enhancements agreed** (see §3): day selection (every day / weekdays / pick from 7 days), **message** field, **duration** field (how long the schedule runs), `scheduleTime` as **time only**, one-per-day rule.
- Pause/resume already supported; pricing is NOT tied to frequency (handled elsewhere — Network only needs the schedule).
- `response`: yes/no/ok or blank + timestamp + triggerId; multiple responses per scheduled trigger.
- `status-check`: query by familyId / initiatorMSISDN / triggerId → one row per scheduled date (incl. expected date = pending if not yet received). **Add**: filter by specific target member MSISDN, and a date-range param.
- `status-update` (dismiss/pause/resume): **add initiatorMSISDN** so Network can enforce admin-only control (Amit to confirm the control with product).

### 2.3 SOS (create / cancel / update / status-check) + alarm
- `create`: familyId, initiatorMSISDN, triggerId → SOS + backend flow starts immediately (no scheduling).
- `cancel`: **only initiator** (Network to add check).
- `update`: acknowledge (multiple) / resolve (one). Future: allow responder to resolve via `resolvedBy`.
- `status-check`: by familyId/initiatorMSISDN/sosId → records incl. alarm status (active/inactive), ack status, resolution.
- **Location:** via `additionalData`; **LBS fallback during SOS** when app location missing; location sent to all responders.
- **No-internet/no-network:** SMS short-code path and device-112 as above (decision #7).
- `alarm/incoming`: used to push an alarm to the user via network channel when the user has no internet (e.g. **presidential alert**).
- `SOS-kill`: drop (decision #8).

### 2.4 Device status / telemetry
- Flow: **Telemetry SDK (in Thanksapp) → Kafka → Network Device-Telemetry hub (store)**; parallel feed to Network DB. Ownership of the SDK/publisher to be confirmed with **Ajay Saini** (Confluence diagram).
- Network provides a **fetch** API: last value + **last-updated timestamp** per parameter (battery, ringer, network type/strength, location, lock/unlock).
- "Still data" when device off/airplane/unreachable → app must **show last-updated time** to the viewer. For SOS, get **actual/updated** location (LBS); for normal viewing, show still data.
- Fetch returns **latest only** (not point-in-time snapshot at a past event). Device-state-at-event history is a separate discussion.
- Network does **not** process device data (no offline/online notifications, no "phone-off" logic) — out of plan.

### 2.5 History / audit (Figma screen)
- Screen mixes check-in replies, device status ("dad's phone was off"), spam/fraud (**Whalebone**), SOS, etc.
- No unified history API today; Network not prepared — **separate session**. Titles via UCM (Channel). Retention 7–30 days (BRD).

### 2.6 Platform / other
- **Bumblebee / IVR** (notifications): Gopal/Bhabani to reach the Bumblebee SPOC (**Parshant Verma**) — separate call; IVR is a feature there.
- Separate sessions to schedule: **telemetry SDK flow** (Ajay Saini), **Bumblebee/IVR**, **history/audit API**.

---

## 3. APIs that need ENHANCEMENT (existing Network APIs)

| # | API | Enhancement required | Owner |
|---|---|---|---|
| E1 | `POST /family/update` | **Remove** member-addition capability (family-level fields only) | Network |
| E2 | `POST /checkin/create` | Add **day selection** (every day / weekdays / pick from 7 days); add **message** field; add **duration** (how long the schedule runs); make `scheduleTime` **time-only**; enforce **one check-in/day** | Network |
| E3 | `GET /checkin/status-check` | Add **filter by target member MSISDN**; add **date-range** param to bound history | Network |
| E4 | `POST /checkin/status-update` | Add **initiatorMSISDN** → Network validates admin before dismiss/pause/resume | Network (+ Product confirm) |
| E5 | `POST /sos/cancel` | Enforce **cancel only by initiator** | Network |
| E6 | `POST /sos/update` | Allow **responder to resolve** via `resolvedBy` (future flexibility) | Network |
| E7 | `POST /sos/create` (+ flow) | Capture location via `additionalData`; **LBS fallback during SOS** when app location absent; fan location to responders | Network (Gopal/Bhabani) |
| E8 | `GET /device-status/fetch` | Confirm returns **last value + last-updated timestamp** per parameter incl. **location** (Kafka feed) | Network |

**APIs to DROP:** `SOS-kill` (not needed — orchestrator does not persist). *Family deletion:* not applicable (use `family/update` status=Inactive).

---

## 4. APIs / capabilities that need to be BUILT (new)

| # | New capability | What / why | Owner |
|---|---|---|---|
| B1 | **Consolidated History / Audit API** | One circle-activity history over 7–30 days (check-ins, SOS, fraud/spam, events). Not designed yet — separate session. Compose Network (events) + Whalebone (fraud) + UCM (titles via Channel) | Network + Channel + Whalebone |
| B2 | **Telemetry pipeline contract** | Define & confirm Telemetry SDK → Kafka → Device-Telemetry hub (store) + the fetch contract; confirm publisher/owner | Ajay Saini + Network |
| B3 | **LBS location lookup (SOS)** | Network capability to ping LBS and return location when app location is missing — SOS only | Network (Gopal) |
| B4 | **No-internet SOS via SMS short code** | Predefined short-code SMS ("SOS" to 52263) → Network registers SOS | Network + App |
| B5 | **Bumblebee / IVR integration** | Notification + IVR channel for alerts/escalation | Network + Bumblebee (Parshant Verma) |
| B6 | **Device-status processing / intelligence** *(if in scope)* | "Phone off for N hrs", offline/online notifications — currently **out of plan**; new scope if product needs it | TBD (separate discussion) |
| B7 | **Platform-112 emergency trigger** *(future)* | Bring device-native 112 SOS into the platform | Network (future) |

---

## 5. Action items

| # | Action | Owner | Due |
|---|---|---|---|
| A1 | Implement E1–E8 API changes; present the diff | Ashiesh / Network | 18 Nov (2 PM) |
| A2 | Design the consolidated **history/audit** API (B1) | Network + Channel | separate session |
| A3 | Confirm **telemetry SDK flow & owner** (B2) via Confluence diagram | Ajay Saini (via Amit) | next |
| A4 | Confirm with **product**: check-in dismiss admin-only (E4); check-in day-selection UX + duration | Amit / Aditi | 18 Nov |
| A5 | **LBS fallback** for SOS location (B3) | Gopal / Bhabani | next |
| A6 | Reach **Bumblebee SPOC** (Parshant Verma) for notification/IVR (B5) — separate call | Gopal / Bhabani | next |
| A7 | **Retention** decision (7 vs 30 days) in BRD | Aditi / Product | next |
| A8 | Confirm orchestrator **does not send** device-store data (consume-only) | Amit | 18 Nov |

**Next meeting:** 18 Nov 2026, 2:00 PM — Ashiesh walks through the updated APIs (today's changes) and the history topic; schedule separate sessions for telemetry SDK, Bumblebee/IVR, and history.

---

*Captured from the meeting auto-transcript; wording normalised to intent. Names/roles as inferred from the discussion.*
