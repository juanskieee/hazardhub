"""
Hazard Hub – Flask Backend
Naive Bayes classifier for AI priority classification.
Run: python app.py
Requires: pip install flask flask-mysqldb werkzeug
"""

from flask import (
    Flask, request, jsonify, redirect, url_for,
    session, abort, send_from_directory
)
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os, uuid, functools, json, math, re
from datetime import datetime
from collections import defaultdict

# ─────────────────────────────────────────────
#  App + Config
# ─────────────────────────────────────────────

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
TRAINING_DATA_FILE = os.path.join(BASE_DIR, "training_data.json")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static")
app.secret_key = "hazardhub-stable-secret-key-2024"

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_COOKIE_SAMESITE"]    = "Lax"
app.config["SESSION_COOKIE_SECURE"]      = False
app.config["SESSION_COOKIE_HTTPONLY"]    = True

# ── Separate session interface for mobile clients ──────────────────────────
# Mobile uses its own cookie ("hazardhub_mobile") so that an employee
# logging in on mobile never overwrites the admin's PC session cookie,
# and vice versa.  All mobile API calls send the header X-Client: mobile
# which switches Flask to read/write the mobile cookie instead.

from flask.sessions import SecureCookieSessionInterface

class MobileSessionInterface(SecureCookieSessionInterface):
    """Session interface that uses a different cookie name for mobile clients."""
    def get_cookie_name(self, app):
        if request.headers.get("X-Client") == "mobile":
            return "hazardhub_mobile"
        return app.config.get("SESSION_COOKIE_NAME", "session")

app.session_interface = MobileSessionInterface()

app.config["MYSQL_HOST"]         = "localhost"
app.config["MYSQL_USER"]         = "root"
app.config["MYSQL_PASSWORD"]     = ""
app.config["MYSQL_DB"]           = "hazardhub"
app.config["MYSQL_CURSORCLASS"]  = "DictCursor"
app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024   # 100 MB
app.config["MYSQL_CHARSET"]      = "utf8mb4"

mysql = MySQL(app)


# ═══════════════════════════════════════════════════════════════════
#  NAIVE BAYES CLASSIFIER
#  Multinomial Naive Bayes with Laplace (add-1) smoothing.
#  Classes: High | Medium | Low
# ═══════════════════════════════════════════════════════════════════

class NaiveBayesClassifier:

    CLASSES = ["High", "Medium", "Low"]

    # ── Labeled training corpus ──────────────────────────────────
    TRAINING_DATA = [
        # ── HIGH ─────────────────────────────────────────────────
        ("fire explosion flammable chemical hazard emergency danger critical",        "High"),
        ("electrical fire exposed wire short circuit spark ignition",                 "High"),
        ("toxic chemical spill gas leak dangerous fume exposure fatal",               "High"),
        ("worker injured accident fatal injury hospitalization ambulance",            "High"),
        ("radiation exposure nuclear hazardous material contamination",               "High"),
        ("building collapse structure failure emergency evacuation",                  "High"),
        ("explosion risk gas leak pressure vessel rupture boiler",                    "High"),
        ("severe injury broken bone fracture amputation critical condition",          "High"),
        ("electrical shock electrocution live wire unprotected circuit",              "High"),
        ("chemical burn acid alkaline corrosive exposure skin eye",                   "High"),
        ("fire in warehouse storage area flammable material ignited",                 "High"),
        ("emergency evacuation required immediate danger life threatening",           "High"),
        ("oxygen deficient confined space asphyxiation fatal risk",                  "High"),
        ("heavy machine caught between crushing injury entanglement",                 "High"),
        ("fall from height scaffold ladder roof serious injury",                      "High"),
        ("electrical panel overloaded circuit breaker fire risk immediate",           "High"),
        ("toxic gas hydrogen sulfide ammonia chlorine release worker exposed",        "High"),
        ("uncontrolled chemical reaction hazardous runaway exothermic",               "High"),
        ("forklift accident collision pedestrian serious injury emergency",           "High"),
        ("lockout tagout failure energy release unexpected start injury",             "High"),
        ("pressurized tank rupture explosion risk immediate shutdown required",       "High"),
        ("worker trapped pinned under heavy object critical rescue needed",           "High"),
        ("acid spill large area contamination chemical emergency response",           "High"),
        ("scaffold collapse multiple workers danger critical structural failure",     "High"),
        ("gas cylinder leaking flammable explosive atmosphere ignition source",       "High"),

        # ── MEDIUM ───────────────────────────────────────────────
        ("slip trip wet floor puddle water walkway uneven surface",                   "Medium"),
        ("broken equipment machinery malfunction not working needs repair",           "Medium"),
        ("ergonomic issue lifting heavy loads awkward posture strain",                "Medium"),
        ("spill minor leak needs cleanup contained area",                             "Medium"),
        ("noise excessive loud machinery hearing protection required",                "Medium"),
        ("poor housekeeping cluttered workstation blocked aisle",                     "Medium"),
        ("missing safety sign warning label faded unclear",                           "Medium"),
        ("vibration hand arm whole body exposure repetitive",                         "Medium"),
        ("heat stress high temperature dehydration rest area needed",                 "Medium"),
        ("biological contamination mold bacteria pest infestation",                   "Medium"),
        ("tripping hazard cables exposed cord floor pathway obstruction",             "Medium"),
        ("worn protective equipment PPE defective needs replacement",                 "Medium"),
        ("poor lighting inadequate visibility dark area working",                     "Medium"),
        ("manual handling injury back pain musculoskeletal disorder",                 "Medium"),
        ("unsafe scaffold incomplete missing guardrail handrail",                     "Medium"),
        ("blocked emergency exit fire door not closing properly",                     "Medium"),
        ("dust accumulation respiratory hazard ventilation inadequate",               "Medium"),
        ("missing fire extinguisher not inspected overdue expired",                   "Medium"),
        ("near miss incident no injury narrow escape recorded",                       "Medium"),
        ("equipment guard missing machine guarding removed bypassed",                 "Medium"),
        ("chemical storage improper flammable material not labeled",                  "Medium"),
        ("forklift speeding pedestrian pathway shared area unsafe",                   "Medium"),
        ("electrical cord frayed damaged insulation minor repair required",           "Medium"),
        ("slip hazard oil grease floor needs anti-slip treatment",                    "Medium"),
        ("broken step stair railing loose damaged walkway hazard",                    "Medium"),

        # ── LOW ──────────────────────────────────────────────────
        ("suggestion improvement workflow process efficiency productivity",            "Low"),
        ("minor cleanliness issue trash not collected cleaning needed",               "Low"),
        ("small scratch dent minor damage cosmetic no safety risk",                   "Low"),
        ("idea feedback recommendation better practice workplace",                    "Low"),
        ("general concern comment feedback observation non-urgent",                   "Low"),
        ("maintenance request routine scheduled preventive upkeep",                   "Low"),
        ("broken chair desk lamp minor office furniture needs fixing",                "Low"),
        ("parking area improvement request signage parking lot",                      "Low"),
        ("cafeteria food quality suggestion employee welfare comfort",                "Low"),
        ("administrative concern paperwork documentation process",                    "Low"),
        ("air conditioning temperature comfort office environment",                   "Low"),
        ("request for additional equipment tool convenience not urgent",              "Low"),
        ("minor communication issue team coordination improvement",                   "Low"),
        ("suggestion for training program schedule employee development",             "Low"),
        ("cosmetic repair paint wall ceiling minor aesthetic issue",                  "Low"),
        ("general housekeeping reminder cleanliness tidiness area",                   "Low"),
        ("suggestion break room improvement coffee machine request",                  "Low"),
        ("feedback on work schedule rotation minor adjustment",                       "Low"),
        ("request for new signage direction board wayfinding non-critical",           "Low"),
        ("improvement idea safety poster awareness campaign",                         "Low"),
        ("request bulletin board notice board update posting area",                   "Low"),
        ("comfort request fan ventilation minor temperature adjustment",              "Low"),
        ("feedback on meeting frequency schedule calendar update",                    "Low"),
        ("minor cosmetic concern floor mat placement comfort request",                "Low"),
        ("suggestion update break schedule locker room improvement",                  "Low"),
    ]

    def __init__(self):
        self.class_log_priors      = {}
        self.word_log_likelihoods  = {c: defaultdict(float) for c in self.CLASSES}
        self.vocabulary            = set()
        self._train()

    # ── Tokenizer ────────────────────────────────────────────────
    @staticmethod
    def tokenize(text):
        text = str(text).lower()
        text = re.sub(r"[^a-z\s]", " ", text)
        return [w for w in text.split() if len(w) > 1]

    # ── Training (Multinomial NB + Laplace smoothing) ─────────────
    def _train(self):
        class_word_lists  = defaultdict(list)
        class_doc_counts  = defaultdict(int)

        for text, label in self.TRAINING_DATA:
            tokens = self.tokenize(text)
            class_word_lists[label].extend(tokens)
            class_doc_counts[label] += 1
            self.vocabulary.update(tokens)

        total_docs = sum(class_doc_counts.values())
        vocab_size = len(self.vocabulary)

        for cls in self.CLASSES:
            # ── Log prior: log( count(class) / total_docs ) ──────
            self.class_log_priors[cls] = math.log(
                class_doc_counts[cls] / total_docs
            )

            # ── Word frequency map for this class ────────────────
            freq = defaultdict(int)
            for word in class_word_lists[cls]:
                freq[word] += 1
            total_words = sum(freq.values()) + vocab_size  # Laplace denominator

            # ── Log-likelihood for every vocab word ──────────────
            for word in self.vocabulary:
                self.word_log_likelihoods[cls][word] = math.log(
                    (freq.get(word, 0) + 1) / total_words
                )
            # Unknown-word fallback
            self.word_log_likelihoods[cls]["<UNK>"] = math.log(1 / total_words)

    # ── Predict ──────────────────────────────────────────────────
    def predict(self, text):
        """
        Returns:
        {
            "priority":   "High" | "Medium" | "Low",
            "confidence": 0.0 – 1.0,
            "scores":     {"High": ..., "Medium": ..., "Low": ...},
            "algorithm":  "Naive Bayes (Multinomial, Laplace smoothing)"
        }
        """
        tokens = self.tokenize(text)
        if not tokens:
            return {
                "priority":   "Low",
                "confidence": 1.0,
                "scores":     {"High": 0.0, "Medium": 0.0, "Low": 1.0},
                "algorithm":  "Naive Bayes (Multinomial, Laplace smoothing)"
            }

        log_scores = {}
        for cls in self.CLASSES:
            score = self.class_log_priors[cls]
            for token in tokens:
                ll = self.word_log_likelihoods[cls]
                score += ll[token] if token in ll else ll["<UNK>"]
            log_scores[cls] = score

        # Softmax over log-scores → probabilities
        max_s = max(log_scores.values())
        exps  = {c: math.exp(s - max_s) for c, s in log_scores.items()}
        total = sum(exps.values())
        probs = {c: exps[c] / total for c in self.CLASSES}

        best = max(probs, key=probs.get)
        return {
            "priority":   best,
            "confidence": round(probs[best], 4),
            "scores": {
                "High":   round(probs["High"],   4),
                "Medium": round(probs["Medium"], 4),
                "Low":    round(probs["Low"],    4),
            },
            "algorithm": "Naive Bayes (Multinomial, Laplace smoothing)"
        }


# ── Singleton ──
nb_classifier = NaiveBayesClassifier()


def classify_priority(text, hazard_type="", risk_level=""):
    """Convenience wrapper. Returns (priority_str, full_nb_result_dict)."""
    combined = " ".join(filter(None, [str(text), str(hazard_type), str(risk_level)]))
    result   = nb_classifier.predict(combined)
    return result["priority"], result


# ═══════════════════════════════════════════════════════════════════
#  CUSTOM TRAINING DATA (JSON persistence)
# ═══════════════════════════════════════════════════════════════════

def load_custom_training_data():
    """Load user-added training examples from JSON file."""
    if os.path.exists(TRAINING_DATA_FILE):
        try:
            with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_custom_training_data(data):
    """Save user-added training examples to JSON file."""
    with open(TRAINING_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_merged_training_data():
    """Return hardcoded + custom training data combined."""
    custom = load_custom_training_data()
    base = [
        {"id": i, "text": text, "priority": priority, "source": "built-in"}
        for i, (text, priority) in enumerate(NaiveBayesClassifier.TRAINING_DATA)
    ]
    offset = len(base)
    custom_merged = [
        {"id": offset + i, "text": item["text"], "priority": item["priority"], "source": "custom"}
        for i, item in enumerate(custom)
    ]
    return base + custom_merged

# Attach to classifier for easy access
nb_classifier.custom_training_data = load_custom_training_data()
nb_classifier.get_all_training_data = get_merged_training_data


# ─────────────────────────────────────────────
#  CORS
# ─────────────────────────────────────────────

@app.after_request
def add_cors(response):
    origin  = request.headers.get("Origin", "")
    allowed = ["http://localhost", "http://127.0.0.1", "null", ""]
    if any(origin.startswith(a) for a in allowed) or origin == "null":
        response.headers["Access-Control-Allow-Origin"]      = origin or "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"]     = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"]     = "GET, POST, PUT, DELETE, OPTIONS"
    return response

@app.route("/api/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    return "", 204


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def read_html(filename):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.isfile(path):
        return f"<h2>Missing file: {filename}</h2><p>Place it in: {BASE_DIR}</p>", 500
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not logged in."}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not logged in."}), 401
            return redirect(url_for("login_page"))
        if session.get("role") != "Admin":
            if request.path.startswith("/api/"):
                return jsonify({"error": "Admin only."}), 403
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
#  Diagnostics
# ─────────────────────────────────────────────

@app.route("/check")
def check():
    db_ok = False; db_msg = ""
    user_count = folder_count = hazard_count = concern_count = fire_count = 0
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM users");             user_count   = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM cert_folders");      folder_count = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM hazard_reports");    hazard_count = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM concern_reports");   concern_count= cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM emergency_lights");  fire_count   = cur.fetchone()["cnt"]
        cur.close(); db_ok = True; db_msg = "✅ Connected"
    except Exception as e:
        db_msg = f"❌ {e}"

    test = nb_classifier.predict("fire explosion chemical danger critical")
    nb_status = f"✅ {test['priority']} ({test['confidence']*100:.1f}%) — vocab={len(nb_classifier.vocabulary)} words"

    logged_in = "user_id" in session
    return f"""<!DOCTYPE html><html><head><title>Diagnostics</title>
<style>body{{font-family:sans-serif;padding:40px;background:#f9f9f9;}}
h1{{color:#E3AB00;}} .ok{{color:green;}} .fail{{color:red;}}
table{{border-collapse:collapse;width:100%;max-width:680px;margin-top:16px;}}
td,th{{border:1px solid #ddd;padding:10px 16px;}}
th{{background:#E3AB00;color:#2a1f00;}}</style></head>
<body><h1>🔍 Hazard Hub – Diagnostics</h1>
<table>
<tr><th>Check</th><th>Result</th></tr>
<tr><td>MySQL</td><td class="{'ok' if db_ok else 'fail'}">{db_msg}</td></tr>
<tr><td>Naive Bayes Classifier</td><td class="ok">{nb_status}</td></tr>
<tr><td>Training Samples</td><td>{len(NaiveBayesClassifier.TRAINING_DATA)} (High/Medium/Low)</td></tr>
<tr><td>Employee Accounts</td><td>{user_count}</td></tr>
<tr><td>Cert Folders</td><td>{folder_count}</td></tr>
<tr><td>Hazard Reports</td><td>{hazard_count}</td></tr>
<tr><td>Concern Reports</td><td>{concern_count}</td></tr>
<tr><td>Emergency Lights</td><td>{fire_count}</td></tr>
<tr><td>Session</td><td class="{'ok' if logged_in else 'fail'}">
{'✅ Logged in as ' + str(session.get('email')) + ' (' + str(session.get('role')) + ')'
 if logged_in else '❌ Not logged in'}
</td></tr>
</table><br>
<a href="/login" style="background:#E3AB00;color:#2a1f00;padding:10px 28px;border-radius:8px;text-decoration:none;font-weight:bold;">Login →</a>
<a href="/dashboard" style="background:#2a1f00;color:#E3AB00;padding:10px 28px;border-radius:8px;text-decoration:none;font-weight:bold;margin-left:10px;">Dashboard →</a>
</body></html>"""


# ─────────────────────────────────────────────
#  API: Naive Bayes standalone endpoint
# ─────────────────────────────────────────────

@app.route("/api/classify", methods=["POST"])
@login_required
def api_classify():
    """
    POST { "text": "...", "hazard_type": "...", "risk_level": "..." }
    Returns full NB result with confidence scores.
    """
    data        = request.get_json(silent=True) or {}
    text        = (data.get("text") or "").strip()
    hazard_type = (data.get("hazard_type") or "").strip()
    risk_level  = (data.get("risk_level") or "").strip()
    if not text and not hazard_type:
        return jsonify({"error": "text is required"}), 400
    _, result = classify_priority(text, hazard_type, risk_level)
    return jsonify({"success": True, "classification": result}), 200


# ─────────────────────────────────────────────
#  Mobile
# ─────────────────────────────────────────────

@app.route("/mobile")
@app.route("/mobi")
def mobile_app():
    for fname in ["mobile_hazardhub.html", "mobile.html"]:
        p = os.path.join(BASE_DIR, fname)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    return "mobile_hazardhub.html not found next to app.py", 404


# ─────────────────────────────────────────────
#  Pages
# ─────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("admin_dashboard") if session.get("role") == "Admin"
                        else url_for("employee_dashboard"))
    return redirect(url_for("login_page"))

@app.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("index"))
    return read_html("login.html")

@app.route("/dashboard")
@login_required
def admin_dashboard():
    if session.get("role") != "Admin":
        return redirect(url_for("login_page"))
    return read_html("admin_dashboard.html")

@app.route("/employee-dashboard")
@login_required
def employee_dashboard():
    return "<h2>Welcome, Employee!</h2>"


# ─────────────────────────────────────────────
#  API: Login / Logout / Session
# ─────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def api_login():
    data        = request.get_json(silent=True) or {}
    identifier  = (data.get("email") or data.get("username") or "").strip()
    password    = data.get("password") or ""
    role_filter = (data.get("role") or "").strip()
    if not identifier or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400
    try:
        cur = mysql.connection.cursor()
        if role_filter:
            cur.execute("SELECT * FROM users WHERE LOWER(email)=%s AND role=%s", (identifier.lower(), role_filter))
        else:
            cur.execute("SELECT * FROM users WHERE LOWER(email)=%s", (identifier.lower(),))
        user = cur.fetchone()
        cur.close()
    except Exception as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500
    if not user or not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"success": False, "error": "Invalid credentials or role."}), 401
    session.permanent    = True
    session["user_id"]   = user["id"]
    session["email"]     = user["email"]
    session["role"]      = user["role"]
    session["full_name"] = user.get("full_name", "")
    redirect_url = "/dashboard" if user["role"] == "Admin" else "/employee-dashboard"
    return jsonify({
        "success": True, "message": "Login successful.",
        "redirect_url": redirect_url,
        "user": {
            "id":        user["id"],
            "email":     user["email"],
            "role":      user["role"],
            "full_name": user.get("full_name", ""),
            "position":  user.get("position", ""),
            "id_number": user.get("id_number", "")
        }
    }), 200

@app.route("/api/logout", methods=["POST", "GET"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out."}), 200

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route("/api/me")
@app.route("/api/current-user")
@login_required
def api_me():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, email, role, full_name, position, id_number,
                   age, sex, civil_status, employment_status,
                   supervisor_name, supervisor_position
            FROM users WHERE id=%s
        """, (session.get("user_id"),))
        user = cur.fetchone(); cur.close()
    except Exception:
        user = None
    base = {
        "id":        session.get("user_id"),
        "email":     session.get("email"),
        "role":      session.get("role"),
        "full_name": session.get("full_name"),
    }
    if user:
        base.update({k: user[k] for k in user if user[k] is not None})
    return jsonify({"success": True, "user": base}), 200


# ─────────────────────────────────────────────
#  API: Dashboard Stats
# ─────────────────────────────────────────────

@app.route("/api/dashboard/stats")
@login_required
def dashboard_stats():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM hazard_reports");  h = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM concern_reports"); c = cur.fetchone()["cnt"]
        total = h + c
        cur.execute("SELECT COUNT(*) AS cnt FROM hazard_reports  WHERE status='resolved'"); rh = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM concern_reports WHERE status='resolved'"); rc = cur.fetchone()["cnt"]
        resolved = rh + rc
        cur.close()
        return jsonify({"success": True, "stats": {
            "total_incidents": total, "hazards_identified": h,
            "resolved_incidents": resolved, "pending_incidents": max(0, total - resolved)
        }}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
#  API: Hazard Reports
# ─────────────────────────────────────────────

def _fmt_duration(created_at, resolved_at):
    """Return human-readable duration string between two datetimes, or None."""
    if not resolved_at or not created_at:
        return None
    try:
        diff = resolved_at - created_at
        total_min = int(diff.total_seconds() // 60)
        if total_min < 0: return None
        days, rem = divmod(total_min, 1440)
        hrs, mins = divmod(rem, 60)
        parts = []
        if days: parts.append(f"{days}d")
        if hrs:  parts.append(f"{hrs}h")
        parts.append(f"{mins}m")
        return " ".join(parts)
    except Exception:
        return None


@app.route("/api/hazards", methods=["GET"])
@login_required
def get_hazards():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, `date`, `time`, location, reported_by,
                   main_hazard_type AS hazard_type, hazard_categories, hazard_details,
                   description, ai_priority, nb_confidence, status, photo_filename,
                   created_at, admin_remarks, ehs_officer, resolved_at
            FROM hazard_reports ORDER BY id DESC LIMIT 100
        """)
        rows = cur.fetchall()
        cur.close()
        result = []
        for r in rows:
            r = dict(r)
            r["duration"] = _fmt_duration(r.get("created_at"), r.get("resolved_at"))
            r["resolved_at"] = r["resolved_at"].strftime("%Y-%m-%d %H:%M:%S") if r.get("resolved_at") else None
            r["created_at"]  = str(r["created_at"]) if r.get("created_at") else None
            result.append(r)
        return jsonify({"success": True, "hazards": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/hazards/<int:hid>", methods=["GET"])
@login_required
def get_hazard_detail(hid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM hazard_reports WHERE id=%s", (hid,))
        row = cur.fetchone(); cur.close()
        if not row:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "hazard": row}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/hazards", methods=["POST"])
@login_required
def create_hazard():
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json(silent=True) or {}

    report_date      = (data.get("date") or data.get("report_date") or "").strip() or datetime.now().strftime("%Y-%m-%d")
    time_val         = (data.get("time") or data.get("report_time") or "").strip() or datetime.now().strftime("%H:%M")
    location         = (data.get("location") or "").strip()
    reported_by      = (data.get("reported_by") or session.get("full_name") or "").strip()
    main_hazard_type = (data.get("main_hazard_type") or "").strip()
    hazard_categories= (data.get("hazard_categories") or "").strip()
    hazard_details   = (data.get("hazard_details") or "").strip()
    description      = (data.get("description") or "").strip()
    risk_level       = (data.get("risk_level") or "").strip()

    # ── Naive Bayes ──
    combined = " ".join(filter(None, [description, main_hazard_type, hazard_categories, hazard_details, risk_level]))
    ai_priority, nb_result = classify_priority(combined)
    nb_confidence  = nb_result["confidence"]
    nb_scores_json = json.dumps(nb_result["scores"])

    photo_filename = ""
    if "photo" in request.files:
        f = request.files["photo"]
        if f and f.filename:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "jpg"
            photo_filename = uuid.uuid4().hex + "." + ext
            f.save(os.path.join(UPLOAD_FOLDER, photo_filename))

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO hazard_reports
              (`date`, `time`, location, reported_by, main_hazard_type,
               hazard_categories, hazard_details, description,
               risk_level, ai_priority, nb_confidence, nb_scores,
               status, photo_filename, submitted_by_user)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s)
        """, (report_date, time_val, location, reported_by, main_hazard_type,
              hazard_categories, hazard_details, description,
              risk_level or ai_priority, ai_priority, nb_confidence, nb_scores_json,
              photo_filename, session.get("user_id")))
        mysql.connection.commit()
        new_id = cur.lastrowid
        if ai_priority == "High":
            cur.execute("""INSERT INTO notifications (`date`, severity, message, location, user_id)
                           VALUES (%s,'high',%s,%s,%s)""",
                        (report_date,
                         f"High-priority hazard: {main_hazard_type or description[:60]}",
                         location, session.get("user_id")))
            mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "id": new_id, "ai_classification": nb_result}), 201


# ─────────────────────────────────────────────
#  API: Concern Reports
# ─────────────────────────────────────────────

@app.route("/api/concerns", methods=["GET"])
@login_required
def get_concerns():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM concern_reports ORDER BY id DESC LIMIT 100")
        raw_rows = cur.fetchall(); cur.close()
        results = []
        for r in raw_rows:
            date_val  = r.get("report_date") or r.get("date") or str(r.get("created_at", ""))[:10]
            time_val  = r.get("report_time") or r.get("time") or ""
            type_val  = r.get("report_type") or r.get("concern_type") or "Concern / Suggestion"
            desc_val  = r.get("concern_description") or r.get("description") or ""
            loc_val   = r.get("incident_location") or r.get("location") or ""
            rep_val   = r.get("reported_by") or r.get("submitted_by") or ""
            prio_val  = str(r.get("risk_level") or r.get("ai_priority") or "low").strip().capitalize()
            photo_val = r.get("photo_filename") or r.get("hazard_image_path") or ""
            results.append({
                "id": r.get("id"), "date": str(date_val)[:10] if date_val else "",
                "time": str(time_val)[:5] if time_val else "",
                "concern_type": type_val, "description": desc_val,
                "location": loc_val, "reported_by": rep_val,
                "ai_priority": prio_val, "nb_confidence": r.get("nb_confidence") or 0.0,
                "status": r.get("status") or "pending",
                "photo_filename": photo_val, "created_at": str(r.get("created_at", "")),
                "admin_remarks": r.get("admin_remarks") or "",
                "ehs_officer": r.get("ehs_officer") or "",
                "resolved_at": r["resolved_at"].strftime("%Y-%m-%d %H:%M:%S") if r.get("resolved_at") else None,
                "duration": _fmt_duration(r.get("created_at"), r.get("resolved_at")),
            })
        return jsonify({"success": True, "concerns": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/concerns/<int:cid>", methods=["GET"])
@login_required
def get_concern_detail(cid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM concern_reports WHERE id=%s", (cid,))
        row = cur.fetchone(); cur.close()
        if not row:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "concern": row}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/concerns", methods=["POST"])
@login_required
def create_concern():
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json(silent=True) or {}

    report_date       = (data.get("date") or data.get("report_date") or "").strip() or datetime.now().strftime("%Y-%m-%d")
    report_time       = (data.get("time") or data.get("report_time") or "").strip() or datetime.now().strftime("%H:%M")
    report_type       = (data.get("concern_type") or data.get("report_type") or "").strip()
    reported_by       = (data.get("submitted_by") or data.get("reported_by") or session.get("full_name") or "").strip()
    is_anonymous      = 1 if data.get("is_anonymous") else 0
    incident_location = (data.get("location") or data.get("incident_location") or "").strip()
    inspected_by      = (data.get("inspected_by") or "").strip()
    hazard_desc       = (data.get("hazard_description") or "").strip()
    concern_desc      = (data.get("description") or data.get("concern_description") or "").strip()
    suggestion_text   = (data.get("suggestion_text") or "").strip()

    if not report_type:
        return jsonify({"success": False, "error": "report_type / concern_type is required."}), 400

    # ── Naive Bayes ──

    combined = " ".join(filter(None, [concern_desc, hazard_desc, report_type, suggestion_text]))
    risk_level, nb_result = classify_priority(combined)
    nb_confidence  = nb_result["confidence"]
    nb_scores_json = json.dumps(nb_result["scores"])

    hazard_image_path = ""
    if "photo" in request.files:
        f = request.files["photo"]
        if f and f.filename:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "jpg"
            hazard_image_path = uuid.uuid4().hex + "." + ext
            f.save(os.path.join(UPLOAD_FOLDER, hazard_image_path))

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO concern_reports
              (report_date, report_time, report_type, reported_by,
               is_anonymous, status, incident_location, inspected_by,
               hazard_description, hazard_image_path, risk_level,
               nb_confidence, nb_scores, concern_description, suggestion_text)
            VALUES (%s,%s,%s,%s,%s,'pending',%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (report_date, report_time, report_type, reported_by,
              is_anonymous, incident_location, inspected_by,
              hazard_desc, hazard_image_path, risk_level,
              nb_confidence, nb_scores_json, concern_desc, suggestion_text))
        mysql.connection.commit()
        new_id = cur.lastrowid; cur.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "id": new_id, "ai_classification": nb_result}), 201


# ─────────────────────────────────────────────
#  API: Status Updates
# ─────────────────────────────────────────────
VALID_STATUSES = {"pending", "resolved", "rejected"}

@app.route("/api/hazards/<int:hid>/status", methods=["PUT"])
@login_required
def update_hazard_status(hid):
    data        = request.get_json(silent=True) or {}
    status      = (data.get("status") or "").strip()
    remarks     = (data.get("remarks") or "").strip()
    ehs_officer = session.get("full_name") or ""
    if status not in VALID_STATUSES:
        return jsonify({"error": "Invalid status"}), 400
    now = datetime.now()
    resolved_at = now if status == "resolved" else None
    try:
        cur = mysql.connection.cursor()
        # Fetch created_at to compute duration
        cur.execute("SELECT created_at, resolved_at FROM hazard_reports WHERE id=%s", (hid,))
        row = cur.fetchone()
        created_at = row["created_at"] if row else None
        # Only set resolved_at if transitioning TO resolved and not already set
        existing_resolved = row["resolved_at"] if row else None
        if status == "resolved" and not existing_resolved:
            resolved_at = now
        elif status != "resolved":
            resolved_at = None
        else:
            resolved_at = existing_resolved  # keep original resolution time
        cur.execute(
            "UPDATE hazard_reports SET status=%s, admin_remarks=%s, ehs_officer=%s, resolved_at=%s WHERE id=%s",
            (status, remarks or None, ehs_officer or None, resolved_at, hid)
        )
        mysql.connection.commit(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # Compute duration
    duration_str = None
    if resolved_at and created_at:
        try:
            diff = resolved_at - created_at
            total_min = int(diff.total_seconds() // 60)
            days, rem = divmod(total_min, 1440)
            hrs, mins = divmod(rem, 60)
            parts = []
            if days: parts.append(f"{days}d")
            if hrs:  parts.append(f"{hrs}h")
            parts.append(f"{mins}m")
            duration_str = " ".join(parts)
        except Exception:
            duration_str = None
    return jsonify({
        "success": True,
        "ehs_officer": ehs_officer,
        "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else None,
        "duration": duration_str
    }), 200

@app.route("/api/concerns/<int:cid>/status", methods=["PUT"])
@login_required
def update_concern_status(cid):
    data        = request.get_json(silent=True) or {}
    status      = (data.get("status") or "").strip()
    remarks     = (data.get("remarks") or "").strip()
    ehs_officer = session.get("full_name") or ""
    if status not in VALID_STATUSES:
        return jsonify({"error": "Invalid status"}), 400
    now = datetime.now()
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT created_at, resolved_at FROM concern_reports WHERE id=%s", (cid,))
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
            "UPDATE concern_reports SET status=%s, admin_remarks=%s, ehs_officer=%s, resolved_at=%s WHERE id=%s",
            (status, remarks or None, ehs_officer or None, resolved_at, cid)
        )
        mysql.connection.commit(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    duration_str = None
    if resolved_at and created_at:
        try:
            diff = resolved_at - created_at
            total_min = int(diff.total_seconds() // 60)
            days, rem = divmod(total_min, 1440)
            hrs, mins = divmod(rem, 60)
            parts = []
            if days: parts.append(f"{days}d")
            if hrs:  parts.append(f"{hrs}h")
            parts.append(f"{mins}m")
            duration_str = " ".join(parts)
        except Exception:
            duration_str = None
    return jsonify({
        "success": True,
        "ehs_officer": ehs_officer,
        "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else None,
        "duration": duration_str
    }), 200


# ─────────────────────────────────────────────
#  API: Notifications
# ─────────────────────────────────────────────
@app.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, `date`, severity, message, location, is_read FROM notifications ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall(); cur.close()
        return jsonify({"success": True, "notifications": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
#  API: Fire Protection
# ─────────────────────────────────────────────
@app.route("/api/fire-protection/stats", methods=["GET"])
@login_required
def fire_protection_stats():
    try:
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM fire_protection_inspections WHERE inspection_type='fire_extinguisher'"); ext = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM fire_protection_inspections WHERE inspection_type='emergency_light'");   em  = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM fire_protection_inspections WHERE inspection_type='fire_hose_cabinet'"); hose= cur.fetchone()["cnt"]
        except Exception:
            try:
                cur.execute("SELECT COUNT(*) AS cnt FROM emergency_lights"); em = cur.fetchone()["cnt"]
            except Exception: em = 0
            ext = hose = 0
        cur.close()
        return jsonify({"success": True, "extinguisher_count": ext, "emergency_light_count": em, "hose_cabinet_count": hose}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/fire-protection/inspection", methods=["POST"])
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
            f.save(os.path.join(UPLOAD_FOLDER, photo_filename))

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO fire_protection_inspections
              (inspection_type, location, extinguisher_type, capacity,
               expiry_date, inspected_by, inspection_date, remark,
               checklist_ok, checklist_ng, photo_filename, user_id, submitted_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
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
            photo_filename, session.get("user_id"),
            (data.get("submitted_at") or "").strip()
        ))
        mysql.connection.commit()
        new_id = cur.lastrowid; cur.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "id": new_id}), 201

@app.route("/api/fire-protection/inspections", methods=["GET"])
@login_required
def get_fire_inspections():
    t = request.args.get("type", "")
    try:
        cur = mysql.connection.cursor()
        if t:
            cur.execute("SELECT * FROM fire_protection_inspections WHERE inspection_type=%s ORDER BY id DESC", (t,))
        else:
            cur.execute("SELECT * FROM fire_protection_inspections ORDER BY id DESC")
        rows = cur.fetchall(); cur.close()
        return jsonify({"success": True, "inspections": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
#  API: Accounts
# ─────────────────────────────────────────────

@app.route("/api/accounts", methods=["GET"])
@admin_required
def get_accounts():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, full_name, email, role, position, id_number, created_at FROM users ORDER BY id")
        rows = cur.fetchall(); cur.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/accounts", methods=["POST"])
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
        cur.execute("INSERT INTO users (full_name, email, password_hash, role, position) VALUES (%s,%s,%s,%s,%s)",
                    (name, email, generate_password_hash(password), role, position))
        mysql.connection.commit()
        new_id = cur.lastrowid
        id_number = f"{'ADMIN' if role=='Admin' else 'EMP'}-{str(new_id).zfill(5)}"
        cur.execute("UPDATE users SET id_number=%s WHERE id=%s", (id_number, new_id))
        mysql.connection.commit(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Account created.", "id": new_id}), 201

@app.route("/api/accounts/<int:uid>", methods=["PUT"])
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
            cur.execute("UPDATE users SET full_name=%s, email=%s, password_hash=%s, role=%s, position=%s, id_number=%s WHERE id=%s",
                        (name, email, generate_password_hash(password), role, position, id_number, uid))
        else:
            cur.execute("UPDATE users SET full_name=%s, email=%s, role=%s, position=%s, id_number=%s WHERE id=%s",
                        (name, email, role, position, id_number, uid))
        mysql.connection.commit(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Account updated."}), 200

@app.route("/api/accounts/<int:uid>", methods=["DELETE"])
@admin_required
def delete_account(uid):
    if uid == session.get("user_id"):
        return jsonify({"error": "Cannot delete your own account."}), 400
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM users WHERE id=%s", (uid,))
        mysql.connection.commit(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Account deleted."}), 200


# ─────────────────────────────────────────────
#  API: Employee Profile (self-service)
# ─────────────────────────────────────────────

@app.route("/api/profile", methods=["GET"])
@login_required
def get_my_profile():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, full_name, email, role, position, id_number,
                   age, sex, civil_status, employment_status,
                   supervisor_name, supervisor_position,
                   profile_complete, profile_updated_at, created_at
            FROM users WHERE id = %s
        """, (session["user_id"],))
        row = cur.fetchone(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if not row:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"success": True, "profile": row}), 200


@app.route("/api/profile", methods=["PUT"])
@login_required
def update_my_profile():
    data = request.get_json(silent=True) or {}

    VALID_ENUMS = {
        "sex":               {"Male", "Female", "Other"},
        "civil_status":      {"Single", "Married", "Widowed", "Separated", "Divorced"},
        "employment_status": {"Regular", "Probationary", "Contractual", "Part-time", "OJT"},
    }
    for field, valid in VALID_ENUMS.items():
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

    sex                 = data.get("sex") or None
    civil_status        = data.get("civil_status") or None
    employment_status   = data.get("employment_status") or None
    supervisor_name     = (data.get("supervisor_name") or "").strip() or None
    supervisor_position = (data.get("supervisor_position") or "").strip() or None

    if all(v is None for v in [age, sex, civil_status, employment_status, supervisor_name, supervisor_position]):
        return jsonify({"error": "No fields provided."}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
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
        """, (age, sex, civil_status, employment_status,
              supervisor_name, supervisor_position,
              datetime.now(), session["user_id"]))
        mysql.connection.commit(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"success": True, "message": "Profile updated successfully."}), 200


# ─────────────────────────────────────────────
#  API: Certificate Folders & Files
# ─────────────────────────────────────────────

@app.route("/api/folders", methods=["GET"])
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

@app.route("/api/folders", methods=["POST"])
@login_required
def create_folder():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    emoji = (data.get("emoji") or "📁").strip()
    if not name:
        return jsonify({"error": "Folder name is required."}), 400
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO cert_folders (name, emoji, created_by) VALUES (%s,%s,%s)", (name, emoji, session["user_id"]))
        mysql.connection.commit()
        new_id = cur.lastrowid; cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"id": new_id, "name": name, "emoji": emoji, "file_count": 0}), 201

@app.route("/api/folders/<int:fid>", methods=["PUT"])
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
        mysql.connection.commit(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Folder renamed."}), 200

@app.route("/api/folders/<int:fid>", methods=["DELETE"])
@login_required
def delete_folder(fid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT filename FROM cert_files WHERE folder_id=%s", (fid,))
        for row in cur.fetchall():
            p = os.path.join(UPLOAD_FOLDER, row["filename"])
            try:
                if os.path.isfile(p): os.remove(p)
            except OSError: pass
        cur.execute("DELETE FROM cert_folders WHERE id=%s", (fid,))
        mysql.connection.commit(); cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Folder deleted."}), 200

@app.route("/api/folders/<int:fid>/files", methods=["GET"])
@login_required
def get_files(fid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM cert_folders WHERE id=%s", (fid,))
    if not cur.fetchone():
        cur.close(); return jsonify({"error": "Folder not found."}), 404
    cur.execute("SELECT id, original_name, file_size, mime_type, filename, uploaded_at FROM cert_files WHERE folder_id=%s ORDER BY id", (fid,))
    rows = cur.fetchall(); cur.close()
    return jsonify(rows), 200

@app.route("/api/folders/<int:fid>/files", methods=["POST"])
@login_required
def upload_file(fid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM cert_folders WHERE id=%s", (fid,))
    if not cur.fetchone():
        cur.close(); return jsonify({"error": "Folder not found."}), 404
    if "file" not in request.files:
        cur.close(); return jsonify({"error": "No file provided."}), 400
    file = request.files["file"]
    if not file.filename:
        cur.close(); return jsonify({"error": "Empty filename."}), 400
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    saved_name = (uuid.uuid4().hex + "." + ext) if ext else uuid.uuid4().hex
    save_path  = os.path.join(UPLOAD_FOLDER, saved_name)
    file.save(save_path)
    size_bytes = os.path.getsize(save_path)
    size_kb = size_bytes / 1024
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
    try:
        cur.execute("INSERT INTO cert_files (folder_id, filename, original_name, file_size, mime_type) VALUES (%s,%s,%s,%s,%s)",
                    (fid, saved_name, file.filename, size_str, file.content_type or ""))
        mysql.connection.commit()
        new_id = cur.lastrowid; cur.close()
    except Exception as e:
        try: os.remove(save_path)
        except OSError: pass
        return jsonify({"error": str(e)}), 500
    return jsonify({"id": new_id, "filename": saved_name, "original_name": file.filename, "file_size": size_str, "mime_type": file.content_type or ""}), 201

@app.route("/api/files/<int:file_id>", methods=["DELETE"])
@login_required
def delete_file(file_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT filename FROM cert_files WHERE id=%s", (file_id,))
        row = cur.fetchone()
        if row:
            p = os.path.join(UPLOAD_FOLDER, row["filename"])
            try:
                if os.path.isfile(p): os.remove(p)
            except OSError: pass
            cur.execute("DELETE FROM cert_files WHERE id=%s", (file_id,))
            mysql.connection.commit()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "File deleted."}), 200


# ─────────────────────────────────────────────
#  Serve uploads
# ─────────────────────────────────────────────
@app.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ─────────────────────────────────────────────
#  API: Employee Autocomplete (for Investigation Report)
# ─────────────────────────────────────────────

@app.route("/api/employees/search", methods=["GET"])
@login_required
def search_employees():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([]), 200
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT full_name, position, id_number,
                   age, sex, civil_status, employment_status,
                   supervisor_name, supervisor_position
            FROM users
            WHERE full_name LIKE %s AND is_active = 1
            ORDER BY full_name
            LIMIT 10
        """, (f"%{q}%",))
        results = cur.fetchall()
        cur.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
#  API: Settings — Training Data & System Info
# ─────────────────────────────────────────────

@app.route("/api/system-info", methods=["GET"])
@login_required
def system_info():
    """Return classifier diagnostics and system stats."""
    custom = load_custom_training_data()
    test = nb_classifier.predict("fire explosion chemical danger critical")
    return jsonify({
        "success": True,
        "nb_status": "OK",
        "vocab_size": len(nb_classifier.vocabulary),
        "builtin_count": len(NaiveBayesClassifier.TRAINING_DATA),
        "custom_count": len(custom),
        "total_samples": len(NaiveBayesClassifier.TRAINING_DATA) + len(custom),
        "algorithm": "Naive Bayes (Multinomial, Laplace smoothing)",
        "test_classification": test["priority"],
        "test_confidence": test["confidence"]
    }), 200

@app.route("/api/nb-training-data", methods=["GET"])
@login_required
def get_nb_training_data():
    """Return all training data split into builtin and custom lists."""
    custom = load_custom_training_data()
    builtin = [
        {"id": i, "text": text, "priority": priority, "source": "built-in"}
        for i, (text, priority) in enumerate(NaiveBayesClassifier.TRAINING_DATA)
    ]
    custom_merged = [
        {"id": len(builtin) + i, "text": item["text"], "priority": item["priority"], "source": "custom"}
        for i, item in enumerate(custom)
    ]
    return jsonify({
        "success": True,
        "builtin": builtin,
        "custom": custom_merged,
        "counts": {
            "built_in": len(builtin),
            "custom": len(custom_merged),
            "total": len(builtin) + len(custom_merged)
        }
    }), 200

@app.route("/api/nb-training-data", methods=["POST"])
@admin_required
def add_nb_training_data():
    """Add a new custom training example."""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    priority = (data.get("priority") or "").strip()
    if not text or not priority:
        return jsonify({"success": False, "error": "text and priority are required."}), 400
    if priority not in NaiveBayesClassifier.CLASSES:
        return jsonify({"success": False, "error": f"priority must be one of {NaiveBayesClassifier.CLASSES}."}), 400
    custom = load_custom_training_data()
    custom.append({"text": text, "priority": priority})
    save_custom_training_data(custom)
    # Update classifier's attached data
    nb_classifier.custom_training_data = custom
    return jsonify({"success": True, "message": "Training example added.", "custom_count": len(custom)}), 201

@app.route("/api/nb-training-data", methods=["DELETE"])
@admin_required
def remove_nb_training_data():
    """Remove a custom training example by index (in custom list)."""
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

@app.route("/api/nb-training-data/custom/<int:index>", methods=["DELETE"])
@admin_required
def remove_nb_training_data_by_url(index):
    """Remove a custom training example by URL path index (frontend-compatible)."""
    custom = load_custom_training_data()
    if index not in range(-len(custom), len(custom)):
        return jsonify({"success": False, "error": "index out of range."}), 404
    removed = custom.pop(index)
    save_custom_training_data(custom)
    nb_classifier.custom_training_data = custom
    return jsonify({"success": True, "message": "Removed.", "removed": removed}), 200

@app.route("/api/nb-classify", methods=["POST"])
@login_required
def api_nb_classify():
    """
    POST { "text": "..." }
    Returns NB classification result with priority, confidence, and scores.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"success": False, "error": "text is required"}), 400
    result = nb_classifier.predict(text)
    return jsonify({
        "success": True,
        "priority": result["priority"],
        "confidence": result["confidence"],
        "scores": result["scores"]
    }), 200


# ─────────────────────────────────────────────
#  Error handlers
# ─────────────────────────────────────────────
@app.errorhandler(403)
def forbidden(e):    return jsonify({"error": "Access denied."}), 403
@app.errorhandler(404)
def not_found(e):    return jsonify({"error": "Not found."}), 404
@app.errorhandler(500)
def server_error(e): return jsonify({"error": f"Server error: {str(e)}"}), 500


# ─────────────────────────────────────────────
#  Startup
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*62)
    print("  Hazard Hub – Flask Backend  (Naive Bayes Classifier)")
    print(f"  Vocab size  : {len(nb_classifier.vocabulary)} words")
    print(f"  Classes     : {NaiveBayesClassifier.CLASSES}")
    print(f"  Train size  : {len(NaiveBayesClassifier.TRAINING_DATA)} samples")
    print("\n  Self-test results:")
    for txt, exp in [
        ("fire explosion chemical gas leak emergency danger fatal",  "High"),
        ("slip wet floor broken equipment near miss noise",          "Medium"),
        ("minor suggestion cleanliness improvement feedback",        "Low"),
    ]:
        _, r = classify_priority(txt)
        ok = "OK" if r["priority"] == exp else "X"
        print(f"  {ok}  {r['priority']:6s} ({r['confidence']*100:4.1f}%) | {txt[:50]}")
    print("\n  Diagnostic : http://localhost:5000/check")
    print("  Login      : http://localhost:5000/login")
    print("="*62 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
