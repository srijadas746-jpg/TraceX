from datetime import datetime
from typing import Optional, List, Dict, Any
from repositories.event_repository import EventRepository
from repositories.evidence_repository import EvidenceRepository
from repositories.finding_repository import FindingRepository
from models.security_event import SecurityEvent
from models.evidence import Evidence

class CorrelationService:
    """
    Explainable multi-entity correlation engine.
    Finds non-causal relationships based on shared attributes (user, IP, source, time window).
    Never claims causation — outputs 'potentially related'.
    """
    def __init__(self,
                 event_repo: Optional[EventRepository] = None,
                 evidence_repo: Optional[EvidenceRepository] = None,
                 finding_repo: Optional[FindingRepository] = None):
        self.event_repo = event_repo or EventRepository()
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.finding_repo = finding_repo or FindingRepository()

    def _to_dt(self, ts_str: str) -> datetime:
        return datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")

    def run_correlation(self, case_id: int, window_minutes: int = 30) -> List[Dict[str, Any]]:
        # Clear prior correlation findings for this case
        self.finding_repo.clear_by_case_and_kind(case_id, kind="CORRELATION")

        events = self.event_repo.list_by_case(case_id)
        evidence_list = self.evidence_repo.list_by_case(case_id)
        correlation_findings = []

        window_seconds = window_minutes * 60

        # 1. Correlate Events by User within time window
        user_map: Dict[str, List[SecurityEvent]] = {}
        for ev in events:
            if ev.event_user:
                user_map.setdefault(ev.event_user, []).append(ev)

        for user, u_events in user_map.items():
            if len(u_events) < 2:
                continue
            # Sort events by timestamp
            u_events.sort(key=lambda e: e.event_timestamp)
            for i in range(len(u_events)):
                for j in range(i + 1, len(u_events)):
                    e1 = u_events[i]
                    e2 = u_events[j]
                    try:
                        delta = (self._to_dt(e2.event_timestamp) - self._to_dt(e1.event_timestamp)).total_seconds()
                    except Exception:
                        continue
                    if delta <= window_seconds:
                        if e1.event_type != e2.event_type:
                            correlation_findings.append({
                                "case_id": case_id,
                                "kind": "CORRELATION",
                                "rule_or_key": "USER_ACTIVITY_CORRELATION",
                                "severity": "MEDIUM",
                                "related_event_ids": [e1.id, e2.id],
                                "related_evidence_ids": [],
                                "description": (
                                    f"Potentially related events detected: User '{user}' associated with "
                                    f"'{e1.event_type}' and '{e2.event_type}' within {int(delta // 60)} minutes. "
                                    f"(Correlated temporal activity — not confirmed causation)."
                                )
                            })
                            break  # pair once per base event to avoid flood
                    else:
                        break

        # 2. Correlate Events by IP reference
        ip_map: Dict[str, List[SecurityEvent]] = {}
        for ev in events:
            if ev.ip_ref and ev.ip_ref != "127.0.0.1" and ev.ip_ref != "localhost":
                ip_map.setdefault(ev.ip_ref, []).append(ev)

        for ip, ip_events in ip_map.items():
            if len(ip_events) < 2:
                continue
            distinct_users = {e.event_user for e in ip_events if e.event_user}
            if len(distinct_users) > 1:
                e_ids = [e.id for e in ip_events[:5]]
                correlation_findings.append({
                    "case_id": case_id,
                    "kind": "CORRELATION",
                    "rule_or_key": "SHARED_IP_MULTI_USER",
                    "severity": "HIGH",
                    "related_event_ids": e_ids,
                    "related_evidence_ids": [],
                    "description": (
                        f"Potentially related events detected: IP address '{ip}' was observed performing "
                        f"actions across multiple usernames ({', '.join(sorted(list(distinct_users))[:4])}). "
                        f"(Correlated network origin — not confirmed causation)."
                    )
                })

        # 3. Correlate Evidence with Log Events (shared source or filename mentioned in raw_line)
        for evd in evidence_list:
            matched_events = []
            for ev in events:
                if (evd.name and evd.name.lower() in (ev.raw_line or "").lower()) or \
                   (evd.source and ev.source and evd.source.lower() == ev.source.lower()):
                    matched_events.append(ev.id)
            if matched_events:
                correlation_findings.append({
                    "case_id": case_id,
                    "kind": "CORRELATION",
                    "rule_or_key": "EVIDENCE_LOG_SOURCE_LINK",
                    "severity": "LOW",
                    "related_event_ids": matched_events[:10],
                    "related_evidence_ids": [evd.id],
                    "description": (
                        f"Potentially related evidence link: Evidence artifact '{evd.name}' corresponds to "
                        f"{len(matched_events)} security event log entries from source '{evd.source}'. "
                        f"(Cross-referenced artifact — not confirmed causation)."
                    )
                })

        if correlation_findings:
            self.finding_repo.bulk_insert(correlation_findings)

        return correlation_findings
