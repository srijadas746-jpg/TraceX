import sqlite3
import os
from pathlib import Path
from flask import g, current_app, has_app_context

BASE_DIR = Path(__file__).resolve().parent.parent

def get_db_path():
    if has_app_context() and current_app:
        return current_app.config.get("DATABASE_PATH")
    return os.environ.get("DATABASE_PATH", str(BASE_DIR / "database" / "tracex.db"))

def get_db(db_path=None):
    target_path = db_path or get_db_path()
    
    if not db_path and has_app_context():
        if "db" in g:
            return g.db

    conn = sqlite3.connect(
        target_path,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    
    if not db_path and has_app_context():
        g.db = conn
    return conn

def close_db(e=None):
    if has_app_context():
        db = g.pop("db", None)
        if db is not None:
            db.close()

def init_db(db_path=None):
    path = db_path or get_db_path()
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
    conn = get_db(path)
    schema_file = BASE_DIR / "database" / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    if db_path or not has_app_context():
        conn.close()
