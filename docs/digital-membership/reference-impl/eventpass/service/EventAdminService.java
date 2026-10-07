package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.document.EventDocument;
import com.airtel.userprofile.eventpass.dto.request.EventUpsertRequest;

/** Admin — manage events (the source of {@code endTime} that drives the 30-day TTL cleanup). */
public interface EventAdminService {

	EventDocument upsert(EventUpsertRequest request, String actor);

	EventDocument get(String eventId);

	/** Close an event (active=false) without deleting it; the TTL still purges at endTime+30d. */
	void close(String eventId, String actor);
}
