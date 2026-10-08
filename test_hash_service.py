import io
import os
import pytest
from services.evidence_service import EvidenceService
from services.case_service import CaseService
from repositories.finding_repository import FindingRepository
from database.db import get_db

def test_t01_valid_hash_verification(test_env):
    """
    T01: Valid evidence hash verification -> Expected: VERIFIED
    """
    app = test_env["app"]
    with app.app_context():
        conn = get_db(test_env["db_path"])
        case_service = CaseService()
        _, _, case = case_service.create_case("Case T01", "Unauthorized Access", "Testing T01", investigator_id=2)

        evidence_service = EvidenceService(store_dir=test_env["store_path"])
        dummy_file = io.BytesIO(b"Synthetic Log File Content For T01\n")
        dummy_file.filename = "t01_log.log"

        success, msg, evidence = evidence_service.add_evidence(
            case_id=case.id,
            file_obj=dummy_file,
            name="t01_log.log",
            evidence_type="LOG",
            source="Test System",
            description="Testing baseline",
            actor_id=2
        )
        assert success is True
        assert evidence.integrity_status == "NOT_VERIFIED"
        assert evidence.sha256_original is not None

        # Verify integrity
        v_success, v_msg, verified_ev, custody = evidence_service.verify_evidence(evidence.id, actor_id=2)
        assert v_success is True
        assert verified_ev.integrity_status == "VERIFIED"
        assert verified_ev.sha256_current == evidence.sha256_original

def test_t02_tampered_evidence_detection(test_env):
    """
    T02: Tampered evidence -> Expected: MODIFIED + CRITICAL finding
    """
    app = test_env["app"]
    with app.app_context():
        case_service = CaseService()
        _, _, case = case_service.create_case("Case T02", "Evidence Tampering", "Testing T02", investigator_id=2)

        evidence_service = EvidenceService(store_dir=test_env["store_path"])
        finding_repo = FindingRepository()

        dummy_file = io.BytesIO(b"Baseline byte contents before tampering\n")
        dummy_file.filename = "t02_artifact.bin"

        _, _, evidence = evidence_service.add_evidence(
            case_id=case.id,
            file_obj=dummy_file,
            name="t02_artifact.bin",
            evidence_type="MEMORY_DUMP",
            source="RAM",
            description="Testing tamper detection",
            actor_id=2
        )

        # Tamper the file on disk
        tamper_success, _ = evidence_service.tamper_evidence_demo(evidence.id, actor_id=2)
        assert tamper_success is True

        # Re-verify
        _, _, rechecked_ev, custody = evidence_service.verify_evidence(evidence.id, actor_id=2)
        assert rechecked_ev.integrity_status == "MODIFIED"
        assert rechecked_ev.sha256_current != evidence.sha256_original
        assert custody.action == "VERIFIED"
        assert custody.new_status == "MODIFIED"

        # Check CRITICAL finding created
        findings = finding_repo.list_by_case(case.id)
        critical_findings = [f for f in findings if f.severity == "CRITICAL" and f.rule_or_key == "R4"]
        assert len(critical_findings) == 1
        assert "Integrity warning" in critical_findings[0].description
