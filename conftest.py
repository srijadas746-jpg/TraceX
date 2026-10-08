import os
import tempfile
import shutil
import pytest
from pathlib import Path
from werkzeug.security import generate_password_hash

from app import create_app
from config import TestingConfig
from database.db import get_db, init_db

@pytest.fixture
def test_env():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_tracex.db")
    store_path = os.path.join(temp_dir, "test_store")
    reports_path = os.path.join(temp_dir, "test_reports")
    os.makedirs(store_path, exist_ok=True)
    os.makedirs(reports_path, exist_ok=True)

    class CustomTestConfig(TestingConfig):
        DATABASE_PATH = db_path
        EVIDENCE_STORE_PATH = store_path
        REPORTS_PATH = reports_path
        TESTING = True
        WTF_CSRF_ENABLED = False

    app = create_app(CustomTestConfig)
    
    with app.app_context():
        init_db(db_path)
        conn = get_db(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO User (username, password_hash, role) VALUES (?, ?, ?);",
            ("admin", generate_password_hash("AdminPassword@123"), "ADMIN")
        )
        cursor.execute(
            "INSERT INTO User (username, password_hash, role) VALUES (?, ?, ?);",
            ("investigator", generate_password_hash("Investigator@123"), "INVESTIGATOR")
        )
        conn.commit()

    yield {
        "app": app,
        "client": app.test_client(),
        "db_path": db_path,
        "store_path": store_path,
        "temp_dir": temp_dir
    }

    shutil.rmtree(temp_dir, ignore_errors=True)
