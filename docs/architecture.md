# TraceX Architecture Specification & System Blueprint
**Version:** 1.0.0 (Architecture Frozen)  
**Classification:** Digital Forensics & Incident Response (DFIR) Educational Application  

---

## 1. System Architecture Overview

TraceX employs a strict 3-tier layered architecture enforcing low coupling, high cohesion, and single responsibility principles:

```
+-------------------------------------------------------------+
|               Client Presentation Layer                     |
|      (Server-Rendered Jinja2 HTML5 / CSS3 / Vanilla JS)     |
|                   Interactive Chart.js                      |
+-------------------------------------------------------------+
                              |
                              | HTTP / Local Loopback
                              v
+-------------------------------------------------------------+
|             Controller Layer (Flask Blueprints)             |
|   auth_routes | case_routes | evidence_routes               |
|   log_routes  | timeline_routes | report_routes             |
+-------------------------------------------------------------+
                              |
                              | Request Context & CSRF Validation
                              v
+-------------------------------------------------------------+
|         Authentication & RBAC Middleware Layer              |
|        @login_required  |  @role_required('ADMIN', ...)     |
+-------------------------------------------------------------+
                              |
                              | Authorized Model DTOs
                              v
+-------------------------------------------------------------+
|                    Service Domain Layer                     |
|   AuthService         | CaseService         | HashService   |
|   EvidenceService     | CustodyService      | ReportService |
|   LogAnalysisService  | TimelineService     | Correlation   |
+-------------------------------------------------------------+
                              |
                              | Parameterized Queries & Abstractions
                              v
+-------------------------------------------------------------+
|                      Repository Layer                       |
|   UserRepository      | CaseRepository      | EvidenceRepo  |
|   CustodyRepository   | EventRepository     | FindingRepo   |
+-------------------------------------------------------------+
                              |
                              | SQLite PRAGMA foreign_keys = ON
                              v
+------------------------------------+   +--------------------+
|          Database Storage          |   |  Evidence Storage  |
|   database/tracex.db (SQLite 3NF)  |   |  evidence-store/   |
+------------------------------------+   +--------------------+
```

### Architectural Layer Invariants:
1. **No direct database queries from routes:** Route controllers only invoke public methods on Service objects.
2. **Service decoupling:** Services depend only on designated repositories or injected sub-services.
3. **Repository isolation:** Repositories isolate SQL execution using parameterized queries.
4. **Isolated evidence store:** Uploaded files reside outside `static/` to prevent unauthorized web scraping.

---

## 2. Frozen Database Schema (3NF)

The database schema is normalized to Third Normal Form (3NF) and consists of exactly six entities:

```
+-------------------+       1:N       +-------------------+
|       User        |---------------->|      "Case"       |
+-------------------+                 +-------------------+
  |               |                     |       |       |
  | 1:N           | 1:N                 | 1:N   | 1:N   | 1:N
  v               v                     v       v       v
+---------------+ +---------------+ +----------+ +-------------+ +---------+
| CustodyRecord | | Case (Assoc.) | | Evidence | |SecurityEvent| | Finding |
+---------------+ +---------------+ +----------+ +-------------+ +---------+
        ^                                 |
        | 1:N                             |
        +---------------------------------+
```

### Entity Specifications:

#### 1. User
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `username` TEXT UNIQUE NOT NULL
- `password_hash` TEXT NOT NULL (Werkzeug pbkdf2:sha256)
- `role` TEXT NOT NULL CHECK(role IN ('ADMIN', 'INVESTIGATOR'))
- `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

#### 2. Case (Quoted identifier `"Case"`)
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `title` TEXT NOT NULL
- `incident_type` TEXT NOT NULL
- `description` TEXT
- `status` TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'CLOSED'))
- `investigator_id` INTEGER NOT NULL REFERENCES User(id) ON DELETE RESTRICT
- `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- `closed_at` TIMESTAMP

#### 3. Evidence
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `case_id` INTEGER NOT NULL REFERENCES "Case"(id) ON DELETE CASCADE
- `name` TEXT NOT NULL
- `type` TEXT NOT NULL
- `source` TEXT NOT NULL
- `file_path` TEXT NOT NULL
- `file_size` INTEGER NOT NULL
- `sha256_original` TEXT NOT NULL
- `sha256_current` TEXT
- `integrity_status` TEXT NOT NULL DEFAULT 'NOT_VERIFIED' CHECK(integrity_status IN ('VERIFIED', 'MODIFIED', 'MISSING', 'NOT_VERIFIED'))
- `description` TEXT
- `collected_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

#### 4. CustodyRecord (Append-Only)
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `evidence_id` INTEGER NOT NULL REFERENCES Evidence(id) ON DELETE CASCADE
- `action` TEXT NOT NULL CHECK(action IN ('COLLECTED', 'TRANSFERRED', 'REVIEWED', 'VERIFIED', 'EXPORTED'))
- `actor_id` INTEGER NOT NULL REFERENCES User(id) ON DELETE RESTRICT
- `prev_status` TEXT
- `new_status` TEXT
- `remarks` TEXT
- `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

#### 5. SecurityEvent
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `case_id` INTEGER NOT NULL REFERENCES "Case"(id) ON DELETE CASCADE
- `event_type` TEXT NOT NULL
- `event_user` TEXT
- `source` TEXT NOT NULL
- `ip_ref` TEXT
- `event_timestamp` TIMESTAMP NOT NULL
- `raw_line` TEXT

#### 6. Finding
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `case_id` INTEGER NOT NULL REFERENCES "Case"(id) ON DELETE CASCADE
- `kind` TEXT NOT NULL CHECK(kind IN ('INDICATOR', 'CORRELATION'))
- `rule_or_key` TEXT NOT NULL
- `severity` TEXT NOT NULL CHECK(severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
- `related_event_ids` TEXT (JSON Array)
- `related_evidence_ids` TEXT (JSON Array)
- `description` TEXT NOT NULL
- `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

---

## 3. Cryptographic Verification & Custody Trail
- **Hashing Algorithm:** SHA-256 (64-byte hexadecimal representation).
- **Chunked Processing:** Ingests files using 64 KB buffers to handle large binaries without memory spikes.
- **Verification Logic:**
  - $\text{Current Hash} = \text{Original Hash} \implies \text{Status: } \mathbf{VERIFIED}$
  - $\text{Current Hash} \neq \text{Original Hash} \implies \text{Status: } \mathbf{MODIFIED} \implies \text{Trigger Rule R4 (CRITICAL)}$
  - $\text{File Missing on Disk} \implies \text{Status: } \mathbf{MISSING}$
- **Immutability Contract:** `CustodyRepository` contains only `create` and `list` operations. Neither update nor delete methods exist in the codebase.

---

## 4. Deterministic Rule Engine
The rule engine contains four explicit, explainable detection rules (no black-box machine learning):

| Rule ID | Condition | Trigger Window | Kind | Severity | Description Label |
|---|---|---|---|---|---|
| **R1** | $\ge 5$ `LOGIN_FAILED` for same user | $\le 10$ minutes (600s) | INDICATOR | **MEDIUM** | Potentially suspicious authentication activity. |
| **R2** | `ACCOUNT_LOCKED` preceded by failed attempts | $\le 15$ minutes (900s) | INDICATOR | **HIGH** | Security indicator: account lock after repeated failures. |
| **R3** | `UNUSUAL_ACCESS` followed by `PERMISSION_CHANGED` | $\le 15$ minutes (900s) | INDICATOR | **HIGH** | Rule matched: suspicious access-then-privilege-change sequence. |
| **R4** | Evidence integrity status becomes `MODIFIED` | Immediate on verify | INDICATOR | **CRITICAL** | Integrity warning: registered evidence changed after acquisition. |

---

## 5. Timeline Reconstruction Algorithm
- **Input:** Set of $n$ `SecurityEvent` records and $m$ `Finding` records for a given `case_id`.
- **Timestamp Normalization:** Timestamps are converted into normalized UTC strings (`YYYY-MM-DD HH:MM:SS`).
- **Complexity:** Standard Python Timsort achieves $O((n+m) \log (n+m))$ execution.
- **Grouping:** Grouped into contiguous date buckets (`YYYY-MM-DD`) for human-readable investigative review.

---

## 6. Multi-Entity Correlation Model
- Non-causal entity linkage based on:
  1. Shared `event_user` within a 30-minute bounded sliding window.
  2. Shared external `ip_ref` originating actions across multiple distinct usernames.
  3. Evidence filename / source references within security log streams.
- **Evidentiary Language:** Always formulated as "potentially related events" and explicitly disclaims causality.
