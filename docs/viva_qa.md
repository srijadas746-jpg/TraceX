# TraceX — Academic Viva Questions & Answers (25 Key Topics)

This reference guide provides clear, concise, technically rigorous answers for faculty evaluations, project presentations, and viva voce panels.

---

### 1. Why TraceX?
**Answer:** TraceX unites the four fundamental pillars of digital forensics and incident response (evidence acquisition, cryptographic integrity, append-only custody, and timeline reconstruction) into a safe, locally runnable educational application. Unlike static mockups or complex enterprise tools, it provides an auditable, transparent pipeline.

### 2. Why Digital Forensics?
**Answer:** Digital forensics enforces the scientific methodology of evidence preservation, non-repudiation, and chronological reconstruction. It bridges core computer science theory (hashing, relational databases, data structures) directly with real-world cybersecurity practice.

### 3. Why SHA-256?
**Answer:** SHA-256 is an NIST-standardized cryptographic hash function producing a 256-bit (32-byte / 64 hex character) digest. It is collision-resistant and exhibits a strong avalanche effect: modifying even a single bit in an evidence file produces an entirely distinct digest, guaranteeing mathematical proof of byte-level alteration.

### 4. What is Chain of Custody?
**Answer:** Chain of custody is a chronological, tamper-evident audit record documenting the acquisition, transfer, analysis, and verification of digital evidence. In TraceX, this is enforced as an immutable append-only ledger—historical entries cannot be updated or deleted.

### 5. Why a Relational Database?
**Answer:** Investigation entities possess explicit one-to-many relationships (Cases contain multiple Evidence items, Custody Records, Security Events, and Findings). Relational schemas enforce foreign-key referential integrity, check constraints, and 3NF normalization, preventing orphaned records and state anomalies.

### 6. Why this Layered 3-Tier Architecture?
**Answer:** It separates presentation (Flask routes & Jinja2 templates), domain business logic (Services), and persistence (Repositories). This separation of concerns enables independent unit testing of services without spinning up a browser, avoids coupling routes to raw SQL, and simplifies maintenance.

### 7. Why Rule-Based Logic Instead of Machine Learning for Log Analysis?
**Answer:** Digital forensics prioritizes explainability, repeatability, and legal defensibility. Heuristic rule engines (such as R1 to R4) are 100% deterministic and can be defended on a whiteboard in two minutes, whereas black-box ML models introduce probabilistic hallucinations and opacity.

### 8. How does Timeline Reconstruction Work?
**Answer:** The system retrieves all `SecurityEvent` and `Finding` rows for a case, normalizes their timestamps into standardized UTC strings, and sorts them chronologically using Timsort in $O(n \log n)$ time. The sorted list is then grouped by date for investigative inspection.

### 9. How does the Correlation Engine Work?
**Answer:** It searches across independent entities for shared attributes (such as identical usernames, external IP addresses, or source origins) within a bounded time window (e.g., 30 minutes). Crucially, correlation outputs are phrased as "potentially related" and never make premature claims of causal attribution.

### 10. What Happens When Evidence is Modified?
**Answer:** When an investigator clicks "Re-Verify", the system recomputes the SHA-256 hash of the stored file. If the digest mismatches the baseline `sha256_original`, the status transitions from `VERIFIED` to `MODIFIED`, an append-only custody record is logged, and the rule engine automatically generates a `CRITICAL` severity indicator (Rule R4).

### 11. How is Authentication and RBAC Secured?
**Answer:** Passwords are never stored in plaintext; they are hashed using Werkzeug's PBKDF2/SHA-256 algorithm. Sessions use HTTP-only cookies with Lax SameSite controls. Role-Based Access Control is enforced server-side using the `@role_required` decorator, returning HTTP 403 Forbidden for unauthorized access.

### 12. What are the Inherent Limitations of TraceX?
**Answer:** TraceX is an educational simulation tool, not a certified courtroom forensic suite. It operates without hardware write-blockers, processes synthetic sanitized logs, and does not conduct live kernel-level memory acquisitions.

### 13. What Makes TraceX Innovative?
**Answer:** TraceX enforces strict evidentiary strength classification at the data layer: distinguishing Observed Evidence from Detected Indicators and System Findings (never labeling inferences as confirmed facts). It couples this with an interactive tamper demonstration utility and one-click report assembly.

### 14. What Core Computer Science Concepts are Applied?
**Answer:** 
- **Algorithms:** $O(n \log n)$ chronological sorting, sliding window cluster detection.
- **DBMS:** 3NF relational normalization, primary/foreign key cascading, index optimization.
- **OOP:** Design patterns (Repository Pattern, Dependency Injection, Service Layer abstraction).
- **Software Engineering:** Unit/integration testing with Pytest, automated regression suites.

### 15. What Cybersecurity Concepts are Applied?
**Answer:** Cryptographic hashing, non-repudiation, tamper detection, session fixation prevention, CSRF protection via tokens, input sanitization, file extension allow-listing, path traversal mitigation, and least privilege authorization.

### 16. Why Append-Only Custody Records Instead of Editable Rows?
**Answer:** Forensic soundness requires complete immutability. If an investigator or administrator could edit or delete past custody records, the audit trail's credibility would be destroyed. TraceX enforces this by omitting update and delete operations in `CustodyRepository`.

### 17. What Does a Hash Prove and What Does it NOT Prove?
**Answer:** A cryptographic hash proves with mathematical certainty whether file contents have remained unaltered since the baseline hash was calculated. It **does not prove** who made a modification, when an external change occurred, or whether the original content was benign or malicious.

### 18. Why SQLite Over Client-Server RDBMS (like MySQL or PostgreSQL)?
**Answer:** SQLite is embedded, serverless, zero-configuration, and fully self-contained. It simplifies academic deployment and evaluation without external daemon dependencies, while still offering complete ACID transactions, indexes, and SQL constraints.

### 19. How Would You Scale TraceX to Multi-Tenant Enterprise Teams?
**Answer:** Migrate SQLite to PostgreSQL, implement row-level security (RLS) policies per case, introduce Redis for background log parsing worker queues (Celery), and apply cryptographic digital signatures (ECDSA) to each custody record.

### 20. How is SQL Injection Prevented?
**Answer:** All database operations utilize parameterized query placeholders (`?`) executed through the Python SQLite driver. No SQL statement strings are ever constructed via string concatenation or user-controlled format strings.

### 21. How is Path Traversal Prevented on Evidence Upload?
**Answer:** Incoming filenames are sanitized using `werkzeug.utils.secure_filename` (stripping directory traversal markers like `../`), stored in an isolated directory (`evidence-store/case_<id>/`), and kept completely outside web-servable directories like `static/`.

### 22. What is the Severity Scoring Model Based On?
**Answer:** TraceX uses a deterministic, explainable four-tier severity model: `INFO` (informational event), `LOW` (single low-impact correlation), `MEDIUM` (single rule violation like R1 brute force), `HIGH` (chained indicators like R2 account lock or R3 privilege change), and `CRITICAL` (forensic integrity violation like R4 evidence tampering).

### 23. Why Distinguish "Finding" from "Fact"?
**Answer:** In forensic science, digital events and indicators are observed artifacts and algorithmic correlations; they are hypotheses until corroborated by physical, contextual, or corroborating proof. Labeling an automated rule trigger as a "Confirmed Fact" would violate forensic integrity.

### 24. What Future Enhancements Could be Added?
**Answer:** Adding interactive relationship graph visualizations (using D3.js/Cytoscape), supporting STIX/TAXII threat intelligence feeds, adding PDF rendering with ReportLab, and implementing multi-case comparative timeline stitching.

### 25. Why not NoSQL (e.g. MongoDB)?
**Answer:** Investigation data is inherently relational: cases connect to evidence, evidence connects to custody history, and security events connect to rules and cases. Relational databases enforce declarative referential integrity, preventing broken links that would undermine an investigation.
