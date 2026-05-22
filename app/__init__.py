"""HazardHub application factory."""

from __future__ import annotations

import os

from flask import Flask, request

from app.config import Config
from app.extensions import init_extensions
from app.services.classifier import init_classifier
from app.routes.pages import pages_bp
from app.routes.auth import auth_bp
from app.routes.hazards import hazards_bp
from app.routes.concerns import concerns_bp
from app.routes.files import files_bp, uploads_bp
from app.routes.fire import fire_bp
from app.routes.admin import admin_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    init_extensions(app)
    init_classifier(app)

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(hazards_bp)
    app.register_blueprint(concerns_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(fire_bp)
    app.register_blueprint(admin_bp)

    @app.after_request
    def add_cors(response):
        origin = request.headers.get("Origin", "")
        allowed = ["http://localhost", "http://127.0.0.1", "null", ""]
        if any(origin.startswith(a) for a in allowed) or origin == "null":
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.route("/api/<path:path>", methods=["OPTIONS"])
    def handle_options(path: str):
        return "", 204

    @app.errorhandler(403)
    def forbidden(e):
        return {"error": "Access denied."}, 403

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found."}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": f"Server error: {str(e)}"}, 500

    return app
