from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, Response, send_file
from services.report_service import ReportService
from services.case_service import CaseService
from routes.auth_middleware import login_required, role_required

report_bp = Blueprint("reports", __name__)

report_service = ReportService()
case_service = CaseService()

@report_bp.route("/cases/<int:case_id>/report", methods=["GET"])
@login_required
def view_report(case_id: int):
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    report_data = report_service.generate_case_report(case_id)
    return render_template("reports/view.html", case=case, report=report_data)

@report_bp.route("/reports/<int:case_id>", methods=["POST"])
@report_bp.route("/cases/<int:case_id>/report/generate", methods=["POST"])
@role_required("ADMIN", "INVESTIGATOR")
def generate_report(case_id: int):
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    report_data = report_service.generate_case_report(case_id)
    report_service.generate_markdown_report(case_id)

    flash("Investigation report compiled successfully with evidentiary labeling.", "success")
    return redirect(url_for("reports.view_report", case_id=case_id))

@report_bp.route("/cases/<int:case_id>/report/download", methods=["GET"])
@login_required
def download_markdown_report(case_id: int):
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    md_content = report_service.generate_markdown_report(case_id)
    filename = f"TraceX_Investigation_Report_Case_{case_id}.md"

    return Response(
        md_content,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@report_bp.route("/cases/<int:case_id>/report/json", methods=["GET"])
@login_required
def download_json_report(case_id: int):
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    report_data = report_service.generate_case_report(case_id)
    return jsonify(report_data)
