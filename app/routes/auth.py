"""Authentication and profile APIs."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import mysql
from app.utils import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


@auth_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("email") or data.get("username") or "").strip()
    password = data.get("password") or ""
    role_filter = (data.get("role") or "").strip()
    if not identifier or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400
    try:
        cur = mysql.connection.cursor()
        if role_filter:
            cur.execute(
                "SELECT * FROM users WHERE LOWER(email)=%s AND role=%s",
                (identifier.lower(), role_filter),
            )
        else:
            cur.execute("SELECT * FROM users WHERE LOWER(email)=%s", (identifier.lower(),))
        user = cur.fetchone()
        cur.close()
    except Exception as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500
    if not user or not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"success": False, "error": "Invalid credentials or role."}), 401
    session.permanent = True
    session["user_id"] = user["id"]
    session["email"] = user["email"]
    session["role"] = user["role"]
    session["full_name"] = user.get("full_name", "")
    redirect_url = "/dashboard" if user["role"] == "Admin" else "/employee-dashboard"
    return (
        jsonify(
            {
                "success": True,
                "message": "Login successful.",
                "redirect_url": redirect_url,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "role": user["role"],
                    "full_name": user.get("full_name", ""),
                    "position": user.get("position", ""),
                    "id_number": user.get("id_number", ""),
                },
            }
        ),
        200,
    )


@auth_bp.route("/logout", methods=["POST", "GET"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out."}), 200


@auth_bp.route("/logout-redirect")
def logout_redirect():
    session.clear()
    return redirect(url_for("pages.login_page"))


@auth_bp.route("/me")
@auth_bp.route("/current-user")
@login_required
def api_me():
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT id, email, role, full_name, position, id_number,
                   age, sex, civil_status, employment_status,
                   supervisor_name, supervisor_position
            FROM users WHERE id=%s
            """,
            (session.get("user_id"),),
        )
        user = cur.fetchone()
        cur.close()
    except Exception:
        user = None
    base = {
        "id": session.get("user_id"),
        "email": session.get("email"),
        "role": session.get("role"),
        "full_name": session.get("full_name"),
    }
    if user:
        base.update({k: user[k] for k in user if user[k] is not None})
    return jsonify({"success": True, "user": base}), 200


@auth_bp.route("/profile", methods=["GET"])
@login_required
def get_my_profile():
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT id, full_name, email, role, position, id_number,
                   age, sex, civil_status, employment_status,
                   supervisor_name, supervisor_position,
                   profile_complete, profile_updated_at, created_at
            FROM users WHERE id = %s
            """,
            (session["user_id"],),
        )
        row = cur.fetchone()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if not row:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"success": True, "profile": row}), 200


@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_my_profile():
    data = request.get_json(silent=True) or {}

    valid_enums = {
        "sex": {"Male", "Female", "Other"},
        "civil_status": {"Single", "Married", "Widowed", "Separated", "Divorced"},
        "employment_status": {"Regular", "Probationary", "Contractual", "Part-time", "OJT"},
    }
    for field, valid in valid_enums.items():
        val = data.get(field)
        if val is not None and val not in valid:
            return jsonify({"error": f"Invalid value for {field}: '{val}'"}), 400

    age = data.get("age")
    if age is not None:
        try:
            age = int(age)
            if not (15 <= age <= 100):
                return jsonify({"error": "Age must be between 15 and 100."}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Age must be a number."}), 400

    sex = data.get("sex") or None
    civil_status = data.get("civil_status") or None
    employment_status = data.get("employment_status") or None
    supervisor_name = (data.get("supervisor_name") or "").strip() or None
    supervisor_position = (data.get("supervisor_position") or "").strip() or None

    if all(
        v is None
        for v in [age, sex, civil_status, employment_status, supervisor_name, supervisor_position]
    ):
        return jsonify({"error": "No fields provided."}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            UPDATE users SET
                age                 = COALESCE(%s, age),
                sex                 = COALESCE(%s, sex),
                civil_status        = COALESCE(%s, civil_status),
                employment_status   = COALESCE(%s, employment_status),
                supervisor_name     = COALESCE(%s, supervisor_name),
                supervisor_position = COALESCE(%s, supervisor_position),
                profile_complete    = 1,
                profile_updated_at  = %s
            WHERE id = %s
            """,
            (
                age,
                sex,
                civil_status,
                employment_status,
                supervisor_name,
                supervisor_position,
                datetime.now(),
                session["user_id"],
            ),
        )
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"success": True, "message": "Profile updated successfully."}), 200
