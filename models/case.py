from dataclasses import dataclass
from typing import Optional

@dataclass
class Case:
    id: Optional[int]
    title: str
    incident_type: str
    description: Optional[str]
    status: str  # 'OPEN' or 'CLOSED'
    investigator_id: int
    created_at: Optional[str] = None
    closed_at: Optional[str] = None
    investigator_username: Optional[str] = None  # Helper for joined queries

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # Handle dict or sqlite3.Row
        keys = row.keys() if hasattr(row, "keys") else row
        return cls(
            id=row["id"],
            title=row["title"],
            incident_type=row["incident_type"],
            description=row["description"],
            status=row["status"],
            investigator_id=row["investigator_id"],
            created_at=row["created_at"],
            closed_at=row["closed_at"],
            investigator_username=row["investigator_username"] if "investigator_username" in keys else None
        )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "incident_type": self.incident_type,
            "description": self.description,
            "status": self.status,
            "investigator_id": self.investigator_id,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "investigator_username": self.investigator_username
        }
