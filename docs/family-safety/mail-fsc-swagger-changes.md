**Subject:** FSC Swagger updated (v1.6) — Spam Call Alert APIs + richer Device Status

Hi Ashiesh / Network team,

I've updated the FSC swagger to **v1.6-merged** with the changes we discussed. Two additions on top of the 1.5-merged spec — please review for feasibility and owning service.

**1. Spam / fraud call alerts (new — Fraud Alert Controller, 2 APIs)**

- **GET `/api/v1/fraud/alert/fetch`** — returns the live alert data a responder needs during a suspicious call: `otpCount`, `callTimerSeconds` (call duration so far), `callStartTime`, `alertType` (SPAM/OTP/FRAUD/PHISHING), `riskLevel`, `callerMsisdn`, `capturedData` (anything else captured for that window). Query by `alertId`, or by `familyId`/`msisdn` for active alerts.
- **POST `/api/v1/fraud/alert/action`** — records the warning / action a responder takes: `action` = WARN | END_CALL | MARK_SAFE | NOTIFY_MEMBER | BLOCK_NUMBER, with `alertId` + `responderMsisdn`.

Open point: which service owns the live spam-alert capture + the end-call/warn action (Whalebone fraud vs Network messaging)? The after-the-fact FRAUD entries still come through `GET /api/v1/history/fetch`.

**2. Device status enhanced — `GET /api/v1/device/status/fetch`**

Now returns a typed `DeviceDetail` per member (the raw property list stays for back-compat), so the app gets proper detail instead of generic name/value pairs: `batteryPercent`, `ringerOn` / `ringerMode`, `phoneOff`, `reachable`, `networkType` / `networkStrength`, `lockState`, **`checkinWorking`**, **`sosWorking`**, `appInstalled`, `lastSeen`, `lastUpdatedOn` per signal.

Please confirm Network can surface the battery/ringer/phone-off/reachability signals and the check-in / SOS "working" flags (app + permissions health) via the telemetry feed.

**Unchanged:** response envelope (`responseCode`, `responseMessage`, `transactionId`) and all other paths. Spec went 15 → 17 paths.

Swagger attached — open `fsc-swagger-merged.html` in a browser for the interactive UI, or import `fsc-swagger-merged.json` into Postman. A one-page change note (`FSC-Spam-Alert-Change-Note`) is attached as well.

Happy to walk through it in the next sync.

Thanks,
Amit
