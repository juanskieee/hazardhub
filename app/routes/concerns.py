"""Concern report APIs."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, session

from app.extensions import mysql
from app.services.classifier import classify_priority
from app.utils import login_required

concerns_bp = Blueprint("concerns", __name__, url_prefix="/api")


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


@concerns_bp.route("/concerns", methods=["GET"])
@login_required
def get_concerns():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM concern_reports ORDER BY id DESC LIMIT 100")
        raw_rows = cur.fetchall()
        cur.close()
        results = []
        for r in raw_rows:
            date_val = r.get("report_date") or r.get("date") or str(r.get("created_at", ""))[:10]
            time_val = r.get("report_time") or r.get("time") or ""
            type_val = r.get("report_type") or r.get("concern_type") or "Concern / Suggestion"
            desc_val = r.get("concern_description") or r.get("description") or ""
            loc_val = r.get("incident_location") or r.get("location") or ""
            rep_val = r.get("reported_by") or r.get("submitted_by") or ""
            prio_val = str(r.get("risk_level") or r.get("ai_priority") or "low").strip().capitalize()
            photo_val = r.get("photo_filename") or r.get("hazard_image_path") or ""
            results.append(
                {
                    "id": r.get("id"),
                    "date": str(date_val)[:10] if date_val else "",
                    "time": str(time_val)[:5] if time_val else "",
                    "concern_type": type_val,
                    "description": desc_val,
                    "location": loc_val,
                    "reported_by": rep_val,
                    "ai_priority": prio_val,
                    "nb_confidence": r.get("nb_confidence") or 0.0,
                    "status": r.get("status") or "pending",
                    "photo_filename": photo_val,
                    "created_at": str(r.get("created_at", "")),
                    "admin_remarks": r.get("admin_remarks") or "",
                    "ehs_officer": r.get("ehs_officer") or "",
                    "resolved_at": r["resolved_at"].strftime("%Y-%m-%d %H:%M:%S") if r.get("resolved_at") else None,
                    "duration": _fmt_duration(r.get("created_at"), r.get("resolved_at")),
                }
            )
        return jsonify({"success": True, "concerns": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@concerns_bp.route("/concerns/<int:cid>", methods=["GET"])
@login_required
def get_concern_detail(cid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM concern_reports WHERE id=%s", (cid,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "concern": row}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@concerns_bp.route("/concerns", methods=["POST"])
@login_required
def create_concern():
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json(silent=True) or {}

    report_date = (
        (data.get("date") or data.get("report_date") or "").strip()
        or datetime.now().strftime("%Y-%m-%d")
    )
    report_time = (
        (data.get("time") or data.get("report_time") or "").strip()
        or datetime.now().strftime("%H:%M")
    )
    incoming_report_type = (data.get("report_type") or "").strip()
    concern_category = (data.get("concern_type") or "").strip()
    report_type = incoming_report_type if incoming_report_type in {"Hazard", "Concern/Suggestion"} else "Concern/Suggestion"
    reported_by = (data.get("submitted_by") or data.get("reported_by") or session.get("full_name") or "").strip()
    is_anonymous = 1 if data.get("is_anonymous") else 0
    incident_location = (data.get("location") or data.get("incident_location") or "").strip()
    inspected_by = (data.get("inspected_by") or "").strip()
    hazard_desc = (data.get("hazard_description") or "").strip()
    concern_desc = (data.get("description") or data.get("concern_description") or "").strip()
    suggestion_text = (data.get("suggestion_text") or concern_category).strip()

    if not incoming_report_type and not concern_category:
        return jsonify({"success": False, "error": "report_type / concern_type is required."}), 400

    combined = " ".join(filter(None, [concern_desc, hazard_desc, report_type, concern_category, suggestion_text]))
    risk_level, nb_result = classify_priority(combined)
    nb_confidence = nb_result["confidence"]
    nb_scores_json = json.dumps(nb_result["scores"])

    hazard_image_path = ""
    if "photo" in request.files:
        f = request.files["photo"]
        if f and f.filename:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "jpg"
            hazard_image_path = uuid.uuid4().hex + "." + ext
            f.save(str(Path(current_app.config["UPLOAD_FOLDER"]) / hazard_image_path))

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO concern_reports
              (report_date, report_time, report_type, reported_by,
               is_anonymous, status, incident_location, inspected_by,
               hazard_description, hazard_image_path, risk_level,
               nb_confidence, nb_scores, concern_description, suggestion_text)
            VALUES (%s,%s,%s,%s,%s,'pending',%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                report_date,
                report_time,
                report_type,
                reported_by,
                is_anonymous,
                incident_location,
                inspected_by,
                hazard_desc,
                hazard_image_path,
                risk_level,
                nb_confidence,
                nb_scores_json,
                concern_desc,
                suggestion_text,
            ),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        
        # Create notification for admin when report is submitted
        try:
            notification_msg = f"New {report_type}: {concern_desc[:60] or hazard_desc[:60] or 'Report submitted'}"
            notification_severity = 'high' if risk_level.lower() == 'high' else 'medium' if risk_level.lower() == 'medium' else 'low'
            cur = mysql.connection.cursor()
            cur.execute(
                """INSERT INTO notifications (`date`, severity, message, location, user_id)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    report_date,
                    notification_severity,
                    notification_msg,
                    incident_location,
                    session.get("user_id"),
                ),
            )
            mysql.connection.commit()
            cur.close()
        except Exception as notif_err:
            pass  # Don't fail the main request if notification fails
        
        cur.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "id": new_id, "ai_classification": nb_result}), 201


VALID_STATUSES = {"pending", "resolved", "rejected"}


@concerns_bp.route("/concerns/<int:cid>/status", methods=["PUT"])
@login_required
def update_concern_status(cid):
    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip()
    remarks = (data.get("remarks") or "").strip()
    ehs_officer = (session.get("full_name") or "").strip()
    if status not in VALID_STATUSES:
        return jsonify({"error": "Invalid status"}), 400
    now = datetime.now()
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT status, created_at, resolved_at FROM concern_reports WHERE id=%s", (cid,))
        row = cur.fetchone()
        existing_status = (row["status"] if row else None) or "pending"
        created_at = row["created_at"] if row else None
        existing_resolved = row["resolved_at"] if row else None

        # Lock: once resolved or rejected, no further edits allowed.
        if (existing_status or "").lower() == "resolved" or existing_resolved is not None:
            return jsonify({"error": "Status already resolved and cannot be edited."}), 400
        if (existing_status or "").lower() == "rejected":
            return jsonify({"error": "Status already rejected and cannot be edited."}), 400


        if status == "resolved" and not existing_resolved:
            resolved_at = now
        elif status != "resolved":
            resolved_at = None
        else:
            resolved_at = existing_resolved

        cur.execute(
            "UPDATE concern_reports SET status=%s, admin_remarks=%s, ehs_officer=%s, resolved_at=%s WHERE id=%s",
            (status, remarks or None, ehs_officer or None, resolved_at, cid),
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
