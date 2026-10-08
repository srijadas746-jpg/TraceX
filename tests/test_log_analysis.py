import io
import pytest
from services.case_service import CaseService
from services.log_analysis_service import LogAnalysisService
from repositories.event_repository import EventRepository
from repositories.finding_repository import FindingRepository

def test_t04_malformed_log_row_handling(test_env):
    """
    T04: Malformed log row -> Row skipped safely, valid rows imported
    """
    app = test_env["app"]
    with app.app_context():
        case_service = CaseService()
        _, _, case = case_service.create_case("Case T04", "Log Audit", "Testing malformed rows", investigator_id=2)

        csv_content = """timestamp,event_type,user,source,ip_ref
2026-09-17 10:00:00,LOGIN_SUCCESS,user1,auth,10.0.0.1
corrupted_malformed_row_without_required_fields
2026-09-17 10:05:00,LOGIN_FAILED,user2,auth,10.0.0.2
2026-09-17 99:99:99,LOGIN_FAILED,user3,auth,10.0.0.3
2026-09-17 10:10:00,FILE_CREATED,user1,fs,10.0.0.1
"""
        log_service = LogAnalysisService()
        stream = io.StringIO(csv_content)
        result = log_service.import_logs_from_stream(case.id, stream, file_format="csv")

        # 3 valid rows imported, 2 invalid rows skipped safely without crashing
        assert result["imported_events"] == 3
        assert result["error_count"] == 2
        
        event_repo = EventRepository()
        assert event_repo.count_by_case(case.id) == 3

def test_t05_repeated_failed_logins_rule_engine(test_env):
    """
    T05: 5 failed logins in window -> MEDIUM indicator created
    """
    app = test_env["app"]
    with app.app_context():
        case_service = CaseService()
        _, _, case = case_service.create_case("Case T05", "Brute Force Authentication", "Rule engine test", investigator_id=2)

        log_data = """timestamp,event_type,user,source,ip_ref
2026-09-17 10:00:00,LOGIN_FAILED,attacker_target,ssh,1.2.3.4
2026-09-17 10:01:00,LOGIN_FAILED,attacker_target,ssh,1.2.3.4
2026-09-17 10:02:00,LOGIN_FAILED,attacker_target,ssh,1.2.3.4
2026-09-17 10:03:00,LOGIN_FAILED,attacker_target,ssh,1.2.3.4
2026-09-17 10:04:00,LOGIN_FAILED,attacker_target,ssh,1.2.3.4
2026-09-17 10:06:00,ACCOUNT_LOCKED,attacker_target,auth-system,1.2.3.4
"""
        log_service = LogAnalysisService()
        stream = io.StringIO(log_data)
        log_service.import_logs_from_stream(case.id, stream, file_format="csv")

        findings = log_service.run_rules(case.id)
        assert len(findings) >= 2

        # Verify R1 (MEDIUM)
        r1_matches = [f for f in findings if f["rule_or_key"] == "R1" and f["severity"] == "MEDIUM"]
        assert len(r1_matches) == 1
        assert "Potentially suspicious authentication activity" in r1_matches[0]["description"]

        # Verify R2 (HIGH)
        r2_matches = [f for f in findings if f["rule_or_key"] == "R2" and f["severity"] == "HIGH"]
        assert len(r2_matches) == 1
        assert "account lock after repeated failures" in r2_matches[0]["description"]
