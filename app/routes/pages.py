"""Page routes."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, redirect, render_template, session, url_for

from app.extensions import mysql
from app.services.classifier import NaiveBayesClassifier, nb_classifier

from app.utils import login_required

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(
            url_for("pages.admin_dashboard")
            if session.get("role") == "Admin"
            else url_for("pages.employee_dashboard")
        )
    return redirect(url_for("pages.login_page"))


@pages_bp.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("pages.index"))
    return render_template("login.html")


@pages_bp.route("/dashboard")
@login_required
def admin_dashboard():
    if session.get("role") != "Admin":
        return redirect(url_for("pages.login_page"))
    return render_template("admin_dashboard.html")


@pages_bp.route("/employee-dashboard")
@login_required
def employee_dashboard():
    return "<h2>Welcome, Employee!</h2>"


@pages_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("pages.login_page"))


@pages_bp.route("/check")
def check():
    db_ok = False
    db_msg = ""
    user_count = folder_count = hazard_count = concern_count = fire_count = 0
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        user_count = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM cert_folders")
        folder_count = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM hazard_reports")
        hazard_count = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM concern_reports")
        concern_count = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM emergency_lights")
        fire_count = cur.fetchone()["cnt"]
        cur.close()
        db_ok = True
        db_msg = "OK"
    except Exception as e:
        db_msg = f"Error: {e}"

    test = nb_classifier.predict("fire explosion chemical danger critical")
    nb_status = (
        f"OK {test['priority']} ({test['confidence']*100:.1f}%) "
        f"- vocab={len(nb_classifier.vocabulary)} words"
    )

    logged_in = "user_id" in session
    return (
        "<!DOCTYPE html><html><head><title>Diagnostics</title>"
        "<style>body{font-family:sans-serif;padding:40px;background:#f9f9f9;}"
        "h1{color:#E3AB00;} .ok{color:green;} .fail{color:red;}"
        "table{border-collapse:collapse;width:100%;max-width:680px;margin-top:16px;}"
        "td,th{border:1px solid #ddd;padding:10px 16px;}"
        "th{background:#E3AB00;color:#2a1f00;}</style></head>"
        "<body><h1>Hazard Hub - Diagnostics</h1>"
        "<table>"
        "<tr><th>Check</th><th>Result</th></tr>"
        f"<tr><td>MySQL</td><td class='{('ok' if db_ok else 'fail')}'>{db_msg}</td></tr>"
        f"<tr><td>Naive Bayes Classifier</td><td class='ok'>{nb_status}</td></tr>"
        f"<tr><td>Training Samples</td><td>{len(NaiveBayesClassifier.TRAINING_DATA)} (High/Medium/Low)</td></tr>"
        f"<tr><td>Employee Accounts</td><td>{user_count}</td></tr>"
        f"<tr><td>Cert Folders</td><td>{folder_count}</td></tr>"
        f"<tr><td>Hazard Reports</td><td>{hazard_count}</td></tr>"
        f"<tr><td>Concern Reports</td><td>{concern_count}</td></tr>"
        f"<tr><td>Emergency Lights</td><td>{fire_count}</td></tr>"
        f"<tr><td>Session</td><td class='{('ok' if logged_in else 'fail')}'>"
        + (
            "Logged in as " + str(session.get("email")) + " (" + str(session.get("role")) + ")"
            if logged_in
            else "Not logged in"
        )
        + "</td></tr>"
        "</table><br>"
        "<a href='/login' style='background:#E3AB00;color:#2a1f00;padding:10px 28px;border-radius:8px;text-decoration:none;font-weight:bold;'>Login -></a>"
        "<a href='/dashboard' style='background:#2a1f00;color:#E3AB00;padding:10px 28px;border-radius:8px;text-decoration:none;font-weight:bold;margin-left:10px;'>Dashboard -></a>"
        "</body></html>",
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


@pages_bp.route("/mobile")
@pages_bp.route("/mobi")
def mobile_app():
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "mobile" / "mobile_hazardhub.html",
        root / "mobile" / "mobile.html",
        root / "mobile_hazardhub.html",
        root / "mobile.html",
    ]
    for path in candidates:
        if path.is_file():
            return path.read_text(encoding="utf-8"), 200, {
                "Content-Type": "text/html; charset=utf-8"
            }
    return "mobile_hazardhub.html not found", 404
