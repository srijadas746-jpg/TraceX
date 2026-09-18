from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from services.timeline_service import TimelineService
from services.correlation_service import CorrelationService
from services.case_service import CaseService
from repositories.finding_repository import FindingRepository
from routes.auth_middleware import login_required, role_required

timeline_bp = Blueprint("timeline", __name__)

timeline_service = TimelineService()
correlation_service = CorrelationService()
case_service = CaseService()
finding_repo = FindingRepository()

@timeline_bp.route("/cases/<int:case_id>/timeline", methods=["GET"])
@timeline_bp.route("/timeline/<int:case_id>", methods=["GET"])
@login_required
def view_timeline(case_id: int):
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    timeline_data = timeline_service.build_timeline(case_id)
    return render_template("timeline/view.html", case=case, timeline=timeline_data)

@timeline_bp.route("/cases/<int:case_id>/correlations/run", methods=["POST"])
@role_required("ADMIN", "INVESTIGATOR")
def run_correlation(case_id: int):
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    window = request.form.get("window_minutes", 30, type=int)
    results = correlation_service.run_correlation(case_id, window_minutes=window)

    if results:
        flash(f"Correlation Engine completed: {len(results)} potential correlation link(s) identified.", "warning")
    else:
        flash("Correlation Engine completed: No cross-entity correlation links matched the parameters.", "info")

    return redirect(url_for("cases.view_case", case_id=case_id, tab="correlation"))

@timeline_bp.route("/correlations/<int:case_id>", methods=["GET"])
@login_required
def get_correlations_json(case_id: int):
    findings = finding_repo.list_by_case(case_id, kind="CORRELATION")
    return jsonify([f.to_dict() for f in findings])
