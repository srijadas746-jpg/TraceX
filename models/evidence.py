from dataclasses import dataclass
from typing import Optional

@dataclass
class Evidence:
    id: Optional[int]
    case_id: int
    name: str
    type: str
    source: str
    file_path: str
    file_size: int
    sha256_original: str
    sha256_current: Optional[str]
    integrity_status: str  # 'VERIFIED', 'MODIFIED', 'MISSING', 'NOT_VERIFIED'
    description: Optional[str]
    collected_at: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            case_id=row["case_id"],
            name=row["name"],
            type=row["type"],
            source=row["source"],
            file_path=row["file_path"],
            file_size=row["file_size"],
            sha256_original=row["sha256_original"],
            sha256_current=row["sha256_current"],
            integrity_status=row["integrity_status"],
            description=row["description"],
            collected_at=row["collected_at"]
        )

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "name": self.name,
            "type": self.type,
            "source": self.source,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "sha256_original": self.sha256_original,
            "sha256_current": self.sha256_current,
            "integrity_status": self.integrity_status,
            "description": self.description,
            "collected_at": self.collected_at
        }
