from dataclasses import dataclass
from typing import Optional

@dataclass
class CustodyRecord:
    id: Optional[int]
    evidence_id: int
    action: str  # 'COLLECTED', 'TRANSFERRED', 'REVIEWED', 'VERIFIED', 'EXPORTED'
    actor_id: int
    prev_status: Optional[str]
    new_status: Optional[str]
    remarks: Optional[str]
    timestamp: Optional[str] = None
    actor_username: Optional[str] = None  # Helper for display

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        keys = row.keys() if hasattr(row, "keys") else row
        return cls(
            id=row["id"],
            evidence_id=row["evidence_id"],
            action=row["action"],
            actor_id=row["actor_id"],
            prev_status=row["prev_status"],
            new_status=row["new_status"],
            remarks=row["remarks"],
            timestamp=row["timestamp"],
            actor_username=row["actor_username"] if "actor_username" in keys else None
        )

    def to_dict(self):
        return {
            "id": self.id,
            "evidence_id": self.evidence_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "prev_status": self.prev_status,
            "new_status": self.new_status,
            "remarks": self.remarks,
            "timestamp": self.timestamp,
            "actor_username": self.actor_username
        }
