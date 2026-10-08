import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "tracex-dev-secret-key-change-in-production-12345")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "database" / "tracex.db"))
    EVIDENCE_STORE_PATH = os.environ.get("EVIDENCE_STORE_PATH", str(BASE_DIR / "evidence-store"))
    REPORTS_PATH = os.environ.get("REPORTS_PATH", str(BASE_DIR / "reports"))
    
    # 16 MB maximum file upload limit
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {"log", "csv", "jsonl", "txt", "bin", "raw", "dump", "cfg", "json"}
    
    # Security session settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Set to True in production with TLS
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    DATABASE_PATH = ":memory:"
    EVIDENCE_STORE_PATH = str(BASE_DIR / "evidence-store" / "test_store")
