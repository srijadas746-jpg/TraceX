# TraceX — Digital Incident Investigation & Evidence Management System
## Project Statement & Specification Document

### 1. Problem Statement
Academic digital forensics and incident response (DFIR) exercises routinely suffer from a major educational tooling gap: students and educators are typically forced to either interact with superficial static mockups that simulate no real forensic properties, or attempt to configure enterprise, proprietary platforms (such as EnCase, FTK, or cloud SIEMs) that require intrusive kernel drivers, complex infrastructure, and excessive setup overhead. Furthermore, existing generic log-viewer applications fail to model core digital forensics imperatives: they lack cryptographic integrity auditing, permit silent record alteration, lack chain-of-custody tracking, and frequently misrepresent unverified heuristic alerts as confirmed facts.

**TraceX** solves this problem by providing a transparent, locally runnable, educational digital forensics and incident response workspace that integrates evidence acquisition, SHA-256 integrity verification, append-only custody tracking, synthetic log parsing, deterministic rule-based analysis, chronological timeline reconstruction, and multi-entity correlation into one unified, explainable architecture.

---

### 2. Scope of the Project
TraceX is specifically scoped as a safe, educational DFIR workstation operating on synthetic incident artifacts.

#### In-Scope:
1. **Case & Investigation Lifecycle:** Opening, tracking, updating, and concluding incident containers.
2. **Digital Evidence Management:** Secure acquisition, validation, storage outside web-servable paths, and SHA-256 cryptographic baseline hashing.
3. **Evidence Integrity Verification:** On-demand byte-level re-hashing with status transitions (`VERIFIED`, `MODIFIED`, `MISSING`, `NOT_VERIFIED`) and automatic critical finding triggers on tampering.
4. **Append-Only Chain of Custody:** Legally inspired, tamper-evident action ledger where historical rows are permanently immutable.
5. **Synthetic Security Log Parsing:** Robust ingestion of CSV and JSON Lines formats with error tolerance for malformed rows.
6. **Deterministic Rule Engine (No Black-Box ML):** Fully explainable, whiteboard-defensible detection rules (R1 to R4) covering brute-force clusters, account lockouts, suspicious privilege escalations, and evidence modification.
7. **Incident Timeline Reconstruction:** Chronological ordering algorithm operating in $O(n \log n)$ time, merging observed security events and system-generated findings with day-by-day clustering.
8. **Multi-Entity Correlation Engine:** Non-causal linkage of evidence, users, sources, and external network origins within bounded temporal windows.
9. **Evidentiary Strength Separation:** Formal system-wide separation between Observed Evidence, Detected Indicators, and System Findings (never labeled as "Confirmed Facts").
10. **Structured Investigation Reporting:** Exporting comprehensive, auditable reports in Markdown and JSON formats with print-ready styling.

#### Out-of-Scope (Safety & Academic Boundaries):
- Execution of real malware or offensive intrusion tooling.
- Kernel-level write blocking or physical disk imaging hardware.
- Real network packet sniffing or live intrusion interception.
- Cloud evidence harvesting or mobile device firmware dumping.
- Black-box machine learning anomaly detection models.

---

### 3. Target Users
- **Cybersecurity & Digital Forensics Students:** Applying foundational DFIR concepts, hashing mathematics, custody tracking, and timeline reconstruction in a safe environment.
- **Academic Evaluators & Viva Panels:** Assessing computer science rigor (relational normalization, 3NF, data structures, algorithm complexity, OOP service patterns) and cybersecurity engineering.
- **Incident Response Trainees:** Learning the operational distinction between tangible evidence, rule-based indicators, and system inferences.

---

### 4. High-Level Features
- **Role-Based Access Control (RBAC):** Distinct administrative (`ADMIN`) and investigative (`INVESTIGATOR`) session boundaries protected with Werkzeug password hashing.
- **Cryptographic Evidence Ledger:** SHA-256 chunked hashing with an interactive tamper demonstration utility.
- **Auditable Audit Trail:** Immutable custody logging capturing actor IDs, prior states, new states, timestamps, and investigator remarks.
- **Resilient Log Ingestor:** Error-tolerant CSV/JSONL parsing engine that isolates malformed records without halting execution.
- **Command Center Dashboard:** Dynamic Chart.js visualizations tracking evidence integrity health and finding severity distributions.
- **One-Click Forensics Report Generation:** Structured export compiling case metadata, evidence summaries, custody histories, indicator catalogs, and unified timelines.
