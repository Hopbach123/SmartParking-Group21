
CREATE TABLE IF NOT EXISTS parking_slots (
 slot_id TEXT PRIMARY KEY CHECK(slot_id IN ('P01','P02','P03','P04')),
 status TEXT NOT NULL CHECK(status IN ('EMPTY','OCCUPIED','UNKNOWN')),
 received_at TEXT, session_id TEXT
);
CREATE TABLE IF NOT EXISTS parking_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT,
 id TEXT NOT NULL UNIQUE, timestamp TEXT NOT NULL,
 slot_id TEXT NOT NULL REFERENCES parking_slots(slot_id),
 type TEXT NOT NULL CHECK(type IN ('IN','OUT','STATUS')),
 previous TEXT NOT NULL CHECK(previous IN ('EMPTY','OCCUPIED','UNKNOWN')),
 current TEXT NOT NULL CHECK(current IN ('EMPTY','OCCUPIED','UNKNOWN'))
);
CREATE TABLE IF NOT EXISTS gate_commands (
 command_id TEXT PRIMARY KEY, request_fingerprint TEXT NOT NULL,
 requested_status TEXT NOT NULL CHECK(requested_status IN ('OPEN','CLOSED')),
 direction TEXT NOT NULL CHECK(direction IN ('ENTRY','EXIT')),
 state TEXT NOT NULL CHECK(state IN ('PENDING','CONFIRMED','ERROR','TIMEOUT')),
 created_at TEXT NOT NULL, completed_at TEXT, error_code TEXT
);
PRAGMA user_version=1;
