from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from services.case_service import CaseService
from services.evidence_service import EvidenceService
from services.custody_service import CustodyService
from services.log_analysis_service import LogAnalysisService
from services.timeline_service import TimelineService
from services.correlation_service import CorrelationService
from repositories.finding_repository import FindingRepository
from repositories.event_repository import EventRepository
from routes.auth_middleware import login_required, role_required, get_current_user

case_bp = Blueprint("cases", __name__)

case_service = CaseService()
evidence_service = EvidenceService()
custody_service = CustodyService()
log_service = LogAnalysisService()
timeline_service = TimelineService()
correlation_service = CorrelationService()
finding_repo = FindingRepository()
event_repo = EventRepository()

@case_bp.route("/")
@case_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    cases_metrics = case_service.get_metrics()
    evidence_status_counts = evidence_service.count_by_status()
    total_evidence = sum(evidence_status_counts.values())
    total_events = event_repo.count_all()
    total_findings = finding_repo.count_all()
    severity_distribution = finding_repo.get_severity_distribution()

    recent_cases = case_service.list_cases()[:5]

    return render_template(
        "dashboard.html",
        user=user,
        cases_metrics=cases_metrics,
        evidence_status_counts=evidence_status_counts,
        total_evidence=total_evidence,
        total_events=total_events,
        total_findings=total_findings,
        severity_distribution=severity_distribution,
        recent_cases=recent_cases
    )

@case_bp.route("/cases", methods=["GET"])
@login_required
def list_cases():
    status = request.args.get("status")
    incident_type = request.args.get("incident_type")
    cases = case_service.list_cases(status=status, incident_type=incident_type)
    return render_template("cases/list.html", cases=cases, current_status=status, current_type=incident_type)

@case_bp.route("/cases/new", methods=["GET", "POST"])
@role_required("ADMIN", "INVESTIGATOR")
def create_case():
    user = get_current_user()
    if request.method == "POST":
        title = request.form.get("title")
        incident_type = request.form.get("incident_type")
        description = request.form.get("description")

        success, message, new_case = case_service.create_case(
            title=title,
            incident_type=incident_type,
            description=description,
            investigator_id=user.id
        )

        if success:
            flash(f"Case #{new_case.id} '{new_case.title}' opened successfully.", "success")
            return redirect(url_for("cases.view_case", case_id=new_case.id))
        else:
            flash(message, "danger")

    return render_template("cases/create.html")

@case_bp.route("/cases/<int:case_id>", methods=["GET"])
@login_required
def view_case(case_id: int):
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    tab = request.args.get("tab", "overview")
    evidence_list = evidence_service.list_by_case(case_id)
    custody_records = custody_service.get_case_custody_history(case_id)
    events_count = event_repo.count_by_case(case_id)
    recent_events = event_repo.list_by_case(case_id, limit=50)
    findings = finding_repo.list_by_case(case_id)
    timeline_data = timeline_service.build_timeline(case_id)

    indicators = [f for f in findings if f.kind == "INDICATOR"]
    correlations = [f for f in findings if f.kind == "CORRELATION"]
    severity_distribution = finding_repo.get_severity_distribution(case_id)

    return render_template(
        "cases/detail.html",
        case=case,
        current_tab=tab,
        evidence_list=evidence_list,
        custody_records=custody_records,
        events_count=events_count,
        recent_events=recent_events,
        findings=findings,
        indicators=indicators,
        correlations=correlations,
        timeline_data=timeline_data,
        severity_distribution=severity_distribution
    )

@case_bp.route("/cases/<int:case_id>/edit", methods=["GET", "POST"])
@role_required("ADMIN", "INVESTIGATOR")
def edit_case(case_id: int):
    user = get_current_user()
    case = case_service.get_case(case_id)
    if not case:
        abort(404, description="Case not found.")

    if request.method == "POST":
        title = request.form.get("title")
        incident_type = request.form.get("incident_type")
        description = request.form.get("description")

        success, message, updated_case = case_service.update_case(
            case_id=case_id,
            title=title,
            incident_type=incident_type,
            description=description,
            user=user
        )

        if success:
            flash("Case details updated successfully.", "success")
            return redirect(url_for("cases.view_case", case_id=case_id))
        else:
            flash(message, "danger")

    return render_template("cases/edit.html", case=case)

@case_bp.route("/cases/<int:case_id>/close", methods=["POST"])
@role_required("ADMIN", "INVESTIGATOR")
def close_case(case_id: int):
    user = get_current_user()
    success, message, _ = case_service.close_case(case_id, user)
    if success:
        flash(message, "success")
    else:
        flash(message, "warning")
    return redirect(url_for("cases.view_case", case_id=case_id))

@case_bp.route("/cases/<int:case_id>/delete", methods=["POST"])
@role_required("ADMIN")
def delete_case(case_id: int):
    user = get_current_user()
    success, message = case_service.delete_case(case_id, user)
    if success:
        flash(message, "success")
        return redirect(url_for("cases.list_cases"))
    else:
        flash(message, "danger")
        return redirect(url_for("cases.view_case", case_id=case_id))
