from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from services.evidence_service import EvidenceService
from services.custody_service import CustodyService
from services.case_service import CaseService
from routes.auth_middleware import login_required, role_required, get_current_user

evidence_bp = Blueprint("evidence", __name__)

evidence_service = EvidenceService()
custody_service = CustodyService()
case_service = CaseService()

@evidence_bp.route("/cases/<int:case_id>/evidence/new", methods=["GET", "POST"])
@evidence_bp.route("/evidence", methods=["POST"])
@role_required("ADMIN", "INVESTIGATOR")
def add_evidence(case_id: int = None):
    user = get_current_user()
    target_case_id = case_id or request.form.get("case_id", type=int)
    if not target_case_id:
        abort(400, description="case_id is required.")

    case = case_service.get_case(target_case_id)
    if not case:
        abort(404, description="Target case not found.")

    if request.method == "POST":
        file_obj = request.files.get("evidence_file")
        name = request.form.get("name")
        evidence_type = request.form.get("type", "LOG")
        source = request.form.get("source", "Internal Network")
        description = request.form.get("description")

        success, message, evidence = evidence_service.add_evidence(
            case_id=target_case_id,
            file_obj=file_obj,
            name=name,
            evidence_type=evidence_type,
            source=source,
            description=description,
            actor_id=user.id
        )

        if success:
            flash(f"Evidence '{evidence.name}' acquired and registered with SHA-256 baseline.", "success")
            return redirect(url_for("evidence.view_evidence", evidence_id=evidence.id))
        else:
            flash(message, "danger")

    return render_template("evidence/upload.html", case=case)

@evidence_bp.route("/evidence/<int:evidence_id>", methods=["GET"])
@login_required
def view_evidence(evidence_id: int):
    evidence = evidence_service.get_evidence(evidence_id)
    if not evidence:
        abort(404, description="Evidence item not found.")

    case = case_service.get_case(evidence.case_id)
    custody_records = custody_service.get_evidence_custody_history(evidence_id)

    return render_template(
        "evidence/detail.html",
        evidence=evidence,
        case=case,
        custody_records=custody_records
    )

@evidence_bp.route("/evidence/<int:evidence_id>/verify", methods=["POST"])
@role_required("ADMIN", "INVESTIGATOR")
def verify_evidence(evidence_id: int):
    user = get_current_user()
    success, message, evidence, _ = evidence_service.verify_evidence(evidence_id, user.id)

    if success:
        if evidence.integrity_status == "VERIFIED":
            flash("Integrity Verified: SHA-256 hash matches recorded baseline perfectly.", "success")
        elif evidence.integrity_status == "MODIFIED":
            flash("CRITICAL WARNING: Integrity violation detected! File has been altered since acquisition.", "danger")
        elif evidence.integrity_status == "MISSING":
            flash("ALERT: Evidence file is missing from local storage media!", "danger")
    else:
        flash(message, "danger")

    return redirect(url_for("evidence.view_evidence", evidence_id=evidence_id))

@evidence_bp.route("/evidence/<int:evidence_id>/custody", methods=["GET"])
@login_required
def get_custody_history(evidence_id: int):
    evidence = evidence_service.get_evidence(evidence_id)
    if not evidence:
        abort(404, description="Evidence not found.")
    records = custody_service.get_evidence_custody_history(evidence_id)
    return render_template("evidence/custody.html", evidence=evidence, records=records)

@evidence_bp.route("/evidence/<int:evidence_id>/tamper-demo", methods=["POST"])
@role_required("ADMIN", "INVESTIGATOR")
def tamper_demo(evidence_id: int):
    """
    Demo utility: Safely appends modification bytes to test the SHA-256 verification alert workflow.
    """
    user = get_current_user()
    success, message = evidence_service.tamper_evidence_demo(evidence_id, user.id)
    if success:
        flash(f"DEMO ACTION: {message}", "warning")
    else:
        flash(f"DEMO ERROR: {message}", "danger")
    return redirect(url_for("evidence.view_evidence", evidence_id=evidence_id))
