# Family Safety — Device Info (telemetry) requirements

**Date:** 24 Nov 2026 · **Source:** Safety Circle Figma screens + PRD §6.1/6.4 · **Feeds:** blocker **AI-2** (finalize `device/status/fetch` `ParameterName` ENUM)
**Flow:** Telemetry SDK → Kafka → Network Device-Telemetry hub → orchestrator **fetch only** (consume-only, no persist).

## 1. What the screens actually need

From the **My Safety Circle** home, member cards, "Their phone" section, permissions screen and Alerts & history:

- Member card: **battery % (82%), signal bars, reachability ("Reachable · just now"), ringer** + **last-updated time**.
- "Their phone": **Phone off** (when it switches off), **No network** (when it loses network), **Battery and signal** (+ low-battery alert).
- Permissions: **Location — only during an SOS**; Critical alerts ring even on silent (needs **ringer**).
- Alerts & history: "**Mom's phone was off**", low-battery, back-online — i.e. **reachability + battery + charging** events.
- Number states (US 11): "**Number inactive**", non-Airtel, SIM-swap/port — needs **SIM status**.

**Feature-health flags** (`checkinWorking`/`sosWorking`) are derived from **permissions**, not telemetry (separate `permission/*` API).

## 2. Requirement matrix — the candidate `device_*` params

| Parameter | Needed | Screen / feature | Maps to (DeviceDetail / ENUM) | Notes |
|---|---|---|---|---|
| `device_battery_info` | **P0** | Card "82%"; low-battery alert ≤20% (US 25) | `BATTERY_PERCENT` | core signal |
| `device_battery_plugin` / `device_battery_plugout` | **P0** | Charging flag; **reset** low-battery alert after charge (US 25) | `CHARGING` | drives alert lifecycle |
| `device_network_reachability_info` | **P0** | "Phone off" / "No network" / reachable + last-on-network (US 24) | `REACHABILITY` (REACHABLE/SWITCHED_OFF/NO_COVERAGE), `LAST_ON_NETWORK` | **core**; phone-off & back-online alerts |
| `device_ringer_status_info` | **P0** | Ringer on card; SOS/check-in "rings even on silent" | `RINGER_MODE` (NORMAL/VIBRATE/SILENT) | Android |
| `device_ringer_change_info` | **P0** | Keeps ringer status fresh (event form of above) | `RINGER_MODE` updates | event push |
| `device_sim_info` | **P0** | "Number inactive"; non-Airtel; SIM-swap/port guard (US 11) | `SIM_STATUS`, `NUMBER_ACTIVE` | SIM/port/ownership lifecycle |
| `device_usage_info` | **P1** | Parental screen-time + usage/trends (US 6.6) | parental `usage` | advanced feature |
| `device_screen_engagement_info` | **P1** | Parental screen time; "last active" liveness | `LAST_SEEN` (partial), parental | mostly parental |
| `device_signal_lock_signal` / `device_signal_unlock_signal` | **P1** | Lock state; last-active liveness | `LOCK_STATE`, `LAST_SEEN` | supports reachability nuance + parental |
| `device_wifi_info` | **P1** | Network **type** for display; off-net Device Safety (Whalebone VPN over Wi-Fi) | `NETWORK_TYPE` = WIFI | low for dashboard; matters for Device Safety coverage |
| `device_call_info` | **P1 (optional)** | Fraud/spam call **context** (on call ≥1 min), call timer | fraud `callActive`/`callDuration` | spam **detection is network-side**; device state only supplements — consent/DPDP |
| `device_hotspot_info` | **No (MVP)** | — not surfaced | — | defer to post-MVP |
| `device_sms_info` | **No (MVP)** | Bank-OTP during call | — | OTP detection is **network/Safe Network**; on-device SMS read is privacy-heavy (DPDP) — **exclude** |

## 3. Needed but **missing** from the candidate list (please add)

| New param | Needed | Screen / feature | Maps to |
|---|---|---|---|
| `device_network_signal_strength` | **P0** | Signal **bars** on member card (US 24) | `NETWORK_STRENGTH` (STRONG/MODERATE/WEAK/NONE) |
| `device_location_info` (GPS) | **P0 (SOS only)** | "Their location — only during an SOS"; live SOS map (US 15) | `LOCATION` — consent-gated, SOS-window only; **LBS fallback is network-side (E7)** |
| `device_last_updated` (per signal) | **P0** | "Reachable · just now" freshness + "last on network at 10:05" | `lastUpdatedOn` per property (E8) |

## 4. Proposed `device/status/fetch` ParameterName ENUM (for AI-2)

**P0 (launch):** `BATTERY_PERCENT`, `CHARGING`, `NETWORK_REACHABILITY`, `NETWORK_STRENGTH`, `NETWORK_TYPE`, `RINGER_MODE`, `SIM_STATUS`, `LAST_ON_NETWORK`, `LOCATION` (SOS-only), plus derived `CHECKIN_WORKING` / `SOS_WORKING` (from permissions, not telemetry).

**P1 (fast-follow / parental):** `LOCK_STATE`, `SCREEN_ENGAGEMENT`, `USAGE`, `CALL_STATE`.

**Excluded (MVP):** `SMS` (network-side OTP), `HOTSPOT`.

Each property returns **value + `lastUpdatedOn`** (+ an `available` flag for iPhone gaps); for a device off/airplane/unreachable, the hub serves the **last value + timestamp** (still-data), and the app shows "last updated …" / "Not confirmed since …". **Cadence:** background refresh is **hourly** (per "Signal · Updates every hour"); SOS fetches fresh/LBS on demand. `RINGER_MODE` is tri-state (NORMAL/VIBRATE/SILENT); `REACHABILITY` includes a combined `SWITCHED_OFF_OR_FLIGHT` value.

## 5. Refinements from the member-page screens (L2/L3)

The Mom/Dad/Riya/own pages, "What's working", "What you share", "Phone permissions" and the offline/stale states add contract detail:

| Observation (screen) | Implication for telemetry |
|---|---|
| **"Signal · Updates every hour"** | Telemetry **cadence is hourly**, not real-time. Fetch returns last value; the app shows "updates every hour". (SOS needs fresh/LBS — separate.) |
| **"Last battery 6%", "Last on-network 6:45 pm"** (Dad offline) | Need **last-known value + timestamp** per signal when the device is unreachable (`lastBatteryLevel`, `lastOnNetworkAt`). |
| **"Last update 11:40 pm", "Not confirmed since 11:40 pm"** | Need a **freshness / staleness** marker per signal (`lastUpdatedOn` + a "stale" flag the app derives). |
| **"Switched off or in flight mode"** badge | `REACHABILITY` must carry a **combined** value when off vs flight can't be separated. |
| **Ringer: "Sound on" / "Vibrate" / "Silent or off"** | `RINGER_MODE` is **tri-state** (NORMAL / VIBRATE / SILENT); "off" rolls into SILENT. |
| **Ringer "Not shared on iPhone"; battery shown; Signal "Glass"** | **iPhone caveats** per signal — ringer not shared, battery on app-open only. Return availability per property. |
| **"Battery and signal — Always" ; "Location — Only during an SOS"** (What you share) | Battery/signal/ringer are **always-shared**; **location only in an SOS window** (consent-gated). |
| **Spam call alerts "on your Airtel number"; OTP "to your responders"** | Fraud/OTP are **network/Safe-Network + Airtel-only** — not device SMS/call content. |
| **Device Safety "What's working": Dangerous websites / Scam links / Ads = Working; "Blocked this month": domain + threat + channel (SMS/WhatsApp) + date** | These are **Whalebone events** (`/events/search`), NOT device telemetry — `{domain, threat_type, channel, timestamp}`. Keep out of the device/status ENUM. |
| **"A permission is missing" → SOS "Location off"; Phone permissions: Notifications / Critical alerts / Location (Always vs While-using)** | **Permissions drive the Working / Not-Working flags** via the `permission/*` API — `checkinWorking`/`sosWorking` are computed, not telemetry. Permission set: LOCATION (ALWAYS/WHILE_USING/OFF), NOTIFICATION, CRITICAL_ALERTS. |
| **"Dad's phone was off — Off for 4 hours, back on at 10:40 pm"; "Dad's phone is off — your check-in goes out when his phone is back on"** | Reachability needs **transition events**: off→on with **offline duration** + back-on timestamp (drives the back-online alert AND **defers a queued check-in** until the phone is back on). Network-sourced. |
| **Check-in SMS/IVR fallback ("Reply 1 if fine, 2 if need help"; "Airtel called her, no answer"); TIME-SENSITIVE push** | Messaging/IVR + notification channel — **not device telemetry**; confirms the check-in escalation contract (push → SMS → IVR), owned by CLM/Bumblebee + Network. |
| **Spam: "Unknown number" / "Caller: Not in her contacts" / "Possible spam call"; "Bank OTP — Not received / Not shared"** | Classifying a caller as **unknown vs known needs CONTACTS** (device permission) — new. Spam-flag + OTP detection stay **network/Safe-Network**; device supplies only the contacts match. |
| **SOS: live map/location; "Dad has no internet → SOS by SMS → airtel.in/sos/…"; "Call 112"; home-screen/lock widget; Live Activity / ongoing notification; SOS card shows "Battery 76%"** | **GPS location** (SOS window), **no-internet SOS via SMS short-code** + native **112**, and **widget / Live Activity / ongoing notification** are **device/OS capabilities** (app side), not telemetry fetch; battery % is reused in the SOS card. |
| **Parental: app categories (social/messaging/games/video), per-app toggles, "Instagram is blocked", scheduled blocks** | Needs the **installed-app inventory / app ids** on the child device (Whalebone app-catalogue + device) for app blocking — P1. Not a dashboard telemetry signal. |

## 6. Master list — all device info (single consolidated list)

Everything surfaced across **all** the Safety Circle screens, de-duplicated, with where it comes from and priority.

### A. Device telemetry — fetched via `GET /device/status/fetch` (hourly; last value + `lastUpdatedOn` + `available`)
| # | Signal (param) | ENUM | Priority | Used by |
|---|---|---|---|---|
| 1 | `device_battery_info` | `BATTERY_PERCENT` | P0 | card %, low-battery ≤20% |
| 2 | `device_battery_plugin` / `device_battery_plugout` | `CHARGING` | P0 | charging; reset low-battery alert |
| 3 | `device_network_reachability_info` (+ transition: offline duration, back-on) | `NETWORK_REACHABILITY` (REACHABLE / SWITCHED_OFF / NO_COVERAGE / SWITCHED_OFF_OR_FLIGHT), `LAST_ON_NETWORK` | P0 | phone-off / no-network / back-online; check-in deferral |
| 4 | `device_network_signal_strength` *(add)* | `NETWORK_STRENGTH` (STRONG/MODERATE/WEAK/NONE) | P0 | signal bars |
| 5 | `device_wifi_info` / network type | `NETWORK_TYPE` (WIFI/5G/4G/…) | P0/P1 | network type; off-net Device Safety |
| 6 | `device_ringer_status_info` | `RINGER_MODE` (NORMAL/VIBRATE/SILENT) | P0 | ringer on card; ring-even-on-silent |
| 7 | `device_ringer_change_info` | `RINGER_MODE` (event) | P0 | keep ringer fresh |
| 8 | `device_sim_info` | `SIM_STATUS`, `NUMBER_ACTIVE` | P0 | number inactive, port-out, SIM-swap, non-Airtel |
| 9 | `device_location_info` (GPS) *(add)* | `LOCATION` | P0 (SOS only) | live SOS map; consent-gated |
| 10 | per-signal freshness *(add)* | `lastUpdatedOn` + stale flag | P0 | "just now" / "Not confirmed since" |
| 11 | `device_contacts_info` *(add)* | `CONTACTS_MATCH` (via permission) | P0 | caller "not in contacts" → OTP/unknown-call alert |
| 12 | `device_usage_info` | `USAGE` | P1 | parental screen-time/usage |
| 13 | `device_screen_engagement_info` | `SCREEN_ENGAGEMENT` | P1 | parental; last-active liveness |
| 14 | `device_signal_lock_signal` / `device_signal_unlock_signal` | `LOCK_STATE` | P1 | lock state; liveness |
| 15 | `device_app_inventory` (installed apps) *(add)* | `APP_LIST` | P1 | parental app blocking |
| 16 | `device_call_info` | `CALL_STATE` | P1 (optional) | fraud call context (spam = network) |
| 17 | `device_sms_info` | — | **Excluded (MVP)** | OTP is network-side; DPDP |
| 18 | `device_hotspot_info` | — | **Excluded (MVP)** | not surfaced |

### B. Device / OS capabilities — app side, NOT a telemetry fetch
SOS home-screen/lock widget · Quick Settings tile / Control Centre · iPhone Live Activity / Android ongoing notification · no-internet **SOS via SMS short-code** + native **112** dial · critical/time-sensitive push · presidential alert.

### C. Permissions — via `permission/*`, drive Working/Not-Working (computed, not telemetry)
LOCATION (ALWAYS / WHILE_USING / OFF), NOTIFICATION, CRITICAL_ALERTS, CONTACTS, BACKGROUND_LOCATION, DISPLAY_OVER_APPS, FULL_SCREEN_ALERT, RUN_IN_BACKGROUND.

### D. Not device telemetry — other systems
Device-Safety blocked events `{domain, threat_type, channel, timestamp}` → **Whalebone `/events`** · spam-flag + OTP detection → **Network / Safe Network** · check-in SMS/IVR escalation → **CLM/Bumblebee + Network** · feature Working/Not-Working → **permissions**.

## 7. Privacy / governance notes

- **Consume-only**: orchestrator fetches; it never stores device/telemetry (DPDP, zero-persist).
- **Location** only within an active SOS window, consent-gated; otherwise not fetched.
- **SMS / call content** excluded — OTP/spam is network-detected; no on-device message reading in MVP.
- **Non-Airtel / no-app** members: only app-sourced signals (battery/ringer) where available; network signals (reachability, strength, last-on-network) are **Airtel-only**.
- **iPhone**: battery updates on app-open only; ringer/strength may be N/A — mark "Not available on iPhone".

---

*Prepared to finalize the device telemetry contract with the Device Telemetry team (AI-2). P0 set unblocks the Home/Member dashboard and reachability/low-battery alerts; P1 set covers parental + liveness.*
