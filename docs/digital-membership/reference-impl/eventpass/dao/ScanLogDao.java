package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.ScanLogDocument;

import java.util.List;
import java.util.Optional;

public interface ScanLogDao {

	ScanLogDocument save(ScanLogDocument log);

	/** Idempotency lookup: the prior terminal result for this scanRequestId, if any. */
	Optional<ScanLogDocument> findByScanRequestId(String scanRequestId);

	/** Full chronological scan history for a customer (dispute API, FR35). */
	List<ScanLogDocument> findByCustomerMsisdnOrderByServerTs(String customerMsisdn);
}
