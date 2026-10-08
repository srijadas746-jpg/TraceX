import io
import os
import pytest
from services.case_service import CaseService
from services.evidence_service import EvidenceService
from services.custody_service import CustodyService
from services.log_analysis_service import LogAnalysisService
from services.timeline_service import TimelineService
from services.correlation_service import CorrelationService
from services.report_service import ReportService
from repositories.finding_repository import FindingRepository

def test_full_10_minute_investigation_scenario(test_env):
    """
    End-to-end programmatic verification of the 10-Minute Scripted Demo Workflow
    """
    app = test_env["app"]
    with app.app_context():
        # Step 1 & 2: Create Case
        case_service = CaseService()
        success, msg, case = case_service.create_case(
            title="Operation Aurora Breach",
            incident_type="Brute Force Authentication",
            description="Simulated infiltration and credential stuffing incident.",
            investigator_id=2
        )
        assert success is True
        assert case.id is not None

        # Step 3 & 4: Add Evidence & Compute SHA-256
        evidence_service = EvidenceService(store_dir=test_env["store_path"])
        sample_file = io.BytesIO(b"Synthetic Disk Sector Capture Data - Authenticated\n")
        sample_file.filename = "auth_dump.raw"

        e_success, e_msg, evidence = evidence_service.add_evidence(
            case_id=case.id,
            file_obj=sample_file,
            name="auth_dump.raw",
            evidence_type="DISK_IMAGE",
            source="DC-PROD-01",
            description="Primary authentication sector snapshot.",
            actor_id=2
        )
        assert e_success is True
        assert evidence.sha256_original is not None

        # Step 5 & 6: Verify evidence baseline integrity & check custody
        v_ok, _, verified_ev, custody_rec = evidence_service.verify_evidence(evidence.id, actor_id=2)
        assert v_ok is True
        assert verified_ev.integrity_status == "VERIFIED"
        assert custody_rec.action == "VERIFIED"

        # Step 7: Import brute-force synthetic logs
        log_service = LogAnalysisService()
        sample_csv_path = os.path.join(os.path.dirname(__file__), "..", "sample-data", "logs_bruteforce.csv")
        with open(sample_csv_path, "r", encoding="utf-8") as f:
            stream = io.StringIO(f.read())
            import_res = log_service.import_logs_from_stream(case.id, stream, file_format="csv")
        assert import_res["imported_events"] >= 6

        # Step 8 & 9: Run Rule Engine
        rule_findings = log_service.run_rules(case.id)
        assert len(rule_findings) >= 2
        severities = [rf["severity"] for rf in rule_findings]
        assert "MEDIUM" in severities
        assert "HIGH" in severities

        # Step 10: Generate timeline
        timeline_service = TimelineService()
        timeline = timeline_service.build_timeline(case.id)
        assert timeline["total_items"] >= 8

        # Step 11: Run correlation engine
        corr_service = CorrelationService()
        corr_res = corr_service.run_correlation(case.id)

        # Step 12, 13, 14, 15: Tamper evidence on disk and re-verify
        t_ok, _ = evidence_service.tamper_evidence_demo(evidence.id, actor_id=2)
        assert t_ok is True

        re_ok, _, tampered_ev, re_custody = evidence_service.verify_evidence(evidence.id, actor_id=2)
        assert re_ok is True
        assert tampered_ev.integrity_status == "MODIFIED"

        # Verify new CRITICAL finding created
        finding_repo = FindingRepository()
        findings = finding_repo.list_by_case(case.id)
        critical_findings = [f for f in findings if f.severity == "CRITICAL"]
        assert len(critical_findings) >= 1
        assert critical_findings[0].rule_or_key == "R4"

        # Step 16: Generate Investigation Report
        report_service = ReportService(reports_dir=os.path.join(test_env["temp_dir"], "reports"))
        report_data = report_service.generate_case_report(case.id)
        md_content = report_service.generate_markdown_report(case.id)

        assert report_data["case"]["title"] == "Operation Aurora Breach"
        assert report_data["evidence_summary"]["total_items"] == 1
        assert report_data["evidence_summary"]["items"][0]["integrity_status"] == "MODIFIED"
        assert len(report_data["findings"]["indicators"]) >= 2
        assert "LEGAL & EVIDENTIARY DISCLAIMER" in md_content
