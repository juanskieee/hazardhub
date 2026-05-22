"""Common helpers and decorators."""

from __future__ import annotations

import functools

from flask import jsonify, redirect, request, session, url_for


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not logged in."}), 401
            return redirect(url_for("pages.login_page"))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not logged in."}), 401
            return redirect(url_for("pages.login_page"))
        if session.get("role") != "Admin":
            if request.path.startswith("/api/"):
                return jsonify({"error": "Admin only."}), 403
            return redirect(url_for("pages.login_page"))
        return f(*args, **kwargs)

    return decorated
