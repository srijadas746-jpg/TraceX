import hashlib
import os
from typing import Optional

class HashService:
    """
    Cryptographic SHA-256 hashing service for digital forensic evidence.
    Verifies byte-level integrity relative to the recorded acquisition hash.
    Important: Hashing proves whether bytes have changed since recording;
    it does NOT attribute who modified a file.
    """
    CHUNK_SIZE = 65536  # 64 KB

    @classmethod
    def compute_file_hash(cls, file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            return None
        
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(cls.CHUNK_SIZE)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError):
            return None

    @classmethod
    def compute_bytes_hash(cls, data: bytes) -> str:
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()
