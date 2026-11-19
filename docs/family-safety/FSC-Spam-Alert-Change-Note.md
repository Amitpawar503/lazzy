# FSC API — Spam Call Alerts + richer Device Status

**Spec:** `1.5-merged` → **`1.6-merged`** · **Base:** `/fsc` · **Date:** 19 Nov 2026
**Files:** `fsc-swagger-merged.html` (Swagger UI) · `fsc-swagger-merged.json`

## A. New — Spam / Fraud Call Alerts (new tag: Fraud Alert Controller)

| # | Method | Path | Purpose |
|---|---|---|---|
| 1 | GET | `/api/v1/fraud/alert/fetch` | Get spam/fraud call **alert data** for responders |
| 2 | POST | `/api/v1/fraud/alert/action` | Record the **warning / action** a responder takes |

**1 — GET `/api/v1/fraud/alert/fetch`** → `ResponseSpamAlertPojo { spamAlertInfos[] }`
- Query: `alertId` (one alert) **or** `familyId` / `msisdn` (active alerts), `status`.
- Each `SpamAlertInfo`: `alertId`, `memberMsisdn`, `callerMsisdn`, `alertType` (SPAM/OTP/FRAUD/PHISHING), `riskLevel` (HIGH/MEDIUM/LOW), **`otpCount`**, `otpShared`, **`callTimerSeconds`** (live call duration), `callStartTime`, `callActive`, `status`, `capturedData` (other data captured for that call window), `lastUpdatedOn`.

**2 — POST `/api/v1/fraud/alert/action`** → `ResponseGenericPojo`
- Body `RequestSpamAlertActionPojo` (required `alertId`, `responderMsisdn`, `action`): `action` = **WARN / END_CALL / MARK_SAFE / NOTIFY_MEMBER / BLOCK_NUMBER**, `actionTimestamp`, `message`, `additionalData`.

## B. Enhanced — `GET /api/v1/device/status/fetch`

Now returns a typed **`DeviceDetail`** per member (alongside the existing raw property list), so the app gets proper device detail instead of generic name/value pairs:

| Field | Meaning |
|---|---|
| `batteryPercent` / `charging` | battery level 0–100, charging flag |
| `ringerOn` / `ringerMode` | ringer audible? (NORMAL/VIBRATE/SILENT) |
| `phoneOff` / `reachable` | phone off/on, currently reachable |
| `networkType` / `networkStrength` | WIFI/5G/4G/… · STRONG/MODERATE/WEAK/NONE |
| `lockState` | LOCKED / UNLOCKED / UNKNOWN |
| **`checkinWorking`** | check-in functional (app + permissions) |
| **`sosWorking`** | SOS functional (app + permissions) |
| `appInstalled`, `lastSeen`, `lastUpdatedOn` | presence + freshness |

The generic `propertyName` enum was also expanded (BATTERY_PERCENT, RINGER_MODE, PHONE_OFF, REACHABLE, CHECKIN_WORKING, SOS_WORKING, …).

**Unchanged:** response envelope (`responseCode`, `responseMessage`, `transactionId`); all other 1.5-merged paths. **15 → 17 paths.**

> Note: the live spam alert (A) is the active-call view for responders; the FRAUD entries in `GET /api/v1/history/fetch` remain the after-the-fact history record.
