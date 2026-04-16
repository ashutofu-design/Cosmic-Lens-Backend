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
import urllib.parse
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kundli_engine import calculate_kundli
from kp_engine import calculate_kp
from ask_engine import process_ask
from dosh_engine import analyze_doshas
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


@app.route("/api/geocode", methods=["GET"])
def geocode():
    import urllib.request, json as _json
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=6&addressdetails=1"
    req = urllib.request.Request(url, headers={
        "User-Agent": "CosmicLens/1.0",
        "Accept-Language": "en",
    })
    with urllib.request.urlopen(req, timeout=8) as resp:
        rows = _json.loads(resp.read())
    results = []
    for x in rows:
        lat = float(x.get("lat", 0))
        lon = float(x.get("lon", 0))
        tz = round((lon / 15) * 2) / 2
        label = ", ".join(x.get("display_name", "").split(",")[:3])
        results.append({"label": label, "lat": lat, "lon": lon, "tz": tz})
    return jsonify(results)


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


@app.route("/api/auth/mobile", methods=["POST"])
def mobile_login():
    data   = request.get_json(force=True, silent=True) or {}
    mobile = (data.get("mobile") or "").strip().replace(" ", "").replace("-", "")

    # Keep only digits
    digits = "".join(c for c in mobile if c.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        return jsonify({"error": "Valid mobile number enter karein (7–15 digits)"}), 400

    pseudo_email = f"mobile:{digits}@cosmic.local"
    user = User.query.filter_by(email=pseudo_email).first()

    if user:
        user.last_active = datetime.utcnow()
        if not user.api_key:
            user.api_key = secrets.token_hex(32)
        db.session.commit()
        return jsonify(user.to_dict())
    else:
        # Auto-create account
        last4 = digits[-4:]
        user = User(
            name=f"User {last4}",
            email=pseudo_email,
            password=None,
            api_key=secrets.token_hex(32),
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201


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


@app.route("/api/dosh-analysis", methods=["POST"])
def dosh_analysis():
    """
    Full 9-dosh Vedic analysis.
    Body: { planets: [...], nakshatra: str }
    planets: [{ name, house, longitude, sign, retrograde }, ...]
    Returns: { total_dosh, active_count, mild_count, none_count, dosh_list }
    """
    data = request.get_json(force=True, silent=True) or {}
    planets   = data.get("planets")
    nakshatra = data.get("nakshatra", "")

    if not planets or not isinstance(planets, list):
        return jsonify({"error": "planets array is required"}), 400

    try:
        result = analyze_doshas(planets, nakshatra)
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


# ── Numerology API ────────────────────────────────────────────────────────────

PYTHAGOREAN = {
    'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,
    'j':1,'k':2,'l':3,'m':4,'n':5,'o':6,'p':7,'q':8,'r':9,
    's':1,'t':2,'u':3,'v':4,'w':5,'x':6,'y':7,'z':8,
}
VOWELS = set('aeiou')

def _reduce(n):
    """Reduce to single digit, preserving 11, 22, 33 as master numbers."""
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n

def _digit_sum(s):
    return sum(int(c) for c in str(s) if c.isdigit())

def _num_life_path(day, month, year):
    return _reduce(_reduce(_digit_sum(day)) + _reduce(_digit_sum(month)) + _reduce(_digit_sum(year)))

def _num_destiny(name):
    cleaned = [c.lower() for c in name if c.isalpha()]
    return _reduce(sum(PYTHAGOREAN.get(c, 0) for c in cleaned))

def _num_soul(name):
    cleaned = [c.lower() for c in name if c.isalpha() and c.lower() in VOWELS]
    return _reduce(sum(PYTHAGOREAN.get(c, 0) for c in cleaned))

def _num_personality(name):
    cleaned = [c.lower() for c in name if c.isalpha() and c.lower() not in VOWELS]
    return _reduce(sum(PYTHAGOREAN.get(c, 0) for c in cleaned))

def _num_maturity(lp, destiny):
    return _reduce(lp + destiny)

def _num_personal_year(day, month, year=None):
    from datetime import datetime
    y = year or datetime.now().year
    return _reduce(_digit_sum(day) + _digit_sum(month) + _digit_sum(y))

def _num_personal_month(day, month, year=None):
    from datetime import datetime
    now = datetime.now()
    y   = year or now.year
    py  = _num_personal_year(day, month, y)
    return _reduce(py + now.month)

NUM_INTERP = {
    1:  {"title":"Sun — Leadership","planet":"Surya","lucky_numbers":"1, 10, 19, 28","lucky_color":"Gold / Orange","traits":["Ambitious","Independent","Pioneering","Creative"],"desc":"You are a natural-born leader with strong willpower. Driven by originality and independence, you chart your own course.","career":"Politics, Management, Entrepreneurship, Military","love":"You need a partner who gives you space and admires your strength.","strength":"Determination, Confidence","weakness":"Ego, Stubbornness","remedy":"Offer water to the rising Sun every morning; donate wheat on Sundays."},
    2:  {"title":"Moon — Intuition","planet":"Chandra","lucky_numbers":"2, 11, 20, 29","lucky_color":"White / Silver","traits":["Sensitive","Cooperative","Diplomatic","Emotional"],"desc":"You are a peacemaker with deep emotional intelligence. You thrive in partnerships and bring harmony wherever you go.","career":"Counseling, Arts, Music, Nursing","love":"You are a romantic and devoted partner who values emotional depth.","strength":"Empathy, Patience","weakness":"Over-sensitivity, Indecisiveness","remedy":"Observe Monday fasts; donate white cloth or rice to temples."},
    3:  {"title":"Jupiter — Creativity","planet":"Guru","lucky_numbers":"3, 12, 21, 30","lucky_color":"Yellow / Purple","traits":["Joyful","Expressive","Optimistic","Social"],"desc":"You radiate enthusiasm and creativity. Gifted with communication skills, you inspire others and bring joy to every room.","career":"Writing, Entertainment, Teaching, Arts","love":"You are a playful, fun-loving partner who keeps the spark alive.","strength":"Optimism, Creativity","weakness":"Scattered focus, Over-indulgence","remedy":"Worship Lord Vishnu on Thursdays; donate yellow sweets or turmeric."},
    4:  {"title":"Rahu — Stability","planet":"Rahu","lucky_numbers":"4, 13, 22, 31","lucky_color":"Electric Blue / Grey","traits":["Disciplined","Hardworking","Systematic","Reliable"],"desc":"You are the builder — disciplined, dependable, and devoted. You create solid foundations through hard work and consistency.","career":"Engineering, Architecture, Finance, Army","love":"You are a loyal and stable partner who values commitment above all.","strength":"Discipline, Reliability","weakness":"Rigidity, Resistance to change","remedy":"Donate blue clothes on Saturdays; chant Rahu beej mantra on Saturdays."},
    5:  {"title":"Mercury — Freedom","planet":"Budha","lucky_numbers":"5, 14, 23","lucky_color":"Green / Light Blue","traits":["Adventurous","Versatile","Quick-witted","Energetic"],"desc":"You are a free spirit — versatile, curious, and always on the move. You excel wherever quick thinking and adaptability are needed.","career":"Journalism, Travel, Sales, Technology","love":"You need an adventurous partner who can keep up with your energy.","strength":"Adaptability, Intelligence","weakness":"Restlessness, Inconsistency","remedy":"Worship Lord Ganesha on Wednesdays; donate green vegetables to the needy."},
    6:  {"title":"Venus — Love","planet":"Shukra","lucky_numbers":"6, 15, 24","lucky_color":"Pink / Light Blue","traits":["Loving","Responsible","Artistic","Nurturing"],"desc":"You are a caretaker with a deep capacity for love and beauty. Harmony, family, and service define your life's purpose.","career":"Medicine, Teaching, Art, Interior Design","love":"You are a devoted, family-first partner with a romantic heart.","strength":"Compassion, Responsibility","weakness":"Over-sacrifice, Jealousy","remedy":"Worship Goddess Lakshmi on Fridays; donate sweets and white flowers."},
    7:  {"title":"Ketu — Wisdom","planet":"Ketu","lucky_numbers":"7, 16, 25","lucky_color":"Violet / Indigo","traits":["Analytical","Spiritual","Introspective","Mysterious"],"desc":"You are the seeker — drawn to deep knowledge, spirituality, and the mysteries of existence. Solitude fuels your wisdom.","career":"Research, Philosophy, Science, Spiritual work","love":"You seek a deep intellectual and spiritual connection with your partner.","strength":"Insight, Wisdom","weakness":"Aloofness, Over-analysis","remedy":"Worship Lord Shiva on Mondays; donate black sesame seeds on Saturdays."},
    8:  {"title":"Saturn — Power","planet":"Shani","lucky_numbers":"8, 17, 26","lucky_color":"Dark Blue / Black","traits":["Powerful","Ambitious","Strategic","Enduring"],"desc":"You carry Saturn's weight — immense power and patience to overcome every obstacle. Great material success awaits your perseverance.","career":"Business, Banking, Politics, Administration","love":"You are an intense, protective partner; loyalty is non-negotiable for you.","strength":"Determination, Resilience","weakness":"Materialism, Control issues","remedy":"Light a mustard oil lamp on Saturdays; donate black sesame to Lord Shani."},
    9:  {"title":"Mars — Compassion","planet":"Mangal","lucky_numbers":"9, 18, 27","lucky_color":"Red / Crimson","traits":["Courageous","Humanitarian","Passionate","Idealistic"],"desc":"You are the warrior with a heart of gold — courageous in battles, compassionate in service. You fight for truth and justice.","career":"Medicine, Law, Military, Social service","love":"You are a passionate, fiercely devoted partner who loves with full intensity.","strength":"Courage, Generosity","weakness":"Impulsiveness, Short temper","remedy":"Worship Lord Hanuman on Tuesdays; donate red lentils and jaggery."},
    11: {"title":"Master Number — Illumination","planet":"Chandra + Surya","lucky_numbers":"11, 29, 2","lucky_color":"Silver / Gold","traits":["Intuitive","Inspirational","Visionary","Sensitive"],"desc":"You carry the Master Number 11 — a highly spiritual vibration of illumination and inspiration. You are here to uplift humanity.","career":"Spiritual leadership, Art, Healing, Counseling","love":"You seek a soulmate-level connection — deep, spiritual, and transformative.","strength":"Intuition, Inspiration","weakness":"Anxiety, Over-idealism","remedy":"Meditate at sunrise; chant 'Om Namah Shivaya' 108 times daily."},
    22: {"title":"Master Builder — Manifestation","planet":"Shani + Surya","lucky_numbers":"22, 4","lucky_color":"Deep Blue / Gold","traits":["Visionary","Disciplined","Powerful","Practical"],"desc":"You carry Master Number 22 — the most powerful of all numbers. You can manifest grand visions into concrete reality.","career":"Architecture, Global business, Politics, Philanthropy","love":"You are a dedicated, visionary partner building a lasting legacy together.","strength":"Vision, Execution","weakness":"Perfectionism, Overwhelm","remedy":"Practice deep meditation; donate to orphanages on Saturdays."},
    33: {"title":"Master Teacher — Divine Love","planet":"Guru + Shukra","lucky_numbers":"33, 6","lucky_color":"Gold / Pink","traits":["Selfless","Nurturing","Creative","Enlightened"],"desc":"You carry Master Number 33 — the vibration of divine love and healing. You are a rare teacher meant to uplift all of humanity.","career":"Healing arts, Spiritual teaching, Creative leadership","love":"You love unconditionally, serving your partner and family with pure devotion.","strength":"Unconditional love, Wisdom","weakness":"Martyrdom, Self-neglect","remedy":"Serve the underprivileged selflessly; light a ghee diya daily in your home."},
}

PERSONAL_YEAR_THEME = {
    1:"New beginnings, fresh start, plant seeds for 9 years ahead",
    2:"Partnerships, patience, cooperation — relationships bloom",
    3:"Creativity, expression, joy — time to shine and communicate",
    4:"Hard work, foundation-building, discipline is key",
    5:"Change, freedom, travel — embrace the unexpected",
    6:"Family, responsibility, service — nurture your loved ones",
    7:"Reflection, spirituality, inner work — seek deeper truth",
    8:"Power, ambition, finance — your efforts get rewarded",
    9:"Completion, release, endings — prepare for a new cycle",
    11:"Spiritual awakening, high sensitivity, divine guidance",
    22:"Master year of manifestation — think big, build big",
    33:"Year of deep love and teaching — serve with a full heart",
}

@app.route("/api/numerology/basic", methods=["POST"])
def numerology_basic():
    data  = request.get_json(force=True, silent=True) or {}
    name  = (data.get("name") or "").strip()
    day   = int(data.get("day", 0))
    month = int(data.get("month", 0))
    year  = int(data.get("year", 0))

    if not name or not day or not month or not year:
        return jsonify({"error": "name, day, month, year are required"}), 400

    lp   = _num_life_path(day, month, year)
    dest = _num_destiny(name)
    soul = _num_soul(name)
    py   = _num_personal_year(day, month)
    pm   = _num_personal_month(day, month)

    def interp(n):
        return NUM_INTERP.get(n, NUM_INTERP[9])

    return jsonify({
        "life_path":    {"number": lp,   **interp(lp)},
        "destiny":      {"number": dest, **interp(dest)},
        "soul_urge":    {"number": soul, **interp(soul)},
        "personal_year":{"number": py,   "theme": PERSONAL_YEAR_THEME.get(py, "")},
        "personal_month":{"number": pm,  "theme": PERSONAL_YEAR_THEME.get(pm, "")},
    })


@app.route("/api/numerology/advanced", methods=["POST"])
def numerology_advanced():
    data  = request.get_json(force=True, silent=True) or {}
    name  = (data.get("name") or "").strip()
    day   = int(data.get("day", 0))
    month = int(data.get("month", 0))
    year  = int(data.get("year", 0))

    if not name or not day or not month or not year:
        return jsonify({"error": "name, day, month, year are required"}), 400

    lp      = _num_life_path(day, month, year)
    dest    = _num_destiny(name)
    soul    = _num_soul(name)
    pers    = _num_personality(name)
    mat     = _num_maturity(lp, dest)
    py      = _num_personal_year(day, month)

    def interp(n):
        return NUM_INTERP.get(n, NUM_INTERP[9])

    # Name correction: check if destiny number is compatible with life path
    compat = abs(lp - dest) <= 2 or (lp + dest) in (11, 22, 33)
    name_note = ("Your name number is well-aligned with your life path." if compat
                 else f"Adjusting your name numerologically to {lp} or {(lp+1) if lp<9 else 1} "
                      f"could enhance your life path energy.")

    # Love compat: even + even or odd + odd = strong; 1+9 = karmic
    love_pairs = {
        (1,1):"Both are leaders — respect each other's independence.",
        (1,2):"Perfect — leader meets diplomat. Very harmonious.",
        (1,9):"Karmic bond — passionate but challenging. Requires work.",
        (2,6):"Most romantic pairing — deep, devoted, loving.",
        (3,5):"Adventurous and fun — never a dull moment together.",
        (4,8):"Power couple — disciplined builders of a great life.",
        (5,7):"Intellectual soulmates — endless depth and curiosity.",
        (6,9):"Deeply compassionate pair — love of service unites you.",
        (7,11):"Spiritual twin flames — rare and profound connection.",
    }
    lp_min, lp_max = (min(lp,dest), max(lp,dest))
    love_msg = love_pairs.get((lp_min, lp_max), f"Life Path {lp} and Destiny {dest} combine to form a unique and evolving bond. Growth is the theme of your relationships.")

    return jsonify({
        "life_path":     {"number": lp,   **interp(lp)},
        "destiny":       {"number": dest, **interp(dest)},
        "soul_urge":     {"number": soul, **interp(soul)},
        "personality":   {"number": pers, **interp(pers)},
        "maturity":      {"number": mat,  **interp(mat)},
        "personal_year": {"number": py,   "theme": PERSONAL_YEAR_THEME.get(py, "")},
        "name_correction":{"compatible": compat, "note": name_note},
        "love_compatibility": {"message": love_msg},
        "challenges": {
            "first":  f"Life Path {lp} challenge: {interp(lp)['weakness']}",
            "main":   f"Destiny {dest} challenge: overcome {interp(dest)['weakness']}",
            "remedy": f"{interp(lp)['remedy']}",
        },
    })


# ── Serve React frontend in production ────────────────────────────────────────
_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "cosmic-lens", "dist", "public")

@app.route("/api/daily_alerts", methods=["POST"])
def daily_alerts():
    """
    Generate personalized 4-day daily alert cards for the Cosmic Lens app.
    POST body: {
      "lagna_deg": float,        # ascendant degree (sidereal)
      "nakshatra": str,          # natal moon nakshatra name
      "mahadasha": str,          # current mahadasha lord
      "antardasha": str,         # current antardasha lord (optional)
      "moon_lon": float          # natal moon longitude (optional, for fallback)
    }
    Returns: { "days": [ { label, emoji, date, energy, score, insight,
                           tags, lucky_color, lucky_number, moon_sign,
                           moon_nakshatra, dasha_note } ] }
    """
    import swisseph as swe
    from datetime import datetime, timedelta
    import math, random

    data       = request.get_json(force=True, silent=True) or {}
    lagna_deg  = float(data.get("lagna_deg", 0))
    birth_nak  = data.get("nakshatra", "")
    mahadasha  = data.get("mahadasha", "")
    antardasha = data.get("antardasha", "")

    RASHI_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    RASHI_HI = ["मेष","वृषभ","मिथुन","कर्क","सिंह","कन्या",
                "तुला","वृश्चिक","धनु","मकर","कुम्भ","मीन"]

    NAKSHATRAS = [
        "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
        "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
        "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
        "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
    ]
    # Tara names and base scores (index 0–8 cycled)
    TARA_INFO = [
        ("Janma", 50),      # 0 — mixed
        ("Sampat", 82),     # 1 — good
        ("Vipat", 25),      # 2 — challenging
        ("Kshema", 78),     # 3 — good
        ("Pratyari", 32),   # 4 — challenging
        ("Sadhaka", 90),    # 5 — very good
        ("Naidhana", 10),   # 6 — very challenging
        ("Mitra", 75),      # 7 — good
        ("Ati-Mitra", 95),  # 8 — excellent
    ]

    # Moon house scores (relative to lagna)
    HOUSE_SCORES = {1:70,2:52,3:58,4:72,5:82,6:35,7:65,8:28,9:80,10:75,11:85,12:32}

    # Benefic/malefic dasha lords
    BENEFIC = {"Jupiter","Venus","Moon","Mercury"}
    MALEFIC  = {"Saturn","Mars","Rahu","Ketu","Sun"}

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    lagna_rashi  = int(lagna_deg / 30) % 12
    birth_nak_idx = NAKSHATRAS.index(birth_nak) if birth_nak in NAKSHATRAS else -1

    # Dasha lord nature bonus/penalty
    dasha_bonus = 0
    if mahadasha in BENEFIC:   dasha_bonus += 8
    elif mahadasha in MALEFIC: dasha_bonus -= 8
    if antardasha in BENEFIC:  dasha_bonus += 4
    elif antardasha in MALEFIC:dasha_bonus -= 4

    # Insight message pools
    GOOD_INSIGHTS = [
        ("Aaj ka din aapke liye shubh hai. Naye kaam shuru karne ka sahi samay hai.", "Today is auspicious. Start new ventures with confidence."),
        ("Moon ki position aapke liye anukool hai. Career mein progress milegi.", "The Moon's placement favors you today — career progress is indicated."),
        ("Jupiter ka ashirvaad aaj aap par hai. Important decisions le sakte hain.", "Jupiter blesses your day. Take important decisions with clarity."),
        ("Aaj aapki communication skills peak par hain. Meetings aur negotiations sahi rahenge.", "Communication is sharp today. Meetings and negotiations will go your way."),
        ("Positive energy ka pravaah ho raha hai. Health aur relationship dono achhe rahenge.", "Positive planetary flow today. Health and relationships are both favorable."),
        ("Aaj luck aapka saath dega. Naye log milenge jo helpful honge.", "Luck is on your side. You may meet helpful people who open new doors."),
        ("Moon Tara aapke janma nakshatra se saadhaka stithi mein hai. Yeh din safal rahega.", "The Moon forms a Sadhaka Tara with your natal star — success is favored today."),
    ]
    NEUTRAL_INSIGHTS = [
        ("Din theek thak rahega. Bade faisale avoid karein, routine mein focus rakhein.", "A steady, moderate day. Focus on routine tasks; avoid major decisions."),
        ("Aaj mixed energy hai. Kuch kaam ban jayenge, kuch mein thodi der lagegi.", "Mixed energy today. Some tasks will flow easily, others need patience."),
        ("Moon transit bata raha hai ki aaj average energy hai. Stability maintain rakhein.", "Moon's transit indicates average energy. Maintain stability and stay grounded."),
        ("Aaj ka din neutral hai. Planning aur preparation ke liye achha samay hai.", "A neutral day — ideal for planning, organizing, and preparation."),
        ("Na zyada anukool, na pratikal. Steady progress possible hai.", "Neither highly favorable nor challenging. Steady progress is possible."),
    ]
    CHALLENGING_INSIGHTS = [
        ("Aaj thoda mentally heavy feel ho sakta hai. Important decisions postpone karein.", "Today may feel mentally heavy. Postpone important decisions if possible."),
        ("Moon ki position aaj dushtana mein hai. Patience rakhein, reactivity se bachein.", "Moon is in a dushtana position today. Stay patient and avoid reactive decisions."),
        ("Shani ya Mangal ka prabhav hai aaj. Arguments aur accidents se bachein.", "Saturn or Mars influence today. Avoid arguments and be careful while traveling."),
        ("Aaj energy low rahegi. Rest aur reflection ke liye sahi samay hai.", "Energy is lower today. Rest, reflect, and avoid overcommitting."),
        ("Vipat Tara chal raha hai — thoda sochsamajh kar kadam rakhein.", "Vipat Tara is active — tread carefully and think before acting."),
        ("Naidhana Tara ka prabhav hai. Major new beginnings aaj avoid karein.", "Naidhana Tara is active. Avoid major new beginnings or financial commitments today."),
    ]

    LUCKY_COLORS = {
        "good":        [("Peela","#eab308"),("Hari","#22c55e"),("Neela","#3b82f6"),("Sona","#f59e0b")],
        "neutral":     [("Safed","#e2e8f0"),("Violet","#8b5cf6"),("Peach","#fb923c"),("Sky","#7dd3fc")],
        "challenging": [("Laal","#ef4444"),("Maroon","#991b1b"),("Bhura","#92400e"),("Slate","#64748b")],
    }
    LUCKY_NUMBERS = {
        "good":        [[1,9],[3,6],[2,7],[5,9],[1,4]],
        "neutral":     [[2,5],[4,8],[3,7],[6,9],[1,6]],
        "challenging": [[4,7],[8,2],[3,9],[5,8],[2,6]],
    }

    TAG_POOLS = {
        "good":        [["💰 Opportunity","✨ Positive"],["💰 Opportunity","❤️ Favorable"],["✨ Positive","💡 Growth"]],
        "neutral":     [["🔄 Mixed","💡 Planning"],["🔄 Mixed","⚖️ Balance"],["💡 Reflection","⚖️ Balance"]],
        "challenging": [["⚠️ Warning","❤️ Emotional"],["⚠️ Caution","🧘 Rest"],["⚠️ Warning","🔄 Introspect"]],
    }

    DAY_META = [
        {"offset": -1, "label": "Previous Day", "label_hi": "कल था",      "emoji": "⏮️"},
        {"offset":  0, "label": "Today",         "label_hi": "आज",         "emoji": "📍"},
        {"offset":  1, "label": "Tomorrow",      "label_hi": "कल",         "emoji": "⏭️"},
        {"offset":  2, "label": "Day After",     "label_hi": "परसों",      "emoji": "🔮"},
    ]

    today_utc = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    results   = []

    for meta in DAY_META:
        day = today_utc + timedelta(days=meta["offset"])
        jd  = swe.julday(day.year, day.month, day.day, 12.0)

        # ── Moon position ──
        moon_res    = swe.calc_ut(jd, swe.MOON, flags)
        moon_lon    = moon_res[0][0] % 360
        moon_rashi  = int(moon_lon / 30) % 12
        moon_nak_idx= int(moon_lon / (360/27)) % 27
        moon_nak    = NAKSHATRAS[moon_nak_idx]

        # ── Tara (nakshatra relationship) ──
        tara_score = 50
        if birth_nak_idx >= 0:
            tara_pos   = ((moon_nak_idx - birth_nak_idx + 27) % 27) % 9
            tara_name, tara_score = TARA_INFO[tara_pos]
        else:
            tara_name = "Unknown"

        # ── Moon house relative to lagna ──
        moon_house  = (moon_rashi - lagna_rashi + 12) % 12 + 1
        house_score = HOUSE_SCORES.get(moon_house, 50)

        # ── Key transit aspects (Saturn & Mars) ──
        try:
            saturn_res = swe.calc_ut(jd, swe.SATURN, flags)
            saturn_lon = saturn_res[0][0] % 360
            saturn_rashi = int(saturn_lon / 30) % 12
        except Exception:
            saturn_rashi = -1

        try:
            mars_res   = swe.calc_ut(jd, swe.MARS, flags)
            mars_lon   = mars_res[0][0] % 360
            mars_rashi = int(mars_lon / 30) % 12
        except Exception:
            mars_rashi = -1

        try:
            jupiter_res   = swe.calc_ut(jd, swe.JUPITER, flags)
            jupiter_rashi = int(jupiter_res[0][0] % 360 / 30) % 12
        except Exception:
            jupiter_rashi = -1

        # Saturn 3rd, 7th, 10th aspect on moon sign → challenging
        saturn_aspect = False
        if saturn_rashi >= 0:
            rel = (moon_rashi - saturn_rashi + 12) % 12
            if rel in (2, 6, 9):  # Saturn 3rd/7th/10th aspect
                saturn_aspect = True

        # Mars 4th, 7th, 8th aspect on moon sign → warning
        mars_aspect = False
        if mars_rashi >= 0:
            rel = (moon_rashi - mars_rashi + 12) % 12
            if rel in (3, 6, 7):  # Mars aspects
                mars_aspect = True

        # Jupiter 5th, 7th, 9th aspect on moon sign → bonus
        jupiter_aspect = False
        if jupiter_rashi >= 0:
            rel = (moon_rashi - jupiter_rashi + 12) % 12
            if rel in (4, 6, 8):  # Jupiter aspects
                jupiter_aspect = True

        aspect_adj  = 0
        if saturn_aspect: aspect_adj -= 10
        if mars_aspect:   aspect_adj -= 8
        if jupiter_aspect:aspect_adj += 10

        # ── Composite score ──
        raw_score = (tara_score * 0.50 + house_score * 0.35 + 50 * 0.15)
        score     = int(max(5, min(98, raw_score + dasha_bonus + aspect_adj)))

        # ── Energy level ──
        if score >= 65:   energy_key = "good";        energy_label = "Good";        energy_color = "#22c55e"
        elif score >= 42: energy_key = "neutral";     energy_label = "Neutral";     energy_color = "#f59e0b"
        else:             energy_key = "challenging"; energy_label = "Challenging"; energy_color = "#ef4444"

        # ── Insight message ──
        seed = abs(hash(f"{day.date()}{birth_nak}{lagna_rashi}")) % 10000
        rng  = random.Random(seed)

        if energy_key == "good":
            pair = rng.choice(GOOD_INSIGHTS)
        elif energy_key == "neutral":
            pair = rng.choice(NEUTRAL_INSIGHTS)
        else:
            pair = rng.choice(CHALLENGING_INSIGHTS)

        # ── Dasha note ──
        dasha_note = ""
        if mahadasha:
            if mahadasha in BENEFIC:
                dasha_note = f"{mahadasha} Mahadasha — favorable planetary period active."
            else:
                dasha_note = f"{mahadasha} Mahadasha — exercise caution during this period."

        # ── Lucky color + number ──
        lc_list   = LUCKY_COLORS[energy_key]
        ln_list   = LUCKY_NUMBERS[energy_key]
        lc_name, lc_hex = rng.choice(lc_list)
        ln_pair   = rng.choice(ln_list)
        tags      = rng.choice(TAG_POOLS[energy_key])

        results.append({
            "offset":         meta["offset"],
            "label":          meta["label"],
            "label_hi":       meta["label_hi"],
            "emoji":          meta["emoji"],
            "date":           day.strftime("%Y-%m-%d"),
            "date_display":   day.strftime("%d %b"),
            "weekday":        day.strftime("%A"),
            "energy":         energy_label,
            "energy_color":   energy_color,
            "score":          score,
            "insight_hi":     pair[0],
            "insight_en":     pair[1],
            "moon_sign":      RASHI_EN[moon_rashi],
            "moon_sign_hi":   RASHI_HI[moon_rashi],
            "moon_house":     moon_house,
            "moon_nakshatra": moon_nak,
            "tara":           tara_name,
            "saturn_aspect":  saturn_aspect,
            "mars_aspect":    mars_aspect,
            "jupiter_aspect": jupiter_aspect,
            "tags":           tags,
            "lucky_color_name": lc_name,
            "lucky_color_hex":  lc_hex,
            "lucky_numbers":    ln_pair,
            "dasha_note":       dasha_note,
        })

    return jsonify({"days": results})


def _get_expo_tunnel_url():
    import glob, re, os
    # Read the live tunnel URL from the Metro bundler log
    for log_path in sorted(glob.glob("/tmp/logs/artifactscosmic-lens-mobile*.log"), reverse=True):
        try:
            with open(log_path, "r") as f:
                content = f.read()
            m = re.search(r"exp://[^\s\n]+", content)
            if m:
                return m.group(0).strip()
        except Exception:
            pass
    # Fallback: construct from Replit Expo domain
    expo_domain = os.environ.get("REPLIT_EXPO_DEV_DOMAIN", "")
    return f"exp://{expo_domain}" if expo_domain else ""


@app.route("/api/open")
def open_in_expo():
    expo_url = _get_expo_tunnel_url()
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Open Cosmic Lens</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      min-height: 100vh;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      padding: 24px;
    }}
    .card {{
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 24px;
      padding: 40px 32px;
      max-width: 360px;
      width: 100%;
      text-align: center;
    }}
    .logo {{ font-size: 56px; margin-bottom: 16px; }}
    h1 {{ color: #fff; font-size: 22px; font-weight: 700; margin-bottom: 8px; }}
    p {{ color: rgba(255,255,255,0.6); font-size: 14px; margin-bottom: 32px; line-height: 1.5; }}
    .btn {{
      display: block;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: #fff;
      text-decoration: none;
      font-size: 17px;
      font-weight: 700;
      padding: 18px 24px;
      border-radius: 16px;
      margin-bottom: 16px;
      letter-spacing: 0.3px;
    }}
    .url-box {{
      background: rgba(0,0,0,0.3);
      border-radius: 12px;
      padding: 12px 16px;
      margin-top: 20px;
    }}
    .url-label {{ color: rgba(255,255,255,0.4); font-size: 11px; margin-bottom: 4px; }}
    .url-text {{ color: rgba(255,255,255,0.7); font-size: 12px; word-break: break-all; }}
    .step {{ color: rgba(255,255,255,0.5); font-size: 12px; margin-top: 12px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">🔮</div>
    <h1>Cosmic Lens</h1>
    <p>Tap the button below to open the app directly in Expo Go on your phone.</p>
    <a class="btn" href="{expo_url}">✨ Open in Expo Go</a>
    <p class="step">Safari mein tap karein → Expo Go automatically open hoga</p>
    <div class="url-box">
      <div class="url-label">Direct URL</div>
      <div class="url-text">{expo_url}</div>
    </div>
  </div>
</body>
</html>"""
    from flask import Response
    return Response(html, mimetype="text/html")


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


@app.route("/api/qr")
def expo_qr():
    tunnel_url = ""
    try:
        import urllib.request, json as _json
        with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=2) as r:
            data = _json.loads(r.read())
            for t in data.get("tunnels", []):
                url = t.get("public_url", "")
                if url.startswith("http://"):
                    tunnel_url = url.replace("http://", "exp://")
                    break
    except Exception:
        pass
    if not tunnel_url:
        try:
            with open("/tmp/expo-tunnel-url", "r") as f:
                tunnel_url = f.read().strip()
        except Exception:
            pass

    status = "Tunnel ready" if tunnel_url else "Waiting for tunnel..."
    qr_section = ""
    if tunnel_url:
        qr_section = f"""
        <div id="qr"></div>
        <p style="font-family:monospace;font-size:14px;margin-top:12px;color:#a5b4fc;">{tunnel_url}</p>
        <p style="color:#64748b;font-size:12px;margin-top:4px;">Open Expo Go → tap the scan icon → scan this code</p>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
        <script>new QRCode(document.getElementById("qr"), {{text:"{tunnel_url}",width:256,height:256,colorDark:"#e2e8f0",colorLight:"#0f172a"}});</script>
        """
    else:
        qr_section = """
        <p style="color:#64748b;font-size:14px;">Starting tunnel — refresh in a few seconds...</p>
        <script>setTimeout(()=>location.reload(),3000);</script>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Cosmic Lens — Expo QR</title>
  <style>
    body{{margin:0;background:#0b1220;color:#e2e8f0;font-family:system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;gap:16px;}}
    h1{{font-size:20px;font-weight:700;color:#a5b4fc;margin:0;}}
    p{{margin:0;}}
    #qr canvas,#qr img{{border-radius:12px;padding:16px;background:#0f172a;border:2px solid #334155;}}
  </style>
</head>
<body>
  <h1>Cosmic Lens — Expo Go</h1>
  <p style="color:#64748b;font-size:13px;">{status}</p>
  {qr_section}
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html"}


@app.route("/api/kundli-milan", methods=["POST"])
def kundli_milan():
    """
    Accurate Ashtakoot Guna Milan using pyswisseph.
    Accepts two persons' birth details, computes Moon sidereal longitude
    for each via Swiss Ephemeris (Lahiri ayanamsa), then derives all
    8 koot scores and returns detailed written analysis.

    Body (JSON):
      p1: { name, day, month, year, hour, minute, ampm, lat, lon, tz }
      p2: { name, day, month, year, hour, minute, ampm, lat, lon, tz }
    """
    import swisseph as swe
    import math

    data = request.get_json(force=True, silent=True)
    if not data or "p1" not in data or "p2" not in data:
        return jsonify({"error": "Missing p1 or p2"}), 400

    # ── Nakshatra / Rashi tables ──────────────────────────────────────────────
    NAKSHATRAS = [
        "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
        "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
        "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
        "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha",
        "Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"
    ]
    RASHIS = [
        "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
    ]
    NAK_SIZE = 360.0 / 27.0   # 13.333… degrees per nakshatra

    def moon_longitude(p):
        """Return sidereal Moon longitude (Lahiri) for birth data dict p."""
        hour24 = p["hour"] % 12
        if p.get("ampm","AM").upper() == "PM":
            hour24 += 12
        hour_frac = hour24 + p.get("minute", 0) / 60.0
        # tz offset → UTC
        tz_offset = float(p.get("tz", 0))
        jd = swe.julday(p["year"], p["month"], p["day"], hour_frac - tz_offset)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        result, _ = swe.calc_ut(jd, swe.MOON, flags)
        return result[0] % 360.0, jd

    def mars_house(p, jd):
        """Return Mars house number (1-12) for birth data."""
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        mars_res, _ = swe.calc_ut(jd, swe.MARS, flags)
        mars_lon = mars_res[0] % 360.0
        ayanamsa = swe.get_ayanamsa_ut(jd)
        cusps, ascmc = swe.houses(jd, float(p["lat"]), float(p["lon"]), b'W')
        asc_sid = (ascmc[0] - ayanamsa + 360) % 360
        # Simple equal-house: house index
        rel = (mars_lon - asc_sid + 360) % 360
        return int(rel / 30) + 1

    def parse_person(p):
        """Return dict with nak_idx, rashi_idx, pada, manglik, name."""
        ml, jd = moon_longitude(p)
        nak_idx   = int(ml / NAK_SIZE) % 27
        pada      = int((ml % NAK_SIZE) / (NAK_SIZE / 4)) + 1
        rashi_idx = int(ml / 30) % 12
        mh        = mars_house(p, jd)
        manglik   = mh in [1, 4, 7, 8, 12]
        return {
            "name": p.get("name","Person"),
            "nak_idx": nak_idx,
            "nak_name": NAKSHATRAS[nak_idx],
            "pada": pada,
            "rashi_idx": rashi_idx,
            "rashi_name": RASHIS[rashi_idx],
            "moon_lon": ml,
            "manglik": manglik,
        }

    # ── 8 Koot calculation tables ────────────────────────────────────────────
    # Nadi (8 pts) — three types cycling per 9 nakshatras
    NADI = [0,1,2, 2,1,0, 0,1,2, 2,1,0, 0,1,2, 2,1,0, 0,1,2, 2,1,0, 0,1,2]
    NADI_N = ["Vata (Adi)","Pitta (Madhya)","Kapha (Antya)"]

    # Gana (6 pts)
    GANA = [0,1,2, 1,0,1, 0,0,2, 2,1,1, 0,2,0, 2,0,2, 2,1,1, 0,1,2, 1,1,0]
    GANA_N = ["Dev","Manushya","Raksha"]

    # Varna (1 pt) — by rashi
    VARNA = [1,2,3,0,1,2,3,0,1,2,3,0]  # Brahmin=0,Kshatriya=1,Vaishya=2,Shudra=3

    # Vasya (2 pts)
    def vasya_score(r1, r2):
        if r1 == r2: return 2
        groups = [[0,3,4],[1,6,7,9],[2,8],[5,10,11]]
        g1 = next(i for i,g in enumerate(groups) if r1 in g)
        g2 = next(i for i,g in enumerate(groups) if r2 in g)
        return 2 if g1 == g2 else 1

    # Tara (3 pts)
    def tara_score(n1, n2):
        fwd = ((n2 - n1 + 27) % 27) + 1
        rev = ((n1 - n2 + 27) % 27) + 1
        bad = {3,5,7}
        fwd_ok = (fwd % 9 or 9) not in bad
        rev_ok = (rev % 9 or 9) not in bad
        if fwd_ok and rev_ok: return 3
        if fwd_ok or rev_ok:  return 1.5
        return 0

    # Yoni (4 pts)
    YONI = [0,1,2,3,4,5,6,7,8,9,10,2,11,12,13,14,14,13,5,12,11,10,3,7,4,9,0]
    YONI_ENEMY = [(0,1),(2,3),(4,5),(6,7),(8,9),(10,11),(12,13),(14,0)]
    def yoni_score(n1, n2):
        y1,y2 = YONI[n1],YONI[n2]
        if y1==y2: return 4
        if any((y1==a and y2==b)or(y1==b and y2==a) for a,b in YONI_ENEMY): return 0
        return 2

    # Graha Maitri (5 pts) — rashi lord friendship
    RASHI_LORD = [2,5,3,1,0,3,5,2,4,6,6,4]   # 0=Sun,1=Moon,2=Mars,3=Merc,4=Jup,5=Ven,6=Sat
    PLN_FRIEND = [
        [1,2,2,1,2,0,0],[2,1,0,1,2,2,0],[2,0,1,1,2,0,2],
        [2,0,2,1,0,2,0],[2,1,2,1,1,0,0],[2,2,0,2,1,1,0],[0,0,2,2,2,0,1],
    ]
    def maitri_score(r1, r2):
        l1,l2 = RASHI_LORD[r1],RASHI_LORD[r2]
        t = PLN_FRIEND[l1][l2] + PLN_FRIEND[l2][l1]
        return 5 if t>=4 else 4 if t==3 else 3 if t==2 else 0

    # Bhakut (7 pts) — rashi gap
    def bhakut_score(r1, r2):
        d = abs(r1 - r2)
        bad = [(1,11),(4,8),(5,7)]
        if any(d==a or d==b for a,b in bad): return 0
        return 7

    try:
        pp1 = parse_person(data["p1"])
        pp2 = parse_person(data["p2"])
    except Exception as e:
        return jsonify({"error": f"Calculation failed: {str(e)}"}), 500

    n1,n2 = pp1["nak_idx"], pp2["nak_idx"]
    r1,r2 = pp1["rashi_idx"], pp2["rashi_idx"]

    nadi_sc   = 8 if NADI[n1]!=NADI[n2] else 0
    gana_sc_raw= GANA[n1],GANA[n2]
    g1,g2     = gana_sc_raw
    if g1==g2:   gana_sc=6
    elif {g1,g2}=={0,2}: gana_sc=1
    elif 2 in {g1,g2}:   gana_sc=0
    else:        gana_sc=6
    bhakut_sc = bhakut_score(r1,r2)
    maitri_sc = maitri_score(r1,r2)
    yoni_sc   = yoni_score(n1,n2)
    tara_sc   = tara_score(n1,n2)
    vasya_sc  = vasya_score(r1,r2)
    varna_sc  = 1 if VARNA[r1]<=VARNA[r2] else 0

    total = nadi_sc + gana_sc + bhakut_sc + maitri_sc + yoni_sc + tara_sc + vasya_sc + varna_sc
    manglik_dosh = pp1["manglik"] != pp2["manglik"]

    koots = [
        {"key":"nadi",   "label":"Nadi",         "score":nadi_sc,   "max":8,
         "detail": f"{NADI_N[NADI[n1]]} × {NADI_N[NADI[n2]]}" if nadi_sc==8 else f"Both {NADI_N[NADI[n1]]}",
         "bad": nadi_sc==0},
        {"key":"gana",   "label":"Gana",          "score":gana_sc,   "max":6,
         "detail": f"{GANA_N[g1]} + {GANA_N[g2]}",  "bad": gana_sc==0},
        {"key":"bhakut", "label":"Bhakut",        "score":bhakut_sc, "max":7,
         "detail": "Shubh" if bhakut_sc==7 else "Dosh present",  "bad": bhakut_sc==0},
        {"key":"maitri", "label":"Graha Maitri",  "score":maitri_sc, "max":5,
         "detail": "Friendly" if maitri_sc>=4 else "Neutral" if maitri_sc>=3 else "Hostile",
         "bad": maitri_sc<3},
        {"key":"yoni",   "label":"Yoni",          "score":yoni_sc,   "max":4,
         "detail": "Same Yoni" if yoni_sc==4 else "Moderate" if yoni_sc==2 else "Hostile Yoni",
         "bad": yoni_sc==0},
        {"key":"tara",   "label":"Tara",          "score":tara_sc,   "max":3,
         "detail": "Auspicious" if tara_sc==3 else "Moderate" if tara_sc>0 else "Inauspicious",
         "bad": tara_sc==0},
        {"key":"vasya",  "label":"Vasya",         "score":vasya_sc,  "max":2,
         "detail": "Strong" if vasya_sc==2 else "Moderate",  "bad": False},
        {"key":"varna",  "label":"Varna",         "score":varna_sc,  "max":1,
         "detail": "Matched" if varna_sc==1 else "Mismatched",  "bad": varna_sc==0},
    ]

    # ── Grade & written analysis ──────────────────────────────────────────────
    if   total>=32: grade_label,grade_col,grade_emoji = "Excellent Match","#22c55e","🌟"
    elif total>=27: grade_label,grade_col,grade_emoji = "Very Good Match","#4ade80","💚"
    elif total>=21: grade_label,grade_col,grade_emoji = "Average Match",  "#fbbf24","💛"
    elif total>=18: grade_label,grade_col,grade_emoji = "Below Average",  "#f97316","🧡"
    else:           grade_label,grade_col,grade_emoji = "Low Compatibility","#ef4444","❤️‍🩹"

    pct = round((total/36)*100)
    verdict = (
        "Stars align strongly. An exceptional and harmonious union." if total>=32 else
        "Very positive match. With love and respect, great potential ahead." if total>=27 else
        "Moderate match. Awareness and effort will help this bond grow." if total>=21 else
        "Challenging match. Remedies and guidance strongly recommended."
    )

    # Strengths
    strengths = []
    if nadi_sc==8:
        strengths.append("Different Nadi types create natural physical and emotional balance — a strong foundation for healthy children and long life together.")
    if gana_sc>=5:
        strengths.append(f"Gana harmony ({GANA_N[g1]} + {GANA_N[g2]}) shows your inner natures are well-matched — temperaments flow without friction in daily life.")
    if bhakut_sc==7:
        strengths.append(f"Bhakut is fully auspicious ({pp1['rashi_name']} – {pp2['rashi_name']}) — Rashi positions promote prosperity, family growth, and mutual welfare.")
    if maitri_sc>=4:
        strengths.append("Strong Graha Maitri — the lords of your Moon signs are friendly, ensuring deep mental compatibility and shared values.")
    if yoni_sc>=3:
        strengths.append("Yoni match indicates strong physical attraction and intimate compatibility — chemistry comes naturally.")
    if tara_sc==3:
        strengths.append("Tara Koot is fully auspicious — destiny favours this union; major life events tend to unfold positively.")
    if vasya_sc==2:
        strengths.append("Strong Vasya — you naturally support each other's decisions and growth without power struggles.")
    if not strengths:
        strengths.append("Every relationship has hidden strengths. Focus on shared values, communication, and mutual respect to discover yours.")

    # Challenges
    challenges = []
    if nadi_sc==0:
        challenges.append(f"Nadi Dosha detected — both partners share {NADI_N[NADI[n1]]} constitutional energy. This may affect health and progeny; Maha Mrityunjaya Jaap (1.25 lakh) is recommended.")
    if gana_sc==0:
        challenges.append(f"Major Gana mismatch ({GANA_N[g1]}–{GANA_N[g2]}) — fundamentally different temperaments. Conscious patience and spiritual practice together are essential.")
    if bhakut_sc==0:
        challenges.append(f"Bhakut Dosha present ({pp1['rashi_name']}–{pp2['rashi_name']}) — may bring tension in finances, family, or progeny. Navagraha Shanti or Vivah Yog puja can help.")
    if maitri_sc<3:
        challenges.append("Graha Maitri is weak — the planetary lords of your Rashis are not naturally friendly, requiring effort to build mutual understanding.")
    if yoni_sc==0:
        challenges.append("Hostile Yoni — instinctive natures tend to clash. Open communication about needs and boundaries is crucial for harmony.")
    if manglik_dosh:
        challenges.append("Manglik Dosha imbalance — only one partner is Manglik. Kumbh Vivah ceremony or Mangal Shanti puja before marriage is strongly advised.")
    if not challenges:
        challenges.append("No major doshas detected — this is a smooth match astrologically. Continue nurturing it with care and devotion.")

    # Marriage Outlook
    marriage_outlook = (
        "This is one of the highest-rated matches in Vedic astrology. Marriage between you is likely to bring lasting joy, prosperity, healthy progeny, and spiritual growth. Family harmony and emotional security will be natural. Sacred rituals and joint pujas will further elevate this beautiful connection." if total>=32 else
        "A very promising marriage match. With love, communication, and respect for each other's space, this relationship can blossom into a deeply fulfilling lifelong partnership. Minor differences smooth over through shared rituals like daily prayers and gratitude practice." if total>=27 else
        "An average match that requires conscious effort. Focus on understanding each other's emotional needs, practice patience, and consider remedies like Vivah Yog rituals. With dedication, this bond grows stronger over time." if total>=21 else
        "A challenging match in classical Vedic terms. Strongly recommend consulting a qualified Jyotishi before marriage. Remedies like Kumbh Vivah, Maha Mrityunjaya Jaap, and Navagraha Shanti can significantly improve outcomes."
    )

    compatibility_insight = (
        f"Out of the maximum 36 Gunas in Ashtakoot Milan, your union scores {total} ({pct}% match). "
        f"In Vedic tradition, scores above 18 are acceptable for marriage, above 24 are good, and above 28 are excellent. "
        f"Your match falls in the \"{grade_label.lower()}\" range — "
        + (
            "the cosmic forces strongly support your union and the foundation is solid."
            if total>=24 else
            "while some astrological challenges exist, sincere effort and remedies can transform this relationship."
        )
        + f" Nakshatra of {pp1['name']}: {pp1['nak_name']} (Pada {pp1['pada']}, {pp1['rashi_name']}). "
        + f"Nakshatra of {pp2['name']}: {pp2['nak_name']} (Pada {pp2['pada']}, {pp2['rashi_name']})."
    )

    return jsonify({
        "p1": {
            "name": pp1["name"],
            "nakshatra": pp1["nak_name"],
            "pada": pp1["pada"],
            "rashi": pp1["rashi_name"],
            "manglik": pp1["manglik"],
        },
        "p2": {
            "name": pp2["name"],
            "nakshatra": pp2["nak_name"],
            "pada": pp2["pada"],
            "rashi": pp2["rashi_name"],
            "manglik": pp2["manglik"],
        },
        "total": total,
        "max": 36,
        "percent": pct,
        "grade": {"label": grade_label, "color": grade_col, "emoji": grade_emoji},
        "verdict": verdict,
        "manglik_dosh": manglik_dosh,
        "koots": koots,
        "analysis": {
            "compatibility_insight": compatibility_insight,
            "strengths": strengths,
            "challenges": challenges,
            "marriage_outlook": marriage_outlook,
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
