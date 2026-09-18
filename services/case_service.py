from typing import Optional, List, Dict, Any, Tuple
from repositories.case_repository import CaseRepository
from models.case import Case
from models.user import User

class CaseService:
    def __init__(self, case_repo: Optional[CaseRepository] = None):
        self.case_repo = case_repo or CaseRepository()

    def create_case(self, title: str, incident_type: str, description: Optional[str], investigator_id: int) -> Tuple[bool, str, Optional[Case]]:
        title = title.strip() if title else ""
        incident_type = incident_type.strip() if incident_type else ""
        
        if not title:
            return False, "Case title cannot be empty.", None
        if not incident_type:
            return False, "Incident type cannot be empty.", None

        case = self.case_repo.create(title, incident_type, description, investigator_id)
        return True, "Case created successfully.", case

    def get_case(self, case_id: int) -> Optional[Case]:
        return self.case_repo.get_by_id(case_id)

    def list_cases(self, status: Optional[str] = None, incident_type: Optional[str] = None) -> List[Case]:
        return self.case_repo.list_all(status=status, incident_type=incident_type)

    def update_case(self, case_id: int, title: str, incident_type: str,
                    description: Optional[str], user: User) -> Tuple[bool, str, Optional[Case]]:
        case = self.get_case(case_id)
        if not case:
            return False, "Case not found.", None

        # Check authorization: ADMIN or the assigned investigator
        if user.role != "ADMIN" and case.investigator_id != user.id:
            return False, "Unauthorized: Only the assigned investigator or an admin can update this case.", None

        title = title.strip() if title else ""
        incident_type = incident_type.strip() if incident_type else ""
        if not title:
            return False, "Case title cannot be empty.", None
        if not incident_type:
            return False, "Incident type cannot be empty.", None

        updated = self.case_repo.update(case_id, title, incident_type, description)
        return True, "Case updated successfully.", updated

    def close_case(self, case_id: int, user: User) -> Tuple[bool, str, Optional[Case]]:
        case = self.get_case(case_id)
        if not case:
            return False, "Case not found.", None

        if user.role != "ADMIN" and case.investigator_id != user.id:
            return False, "Unauthorized: Only the assigned investigator or an admin can close this case.", None

        if case.status == "CLOSED":
            return False, "Case is already closed.", case

        closed = self.case_repo.close(case_id)
        return True, "Case closed successfully.", closed

    def delete_case(self, case_id: int, user: User) -> Tuple[bool, str]:
        if user.role != "ADMIN":
            return False, "Unauthorized: Only administrators can delete cases."
        case = self.get_case(case_id)
        if not case:
            return False, "Case not found."
        deleted = self.case_repo.delete(case_id)
        if deleted:
            return True, "Case deleted successfully."
        return False, "Failed to delete case."

    def get_metrics(self) -> Dict[str, int]:
        return self.case_repo.get_metrics()
