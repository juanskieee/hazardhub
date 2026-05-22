"""Fire protection APIs."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, session

from app.extensions import mysql
from app.utils import login_required

fire_bp = Blueprint("fire", __name__, url_prefix="/api")


@fire_bp.route("/fire-protection/stats", methods=["GET"])
@login_required
def fire_protection_stats():
    try:
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM fire_protection_inspections WHERE inspection_type='fire_extinguisher'"
            )
            ext = cur.fetchone()["cnt"]
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM fire_protection_inspections WHERE inspection_type='emergency_light'"
            )
            em = cur.fetchone()["cnt"]
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM fire_protection_inspections WHERE inspection_type='fire_hose_cabinet'"
            )
            hose = cur.fetchone()["cnt"]
        except Exception:
            try:
                cur.execute("SELECT COUNT(*) AS cnt FROM emergency_lights")
                em = cur.fetchone()["cnt"]
            except Exception:
                em = 0
            ext = hose = 0
        cur.close()
        return (
            jsonify(
                {
                    "success": True,
                    "extinguisher_count": ext,
                    "emergency_light_count": em,
                    "hose_cabinet_count": hose,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fire_bp.route("/fire-protection/inspection", methods=["POST"])
@login_required
def create_fire_inspection():
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json(silent=True) or {}

    inspection_type = (data.get("inspection_type") or "").strip()
    if not inspection_type:
        return jsonify({"success": False, "error": "inspection_type is required."}), 400

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
            INSERT INTO fire_protection_inspections
              (inspection_type, location, extinguisher_type, capacity,
               expiry_date, inspected_by, inspection_date, remark,
               checklist_ok, checklist_ng, photo_filename, user_id, submitted_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                inspection_type,
                (data.get("location") or "").strip(),
                (data.get("extinguisher_type") or "").strip(),
                (data.get("capacity") or "").strip(),
                (data.get("expiry_date") or "").strip(),
                (data.get("inspected_by") or "").strip(),
                (data.get("inspection_date") or "").strip(),
                (data.get("remark") or "").strip(),
                json.dumps(data.get("checklist_ok") or []),
                json.dumps(data.get("checklist_ng") or []),
                photo_filename,
                session.get("user_id"),
                (data.get("submitted_at") or "").strip(),
            ),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "id": new_id}), 201


@fire_bp.route("/fire-protection/inspections", methods=["GET"])
@login_required
def get_fire_inspections():
    t = request.args.get("type", "")
    try:
        cur = mysql.connection.cursor()
        if t:
            cur.execute(
                "SELECT * FROM fire_protection_inspections WHERE inspection_type=%s ORDER BY id DESC",
                (t,),
            )
        else:
            cur.execute("SELECT * FROM fire_protection_inspections ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        return jsonify({"success": True, "inspections": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
