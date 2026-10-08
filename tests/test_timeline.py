import pytest
from services.case_service import CaseService
from repositories.event_repository import EventRepository
from repositories.finding_repository import FindingRepository
from services.timeline_service import TimelineService

def test_t07_timeline_chronological_ordering(test_env):
    """
    T07: Mixed events & findings -> Strictly chronological output
    """
    app = test_env["app"]
    with app.app_context():
        case_service = CaseService()
        _, _, case = case_service.create_case("Case T07", "Timeline Test", "Ordering verification", investigator_id=2)

        event_repo = EventRepository()
        finding_repo = FindingRepository()

        # Insert out of chronological order
        event_repo.create(case.id, "LOGIN_SUCCESS", "alice", "auth", "10.0.0.1", "2026-09-17 12:00:00")
        event_repo.create(case.id, "FILE_MODIFIED", "bob", "fs", "10.0.0.2", "2026-09-17 08:30:00")
        event_repo.create(case.id, "PERMISSION_CHANGED", "carol", "iam", "10.0.0.3", "2026-09-17 15:45:00")

        # Insert findings
        finding_repo.create(case.id, "INDICATOR", "R1", "MEDIUM", [1], [], "Suspicious login pattern", "2026-09-17 10:15:00")

        timeline_service = TimelineService(event_repo, finding_repo)
        timeline = timeline_service.build_timeline(case.id)

        items = timeline["items"]
        assert len(items) == 4

        # Verify strict chronological monotonicity
        for i in range(len(items) - 1):
            assert str(items[i]["timestamp"]) <= str(items[i+1]["timestamp"])

        assert str(items[0]["timestamp"]) == "2026-09-17 08:30:00"
        assert str(items[-1]["timestamp"]) == "2026-09-17 15:45:00"
