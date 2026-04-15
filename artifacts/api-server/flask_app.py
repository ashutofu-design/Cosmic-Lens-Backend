#!/usr/bin/env python3
"""
Flask API server for Cosmic Lens.
Exposes POST /api/kundli, auth endpoints, moon transit, and admin routes.

DATABASE SETUP (portable):
  - Set DATABASE_URL environment variable to switch databases.
  - PostgreSQL: postgresql://user:password@host:5432/dbname
  - SQLite fallback used automatically if DATABASE_URL is not set.
"""

import os
import sys
import secrets
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kundli_engine import calculate_kundli
from kp_engine import calculate_kp
from ask_engine import process_ask
from database import db, init_db
from models import User, Kundli

app = Flask(__name__)
CORS(app)

# ── Database init ──────────────────────────────────────────────────────────────
init_db(app)

# ── Admin auth helper ──────────────────────────────────────────────────────────
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "cosmic-admin-2024")

def require_admin():
    """Check admin token from header. Returns None if valid, error response if not."""
    token = request.headers.get("X-Admin-Token", "")
    if not token or token != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    return None

# ── Auth routes ────────────────────────────────────────────────────────────────

@app.route("/api/auth/config", methods=["GET"])
def auth_config():
    return jsonify({
        "googleClientId": os.environ.get("GOOGLE_CLIENT_ID", "")
    })


@app.route("/api/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data  = request.get_json(force=True, silent=True) or {}
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    pwd   = data.get("password") or ""

    if not name or not email or not pwd:
        return jsonify({"error": "Name, email, and password are required"}), 400
    if "@" not in email or "." not in email:
        return jsonify({"error": "Enter a valid email address"}), 400
    if len(pwd) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(
        name=name, email=email,
        password=generate_password_hash(pwd),
        api_key=secrets.token_hex(32),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data  = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    pwd   = data.get("password") or ""

    if not email or not pwd:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.password or not check_password_hash(user.password, pwd):
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate api_key if user doesn't have one (backfill)
    if not user.api_key:
        user.api_key = secrets.token_hex(32)

    user.last_active = datetime.utcnow()
    db.session.commit()
    return jsonify(user.to_dict())


@app.route("/api/auth/google", methods=["POST"])
def google_login():
    data       = request.get_json(force=True, silent=True) or {}
    credential = data.get("credential") or ""
    client_id  = os.environ.get("GOOGLE_CLIENT_ID", "")

    if not credential:
        return jsonify({"error": "Google credential required"}), 400
    if not client_id:
        return jsonify({"error": "Google Sign-In is not configured on this server"}), 503

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as g_requests
        info      = id_token.verify_oauth2_token(credential, g_requests.Request(), client_id)
        google_id = info["sub"]
        email     = info.get("email", "").lower()
        name      = info.get("name", "")
    except Exception as exc:
        return jsonify({"error": f"Google verification failed: {exc}"}), 401

    user = User.query.filter(
        (User.email == email) | (User.google_id == google_id)
    ).first()

    if user:
        user.google_id   = google_id
        user.last_active = datetime.utcnow()
        db.session.commit()
        return jsonify(user.to_dict())
    else:
        user = User(name=name, email=email, google_id=google_id)
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201


# ── API key auth helper ────────────────────────────────────────────────────────

def get_authed_user(user_id: int):
    """Validate X-API-Key header for a given user_id. Returns (user, error_response)."""
    api_key = request.headers.get("X-API-Key", "").strip()
    user    = User.query.get(user_id)
    if not user:
        return None, (jsonify({"error": "User not found"}), 404)
    if not api_key or user.api_key != api_key:
        return None, (jsonify({"error": "Unauthorized — invalid API key"}), 401)
    return user, None


# ── Kundli save/load routes ────────────────────────────────────────────────────

@app.route("/api/user/<int:user_id>/kundli", methods=["GET"])
def get_user_kundli(user_id):
    """Get saved kundli for a user."""
    user, err = get_authed_user(user_id)
    if err: return err
    if not user.kundli:
        return jsonify({"kundli": None})
    # Return full chart_data too so the app can restore the chart
    import json
    k = user.kundli
    d = k.to_dict()
    if k.chart_data:
        try: d["chart_data"] = json.loads(k.chart_data)
        except Exception: pass
    return jsonify({"kundli": d})


@app.route("/api/user/<int:user_id>/kundli", methods=["POST"])
def save_user_kundli(user_id):
    """Save or update kundli for a user."""
    user, err = get_authed_user(user_id)
    if err: return err

    data = request.get_json(force=True, silent=True) or {}
    import json

    if user.kundli:
        k = user.kundli
    else:
        k = Kundli(user_id=user_id)
        db.session.add(k)

    k.name       = data.get("name", "")
    k.dob        = data.get("dob", "")
    k.tob        = data.get("tob", "")
    k.pob        = data.get("pob", "")
    k.lat        = data.get("lat")
    k.lon        = data.get("lon")
    k.tz         = data.get("tz")
    k.chart_data = json.dumps(data.get("chart_data")) if data.get("chart_data") else None
    k.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"success": True})


# ── Admin routes ────────────────────────────────────────────────────────────────

@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    """Dashboard stats — total users, PRO users, active today."""
    err = require_admin()
    if err:
        return err

    from datetime import timedelta
    today = datetime.utcnow() - timedelta(hours=24)

    total_users  = User.query.count()
    pro_users    = User.query.filter_by(is_pro=True).count()
    active_today = User.query.filter(User.last_active >= today).count()
    total_kundli = Kundli.query.count()

    return jsonify({
        "total_users":  total_users,
        "pro_users":    pro_users,
        "active_today": active_today,
        "total_kundli": total_kundli,
    })


@app.route("/api/admin/users", methods=["GET"])
def admin_users():
    """List all users with pagination."""
    err = require_admin()
    if err:
        return err

    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search   = request.args.get("search", "").strip()

    query = User.query
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    paginated = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "users":   [u.to_admin_dict() for u in paginated.items],
        "total":   paginated.total,
        "page":    page,
        "pages":   paginated.pages,
    })


@app.route("/api/admin/users/<int:user_id>", methods=["GET"])
def admin_user_detail(user_id):
    """Get full detail of one user."""
    err = require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    result = user.to_admin_dict()
    if user.kundli:
        result["kundli"] = user.kundli.to_dict()
    return jsonify(result)


@app.route("/api/admin/users/<int:user_id>/pro", methods=["POST"])
def admin_toggle_pro(user_id):
    """Toggle PRO status for a user."""
    err = require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data     = request.get_json(force=True, silent=True) or {}
    user.is_pro = data.get("is_pro", not user.is_pro)
    db.session.commit()
    return jsonify({"success": True, "user_id": user_id, "is_pro": user.is_pro})


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    """Delete a user and their kundli."""
    err = require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True})


# ── Existing routes ────────────────────────────────────────────────────────────

@app.route("/api/healthz", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/timezone", methods=["GET"])
def timezone_lookup():
    """
    Returns the accurate UTC offset (hours) for a given lat/lon using
    timezonefinder + Python's datetime so DST is always handled correctly.
    """
    try:
        lat = float(request.args.get("lat", 0))
        lon = float(request.args.get("lon", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lon must be numeric"}), 400

    try:
        from timezonefinder import TimezoneFinder
        from zoneinfo import ZoneInfo
        from datetime import datetime as _dt

        tf      = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            tz_offset = round((lon / 15) * 2) / 2
            return jsonify({"tz": tz_offset, "name": "UTC", "approximate": True})

        zone       = ZoneInfo(tz_name)
        now_utc    = _dt.now(ZoneInfo("UTC"))
        offset_sec = now_utc.astimezone(zone).utcoffset().total_seconds()
        tz_offset  = offset_sec / 3600.0

        return jsonify({"tz": tz_offset, "name": tz_name, "approximate": False})

    except Exception as exc:
        tz_offset = round((lon / 15) * 2) / 2
        return jsonify({"tz": tz_offset, "name": "UTC", "approximate": True, "error": str(exc)})


@app.route("/api/kundli", methods=["POST"])
def kundli():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    required = ["day", "month", "year", "hour", "minute", "ampm", "lat", "lon", "tz", "name", "place"]
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        result = calculate_kundli(data)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/moon_transit", methods=["GET"])
def moon_transit():
    import swisseph as swe
    from datetime import datetime

    # Optional ?date=YYYY-MM-DD  →  use noon UTC of that date.
    # Without it, default to right now (current behaviour).
    date_str = request.args.get("date")
    if date_str:
        try:
            d   = datetime.strptime(date_str, "%Y-%m-%d")
            now = d.replace(hour=12, minute=0, second=0)
        except ValueError:
            return jsonify({"error": "date must be YYYY-MM-DD"}), 400
    else:
        now = datetime.utcnow()

    jd   = swe.julday(now.year, now.month, now.day,
                      now.hour + now.minute / 60.0 + now.second / 3600.0)
    # swe.set_sid_mode(SIDM_LAHIRI) already set at kundli_engine module load
    flags  = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    result = swe.calc_ut(jd, swe.MOON, flags)
    lon    = result[0][0]

    rashi_names = [
        "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
    ]
    rashi_index = int(lon / 30) % 12
    return jsonify({
        "rashiIndex": rashi_index,
        "rashiName":  rashi_names[rashi_index],
        "longitude":  round(lon, 4),
    })


@app.route("/api/moon_history", methods=["GET"])
def moon_history():
    """
    Returns real sidereal moon longitude + rashi for N evenly-spaced points.

    Without ?date:  N*interval hours backwards from now (original behaviour).
    With ?date=YYYY-MM-DD:  N evenly-spaced points across that calendar day
                            (from 00:00 to 23:59 UTC).
    Default: 12 points, 2-hour interval.
    """
    import swisseph as swe
    from datetime import datetime, timedelta

    count    = max(1, min(int(request.args.get("count",    12)), 48))
    interval = max(0.5, min(float(request.args.get("interval", 2)), 24))
    date_str = request.args.get("date")  # optional YYYY-MM-DD

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    rashi_names = [
        "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
    ]

    if date_str:
        # Distribute `count` points evenly across the requested day (UTC).
        try:
            day_start = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "date must be YYYY-MM-DD"}), 400
        step_hours = 24.0 / count
        times = [day_start + timedelta(hours=i * step_hours) for i in range(count)]
    else:
        now = datetime.utcnow()
        times = [now - timedelta(hours=(count - 1 - i) * interval) for i in range(count)]

    points = []
    for t in times:
        jd = swe.julday(t.year, t.month, t.day,
                        t.hour + t.minute / 60.0 + t.second / 3600.0)
        result, _ = swe.calc_ut(jd, swe.MOON, flags)
        lon       = result[0] % 360
        rashi_idx = int(lon / 30) % 12

        h = t.hour
        if   h == 0:  label = "12A"
        elif h < 12:  label = f"{h}A"
        elif h == 12: label = "12P"
        else:         label = f"{h - 12}P"

        points.append({
            "longitude":  round(lon, 4),
            "rashiIndex": rashi_idx,
            "rashiName":  rashi_names[rashi_idx],
            "label":      label,
            "hoursAgo":   None if date_str else round((datetime.utcnow() - t).total_seconds() / 3600, 1),
        })

    return jsonify({"points": points})


@app.route("/api/transits", methods=["POST"])
def planet_transits():
    """
    Accept {"dates": ["YYYY-MM-DD", ...]}
    Return sidereal longitudes for Jupiter, Saturn, Rahu, Ketu, Sun, Mars
    for each requested date (using noon UTC).
    """
    import swisseph as swe
    from datetime import datetime

    data = request.get_json(force=True, silent=True) or {}
    dates = data.get("dates", [])
    if not dates or not isinstance(dates, list):
        return jsonify({"error": "Provide dates as a list of YYYY-MM-DD strings"}), 400

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    planet_map = {
        "Jupiter": swe.JUPITER,
        "Saturn":  swe.SATURN,
        "Sun":     swe.SUN,
        "Mars":    swe.MARS,
    }

    results = []
    for date_str in dates[:12]:            # cap at 12 dates
        try:
            d  = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            jd = swe.julday(d.year, d.month, d.day, 12.0)   # noon UTC
        except ValueError:
            results.append({"date": date_str, "error": "bad date format"})
            continue

        positions = {}
        for name, pid in planet_map.items():
            try:
                res = swe.calc_ut(jd, pid, flags)
                positions[name] = round(res[0][0] % 360, 3)
            except Exception:
                positions[name] = 0.0

        # Rahu (Mean Node) + Ketu
        try:
            rahu_res = swe.calc_ut(jd, swe.MEAN_NODE, flags)
            rahu_lon = rahu_res[0][0] % 360
            positions["Rahu"] = round(rahu_lon, 3)
            positions["Ketu"] = round((rahu_lon + 180) % 360, 3)
        except Exception:
            positions["Rahu"] = 0.0
            positions["Ketu"] = 0.0

        results.append({"date": date_str, "positions": positions})

    return jsonify(results)


@app.route("/api/current_transits", methods=["GET"])
def current_transits():
    """Real-time sidereal planetary positions (Lahiri ayanamsha) for all 9 grahas."""
    import swisseph as swe
    from datetime import datetime

    now   = datetime.utcnow()
    jd    = swe.julday(now.year, now.month, now.day,
                       now.hour + now.minute / 60.0 + now.second / 3600.0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    RASHI = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

    planet_map = [
        ("Sun",     swe.SUN),
        ("Moon",    swe.MOON),
        ("Mars",    swe.MARS),
        ("Mercury", swe.MERCURY),
        ("Jupiter", swe.JUPITER),
        ("Venus",   swe.VENUS),
        ("Saturn",  swe.SATURN),
    ]

    planets = []
    for name, pid in planet_map:
        try:
            res = swe.calc_ut(jd, pid, flags)
            lon = res[0][0] % 360
            spd = res[0][3]
            si  = int(lon / 30) % 12
            planets.append({
                "name":       name,
                "longitude":  round(lon, 4),
                "signIndex":  si,
                "signName":   RASHI[si],
                "degInSign":  round(lon % 30, 4),
                "retrograde": bool(spd < 0),
            })
        except Exception:
            planets.append({
                "name": name, "longitude": 0.0, "signIndex": 0,
                "signName": RASHI[0], "degInSign": 0.0, "retrograde": False,
            })

    # Rahu (Mean Node) always retrograde; Ketu = opposite
    try:
        res  = swe.calc_ut(jd, swe.MEAN_NODE, flags)
        rahu = res[0][0] % 360
        ketu = (rahu + 180.0) % 360
        rsi  = int(rahu / 30) % 12
        ksi  = int(ketu / 30) % 12
        planets.append({"name":"Rahu","longitude":round(rahu,4),"signIndex":rsi,
                        "signName":RASHI[rsi],"degInSign":round(rahu%30,4),"retrograde":True})
        planets.append({"name":"Ketu","longitude":round(ketu,4),"signIndex":ksi,
                        "signName":RASHI[ksi],"degInSign":round(ketu%30,4),"retrograde":True})
    except Exception:
        planets.append({"name":"Rahu","longitude":0.0,"signIndex":0,
                        "signName":RASHI[0],"degInSign":0.0,"retrograde":True})
        planets.append({"name":"Ketu","longitude":180.0,"signIndex":6,
                        "signName":RASHI[6],"degInSign":0.0,"retrograde":True})

    return jsonify({
        "planets":   planets,
        "timestamp": now.isoformat() + "Z",
    })


@app.route("/api/kp_kundli", methods=["POST"])
def kp_kundli():
    """
    KP (Krishnamurti Paddhati) calculation.
    Input JSON: same schema as /api/kundli
    (day, month, year, hour, minute, ampm, lat, lon, tz, name, place)
    Returns: cusps, planets, significations, ayanamsa
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    required = ["day", "month", "year", "hour", "minute", "ampm", "lat", "lon", "tz"]
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        result = calculate_kp(data)
        return jsonify(result)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


@app.route("/api/ask", methods=["POST"])
def ask_route():
    """
    AI Ask engine — rule-based astrology question analysis.
    Body: { question, kundli, lang, replyIdx }
    Returns: { text, topic, confidence }
    """
    data = request.get_json(force=True, silent=True) or {}
    question  = data.get("question", "")
    kundli    = data.get("kundli")
    lang      = data.get("lang", "en")
    reply_idx = int(data.get("replyIdx", 0))

    if not question:
        return jsonify({"error": "question is required"}), 400

    try:
        result = process_ask(question, kundli, lang, reply_idx)
        return jsonify(result)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ── Serve React frontend in production ────────────────────────────────────────
_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "cosmic-lens", "dist", "public")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    from flask import send_from_directory
    # Never intercept /api/* — those are handled by explicit routes above
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    full = os.path.join(_DIST, path)
    if path and os.path.isfile(full):
        return send_from_directory(_DIST, path)
    index = os.path.join(_DIST, "index.html")
    if os.path.isfile(index):
        return send_from_directory(_DIST, "index.html")
    return jsonify({"error": "Frontend not built"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
