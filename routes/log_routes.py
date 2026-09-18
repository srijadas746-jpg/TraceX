import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from services.log_analysis_service import LogAnalysisService
from services.case_service import CaseService
from repositories.event_repository import EventRepository
from repositories.finding_repository import FindingRepository
from routes.auth_middleware import login_required, role_required, get_current_user

log_bp = Blueprint("logs", __name__)

log_service = LogAnalysisService()
case_service = CaseService()
event_repo = EventRepository()
finding_repo = FindingRepository()

@log_bp.route("/cases/<int:case_id>/logs/import", methods=["GET", "POST"])
@log_bp.route("/logs/import", methods=["POST"])
@role_required("ADMIN", "INVESTIGATOR")
def import_logs(case_id: int = None):
    target_case_id = case_id or request.form.get("case_id", type=int)
    if not target_case_id:
        abort(400, description="case_id is required.")

    case = case_service.get_case(target_case_id)
    if not case:
        abort(404, description="Target case not found.")

    if request.method == "POST":
        file_obj = request.files.get("log_file")
        if not file_obj or not file_obj.filename:
            flash("Please choose a log file to import (.csv or .jsonl).", "danger")
            return redirect(url_for("logs.import_logs", case_id=target_case_id))

        filename = file_obj.filename.lower()
        if filename.endswith(".csv"):
            fmt = "csv"
        elif filename.endswith(".jsonl") or filename.endswith(".json"):
            fmt = "jsonl"
        else:
            flash("Unsupported log format. Only .csv and .jsonl files are accepted.", "danger")
            return redirect(url_for("logs.import_logs", case_id=target_case_id))

        try:
            content = file_obj.read().decode("utf-8", errors="replace")
            stream = io.StringIO(content)
            result = log_service.import_logs_from_stream(target_case_id, stream, file_format=fmt)

            flash(
                f"Log Import Complete: Successfully ingested {result['imported_events']} valid events "
                f"from {result['total_rows_read']} rows. Skipped {result['error_count']} invalid/malformed rows.",
                "success" if result["imported_events"] > 0 else "warning"
            )
            return redirect(url_for("cases.view_case", case_id=target_case_id, tab="logs"))
        except Exception as e:
            flash(f"Error reading log file: {str(e)}", "danger")

    return render_template("logs/import.html", case=case)

@log_bp.route("/cases/<int:case_id>/logs/analyze", methods=["POST"])
@log_bp.route("/logs/<int:case_id>/analyze", methods=["POST"])
@role_required("ADMIN", "INVESTIGATOR")
def analyze_logs(case_id: int):
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    findings = log_service.run_rules(case_id)
    if findings:
        flash(f"Rule Engine executed successfully: {len(findings)} system-generated indicator(s) identified.", "warning")
    else:
        flash("Rule Engine executed: No suspicious rule conditions triggered across current events.", "info")

    return redirect(url_for("cases.view_case", case_id=case_id, tab="findings"))
