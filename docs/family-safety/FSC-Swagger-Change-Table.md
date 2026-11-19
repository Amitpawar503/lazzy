# FSC Swagger — API Change Table (v1.5-merged → v1.6-merged)

**Base:** `/fsc` · **Date:** 19 Nov 2026 · **Files:** `fsc-swagger-merged.html` (Swagger UI) · `fsc-swagger-merged.json`

| # | Change | Method | Path | Request (key fields) | Response | Notes |
|---|---|---|---|---|---|---|
| 1 | **New** | GET | `/api/v1/fraud/alert/fetch` | `alertId` *or* `familyId`/`msisdn`, `status` | `ResponseSpamAlertPojo` | Spam/fraud call alert data: `otpCount`, `callTimerSeconds`, `callStartTime`, `alertType`, `riskLevel`, `callerMsisdn`, `capturedData` |
| 2 | **New** | POST | `/api/v1/fraud/alert/action` | `alertId`\*, `responderMsisdn`\*, `action`\* | `ResponseGenericPojo` | Responder action: `action` = WARN / END_CALL / MARK_SAFE / NOTIFY_MEMBER / BLOCK_NUMBER |
| 3 | **Enhanced** | GET | `/api/v1/device/status/fetch` | `familyId` / `msisdn` | `ResponseDeviceStatusDataPojo` + typed `DeviceDetail` | Adds `batteryPercent`, `ringerOn`/`ringerMode`, `phoneOff`, `reachable`, `networkType`/`networkStrength`, `lockState`, **`checkinWorking`**, **`sosWorking`**, `appInstalled`, `lastSeen` |

\* = mandatory. Response envelope (`responseCode`, `responseMessage`, `transactionId`) unchanged. **Total paths: 15 → 17.**

## DeviceDetail fields (enhanced device status)

| Field | Type | Meaning |
|---|---|---|
| `batteryPercent` / `charging` | int / bool | Battery 0–100, charging flag |
| `ringerOn` / `ringerMode` | bool / enum | Audible? · NORMAL / VIBRATE / SILENT |
| `phoneOff` / `reachable` | bool / bool | Phone off/on · reachable on network |
| `networkType` / `networkStrength` | enum / enum | WIFI/5G/4G/… · STRONG/MODERATE/WEAK/NONE |
| `lockState` | enum | LOCKED / UNLOCKED / UNKNOWN |
| `checkinWorking` | bool | Check-in functional (app + permissions) |
| `sosWorking` | bool | SOS functional (app + permissions) |
| `appInstalled` / `lastSeen` / `lastUpdatedOn` | bool / datetime / datetime | Presence + freshness |
