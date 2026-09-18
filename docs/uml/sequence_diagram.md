# TraceX — UML Sequence Diagrams

## 1. Digital Evidence Acquisition & SHA-256 Hashing Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Investigator
    participant Routes as evidence_routes
    participant EvidenceSvc as EvidenceService
    participant HashSvc as HashService
    participant EvidenceRepo as EvidenceRepository
    participant CustodySvc as CustodyService
    participant CustodyRepo as CustodyRepository
    participant DB as SQLite DB

    Investigator->>Routes: POST /cases/{id}/evidence/new (file, metadata)
    Routes->>EvidenceSvc: add_evidence(case_id, file, name, type, source, actor_id)
    EvidenceSvc->>EvidenceSvc: validate_file_type & secure_filename()
    EvidenceSvc->>EvidenceSvc: save file to evidence-store/case_{id}/
    EvidenceSvc->>HashSvc: compute_file_hash(target_path)
    HashSvc-->>EvidenceSvc: sha256_hash_digest
    EvidenceSvc->>EvidenceRepo: create(case_id, name, sha256_original, ...)
    EvidenceRepo->>DB: INSERT INTO Evidence (...)
    DB-->>EvidenceRepo: evidence_id
    EvidenceRepo-->>EvidenceSvc: Evidence Model
    EvidenceSvc->>CustodySvc: log_action(evidence_id, action="COLLECTED", actor_id, new_status="NOT_VERIFIED")
    CustodySvc->>CustodyRepo: create(evidence_id, "COLLECTED", ...)
    CustodyRepo->>DB: INSERT INTO CustodyRecord (...)
    DB-->>CustodyRepo: custody_record_id
    CustodyRepo-->>CustodySvc: CustodyRecord Model
    EvidenceSvc-->>Routes: (True, "Registered", Evidence)
    Routes-->>Investigator: 302 Redirect to /evidence/{id} (Success Banner)
```

---

## 2. Integrity Verification & Tamper Detection Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Investigator
    participant Routes as evidence_routes
    participant EvidenceSvc as EvidenceService
    participant HashSvc as HashService
    participant EvidenceRepo as EvidenceRepository
    participant CustodySvc as CustodyService
    participant FindingRepo as FindingRepository
    participant DB as SQLite DB

    Investigator->>Routes: POST /evidence/{id}/verify
    Routes->>EvidenceSvc: verify_evidence(evidence_id, actor_id)
    EvidenceSvc->>EvidenceRepo: get_by_id(evidence_id)
    EvidenceRepo-->>EvidenceSvc: Evidence (baseline sha256_original)
    EvidenceSvc->>HashSvc: compute_file_hash(stored_path)
    HashSvc-->>EvidenceSvc: current_sha256
    
    alt current_sha256 == sha256_original
        EvidenceSvc->>EvidenceSvc: new_status = "VERIFIED"
    else current_sha256 != sha256_original
        EvidenceSvc->>EvidenceSvc: new_status = "MODIFIED"
        EvidenceSvc->>FindingRepo: create(case_id, kind="INDICATOR", rule="R4", severity="CRITICAL", ...)
        FindingRepo->>DB: INSERT INTO Finding (...)
    end

    EvidenceSvc->>EvidenceRepo: update_hash_and_status(evidence_id, current_sha256, new_status)
    EvidenceRepo->>DB: UPDATE Evidence SET ...
    EvidenceSvc->>CustodySvc: log_action(evidence_id, "VERIFIED", actor_id, prev_status, new_status, remarks)
    CustodySvc->>DB: INSERT INTO CustodyRecord (Append-Only)
    EvidenceSvc-->>Routes: (True, status_msg, updated_evidence, custody)
    Routes-->>Investigator: 302 Redirect to /evidence/{id} (Integrity Status Displayed)
```

---

## 3. Log Ingestion, Rule Engine & Timeline Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Investigator
    participant Routes as log_routes / timeline_routes
    participant LogSvc as LogAnalysisService
    participant EventRepo as EventRepository
    participant FindingRepo as FindingRepository
    participant TimelineSvc as TimelineService
    participant DB as SQLite DB

    Investigator->>Routes: POST /cases/{id}/logs/import (CSV / JSONL)
    Routes->>LogSvc: import_logs_from_stream(case_id, stream, format)
    LogSvc->>LogSvc: Parse & normalize UTC timestamps, isolate malformed rows
    LogSvc->>EventRepo: bulk_insert(valid_events)
    EventRepo->>DB: INSERT INTO SecurityEvent (...)
    LogSvc-->>Routes: Import Summary {imported, errors}
    Routes-->>Investigator: Flash Summary

    Investigator->>Routes: POST /cases/{id}/logs/analyze
    Routes->>LogSvc: run_rules(case_id)
    LogSvc->>EventRepo: list_by_case(case_id)
    EventRepo-->>LogSvc: [SecurityEvents]
    LogSvc->>LogSvc: Evaluate R1 (>=5 failures), R2 (lockout), R3 (access->perm)
    LogSvc->>FindingRepo: bulk_insert(findings)
    FindingRepo->>DB: INSERT INTO Finding (...)
    LogSvc-->>Routes: [Findings]
    Routes-->>Investigator: 302 Redirect to Case Detail (Findings Tab)

    Investigator->>Routes: GET /cases/{id}/timeline
    Routes->>TimelineSvc: build_timeline(case_id)
    TimelineSvc->>EventRepo: list_by_case(case_id)
    TimelineSvc->>FindingRepo: list_by_case(case_id)
    TimelineSvc->>TimelineSvc: Merge & sort in O(n log n) chronological order
    TimelineSvc-->>Routes: Timeline Model (Grouped by Day)
    Routes-->>Investigator: Render timeline/view.html
```
