import os
import sys
import io
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import get_db, init_db
from services.case_service import CaseService
from services.evidence_service import EvidenceService
from services.log_analysis_service import LogAnalysisService
from services.correlation_service import CorrelationService
from services.report_service import ReportService

def seed(db_path=None, seed_demo=True):
    target_path = db_path or str(BASE_DIR / "database" / "tracex.db")
    print(f"[*] Initializing database at: {target_path}")
    init_db(target_path)

    conn = get_db(target_path)
    cursor = conn.cursor()

    # 1. Seed Core Users
    users_to_seed = [
        ("admin", generate_password_hash("AdminPassword@123"), "ADMIN"),
        ("investigator", generate_password_hash("Investigator@123"), "INVESTIGATOR"),
    ]

    for username, pwd_hash, role in users_to_seed:
        cursor.execute(
            "INSERT OR IGNORE INTO User (username, password_hash, role) VALUES (?, ?, ?);",
            (username, pwd_hash, role)
        )
    conn.commit()

    cursor.execute("SELECT id, username, role FROM User;")
    users = cursor.fetchall()
    print(f"[+] Total registered accounts: {len(users)}")
    for u in users:
        print(f"    - User #{u['id']}: {u['username']} ({u['role']})")

    # 2. Seed Initial Demonstration Scenario if requested
    if seed_demo:
        cursor.execute('SELECT COUNT(*) FROM "Case";')
        case_count = cursor.fetchone()[0]
        if case_count == 0:
            print("[*] Seeding initial demonstration case: 'Operation Aurora — Infiltration & Exfiltration'...")
            cursor.execute('SELECT id FROM User WHERE username = "investigator";')
            inv_row = cursor.fetchone()
            inv_id = inv_row[0] if inv_row else 1

            case_service = CaseService()
            _, _, demo_case = case_service.create_case(
                title="Operation Aurora — Infiltration & Credential Abuse",
                incident_type="Brute Force Authentication",
                description="Simulated multi-stage incident involving repeated authentication failures, account lockout, and unauthorized access sequences across Domain Controller DC-PROD-01.",
                investigator_id=inv_id
            )

            # Seed evidence
            evidence_sample_path = BASE_DIR / "sample-data" / "evidence_samples" / "auth_dump.raw"
            if evidence_sample_path.exists():
                evidence_service = EvidenceService()
                with open(evidence_sample_path, "rb") as f:
                    content = f.read()
                    stream = io.BytesIO(content)
                    stream.filename = "auth_dump.raw"
                    _, _, ev = evidence_service.add_evidence(
                        case_id=demo_case.id,
                        file_obj=stream,
                        name="auth_dump.raw",
                        evidence_type="DISK_IMAGE",
                        source="DC-PROD-01",
                        description="Acquired sector snapshot of authentication store.",
                        actor_id=inv_id
                    )
                    evidence_service.verify_evidence(ev.id, actor_id=inv_id)
                print(f"[+] Seeded digital evidence artifact #{ev.id} ('{ev.name}') with verified SHA-256.")

            # Seed security events from bruteforce sample log
            log_sample_path = BASE_DIR / "sample-data" / "logs_bruteforce.csv"
            if log_sample_path.exists():
                log_service = LogAnalysisService()
                with open(log_sample_path, "r", encoding="utf-8") as f:
                    log_stream = io.StringIO(f.read())
                    log_res = log_service.import_logs_from_stream(demo_case.id, log_stream, file_format="csv")
                    print(f"[+] Ingested {log_res['imported_events']} security events from sample-data/logs_bruteforce.csv.")

                # Run rule engine
                findings = log_service.run_rules(demo_case.id)
                print(f"[+] Rule Engine executed: Generated {len(findings)} system indicator findings (R1, R2).")

                # Run correlation engine
                corr_service = CorrelationService()
                correlations = corr_service.run_correlation(demo_case.id)
                print(f"[+] Correlation Engine executed: Generated {len(correlations)} correlated links.")

                # Generate initial report
                report_service = ReportService()
                report_service.generate_case_report(demo_case.id)
                report_service.generate_markdown_report(demo_case.id)
                print(f"[+] Compiled baseline investigation report for Case #{demo_case.id}.")

    conn.close()
    print("[+] Database initialization and seeding completed successfully.")

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else None
    seed(db_file)
