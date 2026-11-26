# Whalebone (Airtel Secure) Integration — Use-Case Analysis

**Date:** 26 Nov 2026 · **Source:** Airtel × Whalebone integration flows (provisioning, device-safety, parental, lifecycle) + agreed-decisions / who-stores-what / status-query tables
**For:** Family Safety orchestrator — the **Whalebone adapter** (Dev 2 track)

## 1. The model in one line

**Family ID = Whalebone `subscription_id`; each member MSISDN = a `device_id`; each service is a *tag* on that device.** Turning a service on/off = adding/removing a tag via **full-list PUT** (not PATCH). Whalebone applies the server-side features automatically from the tags; the phone-side protection (VPN / URL inspection) runs through the **SDK**. Whalebone stores **no family hierarchy, no responders, no contacts** — Airtel owns all of that.

```
Airtel family ID  ─= subscription_id=→  Whalebone subscription
   member MSISDN  ─= device_id=→        Whalebone device  ─ tags=[device-safety, parental-control]
```

## 2. The 8 flows (what the orchestrator must do)

| # | Flow | Orchestrator (Airtel BE) calls |
|---|---|---|
| 1 | Buy Airtel Secure (family pack) | `POST /management/subscriptions` (sub_id=familyId) → `POST /management/devices` (device_id=buyer MSISDN) → provisioned, **no tags, nothing blocked** |
| 2 | Add family member | check rights + family link (**UCM**) → `POST /management/devices` (device_id=member MSISDN, sub_id=familyId) → provisioned, not yet protected |
| 3 | **Device safety ON** | first service → `POST /devices` with `tags=[device-safety]`; else **GET-merge-PUT** `PUT /devices/{MSISDN}` tags = current + device-safety → Whalebone sets all threats blocked → phone: pair-app token, authenticate/importCA, OS VPN consent, start protection; user enables URL inspection (Android Accessibility / iOS Safari ext) |
| 4 | **Parental control ON** | tags += parental-control (same upsert) → Whalebone **no action until parent sets filters** → `PUT .../filter`, `PUT .../applications`, `PUT .../scheduled-filter` → pairing/VPN |
| 5 | **Service OFF** | GET current tags → `PUT /devices/{MSISDN}` tags **without** the removed one → device-safety off: threats not blocked, family allow/deny kept if another device still has it; parental off: schedule deleted, content/app filters not blocked → **if no tag left**, app stops SDK (stopProtection/stopProxy) **but pairing is kept**; MSISDN stays provisioned + active |
| 6 | Family allow/deny list | `POST /management/subscriptions/{familyId}/whitelist` or `/blacklist` (remove: `.../delete`) → **applies to every device in the family** |
| 7 | Open Airtel Secure (status) | `GET /management/subscriptions/{familyId}/devices` (status+tags, **≤500/page**) → map tags→features (Airtel's own table) → **VPN status** (new) + **URL-inspection status** (new) per device → feature screens `GET .../filter`, `.../applications`, `.../scheduled-filter`, family lists |
| 8 | Lifecycle | pack expire/cancel → `POST /subscriptions/{familyId}/suspend` (renew `.../activate`); member removed → `POST /devices/{MSISDN}/suspend`; member moves family → `POST /devices/{MSISDN}/migrate`; new number on paired phone → `POST /devices/{MSISDN}/unpair-app` + SDK unpair/logout |

## 3. Agreed decisions (locked)

1. **Family ID = subscription_id** — no extra field. *(Closed)*
2. **Responders from UCM** — Whalebone stores no responders/contacts. *(Closed)*
3. **No hierarchy at Whalebone** — it knows which MSISDNs are in a family, not who's parent/child; Airtel checks who may manage. *(Closed)*
4. **Services = MSISDN tags** (`device-safety`, `parental-control`) — add/remove switches features automatically. *(Confirmed by Whalebone)*
5. **Status via two endpoints** — VPN status + URL-inspection status; **no single "protected" flag**; API key stays in Airtel BE. *(Answered)*
6. **Toggles are PUT (full tag list), not PATCH.** *(Answered)*
7. **Service→feature mapping lives in Airtel BE** — no mapping API. *(Draft for review)*
8. **On/off defaults** per table C. *(Answered)*

## 4. Who stores what

| Airtel (orchestrator / UCM) | Whalebone |
|---|---|
| Family hierarchy & roles (UCM) · responders (UCM) · **service→feature mapping** · which members are in Airtel Secure · how protection is presented | Family ID (as subscription) · member MSISDNs + status (active/suspended) · **service tags per MSISDN** · feature settings (threats, content, apps, schedules, family allow/deny) · **last reported VPN + URL-inspection status (new)** |

## 5. On/off defaults (table C — key behaviours)

- **Device safety ON** → all threats blocked (new); phone starts VPN via SDK (first time = pair + consent); threat blocking on by default.
- **Device safety OFF** → threats not blocked; family allow/deny **kept** if another family device still has device-safety, else deleted; SDK stops URL inspection.
- **Parental ON** → *nothing blocked until the parent sets filters*; SDK starts if not running.
- **Parental OFF** → schedule deleted; content/app filters not blocked.
- **Both OFF** → PUT leaves an **empty tag list**; MSISDN stays provisioned + active; SDK stopped but **pairing kept** (re-enabling a service later needs no re-pair).

## 6. Status-query model (table D)

| Airtel wants to know | API | Query by | Availability |
|---|---|---|---|
| Family members + status | `GET /management/subscriptions/{id}/devices` | family ID | **Today** |
| One member status + services | `GET /management/devices/{MSISDN}` | MSISDN | **Today** |
| Feature settings | `GET /management/devices/{MSISDN}/…` | MSISDN / family ID | **Today** |
| **VPN protection on/off** | separate Mgmt API endpoint | MSISDN | **New — 1 wk lead** |
| **URL inspection on/off** | separate Mgmt API endpoint | MSISDN | **New — 1 wk lead** |

## 7. New development at Whalebone (lead times)

1. **Tag-driven feature switching** (incl. family allow/deny rule) — **2 weeks**.
2. **VPN protection status** endpoint per device — **1 week**.
3. **URL-inspection status** endpoint per device — **1 week**.
Everything else uses **existing** endpoints; exact paths of the new ones to come with the API docs.

## 8. Implications for our build (Whalebone adapter — Dev 2)

**Adapter responsibilities**
- **Provisioning:** subscription create + device create (idempotent; 409 on existing → GET + resume per ops rules).
- **Tag management as upsert:** always **GET current tags → merge → PUT full list** (never PATCH). Serialize per MSISDN to avoid lost updates.
- **Feature writes:** `PUT /filter` (7 threats always true for device-safety), `/applications`, `/scheduled-filter`; **GET-merge-PUT** so omitted types don't get unblocked.
- **Family lists:** whitelist/blacklist POST + `/delete`, family-scoped.
- **Status composition:** there is **no single protected flag** — the app/orchestrator must **combine** device list + VPN-status + URL-inspection-status into the UI's "Working / Not working". Pagination ≤500/page.
- **Lifecycle:** suspend/activate (pack), device suspend (remove), migrate (move family), unpair-app (device swap).
- **Service→feature mapping table** lives in **our BE** (fixed, not runtime) — keep it in `engine/feature-status` / a config map.
- **Membership ↔ subscriptionId (= familyId) + device_id (= MSISDN)** linkage is Airtel's to hold.

**Risks / open items**
- **3 new Whalebone endpoints** (tag switching 2 wk; VPN + URL status 1 wk each) — gate Device Safety status UI; **exact paths TBD** → hold behind the adapter interface, use mocks until shared. (Maps to our ENV/AI blockers.)
- **Service→feature mapping = "Draft for review"** — confirm before build freeze.
- **Full-list PUT concurrency** — two toggles racing can drop a tag; serialize per device + retry on 409.
- **Pairing kept on both-off** — good (no re-pair), but the app must correctly reflect "provisioned but not protected".
- **Allow/deny list is family-wide**, not per-member — a single list applies to every device; UI must set expectations.
- **iPhone**: URL inspection via Safari extension; parity differs from Android Accessibility.

**Not Whalebone (reinforced):** responders, family hierarchy/roles, who-may-manage, members-in-Secure, and **presentation of protection** are all **Airtel/UCM** — confirms our earlier "Whalebone events + permissions, not device telemetry" boundary.

---

*Analysis of the Airtel × Whalebone integration use-cases. Net: a clean tag-driven model that fits our orchestrator's Whalebone adapter; the only build-gating unknowns are the 3 new Whalebone endpoints (paths + lead time) and the service→feature mapping sign-off.*
