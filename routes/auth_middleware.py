from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, jsonify, g
from services.auth_service import AuthService
from models.user import User

def get_current_user() -> User | None:
    if "user" in g:
        return g.user
    user_id = session.get("user_id")
    if not user_id:
        return None
    auth_service = AuthService()
    user = auth_service.get_user_by_id(user_id)
    g.user = user
    return user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized", "message": "Authentication required."}), 401
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if user is None:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Unauthorized", "message": "Authentication required."}), 401
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login", next=request.url))
            
            if user.role not in allowed_roles:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Forbidden", "message": f"Role '{user.role}' not permitted for this action."}), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
