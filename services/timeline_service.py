from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from repositories.event_repository import EventRepository
from repositories.finding_repository import FindingRepository

class TimelineService:
    """
    Deterministic chronological timeline reconstruction.
    Merges SecurityEvents and Findings, sorting in O(n log n) time.
    """
    def __init__(self,
                 event_repo: Optional[EventRepository] = None,
                 finding_repo: Optional[FindingRepository] = None):
        self.event_repo = event_repo or EventRepository()
        self.finding_repo = finding_repo or FindingRepository()

    def build_timeline(self, case_id: int) -> Dict[str, Any]:
        events = self.event_repo.list_by_case(case_id)
        findings = self.finding_repo.list_by_case(case_id)

        timeline_items = []

        # Convert SecurityEvents to timeline entries
        for ev in events:
            timeline_items.append({
                "item_type": "SECURITY_EVENT",
                "label": "Observed Security Event",
                "id": ev.id,
                "timestamp": ev.event_timestamp,
                "title": ev.event_type,
                "user": ev.event_user or "N/A",
                "source": ev.source,
                "ip_ref": ev.ip_ref or "N/A",
                "severity": "INFO",
                "details": ev.raw_line or f"Event {ev.event_type} from {ev.source}",
                "is_system_finding": False
            })

        # Convert Findings to timeline entries
        for fd in findings:
            created_ts = fd.created_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            timeline_items.append({
                "item_type": "FINDING",
                "label": f"System-Generated Finding ({fd.kind})",
                "id": fd.id,
                "timestamp": created_ts,
                "title": f"Rule/Key: {fd.rule_or_key}",
                "user": "System Engine",
                "source": "TraceX Analysis Engine",
                "ip_ref": "N/A",
                "severity": fd.severity,
                "details": fd.description,
                "is_system_finding": True,
                "related_event_ids": fd.event_ids_list,
                "related_evidence_ids": fd.evidence_ids_list
            })

        # Chronological sorting: O(n log n)
        timeline_items.sort(key=lambda x: str(x["timestamp"]))

        # Group by day for structured UI presentation
        grouped_by_day: Dict[str, List[Dict[str, Any]]] = {}
        for item in timeline_items:
            # Extract YYYY-MM-DD
            day_str = str(item["timestamp"])[:10] if item["timestamp"] else "Unknown Date"
            if day_str not in grouped_by_day:
                grouped_by_day[day_str] = []
            grouped_by_day[day_str].append(item)

        return {
            "total_items": len(timeline_items),
            "items": timeline_items,
            "timeline_items": timeline_items,
            "grouped_by_day": grouped_by_day
        }
