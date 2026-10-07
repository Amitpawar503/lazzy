// =============================================================================
// event_agent — single sample document insert.
// Run:  mongosh "<uri>" event_agent.sample-insert.mongo.js
// (run event_agent.collection.mongo.js first to create the collection + indexes)
//
// With the demo TTL (index on createdAt, expireAfterSeconds: 300) this row is
// auto-removed by Mongo ~5 minutes after createdAt. To keep it longer, set
// createdAt further in the past or switch to the production TTL (see the
// collection script).
// =============================================================================

db.event_agent.insertOne({
  _id: "7000000001::ARTLPPAZK",        // composite key = msisdn::eventId
  // ---- agent ----
  msisdn: "7000000001",
  checkpoints: ["ENTRY", "GOODIE"],    // this agent may scan both gates
  active: true,
  // ---- the one event this row is about ----
  eventId: "ARTLPPAZK",
  eventName: "Advantage Club Live",
  venue: "Delhi",
  startTime: ISODate("2026-10-10T14:00:00Z"),
  endTime:   ISODate("2026-10-10T22:00:00Z"),
  // ---- lifecycle ----
  cleanupAt: ISODate("2026-11-09T22:00:00Z"),  // production anchor = endTime + 30d
  createdBy: "9812300000",
  createdAt: new Date(),               // demo TTL removes the row 5 min after this
  updatedAt: new Date()
});

print("inserted event_agent row _id=7000000001::ARTLPPAZK");
