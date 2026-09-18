from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from services.auth_service import AuthService
from routes.auth_middleware import login_required, role_required, get_current_user

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()

@auth_bp.route("/login", methods=["GET", "POST"])
@auth_bp.route("/auth/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("cases.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = auth_service.authenticate(username, password)
        if user:
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            flash(f"Welcome back, {user.username}! Signed in with {user.role} privileges.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("cases.dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/logout", methods=["GET", "POST"])
@auth_bp.route("/auth/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/admin/users", methods=["GET", "POST"])
@role_required("ADMIN")
def manage_users():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "INVESTIGATOR")

        success, message, _ = auth_service.register_user(username, password, role)
        if success:
            flash(f"User '{username}' ({role}) created successfully.", "success")
            return redirect(url_for("auth.manage_users"))
        else:
            flash(message, "danger")

    users = auth_service.list_users()
    return render_template("admin/users.html", users=users)
