import io
import pytest
from services.case_service import CaseService
from services.evidence_service import EvidenceService
from services.custody_service import CustodyService

def test_t03_custody_append_only_behavior(test_env):
    """
    T03: Custody verification action -> Expected: New append-only row, old rows unchanged
    """
    app = test_env["app"]
    with app.app_context():
        case_service = CaseService()
        _, _, case = case_service.create_case("Case T03", "Data Exfiltration", "Custody Test", investigator_id=2)

        evidence_service = EvidenceService(store_dir=test_env["store_path"])
        custody_service = CustodyService()

        dummy_file = io.BytesIO(b"Synthetic data for custody test\n")
        dummy_file.filename = "t03_custody.dump"

        _, _, evidence = evidence_service.add_evidence(
            case_id=case.id,
            file_obj=dummy_file,
            name="t03_custody.dump",
            evidence_type="DISK_IMAGE",
            source="HardDrive-0",
            description="Custody chain validation",
            actor_id=2
        )

        history_1 = custody_service.get_evidence_custody_history(evidence.id)
        assert len(history_1) == 1
        initial_record = history_1[0]
        assert initial_record.action == "COLLECTED"
        assert initial_record.new_status == "NOT_VERIFIED"
        first_id = initial_record.id
        first_timestamp = initial_record.timestamp

        # Perform verification action
        evidence_service.verify_evidence(evidence.id, actor_id=2)

        history_2 = custody_service.get_evidence_custody_history(evidence.id)
        assert len(history_2) == 2

        # Verify old record unchanged
        assert history_2[0].id == first_id
        assert history_2[0].action == "COLLECTED"
        assert history_2[0].timestamp == first_timestamp

        # Verify new record appended
        assert history_2[1].id > first_id
        assert history_2[1].action == "VERIFIED"
        assert history_2[1].new_status == "VERIFIED"
