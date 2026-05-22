"""Admin and system APIs."""

from __future__ import annotations

import json

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash

from app.extensions import mysql
from app.services.classifier import (
    NaiveBayesClassifier,
    classify_priority,
    load_custom_training_data,
    nb_classifier,
    save_custom_training_data,
)
from app.utils import admin_required, login_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api")


@admin_bp.route("/dashboard/stats")
@login_required
def dashboard_stats():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM hazard_reports")
        h = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM concern_reports")
        c = cur.fetchone()["cnt"]
        total = h + c
        cur.execute("SELECT COUNT(*) AS cnt FROM hazard_reports WHERE status='resolved'")
        rh = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM concern_reports WHERE status='resolved'")
        rc = cur.fetchone()["cnt"]
        resolved = rh + rc
        cur.close()
        return (
            jsonify(
                {
                    "success": True,
                    "stats": {
                        "total_incidents": total,
                        "hazards_identified": h,
                        "resolved_incidents": resolved,
                        "pending_incidents": max(0, total - resolved),
                    },
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/notifications", methods=["GET"])
@login_required
def get_notifications():
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT id, `date`, severity, message, location, is_read FROM notifications ORDER BY id DESC LIMIT 20"
        )
        rows = cur.fetchall()
        cur.close()
        return jsonify({"success": True, "notifications": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/accounts", methods=["GET"])
@admin_required
def get_accounts():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, full_name, email, role, position, id_number, created_at FROM users ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/accounts", methods=["POST"])
@admin_required
def create_account():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "Employee").strip()
    position = (data.get("position") or "").strip()
    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash, role, position) VALUES (%s,%s,%s,%s,%s)",
            (name, email, generate_password_hash(password), role, position),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        id_number = f"{'ADMIN' if role=='Admin' else 'EMP'}-{str(new_id).zfill(5)}"
        cur.execute("UPDATE users SET id_number=%s WHERE id=%s", (id_number, new_id))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Account created.", "id": new_id}), 201


@admin_bp.route("/accounts/<int:uid>", methods=["PUT"])
@admin_required
def update_account(uid):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "Employee").strip()
    position = (data.get("position") or "").strip()
    id_number = f"{'ADMIN' if role=='Admin' else 'EMP'}-{str(uid).zfill(5)}"
    try:
        cur = mysql.connection.cursor()
        if password:
            cur.execute(
                "UPDATE users SET full_name=%s, email=%s, password_hash=%s, role=%s, position=%s, id_number=%s WHERE id=%s",
                (name, email, generate_password_hash(password), role, position, id_number, uid),
            )
        else:
            cur.execute(
                "UPDATE users SET full_name=%s, email=%s, role=%s, position=%s, id_number=%s WHERE id=%s",
                (name, email, role, position, id_number, uid),
            )
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Account updated."}), 200


@admin_bp.route("/accounts/<int:uid>", methods=["DELETE"])
@admin_required
def delete_account(uid):
    if uid == session.get("user_id"):
        return jsonify({"error": "Cannot delete your own account."}), 400
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM users WHERE id=%s", (uid,))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Account deleted."}), 200


@admin_bp.route("/employees/search", methods=["GET"])
@login_required
def search_employees():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([]), 200
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT full_name, position, id_number,
                   age, sex, civil_status, employment_status,
                   supervisor_name, supervisor_position
            FROM users
            WHERE full_name LIKE %s AND is_active = 1
            ORDER BY full_name
            LIMIT 10
            """,
            (f"%{q}%",),
        )
        results = cur.fetchall()
        cur.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/system-info", methods=["GET"])
@login_required
def system_info():
    custom = load_custom_training_data()
    test = nb_classifier.predict("fire explosion chemical danger critical")
    return (
        jsonify(
            {
                "success": True,
                "nb_status": "OK",
                "vocab_size": len(nb_classifier.vocabulary),
                "builtin_count": len(NaiveBayesClassifier.TRAINING_DATA),
                "custom_count": len(custom),
                "total_samples": len(NaiveBayesClassifier.TRAINING_DATA) + len(custom),
                "algorithm": "Naive Bayes (Multinomial, Laplace smoothing)",
                "test_classification": test["priority"],
                "test_confidence": test["confidence"],
            }
        ),
        200,
    )


@admin_bp.route("/nb-training-data", methods=["GET"])
@login_required
def get_nb_training_data():
    custom = load_custom_training_data()
    builtin = [
        {"id": i, "text": text, "priority": priority, "source": "built-in"}
        for i, (text, priority) in enumerate(NaiveBayesClassifier.TRAINING_DATA)
    ]
    custom_merged = [
        {"id": len(builtin) + i, "text": item["text"], "priority": item["priority"], "source": "custom"}
        for i, item in enumerate(custom)
    ]
    return (
        jsonify(
            {
                "success": True,
                "builtin": builtin,
                "custom": custom_merged,
                "counts": {
                    "built_in": len(builtin),
                    "custom": len(custom_merged),
                    "total": len(builtin) + len(custom_merged),
                },
            }
        ),
        200,
    )


@admin_bp.route("/nb-training-data", methods=["POST"])
@admin_required
def add_nb_training_data():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    priority = (data.get("priority") or "").strip()
    if not text or not priority:
        return jsonify({"success": False, "error": "text and priority are required."}), 400
    if priority not in NaiveBayesClassifier.CLASSES:
        return (
            jsonify({"success": False, "error": f"priority must be one of {NaiveBayesClassifier.CLASSES}."}),
            400,
        )
    custom = load_custom_training_data()
    custom.append({"text": text, "priority": priority})
    save_custom_training_data(custom)
    nb_classifier.custom_training_data = custom
    return jsonify({"success": True, "message": "Training example added.", "custom_count": len(custom)}), 201


@admin_bp.route("/nb-training-data", methods=["DELETE"])
@admin_required
def remove_nb_training_data():
    data = request.get_json(silent=True) or {}
    index = data.get("index")
    if index is None:
        return jsonify({"success": False, "error": "index is required."}), 400
    try:
        index = int(index)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "index must be an integer."}), 400
    custom = load_custom_training_data()
    if index not in range(-len(custom), len(custom)):
        return jsonify({"success": False, "error": "index out of range."}), 404
    removed = custom.pop(index)
    save_custom_training_data(custom)
    nb_classifier.custom_training_data = custom
    return jsonify({"success": True, "message": "Removed.", "removed": removed}), 200


@admin_bp.route("/nb-training-data/custom/<int:index>", methods=["DELETE"])
@admin_required
def remove_nb_training_data_by_url(index):
    custom = load_custom_training_data()
    if index not in range(-len(custom), len(custom)):
        return jsonify({"success": False, "error": "index out of range."}), 404
    removed = custom.pop(index)
    save_custom_training_data(custom)
    nb_classifier.custom_training_data = custom
    return jsonify({"success": True, "message": "Removed.", "removed": removed}), 200


@admin_bp.route("/nb-classify", methods=["POST"])
@login_required
def api_nb_classify():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"success": False, "error": "text is required"}), 400
    result = nb_classifier.predict(text)
    return (
        jsonify(
            {
                "success": True,
                "priority": result["priority"],
                "confidence": result["confidence"],
                "scores": result["scores"],
            }
        ),
        200,
    )


@admin_bp.route("/classify", methods=["POST"])
@login_required
def api_classify():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    hazard_type = (data.get("hazard_type") or "").strip()
    risk_level = (data.get("risk_level") or "").strip()
    if not text and not hazard_type:
        return jsonify({"error": "text is required"}), 400
    _, result = classify_priority(text, hazard_type, risk_level)
    return jsonify({"success": True, "classification": result}), 200
