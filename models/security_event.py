from dataclasses import dataclass
from typing import Optional

@dataclass
class SecurityEvent:
    id: Optional[int]
    case_id: int
    event_type: str
    event_user: Optional[str]
    source: str
    ip_ref: Optional[str]
    event_timestamp: str
    raw_line: Optional[str]

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            case_id=row["case_id"],
            event_type=row["event_type"],
            event_user=row["event_user"],
            source=row["source"],
            ip_ref=row["ip_ref"],
            event_timestamp=row["event_timestamp"],
            raw_line=row["raw_line"]
        )

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "event_type": self.event_type,
            "event_user": self.event_user,
            "source": self.source,
            "ip_ref": self.ip_ref,
            "event_timestamp": self.event_timestamp,
            "raw_line": self.raw_line
        }
