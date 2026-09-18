# TraceX — Digital Incident Investigation & Evidence Management System
## Academic Project Report & Technical Documentation
**Course:** Cyber Forensics & Digital Investigation (CSE Specialization)  
**Author:** Student Lead Architect & Engineer  
**Institution:** School of Computer Science & Engineering (VIT)  

---

### 1. Cover Page
- **Project Title:** TraceX — Digital Incident Investigation & Evidence Management System
- **Tagline:** *"From evidence to timeline — a transparent forensic investigation workspace."*
- **Date of Submission:** September 2026
- **Architecture Freeze Version:** 1.0.0
- **Technology Stack:** Python 3.13, Flask 3.1, SQLite (3NF), Jinja2, HTML5/CSS3, Vanilla JavaScript, Chart.js

---

### 2. Introduction
In contemporary digital forensic investigations, preserving data authenticity, preventing spoliation, and establishing an unbroken chain of custody are paramount. Modern security incident response teams handle massive volumes of disparate event logs, host artifacts, and memory snapshots. However, the software tooling ecosystem predominantly consists of either closed-source, expensive enterprise suites (such as Guidance EnCase or OpenText FTK) that are inaccessible for rapid academic pedagogy, or simplistic log viewers that lack forensic guarantees.

**TraceX** was conceived and engineered to bridge this gap. Designed as a local, transparent, and auditable digital forensics and incident response (DFIR) workspace, TraceX models authentic forensic workflows on safe, synthetic incident artifacts. The application strictly maintains the distinction between tangible physical/digital evidence, heuristic indicators, and automated system inferences, embodying the highest standards of scientific methodology.

---

### 3. Problem Statement
Educational cybersecurity exercises routinely face two recurring failures:
1. **The Static Mockup Dilemma:** Web applications that merely store files and display rows without computing cryptographic integrity, simulating forensic custody, or executing deterministic analysis.
2. **The Proprietary Complexity Barrier:** Enterprise tools that require commercial dongles, complex infrastructure, and opaque analysis pipelines that hinder student comprehension during technical viva defense.

TraceX directly resolves this problem by implementing a transparent 3-tier architecture with:
- Verifiable cryptographic integrity checking using NIST-standard SHA-256.
- An auditable, append-only chain of custody where past actions are immutable.
- A deterministic, rule-based detection engine devoid of probabilistic "black-box" models.
- An $O(n \log n)$ chronological incident timeline reconstruction.
- An explainable, non-causal multi-entity correlation engine.

---

### 4. Functional Requirements
The system delivers six major functional modules matching the approved blueprint:

1. **Case Management:**
   - Create, retrieve, filter, update, and close investigation case containers.
   - Associate incident classifications and investigator ownership.
2. **Digital Evidence Management:**
   - Ingest synthetic evidence files with filename sanitization and extension allow-listing.
   - Compute initial chunked SHA-256 baseline digests upon acquisition.
   - Re-verify evidence integrity on demand, updating state to `VERIFIED`, `MODIFIED`, or `MISSING`.
   - Provide an interactive simulation utility to demonstrate tamper detection in real time.
3. **Chain of Custody:**
   - Automatically record state-changing actions (`COLLECTED`, `TRANSFERRED`, `REVIEWED`, `VERIFIED`, `EXPORTED`).
   - Enforce an immutable, append-only ledger pattern.
4. **Log Analysis & Rule Engine:**
   - Parse CSV and JSON Lines log streams, safely skipping malformed rows.
   - Execute deterministic detection rules:
     - **R1 (MEDIUM):** 5+ failed logins for the same user within 10 minutes.
     - **R2 (HIGH):** Account lockout preceded by failed attempts within 15 minutes.
     - **R3 (HIGH):** Unusual access followed by permission change within 15 minutes.
     - **R4 (CRITICAL):** Evidence integrity violation (`MODIFIED` status).
5. **Timeline Reconstruction:**
   - Merge `SecurityEvent` and `Finding` rows into a unified chronological sequence.
   - Sort in $O(n \log n)$ time and cluster by calendar date.
6. **Correlation & Investigation Reporting:**
   - Correlate entities sharing usernames, external IP addresses, or log sources.
   - Compile comprehensive, structured reports in printable HTML, Markdown, and JSON formats.

---

### 5. Non-Functional Requirements
1. **Security & Confidentiality:**
   - Passwords hashed using Werkzeug PBKDF2:SHA-256 with secure salts.
   - Session cookies secured with `HttpOnly` and `SameSite=Lax`.
   - Role-Based Access Control enforced server-side via `@role_required`.
   - 100% parameterized SQL queries preventing SQL injection.
   - Evidence files stored strictly outside `static/` to prevent unauthorized scraping.
2. **Reliability & Audit Integrity:**
   - Append-only database repository for custody records preventing history alteration.
   - Fault-tolerant log parsing that isolates bad rows without terminating execution.
3. **Performance & Efficiency:**
   - Database indexes on `(case_id, event_timestamp)`, `Evidence(case_id)`, `Finding(case_id)`.
   - Chunked file I/O (64 KB buffers) for evidence hashing preventing memory exhaustion.
4. **Usability & Explainability:**
   - High-contrast cyber DFIR visual theme with clear status badges and evidentiary strength tags.
   - Complete empty states and informative flash feedback on every view.

---

### 6. System Architecture
TraceX implements a 3-tier layered software pattern:
- **Presentation Layer:** Jinja2 server-rendered templates styled with modern CSS and vanilla JavaScript. Dynamic charts powered by Chart.js.
- **Controller / Middleware Layer:** Flask Blueprints (`auth`, `cases`, `evidence`, `logs`, `timeline`, `reports`) coupled with CSRF protection and RBAC decorators.
- **Service Layer:** Independent domain classes (`AuthService`, `CaseService`, `EvidenceService`, `HashService`, `CustodyService`, `LogAnalysisService`, `TimelineService`, `CorrelationService`, `ReportService`).
- **Repository Layer:** Data access objects (`UserRepository`, `CaseRepository`, `EvidenceRepository`, `CustodyRepository`, `EventRepository`, `FindingRepository`) executing parameterized SQL.
- **Storage Layer:** SQLite database (`database/tracex.db`) with foreign key enforcement and isolated evidence directory (`evidence-store/`).

---

### 7. Design Diagrams
*(Detailed textual and graphical diagrams are maintained in `docs/uml/` and `docs/er-diagram.svg`)*:
- **Use Case Diagram:** Documents Investigator and Administrator actors interacting with the 11 system use cases.
- **Workflow Diagram:** Depicts the 16-step investigative lifecycle from user authentication to report export.
- **Sequence Diagrams:** Models Evidence Acquisition, Hash Verification, Log Ingestion, and Timeline Generation.
- **Class Diagram:** Illustrates OOP relationships between Models, Services, and Repositories.
- **ER Diagram:** Depicts the 6-table normalized relational schema with primary and foreign key constraints.

---

### 8. Design Decisions & Rationale
1. **Flask + SQLite vs. Complex Frameworks:** Flask provides a lightweight, transparent micro-framework without opaque abstraction layers. SQLite eliminates daemon configuration overhead, enabling 100% reproducible local execution for academic panels.
2. **Rule-Based Engine vs. Machine Learning:** Real digital forensics demands legal defensibility and mathematical determinism. Machine learning models introduce probabilistic unpredictability and false positive ambiguity. Rules R1–R4 can be proven and verified step-by-step.
3. **Append-Only Custody:** Updating or deleting custody records violates forensic integrity. The repository layer strictly excludes update/delete methods for custody entities.
4. **Evidentiary Strength Labeling:** To maintain scientific rigor, TraceX categorizes findings into Observed Evidence, Detected Indicators, and System-Generated Findings, explicitly avoiding the false label of "Confirmed Facts".

---

### 9. Implementation Details
- **Programming Language:** Python 3.13
- **Web Engine:** Flask 3.1.1, Jinja2 3.1.5, Werkzeug 3.1.3
- **Security:** Flask-WTF 1.3.0, WTForms 3.2.2
- **Testing:** Pytest 8.3.5 (10 unit and integration tests)
- **Data Visualizations:** Chart.js 4.4.1

---

### 10. Screenshots & Results
1. **Command Center Dashboard:** Real-time counters and Chart.js visualizations tracking evidence integrity health and finding severity distribution.
2. **Evidence Cryptographic Ledger:** Side-by-side comparison of baseline acquisition hash versus recomputed media hash, displaying `VERIFIED` (green) or `MODIFIED` (red) status badges.
3. **Incident Chronological Timeline:** Unified, vertical timeline cards grouped by day, presenting timestamps, entity users, sources, and evidentiary tags.
4. **Investigation Report:** Professional, printable audit artifact containing executive summary, evidence register, custody trail, rule indicators, and timeline.

---

### 11. Testing Approach
TraceX was verified using a 10-test automated regression suite covering:
- `T01`: Valid evidence SHA-256 baseline match (`VERIFIED`).
- `T02`: Tampered evidence byte alteration detection (`MODIFIED` + Rule R4 `CRITICAL` finding).
- `T03`: Append-only custody logging verification (new rows appended, historical rows unchanged).
- `T04`: Malformed log row isolation (bad lines skipped, valid lines ingested).
- `T05`: Deterministic Rule R1 (`MEDIUM`) and Rule R2 (`HIGH`) execution.
- `T06`: Server-side RBAC enforcement returning `403 Forbidden` for unauthorized roles.
- `T07`: Chronological timeline sorting monotonicity ($O(n \log n)$).
- `T08`: Multi-entity correlation logic.
- `T09`: Complete web route and template rendering validation.
- `T10`: End-to-end 10-minute scripted demonstration scenario.

**Execution Result:** 10/10 tests passed with zero failures and zero warnings.

---

### 12. Challenges Faced & Solutions
1. **Challenge:** Reserved SQL keyword conflict with table name `Case`.  
   *Solution:* Applied standard quoted identifier notation (`"Case"`) across all DDL and parameterized SQL queries while preserving the approved entity name.
2. **Challenge:** Cross-platform file stream differences between Flask `FileStorage` and test `io.BytesIO`.  
   *Solution:* Implemented dual-mode stream saving in `EvidenceService` that handles both `.save()` and chunked `.read()`.
3. **Challenge:** Template naming collisions in Jinja2 with dictionary `.items` method.  
   *Solution:* Utilized explicit key index lookups (`dict['items']`) and dual-aliased dictionary keys (`items` and `timeline_items`).

---

### 13. Learnings & Key Takeaways
- Mastery of 3-tier software architecture and the Repository Pattern in Python.
- Deep practical understanding of cryptographic hashing, bit-level avalanche effects, and non-repudiation in digital forensics.
- Implementation of resilient, fault-tolerant parsing pipelines for unstructured and semi-structured log streams.
- Rigorous application of software testing methodologies with automated Pytest suites.

---

### 14. Future Enhancements
- Visual graph relationship explorer using D3.js or Cytoscape for interactive network graph analysis.
- Integration of STIX / TAXII threat intelligence feeds to match synthetic indicators against known MITRE ATT&CK tactics.
- Automated generation of cryptographically signed PDF forensic reports using ReportLab with embedded X.509 digital signatures.

---

### 15. References
1. NIST Special Publication 800-86: *Guide to Integrating Forensic Techniques into Incident Response*.
2. Carrier, Brian: *File System Forensic Analysis*, Addison-Wesley Professional.
3. Casey, Eoghan: *Digital Evidence and Computer Crime: Forensic Science, Computers, and the Internet*, Academic Press.
4. Python Software Foundation: *Python 3 Standard Library Documentation (hashlib, sqlite3)*.
5. Pallets Projects: *Flask & Werkzeug Architectural Patterns*.
