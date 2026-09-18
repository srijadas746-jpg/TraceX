import json
from dataclasses import dataclass
from typing import Optional, List, Any

@dataclass
class Finding:
    id: Optional[int]
    case_id: int
    kind: str  # 'INDICATOR' or 'CORRELATION'
    rule_or_key: str
    severity: str  # 'INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    related_event_ids: Optional[str]  # JSON string in DB
    related_evidence_ids: Optional[str]  # JSON string in DB
    description: str
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            case_id=row["case_id"],
            kind=row["kind"],
            rule_or_key=row["rule_or_key"],
            severity=row["severity"],
            related_event_ids=row["related_event_ids"],
            related_evidence_ids=row["related_evidence_ids"],
            description=row["description"],
            created_at=row["created_at"]
        )

    @property
    def event_ids_list(self) -> List[int]:
        if not self.related_event_ids:
            return []
        try:
            return json.loads(self.related_event_ids)
        except Exception:
            return []

    @property
    def evidence_ids_list(self) -> List[int]:
        if not self.related_evidence_ids:
            return []
        try:
            return json.loads(self.related_evidence_ids)
        except Exception:
            return []

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "kind": self.kind,
            "rule_or_key": self.rule_or_key,
            "severity": self.severity,
            "related_event_ids": self.event_ids_list,
            "related_evidence_ids": self.evidence_ids_list,
            "description": self.description,
            "created_at": self.created_at
        }
