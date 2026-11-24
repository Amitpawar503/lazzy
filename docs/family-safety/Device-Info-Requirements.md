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

Each property returns **value + `lastUpdatedOn`**; for a device off/airplane/unreachable, the hub serves the **last value + timestamp** (still-data), and the app shows "last updated …".

## 5. Privacy / governance notes

- **Consume-only**: orchestrator fetches; it never stores device/telemetry (DPDP, zero-persist).
- **Location** only within an active SOS window, consent-gated; otherwise not fetched.
- **SMS / call content** excluded — OTP/spam is network-detected; no on-device message reading in MVP.
- **Non-Airtel / no-app** members: only app-sourced signals (battery/ringer) where available; network signals (reachability, strength, last-on-network) are **Airtel-only**.
- **iPhone**: battery updates on app-open only; ringer/strength may be N/A — mark "Not available on iPhone".

---

*Prepared to finalize the device telemetry contract with the Device Telemetry team (AI-2). P0 set unblocks the Home/Member dashboard and reachability/low-battery alerts; P1 set covers parental + liveness.*
