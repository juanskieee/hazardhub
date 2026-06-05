"""Hazard report APIs."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, session

from app.extensions import mysql
from app.services.classifier import classify_priority
from app.utils import login_required

hazards_bp = Blueprint("hazards", __name__, url_prefix="/api")


def _fmt_duration(created_at, resolved_at):
    if not resolved_at or not created_at:
        return None
    try:
        diff = resolved_at - created_at
        total_min = int(diff.total_seconds() // 60)
        if total_min < 0:
            return None
        days, rem = divmod(total_min, 1440)
        hrs, mins = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hrs:
            parts.append(f"{hrs}h")
        parts.append(f"{mins}m")
        return " ".join(parts)
    except Exception:
        return None


@hazards_bp.route("/hazards", methods=["GET"])
@login_required
def get_hazards():
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT id, `date`, `time`, location, reported_by,
                   main_hazard_type AS hazard_type, hazard_categories, hazard_details,
                   description, ai_priority, nb_confidence, status, photo_filename,
                   created_at, admin_remarks, ehs_officer, resolved_at
            FROM hazard_reports ORDER BY id DESC LIMIT 100
            """
        )
        rows = cur.fetchall()
        cur.close()
        result = []
        for r in rows:
            r = dict(r)
            r["duration"] = _fmt_duration(r.get("created_at"), r.get("resolved_at"))
            r["resolved_at"] = (
                r["resolved_at"].strftime("%Y-%m-%d %H:%M:%S")
                if r.get("resolved_at")
                else None
            )
            r["created_at"] = str(r["created_at"]) if r.get("created_at") else None
            result.append(r)
        return jsonify({"success": True, "hazards": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@hazards_bp.route("/hazards/<int:hid>", methods=["GET"])
@login_required
def get_hazard_detail(hid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM hazard_reports WHERE id=%s", (hid,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "hazard": row}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@hazards_bp.route("/hazards", methods=["POST"])
@login_required
def create_hazard():
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json(silent=True) or {}

    report_date = (
        (data.get("date") or data.get("report_date") or "").strip()
        or datetime.now().strftime("%Y-%m-%d")
    )
    time_val = (
        (data.get("time") or data.get("report_time") or "").strip()
        or datetime.now().strftime("%H:%M")
    )
    location = (data.get("location") or "").strip()
    reported_by = (data.get("reported_by") or session.get("full_name") or "").strip()
    main_hazard_type = (data.get("main_hazard_type") or "").strip()
    hazard_categories = (data.get("hazard_categories") or "").strip()
    hazard_details = (data.get("hazard_details") or "").strip()
    description = (data.get("description") or "").strip()
    risk_level = (data.get("risk_level") or "").strip()

    combined = " ".join(
        filter(
            None,
            [description, main_hazard_type, hazard_categories, hazard_details, risk_level],
        )
    )
    ai_priority, nb_result = classify_priority(combined)
    nb_confidence = nb_result["confidence"]
    nb_scores_json = json.dumps(nb_result["scores"])

    photo_filename = ""
    if "photo" in request.files:
        f = request.files["photo"]
        if f and f.filename:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "jpg"
            photo_filename = uuid.uuid4().hex + "." + ext
            f.save(str(Path(current_app.config["UPLOAD_FOLDER"]) / photo_filename))

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO hazard_reports
              (`date`, `time`, location, reported_by, main_hazard_type,
               hazard_categories, hazard_details, description,
               risk_level, ai_priority, nb_confidence, nb_scores,
               status, photo_filename, submitted_by_user)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s)
            """,
            (
                report_date,
                time_val,
                location,
                reported_by,
                main_hazard_type,
                hazard_categories,
                hazard_details,
                description,
                risk_level or ai_priority,
                ai_priority,
                nb_confidence,
                nb_scores_json,
                photo_filename,
                session.get("user_id"),
            ),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        
        # Create notification for admin when hazard is reported
        try:
            notification_severity = 'high' if ai_priority == 'High' else 'medium' if ai_priority == 'Medium' else 'low'
            notification_msg = f"New Hazard Report: {main_hazard_type or description[:60]}"
            cur.execute(
                """INSERT INTO notifications (`date`, severity, message, location, user_id)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    report_date,
                    notification_severity,
                    notification_msg,
                    location,
                    session.get("user_id"),
                ),
            )
            mysql.connection.commit()
        except Exception as notif_err:
            pass  # Don't fail the main request if notification fails
        cur.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "id": new_id, "ai_classification": nb_result}), 201


VALID_STATUSES = {"pending", "resolved", "rejected"}


@hazards_bp.route("/hazards/<int:hid>/status", methods=["PUT"])
@login_required
def update_hazard_status(hid):
    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip()
    remarks = (data.get("remarks") or "").strip()
    ehs_officer = session.get("full_name") or ""
    if status not in VALID_STATUSES:
        return jsonify({"error": "Invalid status"}), 400
    now = datetime.now()
    resolved_at = now if status == "resolved" else None
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT created_at, resolved_at FROM hazard_reports WHERE id=%s", (hid,))
        row = cur.fetchone()
        created_at = row["created_at"] if row else None
        existing_resolved = row["resolved_at"] if row else None
        if status == "resolved" and not existing_resolved:
            resolved_at = now
        elif status != "resolved":
            resolved_at = None
        else:
            resolved_at = existing_resolved
        cur.execute(
            "UPDATE hazard_reports SET status=%s, admin_remarks=%s, ehs_officer=%s, resolved_at=%s WHERE id=%s",
            (status, remarks or None, ehs_officer or None, resolved_at, hid),
        )
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    duration_str = None
    if resolved_at and created_at:
        duration_str = _fmt_duration(created_at, resolved_at)

    return (
        jsonify(
            {
                "success": True,
                "ehs_officer": ehs_officer,
                "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else None,
                "duration": duration_str,
            }
        ),
        200,
    )
