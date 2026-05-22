"""Certificate folder/file APIs and upload serving."""

from __future__ import annotations

import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_from_directory, session

from app.extensions import mysql
from app.utils import login_required

files_bp = Blueprint("files", __name__, url_prefix="/api")
uploads_bp = Blueprint("uploads", __name__)


@files_bp.route("/folders", methods=["GET"])
@login_required
def get_folders():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, emoji, created_at FROM cert_folders ORDER BY id")
    folders = cur.fetchall()
    for folder in folders:
        cur.execute("SELECT COUNT(*) AS cnt FROM cert_files WHERE folder_id=%s", (folder["id"],))
        folder["file_count"] = cur.fetchone()["cnt"]
    cur.close()
    return jsonify(folders), 200


@files_bp.route("/folders", methods=["POST"])
@login_required
def create_folder():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    emoji = (data.get("emoji") or "📁").strip()
    if not name:
        return jsonify({"error": "Folder name is required."}), 400
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO cert_folders (name, emoji, created_by) VALUES (%s,%s,%s)",
            (name, emoji, session.get("user_id")),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"id": new_id, "name": name, "emoji": emoji, "file_count": 0}), 201


@files_bp.route("/folders/<int:fid>", methods=["PUT"])
@login_required
def rename_folder(fid):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    emoji = (data.get("emoji") or "").strip()
    if not name:
        return jsonify({"error": "Name required."}), 400
    try:
        cur = mysql.connection.cursor()
        if emoji:
            cur.execute("UPDATE cert_folders SET name=%s, emoji=%s WHERE id=%s", (name, emoji, fid))
        else:
            cur.execute("UPDATE cert_folders SET name=%s WHERE id=%s", (name, fid))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Folder renamed."}), 200


@files_bp.route("/folders/<int:fid>", methods=["DELETE"])
@login_required
def delete_folder(fid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT filename FROM cert_files WHERE folder_id=%s", (fid,))
        for row in cur.fetchall():
            p = os.path.join(current_app.config["UPLOAD_FOLDER"], row["filename"])
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except OSError:
                pass
        cur.execute("DELETE FROM cert_folders WHERE id=%s", (fid,))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Folder deleted."}), 200


@files_bp.route("/folders/<int:fid>/files", methods=["GET"])
@login_required
def get_files(fid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM cert_folders WHERE id=%s", (fid,))
    if not cur.fetchone():
        cur.close()
        return jsonify({"error": "Folder not found."}), 404
    cur.execute(
        "SELECT id, original_name, file_size, mime_type, filename, uploaded_at FROM cert_files WHERE folder_id=%s ORDER BY id",
        (fid,),
    )
    rows = cur.fetchall()
    cur.close()
    return jsonify(rows), 200


@files_bp.route("/folders/<int:fid>/files", methods=["POST"])
@login_required
def upload_file(fid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM cert_folders WHERE id=%s", (fid,))
    if not cur.fetchone():
        cur.close()
        return jsonify({"error": "Folder not found."}), 404
    if "file" not in request.files:
        cur.close()
        return jsonify({"error": "No file provided."}), 400
    file = request.files["file"]
    if not file.filename:
        cur.close()
        return jsonify({"error": "Empty filename."}), 400
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    saved_name = (uuid.uuid4().hex + "." + ext) if ext else uuid.uuid4().hex
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_name)
    file.save(save_path)
    size_bytes = os.path.getsize(save_path)
    size_kb = size_bytes / 1024
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
    try:
        cur.execute(
            "INSERT INTO cert_files (folder_id, filename, original_name, file_size, mime_type) VALUES (%s,%s,%s,%s,%s)",
            (fid, saved_name, file.filename, size_str, file.content_type or ""),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
    except Exception as e:
        try:
            os.remove(save_path)
        except OSError:
            pass
        return jsonify({"error": str(e)}), 500
    return (
        jsonify(
            {
                "id": new_id,
                "filename": saved_name,
                "original_name": file.filename,
                "file_size": size_str,
                "mime_type": file.content_type or "",
            }
        ),
        201,
    )


@files_bp.route("/files/<int:file_id>", methods=["DELETE"])
@login_required
def delete_file(file_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT filename FROM cert_files WHERE id=%s", (file_id,))
        row = cur.fetchone()
        if row:
            p = os.path.join(current_app.config["UPLOAD_FOLDER"], row["filename"])
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except OSError:
                pass
            cur.execute("DELETE FROM cert_files WHERE id=%s", (file_id,))
            mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "File deleted."}), 200


@uploads_bp.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
