import io
import pytest
from services.case_service import CaseService
from services.evidence_service import EvidenceService
from repositories.event_repository import EventRepository
from repositories.finding_repository import FindingRepository
from services.correlation_service import CorrelationService

def test_correlation_engine(test_env):
    app = test_env["app"]
    with app.app_context():
        case_service = CaseService()
        _, _, case = case_service.create_case("Case Correlation", "Multi-Entity", "Correlation Test", investigator_id=2)

        event_repo = EventRepository()
        finding_repo = FindingRepository()
        evidence_service = EvidenceService(store_dir=test_env["store_path"])

        # Insert events with shared IP across multiple users
        event_repo.create(case.id, "LOGIN_FAILED", "user_alpha", "ssh", "198.51.100.99", "2026-09-17 11:00:00")
        event_repo.create(case.id, "LOGIN_FAILED", "user_beta", "ssh", "198.51.100.99", "2026-09-17 11:05:00")

        # Insert evidence with matching source
        dummy_file = io.BytesIO(b"Synthetic server dump\n")
        dummy_file.filename = "ssh_capture.raw"
        evidence_service.add_evidence(
            case_id=case.id,
            file_obj=dummy_file,
            name="ssh_capture.raw",
            evidence_type="LOG",
            source="ssh",
            description="Testing correlation link",
            actor_id=2
        )

        corr_service = CorrelationService(event_repo=event_repo, finding_repo=finding_repo)
        results = corr_service.run_correlation(case.id, window_minutes=30)

        assert len(results) >= 1
        # Check IP correlation finding
        ip_findings = [r for r in results if r["rule_or_key"] == "SHARED_IP_MULTI_USER"]
        assert len(ip_findings) == 1
        assert "198.51.100.99" in ip_findings[0]["description"]
        assert "not confirmed causation" in ip_findings[0]["description"]
