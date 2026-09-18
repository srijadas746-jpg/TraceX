-- ============================================================
-- TraceX Database Schema (Frozen Source of Truth)
-- Entities: User, Case, Evidence, CustodyRecord, SecurityEvent, Finding
-- ============================================================

PRAGMA foreign_keys = ON;

-- 1. Users
CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('ADMIN', 'INVESTIGATOR')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Cases ("Case" is quoted as it is a SQL reserved keyword)
CREATE TABLE IF NOT EXISTS "Case" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'CLOSED')),
    investigator_id INTEGER NOT NULL REFERENCES User(id) ON DELETE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

-- 3. Evidence
CREATE TABLE IF NOT EXISTS Evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES "Case"(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    source TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    sha256_original TEXT NOT NULL,
    sha256_current TEXT,
    integrity_status TEXT NOT NULL DEFAULT 'NOT_VERIFIED' CHECK(integrity_status IN ('VERIFIED', 'MODIFIED', 'MISSING', 'NOT_VERIFIED')),
    description TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Chain of Custody Records (Append-Only)
CREATE TABLE IF NOT EXISTS CustodyRecord (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL REFERENCES Evidence(id) ON DELETE CASCADE,
    action TEXT NOT NULL CHECK(action IN ('COLLECTED', 'TRANSFERRED', 'REVIEWED', 'VERIFIED', 'EXPORTED')),
    actor_id INTEGER NOT NULL REFERENCES User(id) ON DELETE RESTRICT,
    prev_status TEXT,
    new_status TEXT,
    remarks TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Security Events (Parsed from synthetic logs)
CREATE TABLE IF NOT EXISTS SecurityEvent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES "Case"(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_user TEXT,
    source TEXT NOT NULL,
    ip_ref TEXT,
    event_timestamp TIMESTAMP NOT NULL,
    raw_line TEXT
);

-- 6. Findings (Rule indicators and Correlation outcomes)
CREATE TABLE IF NOT EXISTS Finding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES "Case"(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK(kind IN ('INDICATOR', 'CORRELATION')),
    rule_or_key TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    related_event_ids TEXT,
    related_evidence_ids TEXT,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_evidence_case ON Evidence(case_id);
CREATE INDEX IF NOT EXISTS idx_event_case_time ON SecurityEvent(case_id, event_timestamp);
CREATE INDEX IF NOT EXISTS idx_finding_case ON Finding(case_id);
CREATE INDEX IF NOT EXISTS idx_custody_evidence ON CustodyRecord(evidence_id);
