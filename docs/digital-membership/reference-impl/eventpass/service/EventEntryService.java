package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.document.ScanLogDocument;
import com.airtel.userprofile.eventpass.dto.request.EntryScanRequest;
import com.airtel.userprofile.eventpass.dto.response.EntryScanResponse;

import java.util.List;

/** API 3 — record an entry / goodie redemption after a scan. Returns the gate decision. */
public interface EventEntryService {

	/**
	 * @param agentSessionId the agent's active scanning session (event + checkpoint bound to it)
	 * @param request        decoded qrToken + checkpoint + scanRequestId (idempotency key)
	 */
	EntryScanResponse recordEntry(String agentSessionId, EntryScanRequest request);

	/** Admin (FR35) — full chronological scan history for a customer, for dispute resolution. */
	List<ScanLogDocument> scanHistory(String customerMsisdn);
}
