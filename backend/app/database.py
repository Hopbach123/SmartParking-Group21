import sqlite3
from contextlib import contextmanager
from pathlib import Path
from app.models import SLOT_IDS

EVENT_TABLE = """CREATE TABLE parking_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT,
 id TEXT NOT NULL UNIQUE, timestamp TEXT NOT NULL,
 slot_id TEXT NOT NULL,
 type TEXT NOT NULL, previous TEXT NOT NULL, current TEXT NOT NULL,
 CHECK ((slot_id IN ('P01','P02','P03','P04') AND type IN ('IN','OUT','STATUS')
 AND previous IN ('EMPTY','OCCUPIED','UNKNOWN') AND current IN ('EMPTY','OCCUPIED','UNKNOWN'))
 OR (slot_id='GATE' AND type='GATE' AND previous IN ('OPEN','CLOSED') AND current IN ('OPEN','CLOSED')))
)"""

class Database:
    def __init__(self,path: Path): self.path=Path(path).resolve()

    @contextmanager
    def connect(self):
        connection=sqlite3.connect(self.path,timeout=10)
        connection.row_factory=sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        try:
            with connection: yield connection
        finally: connection.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0,1,2): raise RuntimeError('Unsupported database schema version')
            if version==1:
                backup=self.path.with_name(self.path.name+'.before-phase04.bak')
                if not backup.exists():
                    with sqlite3.connect(backup) as target: db.backup(target)
            db.execute('BEGIN IMMEDIATE')
            db.execute("""CREATE TABLE IF NOT EXISTS parking_slots (
                slot_id TEXT PRIMARY KEY CHECK(slot_id IN ('P01','P02','P03','P04')),
                status TEXT NOT NULL CHECK(status IN ('EMPTY','OCCUPIED','UNKNOWN')),
                received_at TEXT,session_id TEXT)""")
            if version==1:
                db.execute('ALTER TABLE parking_events RENAME TO parking_events_v1')
                db.execute(EVENT_TABLE)
                db.execute('INSERT INTO parking_events SELECT * FROM parking_events_v1')
                db.execute('DROP TABLE parking_events_v1')
            elif version==0: db.execute(EVENT_TABLE)
            db.execute("""CREATE TABLE IF NOT EXISTS gate_commands (
                command_id TEXT PRIMARY KEY, request_fingerprint TEXT NOT NULL,
                requested_status TEXT NOT NULL CHECK(requested_status IN ('OPEN','CLOSED')),
                direction TEXT NOT NULL CHECK(direction IN ('ENTRY','EXIT')),
                state TEXT NOT NULL CHECK(state IN ('PENDING','CONFIRMED','ERROR','TIMEOUT')),
                created_at TEXT NOT NULL, completed_at TEXT, error_code TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS gate_state (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                status TEXT NOT NULL CHECK(status IN ('OPEN','CLOSED')),
                confirmed INTEGER NOT NULL CHECK(confirmed IN (0,1)),confirmed_at TEXT)""")
            db.execute("INSERT OR IGNORE INTO gate_state VALUES (1,'CLOSED',0,NULL)")
            db.execute("""CREATE TABLE IF NOT EXISTS gate_ack_audit (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, command_id TEXT NOT NULL,
                status TEXT NOT NULL,received_at TEXT NOT NULL,outcome TEXT NOT NULL)""")
            db.executemany('INSERT OR IGNORE INTO parking_slots(slot_id,status) VALUES (?,?)',[(slot,'UNKNOWN') for slot in SLOT_IDS])
            db.execute('PRAGMA user_version=2')
