import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from config import Config
from repositories.case_repository import CaseRepository
from repositories.evidence_repository import EvidenceRepository
from repositories.custody_repository import CustodyRepository
from repositories.event_repository import EventRepository
from repositories.finding_repository import FindingRepository
from services.timeline_service import TimelineService

class ReportService:
    """
    Assembles comprehensive, structured digital forensic investigation reports.
    Preserves evidentiary classification:
      1. Observed Evidence
      2. Detected Indicators
      3. System-Generated Findings (Correlations & Warnings)
    Explicitly caveats inferences against confirmed facts.
    """
    def __init__(self,
                 case_repo: Optional[CaseRepository] = None,
                 evidence_repo: Optional[EvidenceRepository] = None,
                 custody_repo: Optional[CustodyRepository] = None,
                 event_repo: Optional[EventRepository] = None,
                 finding_repo: Optional[FindingRepository] = None,
                 timeline_service: Optional[TimelineService] = None,
                 reports_dir: Optional[str] = None):
        self.case_repo = case_repo or CaseRepository()
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.custody_repo = custody_repo or CustodyRepository()
        self.event_repo = event_repo or EventRepository()
        self.finding_repo = finding_repo or FindingRepository()
        self.timeline_service = timeline_service or TimelineService(self.event_repo, self.finding_repo)
        self.reports_dir = reports_dir or Config.REPORTS_PATH

    def generate_case_report(self, case_id: int) -> Optional[Dict[str, Any]]:
        case = self.case_repo.get_by_id(case_id)
        if not case:
            return None

        evidence_list = self.evidence_repo.list_by_case(case_id)
        custody_list = self.custody_repo.list_by_case(case_id)
        events_list = self.event_repo.list_by_case(case_id)
        findings_list = self.finding_repo.list_by_case(case_id)
        timeline_data = self.timeline_service.build_timeline(case_id)

        # Categorize findings
        indicators = [f.to_dict() for f in findings_list if f.kind == "INDICATOR"]
        correlations = [f.to_dict() for f in findings_list if f.kind == "CORRELATION"]

        report_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        report_data = {
            "metadata": {
                "system": "TraceX Digital Forensics & Incident Response",
                "version": "1.0.0",
                "report_generated_at": report_timestamp,
                "disclaimer": (
                    "LEGAL & EVIDENTIARY DISCLAIMER: This investigation report was produced using "
                    "TraceX educational DFIR software. Items classified as 'Detected Indicators' or "
                    "'System-Generated Findings' represent rule-based algorithmic inferences and must "
                    "never be construed as legally confirmed facts without corroborating physical forensic proof."
                )
            },
            "case": case.to_dict(),
            "evidence_summary": {
                "total_items": len(evidence_list),
                "items": [e.to_dict() for e in evidence_list]
            },
            "chain_of_custody": {
                "total_records": len(custody_list),
                "records": [c.to_dict() for c in custody_list]
            },
            "security_events_summary": {
                "total_events": len(events_list),
                "distribution": self.event_repo.get_event_type_distribution(case_id)
            },
            "findings": {
                "total_findings": len(findings_list),
                "indicators": indicators,
                "correlations": correlations,
                "severity_counts": self.finding_repo.get_severity_distribution(case_id)
            },
            "timeline": timeline_data
        }

        # Write copy to disk in reports folder
        os.makedirs(self.reports_dir, exist_ok=True)
        report_file = Path(self.reports_dir) / f"investigation_report_case_{case_id}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        return report_data

    def generate_markdown_report(self, case_id: int) -> Optional[str]:
        report = self.generate_case_report(case_id)
        if not report:
            return None

        case = report["case"]
        meta = report["metadata"]

        md = []
        md.append(f"# TraceX Investigation Report: Case #{case['id']} — {case['title']}")
        md.append(f"**Generated:** {meta['report_generated_at']}  ")
        md.append(f"**Classification:** Educational DFIR Artifact  ")
        md.append(f"**Status:** {case['status']} | **Incident Type:** {case['incident_type']} | **Investigator ID:** {case['investigator_id']}  \n")

        md.append("## 1. Evidentiary Disclaimer")
        md.append(f"> {meta['disclaimer']}\n")

        md.append("## 2. Executive Incident Overview")
        md.append(f"- **Title:** {case['title']}")
        md.append(f"- **Incident Classification:** {case['incident_type']}")
        md.append(f"- **Date Opened:** {case['created_at']}")
        md.append(f"- **Date Closed:** {case.get('closed_at') or 'Active / Open'}")
        md.append(f"- **Description:** {case.get('description') or 'No narrative provided.'}\n")

        md.append("## 3. Registered Digital Evidence (Observed Evidence)")
        md.append("| ID | Name | Type | Source | SHA-256 Original | Integrity Status |")
        md.append("|---|---|---|---|---|---|")
        for e in report["evidence_summary"]["items"]:
            md.append(f"| #{e['id']} | `{e['name']}` | {e['type']} | {e['source']} | `{e['sha256_original'][:16]}...` | **{e['integrity_status']}** |")
        md.append("")

        md.append("## 4. Chain of Custody Audit Trail (Append-Only)")
        md.append("| Timestamp | Evidence ID | Action | Actor ID | Prev Status | New Status | Remarks |")
        md.append("|---|---|---|---|---|---|---|")
        for c in report["chain_of_custody"]["records"]:
            md.append(f"| {c['timestamp']} | #{c['evidence_id']} | `{c['action']}` | User #{c['actor_id']} | {c['prev_status'] or '-'} | {c['new_status'] or '-'} | {c['remarks'] or '-'} |")
        md.append("")

        md.append("## 5. System-Generated Findings & Indicators")
        md.append("### A. Detected Indicators (Rule-Engine Inferences)")
        if report["findings"]["indicators"]:
            for ind in report["findings"]["indicators"]:
                md.append(f"- **[{ind['severity']}] Rule {ind['rule_or_key']}**: {ind['description']}")
        else:
            md.append("*No rule-triggered indicators detected.*")
        md.append("")

        md.append("### B. Correlated Multi-Entity Activity")
        if report["findings"]["correlations"]:
            for corr in report["findings"]["correlations"]:
                md.append(f"- **[{corr['severity']}] Key {corr['rule_or_key']}**: {corr['description']}")
        else:
            md.append("*No cross-entity correlations detected.*")
        md.append("")

        md.append("## 6. Incident Chronological Timeline")
        md.append("| Timestamp | Type | Entity / User | Details | Evidentiary Tag |")
        md.append("|---|---|---|---|---|")
        for item in report["timeline"]["items"]:
            md.append(f"| {item['timestamp']} | {item['title']} | {item['user']} | {item['details'][:80]}... | `{item['label']}` |")
        md.append("")

        md.append("---")
        md.append("*End of TraceX Investigation Report*")

        md_content = "\n".join(md)
        md_file = Path(self.reports_dir) / f"investigation_report_case_{case_id}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        return md_content
