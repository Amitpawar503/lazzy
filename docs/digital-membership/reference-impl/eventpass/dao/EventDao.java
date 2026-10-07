package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.EventDocument;

import java.util.Optional;

public interface EventDao {

	/** Create or update an event; recomputes {@code cleanupAt = endTime + 30d}. */
	EventDocument upsert(EventDocument event);

	Optional<EventDocument> findById(String eventId);

	/** Flip {@code active=false} (e.g. at endTime); the TTL still purges at endTime+30d. @return matched. */
	long setActive(String eventId, boolean active);
}
