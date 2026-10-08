import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request, g, session
from flask_wtf.csrf import CSRFProtect

from config import Config
from database.db import close_db, init_db
from routes.auth_middleware import get_current_user
from routes import auth_bp, case_bp, evidence_bp, log_bp, timeline_bp, report_bp

csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CSRF protection
    csrf.init_app(app)

    # Register teardown
    app.teardown_appcontext(close_db)

    # Context processor to inject current logged in user into all Jinja templates
    @app.context_processor
    def inject_user():
        return {
            "current_user": get_current_user()
        }

    # Error handlers (Central Flask error handling as specified in Blueprint Section 26)
    @app.errorhandler(400)
    def bad_request_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Bad Request", "message": str(e.description)}), 400
        return render_template("errors/400.html", error=e), 400

    @app.errorhandler(401)
    def unauthorized_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Unauthorized", "message": "Authentication required."}), 401
        return render_template("errors/401.html", error=e), 401

    @app.errorhandler(403)
    def forbidden_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Forbidden", "message": "You do not have permission to perform this action."}), 403
        return render_template("errors/403.html", error=e), 403

    @app.errorhandler(404)
    def not_found_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Not Found", "message": str(e.description)}), 404
        return render_template("errors/404.html", error=e), 404

    @app.errorhandler(409)
    def conflict_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Conflict", "message": str(e.description)}), 409
        return render_template("errors/409.html", error=e), 409

    @app.errorhandler(413)
    def request_entity_too_large_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Payload Too Large", "message": "Uploaded file exceeds the maximum permitted size (16MB)."}), 413
        return render_template("errors/413.html", error=e), 413

    @app.errorhandler(415)
    def unsupported_media_type_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Unsupported Media Type", "message": "File format not supported."}), 415
        return render_template("errors/415.html", error=e), 415

    @app.errorhandler(422)
    def unprocessable_entity_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Unprocessable Entity", "message": str(e.description)}), 422
        return render_template("errors/422.html", error=e), 422

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Internal Server Error", "message": "An unexpected server error occurred."}), 500
        return render_template("errors/500.html", error=e), 500

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(case_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(report_bp)

    # Ensure database tables exist
    db_path = app.config.get("DATABASE_PATH")
    if db_path and db_path != ":memory:" and not os.path.exists(db_path):
        with app.app_context():
            init_db(db_path)

    # Ensure runtime directories exist
    os.makedirs(app.config.get("EVIDENCE_STORE_PATH", "evidence-store"), exist_ok=True)
    os.makedirs(app.config.get("REPORTS_PATH", "reports"), exist_ok=True)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
