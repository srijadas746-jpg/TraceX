import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from werkzeug.utils import secure_filename

from config import Config
from repositories.evidence_repository import EvidenceRepository
from repositories.finding_repository import FindingRepository
from services.hash_service import HashService
from services.custody_service import CustodyService
from models.evidence import Evidence
from models.custody_record import CustodyRecord

class EvidenceService:
    def __init__(self,
                 evidence_repo: Optional[EvidenceRepository] = None,
                 hash_service: Optional[HashService] = None,
                 custody_service: Optional[CustodyService] = None,
                 finding_repo: Optional[FindingRepository] = None,
                 store_dir: Optional[str] = None):
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.hash_service = hash_service or HashService()
        self.custody_service = custody_service or CustodyService()
        self.finding_repo = finding_repo or FindingRepository()
        self.store_dir = store_dir or Config.EVIDENCE_STORE_PATH

    def _is_allowed_extension(self, filename: str) -> bool:
        if "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in Config.ALLOWED_EXTENSIONS

    def add_evidence(self, case_id: int, file_obj, name: str,
                     evidence_type: str, source: str, description: Optional[str],
                     actor_id: int) -> Tuple[bool, str, Optional[Evidence]]:
        if not file_obj or not getattr(file_obj, "filename", None):
            return False, "No file provided for evidence acquisition.", None

        original_filename = secure_filename(file_obj.filename)
        if not original_filename:
            return False, "Invalid filename.", None

        if not self._is_allowed_extension(original_filename):
            return False, f"File extension not permitted. Allowed extensions: {', '.join(sorted(Config.ALLOWED_EXTENSIONS))}", None

        # Build isolated target directory: evidence-store/case_<id>/
        case_store = Path(self.store_dir) / f"case_{case_id}"
        case_store.mkdir(parents=True, exist_ok=True)

        target_file_path = case_store / original_filename
        # Avoid clobbering if same filename exists
        counter = 1
        base_stem = target_file_path.stem
        suffix = target_file_path.suffix
        while target_file_path.exists():
            target_file_path = case_store / f"{base_stem}_{counter}{suffix}"
            counter += 1

        # Save file safely to storage (supporting both FileStorage and BytesIO/file-like)
        try:
            if hasattr(file_obj, "save"):
                file_obj.save(str(target_file_path))
            elif hasattr(file_obj, "read"):
                with open(str(target_file_path), "wb") as f:
                    content = file_obj.read()
                    f.write(content if isinstance(content, bytes) else content.encode("utf-8"))
            else:
                return False, "Unsupported file stream object.", None
        except Exception as e:
            return False, f"Failed to save evidence file securely: {str(e)}", None

        # Compute SHA-256 immediately upon acquisition
        file_size = target_file_path.stat().st_size
        sha256_hash = self.hash_service.compute_file_hash(str(target_file_path))
        if not sha256_hash:
            return False, "Failed to compute cryptographic hash for evidence.", None

        # Insert Evidence row
        display_name = name.strip() if name and name.strip() else original_filename
        evidence = self.evidence_repo.create(
            case_id=case_id,
            name=display_name,
            type=evidence_type,
            source=source.strip() if source else "Unknown",
            file_path=str(target_file_path),
            file_size=file_size,
            sha256_original=sha256_hash,
            description=description
        )

        # Record initial chain of custody entry
        self.custody_service.log_action(
            evidence_id=evidence.id,
            action="COLLECTED",
            actor_id=actor_id,
            prev_status=None,
            new_status="NOT_VERIFIED",
            remarks=f"Evidence acquired and registered with initial SHA-256: {sha256_hash[:16]}..."
        )

        return True, "Evidence registered and hashed successfully.", evidence

    def verify_evidence(self, evidence_id: int, actor_id: int) -> Tuple[bool, str, Optional[Evidence], Optional[CustodyRecord]]:
        evidence = self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            return False, "Evidence not found.", None, None

        prev_status = evidence.integrity_status
        target_path = evidence.file_path

        if not os.path.exists(target_path):
            new_status = "MISSING"
            current_hash = None
            remarks = "Verification failed: Evidence file could not be found on storage media."
        else:
            current_hash = self.hash_service.compute_file_hash(target_path)
            if current_hash == evidence.sha256_original:
                new_status = "VERIFIED"
                remarks = f"Cryptographic integrity confirmed. Current SHA-256 matches baseline ({current_hash[:16]}...)."
            else:
                new_status = "MODIFIED"
                remarks = (f"CRITICAL: Integrity violation detected! Baseline: {evidence.sha256_original[:16]}... "
                           f"vs Current: {current_hash[:16] if current_hash else 'N/A'}...")

        # Update evidence status in database
        updated_evidence = self.evidence_repo.update_hash_and_status(evidence_id, current_hash, new_status)

        # Log custody verification entry
        _, _, custody_rec = self.custody_service.log_action(
            evidence_id=evidence_id,
            action="VERIFIED",
            actor_id=actor_id,
            prev_status=prev_status,
            new_status=new_status,
            remarks=remarks
        )

        # If modified, create rule R4 CRITICAL finding according to frozen blueprint
        if new_status == "MODIFIED":
            desc = (f"Integrity warning: registered evidence '{evidence.name}' (ID #{evidence.id}) "
                    f"changed after acquisition. Expected hash: {evidence.sha256_original}, "
                    f"Computed hash: {current_hash}.")
            self.finding_repo.create(
                case_id=evidence.case_id,
                kind="INDICATOR",
                rule_or_key="R4",
                severity="CRITICAL",
                related_event_ids=[],
                related_evidence_ids=[evidence.id],
                description=desc
            )

        return True, f"Verification completed: status is {new_status}.", updated_evidence, custody_rec

    def tamper_evidence_demo(self, evidence_id: int, actor_id: int) -> Tuple[bool, str]:
        """
        Demonstration utility: Safely appends synthetic modification bytes to simulate evidence tampering.
        """
        evidence = self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            return False, "Evidence not found."

        if not os.path.exists(evidence.file_path):
            return False, "Evidence file does not exist on disk."

        try:
            with open(evidence.file_path, "ab") as f:
                f.write(b"\n[SIMULATED_TAMPER_ARTIFACT_MODIFIED]\n")
            return True, f"Simulated tamper artifact written to '{evidence.name}'. Re-verify to observe status change."
        except Exception as e:
            return False, f"Failed to simulate file modification: {str(e)}"

    def get_evidence(self, evidence_id: int) -> Optional[Evidence]:
        return self.evidence_repo.get_by_id(evidence_id)

    def list_by_case(self, case_id: int) -> List[Evidence]:
        return self.evidence_repo.list_by_case(case_id)

    def count_by_status(self, case_id: Optional[int] = None) -> Dict[str, int]:
        return self.evidence_repo.count_by_status(case_id)
