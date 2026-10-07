package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.dao.EventDao;
import com.airtel.userprofile.eventpass.document.EventDocument;
import com.airtel.userprofile.eventpass.dto.request.EventUpsertRequest;
import com.airtel.userprofile.eventpass.service.EventAdminService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class EventAdminServiceImpl implements EventAdminService {

	private final EventDao eventDao;

	@Override
	public EventDocument upsert(EventUpsertRequest r, String actor) {
		if (r.getEndTime().isBefore(r.getStartTime())) {
			throw new IllegalArgumentException("endTime must be after startTime");
		}
		EventDocument event = EventDocument.builder()
				.eventId(r.getEventId())
				.eventName(r.getEventName())
				.venue(r.getVenue())
				.startTime(r.getStartTime())
				.endTime(r.getEndTime())
				.active(true)
				.checkpointsEnabled(r.getCheckpointsEnabled())
				.createdBy(actor)
				.build();
		EventDocument saved = eventDao.upsert(event);   // sets cleanupAt = endTime + 30d
		log.info("Event upserted by {}: eventId={} endTime={} cleanupAt={}",
				actor, saved.getEventId(), saved.getEndTime(), saved.getCleanupAt());
		return saved;
	}

	@Override
	public EventDocument get(String eventId) {
		return eventDao.findById(eventId)
				.orElseThrow(() -> new IllegalArgumentException("No event " + eventId));
	}

	@Override
	public void close(String eventId, String actor) {
		if (eventDao.setActive(eventId, false) == 0) {
			throw new IllegalArgumentException("No event " + eventId);
		}
		log.info("Event closed by {}: eventId={}", actor, eventId);
	}
}
