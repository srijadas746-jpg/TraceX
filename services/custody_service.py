from typing import Optional, List, Tuple
from repositories.custody_repository import CustodyRepository
from models.custody_record import CustodyRecord

ALLOWED_ACTIONS = {"COLLECTED", "TRANSFERRED", "REVIEWED", "VERIFIED", "EXPORTED"}

class CustodyService:
    """
    Append-only Chain of Custody Service.
    Enforces immutable forensic audit trails for all evidence interactions.
    """
    def __init__(self, custody_repo: Optional[CustodyRepository] = None):
        self.custody_repo = custody_repo or CustodyRepository()

    def log_action(self, evidence_id: int, action: str, actor_id: int,
                   prev_status: Optional[str] = None,
                   new_status: Optional[str] = None,
                   remarks: Optional[str] = None) -> Tuple[bool, str, Optional[CustodyRecord]]:
        if action not in ALLOWED_ACTIONS:
            return False, f"Invalid custody action: {action}. Must be one of {ALLOWED_ACTIONS}", None

        record = self.custody_repo.create(
            evidence_id=evidence_id,
            action=action,
            actor_id=actor_id,
            prev_status=prev_status,
            new_status=new_status,
            remarks=remarks
        )
        return True, "Custody record appended.", record

    def get_evidence_custody_history(self, evidence_id: int) -> List[CustodyRecord]:
        return self.custody_repo.list_by_evidence(evidence_id)

    def get_case_custody_history(self, case_id: int) -> List[CustodyRecord]:
        return self.custody_repo.list_by_case(case_id)
