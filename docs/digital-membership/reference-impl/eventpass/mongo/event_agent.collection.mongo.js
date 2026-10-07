// =============================================================================
// event_agent — the single Event-Pass collection (agent + one event per row)
// mongosh setup script.  Run:  mongosh "<uri>" event_agent.collection.mongo.js
//
// TTL here is set to **5 minutes** (300s) for demo/testing — every document is
// auto-removed by Mongo's TTL monitor ~5 minutes after it is inserted, so you
// can watch the cleanup work without waiting 30 days.
//
//   PRODUCTION: use the 30-day retention instead — drop this TTL index and
//   create the commented one at the bottom (expireAfterSeconds: 0 on cleanupAt,
//   which the app sets to endTime + 30d). Spring Data would otherwise try to
//   auto-create that 0-second index from @Indexed(expireAfterSeconds = 0); for
//   this 5-min demo set the Java field to @Indexed(expireAfterSeconds = 300) on
//   createdAt, or disable auto-index-creation, so the two do not fight.
// =============================================================================

const COLL = "event_agent";

// ---- 1) create (or keep) the collection with a JSON-schema validator --------
if (!db.getCollectionNames().includes(COLL)) {
  db.createCollection(COLL, {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        // composite key msisdn::eventId + the fields the app reads/writes
        required: ["_id", "msisdn", "checkpoints", "active", "eventId", "endTime", "cleanupAt", "createdAt"],
        additionalProperties: true,
        properties: {
          _id:         { bsonType: "string", description: "composite key: msisdn::eventId" },
          msisdn:      { bsonType: "string", description: "agent MSISDN" },
          checkpoints: {
            bsonType: "array",
            minItems: 1,
            uniqueItems: true,
            description: "checkpoints this agent may scan at this event",
            items: { enum: ["ENTRY", "GOODIE"] }
          },
          active:      { bsonType: "bool", description: "soft on/off without deleting the row" },

          // the one event this row is about (denormalized)
          eventId:     { bsonType: "string" },
          eventName:   { bsonType: ["string", "null"] },
          venue:       { bsonType: ["string", "null"] },
          startTime:   { bsonType: ["date", "null"] },
          endTime:     { bsonType: "date", description: "drives retention" },

          // lifecycle
          cleanupAt:   { bsonType: "date", description: "retention anchor (TTL deletes the row after it)" },
          createdBy:   { bsonType: ["string", "null"] },
          createdAt:   { bsonType: "date" },
          updatedAt:   { bsonType: ["date", "null"] }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  print(`created collection ${COLL}`);
} else {
  print(`collection ${COLL} already exists — leaving data in place`);
}

// ---- 2) lookup indexes (point reads by agent / by event) --------------------
db[COLL].createIndex({ msisdn: 1 }, { name: "idx_ea_msisdn" });
db[COLL].createIndex({ eventId: 1 }, { name: "idx_ea_event" });

// ---- 3) TTL index — DEMO: remove each document 5 minutes after it is written -
//         (TTL anchored on createdAt so removal is always "5 min after insert",
//          regardless of the business endTime/cleanupAt values)
db[COLL].createIndex(
  { createdAt: 1 },
  { name: "ttl_event_agent_5min", expireAfterSeconds: 300 }
);
print("TTL index ttl_event_agent_5min created — docs auto-remove 5 min after createdAt");

// ---- sample insert (will be gone ~5 minutes later) --------------------------
// db.event_agent.insertOne({
//   _id: "7000000001::ARTLPPAZK",
//   msisdn: "7000000001",
//   checkpoints: ["ENTRY", "GOODIE"],
//   active: true,
//   eventId: "ARTLPPAZK",
//   eventName: "Advantage Club Live",
//   venue: "Delhi",
//   startTime: ISODate("2026-10-10T14:00:00Z"),
//   endTime:   ISODate("2026-10-10T22:00:00Z"),
//   cleanupAt: new Date(),            // demo: now; TTL on createdAt removes it in 5 min
//   createdBy: "9812300000",
//   createdAt: new Date(),
//   updatedAt: new Date()
// });

// ---- PRODUCTION TTL (30 days after the event ends) --------------------------
// Replace the demo index above with:
//   db.event_agent.dropIndex("ttl_event_agent_5min");
//   db.event_agent.createIndex(
//     { cleanupAt: 1 },
//     { name: "ttl_event_agent_cleanup", expireAfterSeconds: 0 }
//   );
// and have the app set cleanupAt = endTime + 30d (EventAgentDocument.cleanupFrom).
