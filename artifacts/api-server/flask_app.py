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
import json
import secrets
import urllib.parse
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kundli_engine import calculate_kundli
from kp_engine import calculate_kp
from ask_engine import process_ask
from openai_helper import ai_ask, ai_ask_stream, vastu_scan, is_available as openai_available
from dosh_engine import analyze_doshas
from energy_engine import calculate_energy
from database import db, init_db
from models import User, Kundli, Profile

app = Flask(__name__)
import logging as _logging
app.logger.setLevel(_logging.INFO)
if not app.logger.handlers:
    _h = _logging.StreamHandler()
    _h.setLevel(_logging.INFO)
    _h.setFormatter(_logging.Formatter("[%(levelname)s] %(message)s"))
    app.logger.addHandler(_h)
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

# ── Public legal page (no auth required) ──────────────────────────────────────

LEGAL_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>Legal - Cosmic Lens</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 860px; margin: 0 auto; padding: 32px 20px 80px; color: #1a1a2e; line-height: 1.65; background: #fafafa; }
  h1 { font-size: 32px; margin: 0 0 8px; color: #6d28d9; }
  h2 { font-size: 22px; margin-top: 40px; padding-top: 18px; border-top: 2px solid #e5e7eb; color: #4c1d95; }
  h3 { font-size: 17px; margin-top: 22px; color: #374151; }
  .lead { color: #6b7280; margin-bottom: 24px; }
  .toc { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px 22px; margin-bottom: 28px; }
  .toc a { display: block; padding: 4px 0; color: #6d28d9; text-decoration: none; font-weight: 500; }
  .toc a:hover { text-decoration: underline; }
  .highlight { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 14px 18px; margin: 18px 0; border-radius: 6px; }
  .contact { background: #ede9fe; border-radius: 8px; padding: 14px 18px; margin-top: 12px; }
  ul { padding-left: 22px; }
  li { margin-bottom: 6px; }
  footer { margin-top: 60px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 13px; text-align: center; }
  footer a { color: #6d28d9; margin: 0 8px; }
  a { color: #6d28d9; }
</style>
</head>
<body>

<h1>Legal &amp; Policies</h1>
<p class=\"lead\">Cosmic Lens — Vedic Astrology Platform. Last updated: April 2026.</p>
<p style=\"background:#ede9fe;border-left:4px solid #6d28d9;padding:12px 16px;border-radius:6px;margin:0 0 24px;color:#4c1d95;font-weight:500\">
  This page is publicly accessible and applies to all users of Cosmic Lens services.
</p>

<div class=\"toc\">
  <strong>Contents</strong>
  <a href=\"#privacy\">1. Privacy Policy</a>
  <a href=\"#terms\">2. Terms of Service</a>
  <a href=\"#refund\">3. Refund &amp; Cancellation Policy</a>
  <a href=\"#disclaimer\">4. Disclaimer</a>
  <a href=\"#contact\">5. Contact Us</a>
</div>

<!-- ────────────────────────── PRIVACY ────────────────────────── -->
<h2 id=\"privacy\">1. Privacy Policy</h2>
<p>Cosmic Lens (&quot;we&quot;, &quot;our&quot;, &quot;us&quot;) respects your privacy. This policy explains what data we collect, how we use it, and your rights.</p>

<h3>Information We Collect</h3>
<ul>
  <li><strong>Account data:</strong> mobile number (verified via OTP), name, language preference.</li>
  <li><strong>Birth details:</strong> date, time, and place of birth — used solely to compute your kundli.</li>
  <li><strong>Payment data:</strong> processed by Cashfree Payments. We never see or store your card or UPI credentials.</li>
  <li><strong>Usage data:</strong> app interactions, feature usage, and crash logs to improve the service.</li>
</ul>

<h3>How We Use Your Information</h3>
<ul>
  <li>Generate your personalized Vedic kundli, dasha, and predictions.</li>
  <li>Process subscription payments and manage your plan.</li>
  <li>Send OTP for authentication (via Firebase Phone Authentication).</li>
  <li>Improve the app and detect fraud or abuse.</li>
</ul>

<h3>Data Sharing</h3>
<p>We do <strong>not</strong> sell your personal data. We share only with:</p>
<ul>
  <li><strong>Cashfree Payments</strong> — for processing transactions.</li>
  <li><strong>Google Firebase</strong> — for sending one-time passwords (Phone Auth).</li>
  <li><strong>Government authorities</strong> — only when legally required.</li>
</ul>

<h3>Data Retention &amp; Deletion</h3>
<p>You may delete your account at any time from <em>Settings → Delete Account</em>. Upon deletion, your personal data is removed within 30 days. Anonymized analytics may be retained.</p>

<h3>Security</h3>
<p>All data is transmitted over HTTPS. Passwords (where applicable) are hashed. Payment processing uses PCI-DSS compliant gateways.</p>

<!-- ────────────────────────── TERMS ────────────────────────── -->
<h2 id=\"terms\">2. Terms of Service</h2>
<p>By using Cosmic Lens, you agree to these terms.</p>

<h3>Eligibility</h3>
<ul>
  <li>You must be at least 18 years old.</li>
  <li>The service is currently available only to users in India.</li>
  <li>You must provide accurate birth details for kundli generation.</li>
</ul>

<h3>Subscription Plans</h3>
<ul>
  <li><strong>Free:</strong> basic kundli &amp; daily horoscope.</li>
  <li><strong>Basic:</strong> ₹199 per month, recurring monthly.</li>
  <li><strong>Pro:</strong> ₹499 per month, recurring monthly.</li>
</ul>
<p>All prices are in Indian Rupees (INR) and inclusive of applicable taxes.</p>

<h3>Acceptable Use</h3>
<ul>
  <li>Do not abuse, reverse engineer, or scrape the service.</li>
  <li>Do not impersonate others or share your account.</li>
  <li>We may suspend accounts that violate these terms.</li>
</ul>

<h3>Intellectual Property</h3>
<p>All content, algorithms, and designs in Cosmic Lens are owned by us. Your kundli output is for personal use only.</p>

<!-- ────────────────────────── REFUND ────────────────────────── -->
<h2 id=\"refund\">3. Refund &amp; Cancellation Policy</h2>

<div class=\"highlight\">
  <strong>Quick summary:</strong> Cancel anytime. Refunds may be granted within 7 days of purchase if the service has not been meaningfully used, subject to review.
</div>

<h3>Cancellation</h3>
<ul>
  <li>You may cancel your subscription at any time from <em>Settings → Subscription → Cancel</em>.</li>
  <li>Cancellation stops future renewals immediately. You retain access until the end of your current billing cycle.</li>
  <li>No cancellation fee is charged.</li>
</ul>

<h3>Refund Eligibility</h3>
<ul>
  <li><strong>Refunds may be granted within 7 days of purchase if the service has not been meaningfully used, subject to review.</strong></li>
  <li><strong>Partial refund:</strong> Not provided. Refunds are either full or none, based on review.</li>
  <li><strong>Renewal charges:</strong> Once a renewal is processed, that billing cycle is non-refundable. Cancel before the next billing date to avoid charges.</li>
</ul>

<h3>How to Request a Refund</h3>
<p>Email <a href=\"mailto:support@cosmiclens.app\">support@cosmiclens.app</a> with:</p>
<ul>
  <li>Your registered mobile number</li>
  <li>Order ID (visible on your subscription page)</li>
  <li>Reason for refund</li>
</ul>
<p>We respond within <strong>2 business days</strong> and process approved refunds within <strong>5–7 business days</strong> to the original payment method via Cashfree.</p>

<h3>Failed / Duplicate Payments</h3>
<p>If you were charged but the subscription did not activate, or you were charged twice for the same order, we will refund automatically within 7 business days. Contact support if not received.</p>

<!-- ────────────────────────── DISCLAIMER ────────────────────────── -->
<h2 id=\"disclaimer\">4. Disclaimer</h2>

<div class=\"highlight\">
  <strong>Important:</strong> Cosmic Lens is for guidance and informational purposes only. Astrological predictions are not a substitute for professional medical, legal, financial, or psychological advice.
</div>

<ul>
  <li>We do not guarantee the accuracy, completeness, or outcomes of any prediction.</li>
  <li>Predictions are generated using traditional Vedic astrology algorithms based on the birth details you provide. Accuracy depends entirely on the correctness of those inputs.</li>
  <li>Any decisions you take based on the content (career, marriage, finance, health) are your sole responsibility.</li>
  <li>Always consult qualified professionals — doctors, lawyers, financial advisors — for matters in their respective fields.</li>
  <li>The app does not promote superstition or discrimination on the basis of caste, religion, or gender.</li>
</ul>

<!-- ────────────────────────── CONTACT ────────────────────────── -->
<h2 id=\"contact\">5. Contact Us</h2>
<div class=\"contact\">
  <p style=\"margin:4px 0\"><strong>Cosmic Lens Support</strong></p>
  <p style=\"margin:4px 0\">Email: <a href=\"mailto:support@cosmiclens.app\">support@cosmiclens.app</a></p>
  <p style=\"margin:4px 0\">For refund requests, mention &quot;Refund&quot; in the subject line.</p>
  <p style=\"margin:4px 0\">Response time: within 2 business days.</p>
</div>

<footer>
  <div>
    <a href=\"#privacy\">Privacy</a> ·
    <a href=\"#terms\">Terms</a> ·
    <a href=\"#refund\"><strong>Refund Policy</strong></a> ·
    <a href=\"#disclaimer\">Disclaimer</a>
  </div>
  <div style=\"margin-top:10px\">© 2026 Cosmic Lens. All rights reserved.</div>
</footer>

</body>
</html>"""

@app.route("/legal", methods=["GET"])
@app.route("/legal/", methods=["GET"])
@app.route("/privacy", methods=["GET"])
@app.route("/terms", methods=["GET"])
@app.route("/refund", methods=["GET"])
@app.route("/refund-policy", methods=["GET"])
@app.route("/disclaimer", methods=["GET"])
def legal_page():
    from flask import Response
    return Response(LEGAL_HTML, mimetype="text/html; charset=utf-8")

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
    import urllib.request, urllib.error, json as _json
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])

    def _fetch(provider_url: str, timeout: int = 12):
        req = urllib.request.Request(provider_url, headers={
            "User-Agent": "CosmicLens/1.0 (support@cosmiclens.app)",
            "Accept-Language": "en",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _json.loads(resp.read())

    # Primary: Open-Meteo Geocoding API (fast, reliable, no API key, no rate limit issues).
    try:
        fb_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(q)}&count=6&language=en&format=json"
        fb = _fetch(fb_url, timeout=8)
        fb_rows = fb.get("results") or []
        results = []
        for x in fb_rows:
            lat = float(x.get("latitude", 0))
            lon = float(x.get("longitude", 0))
            tz = round((lon / 15) * 2) / 2
            parts = [x.get("name"), x.get("admin1"), x.get("country")]
            label = ", ".join(p for p in parts if p)
            if label:
                results.append({"label": label, "lat": lat, "lon": lon, "tz": tz})
        if results:
            return jsonify(results)
    except Exception as e:
        app.logger.warning(f"geocode primary (open-meteo) failed for '{q}': {e}")

    # Fallback: Nominatim (OSM) — slower but broader coverage.
    try:
        nom_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=6&addressdetails=1"
        rows = _fetch(nom_url, timeout=8)
        results = []
        for x in rows:
            lat = float(x.get("lat", 0))
            lon = float(x.get("lon", 0))
            tz = round((lon / 15) * 2) / 2
            label = ", ".join(x.get("display_name", "").split(",")[:3])
            if label:
                results.append({"label": label, "lat": lat, "lon": lon, "tz": tz})
        return jsonify(results)
    except Exception as e:
        app.logger.warning(f"geocode fallback (nominatim) failed for '{q}': {e}")
        return jsonify([]), 200  # Return empty rather than 500, so client shows "no results"


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — Phone OTP via Firebase Phone Authentication.
# OTP send + confirm happens entirely on the client (Firebase SDK).
# Backend only verifies the resulting Firebase ID token below.
# Legacy email/password and MSG91 OTP endpoints have been removed.
# ─────────────────────────────────────────────────────────────────────────────


@app.route("/api/auth/firebase-verify", methods=["POST"])
def firebase_verify_route():
    """
    Production-grade phone-OTP login powered by Firebase Phone Authentication.

    Body: { "id_token": "<Firebase ID token from client SDK>", "name?": "..." }

    Flow:
      1. Client (Expo) calls Firebase signInWithPhoneNumber → user enters OTP →
         confirmation.confirm(code) → client receives a short-lived ID token.
      2. Client POSTs that ID token here.
      3. Backend verifies signature + expiry with Firebase Admin SDK.
      4. Extracts the verified phone number, finds-or-creates the local User row,
         and returns the standard auth payload (id, api_key, subscription, ...).

    On success: 200 (existing user) or 201 (new user).
    On failure: 401 with { ok: false, error: "..." }.
    """
    from subscription_helper import auto_start_trial_on_signup, subscription_status
    from firebase_admin_helper import verify_id_token, FirebaseAuthError
    from sqlalchemy.exc import IntegrityError

    data     = request.get_json(force=True, silent=True) or {}
    id_token = (data.get("id_token") or "").strip()
    name     = (data.get("name") or "").strip()[:200]

    if not id_token:
        return jsonify({"ok": False, "error": "Missing id_token"}), 400

    try:
        decoded = verify_id_token(id_token)
    except FirebaseAuthError as e:
        app.logger.warning("[firebase-verify] %s", e)
        return jsonify({"ok": False, "error": str(e)}), 401

    phone_e164 = (decoded.get("phone_number") or "").strip()
    if not phone_e164 or not phone_e164.startswith("+"):
        return jsonify({
            "ok":    False,
            "error": "Token has no verified phone number",
        }), 401

    # India-only policy: keep parity with the previous OTP flow.
    if not phone_e164.startswith("+91"):
        return jsonify({
            "ok":    False,
            "error": "Only Indian mobile numbers are supported (+91).",
        }), 403

    cc_norm = "91"
    ph_norm = phone_e164[3:]  # 10-digit local part after +91

    # Find or create user by phone (canonical identity).
    user   = User.query.filter_by(phone=phone_e164).first()
    is_new = False
    if not user:
        is_new = True
        last4 = ph_norm[-4:] if len(ph_norm) >= 4 else ph_norm
        user = User(
            name         = name or f"User {last4}",
            phone        = phone_e164,
            country_code = cc_norm,
            api_key      = secrets.token_hex(32),
        )
        db.session.add(user)
        try:
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            user = User.query.filter_by(phone=phone_e164).first()
            is_new = False
            if not user:
                return jsonify({
                    "ok":    False,
                    "error": "User creation race; please retry",
                }), 500
        if is_new:
            try:
                auto_start_trial_on_signup(user)
            except Exception:
                app.logger.exception("[firebase-verify] auto_start_trial failed")
    else:
        if not user.api_key:
            user.api_key = secrets.token_hex(32)
        user.last_active = datetime.utcnow()
        if name and (not user.name or user.name.startswith("User ")):
            user.name = name

    db.session.commit()

    payload = user.to_dict()
    payload["subscription"] = subscription_status(user)
    payload["is_new_user"]  = is_new
    payload["ok"]           = True
    return jsonify(payload), (201 if is_new else 200)


@app.route("/api/auth/demo", methods=["POST"])
def demo_login_route():
    """Idempotent demo user — for testing only.
    Returns a real backend user with valid id + api_key so payment & quota flows work.
    """
    from subscription_helper import subscription_status
    from datetime import timedelta as _td
    DEMO_PHONE = "+919999000001"
    user = User.query.filter_by(phone=DEMO_PHONE).first()
    is_new = False
    if not user:
        is_new = True
        user = User(
            name         = "Demo User",
            phone        = DEMO_PHONE,
            country_code = "91",
            api_key      = secrets.token_hex(32),
        )
        db.session.add(user)
        db.session.flush()
    else:
        if not user.api_key:
            user.api_key = secrets.token_hex(32)
        user.last_active = datetime.utcnow()

    # Demo user always gets full Pro — for testing every paid feature end-to-end.
    user.is_pro      = True
    user.plan        = "pro"
    user.plan_expiry = datetime.utcnow() + _td(days=365 * 10)
    db.session.commit()
    payload = user.to_dict()
    payload["subscription"] = subscription_status(user)
    payload["is_new_user"]  = is_new
    return jsonify(payload), 200


@app.route("/api/auth/signup", methods=["POST"])
@app.route("/api/auth/login",  methods=["POST"])
@app.route("/api/auth/mobile", methods=["POST"])
@app.route("/api/auth/google", methods=["POST"])
def _legacy_auth_gone():
    return jsonify({
        "error":   "endpoint_removed",
        "message": "Login ab sirf mobile OTP se hota hai. App update karein.",
    }), 410


# ─────────────────────────────────────────────────────────────────────────────
# SUBSCRIPTION endpoints (single source of truth: subscription_helper.py)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/subscription/status", methods=["GET"])
def subscription_status_route():
    """Returns the user's effective plan, trial state, daily quota, prices.
    Anonymous (no user_id) → returns DEFAULT free-plan shape.
    Authenticated → requires matching X-API-Key for that user_id (prevents IDOR)."""
    from subscription_helper import subscription_status
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify(subscription_status(None))

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key or user.api_key != api_key:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify(subscription_status(user))


@app.route("/api/subscription/start-trial", methods=["POST"])
def start_trial_route():
    """Begin the 7-day free trial for a user (one-time)."""
    from subscription_helper import start_trial, subscription_status
    data    = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id")

    user = User.query.get(user_id) if user_id else None
    if not user:
        return jsonify({"ok": False, "error": "User not found"}), 404

    # Mandatory api-key check (prevents trial fraud / IDOR)
    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key or user.api_key != api_key:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    res = start_trial(user)
    if not res.get("ok"):
        return jsonify(res), 400

    return jsonify({
        "ok":           True,
        "expires_at":   res["expires_at"],
        "subscription": subscription_status(user),
    })


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

@app.route("/api/user/<int:user_id>/language", methods=["GET", "PUT"])
def user_language_pref(user_id):
    """Get or set the user's sticky preferred reply language.

    GET  → { preferred_language: "en"|"hi"|"hn"|null }
    PUT  → body { preferred_language: "en"|"hi"|"hn"|null }
           Setting null reverts to per-question auto-detection.
    """
    user, err = get_authed_user(user_id)
    if err:
        return err
    if request.method == "GET":
        return jsonify({"preferred_language": user.preferred_language})

    data = request.get_json(force=True, silent=True) or {}
    raw = data.get("preferred_language", None)
    if raw is None or (isinstance(raw, str) and raw.strip().lower() in {"", "auto", "null"}):
        user.preferred_language = None
    else:
        v = str(raw).strip().lower()
        if v not in {"en", "hi", "hn"}:
            return jsonify({"error": "preferred_language must be one of: en, hi, hn, null"}), 400
        user.preferred_language = v
    db.session.commit()
    return jsonify({"preferred_language": user.preferred_language})


@app.route("/api/user/<int:user_id>/kundli", methods=["GET"])
def get_user_kundli(user_id):
    """Get saved kundli + user profile (including subscription plan) for a user."""
    user, err = get_authed_user(user_id)
    if err: return err
    kundli_data = None
    if user.kundli:
        import json
        k = user.kundli
        d = k.to_dict()
        if k.chart_data:
            try: d["chart_data"] = json.loads(k.chart_data)
            except Exception: pass
        kundli_data = d
    return jsonify({"kundli": kundli_data, "user": user.to_dict()})


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


# ── Multi-profile cloud sync ───────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT DELETION  (Play Store / App Store mandatory)
# Permanently removes the user and all related personal data.
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/user/<int:user_id>/delete", methods=["POST", "DELETE"])
def delete_user_account(user_id):
    """Permanently delete a user and all related data (kundlis, profiles).
    Requires X-API-Key matching the user. Idempotent: returns 200 even if
    already deleted."""
    # Idempotent: if the user no longer exists, treat any request bearing
    # an X-API-Key header as already-deleted (200) so retries after network
    # ambiguity succeed. Wrong/missing key on a NON-existent user is also
    # treated as success — no data is leaked either way.
    api_key = request.headers.get("X-API-Key", "").strip()
    user    = User.query.get(user_id)
    if not user:
        return jsonify({
            "ok":      True,
            "message": "Account already deleted",
            "note":    "No further action required.",
        }), 200
    if not api_key or user.api_key != api_key:
        return jsonify({"error": "Unauthorized — invalid API key"}), 401

    # Confirmation phrase required (mobile sends "DELETE")
    body         = request.get_json(silent=True) or {}
    confirmation = (body.get("confirm") or "").strip().upper()
    if confirmation != "DELETE":
        return jsonify({
            "error": "Confirmation required. Send {\"confirm\":\"DELETE\"} to proceed.",
        }), 400

    deleted_email = user.email
    try:
        # 1) Delete kundlis (no CASCADE on this FK)
        Kundli.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        # 2) Profiles cascade automatically via ondelete="CASCADE"
        Profile.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        # 3) Delete the user row itself
        db.session.delete(user)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Deletion failed: {exc}"}), 500

    return jsonify({
        "ok":      True,
        "message": "Account permanently deleted",
        "email":   deleted_email,
        "note":    "Personal data has been erased. Tax invoices may be retained for 7 years per Indian law.",
    })


RECENTLY_DELETED_HOURS = 24


def _purge_expired_deleted(user_id: int) -> None:
    """Hard-delete soft-deleted profiles older than the 24-hr restore window."""
    from datetime import timedelta as _td
    cutoff = datetime.utcnow() - _td(hours=RECENTLY_DELETED_HOURS)
    expired = Profile.query.filter(
        Profile.user_id == user_id,
        Profile.deleted_at.isnot(None),
        Profile.deleted_at < cutoff,
    ).all()
    for row in expired:
        db.session.delete(row)
    if expired:
        db.session.commit()


@app.route("/api/user/<int:user_id>/profiles", methods=["GET"])
def list_user_profiles(user_id):
    """Return every ACTIVE profile saved by this user (excludes Recently Deleted)."""
    user, err = get_authed_user(user_id)
    if err: return err

    _purge_expired_deleted(user_id)

    rows = (Profile.query
            .filter_by(user_id=user_id, deleted_at=None)
            .order_by(Profile.is_primary.desc(), Profile.created_at.asc())
            .all())
    primary_id = next((r.client_id for r in rows if r.is_primary), (rows[0].client_id if rows else None))
    return jsonify({
        "profiles":         [r.to_dict() for r in rows],
        "primaryProfileId": primary_id,
    })


@app.route("/api/user/<int:user_id>/profiles/deleted", methods=["GET"])
def list_deleted_profiles(user_id):
    """Recently Deleted (last 24 hrs) — restorable without quota cost."""
    user, err = get_authed_user(user_id)
    if err: return err

    _purge_expired_deleted(user_id)

    rows = (Profile.query
            .filter(Profile.user_id == user_id, Profile.deleted_at.isnot(None))
            .order_by(Profile.deleted_at.desc())
            .all())
    return jsonify({"profiles": [r.to_dict() for r in rows]})


@app.route("/api/user/<int:user_id>/profiles/<client_id>/restore", methods=["POST"])
def restore_user_profile(user_id, client_id):
    """Restore a soft-deleted profile (within 24 hrs)."""
    from datetime import timedelta as _td
    user, err = get_authed_user(user_id)
    if err: return err

    row = Profile.query.filter_by(user_id=user_id, client_id=client_id).first()
    if not row or row.deleted_at is None:
        return jsonify({"ok": False, "error": "Profile not found in Recently Deleted"}), 404

    if row.deleted_at < datetime.utcnow() - _td(hours=RECENTLY_DELETED_HOURS):
        # Window has elapsed — purge and reject
        db.session.delete(row)
        db.session.commit()
        return jsonify({"ok": False, "error": "Restore window expired"}), 410

    row.deleted_at = None
    db.session.commit()
    return jsonify({"ok": True, "profile": row.to_dict()})


@app.route("/api/user/<int:user_id>/profiles/sync", methods=["POST"])
def sync_user_profiles(user_id):
    """Bulk upsert — client sends full ACTIVE profile list + primaryId.
    Removed-from-list profiles are SOFT-deleted (24-hr Recently Deleted window).
    Body: { profiles: [{id, name, gender, relation, birthData, kundli}], primaryProfileId: str }
    """
    user, err = get_authed_user(user_id)
    if err: return err
    import json as _json
    from models import compute_birth_key

    _purge_expired_deleted(user_id)

    data = request.get_json(force=True, silent=True) or {}
    incoming = data.get("profiles") or []
    primary_id = data.get("primaryProfileId")

    incoming_ids = {p.get("id") for p in incoming if p.get("id")}
    existing = {r.client_id: r for r in Profile.query.filter_by(user_id=user_id).all()}

    now = datetime.utcnow()

    # SOFT-delete profiles that disappeared from the active list (skip rows
    # already soft-deleted so we don't extend their restore window).
    for cid, row in existing.items():
        if cid not in incoming_ids and row.deleted_at is None:
            row.deleted_at = now

    # Upsert (also auto-restores any matching soft-deleted row by clearing deleted_at)
    for p in incoming:
        cid = p.get("id")
        if not cid: continue
        row = existing.get(cid)
        if not row:
            row = Profile(user_id=user_id, client_id=cid)
            db.session.add(row)
        row.name       = (p.get("name") or "")[:200]
        row.gender     = (p.get("gender") or "")[:20]
        row.relation   = (p.get("relation") or "")[:50]
        row.is_primary = (cid == primary_id)
        bd             = p.get("birthData")
        row.birth_data = _json.dumps(bd) if bd else None
        row.chart_data = _json.dumps(p.get("kundli")) if p.get("kundli") else None
        row.birth_key  = compute_birth_key(bd) if bd else None
        row.deleted_at = None  # incoming = active

    db.session.commit()
    rows = (Profile.query
            .filter_by(user_id=user_id, deleted_at=None)
            .order_by(Profile.is_primary.desc(), Profile.created_at.asc())
            .all())
    return jsonify({
        "profiles":         [r.to_dict() for r in rows],
        "primaryProfileId": next((r.client_id for r in rows if r.is_primary), (rows[0].client_id if rows else None)),
    })


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
    from subscription_helper import consume_kundli, effective_plan, can_generate_kundli
    from models import compute_birth_key
    import json as _json

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    required = ["day", "month", "year", "hour", "minute", "ampm", "lat", "lon", "tz", "name", "place"]
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    user_id = data.get("user_id")
    user    = None
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key or user.api_key != api_key:
            return jsonify({"error": "Unauthorized"}), 401

        # ── Per-user dedup: same DOB/time/place → return cached chart, NO quota cost ──
        birth_key = compute_birth_key(data)
        if birth_key:
            cached = (Profile.query
                      .filter_by(user_id=user.id, birth_key=birth_key, deleted_at=None)
                      .filter(Profile.chart_data.isnot(None))
                      .first())
            if not cached:
                # Backfill legacy profiles (rows that have chart_data but null birth_key
                # because they predate the dedup feature). Cheap one-time scan per user.
                legacy = (Profile.query
                          .filter_by(user_id=user.id, birth_key=None, deleted_at=None)
                          .filter(Profile.birth_data.isnot(None))
                          .all())
                if legacy:
                    for r in legacy:
                        try:
                            bd = _json.loads(r.birth_data)
                            r.birth_key = compute_birth_key(bd)
                        except Exception:
                            r.birth_key = ""
                    db.session.commit()
                    cached = (Profile.query
                              .filter_by(user_id=user.id, birth_key=birth_key, deleted_at=None)
                              .filter(Profile.chart_data.isnot(None))
                              .first())
            if cached:
                try:
                    chart = _json.loads(cached.chart_data)
                    if isinstance(chart, dict):
                        chart["cached"]    = True
                        chart["cached_id"] = cached.client_id
                        return jsonify(chart)
                except Exception:
                    pass  # corrupt cache → fall through to fresh compute

        # ── Quota check (only when no cache hit) ──
        check = can_generate_kundli(user)
        if not check["allowed"]:
            return jsonify({
                "error":            "daily_kundli_limit_reached",
                "message":          f"Aaj ka {check['limit']} kundli ka limit poora ho gaya. Pro upgrade karein for unlimited.",
                "quota":            {"used": check["used"], "limit": check["limit"]},
                "plan":             effective_plan(user),
                "upgrade_required": True,
            }), 402

    try:
        result = calculate_kundli(data)
        # Consume quota ONLY after a successful fresh calculation. The atomic
        # consume can still fail under heavy concurrency (another request used
        # the last slot between our pre-check and now) — in that case we must
        # honor the hard limit and reject this response.
        if user:
            quota = consume_kundli(user)
            if not quota.get("allowed"):
                return jsonify({
                    "error":            "daily_kundli_limit_reached",
                    "message":          f"Aaj ka {quota['limit']} kundli ka limit poora ho gaya. Pro upgrade karein for unlimited.",
                    "quota":            {"used": quota["used"], "limit": quota["limit"]},
                    "plan":             effective_plan(user),
                    "upgrade_required": True,
                }), 402
            result["quota"]  = {"used": quota["used"], "limit": quota["limit"]}
            result["cached"] = False
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/energy/today", methods=["GET", "POST"])
def energy_today():
    """
    Daily Energy Score (0-100) using weighted Vedic formula:
        Dasha 30% + Moon Transit 25% + Ashtakavarga 20%
        + Tara Bal 15% + Aspect/Strength 10%

    Auth modes:
      • Pass `user_id` (query or JSON body) + X-API-Key header → loads
        the user's saved kundli from DB.
      • Or POST JSON body with `kundli` (full chart_data) → stateless,
        no auth needed.

    Optional `date=YYYY-MM-DD` query/body for back-dated runs.
    """
    import json as _json
    import swisseph as swe
    from datetime import datetime as _dt

    body = request.get_json(force=True, silent=True) or {}
    date_str = (request.args.get("date") or body.get("date") or "").strip()

    # ── Resolve target date ──────────────────────────────────────────────
    try:
        if date_str:
            day = _dt.strptime(date_str, "%Y-%m-%d").replace(hour=12)
        else:
            day = _dt.utcnow()
    except ValueError:
        return jsonify({"error": "date must be YYYY-MM-DD"}), 400

    date_iso = day.strftime("%Y-%m-%d")

    # ── Resolve user kundli ──────────────────────────────────────────────
    kundli_dict = body.get("kundli") or body.get("chart_data")
    if not kundli_dict:
        uid_raw = request.args.get("user_id") or body.get("user_id")
        if not uid_raw:
            return jsonify({"error": "Provide user_id (with X-API-Key) or kundli body"}), 400
        try:
            user_id = int(uid_raw)
        except (TypeError, ValueError):
            return jsonify({"error": "user_id must be an integer"}), 400

        user, err = get_authed_user(user_id)
        if err:
            return err
        if not user.kundli or not user.kundli.chart_data:
            return jsonify({"error": "No kundli saved for this user"}), 404
        try:
            kundli_dict = _json.loads(user.kundli.chart_data)
        except Exception:
            return jsonify({"error": "Saved kundli is corrupted"}), 500

    # ── Compute today's moon (sidereal) ──────────────────────────────────
    jd = swe.julday(day.year, day.month, day.day,
                    day.hour + day.minute / 60.0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    moon_lon = swe.calc_ut(jd, swe.MOON, flags)[0][0] % 360.0

    today_moon = {
        "longitude":      round(moon_lon, 4),
        "rashiIndex":     int(moon_lon / 30) % 12,
        "nakshatraIndex": int(moon_lon / (360 / 27)) % 27,
    }

    # ── Run engine ───────────────────────────────────────────────────────
    result = calculate_energy(kundli_dict, today_moon, date_iso=date_iso)
    if "error" in result:
        return jsonify(result), 400

    result["today_moon"] = today_moon
    return jsonify(result)


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
    Full Vedic transit engine with sign-based aspects, Sade Sati detection,
    and per-domain impact scoring.

    Request body:
      {
        "dates": ["YYYY-MM-DD", ...],           -- required, max 12
        "natal": {                              -- optional; omit for positions-only
          "moon_sign":          int (0-11),
          "pd_planet":          str,
          "pd_planet_sign":     int (0-11),
          "lagna_sign":         int (0-11),
          "domain_house_signs": {
            "career": int, "finance": int,
            "relationship": int, "health": int
          }
        }
      }

    Response per date entry:
      {
        "date":          str,
        "positions":     {planet: longitude_float | null, ...},
        "domain_impact": {"career":int, "finance":int,
                          "relationship":int, "health":int},  -- only if natal given
        "reasons":       [str, ...],                           -- only if natal given
        "sade_sati":     bool,                                 -- only if natal given
        "error":         null | str
      }
    """
    import swisseph as swe
    import logging

    logger = logging.getLogger(__name__)

    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception as exc:
        logger.error("Transit API: JSON parse failure: %s", exc)
        return jsonify({"error": "Invalid JSON body", "results": []}), 400

    dates = data.get("dates", [])
    if not dates or not isinstance(dates, list):
        return jsonify({"error": "Provide 'dates' as a list of YYYY-MM-DD strings", "results": []}), 400

    DOMAINS = ["career", "finance", "relationship", "health"]

    # per-domain natal context: supports divisional-chart overrides (D9/D10) so
    # relationship is judged on Navamsha signs and career on Dashamsha signs.
    # Shape: {domain: {"pd_sign":0-11, "house_sign":0-11, "lagna_sign":0-11, "chart":"D1|D9|D10"}}
    natal = data.get("natal")
    domain_ctx = None
    if natal:
        try:
            moon_sign   = int(natal["moon_sign"]) % 12
            pd_planet   = str(natal.get("pd_planet", ""))
            lagna_sign  = int(natal["lagna_sign"]) % 12      # D1 lagna, for reason labels

            raw_ctx = natal.get("domain_context")
            if isinstance(raw_ctx, dict):
                domain_ctx = {}
                for d in DOMAINS:
                    dc = raw_ctx.get(d) or {}
                    domain_ctx[d] = {
                        "pd_sign":    (int(dc["pd_sign"])    % 12) if dc.get("pd_sign")    is not None else None,
                        "house_sign": (int(dc["house_sign"]) % 12) if dc.get("house_sign") is not None else None,
                        "lagna_sign": (int(dc["lagna_sign"]) % 12) if dc.get("lagna_sign") is not None else lagna_sign,
                        "chart":      str(dc.get("chart", "D1")).upper(),
                    }
                # legacy flat fields not required in this path
                pd_sign = None
            else:
                # legacy flat payload — synthesize domain_ctx so everything is D1
                pd_sign      = int(natal["pd_planet_sign"]) % 12
                raw_dhs      = natal.get("domain_house_signs", {}) or {}
                domain_ctx   = {}
                for d in DOMAINS:
                    hs = raw_dhs.get(d)
                    domain_ctx[d] = {
                        "pd_sign":    pd_sign,
                        "house_sign": (int(hs) % 12) if hs is not None else None,
                        "lagna_sign": lagna_sign,
                        "chart":      "D1",
                    }
        except (KeyError, TypeError, ValueError) as exc:
            logger.error("Transit API: bad natal payload: %s", exc)
            return jsonify({"error": f"Invalid natal data: {exc}", "results": []}), 400
    else:
        moon_sign = pd_planet = lagna_sign = None

    SIGN_NAMES = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    HOUSE_NAMES = {
        1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th",6:"6th",
        7:"7th",8:"8th",9:"9th",10:"10th",11:"11th",12:"12th",
    }

    def sign_to_house(sign: int, lagna: int) -> int:
        return (sign - lagna + 12) % 12 + 1

    def vedic_aspected_signs(planet_name: str, t_sign: int) -> list:
        sigs = [(t_sign + 6) % 12]                              # 7th — all planets
        if planet_name == "Jupiter":
            sigs += [(t_sign + 4) % 12, (t_sign + 8) % 12]    # 5th, 9th
        elif planet_name == "Saturn":
            sigs += [(t_sign + 2) % 12, (t_sign + 9) % 12]    # 3rd, 10th
        elif planet_name == "Mars":
            sigs += [(t_sign + 3) % 12, (t_sign + 7) % 12]    # 4th, 8th
        elif planet_name in ("Rahu", "Ketu"):
            sigs += [(t_sign + 4) % 12, (t_sign + 8) % 12]    # 5th, 9th
        return sigs

    def aspect_num(from_sign: int, to_sign: int) -> int:
        return (to_sign - from_sign + 12) % 12 + 1

    ASPECT_LABEL = {
        "Jupiter": {5: "5th trine", 7: "7th opposition", 9: "9th trine"},
        "Saturn":  {3: "3rd",       7: "7th opposition", 10: "10th"},
        "Mars":    {4: "4th",       7: "7th opposition",  8: "8th"},
        "Rahu":    {5: "5th",       7: "7th opposition",  9: "9th"},
        "Ketu":    {5: "5th",       7: "7th opposition",  9: "9th"},
    }

    DOMAIN_BIAS = {
        ("Jupiter","career"):        +10, ("Jupiter","finance"):       +8,
        ("Jupiter","relationship"):  +9,  ("Jupiter","health"):        +7,
        ("Saturn", "career"):        -9,  ("Saturn", "finance"):       -9,
        ("Saturn", "relationship"):  -8,  ("Saturn", "health"):        -11,
        ("Mars",   "career"):        +6,  ("Mars",   "finance"):       +3,
        ("Mars",   "relationship"):  -7,  ("Mars",   "health"):        -8,
        ("Venus",  "career"):        +3,  ("Venus",  "finance"):       +7,
        ("Venus",  "relationship"):  +9,  ("Venus",  "health"):        +4,
        ("Mercury","career"):        +5,  ("Mercury","finance"):       +5,
        ("Mercury","relationship"):  +3,  ("Mercury","health"):        +2,
        ("Sun",    "career"):        +6,  ("Sun",    "finance"):       +2,
        ("Sun",    "relationship"):  -2,  ("Sun",    "health"):        +3,
        ("Rahu",   "career"):        -4,  ("Rahu",   "finance"):       -6,
        ("Rahu",   "relationship"):  -8,  ("Rahu",   "health"):        -7,
        ("Ketu",   "career"):        -5,  ("Ketu",   "finance"):       -4,
        ("Ketu",   "relationship"):  -6,  ("Ketu",   "health"):        -6,
    }

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    planet_map = {
        "Jupiter": swe.JUPITER,
        "Saturn":  swe.SATURN,
        "Sun":     swe.SUN,
        "Mars":    swe.MARS,
        "Venus":   swe.VENUS,
        "Mercury": swe.MERCURY,
    }

    results = []

    for date_str in dates[:12]:
        entry = {"date": date_str, "positions": {}, "error": None}
        calc_error = False

        try:
            d  = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            jd = swe.julday(d.year, d.month, d.day, 12.0)
        except ValueError as exc:
            msg = f"Bad date format '{date_str}'"
            logger.warning("Transit API: %s — %s", msg, exc)
            entry["error"] = msg
            if natal:
                entry.update({"domain_impact": {k: 0 for k in DOMAINS}, "reasons": [], "sade_sati": False})
            results.append(entry)
            continue

        positions = {}
        for name, pid in planet_map.items():
            try:
                res = swe.calc_ut(jd, pid, flags)
                positions[name] = round(res[0][0] % 360, 3)
            except Exception as exc:
                logger.error("Transit API: swe.calc_ut failed for %s on %s: %s", name, date_str, exc)
                positions[name] = None
                calc_error = True

        try:
            rahu_res = swe.calc_ut(jd, swe.MEAN_NODE, flags)
            rahu_lon = rahu_res[0][0] % 360
            positions["Rahu"] = round(rahu_lon, 3)
            positions["Ketu"] = round((rahu_lon + 180) % 360, 3)
        except Exception as exc:
            logger.error("Transit API: Rahu/Ketu calc failed on %s: %s", date_str, exc)
            positions["Rahu"] = None
            positions["Ketu"] = None
            calc_error = True

        entry["positions"] = positions
        if calc_error:
            entry["error"] = "Partial ephemeris failure — some planet positions unavailable"

        if natal and moon_sign is not None and domain_ctx is not None:
            impact    = {d: 0 for d in DOMAINS}
            reasons   = []
            sade_sati = False

            for planet_name, lon in positions.items():
                if lon is None:
                    continue

                t_sign   = int(lon // 30) % 12
                t_name   = SIGN_NAMES[t_sign]
                aspected = vedic_aspected_signs(planet_name, t_sign)

                # Sade Sati — always judged on D1 Moon sign (not a divisional concept)
                if planet_name == "Saturn":
                    ss_signs = {
                        (moon_sign + 11) % 12: "rising",
                        moon_sign:             "peak",
                        (moon_sign +  1) % 12: "setting",
                    }
                    if t_sign in ss_signs:
                        sade_sati = True
                        phase = ss_signs[t_sign]
                        h_from_moon = sign_to_house(t_sign, moon_sign)
                        reasons.append(
                            f"Sade Sati ({phase} phase): Saturn in {t_name} "
                            f"({HOUSE_NAMES[h_from_moon]} from natal Moon) — "
                            f"karmic pressure on health, finances and relationships"
                        )
                        impact["health"]       += -15
                        impact["finance"]      += -10
                        impact["relationship"] += -10
                        impact["career"]       += -8

                asp_labels = ASPECT_LABEL.get(planet_name, {})

                for asp_sign in aspected:
                    a_num = aspect_num(t_sign, asp_sign)
                    a_lbl = asp_labels.get(a_num, f"{a_num}th")

                    for domain in DOMAINS:
                        ctx = domain_ctx.get(domain) or {}
                        dh_sign   = ctx.get("house_sign")
                        pd_s      = ctx.get("pd_sign")
                        d_lagna   = ctx.get("lagna_sign", lagna_sign)
                        chart_lbl = ctx.get("chart", "D1")

                        hit_house = dh_sign is not None and asp_sign == dh_sign
                        hit_moon  = asp_sign == moon_sign
                        hit_pd    = pd_s is not None and asp_sign == pd_s

                        if not (hit_house or hit_moon or hit_pd):
                            continue

                        delta = DOMAIN_BIAS.get((planet_name, domain), 0)
                        if delta == 0:
                            continue

                        impact[domain] += delta

                        # Chart tag helps UI explain WHY divisional chart is used
                        # (e.g. "your D10 10th house" for career)
                        chart_tag = f" [{chart_lbl}]" if chart_lbl != "D1" else ""

                        targets = []
                        if hit_house and d_lagna is not None:
                            h_num = sign_to_house(dh_sign, d_lagna)
                            targets.append(
                                f"{HOUSE_NAMES.get(h_num, str(h_num))}{chart_tag} house ({domain})"
                            )
                        if hit_moon:
                            targets.append("natal Moon")
                        if hit_pd and pd_planet:
                            targets.append(f"natal {pd_planet}{chart_tag} (PD lord)")

                        if targets:
                            direction = "supporting" if delta > 0 else "stressing"
                            reasons.append(
                                f"{planet_name} ({a_lbl} aspect from {t_name}) "
                                f"{direction} your {' and '.join(targets)} "
                                f"[{'+' if delta > 0 else ''}{delta} {domain}]"
                            )

            for d in DOMAINS:
                impact[d] = max(-30, min(20, impact[d]))

            seen, unique = set(), []
            for r in reasons:
                if r not in seen:
                    seen.add(r)
                    unique.append(r)

            entry["domain_impact"] = impact
            entry["reasons"]       = unique
            entry["sade_sati"]     = sade_sati

        results.append(entry)

    return jsonify(results)


@app.route("/api/career-analysis", methods=["POST", "OPTIONS"])
def career_analysis():
    """
    Vedic career analysis with Basic / Pro tiering.

    Body: { "user_id": int, "kundli": {...saved kundli object...} }
    Headers: X-API-Key (required)

    Returns:
      basic block (always): { score 0-100, trend, summary, hook }
      pro   block (only Pro/Trial users): houses, planets, dasha, transit,
                                          growth, struggles, promotion, job_change, risks
      meta:  { level: 'basic'|'pro', pro_locked: bool }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    import swisseph as swe
    from subscription_helper import effective_plan

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    kundli  = data.get("kundli") or {}

    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    user, err = get_authed_user(int(user_id))
    if err:
        return err

    planets = kundli.get("planets") or []
    if not planets:
        return jsonify({"error": "Kundli not provided. Please complete your birth chart first."}), 400

    SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    SIGN_LORD = {
        "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
        "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
        "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
    }
    EXALT = {"Sun":"Aries","Moon":"Taurus","Mars":"Capricorn","Mercury":"Virgo",
             "Jupiter":"Cancer","Venus":"Pisces","Saturn":"Libra"}
    DEBIL = {"Sun":"Libra","Moon":"Scorpio","Mars":"Cancer","Mercury":"Pisces",
             "Jupiter":"Capricorn","Venus":"Virgo","Saturn":"Aries"}
    OWN   = {"Sun":["Leo"],"Moon":["Cancer"],"Mars":["Aries","Scorpio"],
             "Mercury":["Gemini","Virgo"],"Jupiter":["Sagittarius","Pisces"],
             "Venus":["Taurus","Libra"],"Saturn":["Capricorn","Aquarius"]}

    def find_planet(name, source=planets):
        for p in source:
            if p.get("name") == name:
                return p
        return None

    asc_sign = kundli.get("ascendant") or "Aries"
    asc_idx  = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    sign_of_10th = SIGNS[(asc_idx + 9) % 12]
    sign_of_6th  = SIGNS[(asc_idx + 5) % 12]
    sign_of_11th = SIGNS[(asc_idx + 10) % 12]
    lord_10th    = SIGN_LORD[sign_of_10th]

    # ── Score calculation ────────────────────────────────────────────────
    score   = 50
    reasons = []

    # 10th house occupants (D1)
    p10 = [p for p in planets if p.get("house") == 10]
    benefics = {"Jupiter","Venus","Mercury"}
    malefics_hard = {"Saturn","Mars","Rahu","Ketu"}
    for p in p10:
        nm = p.get("name")
        if nm in benefics:
            score += 6; reasons.append(f"{nm} in 10th — benefic support for career")
        elif nm == "Sun":
            score += 8; reasons.append("Sun in 10th — strong status & authority")
        elif nm == "Saturn":
            score += 5; reasons.append("Saturn in 10th — disciplined long-term career builder")
        elif nm == "Mars":
            score += 4; reasons.append("Mars in 10th — drive & competitive edge")
        elif nm == "Rahu":
            score += 3; reasons.append("Rahu in 10th — unconventional rise, sudden growth")
        elif nm == "Ketu":
            score -= 4; reasons.append("Ketu in 10th — detachment, frequent career shifts")

    # 10th lord placement
    lord_p = find_planet(lord_10th)
    if lord_p:
        lh = lord_p.get("house", 0)
        lsign = lord_p.get("sign", "")
        if lh in (1,4,5,7,9,10,11):
            score += 7; reasons.append(f"10th lord {lord_10th} in {lh}th — favorable house placement")
        elif lh in (6,8,12):
            score -= 6; reasons.append(f"10th lord {lord_10th} in {lh}th (dusthana) — career obstacles")
        if lord_10th in EXALT and lsign == EXALT[lord_10th]:
            score += 6; reasons.append(f"{lord_10th} exalted in {lsign} — exceptional career strength")
        elif lord_10th in DEBIL and lsign == DEBIL[lord_10th]:
            score -= 6; reasons.append(f"{lord_10th} debilitated in {lsign} — career struggles indicated")
        elif lsign in OWN.get(lord_10th, []):
            score += 4; reasons.append(f"{lord_10th} in own sign {lsign} — stable career foundation")

    # 11th house — gains
    p11 = [p for p in planets if p.get("house") == 11]
    for p in p11:
        if p.get("name") in benefics or p.get("name") == "Jupiter":
            score += 4; reasons.append(f"{p['name']} in 11th — strong income & gains")
        elif p.get("name") in ("Sun","Saturn","Mars"):
            score += 2

    # 6th house — service & competition
    p6 = [p for p in planets if p.get("house") == 6]
    for p in p6:
        if p.get("name") in ("Mars","Saturn","Sun"):
            score += 3; reasons.append(f"{p['name']} in 6th — wins over rivals & job stability")

    # Saturn dignity (work karaka)
    sat = find_planet("Saturn")
    if sat:
        ssg = sat.get("sign","")
        if ssg == EXALT["Saturn"]:
            score += 5; reasons.append("Saturn exalted — natural karma karaka strong")
        elif ssg == DEBIL["Saturn"]:
            score -= 5; reasons.append("Saturn debilitated — extra effort needed in career")

    # Sun dignity (status karaka)
    sun = find_planet("Sun")
    if sun:
        ssg = sun.get("sign","")
        if ssg == EXALT["Sun"]:
            score += 4; reasons.append("Sun exalted — leadership & recognition")
        elif ssg == DEBIL["Sun"]:
            score -= 4; reasons.append("Sun debilitated — confidence & authority challenges")

    # D10 Dashamsha — career-specific divisional chart
    d10 = (kundli.get("divisionalCharts") or {}).get("D10") or {}
    d10_planets = d10.get("planets") or []
    d10_p10 = [p for p in d10_planets if p.get("house") == 10]
    for p in d10_p10:
        if p.get("name") in benefics:
            score += 4; reasons.append(f"{p['name']} in D10 10th — refined career karma")
        elif p.get("name") == "Sun":
            score += 5; reasons.append("Sun in D10 10th — destined for visible authority")

    # ── Current Mahadasha lord favorability for career ──────────────────
    cd = kundli.get("currentDasha") or {}
    md_lord = cd.get("maha","")
    ad_lord = cd.get("antar","")
    DASHA_CAREER = {
        "Jupiter": +8, "Sun": +7, "Mercury": +6, "Saturn": +5,
        "Mars": +3, "Venus": +2, "Moon": 0, "Rahu": -3, "Ketu": -5,
    }
    if md_lord in DASHA_CAREER:
        score += DASHA_CAREER[md_lord]
        reasons.append(f"Mahadasha {md_lord} — {'favorable' if DASHA_CAREER[md_lord] >= 0 else 'challenging'} for career")
    if ad_lord in DASHA_CAREER:
        score += DASHA_CAREER[ad_lord] // 2

    # ── Live transit: Saturn & Jupiter on 10th house ──────────────────────
    transit_notes = []
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        jd_now = swe.julday(*datetime.utcnow().timetuple()[:3], 12.0)
        for p_name, p_id in (("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN)):
            res = swe.calc_ut(jd_now, p_id, flags)
            t_lon = res[0][0] % 360
            t_sign = SIGNS[int(t_lon // 30)]
            t_house = ((SIGNS.index(t_sign) - asc_idx + 12) % 12) + 1
            if p_name == "Jupiter" and t_house in (10, 2, 6):
                score += 4
                transit_notes.append(f"Jupiter currently transiting your {t_house}th house — career growth phase active")
            if p_name == "Saturn" and t_house == 10:
                score += 2
                transit_notes.append(f"Saturn transiting your 10th house — major career restructuring period")
            elif p_name == "Saturn" and t_house in (4, 8, 12):
                score -= 4
                transit_notes.append(f"Saturn transiting your {t_house}th house — slow progress phase")
    except Exception:
        pass

    # Clamp & summarize
    score = max(20, min(95, score))
    if score >= 70:
        trend = "Good"
        summary = "Career mein strong support hai. Mehnat ka achha phal milne wala hai. Aage badhne ka time hai."
    elif score >= 50:
        trend = "Average"
        summary = "Mixed energy hai career mein. Patience aur sahi planning se progress hogi. Bade decisions sambhal ke lein."
    else:
        trend = "Risk"
        summary = "Abhi career mein challenges hain. Jaldi switch mat karein. Skill build karein, time better hoga."

    hook = "A major career shift is indicated in your chart — full timing and reason inside Pro."

    plan = effective_plan(user)
    is_pro_user = plan in ("pro", "trial")

    response = {
        "level":      "pro" if is_pro_user else "basic",
        "pro_locked": not is_pro_user,
        "basic": {
            "score":   score,
            "trend":   trend,
            "summary": summary,
            "hook":    hook,
        },
    }

    if is_pro_user:
        # ── Build Pro deep-dive sections ──────────────────────────────
        # Houses
        def fmt_house(num, sign, occ):
            occ_names = ", ".join(p["name"] for p in occ) if occ else "Khaali"
            return {
                "house":     num,
                "sign":      sign,
                "lord":      SIGN_LORD[sign],
                "occupants": occ_names,
            }
        houses_block = {
            "h10": fmt_house(10, sign_of_10th, p10),
            "h6":  fmt_house(6,  sign_of_6th,  p6),
            "h11": fmt_house(11, sign_of_11th, p11),
        }

        # Planet strengths
        def planet_strength(name):
            p = find_planet(name)
            if not p:
                return None
            sg = p.get("sign","")
            status = "neutral"
            if name in EXALT and sg == EXALT[name]:
                status = "exalted"
            elif name in DEBIL and sg == DEBIL[name]:
                status = "debilitated"
            elif sg in OWN.get(name, []):
                status = "own sign"
            return {"name": name, "sign": sg, "house": p.get("house"), "status": status,
                    "retrograde": bool(p.get("retrograde"))}

        planets_block = [planet_strength(n) for n in ("Saturn","Sun","Mercury","Jupiter","Mars")]
        planets_block = [p for p in planets_block if p]

        # Dasha block
        dasha_block = {
            "mahadasha": md_lord,
            "antardasha": ad_lord,
            "verdict": (
                "Career-supportive period — promotions & visibility likely."
                if DASHA_CAREER.get(md_lord, 0) >= 5 else
                "Mixed dasha — focus on consolidation, avoid risky switches."
                if DASHA_CAREER.get(md_lord, 0) >= 0 else
                "Challenging dasha — patience & skill building over jumps."
            ),
            "ends": cd.get("endDate", ""),
        }

        # Timing predictions (qualitative, derived from dasha + current trend)
        growth = []
        struggles = []
        promotion = []
        job_change = []
        risks = []

        if DASHA_CAREER.get(md_lord, 0) >= 5:
            growth.append(f"Current {md_lord} mahadasha aapke career ke favorable phase mein hai — recognition aur growth ke chances strong hain.")
            promotion.append(f"{md_lord} dasha mein promotion ya bigger role lene ka achha samay hai. Visible work pe focus karein.")
        if md_lord in ("Saturn","Rahu","Ketu"):
            struggles.append(f"{md_lord} dasha slow but transformative hai — quick rewards ki ummeed na rakhein.")
        if ad_lord in ("Mars","Rahu") and md_lord in ("Saturn","Sun"):
            job_change.append(f"{md_lord}-{ad_lord} antardasha — job change ya career direction shift ka strong indicator.")
        if not job_change:
            job_change.append("Next 6-12 months mein major job change ka indicator weak hai. Stability favor karein.")

        if score < 50:
            risks.append("Career score abhi low hai — financial commitment ya loan se bachein.")
            risks.append("Workplace politics aur authority figures (boss/seniors) se sambhalkar communicate karein.")
        if any(r for r in transit_notes if "slow progress" in r.lower()):
            risks.append("Saturn transit slow progress de raha hai — long-term planning, short-term patience.")

        if not growth:
            growth.append("Steady but unremarkable growth phase. Skill-building pe focus karein, results 2-3 saal mein dikhenge.")
        if not struggles:
            struggles.append("Major struggle indicators absent. Routine challenges hi expected hain.")
        if not promotion:
            promotion.append("Promotion ka clear yog abhi nahi hai — current role mein excel karke setup tayyar karein.")

        response["pro"] = {
            "houses":     houses_block,
            "planets":    planets_block,
            "dasha":      dasha_block,
            "transit":    transit_notes or ["No major Saturn/Jupiter transit on career houses currently."],
            "growth":     growth,
            "struggles":  struggles,
            "promotion":  promotion,
            "job_change": job_change,
            "risks":      risks,
            "reasons":    reasons[:8],
        }

    return jsonify(response)


@app.route("/api/health-analysis", methods=["POST", "OPTIONS"])
def health_analysis():
    """
    Vedic health analysis with Basic / Pro tiering.
    Body: { "user_id": int, "kundli": {...} }   Headers: X-API-Key
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    import swisseph as swe
    from subscription_helper import effective_plan

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    kundli  = data.get("kundli") or {}

    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    user, err = get_authed_user(int(user_id))
    if err:
        return err

    planets = kundli.get("planets") or []
    if not planets:
        return jsonify({"error": "Kundli not provided. Please complete your birth chart first."}), 400

    SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    SIGN_LORD = {
        "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
        "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
        "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
    }
    EXALT = {"Sun":"Aries","Moon":"Taurus","Mars":"Capricorn","Mercury":"Virgo",
             "Jupiter":"Cancer","Venus":"Pisces","Saturn":"Libra"}
    DEBIL = {"Sun":"Libra","Moon":"Scorpio","Mars":"Cancer","Mercury":"Pisces",
             "Jupiter":"Capricorn","Venus":"Virgo","Saturn":"Aries"}
    OWN   = {"Sun":["Leo"],"Moon":["Cancer"],"Mars":["Aries","Scorpio"],
             "Mercury":["Gemini","Virgo"],"Jupiter":["Sagittarius","Pisces"],
             "Venus":["Taurus","Libra"],"Saturn":["Capricorn","Aquarius"]}

    def find_planet(name):
        for p in planets:
            if p.get("name") == name:
                return p
        return None

    asc_sign = kundli.get("ascendant") or "Aries"
    asc_idx  = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    sign_of_1st  = asc_sign
    sign_of_6th  = SIGNS[(asc_idx + 5) % 12]
    sign_of_8th  = SIGNS[(asc_idx + 7) % 12]
    sign_of_12th = SIGNS[(asc_idx + 11) % 12]
    lord_1st     = SIGN_LORD[sign_of_1st]
    lord_6th     = SIGN_LORD[sign_of_6th]
    lord_8th     = SIGN_LORD[sign_of_8th]

    # ── Health score (start strong, deduct for vulnerabilities) ──────────
    score   = 65
    notes   = []
    benefics = {"Jupiter","Venus","Mercury","Moon"}

    # Lagna lord placement & dignity → vitality
    l1 = find_planet(lord_1st)
    if l1:
        h = l1.get("house", 0)
        sg = l1.get("sign","")
        if h in (1, 4, 5, 7, 9, 10, 11):
            score += 6; notes.append(f"Lagna lord {lord_1st} well-placed in {h}th — strong vitality")
        elif h in (6, 8, 12):
            score -= 8; notes.append(f"Lagna lord {lord_1st} in {h}th (dusthana) — vitality challenges")
        if lord_1st in EXALT and sg == EXALT[lord_1st]:
            score += 5; notes.append(f"{lord_1st} exalted — robust constitution")
        elif lord_1st in DEBIL and sg == DEBIL[lord_1st]:
            score -= 6; notes.append(f"{lord_1st} debilitated — extra self-care needed")

    # Planets in 1st house
    p1 = [p for p in planets if p.get("house") == 1]
    for p in p1:
        nm = p.get("name")
        if nm in benefics:
            score += 4
        elif nm in ("Saturn","Mars","Rahu","Ketu"):
            score -= 5
            notes.append(f"{nm} in Lagna — affects natural body strength")

    # 6th house — disease (more planets here = more health activity, often issues)
    p6 = [p for p in planets if p.get("house") == 6]
    for p in p6:
        nm = p.get("name")
        if nm == "Saturn":
            score -= 5; notes.append("Saturn in 6th — chronic, slow-recovery tendency")
        elif nm == "Mars":
            score -= 3; notes.append("Mars in 6th — inflammation & accident-prone phases")
        elif nm == "Rahu":
            score -= 4; notes.append("Rahu in 6th — sudden, hard-to-diagnose issues")
        elif nm == "Sun":
            score -= 2
        elif nm in benefics:
            score += 2  # benefics in 6th can give recovery strength

    # 8th house — chronic / longevity
    p8 = [p for p in planets if p.get("house") == 8]
    for p in p8:
        nm = p.get("name")
        if nm in ("Saturn","Mars","Rahu","Ketu"):
            score -= 4; notes.append(f"{nm} in 8th — chronic patterns possible")
        elif nm == "Sun":
            score -= 2

    # 12th house — hidden/sleep/hospital
    p12 = [p for p in planets if p.get("house") == 12]
    for p in p12:
        nm = p.get("name")
        if nm in ("Saturn","Rahu","Ketu"):
            score -= 3; notes.append(f"{nm} in 12th — sleep or hidden issues to monitor")

    # Moon — mental health
    moon = find_planet("Moon")
    moon_house = moon.get("house") if moon else 0
    if moon:
        msg = moon.get("sign","")
        if msg == EXALT["Moon"]:
            score += 4; notes.append("Moon exalted — strong emotional balance")
        elif msg == DEBIL["Moon"]:
            score -= 5; notes.append("Moon debilitated — mood swings & stress sensitivity")
        if moon_house in (6,8,12):
            score -= 4; notes.append(f"Moon in {moon_house}th — mental fatigue prone")
        # Moon-Saturn close house = depression risk
        sat = find_planet("Saturn")
        if sat and abs((sat.get("house",0) or 0) - (moon_house or 0)) <= 1:
            score -= 3; notes.append("Moon-Saturn proximity — emotional heaviness, needs grounding")

    # Sun — vitality
    sun = find_planet("Sun")
    if sun:
        ssg = sun.get("sign","")
        if ssg == EXALT["Sun"]:
            score += 3
        elif ssg == DEBIL["Sun"]:
            score -= 3; notes.append("Sun debilitated — low immunity periods possible")

    # ── Live transit: Saturn / Mars / Rahu on health houses ──────────────
    transit_notes = []
    transit_planets_raw = []
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        jd_now = swe.julday(*datetime.utcnow().timetuple()[:3], 12.0)
        for p_name, p_id in (("Saturn", swe.SATURN), ("Mars", swe.MARS),
                             ("Jupiter", swe.JUPITER), ("Rahu", swe.MEAN_NODE)):
            res = swe.calc_ut(jd_now, p_id, flags)
            t_lon = res[0][0] % 360
            t_sign = SIGNS[int(t_lon // 30)]
            t_house = ((SIGNS.index(t_sign) - asc_idx + 12) % 12) + 1
            transit_planets_raw.append((p_name, t_sign, t_house))
            if p_name == "Saturn" and t_house in (1, 6, 8, 12):
                score -= 4
                transit_notes.append(f"Saturn transiting {t_house}th — slow energy, needs extra rest")
            if p_name == "Mars" and t_house in (1, 6, 8):
                score -= 3
                transit_notes.append(f"Mars transiting {t_house}th — be cautious with injuries & inflammation")
            if p_name == "Jupiter" and t_house in (1, 5, 9):
                score += 4
                transit_notes.append(f"Jupiter transiting {t_house}th — protective & healing influence")
            if p_name == "Rahu" and t_house in (1, 6, 8):
                score -= 2
                transit_notes.append(f"Rahu transiting {t_house}th — unusual symptoms may surface, check early")
    except Exception:
        pass

    # ── Current dasha lord influence ─────────────────────────────────────
    cd = kundli.get("currentDasha") or {}
    md_lord = cd.get("maha","")
    ad_lord = cd.get("antar","")
    DASHA_HEALTH = {
        "Jupiter": +5, "Venus": +3, "Mercury": +2, "Moon": +1,
        "Sun": 0, "Mars": -3, "Saturn": -4, "Rahu": -5, "Ketu": -4,
    }
    if md_lord in DASHA_HEALTH:
        score += DASHA_HEALTH[md_lord]
    if ad_lord in DASHA_HEALTH:
        score += DASHA_HEALTH[ad_lord] // 2

    # Clamp
    score = max(25, min(95, score))
    if score >= 70:
        risk = "Low"
        summary = "Aapki health energy strong dikh rahi hai. Routine maintain karein, sab achha rahega."
    elif score >= 50:
        risk = "Moderate"
        summary = "Health mixed phase mein hai. Sleep, food aur stress management pe dhyan dein — chhoti aadat badi rakshak hoti hai."
    else:
        risk = "High"
        summary = "Body abhi extra care maang rahi hai. Kuch areas mein dhyan dene se bade issue tale ja sakte hain. Doctor consult zaroori lagey to lein."

    hook = "A hidden health risk period is indicated — full timing and causes are revealed in Pro."

    plan = effective_plan(user)
    is_pro_user = plan in ("pro", "trial")

    response = {
        "level":      "pro" if is_pro_user else "basic",
        "pro_locked": not is_pro_user,
        "basic": {
            "score":   score,
            "risk":    risk,
            "summary": summary,
            "hook":    hook,
        },
    }

    if is_pro_user:
        # ── Pro deep-dive ────────────────────────────────────────────────
        def planet_strength(name):
            p = find_planet(name)
            if not p: return None
            sg = p.get("sign","")
            status = "neutral"
            if name in EXALT and sg == EXALT[name]:    status = "exalted"
            elif name in DEBIL and sg == DEBIL[name]:  status = "debilitated"
            elif sg in OWN.get(name, []):              status = "own sign"
            return {"name": name, "sign": sg, "house": p.get("house"),
                    "status": status, "retrograde": bool(p.get("retrograde"))}

        houses_block = {
            "h1":  {"sign": sign_of_1st,  "lord": lord_1st,
                    "occupants": ", ".join(p["name"] for p in p1) or "Khaali",
                    "meaning": "Body & vitality"},
            "h6":  {"sign": sign_of_6th,  "lord": lord_6th,
                    "occupants": ", ".join(p["name"] for p in p6) or "Khaali",
                    "meaning": "Disease & immunity"},
            "h8":  {"sign": sign_of_8th,  "lord": lord_8th,
                    "occupants": ", ".join(p["name"] for p in p8) or "Khaali",
                    "meaning": "Chronic & longevity"},
            "h12": {"sign": sign_of_12th, "lord": SIGN_LORD[sign_of_12th],
                    "occupants": ", ".join(p["name"] for p in p12) or "Khaali",
                    "meaning": "Sleep & hidden issues"},
        }

        planets_block = [planet_strength(n) for n in ("Moon","Sun","Saturn","Mars","Jupiter")]
        planets_block = [p for p in planets_block if p]

        # Risk periods (qualitative based on dasha)
        risk_periods = []
        if md_lord in ("Saturn","Rahu","Ketu","Mars"):
            risk_periods.append(f"Current {md_lord} mahadasha — extra rest, regular checkups recommended.")
        if ad_lord in ("Saturn","Mars","Rahu","Ketu") and ad_lord != md_lord:
            risk_periods.append(f"{md_lord}-{ad_lord} antardasha (ends {cd.get('endDate','')}) — peak window for stress or minor health flare-ups.")
        if any(("Saturn" in t or "Mars" in t) and ("transiting" in t) for t in transit_notes):
            risk_periods.append("Live transit also indicates a sensitivity window — slow down for next few weeks.")
        if not risk_periods:
            risk_periods.append("Koi major risk period abhi nahi hai. Routine care kaafi hai.")

        # Nature of issues — derived from afflicted planets/houses
        nature = []
        sat = find_planet("Saturn")
        mars = find_planet("Mars")
        merc = find_planet("Mercury")
        if sat and sat.get("house") in (1,6,8,12):
            nature.append("Joint, bone ya knee-related stiffness — daily stretching aur warmth helpful.")
        if mars and mars.get("house") in (1,6,8):
            nature.append("Inflammation, acidity, blood-pressure ya minor injuries ka chance — spicy food kam karein.")
        if merc and merc.get("house") in (6,8,12):
            nature.append("Nervous system aur digestion sensitive — calm routine + light meals.")
        if moon and (moon_house in (6,8,12) or moon.get("sign") == DEBIL["Moon"]):
            nature.append("Stress, mood swings, neend mein disturbance — pranayam aur 7-8 hour sleep zaroori.")
        if not nature:
            nature.append("Constitution overall steady hai — minor seasonal issues hi expected hain.")

        # Recovery strength
        jup = find_planet("Jupiter")
        ven = find_planet("Venus")
        recovery_score = 0
        if jup:
            if jup.get("house") in (1,5,9): recovery_score += 2
            if jup.get("sign") == EXALT["Jupiter"]: recovery_score += 2
        if ven and ven.get("house") in (1,4,7,10): recovery_score += 1
        if l1 and l1.get("house") in (1,4,5,7,9,10): recovery_score += 1
        if recovery_score >= 4:
            recovery = "Strong — body bounces back fast. Healing energies actively support you."
        elif recovery_score >= 2:
            recovery = "Moderate — recovery aaram se hoti hai with proper rest aur diet."
        else:
            recovery = "Slow — patience zaroori hai. Recovery time genuinely lagta hai, jaldbazi mat karein."

        # Preventive guidance
        prevent = [
            "Daily 30 min walk ya light yoga — circulation aur immunity dono ke liye base hai.",
            "Subah Surya ko jal arpan + 10 min sunlight — Sun energy strengthen karta hai.",
            "Sleep 10:30 PM se pehle, screen 1 hour pehle band — Moon ki energy balance karega.",
            "Hydration + warm cooked food — Vata aur acidity dono ke liye supportive.",
        ]
        if sat and sat.get("house") in (1,6,8,12):
            prevent.append("Saturn affliction — black sesame oil massage, knees aur lower back ka extra dhyan.")
        if mars and mars.get("house") in (1,6,8):
            prevent.append("Mars affliction — alcohol/spice cut down, anger pe Pranayam helpful.")

        # Remedies — gentle, mantra + lifestyle (no fear)
        remedies = []
        if md_lord == "Saturn" or (sat and sat.get("house") in (1,6,8,12)):
            remedies.append("Shanivaar ko 'Om Sham Shanaischaraya Namah' 108 baar — Saturn ki heaviness halki hoti hai.")
        if md_lord == "Mars" or (mars and mars.get("house") in (1,6,8)):
            remedies.append("Mangalvaar ko Hanuman Chalisa — Mars ki agni constructive direction milti hai.")
        if moon and (moon_house in (6,8,12) or moon.get("sign") == DEBIL["Moon"]):
            remedies.append("Somvaar ko white food (rice/milk) + 'Om Som Somaya Namah' 108 baar — mind shanti milti hai.")
        if md_lord == "Rahu" or md_lord == "Ketu":
            remedies.append("Roz 5 min meditation + clean room — Rahu/Ketu ki chaos energy settle hoti hai.")
        if not remedies:
            remedies.append("Daily 'Maha Mrityunjaya Mantra' 11 baar — universal health protector.")
            remedies.append("Tulsi ke 2-3 patte subah — natural immunity booster.")

        response["pro"] = {
            "houses":        houses_block,
            "planets":       planets_block,
            "transit":       transit_notes or ["No major adverse transit on health houses currently — protective phase."],
            "risk_periods":  risk_periods,
            "nature":        nature,
            "recovery":      recovery,
            "prevent":       prevent,
            "remedies":      remedies,
            "reasons":       notes[:8],
        }

    return jsonify(response)


@app.route("/api/finance-analysis", methods=["POST", "OPTIONS"])
def finance_analysis():
    """
    Vedic finance analysis with Basic / Pro tiering.
    Body: { "user_id": int, "kundli": {...} }   Headers: X-API-Key
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    import swisseph as swe
    from subscription_helper import effective_plan

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    kundli  = data.get("kundli") or {}

    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    user, err = get_authed_user(int(user_id))
    if err:
        return err

    planets = kundli.get("planets") or []
    if not planets:
        return jsonify({"error": "Kundli not provided. Please complete your birth chart first."}), 400

    SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    SIGN_LORD = {
        "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
        "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
        "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
    }
    EXALT = {"Sun":"Aries","Moon":"Taurus","Mars":"Capricorn","Mercury":"Virgo",
             "Jupiter":"Cancer","Venus":"Pisces","Saturn":"Libra"}
    DEBIL = {"Sun":"Libra","Moon":"Scorpio","Mars":"Cancer","Mercury":"Pisces",
             "Jupiter":"Capricorn","Venus":"Virgo","Saturn":"Aries"}
    OWN   = {"Sun":["Leo"],"Moon":["Cancer"],"Mars":["Aries","Scorpio"],
             "Mercury":["Gemini","Virgo"],"Jupiter":["Sagittarius","Pisces"],
             "Venus":["Taurus","Libra"],"Saturn":["Capricorn","Aquarius"]}

    def find_planet(name):
        for p in planets:
            if p.get("name") == name:
                return p
        return None

    asc_sign = kundli.get("ascendant") or "Aries"
    asc_idx  = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    sign_of_2nd  = SIGNS[(asc_idx + 1)  % 12]
    sign_of_5th  = SIGNS[(asc_idx + 4)  % 12]
    sign_of_8th  = SIGNS[(asc_idx + 7)  % 12]
    sign_of_9th  = SIGNS[(asc_idx + 8)  % 12]
    sign_of_11th = SIGNS[(asc_idx + 10) % 12]
    sign_of_12th = SIGNS[(asc_idx + 11) % 12]
    lord_2nd     = SIGN_LORD[sign_of_2nd]
    lord_11th    = SIGN_LORD[sign_of_11th]

    score   = 55
    notes   = []
    benefics = {"Jupiter","Venus","Mercury"}

    # 2nd house — wealth/savings
    p2 = [p for p in planets if p.get("house") == 2]
    for p in p2:
        nm = p.get("name")
        if nm == "Jupiter":
            score += 8; notes.append("Jupiter in 2nd — strong savings & family wealth")
        elif nm == "Venus":
            score += 6; notes.append("Venus in 2nd — luxury & comfort money")
        elif nm == "Mercury":
            score += 4; notes.append("Mercury in 2nd — sharp money sense, business mind")
        elif nm == "Saturn":
            score -= 4; notes.append("Saturn in 2nd — savings build slowly, late but steady")
        elif nm == "Rahu":
            score += 2; notes.append("Rahu in 2nd — unconventional income paths")
        elif nm == "Ketu":
            score -= 3; notes.append("Ketu in 2nd — money can slip away, avoid leaks")

    # 2nd lord placement
    l2 = find_planet(lord_2nd)
    if l2:
        h = l2.get("house", 0); sg = l2.get("sign","")
        if h in (1,2,5,9,10,11):
            score += 6; notes.append(f"2nd lord {lord_2nd} in {h}th — wealth flow supported")
        elif h in (6,8,12):
            score -= 7; notes.append(f"2nd lord {lord_2nd} in {h}th (dusthana) — wealth leakage risk")
        if lord_2nd in EXALT and sg == EXALT[lord_2nd]:
            score += 5; notes.append(f"{lord_2nd} exalted — wealth karma strong")
        elif lord_2nd in DEBIL and sg == DEBIL[lord_2nd]:
            score -= 5; notes.append(f"{lord_2nd} debilitated — money matters need extra effort")

    # 11th house — gains/income
    p11 = [p for p in planets if p.get("house") == 11]
    for p in p11:
        nm = p.get("name")
        if nm in benefics:
            score += 6; notes.append(f"{nm} in 11th — multiple income streams indicated")
        elif nm == "Sun":
            score += 4; notes.append("Sun in 11th — gains through authority/position")
        elif nm == "Saturn":
            score += 5; notes.append("Saturn in 11th — slow but huge long-term gains")
        elif nm == "Mars":
            score += 3; notes.append("Mars in 11th — gains through enterprise & courage")
        elif nm == "Rahu":
            score += 6; notes.append("Rahu in 11th — sudden, large gains from foreign/unconventional sources")

    # 11th lord
    l11 = find_planet(lord_11th)
    if l11:
        h = l11.get("house", 0)
        if h in (2,5,9,10,11):
            score += 5; notes.append(f"11th lord {lord_11th} in {h}th — gains channel strong")
        elif h in (6,8,12):
            score -= 5; notes.append(f"11th lord {lord_11th} in {h}th — income blocked or delayed")

    # 5th house — investments/speculation
    p5 = [p for p in planets if p.get("house") == 5]
    for p in p5:
        nm = p.get("name")
        if nm in benefics:
            score += 4; notes.append(f"{nm} in 5th — favorable for investments")
        elif nm in ("Mars","Rahu"):
            score += 1; notes.append(f"{nm} in 5th — speculation possible, but high risk")
        elif nm == "Ketu":
            score -= 3; notes.append("Ketu in 5th — avoid speculation, pure luck weak")

    # 9th house — luck/fortune
    p9 = [p for p in planets if p.get("house") == 9]
    for p in p9:
        nm = p.get("name")
        if nm in benefics or nm == "Sun":
            score += 4; notes.append(f"{nm} in 9th — fortune & elder/mentor support")
        elif nm in ("Saturn","Rahu","Ketu"):
            score -= 2

    # 8th house — sudden gains/losses
    p8 = [p for p in planets if p.get("house") == 8]
    for p in p8:
        nm = p.get("name")
        if nm == "Jupiter":
            score += 3; notes.append("Jupiter in 8th — possible inheritance/sudden wealth")
        elif nm == "Venus":
            score += 2
        elif nm in ("Mars","Saturn","Ketu"):
            score -= 3; notes.append(f"{nm} in 8th — sudden expenses possible, keep emergency fund")

    # 12th house — expenses
    p12 = [p for p in planets if p.get("house") == 12]
    for p in p12:
        nm = p.get("name")
        if nm in ("Saturn","Rahu","Ketu"):
            score -= 4; notes.append(f"{nm} in 12th — high expense or hidden outflow")
        elif nm == "Mars":
            score -= 2

    # Jupiter karaka strength
    jup = find_planet("Jupiter")
    if jup:
        jsg = jup.get("sign","")
        if jsg == EXALT["Jupiter"]:
            score += 5; notes.append("Jupiter exalted — natural wealth protector strong")
        elif jsg == DEBIL["Jupiter"]:
            score -= 5; notes.append("Jupiter debilitated — wealth wisdom needs nurture")
        if jup.get("house") in (1,2,5,9,11):
            score += 3
        elif jup.get("house") in (6,8,12):
            score -= 3

    # Venus karaka strength
    ven = find_planet("Venus")
    if ven:
        vsg = ven.get("sign","")
        if vsg == EXALT["Venus"]:
            score += 4
        elif vsg == DEBIL["Venus"]:
            score -= 4

    # Saturn delay/loss factor
    sat = find_planet("Saturn")
    if sat and sat.get("house") in (2,5,8,11,12):
        # Saturn in 11th is actually positive (handled above)
        if sat.get("house") in (8,12):
            score -= 3; notes.append(f"Saturn in {sat.get('house')}th — delays in money matters")

    # ── Live transits: Jupiter, Saturn, Rahu on wealth houses ────────────
    transit_notes = []
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        jd_now = swe.julday(*datetime.utcnow().timetuple()[:3], 12.0)
        for p_name, p_id in (("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN),
                             ("Rahu", swe.MEAN_NODE), ("Venus", swe.VENUS)):
            res = swe.calc_ut(jd_now, p_id, flags)
            t_lon = res[0][0] % 360
            t_sign = SIGNS[int(t_lon // 30)]
            t_house = ((SIGNS.index(t_sign) - asc_idx + 12) % 12) + 1
            if p_name == "Jupiter" and t_house in (2, 5, 9, 11):
                score += 5
                transit_notes.append(f"Jupiter currently in your {t_house}th — wealth-building & opportunity phase active")
            if p_name == "Saturn" and t_house in (2, 11):
                score += 3
                transit_notes.append(f"Saturn in {t_house}th — slow but solid long-term wealth structure forming")
            if p_name == "Saturn" and t_house in (8, 12):
                score -= 3
                transit_notes.append(f"Saturn in {t_house}th — extra discipline on expenses needed")
            if p_name == "Rahu" and t_house in (2, 5, 11):
                score += 4
                transit_notes.append(f"Rahu in {t_house}th — sudden income or unconventional gain possible")
            if p_name == "Venus" and t_house in (2, 11):
                score += 2
                transit_notes.append(f"Venus in {t_house}th — comfort spending & luxury inflow phase")
    except Exception:
        pass

    # ── Current dasha favorability for finance ──────────────────────────
    cd = kundli.get("currentDasha") or {}
    md_lord = cd.get("maha","")
    ad_lord = cd.get("antar","")
    DASHA_WEALTH = {
        "Jupiter": +8, "Venus": +6, "Mercury": +5, "Sun": +3,
        "Moon": +2, "Saturn": +2, "Mars": 0, "Rahu": +4, "Ketu": -3,
    }
    if md_lord in DASHA_WEALTH:
        score += DASHA_WEALTH[md_lord]
    if ad_lord in DASHA_WEALTH:
        score += DASHA_WEALTH[ad_lord] // 2

    score = max(25, min(95, score))
    if score >= 70:
        trend = "Gain"
        summary = "Finance mein achhi energy hai. Income grow karne ke yog hain. Sahi opportunity ka faayda uthayein."
    elif score >= 50:
        trend = "Stable"
        summary = "Money flow steady hai. Bade risks abhi avoid karein, slow & disciplined approach se wealth build hogi."
    else:
        trend = "Loss"
        summary = "Abhi expenses ya delay phase chal sakta hai. Naya investment soch-samajh ke karein, savings ko priority dein."

    hook = "A strong financial gain period is indicated — full timing and source are revealed in Pro."

    plan = effective_plan(user)
    is_pro_user = plan in ("pro", "trial")

    response = {
        "level":      "pro" if is_pro_user else "basic",
        "pro_locked": not is_pro_user,
        "basic": {
            "score":   score,
            "trend":   trend,
            "summary": summary,
            "hook":    hook,
        },
    }

    if is_pro_user:
        def planet_strength(name):
            p = find_planet(name)
            if not p: return None
            sg = p.get("sign","")
            status = "neutral"
            if name in EXALT and sg == EXALT[name]:    status = "exalted"
            elif name in DEBIL and sg == DEBIL[name]:  status = "debilitated"
            elif sg in OWN.get(name, []):              status = "own sign"
            return {"name": name, "sign": sg, "house": p.get("house"),
                    "status": status, "retrograde": bool(p.get("retrograde"))}

        houses_block = {
            "h2":  {"sign": sign_of_2nd,  "lord": lord_2nd,
                    "occupants": ", ".join(p["name"] for p in p2) or "Khaali",
                    "meaning": "Wealth & savings"},
            "h11": {"sign": sign_of_11th, "lord": lord_11th,
                    "occupants": ", ".join(p["name"] for p in p11) or "Khaali",
                    "meaning": "Income & gains"},
            "h5":  {"sign": sign_of_5th,  "lord": SIGN_LORD[sign_of_5th],
                    "occupants": ", ".join(p["name"] for p in p5) or "Khaali",
                    "meaning": "Investment & speculation"},
            "h9":  {"sign": sign_of_9th,  "lord": SIGN_LORD[sign_of_9th],
                    "occupants": ", ".join(p["name"] for p in p9) or "Khaali",
                    "meaning": "Luck & fortune"},
        }

        planets_block = [planet_strength(n) for n in ("Jupiter","Venus","Mercury","Saturn","Rahu")]
        planets_block = [p for p in planets_block if p]

        # Inflow periods
        inflow = []
        if md_lord in ("Jupiter","Venus","Mercury") and DASHA_WEALTH.get(md_lord, 0) >= 5:
            inflow.append(f"Current {md_lord} mahadasha — wealth-favorable phase, naye income channels khulne ke chances strong hain.")
        if ad_lord in ("Jupiter","Venus","Mercury","Rahu"):
            inflow.append(f"{md_lord}-{ad_lord} antardasha (ends {cd.get('endDate','')}) — short-term gain window active hai.")
        if any("opportunity phase" in t or "sudden income" in t for t in transit_notes):
            inflow.append("Jupiter/Rahu transit bhi support de raha hai — apportunities pe quickly act karein.")
        if not inflow:
            inflow.append("Major inflow yog abhi nahi hai. Existing income consolidate karein, naye sources slowly explore karein.")

        # Expense / loss phases
        expenses = []
        if md_lord in ("Saturn","Ketu","Rahu") and md_lord != "Jupiter":
            if md_lord == "Ketu":
                expenses.append(f"Ketu mahadasha — money detachment phase, unexpected expense possible. Budget tight rakhein.")
            elif md_lord == "Saturn":
                expenses.append(f"Saturn mahadasha — slow income aur disciplined spending zaroori. Loans soch-samajh ke.")
        if any("expense" in t.lower() or "discipline on expenses" in t for t in transit_notes):
            expenses.append("Saturn transit kuch hidden outflow la raha hai — monthly expenses track karein.")
        if not expenses:
            expenses.append("Major loss phase abhi nahi hai. Routine expenses hi expected hain.")

        # Investment opportunities
        invest = []
        if jup and jup.get("house") in (5,9,11):
            invest.append("Jupiter strong placement — long-term investments (mutual funds, gold, education) favorable.")
        if any(p.get("name") in benefics and p.get("house") == 5 for p in planets):
            invest.append("5th house mein benefic — equity/SIP route try kar sakte ho, but research zaroor karein.")
        if any(p.get("name") == "Rahu" and p.get("house") in (5,11) for p in planets):
            invest.append("Rahu in 5th/11th — speculation/crypto attract karega, but max 5-10% portfolio rakhein.")
        if not invest:
            invest.append("Conservative tools (FD, RD, PPF) abhi behtar — speculation se door rahein.")

        # Sudden gain/loss
        sudden = []
        if any(p.get("name") == "Rahu" and p.get("house") in (2,5,8,11) for p in planets):
            sudden.append("Rahu wealth-house mein — sudden bonus, lottery ya unexpected money ka chance, but equally sudden loss bhi possible.")
        if any(p.get("name") == "Jupiter" and p.get("house") == 8 for p in planets):
            sudden.append("Jupiter in 8th — inheritance ya gift se wealth aane ka subtle yog.")
        if any(p.get("name") in ("Mars","Ketu") and p.get("house") == 8 for p in planets):
            sudden.append("Mars/Ketu in 8th — emergency fund maintain rakhein, sudden expense possible.")
        if not sudden:
            sudden.append("Sudden gain/loss ka strong indicator nahi hai. Steady flow expected.")

        # Wealth stability
        stability_score = 0
        if l2 and l2.get("house") in (1,2,5,9,10,11): stability_score += 2
        if jup and jup.get("house") in (1,2,5,9,11): stability_score += 2
        if any(p.get("name") == "Saturn" and p.get("house") == 11 for p in planets): stability_score += 1
        if any(p.get("name") in ("Saturn","Rahu","Ketu") and p.get("house") == 12 for p in planets): stability_score -= 2

        if stability_score >= 3:
            stability = "Strong — long-term wealth structure solid hai. Routine bachat hi compound hokar bada corpus banega."
        elif stability_score >= 0:
            stability = "Moderate — wealth slowly build hoti hai. Patience aur disciplined SIP zaroori."
        else:
            stability = "Volatile — money aata-jaata rehta hai. Spending discipline aur emergency fund priority hai."

        # Remedies
        remedies = []
        if jup and (jup.get("sign") == DEBIL["Jupiter"] or jup.get("house") in (6,8,12)):
            remedies.append("Brihaspativaar (Thursday) ko 'Om Brim Brihaspataye Namah' 108 baar — Jupiter ki blessings activate hoti hain.")
        if md_lord == "Saturn" or (sat and sat.get("house") in (2,8,12)):
            remedies.append("Shanivaar ko till tel ka deepak Peepal ke neeche — Saturn ki delay halki hoti hai.")
        if ven and (ven.get("sign") == DEBIL["Venus"] or ven.get("house") in (6,8,12)):
            remedies.append("Shukravaar ko white sweet kanya ko daan — Venus ki kripa wealth flow lati hai.")
        if md_lord == "Rahu" or any(p.get("name") == "Rahu" and p.get("house") == 12 for p in planets):
            remedies.append("Roz subah 7 daane gud + chana cow ko — Rahu ki chaos energy stable hoti hai.")
        # Always include practical
        remedies.append("Practical: 50-30-20 rule (50% needs, 30% wants, 20% savings) — Lakshmi sthir wahin tikti hai jahan discipline hai.")
        remedies.append("Practical: Har month 10% income emergency fund mein — sudden expense ke time grace milega.")

        response["pro"] = {
            "houses":     houses_block,
            "planets":    planets_block,
            "transit":    transit_notes or ["No major Jupiter/Saturn transit on wealth houses currently."],
            "inflow":     inflow,
            "expenses":   expenses,
            "invest":     invest,
            "sudden":     sudden,
            "stability":  stability,
            "remedies":   remedies,
            "reasons":    notes[:8],
        }

    return jsonify(response)


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


# ── AstroVastu BASIC (Sprint 2 — text-only personalized check) ───────────────

@app.route("/api/astrovastu-basic", methods=["POST"])
def astrovastu_basic_route():
    """
    BASIC AstroVastu — deterministic personalized Vastu check using the user's
    saved kundli + classical rules. No vision, no LLM call (cost ~₹0.50/check).

    Body: {
      user_id:      <int>           (required for authed quota; optional preview),
      room_type:    str             (e.g. "bedroom", "kitchen", "pooja"),
      direction:    str             (one of 8 directions; case-insensitive),
      floor:        int             (optional),
      current_color: str            (optional),
      notes:        str             (optional)
    }
    Headers: X-API-Key  (required when user_id sent)

    Returns 200 with full deterministic response (see astrovastu_response.py),
    or 401/402/404/422 on auth/quota/profile/validation errors.
    """
    from subscription_helper import (
        can_use_astrovastu_basic_v2,
        consume_astrovastu_basic_v2,
        effective_plan,
    )
    from astrovastu_engine import (
        build_kundli_context,
        apply_tie_breakers,
        personalized_severity_multiplier,
        is_profile_complete,
    )
    from astrovastu_rules import (
        DIRECTIONS,
        get_generic_room_rule,
    )
    from astrovastu_response import build_basic_response
    from kundli_engine import calculate_kundli
    from models import AstroVastuBasicLog
    import json

    data = request.get_json(force=True, silent=True) or {}

    # ── Item 17: request validation ─────────────────────────────────────────
    room_type = (data.get("room_type") or "").strip().lower()
    direction = (data.get("direction") or "").strip()
    if not room_type:
        return jsonify({"error": "room_type is required"}), 400

    # Normalize direction (accept "north-east", "Northeast", "NE", etc. → "North-East")
    DIR_ALIASES = {
        "n":  "North", "north":      "North",
        "ne": "North-East", "northeast": "North-East", "north-east": "North-East",
        "e":  "East",  "east":       "East",
        "se": "South-East", "southeast": "South-East", "south-east": "South-East",
        "s":  "South", "south":      "South",
        "sw": "South-West", "southwest": "South-West", "south-west": "South-West",
        "w":  "West",  "west":       "West",
        "nw": "North-West", "northwest": "North-West", "north-west": "North-West",
    }
    direction_norm = DIR_ALIASES.get(direction.lower(), direction)
    if direction_norm not in DIRECTIONS:
        return jsonify({
            "error": "invalid direction",
            "allowed": DIRECTIONS,
        }), 400

    # ── Item 18: auth (mandatory when user_id provided) ────────────────────
    user_id = data.get("user_id")
    user = None
    plan = "free"
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key or user.api_key != api_key:
            return jsonify({"error": "Unauthorized — invalid API key"}), 401
        plan = effective_plan(user)
    else:
        return jsonify({
            "error": "auth_required",
            "message": "Login zaroori hai personalized check ke liye.",
        }), 401

    # ── Item 19: profile completeness gate ─────────────────────────────────
    # Accept either: cached chart_data, OR raw birth fields (we recompute).
    # Hard-block only when neither is usable.
    k = user.kundli
    if not k:
        return jsonify({
            "error":   "profile_incomplete",
            "message": "Pehle apni Kundli profile complete karein (DOB, time, place).",
            "missing_fields": ["dob", "tob", "pob", "lat", "lon", "tz"],
        }), 422

    chart = None
    if k.chart_data:
        try:
            chart = json.loads(k.chart_data)
        except Exception:
            chart = None

    if not chart:
        # Validate raw birth fields before attempting recompute.
        missing = []
        if not k.dob:       missing.append("dob")
        if not k.tob:       missing.append("tob")
        if k.lat is None:   missing.append("lat")
        if k.lon is None:   missing.append("lon")
        if k.tz  is None:   missing.append("tz")
        if missing:
            return jsonify({
                "error":   "profile_incomplete",
                "message": "Pehle apni Kundli profile complete karein (DOB, time, place).",
                "missing_fields": missing,
            }), 422
        try:
            chart = calculate_kundli({
                "name":     k.name or user.name or "User",
                "day":      int(k.dob.split("-")[2]),
                "month":    int(k.dob.split("-")[1]),
                "year":     int(k.dob.split("-")[0]),
                "hour":     int((k.tob or "06:00").split(":")[0]),
                "minute":   int((k.tob or "06:00").split(":")[1]),
                "ampm":     "AM",
                "lat":      float(k.lat or 0),
                "lon":      float(k.lon or 0),
                "tz":       float(k.tz or 5.5),
                "place":    k.pob or "",
            })
        except Exception as exc:
            return jsonify({
                "error":   "kundli_unreadable",
                "message": f"Kundli data parse nahin ho saka: {exc}",
            }), 422

    # ── Item 20a: Phase-2 unlock gate (Pro / property unlock / room credit / daily quota)
    property_name = (data.get("property_name") or "").strip()
    quota_check = can_use_astrovastu_basic_v2(user, property_name)
    if not quota_check["allowed"]:
        return jsonify({
            "error":   "upgrade_required",
            "message": quota_check.get("reason",
                       "Login + Kundli profile required for personalized Basic check."),
            "credits": quota_check.get("credits", 0),
            "unlocks": quota_check.get("unlocks", []),
            "plan":    plan,
            "upgrade_required": True,
        }), 402

    # ── Item 21: engine pipeline (run BEFORE charging quota) ──────────────
    # If the engine fails, the user must NOT lose a daily check.
    try:
        ctx     = build_kundli_context(chart)
        tb_res  = apply_tie_breakers(room_type, direction_norm, ctx)
        sev_res = personalized_severity_multiplier(direction_norm, ctx)
        rule    = get_generic_room_rule(room_type)
    except Exception as exc:
        import traceback; traceback.print_exc()
        return jsonify({"error": "engine_failure"}), 500

    # ── Item 20b: Phase-2 atomic consume AFTER engine success ─────────────
    quota = consume_astrovastu_basic_v2(user, property_name)
    if not quota["allowed"]:
        return jsonify({
            "error":   "upgrade_required",
            "message": quota.get("reason", "Out of credits."),
            "credits": quota.get("credits", 0),
            "plan":    plan,
            "upgrade_required": True,
        }), 402

    # ── Item 22: build response (deterministic, bilingual) ────────────────
    response = build_basic_response(
        room_type=room_type,
        direction=direction_norm,
        kundli_context=ctx,
        tie_breaker_result=tb_res,
        severity_result=sev_res,
        generic_room_rule=rule,
    )
    response["unlock"] = {
        "via":            quota.get("via"),
        "credits_left":   quota.get("credits", 0),
        "property_name":  property_name or None,
    }
    # Backward-compat shim — older clients still read response.quota.{used,limit}
    response["quota"] = {
        "used":  quota.get("used", 0) or 0,
        "limit": quota.get("limit", -1) if quota.get("via") == "daily_free_quota" else -1,
    }
    response["plan"]  = plan

    # ── Item 24: log to DB ────────────────────────────────────────────────
    try:
        log = AstroVastuBasicLog(
            user_id    = user.id,
            room_type  = room_type,
            direction  = direction_norm,
            verdict    = response["verdict"],
            severity   = response["severity"]["bucket"],
            multiplier = response["severity"]["multiplier"],
            lagna      = ctx.get("lagna"),
            mahadasha  = ctx.get("current_mahadasha"),
            sade_sati  = bool(ctx.get("sade_sati", {}).get("active")),
            plan       = plan,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        # Logging never blocks the user's result
        print(f"[astrovastu-basic] log failed: {exc}")
        db.session.rollback()

    return jsonify(response)


# ─────────────────────────────────────────────────────────────────────────────
# AstroVastu PRO  —  multi-room deep-scan endpoint  (Sprint 3)
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_user_chart(user):
    """
    Load the user's birth chart, preferring the multi-profile primary Profile,
    then falling back to the legacy `user.kundli` table.

    Returns (chart_dict_or_None, missing_fields_list, name_str).
    A non-None chart means we're good to proceed; otherwise `missing_fields`
    tells the client what to ask for.
    """
    import json as _json
    from kundli_engine import calculate_kundli as _calc

    # 1) Multi-profile primary (canonical source in current app)
    try:
        prim = (Profile.query
                .filter_by(user_id=user.id, deleted_at=None, is_primary=True)
                .first())
        if not prim:
            prim = (Profile.query
                    .filter_by(user_id=user.id, deleted_at=None)
                    .order_by(Profile.created_at.asc())
                    .first())
        if prim:
            name = prim.name or user.name or "User"
            if prim.chart_data:
                try:
                    return _json.loads(prim.chart_data), [], name
                except Exception:
                    pass
            bd = None
            if prim.birth_data:
                try: bd = _json.loads(prim.birth_data)
                except Exception: bd = None
            if isinstance(bd, dict):
                try:
                    chart = _calc({
                        "name":   name,
                        "day":    int(bd.get("day", 0)),
                        "month":  int(bd.get("month", 0)),
                        "year":   int(bd.get("year", 0)),
                        "hour":   int(bd.get("hour", 0)),
                        "minute": int(bd.get("minute", 0)),
                        "ampm":   str(bd.get("ampm") or "AM").upper(),
                        "lat":    float(bd.get("lat") or 0),
                        "lon":    float(bd.get("lon") or 0),
                        "tz":     float(bd.get("tz")  or 5.5),
                        "place":  bd.get("place") or "",
                    })
                    return chart, [], name
                except Exception as exc:
                    print(f"[chart-resolve] primary profile calc failed: {exc}")
    except Exception as exc:
        print(f"[chart-resolve] primary profile lookup failed: {exc}")

    # 2) Legacy single-kundli fallback
    k = user.kundli
    if k:
        name = k.name or user.name or "User"
        if k.chart_data:
            try:
                return _json.loads(k.chart_data), [], name
            except Exception:
                pass
        missing = [f for f, v in [("dob", k.dob), ("tob", k.tob),
                                  ("lat", k.lat), ("lon", k.lon), ("tz", k.tz)]
                   if v in (None, "")]
        if not missing:
            try:
                chart = _calc({
                    "name":   name,
                    "day":    int(k.dob.split("-")[2]),
                    "month":  int(k.dob.split("-")[1]),
                    "year":   int(k.dob.split("-")[0]),
                    "hour":   int((k.tob or "06:00").split(":")[0]),
                    "minute": int((k.tob or "06:00").split(":")[1]),
                    "ampm":   "AM",
                    "lat":    float(k.lat or 0),
                    "lon":    float(k.lon or 0),
                    "tz":     float(k.tz  or 5.5),
                    "place":  k.pob or "",
                })
                return chart, [], name
            except Exception as exc:
                print(f"[chart-resolve] legacy kundli calc failed: {exc}")
        return None, (missing or ["dob", "tob", "pob", "lat", "lon", "tz"]), name

    return None, ["dob", "tob", "pob", "lat", "lon", "tz"], (user.name or "User")


@app.route("/api/astrovastu-pro", methods=["POST"])
def astrovastu_pro_route():
    """
    PRO AstroVastu — full-house deep scan with mahadasha-mandatory layer.

    Body: {
      user_id:    <int>                                        (required, authed),
      floor_plan: [ {room_type:str, direction:str}, ...max 12 ] (required)
    }
    Headers: X-API-Key (required)

    Returns 200 with full PRO report (see astrovastu_pro_response.py)
        or 400/401/402/422/500 on validation/auth/quota/profile/engine errors.

    Quota: monthly counter (basic=1/mo, pro=unlimited). Consumed AFTER engine
    success — failed scans never charge the user (Sprint-2 architect fix).
    """
    from subscription_helper import (
        can_use_astrovastu_pro_v2, consume_astrovastu_pro_v2, effective_plan,
    )
    from astrovastu_pro_engine import analyze_floor_plan
    from astrovastu_pro_response import build_pro_response
    from kundli_engine import calculate_kundli
    from models import AstroVastuProLog
    import json

    data = request.get_json(force=True, silent=True) or {}
    lang = (data.get("lang") or "en").strip().lower()

    # ── Phase 6: Cosmic Vision floor-plan extraction (optional, NEVER blocks) ─
    vision_data    = None
    vision_warning = None
    fp_upload = data.get("floor_plan_upload")
    if isinstance(fp_upload, dict) and (fp_upload.get("data_url") or fp_upload.get("base64")):
        try:
            from vision_layer import extract_floor_plan_from_upload
            vd, verr = extract_floor_plan_from_upload(fp_upload, business_type=None, lang=lang)
        except Exception as exc:
            print(f"[astrovastu-pro] floor-plan vision crashed (non-fatal): {exc}")
            vd, verr = {}, "Cosmic Vision is temporarily unavailable. Continuing with your manual layout."
        if verr:
            vision_warning = verr
        if vd and vd.get("rooms"):
            vision_data = vd
            if not data.get("floor_plan"):
                data["floor_plan"] = vd["rooms"]

    # ── Validation ────────────────────────────────────────────────────────
    floor_plan = data.get("floor_plan")
    if not isinstance(floor_plan, list) or not floor_plan:
        # If user uploaded a floor plan but Cosmic Vision couldn't read it,
        # surface a brand-safe, actionable message instead of a generic 400.
        if fp_upload:
            return jsonify({
                "error":          "vision_inconclusive",
                "message":        vision_warning or "Cosmic Vision could not detect rooms in this upload. Please try a clearer image, or list rooms manually below.",
                "vision_warning": vision_warning or "Cosmic Vision could not detect rooms.",
            }), 422
        return jsonify({"error": "floor_plan must be a non-empty list of rooms"}), 400
    if len(floor_plan) > 12:
        return jsonify({"error": "floor_plan supports at most 12 rooms per scan"}), 400
    for i, room in enumerate(floor_plan):
        if not isinstance(room, dict):
            return jsonify({"error": f"floor_plan[{i}] must be an object"}), 400
        if not room.get("room_type") or not room.get("direction"):
            return jsonify({"error": f"floor_plan[{i}] missing room_type or direction"}), 400

    # ── Auth (X-API-Key + user_id) ────────────────────────────────────────
    user_id = data.get("user_id")
    api_key = request.headers.get("X-API-Key", "")
    if not user_id or not api_key:
        return jsonify({"error": "auth_required",
                        "message": "Login zaroori hai PRO deep-scan ke liye."}), 401
    user = User.query.filter_by(id=user_id, api_key=api_key).first()
    if not user:
        return jsonify({"error": "invalid_credentials"}), 401

    plan = effective_plan(user)

    # ── Profile completeness (multi-profile primary OR legacy kundli) ────
    chart, missing, _name = _resolve_user_chart(user)
    if not chart:
        return jsonify({"error": "profile_incomplete",
                        "missing_fields": missing,
                        "message": "Pehle apni Kundli profile complete karein."}), 422

    # ── Phase-2 unlock gate (Pro / property unlock / monthly basic quota) ─
    property_name = (data.get("property_name") or "").strip()
    quota_check = can_use_astrovastu_pro_v2(user, property_name)
    if not quota_check["allowed"]:
        return jsonify({
            "error":   "upgrade_required",
            "message": quota_check.get("reason",
                       "Buy a PRO Home Scan (₹199), 3-Scan Bundle (₹499), or Full Home Lifetime (₹2,999)."),
            "unlocks": quota_check.get("unlocks", []),
            "plan":    plan,
            "upgrade_required": True,
            "suggested_skus": ["full_home_2999", "shop_999", "office_1499", "factory_2999"],
        }), 402

    # ── Engine pipeline (run BEFORE charging quota — Sprint-2 fix) ──────
    try:
        scan = analyze_floor_plan(floor_plan, chart)
        # Pass classical-rule inputs (adjacency, topography, dimensions) through
        # so the response builder can run those modules and surface findings.
        pro_extras = {
            "room_adjacencies": data.get("room_adjacencies") or [],
            "plot_topography":  data.get("plot_topography")  or {},
            "floor_plan":       floor_plan,  # for per-room dimension_rules
        }
        report = build_pro_response(scan, plan=plan, extras=pro_extras)
    except Exception as exc:
        import traceback; traceback.print_exc()
        return jsonify({"error": "engine_failure"}), 500

    # ── Phase 6: room photo visual findings (optional, non-fatal) ────────
    room_photos = data.get("room_photos")
    if isinstance(room_photos, list) and room_photos:
        try:
            from vision_layer import annotate_report_with_room_photos
            annotate_report_with_room_photos(report, room_photos, lang=lang)
        except Exception as exc:
            print(f"[astrovastu-pro] room photo vision failed (non-fatal): {exc}")
    if vision_data:
        report["vision_floor_plan"] = vision_data
    if vision_warning:
        report["vision_warning"] = vision_warning
    report["vision_used"] = bool(vision_data) or bool(
        (report.get("vision_room_findings") or {}).get("rooms_analyzed", 0)
    )
    # vision_findings_count = total visual findings across all rooms
    _vfc = 0
    for _r in (report.get("rooms") or []):
        _vfc += len(_r.get("visual_findings") or [])
    report["vision_findings_count"] = _vfc

    # ── Phase-2 atomic consume AFTER engine success ──────────────────────
    quota = consume_astrovastu_pro_v2(user, property_name)
    if not quota["allowed"]:
        return jsonify({
            "error":   "upgrade_required",
            "message": quota.get("reason"),
            "plan":    plan,
            "upgrade_required": True,
        }), 402

    report["unlock"] = {
        "via":           quota.get("via"),
        "property_name": property_name or None,
        "plan":          plan,
    }
    # Backward-compat shim for older clients
    report["quota"] = {
        "used":  quota.get("used", 0) or 0,
        "limit": quota.get("limit", -1) if quota.get("via") == "monthly_quota" else -1,
        "plan":  plan,
    }

    # ── Log row (analytics; never blocks user response) ──────────────────
    try:
        log = AstroVastuProLog(
            user_id       = user.id,
            rooms_count   = scan.get("rooms_count", 0),
            overall_score = report["overall"]["score"],
            avoid_count   = report["overall"]["counts"]["avoid"],
            adjust_count  = report["overall"]["counts"]["adjustment_needed"],
            ideal_count   = report["overall"]["counts"]["ideal"],
            lagna         = report["kundli_summary"].get("lagna"),
            mahadasha     = report["kundli_summary"].get("mahadasha"),
            sade_sati     = bool(report["kundli_summary"].get("sade_sati")),
            floor_plan    = json.dumps(floor_plan, ensure_ascii=False),
            plan          = plan,
            property_name = (property_name or None),
            report_json   = json.dumps(report, ensure_ascii=False),
        )
        db.session.add(log)
        db.session.commit()
        report["report_id"] = log.id
        report["pdf_url"]   = f"/api/astrovastu-pro/pdf/{log.id}"
        report["pdf_token"] = make_pdf_token("pro", log.id, user.id)
    except Exception as exc:
        print(f"[astrovastu-pro] log failed: {exc}")
        db.session.rollback()

    return jsonify(report)


# ─────────────────────────────────────────────────────────────────────────────
# Business Vastu (Phase 4) — Shop / Office / Factory deep-scan
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/business-vastu", methods=["POST"])
def business_vastu_route():
    """
    Business Vastu deep-scan for commercial premises.

    Body:
      user_id        : int    (required, authed via X-API-Key)
      business_type  : str    (required, one of "shop"|"office"|"factory")
      floor_plan     : list   (required, 1-15 rooms of {room_type, direction})
      property_name  : str    (required for non-Pro users — drives unlock match)
      partners       : list   (optional, up to 3 user-profile-ids whose
                               kundlis layer in stakeholder synergy)
      muhurat        : dict   (optional, business-start chart input —
                               { dob:"YYYY-MM-DD", tob:"HH:MM", lat, lon, tz, place })

    Returns 200 with full Business Vastu report
            or 400 / 401 / 402 / 422 / 500.

    Gating: Phase-4 — Pro plan OR property_unlock for the matching business
    SKU (shop_999 / office_1499 / factory_2999). NO monthly fallback —
    this is a one-time professional purchase per premise.
    """
    from subscription_helper import (
        can_use_business_vastu_v2, consume_business_vastu_v2, effective_plan,
    )
    from business_vastu_engine import analyze_business
    from business_vastu_response import build_business_response
    from kundli_engine import calculate_kundli
    from models import BusinessVastuLog, Profile
    import json

    data = request.get_json(force=True, silent=True) or {}
    lang = (data.get("lang") or "en").strip().lower()

    # ── Validation ────────────────────────────────────────────────────────
    btype = (data.get("business_type") or "").strip().lower()
    if btype not in ("shop", "office", "factory"):
        return jsonify({"error": "invalid_business_type",
                        "message": "business_type must be shop / office / factory."}), 400

    # ── Phase 6: Cosmic Vision floor-plan extraction (optional, NEVER blocks) ─
    vision_data    = None
    vision_warning = None
    fp_upload = data.get("floor_plan_upload")
    if isinstance(fp_upload, dict) and (fp_upload.get("data_url") or fp_upload.get("base64")):
        try:
            from vision_layer import extract_floor_plan_from_upload
            vd, verr = extract_floor_plan_from_upload(fp_upload, business_type=btype, lang=lang)
        except Exception as exc:
            print(f"[business-vastu] floor-plan vision crashed (non-fatal): {exc}")
            vd, verr = {}, "Cosmic Vision is temporarily unavailable. Continuing with your manual layout."
        if verr:
            vision_warning = verr
        if vd and vd.get("rooms"):
            vision_data = vd
            if not data.get("floor_plan"):
                data["floor_plan"] = vd["rooms"]

    floor_plan = data.get("floor_plan")
    if not isinstance(floor_plan, list) or not floor_plan:
        if fp_upload:
            return jsonify({
                "error":          "vision_inconclusive",
                "message":        vision_warning or "Cosmic Vision could not detect rooms in this upload. Please try a clearer image, or list rooms manually below.",
                "vision_warning": vision_warning or "Cosmic Vision could not detect rooms.",
            }), 422
        return jsonify({"error": "floor_plan must be a non-empty list of rooms"}), 400
    if len(floor_plan) > 15:
        return jsonify({"error": "floor_plan supports at most 15 rooms per scan"}), 400
    for i, room in enumerate(floor_plan):
        if not isinstance(room, dict):
            return jsonify({"error": f"floor_plan[{i}] must be an object"}), 400
        if not room.get("room_type") or not room.get("direction"):
            return jsonify({"error": f"floor_plan[{i}] missing room_type or direction"}), 400

    # ── Auth ──────────────────────────────────────────────────────────────
    user_id = data.get("user_id")
    api_key = request.headers.get("X-API-Key", "")
    if not user_id or not api_key:
        return jsonify({"error": "auth_required",
                        "message": "Login zaroori hai Business Vastu ke liye."}), 401
    user = User.query.filter_by(id=user_id, api_key=api_key).first()
    if not user:
        return jsonify({"error": "invalid_credentials"}), 401

    plan = effective_plan(user)

    # ── Owner kundli (multi-profile primary OR legacy kundli) ────────────
    owner_chart, missing, _name = _resolve_user_chart(user)
    if not owner_chart:
        return jsonify({"error": "profile_incomplete",
                        "missing_fields": missing,
                        "message": "Pehle apni Kundli profile complete karein."}), 422
    # ── Optional partner kundlis (max 3, must belong to this user) ──────
    partner_charts = []
    partner_ids = data.get("partners") or []
    if isinstance(partner_ids, list) and partner_ids:
        for pid in partner_ids[:3]:
            try:    pid_int = int(pid)
            except: continue
            prof = Profile.query.filter_by(id=pid_int, user_id=user.id,
                                            deleted_at=None).first()
            if not prof or not prof.chart_data:
                continue
            try:    partner_charts.append(json.loads(prof.chart_data))
            except: pass

    # ── Optional muhurat chart ──────────────────────────────────────────
    muhurat_chart = None
    muhurat_in    = data.get("muhurat")
    if isinstance(muhurat_in, dict) and muhurat_in.get("dob"):
        try:
            muhurat_chart = calculate_kundli({
                "name":   "Muhurat",
                "day":    int(muhurat_in["dob"].split("-")[2]),
                "month":  int(muhurat_in["dob"].split("-")[1]),
                "year":   int(muhurat_in["dob"].split("-")[0]),
                "hour":   int((muhurat_in.get("tob") or "12:00").split(":")[0]),
                "minute": int((muhurat_in.get("tob") or "12:00").split(":")[1]),
                "ampm":   "AM",
                "lat":    float(muhurat_in.get("lat") or k.lat or 0),
                "lon":    float(muhurat_in.get("lon") or k.lon or 0),
                "tz":     float(muhurat_in.get("tz")  or k.tz  or 5.5),
                "place":  muhurat_in.get("place") or k.pob or "",
            })
        except Exception as exc:
            print(f"[business-vastu] muhurat chart failed (non-fatal): {exc}")
            muhurat_chart = None

    # ── Phase-4 unlock gate ──────────────────────────────────────────────
    property_name = (data.get("property_name") or "").strip()
    gate = can_use_business_vastu_v2(user, btype, property_name)
    if not gate["allowed"]:
        return jsonify({
            "error":            "upgrade_required",
            "message":          gate.get("reason"),
            "required_sku":     gate.get("required_sku"),
            "unlocks":          gate.get("unlocks", []),
            "plan":             plan,
            "upgrade_required": True,
        }), 402

    # ── Engine pipeline (run BEFORE charging — Sprint-2 pattern) ─────────
    try:
        scan   = analyze_business(floor_plan, btype, owner_chart,
                                   partner_kundlis=partner_charts or None,
                                   muhurat_kundli=muhurat_chart)
        if scan.get("error"):
            return jsonify({"error": scan["error"]}), 400
        report = build_business_response(scan, plan=plan)
    except Exception as exc:
        import traceback; traceback.print_exc()
        return jsonify({"error": "engine_failure"}), 500

    # ── Phase 6: room photo visual findings (optional, non-fatal) ────────
    room_photos = data.get("room_photos")
    if isinstance(room_photos, list) and room_photos:
        try:
            from vision_layer import annotate_report_with_room_photos
            annotate_report_with_room_photos(report, room_photos, lang=lang)
        except Exception as exc:
            print(f"[business-vastu] room photo vision failed (non-fatal): {exc}")
    if vision_data:
        report["vision_floor_plan"] = vision_data
    if vision_warning:
        report["vision_warning"] = vision_warning
    report["vision_used"] = bool(vision_data) or bool(
        (report.get("vision_room_findings") or {}).get("rooms_analyzed", 0)
    )
    _vfc = 0
    for _r in (report.get("rooms") or []):
        _vfc += len(_r.get("visual_findings") or [])
    report["vision_findings_count"] = _vfc

    # ── Phase-4 consume (no-op for lifetime model — just re-confirm gate) ─
    consumed = consume_business_vastu_v2(user, btype, property_name)
    if not consumed["allowed"]:
        return jsonify({
            "error":            "upgrade_required",
            "message":          consumed.get("reason"),
            "plan":             plan,
            "upgrade_required": True,
        }), 402

    report["unlock"] = {
        "via":           consumed.get("via"),
        "property_name": property_name or None,
        "plan":          plan,
    }

    # ── Log row (analytics; never blocks user response) ──────────────────
    try:
        counts = report["overall"]["counts"]
        log = BusinessVastuLog(
            user_id       = user.id,
            business_type = btype,
            property_name = property_name or None,
            rooms_count   = scan.get("rooms_count", 0),
            overall_score = report["overall"]["score"],
            avoid_count   = counts.get("avoid", 0),
            adjust_count  = counts.get("adjustment_needed", 0),
            ideal_count   = counts.get("ideal", 0),
            partner_count = len(partner_charts),
            has_muhurat   = muhurat_chart is not None,
            lagna         = (scan.get("owner_context") or {}).get("lagna"),
            mahadasha     = (scan.get("owner_context") or {}).get("mahadasha"),
            floor_plan    = json.dumps(floor_plan, ensure_ascii=False),
            via           = consumed.get("via", "property_unlock"),
            plan          = plan,
            report_json   = json.dumps(report, ensure_ascii=False),
        )
        db.session.add(log)
        db.session.commit()
        report["report_id"] = log.id
        report["pdf_url"]   = f"/api/business-vastu/pdf/{log.id}"
        report["pdf_token"] = make_pdf_token("biz", log.id, user.id)
    except Exception as exc:
        print(f"[business-vastu] log failed: {exc}")
        db.session.rollback()

    return jsonify(report)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4.5 — PDF report endpoints (PRO + Business)
# Auth: X-API-Key header (preferred for API clients) OR a short-lived signed
# `?t=` token (mobile uses Linking.openURL which cannot set headers).
# The token is HMAC-SHA256 over (kind, log_id, user_id, exp) using SESSION_SECRET
# and is valid for ~10 minutes. Long-lived account api_key is NEVER accepted in
# the URL. Ownership: log.user_id must match resolved user.id.
# Canonical brand footer is always enforced at render time.
# ─────────────────────────────────────────────────────────────────────────────
PDF_BRAND_FOOTER = "Powered by Advanced Cosmic Intelligence"
_PDF_TOKEN_TTL_SEC = 600  # 10 minutes


def _pdf_token_secret() -> bytes:
    sec = os.environ.get("SESSION_SECRET")
    if not sec:
        raise RuntimeError(
            "SESSION_SECRET is required for signing PDF access tokens; "
            "refusing to use a predictable fallback."
        )
    return sec.encode()


def make_pdf_token(kind: str, log_id: int, user_id: int,
                   ttl: int = _PDF_TOKEN_TTL_SEC) -> str:
    import hmac as _hmac, hashlib, base64, time as _t
    exp = int(_t.time()) + max(60, int(ttl))
    msg = f"{kind}|{log_id}|{user_id}|{exp}".encode()
    sig = _hmac.new(_pdf_token_secret(), msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{exp}.{sig_b64}"


def _verify_pdf_token(token: str, kind: str, log_id: int) -> int | None:
    """Returns user_id on success, else None."""
    import hmac as _hmac, hashlib, base64, time as _t
    if not token or "." not in token:
        return None
    try:
        exp_str, sig_b64 = token.split(".", 1)
        exp = int(exp_str)
        if exp < int(_t.time()):
            return None
        # Token is signed for *some* user_id; we must brute-force only the
        # log's owner. Caller supplies log_id; we try the log's user_id.
        log = None
        if kind == "biz":
            from models import BusinessVastuLog as _M
            log = db.session.get(_M, log_id)
        elif kind == "pro":
            from models import AstroVastuProLog as _M
            log = db.session.get(_M, log_id)
        if log is None:
            return None
        msg = f"{kind}|{log_id}|{log.user_id}|{exp}".encode()
        expected = _hmac.new(_pdf_token_secret(), msg, hashlib.sha256).digest()
        expected_b64 = base64.urlsafe_b64encode(expected).rstrip(b"=").decode()
        if _hmac.compare_digest(expected_b64, sig_b64):
            return int(log.user_id)
        return None
    except Exception:
        return None


def _resolve_user_for_pdf(kind: str, log_id: int):
    """Header api_key (preferred) OR signed short-lived ?t= token."""
    api_key = (request.headers.get("X-API-Key") or "").strip()
    if api_key:
        return User.query.filter_by(api_key=api_key).first()
    token = (request.args.get("t") or "").strip()
    if token:
        uid = _verify_pdf_token(token, kind, log_id)
        if uid:
            return db.session.get(User, uid)
    return None


@app.route("/api/business-vastu/pdf/<int:log_id>", methods=["GET"])
def business_vastu_pdf(log_id: int):
    import json
    from models import BusinessVastuLog
    user = _resolve_user_for_pdf("biz", log_id)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    log = db.session.get(BusinessVastuLog, log_id)
    if not log or log.user_id != user.id:
        return jsonify({"error": "not_found"}), 404
    if not log.report_json:
        return jsonify({"error": "report_unavailable",
                        "message": "Re-run the scan to generate a fresh PDF."}), 410

    try:
        report = json.loads(log.report_json) if isinstance(log.report_json, str) else log.report_json
    except Exception as e:
        app.logger.exception("[PDF/biz] json parse failed: %s", e)
        return jsonify({"error": "report_corrupt"}), 500

    # Force canonical brand footer (no leakage of LLM/AI mentions)
    if isinstance(report, dict):
        report["footer"] = {"en": PDF_BRAND_FOOTER, "hi": PDF_BRAND_FOOTER}

    user_name = ""
    try:
        if user.kundli and user.kundli.name:
            user_name = user.kundli.name
    except Exception:
        pass

    lang = (request.args.get("lang") or "bilingual").strip().lower()
    try:
        from pdf_renderer import render_business_pdf
        pdf_bytes = render_business_pdf(
            report,
            property_name=log.property_name or "",
            user_name=user_name,
            lang=lang,
        )
    except Exception as e:
        app.logger.exception("[PDF/biz] render failed: %s", e)
        return jsonify({"error": "render_failed"}), 500
    safe_name = (log.property_name or "premise").replace(" ", "_")
    fname = f"BusinessVastu_{log.business_type}_{safe_name}_{log.id}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{fname}"',
            "Cache-Control": "private, max-age=3600",
        },
    )


@app.route("/api/astrovastu-pro/pdf/<int:log_id>", methods=["GET"])
def astrovastu_pro_pdf(log_id: int):
    import json
    from models import AstroVastuProLog
    user = _resolve_user_for_pdf("pro", log_id)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    log = db.session.get(AstroVastuProLog, log_id)
    if not log or log.user_id != user.id:
        return jsonify({"error": "not_found"}), 404
    if not log.report_json:
        return jsonify({"error": "report_unavailable",
                        "message": "Re-run the scan to generate a fresh PDF."}), 410

    try:
        report = json.loads(log.report_json) if isinstance(log.report_json, str) else log.report_json
    except Exception as e:
        app.logger.exception("[PDF/pro] json parse failed: %s", e)
        return jsonify({"error": "report_corrupt"}), 500

    # Force canonical brand footer
    if isinstance(report, dict):
        report["footer"] = PDF_BRAND_FOOTER

    user_name = ""
    try:
        if user.kundli and user.kundli.name:
            user_name = user.kundli.name
    except Exception:
        pass

    property_name = ""
    try:
        property_name = (report.get("meta") or {}).get("property_name") or ""
    except Exception:
        pass

    lang = (request.args.get("lang") or "bilingual").strip().lower()
    try:
        from pdf_renderer import render_pro_pdf
        pdf_bytes = render_pro_pdf(report, property_name=property_name, user_name=user_name, lang=lang)
    except Exception as e:
        app.logger.exception("[PDF/pro] render failed: %s", e)
        return jsonify({"error": "render_failed"}), 500
    fname = f"AstroVastuPRO_{log.id}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{fname}"',
            "Cache-Control": "private, max-age=3600",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 53-N4 — Numerology PDF report
# Stateless endpoint: accepts birth details, computes numerology on-the-fly,
# returns a multi-page PDF. No DB log (numerology has no chart-payload state).
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/numerology/pdf", methods=["POST"])
def numerology_pdf():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    dob  = (body.get("dob")  or "").strip()
    tob  = (body.get("tob")  or "12:00").strip()
    gender = (body.get("gender") or "").strip() or None

    if not name or not dob:
        return jsonify({"error": "missing_fields",
                        "message": "name and dob (YYYY-MM-DD) required"}), 400

    # Strict DOB validation (calendar-correct)
    from datetime import datetime as _dt
    try:
        _dt.strptime(dob, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "invalid_dob",
                        "message": "dob must be a valid date in YYYY-MM-DD format"}), 400

    # Optional tob validation (HH:MM 24h)
    if tob:
        try:
            _dt.strptime(tob, "%H:%M")
        except ValueError:
            return jsonify({"error": "invalid_tob",
                            "message": "tob must be in HH:MM 24-hour format"}), 400

    birth = {"name": name, "dob": dob, "tob": tob, "gender": gender or "male"}

    try:
        from vedic.numerology.phase_s import compute_phase_s
        from vedic.numerology.extended import compute_extended_numerology
        from vedic.numerology.practical import compute_practical
        from numerology_pdf import render_numerology_pdf

        ps = compute_phase_s({}, birth) or {}
        ex = compute_extended_numerology(birth) or {}
        pr = compute_practical(birth) or {}

        # Require at least the core numerology block (extended) to be available;
        # phase_s often defaults to True via static directions.
        if not ex.get("available"):
            return jsonify({"error": "compute_failed",
                            "message": "numerology engines returned no data"}), 500

        pdf_bytes = render_numerology_pdf(
            name=name, dob=dob, gender=gender,
            phase_s=ps, extended=ex, practical=pr,
        )
    except Exception as e:
        # Log full trace internally; never leak exception details to client.
        app.logger.exception("[numerology/pdf] render failed: %s", e)
        return jsonify({"error": "render_failed",
                        "message": "Failed to render PDF. Please try again."}), 500

    safe_name = "".join(c for c in name if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "report"
    fname = f"Numerology_{safe_name}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{fname}"',
            "Cache-Control": "private, max-age=3600",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — Reports history (combined BIZ + PRO)
# ─────────────────────────────────────────────────────────────────────────────
def _grade_for(score: int) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "E"


@app.route("/api/user/<int:user_id>/reports/history", methods=["GET"])
def reports_history_route(user_id):
    """
    Returns the user's combined paid-scan history (newest first).
    Each item carries a freshly-issued short-lived `pdf_token` so the mobile
    client can open the PDF without a second auth round-trip.

    Auth: user_id + X-API-Key header.
    """
    from models import BusinessVastuLog, AstroVastuProLog

    user, err = get_authed_user(user_id)
    if err:
        return err

    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
    except (TypeError, ValueError):
        limit = 50

    items = []

    biz_rows = (BusinessVastuLog.query
                .filter_by(user_id=user.id)
                .order_by(BusinessVastuLog.created_at.desc())
                .limit(limit).all())
    for r in biz_rows:
        items.append({
            "kind":          "business",
            "id":            r.id,
            "property_name": r.property_name or f"{(r.business_type or '').title()} scan",
            "business_type": r.business_type,
            "rooms_count":   r.rooms_count,
            "score":         r.overall_score,
            "grade":         _grade_for(r.overall_score or 0),
            "created_at":    r.created_at.isoformat() if r.created_at else None,
            "pdf_url":       f"/api/business-vastu/pdf/{r.id}",
            "pdf_token":     make_pdf_token("biz", r.id, user.id),
        })

    pro_rows = (AstroVastuProLog.query
                .filter_by(user_id=user.id)
                .order_by(AstroVastuProLog.created_at.desc())
                .limit(limit).all())
    for r in pro_rows:
        items.append({
            "kind":          "pro",
            "id":            r.id,
            "property_name": getattr(r, "property_name", None) or "Home deep-scan",
            "business_type": None,
            "rooms_count":   r.rooms_count,
            "score":         r.overall_score,
            "grade":         _grade_for(r.overall_score or 0),
            "created_at":    r.created_at.isoformat() if r.created_at else None,
            "pdf_url":       f"/api/astrovastu-pro/pdf/{r.id}",
            "pdf_token":     make_pdf_token("pro", r.id, user.id),
        })

    items.sort(key=lambda x: x["created_at"] or "", reverse=True)
    items = items[:limit]

    return jsonify({"count": len(items), "items": items})


# ─────────────────────────────────────────────────────────────────────────────
# AstroVastu  —  Phase-2 Status & Purchase Intent endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/astrovastu/status", methods=["GET", "POST"])
def astrovastu_status_route():
    """
    Returns the user's AstroVastu unlock state:
      { plan, room_credits, unlocked_properties:[{name,tier,unlocked_at}],
        catalog:{sku:{price,label,grants}}, monthly_pro_used, monthly_pro_limit }
    Auth: user_id + X-API-Key (mandatory).
    """
    from subscription_helper import (
        SKU_CATALOG, list_unlocked_properties, effective_plan,
        astrovastu_pro_monthly_limit,
    )
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id") or request.args.get("user_id")
    api_key = request.headers.get("X-API-Key", "").strip()
    if not user_id or not api_key:
        return jsonify({"error": "auth_required"}), 401
    user = User.query.filter_by(id=user_id, api_key=api_key).first()
    if not user:
        return jsonify({"error": "invalid_credentials"}), 401

    plan = effective_plan(user)
    return jsonify({
        "plan":                 plan,
        "is_pro":               plan == "pro",
        "room_credits":         user.astrovastu_room_credits or 0,
        "unlocked_properties":  list_unlocked_properties(user),
        "monthly_pro_used":     user.monthly_astrovastu_pro_used or 0,
        "monthly_pro_limit":    astrovastu_pro_monthly_limit(user),
        "catalog":              SKU_CATALOG,
    })


@app.route("/api/astrovastu/intent", methods=["POST"])
def astrovastu_purchase_intent_route():
    """
    Creates a one-time payment intent for an AstroVastu SKU. Returns the
    purchase row id + the SKU spec. Phase 3 will hook this to Cashfree
    (creates a Cashfree order, returns payment_session_id).

    Body: { user_id, sku, property_name? }
    Headers: X-API-Key
    """
    from subscription_helper import SKU_CATALOG, effective_plan
    from models import AstroVastuPurchase

    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id")
    api_key = request.headers.get("X-API-Key", "").strip()
    sku     = (data.get("sku") or "").strip()
    pname   = (data.get("property_name") or "").strip()

    if not user_id or not api_key:
        return jsonify({"error": "auth_required"}), 401
    user = User.query.filter_by(id=user_id, api_key=api_key).first()
    if not user:
        return jsonify({"error": "invalid_credentials"}), 401

    spec = SKU_CATALOG.get(sku)
    if not spec:
        return jsonify({"error": "invalid_sku", "valid_skus": list(SKU_CATALOG.keys())}), 400
    if spec["grants"] == "unlock" and not pname:
        return jsonify({"error": "property_name_required",
                        "message": "Please name this property (e.g. 'Mumbai Flat')."}), 400

    purchase = AstroVastuPurchase(
        user_id       = user.id,
        sku           = sku,
        amount        = spec["price"],
        property_name = pname or None,
        status        = "created",
    )
    db.session.add(purchase)
    db.session.commit()

    return jsonify({
        "purchase_id":        purchase.id,
        "sku":                sku,
        "amount":             spec["price"],
        "label":              spec["label"],
        "grants":             spec["grants"],
        "property_name":      pname or None,
        "plan":               effective_plan(user),
        "payment_session_id": None,
        "payment_url":        None,
        "status":             "created",
        "message":            "Payment integration arrives in Phase 3 — purchase logged.",
    })


@app.route("/api/astrovastu/create-order", methods=["POST", "OPTIONS"])
def astrovastu_create_order_route():
    """
    Phase 3 — Cashfree one-time order for an AstroVastu SKU.

    Flow:
      1. Validate user + SKU (and property_name for unlock SKUs).
      2. Create or reuse an AstroVastuPurchase row (status=created).
      3. POST to Cashfree /pg/orders with order_tags={kind:astrovastu, purchase_id}.
      4. Persist returned cf order_id back on the purchase row.
      5. Return { payment_session_id, payment_link, order_id, purchase_id }.

    Body: { user_id, sku, property_name?, purchase_id? }
    Headers: X-API-Key
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    import urllib.request as _req, urllib.error as _err_mod, json as _json
    from subscription_helper import SKU_CATALOG
    from models import AstroVastuPurchase

    if not CASHFREE_APP_ID or not CASHFREE_SECRET:
        return jsonify({"error": "cashfree_not_configured"}), 503

    data    = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id")
    api_key = request.headers.get("X-API-Key", "").strip()
    sku     = (data.get("sku") or "").strip()
    pname   = (data.get("property_name") or "").strip()
    pid_in  = data.get("purchase_id")

    if not user_id or not api_key:
        return jsonify({"error": "auth_required"}), 401
    user = User.query.filter_by(id=user_id, api_key=api_key).first()
    if not user:
        return jsonify({"error": "invalid_credentials"}), 401

    spec = SKU_CATALOG.get(sku)
    if not spec:
        return jsonify({"error": "invalid_sku",
                        "valid_skus": list(SKU_CATALOG.keys())}), 400
    if spec["grants"] == "unlock" and not pname:
        return jsonify({"error": "property_name_required"}), 400

    # Reuse existing intent if caller provided a still-pending purchase_id.
    purchase = None
    if pid_in:
        purchase = AstroVastuPurchase.query.get(pid_in)
        if purchase and (purchase.user_id != user.id or
                         purchase.status != "created" or
                         purchase.sku != sku):
            purchase = None
    if not purchase:
        purchase = AstroVastuPurchase(
            user_id       = user.id,
            sku           = sku,
            amount        = spec["price"],
            property_name = pname or None,
            status        = "created",
        )
        db.session.add(purchase)
        db.session.commit()

    # Order id encodes user + purchase so webhook + status route can route fast.
    ts       = int(datetime.utcnow().timestamp())
    order_id = f"AV{user.id}_{purchase.id}_{ts}"

    return_url = (
        f"{os.environ.get('API_BASE', 'http://localhost:8080')}/api/payment/return"
        f"?order_id={order_id}&plan=astrovastu&cycle=onetime"
    )

    cust_email = (user.email or "").strip() or f"user{user.id}@cosmiclens.app"
    raw_phone  = (user.phone or "").strip()
    digits     = "".join(c for c in raw_phone if c.isdigit())
    cust_phone = digits[-10:] if len(digits) >= 10 else "9999999999"

    payload = {
        "order_id":       order_id,
        "order_amount":   spec["price"],
        "order_currency": "INR",
        "customer_details": {
            "customer_id":    str(user.id),
            "customer_name":  user.name or "User",
            "customer_email": cust_email,
            "customer_phone": cust_phone,
        },
        "order_meta": {"return_url": return_url},
        # PII-minimised tags — purchase_id is the canonical link back to our
        # DB row (which holds property_name + user_id). We deliberately
        # exclude user_id and property_name from Cashfree metadata.
        "order_tags": {
            "kind":        "astrovastu",
            "purchase_id": str(purchase.id),
            "sku":         sku,
        },
    }

    body   = _json.dumps(payload).encode()
    cf_req = _req.Request(
        f"{_cf_base()}/orders", data=body,
        headers={
            "Content-Type":    "application/json",
            "x-client-id":     CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET,
            "x-api-version":   "2023-08-01",
        },
        method="POST",
    )
    app.logger.info(f"[CF-AV] POST /orders  order={order_id}  amt=₹{spec['price']}  user={user.id}  sku={sku}")
    try:
        with _req.urlopen(cf_req, timeout=15) as resp:
            result = _json.loads(resp.read())
    except _err_mod.HTTPError as e:
        try:    detail = e.read().decode()
        except: detail = ""
        app.logger.error(f"[CF-AV] HTTP {e.code} on /orders: {detail}")
        return jsonify({"error": "cashfree_order_failed",
                        "code": e.code, "detail": detail}), 502
    except Exception as e:
        app.logger.error(f"[CF-AV] network error: {e}")
        return jsonify({"error": str(e)}), 502

    session_id = result.get("payment_session_id", "")
    if not session_id:
        app.logger.error(f"[CF-AV] no session id in response: {result}")
        return jsonify({"error": "cashfree_no_session", "raw": result}), 502

    purchase.order_id = order_id
    db.session.commit()

    payment_link = _cf_payment_url(session_id)
    app.logger.info(f"[CF-AV] OK  cf_order={result.get('cf_order_id')}  session=...{session_id[-12:]}")

    return jsonify({
        "purchase_id":        purchase.id,
        "order_id":           order_id,
        "payment_session_id": session_id,
        "payment_link":       payment_link,
        "amount":             spec["price"],
        "sku":                sku,
        "label":              spec["label"],
        "grants":             spec["grants"],
        "property_name":      pname or None,
    })


@app.route("/api/astrovastu/purchase-status/<int:purchase_id>", methods=["GET", "OPTIONS"])
def astrovastu_purchase_status_route(purchase_id):
    """
    Mobile polling endpoint after the Cashfree WebView returns. Idempotent.

    Behaviour:
      1. Returns the current AstroVastuPurchase row for the authed user.
      2. If status is still 'created' AND we have a Cashfree order_id, polls
         Cashfree once, and on SUCCESS marks paid + grants idempotently.
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    import urllib.request as _req, json as _json
    from subscription_helper import grant_purchase_idempotent
    from models import AstroVastuPurchase

    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key:
        return jsonify({"error": "auth_required"}), 401

    purchase = AstroVastuPurchase.query.get(purchase_id)
    if not purchase:
        return jsonify({"error": "purchase_not_found"}), 404

    user = User.query.filter_by(id=purchase.user_id, api_key=api_key).first()
    if not user:
        return jsonify({"error": "invalid_credentials"}), 401

    # Live-poll Cashfree if we still think the order is open.
    if purchase.status == "created" and purchase.order_id and CASHFREE_APP_ID and CASHFREE_SECRET:
        try:
            cf_req = _req.Request(
                f"{_cf_base()}/orders/{purchase.order_id}/payments",
                headers={
                    "x-client-id":     CASHFREE_APP_ID,
                    "x-client-secret": CASHFREE_SECRET,
                    "x-api-version":   "2023-08-01",
                },
            )
            with _req.urlopen(cf_req, timeout=10) as resp:
                payments = _json.loads(resp.read())
            if not isinstance(payments, list):
                payments = []
            if any(p.get("payment_status") == "SUCCESS" for p in payments):
                purchase.status  = "paid"
                purchase.paid_at = datetime.utcnow()
                db.session.commit()
                grant_purchase_idempotent(purchase)
                db.session.refresh(purchase)
                db.session.refresh(user)
            elif any(p.get("payment_status") in ("FAILED", "USER_DROPPED", "CANCELLED")
                     for p in payments):
                # Don't flip to failed — user can retry the same intent.
                pass
        except Exception as e:
            app.logger.warning(f"[CF-AV] poll error for order {purchase.order_id}: {e}")

    return jsonify({
        "purchase_id":   purchase.id,
        "sku":           purchase.sku,
        "amount":        purchase.amount,
        "property_name": purchase.property_name,
        "order_id":      purchase.order_id,
        "status":        purchase.status,        # created / paid / failed / expired
        "granted":       bool(purchase.granted),
        "paid_at":       purchase.paid_at.isoformat() if purchase.paid_at else None,
        "room_credits":  user.astrovastu_room_credits or 0,
        "is_pro":        bool(getattr(user, "is_pro", False)),
    })


@app.route("/api/astrovastu/dev-grant", methods=["POST"])
def astrovastu_dev_grant_route():
    """
    DEV-ONLY: marks a created purchase as paid and grants the credits/unlock.
    Disabled in production. Used to test Phase-2 unlock flow before Phase-3
    Cashfree integration is live.

    Body: { user_id, purchase_id }
    Headers: X-API-Key
    """
    import os as _os
    from subscription_helper import grant_purchase_idempotent
    from models import AstroVastuPurchase

    # SECURE-BY-DEFAULT — must explicitly opt in via env flag AND not be prod.
    if (_os.environ.get("ASTROVASTU_DEV_GRANT_ENABLED") or "").strip() != "1":
        return jsonify({"error": "dev_grant_disabled",
                        "message": "Set ASTROVASTU_DEV_GRANT_ENABLED=1 to enable in dev."}), 403
    if (_os.environ.get("FLASK_ENV") or "").lower() == "production":
        return jsonify({"error": "disabled_in_production"}), 403

    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id")
    api_key = request.headers.get("X-API-Key", "").strip()
    pid     = data.get("purchase_id")
    if not user_id or not api_key:
        return jsonify({"error": "auth_required"}), 401
    user = User.query.filter_by(id=user_id, api_key=api_key).first()
    if not user:
        return jsonify({"error": "invalid_credentials"}), 401

    purchase = AstroVastuPurchase.query.get(pid)
    if not purchase or purchase.user_id != user.id:
        return jsonify({"error": "purchase_not_found"}), 404

    from datetime import datetime as _dt
    purchase.status  = "paid"
    purchase.paid_at = _dt.utcnow()
    db.session.commit()

    result = grant_purchase_idempotent(purchase)
    db.session.refresh(user)
    return jsonify({"purchase_id": pid, **result,
                    "room_credits": user.astrovastu_room_credits})


@app.route("/api/ask", methods=["POST"])
def ask_route():
    """
    AI Ask engine — rule-based astrology question analysis.
    Body: { question, kundli, lang, replyIdx, user_id }
    Returns: { text, topic, confidence, quota:{used,limit} }
    On limit hit returns 402 with {error, quota, upgrade_required:true}.
    """
    from subscription_helper import consume_question, effective_plan

    data = request.get_json(force=True, silent=True) or {}
    question  = data.get("question", "")
    kundli    = data.get("kundli")
    birth     = data.get("birthData") or data.get("birth")
    history   = data.get("history") or []
    lang      = data.get("lang", "en")
    reply_idx = int(data.get("replyIdx", 0))
    user_id   = data.get("user_id")

    if not question:
        return jsonify({"error": "question is required"}), 400

    # ── Daily-quota gate (auth mandatory when user_id supplied) ──────────────
    user = None
    if user_id:
        # user_id may arrive as a JSON string from the mobile client. Coerce
        # to int safely; treat anything non-numeric as anonymous rather than
        # crashing the SQLAlchemy primary-key lookup.
        try:
            uid_int = int(str(user_id).strip())
        except (TypeError, ValueError):
            uid_int = None
        user = User.query.get(uid_int) if uid_int is not None else None
        if not user:
            return jsonify({"error": "User not found"}), 404
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key or user.api_key != api_key:
            return jsonify({"error": "Unauthorized"}), 401

        quota = consume_question(user)
        if not quota["allowed"]:
            return jsonify({
                "error":            "daily_limit_reached",
                "message":          f"Aaj ka {quota['limit']} questions ka limit poora ho gaya. Pro upgrade karein for unlimited.",
                "quota":            {"used": quota["used"], "limit": quota["limit"]},
                "plan":             effective_plan(user),
                "upgrade_required": True,
            }), 402
    else:
        # Anonymous fallback — kept for legacy callers (e.g. preview/demo).
        # No persistence; loose 1/req behaviour. Mobile clients should always
        # send user_id+X-API-Key so quota truly enforces.
        quota = {"used": 0, "limit": 1}

    # ── Run engine ───────────────────────────────────────────────────────────
    # Strategy: try OpenAI (richer, conversational answers). On any failure
    # — missing key, rate limit, network error — silently fall back to the
    # deterministic rule-based engine so the user never sees an outage.
    result = None
    used_ai = False
    # Sticky reply-language preference: set by user in app settings; overrides
    # per-question language detection. None → fall back to detection + lang.
    preferred_language = (user.preferred_language if user else None)

    if openai_available():
        try:
            result = ai_ask(question, kundli, lang, reply_idx, birth=birth,
                            history=history, preferred_language=preferred_language)
            used_ai = True
        except Exception as exc:
            print(f"[ask] OpenAI failed, falling back to rule engine: {exc}")
            result = None

    if result is None:
        try:
            result = process_ask(question, kundli, lang, reply_idx)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(exc)}), 500

    if isinstance(result, dict):
        result["quota"]  = {"used": quota["used"], "limit": quota["limit"]}
        result["plan"]   = effective_plan(user) if user else "free"
        result["source"] = result.get("source", "ai" if used_ai else "rules")
    return jsonify(result)


# ── Streaming variant of /api/ask ────────────────────────────────────────────
# Returns either:
#   • text/event-stream  — token deltas for the streamable OpenAI path, ending
#                          with a single {"done": true, ...} payload that
#                          carries the FINAL scrubbed text + topic + follow_ups
#                          + quota + plan. Mobile must trust `text` from the
#                          done event over the accumulated deltas (scrubber
#                          may have removed banned words).
#   • application/json   — single-shot result for non-streamable paths
#                          (brand_guard, no-chart fail-safe, marriage
#                          deterministic engine). Same shape as /api/ask so
#                          the frontend can branch purely on Content-Type.
@app.route("/api/ask/stream", methods=["POST"])
def ask_stream_route():
    from subscription_helper import consume_question, effective_plan
    import itertools

    data = request.get_json(force=True, silent=True) or {}
    question  = data.get("question", "")
    kundli    = data.get("kundli")
    birth     = data.get("birthData") or data.get("birth")
    history   = data.get("history") or []
    lang      = data.get("lang", "en")
    reply_idx = int(data.get("replyIdx", 0))
    user_id   = data.get("user_id")

    if not question:
        return jsonify({"error": "question is required"}), 400

    # ── Auth + quota — identical contract to /api/ask ────────────────────────
    user = None
    if user_id:
        try:
            uid_int = int(str(user_id).strip())
        except (TypeError, ValueError):
            uid_int = None
        user = User.query.get(uid_int) if uid_int is not None else None
        if not user:
            return jsonify({"error": "User not found"}), 404
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key or user.api_key != api_key:
            return jsonify({"error": "Unauthorized"}), 401
        quota = consume_question(user)
        if not quota["allowed"]:
            return jsonify({
                "error":            "daily_limit_reached",
                "message":          f"Aaj ka {quota['limit']} questions ka limit poora ho gaya. Pro upgrade karein for unlimited.",
                "quota":            {"used": quota["used"], "limit": quota["limit"]},
                "plan":             effective_plan(user),
                "upgrade_required": True,
            }), 402
    else:
        quota = {"used": 0, "limit": 1}

    preferred_language = (user.preferred_language if user else None)
    quota_payload = {"used": quota["used"], "limit": quota["limit"]}
    plan_payload  = effective_plan(user) if user else "free"

    # ── No OpenAI → degrade gracefully to rule-engine JSON (no streaming). ──
    if not openai_available():
        try:
            result = process_ask(question, kundli, lang, reply_idx)
        except Exception as exc:
            import traceback; traceback.print_exc()
            return jsonify({"error": str(exc)}), 500
        if isinstance(result, dict):
            result["quota"]  = quota_payload
            result["plan"]   = plan_payload
            result["source"] = result.get("source", "rules")
        return jsonify(result)

    # ── Probe first event to decide stream vs one-shot vs hard-fallback ────
    try:
        gen   = ai_ask_stream(question, kundli, lang, reply_idx, birth=birth,
                              history=history, preferred_language=preferred_language)
        first = next(gen)
    except StopIteration:
        first = None
    except Exception as exc:
        print(f"[ask/stream] generator setup failed → fallback to ai_ask: {exc}")
        first = None

    # On any stream-setup failure, fall back to non-streaming ai_ask → rule_engine
    if first is None:
        used_ai = True
        try:
            result = ai_ask(question, kundli, lang, reply_idx, birth=birth,
                            history=history, preferred_language=preferred_language)
        except Exception as exc:
            print(f"[ask/stream] ai_ask fallback failed → rule engine: {exc}")
            used_ai = False
            try:
                result = process_ask(question, kundli, lang, reply_idx)
            except Exception as exc2:
                import traceback; traceback.print_exc()
                return jsonify({"error": str(exc2)}), 500
        if isinstance(result, dict):
            result["quota"]  = quota_payload
            result["plan"]   = plan_payload
            result["source"] = result.get("source", "ai" if used_ai else "rules")
        return jsonify(result)

    # One-shot paths (brand_guard / no_chart / marriage) → return as JSON.
    if first.get("kind") == "oneshot":
        result = first.get("data") or {}
        if isinstance(result, dict):
            result["quota"]  = quota_payload
            result["plan"]   = plan_payload
            result["source"] = result.get("source", "ai")
        return jsonify(result)

    # ── True SSE stream ──────────────────────────────────────────────────────
    def sse():
        try:
            for evt in itertools.chain([first], gen):
                kind = evt.get("kind")
                if kind == "delta":
                    yield "data: " + json.dumps(
                        {"delta": evt.get("text", "")},
                        ensure_ascii=False,
                    ) + "\n\n"
                elif kind == "final":
                    yield "data: " + json.dumps({
                        "done":       True,
                        "text":       evt.get("text", ""),
                        "topic":      evt.get("topic", "general"),
                        "confidence": evt.get("confidence", 0.0),
                        "source":     evt.get("source", "openai_stream"),
                        "follow_ups": evt.get("follow_ups", []),
                        "quota":      quota_payload,
                        "plan":       plan_payload,
                    }, ensure_ascii=False) + "\n\n"
        except Exception as exc:
            print(f"[ask/stream] mid-stream error: {exc}")
            yield "data: " + json.dumps(
                {"error": str(exc)},
                ensure_ascii=False,
            ) + "\n\n"

    from flask import Response
    return Response(
        sse(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":      "no-cache, no-transform",
            "Connection":         "keep-alive",
            "X-Accel-Buffering":  "no",
        },
    )


# ── Divya Prashna — Horary (Time Prashna) ────────────────────────────────────

@app.route("/api/prashna/categories", methods=["GET"])
def prashna_categories_route():
    """Return the list of supported Divya Prashna categories for the UI."""
    from prashna_engine import list_categories
    return jsonify({"categories": list_categories()})


@app.route("/api/prashna/ask", methods=["POST"])
def prashna_ask_route():
    """
    Divya Prashna — answer a horary question using the live KP cusp chart
    cast for the current server time at Bhubaneswar (astrologer's seat).

    Body JSON:
      {
        "question": "Mera sona milega?"   (required, free text),
        "category": "stolen_item" | ...   (optional, auto-inferred if omitted),
        "user_id":  <int>                 (optional, for daily-quota gate)
      }

    Returns the prashna_engine result. Daily quota: same as /api/ask.
    """
    from prashna_engine import ask_prashna
    from subscription_helper import consume_question, effective_plan

    data     = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    category = data.get("category")
    user_id  = data.get("user_id")

    if not question:
        return jsonify({"error": "question is required"}), 400

    # ── Optional auth + daily quota (mirrors /api/ask) ───────────────────────
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key or user.api_key != api_key:
            return jsonify({"error": "Unauthorized"}), 401

        quota = consume_question(user)
        if not quota["allowed"]:
            return jsonify({
                "error":            "daily_limit_reached",
                "message":          (
                    f"Aaj ka {quota['limit']} prashna ka limit poora ho gaya. "
                    "Pro upgrade karein for unlimited."
                ),
                "quota":            {"used": quota["used"], "limit": quota["limit"]},
                "plan":             effective_plan(user),
                "upgrade_required": True,
            }), 402

    try:
        result = ask_prashna(question=question, category=category)
    except Exception:
        app.logger.exception("[Divya Prashna] failed")
        return jsonify({
            "error":   "internal_error",
            "message": "Prashna chart banane mein samasya hui. Punah prayaas karein.",
        }), 500

    return jsonify(result)


# ── Prashna Kundli — KP Number Horary (1-249) ────────────────────────────────

@app.route("/api/prashna/number-ask", methods=["POST"])
def prashna_number_ask_route():
    """
    KP Horary by number (Cuspal Interlinks Theory). The querent picks a
    number 1-249; that number forces the lagna of a chart cast at the
    current moment in Bhubaneswar. The cuspal sub-lord at the relevant
    house yields a deterministic Yes/No/Conditional verdict.

    Body JSON:
      {
        "number":   <int 1..249>            (required),
        "question": "Mera vivah kab hoga?"  (optional, used for category infer),
        "category": "marriage" | ...        (optional, overrides inference),
        "user_id":  <int>                   (optional, for daily quota)
      }
    """
    from prashna_engine import ask_number_prashna, KP_249_COUNT
    from subscription_helper import consume_question, effective_plan

    data     = request.get_json(force=True, silent=True) or {}
    raw_n    = data.get("number")
    question = (data.get("question") or "").strip()
    category = data.get("category")
    user_id  = data.get("user_id")

    try:
        number = int(raw_n)
    except (TypeError, ValueError):
        return jsonify({"error": f"number must be an integer 1..{KP_249_COUNT}"}), 400
    if number < 1 or number > KP_249_COUNT:
        return jsonify({"error": f"number must be 1..{KP_249_COUNT}"}), 400

    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key or user.api_key != api_key:
            return jsonify({"error": "Unauthorized"}), 401

        quota = consume_question(user)
        if not quota["allowed"]:
            return jsonify({
                "error":            "daily_limit_reached",
                "message":          (
                    f"Aaj ka {quota['limit']} prashna ka limit poora ho gaya. "
                    "Pro upgrade karein for unlimited."
                ),
                "quota":            {"used": quota["used"], "limit": quota["limit"]},
                "plan":             effective_plan(user),
                "upgrade_required": True,
            }), 402

    try:
        result = ask_number_prashna(number=number, question=question, category=category)
    except Exception:
        app.logger.exception("[Prashna Number] failed")
        return jsonify({
            "error":   "internal_error",
            "message": "Prashna kundli banane mein samasya hui. Punah prayaas karein.",
        }), 500

    return jsonify(result)


# ── Future Partner Portrait — async task with progress ───────────────────────

@app.route("/api/partner-portrait/start", methods=["POST"])
def partner_portrait_start_route():
    """
    Kick off async portrait generation. Body:
      {
        "kundli":      <kundli dict from /api/kundli>  (required),
        "birth_data":  <birth dict>                    (optional, enables KP layer),
        "user_gender": "male" | "female"               (optional, default male),
        "user_id":     <int>                           (optional, for future quota gating)
      }
    Returns: { task_id, status: "queued" }
    """
    from partner_portrait_engine import start_portrait_task

    data        = request.get_json(force=True, silent=True) or {}
    kundli      = data.get("kundli")
    birth_data  = data.get("birth_data")
    user_gender = (data.get("user_gender") or "male").lower()
    if user_gender not in ("male", "female"):
        user_gender = "male"

    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return jsonify({"error": "kundli is required"}), 400

    # Optional auth (mirrors /api/ask)
    user_id = data.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key or user.api_key != api_key:
            return jsonify({"error": "Unauthorized"}), 401

    try:
        task_id = start_portrait_task(kundli, birth_data, user_gender)
    except Exception:
        app.logger.exception("[partner-portrait] start failed")
        return jsonify({
            "error":   "internal_error",
            "message": "Portrait shuru nahi ho saka. Punah prayaas karein.",
        }), 500

    return jsonify({"task_id": task_id, "status": "queued"})


@app.route("/api/partner-portrait/status/<task_id>", methods=["GET"])
def partner_portrait_status_route(task_id):
    """Poll the status of a running portrait task. Returns progress 0-100 + image_url when done."""
    from partner_portrait_engine import get_task_status
    status = get_task_status(task_id)
    if not status:
        return jsonify({"error": "task_not_found"}), 404
    return jsonify(status)


# ── Vastu Drishti Scan (vision) ───────────────────────────────────────────────

@app.route("/api/vastu-scan", methods=["POST"])
def vastu_scan_route():
    """
    Vastu Drishti — analyze a room photo via Acharya Vidyasagar persona.
    Body JSON:
      {
        "image":     "data:image/jpeg;base64,..."  (required),
        "room":      "bedroom" | "kitchen" | "pooja" | ...  (optional),
        "lang":      "hn" | "hi" | "en" | ...               (optional),
        "user_id":   <int>                                  (optional, for quota)
      }
    Returns: { text, room, source, quota:{used,limit}, plan }

    Quota: Vastu Scan counts against the daily question quota (one scan = one
    question) so free-tier abuse is bounded. Free plan = 3/day.
    """
    from subscription_helper import consume_question, effective_plan

    data = request.get_json(force=True, silent=True) or {}
    image   = (data.get("image") or "").strip()
    room    = (data.get("room") or "room").strip() or "room"
    lang    = data.get("lang", "en")
    user_id = data.get("user_id")

    # Optional REAL device sensor reading (compass heading at scan time).
    # Single biggest accuracy lever — when present, the LLM uses this as
    # ground truth for directional analysis instead of guessing.
    heading_raw = data.get("heading_deg")
    heading_deg: float | None = None
    if heading_raw is not None:
        try:
            heading_deg = float(heading_raw)
            if not (0.0 <= heading_deg < 360.0):
                heading_deg = heading_deg % 360.0
        except (TypeError, ValueError):
            heading_deg = None

    if not image:
        return jsonify({"error": "image is required"}), 400

    # Cap payload at ~10MB raw to keep OpenAI costs in check.
    if len(image) > 10 * 1024 * 1024:
        return jsonify({"error": "image too large (max 10 MB)"}), 413

    if not openai_available():
        return jsonify({
            "error":   "vastu_scan_unavailable",
            "message": "Vastu Drishti seva abhi temporarily band hai — kuch der baad try karein.",
        }), 503

    # ── PRO-tier gate (Cosmic Vision API costs ~₹2-3/scan; PRO+ only) ────────
    if not user_id:
        return jsonify({
            "error":            "login_required",
            "message":          "AstroVastu PRO unlock karne ke liye login zaroori hai.",
            "upgrade_required": True,
        }), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key or user.api_key != api_key:
        return jsonify({"error": "Unauthorized"}), 401

    plan = effective_plan(user)
    if plan not in ("pro", "trial"):
        return jsonify({
            "error":            "upgrade_required",
            "message":          "Vastu Drishti scanner sirf AstroVastu PRO members ke liye hai. ₹199 ek baar mein unlock karein.",
            "plan":             plan,
            "upgrade_required": True,
        }), 402

    quota = consume_question(user)
    if not quota["allowed"]:
        return jsonify({
            "error":            "daily_limit_reached",
            "message":          f"Aaj ka {quota['limit']} scans ka limit poora ho gaya.",
            "quota":            {"used": quota["used"], "limit": quota["limit"]},
            "plan":             plan,
            "upgrade_required": True,
        }), 402

    try:
        result = vastu_scan(image, room, lang, heading_deg=heading_deg)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error":   "vastu_scan_failed",
            "message": "Photo analyze nahi ho payi. Ek baar phir se acchi roshni mein photo lekar try karein.",
            "detail":  str(exc),
        }), 500

    result["quota"] = {"used": quota["used"], "limit": quota["limit"]}
    result["plan"]  = effective_plan(user) if user else "free"
    return jsonify(result)


# ── Vastu Drishti DEEP Scan (Phase 2 — multi-photo guided 4-wall capture) ─────

@app.route("/api/vastu-deep-scan", methods=["POST"])
def vastu_deep_scan_route():
    """
    Deep multi-photo Vastu analysis. Builds a complete spatial map by
    cross-referencing 2-6 directional photos (each tagged with REAL device
    magnetometer heading) plus an optional top-down floor plan.

    Body JSON:
      {
        "photos": [
          {"image": "data:image/jpeg;base64,...", "heading_deg": 0,   "label": "north_wall"},
          {"image": "data:image/jpeg;base64,...", "heading_deg": 90,  "label": "east_wall"},
          {"image": "data:image/jpeg;base64,...", "heading_deg": 180, "label": "south_wall"},
          {"image": "data:image/jpeg;base64,...", "heading_deg": 270, "label": "west_wall"}
        ],
        "floor_plan":  "data:image/jpeg;base64,..."  (optional, top-down view),
        "room":        "bedroom",
        "lang":        "hn",
        "user_id":     <int>  (REQUIRED — login required for deep scan)
      }

    Quota: deep scan consumes 1 question unit (cost ~₹3-5/scan).
    """
    from subscription_helper import consume_question, effective_plan
    from openai_helper       import vastu_deep_scan

    data       = request.get_json(force=True, silent=True) or {}
    photos_raw = data.get("photos") or []
    floor_plan = (data.get("floor_plan") or "").strip() or None
    room       = (data.get("room") or "room").strip() or "room"
    lang       = data.get("lang", "en")
    user_id    = data.get("user_id")

    if not isinstance(photos_raw, list) or len(photos_raw) < 2:
        return jsonify({"error": "at least 2 directional photos are required"}), 400
    if len(photos_raw) > 6:
        return jsonify({"error": "maximum 6 directional photos supported"}), 400

    # Normalize + validate each photo entry
    photos: list[dict] = []
    total_size = 0
    for i, p in enumerate(photos_raw):
        if not isinstance(p, dict):
            return jsonify({"error": f"photo {i+1} must be an object"}), 400
        img = (p.get("image") or "").strip()
        if not img:
            return jsonify({"error": f"photo {i+1}: image is required"}), 400
        h = p.get("heading_deg")
        if h is None:
            return jsonify({"error": f"photo {i+1}: heading_deg required (real magnetometer reading)"}), 400
        try:
            h = float(h) % 360.0
        except (TypeError, ValueError):
            return jsonify({"error": f"photo {i+1}: heading_deg must be a number"}), 400
        total_size += len(img)
        photos.append({"image_data_url": img, "heading_deg": h, "label": p.get("label") or f"photo_{i+1}"})

    if floor_plan:
        total_size += len(floor_plan)

    # Cap aggregate payload at 30 MB raw — protects backend + OpenAI bill.
    if total_size > 30 * 1024 * 1024:
        return jsonify({"error": "total image payload too large (max 30 MB)"}), 413

    if not openai_available():
        return jsonify({
            "error":   "vastu_deep_scan_unavailable",
            "message": "Deep Scan seva abhi temporarily band hai — kuch der baad try karein.",
        }), 503

    # ── PRO-tier gate (Cosmic Vision multi-photo deep scan; PRO+ only) ───────
    if not user_id:
        return jsonify({
            "error":            "login_required",
            "message":          "Deep Scan ke liye login zaroori hai — yeh AstroVastu PRO ka advanced feature hai.",
            "upgrade_required": True,
        }), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key or user.api_key != api_key:
        return jsonify({"error": "Unauthorized"}), 401

    plan = effective_plan(user)
    if plan not in ("pro", "trial"):
        return jsonify({
            "error":            "upgrade_required",
            "message":          "Deep Scan sirf AstroVastu PRO members ke liye hai. ₹199 ek baar mein unlock karein.",
            "plan":             plan,
            "upgrade_required": True,
        }), 402

    quota = consume_question(user)
    if not quota["allowed"]:
        return jsonify({
            "error":            "daily_limit_reached",
            "message":          f"Aaj ka {quota['limit']} scans ka limit poora ho gaya.",
            "quota":            {"used": quota["used"], "limit": quota["limit"]},
            "plan":             plan,
            "upgrade_required": True,
        }), 402

    try:
        result = vastu_deep_scan(photos, room_type=room, lang=lang, floor_plan_url=floor_plan)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error":   "vastu_deep_scan_failed",
            "message": "Deep scan complete nahi ho payi. Photos ko acchi roshni mein dobara capture karein.",
            "detail":  str(exc),
        }), 500

    result["quota"] = {"used": quota["used"], "limit": quota["limit"]}
    result["plan"]  = effective_plan(user)
    return jsonify(result)


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


# ═══════════════════════════════════════════════════════════════════════════════
# ── Cashfree Payment Gateway ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID", "")
CASHFREE_SECRET = os.environ.get("CASHFREE_SECRET_KEY", "") or os.environ.get("CASHFREE_SECRET", "")
CASHFREE_ENV    = os.environ.get("CASHFREE_ENV", "sandbox")  # "sandbox" or "production"

PLAN_PRICES = {
    "trial_weekly":  1,      # ₹1 → 7-day trial (one-time, Basic-tier access)
    "basic_monthly": 199,
    "basic_yearly":  1799,
    "pro_monthly":   499,
    # Pro yearly removed — Pro is monthly-only.
    # legacy fallback (do not advertise)
    "elite_monthly": 499,
}


def _cf_base():
    if CASHFREE_ENV == "production":
        return "https://api.cashfree.com/pg"
    return "https://sandbox.cashfree.com/pg"


def _cf_payment_url(session_id: str) -> str:
    if CASHFREE_ENV == "production":
        return f"https://payments.cashfree.com/order/#{session_id}"
    return f"https://payments-test.cashfree.com/order/#{session_id}"


def _activate_plan(user_id: int, plan: str, cycle: str, order_id: str):
    """Grant Trial / Basic / Pro / Elite plan to user and set expiry date.

    IDEMPOTENT: if this exact order_id has already been processed for this user,
    no-op. Prevents repeated polling / webhook retries from extending the plan.
    """
    from datetime import timedelta
    user = User.query.get(user_id)
    if not user:
        return False

    # Idempotency guard — same order_id already activated → no-op
    if user.plan_order_id and user.plan_order_id == order_id:
        return True

    now = datetime.utcnow()

    # ── Trial: 7-day Basic-tier access, gated by trial_started_at ─────────
    if plan == "trial":
        if user.trial_used:
            # Already consumed — refund/idempotency case. No-op (still 200).
            return True
        user.trial_started_at = now
        user.trial_used       = True
        user.plan_order_id    = order_id
        db.session.commit()
        return True

    # Treat 'elite' as legacy 'pro' — and force monthly cycle (Pro is monthly-only)
    if plan == "elite":
        plan = "pro"
    if plan == "pro":
        cycle = "monthly"

    days   = 365 if cycle == "yearly" else 31
    # Extend from existing expiry if still active, else from now
    base   = user.plan_expiry if (user.plan_expiry and user.plan_expiry > now) else now
    expiry = base + timedelta(days=days)

    user.plan          = plan
    user.plan_expiry   = expiry
    user.plan_order_id = order_id
    user.is_pro        = (plan == "pro")
    db.session.commit()
    return True


@app.route("/api/payment/create-order", methods=["POST", "OPTIONS"])
def create_payment_order():
    """Create a Cashfree payment order and return a payment link."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    import urllib.request as _req, urllib.error as _err_mod, json as _json

    if not CASHFREE_APP_ID or not CASHFREE_SECRET:
        return jsonify({"error": "Cashfree not configured on server"}), 503

    data    = request.get_json() or {}
    user_id = data.get("user_id")
    plan    = data.get("plan")   # "trial" / "basic" / "pro" / "elite"
    cycle   = data.get("cycle")  # "weekly" / "monthly" / "yearly"

    # Auth: require X-API-Key tied to this user_id
    if user_id:
        try:
            _user, _err = get_authed_user(int(user_id))
            if _err:
                return _err
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid user_id"}), 400

    valid_combos = {
        ("trial", "weekly"),
        ("basic", "monthly"), ("basic", "yearly"),
        ("pro",   "monthly"),
        ("elite", "monthly"),
    }
    if not user_id or (plan, cycle) not in valid_combos:
        return jsonify({"error": "Invalid request: need user_id, plan, cycle"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # One-time trial guard: don't let user pay ₹1 again if already used
    if plan == "trial" and user.trial_used:
        return jsonify({"error": "Trial already used. Please choose Basic or Pro."}), 400

    plan_key = f"{plan}_{cycle}"
    amount   = PLAN_PRICES.get(plan_key, 0)

    # Unique order ID — encodes user/plan/cycle for webhook parsing
    # plan codes: B=basic, P=pro, E=elite (legacy)
    ts       = int(datetime.utcnow().timestamp())
    order_id = f"CL{user_id}_{plan[0].upper()}{cycle[0].upper()}_{ts}"

    # Return URL shown in browser after payment completes (no deep link needed)
    return_url = f"{os.environ.get('API_BASE', 'http://localhost:8080')}/api/payment/return?order_id={order_id}&plan={plan}&cycle={cycle}"

    # Cashfree's hosted checkout requires a non-empty email + valid phone (10 digits, no +91).
    # Fall back to safe defaults for demo / phone-only signups.
    cust_email = (user.email or "").strip() or f"user{user.id}@cosmiclens.app"
    raw_phone  = (user.phone or "").strip()
    digits     = "".join(c for c in raw_phone if c.isdigit())
    if len(digits) >= 10:
        cust_phone = digits[-10:]   # Cashfree wants 10-digit Indian number
    else:
        cust_phone = "9999999999"

    payload = {
        "order_id":       order_id,
        "order_amount":   amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id":    str(user.id),
            "customer_name":  user.name or "User",
            "customer_email": cust_email,
            "customer_phone": cust_phone,
        },
        "order_meta": {
            "return_url": return_url,
        },
        "order_tags": {
            "plan":    plan,
            "cycle":   cycle,
            "user_id": str(user_id),
        },
    }

    body   = _json.dumps(payload).encode()
    cf_req = _req.Request(
        f"{_cf_base()}/orders",
        data=body,
        headers={
            "Content-Type":    "application/json",
            "x-client-id":     CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET,
            "x-api-version":   "2023-08-01",
        },
        method="POST",
    )
    app.logger.info(f"[CF] POST {_cf_base()}/orders  env={CASHFREE_ENV}  order={order_id}  amt=₹{amount}  user={user_id}")
    try:
        with _req.urlopen(cf_req, timeout=15) as resp:
            result = _json.loads(resp.read())
    except _err_mod.HTTPError as e:
        try:
            detail = e.read().decode()
        except Exception:
            detail = ""
        app.logger.error(f"[CF] ❌ HTTP {e.code} on /orders: {detail}")
        return jsonify({
            "error":  "Cashfree order creation failed",
            "code":   e.code,
            "detail": detail,
        }), 502
    except Exception as e:
        app.logger.error(f"[CF] ❌ network error: {e}")
        return jsonify({"error": str(e)}), 502

    session_id   = result.get("payment_session_id", "")
    cf_order_id  = result.get("cf_order_id", "")
    if not session_id:
        app.logger.error(f"[CF] ❌ no payment_session_id in response: {result}")
        return jsonify({"error": "Cashfree returned no session_id", "raw": result}), 502
    payment_link = _cf_payment_url(session_id)
    app.logger.info(f"[CF] ✅ order created  cf_order_id={cf_order_id}  session=...{session_id[-20:]}  link_len={len(payment_link)}")

    return jsonify({
        "order_id":           order_id,
        "payment_session_id": session_id,
        "payment_link":       payment_link,
        "amount":             amount,
        "plan":               plan,
        "cycle":              cycle,
    })


@app.route("/api/payment/status/<order_id>", methods=["GET", "OPTIONS"])
def payment_status(order_id):
    """Poll Cashfree for payment status — called by frontend after browser returns."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    import urllib.request as _req, json as _json

    if not CASHFREE_APP_ID or not CASHFREE_SECRET:
        return jsonify({"error": "Cashfree not configured"}), 503

    # Auth: order_id encodes user_id ("CL{uid}_..."). Verify caller owns this user.
    try:
        _uid = int(order_id.split("_")[0][2:])
        _user, _err = get_authed_user(_uid)
        if _err:
            return _err
    except (IndexError, ValueError):
        return jsonify({"error": "Invalid order_id"}), 400

    cf_req = _req.Request(
        f"{_cf_base()}/orders/{order_id}/payments",
        headers={
            "x-client-id":     CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET,
            "x-api-version":   "2023-08-01",
        },
    )
    try:
        with _req.urlopen(cf_req, timeout=15) as resp:
            payments = _json.loads(resp.read())
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    if not isinstance(payments, list):
        payments = []

    paid = any(p.get("payment_status") == "SUCCESS" for p in payments)

    if paid:
        # Parse order_id: CL{user_id}_{T/B/P/E}{W/M/Y}_{ts}
        # T=trial, B=basic, P=pro, E=elite (legacy)
        # W=weekly (trial only), M=monthly, Y=yearly
        try:
            parts   = order_id.split("_")
            uid_str = parts[0][2:]          # strip "CL"
            code    = parts[1]              # e.g. "TW", "BM", "PY"
            plan_map  = {"T": "trial", "B": "basic", "P": "pro", "E": "elite"}
            cycle_map = {"W": "weekly",  "M": "monthly", "Y": "yearly"}
            plan  = plan_map.get(code[0])
            cycle = cycle_map.get(code[1])
            if not plan or not cycle:
                # Unknown order shape — refuse rather than activating wrong plan
                return jsonify({"status": "SUCCESS", "warning": "unknown_order_shape"})
            _activate_plan(int(uid_str), plan, cycle, order_id)
            # Return fresh user data
            user = User.query.get(int(uid_str))
            return jsonify({
                "status":  "SUCCESS",
                "plan":    plan,
                "cycle":   cycle,
                "user":    user.to_dict() if user else None,
            })
        except Exception:
            return jsonify({"status": "SUCCESS"})

    statuses = list({p.get("payment_status", "PENDING") for p in payments})
    return jsonify({"status": statuses[0] if statuses else "PENDING"})


@app.route("/api/payment/webhook", methods=["POST"])
def payment_webhook():
    """Cashfree webhook — verifies signature and activates subscription."""
    import hmac as _hmac, hashlib, base64, json as _json

    raw_body     = request.get_data()
    received_sig = request.headers.get("x-webhook-signature", "")
    timestamp    = request.headers.get("x-webhook-timestamp", "")

    # Mandatory signature verification when CASHFREE_SECRET is configured.
    # This prevents spoofed webhook calls from activating subscriptions.
    if CASHFREE_SECRET:
        if not received_sig or not timestamp:
            return jsonify({"error": "Signature required"}), 401
        message  = (timestamp + raw_body.decode()).encode()
        expected = base64.b64encode(
            _hmac.new(CASHFREE_SECRET.encode(), message, hashlib.sha256).digest()
        ).decode()
        if not _hmac.compare_digest(received_sig, expected):
            return jsonify({"error": "Invalid signature"}), 401

    try:
        payload = _json.loads(raw_body)
    except Exception:
        return jsonify({"error": "Bad JSON"}), 400

    event = payload.get("type", "")

    if event in ("PAYMENT_SUCCESS_WEBHOOK", "PAYMENT_SUCCESS"):
        order    = payload.get("data", {}).get("order", {})
        order_id = order.get("order_id", "")
        tags     = order.get("order_tags", {}) or {}
        uid      = tags.get("user_id", "")

        # ── AstroVastu one-time purchases (Phase 3) ────────────────────────
        if tags.get("kind") == "astrovastu" or (order_id and order_id.startswith("AV")):
            from subscription_helper import grant_purchase_idempotent
            from models import AstroVastuPurchase
            pid = tags.get("purchase_id") or ""
            purchase = None
            if pid:
                try:
                    purchase = AstroVastuPurchase.query.get(int(pid))
                except (TypeError, ValueError):
                    purchase = None
            if not purchase and order_id:
                purchase = AstroVastuPurchase.query.filter_by(order_id=order_id).first()
            # Fallback parse from order_id format AV{user}_{purchase}_{ts}
            if not purchase and order_id and order_id.startswith("AV"):
                try:
                    parsed_pid = int(order_id.split("_")[1])
                    purchase = AstroVastuPurchase.query.get(parsed_pid)
                except (IndexError, ValueError):
                    pass
            if purchase:
                if purchase.status != "paid":
                    purchase.status  = "paid"
                    purchase.paid_at = datetime.utcnow()
                    db.session.commit()
                grant_purchase_idempotent(purchase)
                app.logger.info(f"[CF-AV] webhook granted purchase id={purchase.id} sku={purchase.sku}")
            else:
                app.logger.warning(f"[CF-AV] webhook: no AstroVastuPurchase for order={order_id} pid={pid}")
            return jsonify({"status": "ok"}), 200

        # ── Subscription plans (existing flow) ─────────────────────────────
        plan  = tags.get("plan", "")
        cycle = tags.get("cycle", "monthly")
        if uid and plan and order_id:
            _activate_plan(int(uid), plan, cycle, order_id)

    return jsonify({"status": "ok"}), 200


@app.route("/api/payment/return", methods=["GET"])
def payment_return():
    """Browser return page shown to user after Cashfree payment."""
    order_id = request.args.get("order_id", "")
    plan     = request.args.get("plan", "")
    cycle    = request.args.get("cycle", "")
    status   = request.args.get("status", "")

    plan_label = f"{plan.title()} ({cycle})" if plan else "plan"

    if status and status.upper() != "CANCELLED":
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Payment Complete — Cosmic Lens</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
          background:#0c0818;color:#fff;min-height:100vh;
          display:flex;align-items:center;justify-content:center;padding:24px}}
    .card{{background:rgba(255,255,255,0.06);border:1px solid rgba(245,158,11,0.3);
           border-radius:20px;padding:32px 24px;max-width:400px;width:100%;text-align:center}}
    .emoji{{font-size:52px;margin-bottom:16px}}
    h1{{font-size:22px;font-weight:700;color:#f59e0b;margin-bottom:8px}}
    p{{color:rgba(255,255,255,0.6);font-size:14px;line-height:1.6;margin-bottom:20px}}
    .badge{{display:inline-block;background:rgba(245,158,11,0.15);
            border:1px solid rgba(245,158,11,0.4);border-radius:20px;
            padding:6px 16px;font-size:12px;color:#f59e0b;font-weight:600;margin-bottom:20px}}
    .note{{font-size:12px;color:rgba(255,255,255,0.35)}}
  </style>
</head>
<body>
  <div class="card">
    <div class="emoji">⭐</div>
    <h1>Payment Successful!</h1>
    <div class="badge">{plan_label.upper()} ACTIVATED</div>
    <p>Aapka {plan_label} plan activate ho gaya hai.<br/>
       Cosmic Lens app mein wapas jao aur features enjoy karo!</p>
    <p class="note">Order: {order_id}</p>
  </div>
</body>
</html>"""
    else:
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Payment Cancelled — Cosmic Lens</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
          background:#0c0818;color:#fff;min-height:100vh;
          display:flex;align-items:center;justify-content:center;padding:24px}}
    .card{{background:rgba(255,255,255,0.06);border:1px solid rgba(100,116,139,0.3);
           border-radius:20px;padding:32px 24px;max-width:400px;width:100%;text-align:center}}
    .emoji{{font-size:52px;margin-bottom:16px}}
    h1{{font-size:22px;font-weight:700;color:#94a3b8;margin-bottom:8px}}
    p{{color:rgba(255,255,255,0.6);font-size:14px;line-height:1.6}}
  </style>
</head>
<body>
  <div class="card">
    <div class="emoji">🌙</div>
    <h1>Payment Cancelled</h1>
    <p>Koi baat nahi — jab chahein try karein.<br/>App mein wapas jakar phir se upgrade karein.</p>
  </div>
</body>
</html>"""

    from flask import make_response
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html"
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# LOVE COMPATIBILITY ENGINE — D1 + D9 + Dasha + Transit, zero templates
# All reasons derived from actual kundli data: positions, dignities, houses,
# aspects, dashas, real-time transits. Output AI-consumable strict JSON.
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/love-compatibility", methods=["POST"])
def love_compatibility():
    """
    Strict structure:
      {
        "score": 0-100,
        "factors": {emotional, attraction, communication, karmic, stability},
        "reasons": [raw astrology phrases]
      }
    Input body: { "p1": <birth_data>, "p2": <birth_data> }
    """
    import swisseph as swe
    from datetime import datetime as _dt

    data = request.get_json(force=True, silent=True) or {}
    if "p1" not in data or "p2" not in data:
        return jsonify({"error": "Missing p1 or p2"}), 400

    try:
        k1 = calculate_kundli(data["p1"])
        k2 = calculate_kundli(data["p2"])
    except Exception as exc:
        return jsonify({"error": f"Kundli calculation failed: {exc}"}), 500

    SIGNS_LC = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    SIGN_LORDS_LC = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
                     "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]

    # classical 7-planet friendship — values: 2 friend, 1 neutral, 0 enemy
    # order: Sun Moon Mars Mercury Jupiter Venus Saturn
    PLN_IDX = {"Sun":0,"Moon":1,"Mars":2,"Mercury":3,"Jupiter":4,"Venus":5,"Saturn":6}
    PLN_FRIEND_LC = [
        [1,2,2,1,2,0,0],  # Sun
        [2,1,0,1,2,2,0],  # Moon
        [2,0,1,1,2,0,2],  # Mars  (Merc neutral kept 1)
        [2,0,2,1,0,2,0],  # Mercury
        [2,1,2,1,1,0,0],  # Jupiter
        [2,2,0,2,1,1,0],  # Venus  (Sat own)
        [0,0,2,2,2,0,1],  # Saturn
    ]
    EXALT_LC = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
    DEBIL_LC = {"Sun":6,"Moon":7,"Mars":3,"Mercury":11,"Jupiter":9,"Venus":5,"Saturn":0}
    OWN_LC   = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
                "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
    BENEFIC  = {"Jupiter","Venus","Mercury","Moon"}
    MALEFIC  = {"Saturn","Mars","Rahu","Ketu"}
    MANGLIK_HOUSES = {1,4,7,8,12}

    def sidx(sign_name):
        try:    return SIGNS_LC.index(sign_name)
        except: return 0

    def getp(k, name):
        for p in k.get("planets", []):
            if p["name"] == name: return p
        return None

    def vargap(k, chart, name):
        v = (k.get("divisionalCharts") or {}).get(chart) or {}
        for p in v.get("planets", []):
            if p["name"] == name: return p
        return None

    def dignity_score(planet_name, sign_index):
        if EXALT_LC.get(planet_name) == sign_index: return 2
        if DEBIL_LC.get(planet_name) == sign_index: return -2
        if sign_index in OWN_LC.get(planet_name, []): return 1
        lord = SIGN_LORDS_LC[sign_index]
        if planet_name in PLN_IDX and lord in PLN_IDX:
            f = PLN_FRIEND_LC[PLN_IDX[planet_name]][PLN_IDX[lord]]
            return 1 if f == 2 else -1 if f == 0 else 0
        return 0

    def dignity_word(d):
        return {2:"exalted",1:"own-sign",0:"neutral",-1:"enemy-sign",-2:"debilitated"}.get(d,"neutral")

    def aspects_planet(k, target_planet):
        """Return list of planet-names that aspect `target_planet` in D1 (Vedic aspects)."""
        tgt = getp(k, target_planet)
        if not tgt: return []
        ts  = sidx(tgt["sign"])
        hits = []
        for p in k.get("planets", []):
            if p["name"] == target_planet: continue
            ps = sidx(p["sign"])
            d  = (ts - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":    ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn":  ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    def aspects_house(k, house_num):
        """Return list of planet names aspecting the given house (1-12) of kundli k."""
        asc = sidx(k.get("ascendant", "Aries"))
        tgt_sign = (asc + house_num - 1) % 12
        hits = []
        for p in k.get("planets", []):
            ps = sidx(p["sign"])
            d  = (tgt_sign - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":    ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn":  ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    def occupants(k, house_num):
        return [p["name"] for p in k.get("planets", []) if p["house"] == house_num]

    def name_of(k):  return k.get("name") or "partner"

    reasons = []

    # ── 1. EMOTIONAL (Moon) ────────────────────────────────────────────────────
    def score_emotional():
        m1, m2 = getp(k1,"Moon"), getp(k2,"Moon")
        if not m1 or not m2: return 50
        s1, s2 = sidx(m1["sign"]), sidx(m2["sign"])
        l1, l2 = SIGN_LORDS_LC[s1], SIGN_LORDS_LC[s2]
        f = PLN_FRIEND_LC[PLN_IDX[l1]][PLN_IDX[l2]] + PLN_FRIEND_LC[PLN_IDX[l2]][PLN_IDX[l1]]
        base = {4:85, 3:72, 2:58, 1:45, 0:30}.get(f, 50)
        if f >= 3: reasons.append(f"Moon signs {m1['sign']} & {m2['sign']} — lords {l1}/{l2} friendly, emotional harmony")
        elif f <= 1: reasons.append(f"Moon signs {m1['sign']} & {m2['sign']} — lords {l1}/{l2} hostile, emotional mismatch")

        # D1 house placement
        for label, m, k in [(name_of(k1), m1, k1), (name_of(k2), m2, k2)]:
            if m["house"] in (6,8,12):
                base -= 8
                reasons.append(f"{label}'s Moon in dusthana house {m['house']} — inner insecurity / mood swings")
            elif m["house"] in (1,4,7,10):
                base += 4
                reasons.append(f"{label}'s Moon in kendra house {m['house']} — emotionally grounded")
            # D9 moon
            m9 = vargap(k, "D9", "Moon")
            if m9:
                d9_dig = dignity_score("Moon", m9["signIndex"])
                if d9_dig >= 1:
                    base += 5
                    reasons.append(f"{label}'s Moon {dignity_word(d9_dig)} in D9 Navamsa — deep emotional stability")
                elif d9_dig <= -1:
                    base -= 6
                    reasons.append(f"{label}'s Moon {dignity_word(d9_dig)} in D9 Navamsa — vulnerable emotional core")
            # Affliction check
            afflictors = [a for a in aspects_planet(k, "Moon") if a in ("Saturn","Rahu","Ketu","Mars")]
            same_house = [p["name"] for p in k["planets"] if p["name"] in ("Saturn","Rahu","Ketu","Mars") and p["house"] == m["house"]]
            all_af = set(afflictors) | set(same_house)
            if all_af:
                base -= 4 * len(all_af)
                reasons.append(f"{label}'s Moon afflicted by {', '.join(sorted(all_af))} — emotional friction")

        return max(0, min(100, base))

    # ── 2. ATTRACTION (Venus × Mars) ───────────────────────────────────────────
    def score_attraction():
        v1, m1 = getp(k1,"Venus"), getp(k1,"Mars")
        v2, m2 = getp(k2,"Venus"), getp(k2,"Mars")
        if not all([v1,m1,v2,m2]): return 50
        base = 55

        # Cross Venus-Mars: p1 Venus × p2 Mars and vice versa
        for a_label, a, b_label, b in [
            (name_of(k1)+"'s Venus", v1, name_of(k2)+"'s Mars", m2),
            (name_of(k2)+"'s Venus", v2, name_of(k1)+"'s Mars", m1),
        ]:
            d = (sidx(a["sign"]) - sidx(b["sign"]) + 12) % 12
            if d == 0:
                base += 12; reasons.append(f"{a_label} conjunct {b_label} in {a['sign']} — magnetic attraction")
            elif d == 6:
                base += 8;  reasons.append(f"{a_label} opposite {b_label} (7th axis) — polarity chemistry")
            elif d in (4,8):
                base += 4;  reasons.append(f"{a_label} in trine with {b_label} — graceful romantic flow")

        # Venus dignity
        for lbl, v, kref in [(name_of(k1), v1, k1), (name_of(k2), v2, k2)]:
            vd = dignity_score("Venus", sidx(v["sign"]))
            if vd >= 1:
                base += 6; reasons.append(f"{lbl}'s Venus {dignity_word(vd)} in {v['sign']} — strong romantic nature")
            elif vd <= -1:
                base -= 6; reasons.append(f"{lbl}'s Venus {dignity_word(vd)} in {v['sign']} — love style struggles")
            # Venus in D9
            v9 = vargap(kref, "D9", "Venus")
            if v9:
                d9d = dignity_score("Venus", v9["signIndex"])
                if d9d >= 1:
                    base += 4; reasons.append(f"{lbl}'s Venus {dignity_word(d9d)} in D9 — lasting romantic fulfilment")
                elif d9d <= -1:
                    base -= 4; reasons.append(f"{lbl}'s Venus {dignity_word(d9d)} in D9 — romantic disappointments")

        # Mars dignity (passion / aggression balance)
        for lbl, m in [(name_of(k1), m1), (name_of(k2), m2)]:
            md = dignity_score("Mars", sidx(m["sign"]))
            if md <= -1:
                base -= 5; reasons.append(f"{lbl}'s Mars {dignity_word(md)} in {m['sign']} — aggression / temper friction")
            elif md >= 1:
                base += 3; reasons.append(f"{lbl}'s Mars {dignity_word(md)} in {m['sign']} — healthy passion drive")
            if m["house"] in MANGLIK_HOUSES:
                base -= 3; reasons.append(f"{lbl}'s Mars in house {m['house']} — manglik placement, intense energy")

        return max(0, min(100, base))

    # ── 3. COMMUNICATION (Mercury + 3rd house) ─────────────────────────────────
    def score_communication():
        me1, me2 = getp(k1,"Mercury"), getp(k2,"Mercury")
        if not me1 or not me2: return 50
        base = 55

        for lbl, me, k in [(name_of(k1), me1, k1), (name_of(k2), me2, k2)]:
            md = dignity_score("Mercury", sidx(me["sign"]))
            if md >= 1:
                base += 6; reasons.append(f"{lbl}'s Mercury {dignity_word(md)} in {me['sign']} — clear articulate expression")
            elif md <= -1:
                base -= 6; reasons.append(f"{lbl}'s Mercury {dignity_word(md)} in {me['sign']} — communication distortions")
            # affliction
            af = [a for a in aspects_planet(k, "Mercury") if a in ("Saturn","Rahu","Ketu","Mars")]
            same = [p["name"] for p in k["planets"] if p["name"] in ("Saturn","Rahu","Ketu") and p["house"] == me["house"]]
            all_af = set(af) | set(same)
            if all_af:
                base -= 3 * len(all_af)
                reasons.append(f"{lbl}'s Mercury afflicted by {', '.join(sorted(all_af))} — speech misunderstandings")
            # 3rd house condition
            h3 = occupants(k, 3)
            mal3 = [p for p in h3 if p in MALEFIC]
            ben3 = [p for p in h3 if p in BENEFIC]
            if ben3:
                base += 3; reasons.append(f"{lbl}'s 3rd house has {', '.join(ben3)} — warmth in daily conversation")
            if mal3:
                base -= 3; reasons.append(f"{lbl}'s 3rd house has {', '.join(mal3)} — blunt or harsh speech style")

        # Gana koot from nakshatra
        GANA = [0,1,2, 1,0,1, 0,0,2, 2,1,1, 0,2,0, 2,0,2, 2,1,1, 0,1,2, 1,1,0]
        GANA_N = ["Deva","Manushya","Rakshasa"]
        NAK = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
               "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
               "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
               "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
        try:
            n1, n2 = NAK.index(k1["nakshatra"]), NAK.index(k2["nakshatra"])
            g1, g2 = GANA[n1], GANA[n2]
            if g1 == g2:
                base += 5; reasons.append(f"Same gana ({GANA_N[g1]}) — matched mental temperament")
            elif {g1, g2} == {0, 2}:
                base -= 8; reasons.append(f"Gana clash ({GANA_N[g1]}/{GANA_N[g2]}) — opposing thought styles")
        except ValueError:
            pass

        return max(0, min(100, base))

    # ── 4. KARMIC (Rahu/Ketu on 1-7 axis, Venus, Moon) ─────────────────────────
    def score_karmic():
        base = 50
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            r, ke = getp(k,"Rahu"), getp(k,"Ketu")
            if ke and ke["house"] == 7:
                base += 10; reasons.append(f"{lbl}'s Ketu in 7th — strong karmic partnership, past-life detachment to resolve")
            if r and r["house"] == 7:
                base += 6; reasons.append(f"{lbl}'s Rahu in 7th — unusual attractions, karmic magnetism in partner")
            if ke and ke["house"] == 1:
                base += 4; reasons.append(f"{lbl}'s Ketu in 1st — inward soul lesson around self vs partner")
            if r and r["house"] == 1:
                base += 3; reasons.append(f"{lbl}'s Rahu in 1st — identity amplified by partner dynamics")
            # Rahu influencing Venus or Moon
            for tgt in ("Venus","Moon"):
                tp = getp(k, tgt)
                if not tp: continue
                if r and (r["house"] == tp["house"] or r["sign"] == tp["sign"]):
                    base += 5; reasons.append(f"{lbl}'s Rahu with {tgt} in {tp['sign']} — karmic intensity around love/emotion")
                elif "Rahu" in aspects_planet(k, tgt):
                    base += 3; reasons.append(f"{lbl}'s Rahu aspects {tgt} — obsessive/addictive relational pull")
            # D9 1-7 axis
            for n in ("Rahu","Ketu"):
                pd9 = vargap(k, "D9", n)
                if pd9 and pd9["house"] in (1,7):
                    base += 4; reasons.append(f"{lbl}'s {n} on D9 1-7 axis (house {pd9['house']}) — destined marriage karma")
        return max(0, min(100, base))

    # ── 5. STABILITY (7th house + D9 + doshas) ─────────────────────────────────
    def score_stability():
        base = 60
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            asc = sidx(k.get("ascendant", "Aries"))
            seventh_sign = (asc + 6) % 12
            seventh_lord = SIGN_LORDS_LC[seventh_sign]
            seventh_lord_p = getp(k, seventh_lord)
            occ7 = occupants(k, 7)

            ben7 = [p for p in occ7 if p in BENEFIC]
            mal7 = [p for p in occ7 if p in MALEFIC]
            if ben7:
                base += 6; reasons.append(f"{lbl}'s 7th house holds {', '.join(ben7)} — benefics supporting marriage")
            if mal7:
                base -= 6; reasons.append(f"{lbl}'s 7th house holds {', '.join(mal7)} — friction in partnership area")

            # Saturn influence on 7th
            asp7 = aspects_house(k, 7)
            if "Saturn" in asp7 and "Saturn" not in occ7:
                base -= 5; reasons.append(f"{lbl}'s Saturn aspects 7th house — delay or duty in marriage")

            # 7th lord placement
            if seventh_lord_p:
                if seventh_lord_p["house"] in (1,4,5,7,9,10,11):
                    base += 5; reasons.append(f"{lbl}'s 7th lord {seventh_lord} in house {seventh_lord_p['house']} — well-placed for marriage")
                elif seventh_lord_p["house"] in (6,8,12):
                    base -= 7; reasons.append(f"{lbl}'s 7th lord {seventh_lord} in dusthana house {seventh_lord_p['house']} — marital instability risk")
                lord_dig = dignity_score(seventh_lord, sidx(seventh_lord_p["sign"]))
                if lord_dig >= 1:
                    base += 4; reasons.append(f"{lbl}'s 7th lord {seventh_lord} {dignity_word(lord_dig)} — strong marriage karma")
                elif lord_dig <= -1:
                    base -= 4; reasons.append(f"{lbl}'s 7th lord {seventh_lord} {dignity_word(lord_dig)} — weak marriage foundation")

            # D9 7th lord
            d9l_sign = vargap(k, "D9", seventh_lord)
            if d9l_sign:
                d9d = dignity_score(seventh_lord, d9l_sign["signIndex"])
                if d9d >= 1:
                    base += 4; reasons.append(f"{lbl}'s 7th lord {seventh_lord} {dignity_word(d9d)} in D9 — durable bond in marriage")
                elif d9d <= -1:
                    base -= 4; reasons.append(f"{lbl}'s 7th lord {seventh_lord} {dignity_word(d9d)} in D9 — D9 weakness in marriage area")

        # Bhakoot dosha
        mo1, mo2 = getp(k1,"Moon"), getp(k2,"Moon")
        if mo1 and mo2:
            s1, s2 = sidx(mo1["sign"]), sidx(mo2["sign"])
            diff = min((s1-s2)%12, (s2-s1)%12)
            pair = tuple(sorted([(s1-s2)%12+1, (s2-s1)%12+1]))
            # bad pairs: 6-8, 2-12, 5-9
            if pair in [(6,8),(2,12),(5,9)]:
                base -= 10; reasons.append(f"Bhakoot dosha — Moon signs form {pair[0]}-{pair[1]} axis, prosperity strain")

        # Nadi dosha
        NADI = [0,1,2, 2,1,0, 0,1,2, 2,1,0, 0,1,2, 2,1,0, 0,1,2, 2,1,0, 0,1,2]
        NAK = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
               "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
               "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
               "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
        try:
            n1, n2 = NAK.index(k1["nakshatra"]), NAK.index(k2["nakshatra"])
            if NADI[n1] == NADI[n2]:
                base -= 8; reasons.append(f"Nadi dosha — same nadi nakshatra, genetic/health compatibility concern")
        except ValueError:
            pass

        return max(0, min(100, base))

    # ── 6. DOSHA CHECK (severity) ──────────────────────────────────────────────
    def score_dosha():
        """Returns (severity_0_10, individual dosha reasons)."""
        severity = 0
        m1, m2 = getp(k1,"Mars"), getp(k2,"Mars")
        mang1 = m1 and m1["house"] in MANGLIK_HOUSES
        mang2 = m2 and m2["house"] in MANGLIK_HOUSES
        if mang1 and mang2:
            reasons.append(f"Both partners manglik (Mars in house {m1['house']}/{m2['house']}) — dosha self-cancels")
        elif mang1 or mang2:
            severity += 4
            who = name_of(k1) if mang1 else name_of(k2)
            mref = m1 if mang1 else m2
            reasons.append(f"Manglik dosha on {who} side — Mars in house {mref['house']}, possible friction / remedies advised")

        # Bhakoot & Nadi already reasoned in stability — just add severity weight
        mo1, mo2 = getp(k1,"Moon"), getp(k2,"Moon")
        if mo1 and mo2:
            s1,s2 = sidx(mo1["sign"]), sidx(mo2["sign"])
            pair = tuple(sorted([(s1-s2)%12+1, (s2-s1)%12+1]))
            if pair in [(6,8),(2,12),(5,9)]: severity += 3
        NADI = [0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2]
        NAK = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
               "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
               "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
               "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
        try:
            n1,n2 = NAK.index(k1["nakshatra"]), NAK.index(k2["nakshatra"])
            if NADI[n1] == NADI[n2]: severity += 3
        except ValueError:
            pass
        return min(10, severity)

    # ── 7. DASHA SUPPORT ───────────────────────────────────────────────────────
    def score_dasha():
        base = 55
        RELATIONSHIP_PLANETS = {"Venus", "Moon"}
        STRESS_PLANETS = {"Saturn", "Rahu", "Ketu"}

        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            cd = k.get("currentDasha") or {}
            md, ad = cd.get("maha"), cd.get("antar")
            if not md: continue
            asc = sidx(k.get("ascendant","Aries"))
            seventh_lord = SIGN_LORDS_LC[(asc + 6) % 12]

            for role, planet in [("MD", md), ("AD", ad)]:
                if not planet: continue
                if planet in RELATIONSHIP_PLANETS or planet == seventh_lord:
                    base += 7 if role == "MD" else 4
                    reasons.append(f"{lbl} running {planet} {role} — relationship karma active now")
                elif planet in STRESS_PLANETS:
                    base -= 6 if role == "MD" else 3
                    reasons.append(f"{lbl} running {planet} {role} — strain on partnership timing")
        return max(0, min(100, base))

    # ── 8. TRANSIT IMPACT (real-time) ──────────────────────────────────────────
    def score_transit():
        base = 55
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        now = _dt.utcnow()
        jd  = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        transits = {}
        for pname, pid in [("Jupiter",swe.JUPITER),("Saturn",swe.SATURN),
                           ("Mars",swe.MARS),("Sun",swe.SUN),("Venus",swe.VENUS),
                           ("Mercury",swe.MERCURY),("Rahu",swe.MEAN_NODE)]:
            try:
                r = swe.calc_ut(jd, pid, flags)
                transits[pname] = int((r[0][0] % 360) // 30)
            except Exception: pass
        if "Rahu" in transits:
            transits["Ketu"] = (transits["Rahu"] + 6) % 12

        def vedic_aspect_signs(planet, t_sign):
            out = [(t_sign + 6) % 12]
            if planet == "Jupiter": out += [(t_sign+4)%12, (t_sign+8)%12]
            if planet == "Saturn":  out += [(t_sign+2)%12, (t_sign+9)%12]
            if planet == "Mars":    out += [(t_sign+3)%12, (t_sign+7)%12]
            if planet in ("Rahu","Ketu"): out += [(t_sign+4)%12, (t_sign+8)%12]
            return out

        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            asc = sidx(k.get("ascendant","Aries"))
            seventh_sign = (asc + 6) % 12
            venus = getp(k,"Venus");  moon = getp(k,"Moon")
            venus_sign = sidx(venus["sign"]) if venus else None
            moon_sign  = sidx(moon["sign"]) if moon else None

            for tp, tsign in transits.items():
                aspects = vedic_aspect_signs(tp, tsign)
                for target_name, tgt in [("7th house", seventh_sign),
                                         ("Venus", venus_sign),
                                         ("Moon", moon_sign)]:
                    if tgt is None: continue
                    if tgt in aspects:
                        if tp == "Jupiter":
                            base += 4; reasons.append(f"{lbl}: Jupiter transiting {SIGNS_LC[tsign]} aspects {target_name} — blessings on love")
                        elif tp == "Saturn":
                            base -= 4; reasons.append(f"{lbl}: Saturn transiting {SIGNS_LC[tsign]} aspects {target_name} — test / delay")
                        elif tp == "Rahu":
                            base -= 2; reasons.append(f"{lbl}: Rahu transit aspects {target_name} — confusion / obsession risk")
                        elif tp == "Ketu":
                            base -= 2; reasons.append(f"{lbl}: Ketu transit aspects {target_name} — detachment / karmic release")
                        elif tp == "Venus" and target_name in ("7th house","Moon"):
                            base += 2; reasons.append(f"{lbl}: Venus transit aspects {target_name} — romantic window opening")
        return max(0, min(100, base))

    # ── 9. D9 DEEP CHECK ───────────────────────────────────────────────────────
    def score_d9():
        base = 55
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            asc = sidx(k.get("ascendant","Aries"))
            seventh_lord = SIGN_LORDS_LC[(asc + 6) % 12]

            # spouse nature from D9 7th lord placement
            d9 = (k.get("divisionalCharts") or {}).get("D9") or {}
            d9_asc = d9.get("ascendantSignIndex", 0)
            d9_7th = (d9_asc + 6) % 12
            # who is in D9 7th
            d9_7th_occ = [p["name"] for p in d9.get("planets", []) if p.get("signIndex") == d9_7th]
            if d9_7th_occ:
                ben = [p for p in d9_7th_occ if p in BENEFIC]
                mal = [p for p in d9_7th_occ if p in MALEFIC]
                if ben:
                    base += 5; reasons.append(f"{lbl}'s D9 7th house has {', '.join(ben)} — nurturing spouse quality")
                if mal:
                    base -= 5; reasons.append(f"{lbl}'s D9 7th house has {', '.join(mal)} — challenging spouse dynamic")

            # 7th lord in D9
            d9_7L = vargap(k, "D9", seventh_lord)
            if d9_7L:
                dg = dignity_score(seventh_lord, d9_7L["signIndex"])
                if dg >= 1:
                    base += 5; reasons.append(f"{lbl}'s 7th lord {seventh_lord} {dignity_word(dg)} in D9 — marriage dharma secured")
                elif dg <= -1:
                    base -= 5; reasons.append(f"{lbl}'s 7th lord {seventh_lord} {dignity_word(dg)} in D9 — spouse-related karma strained")
        return max(0, min(100, base))

    # ── 10. FINAL SCORE ────────────────────────────────────────────────────────
    emo = score_emotional()
    att = score_attraction()
    com = score_communication()
    kar = score_karmic()
    sta = score_stability()
    dashaS = score_dasha()
    tran   = score_transit()
    d9s    = score_d9()
    dosha_severity = score_dosha()

    # merge stability with D9 (D9 deepens stability) → weighted mix
    stability_final = round(sta * 0.55 + d9s * 0.45)
    dasha_transit   = round(dashaS * 0.55 + tran * 0.45)

    weighted = (
        emo * 0.20 +
        att * 0.15 +
        com * 0.15 +
        kar * 0.10 +
        stability_final * 0.25 +
        dasha_transit   * 0.25
    )
    # normalize sum of weights (1.10) back to 100 scale, then apply dosha
    weighted = weighted / 1.10
    final_score = max(0, min(100, round(weighted - dosha_severity)))

    def bucket(v): return "strong" if v >= 67 else "medium" if v >= 45 else "weak"

    # Dedupe reasons preserving order
    seen = set(); unique_reasons = []
    for r in reasons:
        if r not in seen:
            seen.add(r); unique_reasons.append(r)

    return jsonify({
        "score": final_score,
        "factors": {
            "emotional":     bucket(emo),
            "attraction":    bucket(att),
            "communication": bucket(com),
            "karmic":        bucket(kar),
            "stability":     bucket(stability_final),
        },
        "reasons": unique_reasons,
        "breakdown": {
            "emotional":     emo,
            "attraction":    att,
            "communication": com,
            "karmic":        kar,
            "stability":     stability_final,
            "dasha_transit": dasha_transit,
            "dosha_severity": dosha_severity,
        },
    })


@app.route("/api/breakup-chances", methods=["POST"])
def breakup_chances():
    """
    Vedic + KP breakup-probability engine.
    Body: { "p1": <birth_data>, "p2": <birth_data> }
    Returns:
      {
        "breakup_score": 0-100,
        "risk_level": "low|medium|high|very high",
        "factors": { dasha, houses, venus_moon, kp },
        "reasons": [ ... raw astrology reasons ... ],
        "breakdown": { dasha, houses, venus_moon, kp, transit }
      }
    Weighting:
      Dasha 60 • Houses/Affliction 25 • Venus-Moon 10 • KP 5 • Transit ±10 adjustment
    """
    import swisseph as swe
    from datetime import datetime as _dt

    data = request.get_json(force=True, silent=True) or {}
    if "p1" not in data or "p2" not in data:
        return jsonify({"error": "Missing p1 or p2"}), 400

    try:
        k1 = calculate_kundli(data["p1"])
        k2 = calculate_kundli(data["p2"])
    except Exception as exc:
        return jsonify({"error": f"Kundli calculation failed: {exc}"}), 500

    SIGNS_BR = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    SIGN_LORDS_BR = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
                     "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
    EXALT_BR = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
    DEBIL_BR = {"Sun":6,"Moon":7,"Mars":3,"Mercury":11,"Jupiter":9,"Venus":5,"Saturn":0}
    OWN_BR   = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
                "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
    BENEFIC_BR = {"Jupiter","Venus","Mercury","Moon"}
    MALEFIC_BR = {"Saturn","Mars","Rahu","Ketu"}

    # KP Vimshottari sub-lord calc helpers
    KP_SEQ   = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
    KP_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
                "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
    # 27 nakshatra lords in order
    NAK_LORDS = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
                 "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
                 "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
    NAK_SPAN = 360.0 / 27.0   # 13°20'

    def sidx(sname):
        try: return SIGNS_BR.index(sname)
        except: return 0

    def getp(k, name):
        for p in k.get("planets", []):
            if p["name"] == name: return p
        return None

    def vargap(k, chart, name):
        v = (k.get("divisionalCharts") or {}).get(chart) or {}
        for p in v.get("planets", []):
            if p["name"] == name: return p
        return None

    def dignity(planet, sign_index):
        if EXALT_BR.get(planet) == sign_index: return 2
        if DEBIL_BR.get(planet) == sign_index: return -2
        if sign_index in OWN_BR.get(planet, []): return 1
        return 0

    def dword(d):
        return {2:"exalted",1:"own-sign",0:"neutral",-2:"debilitated"}.get(d,"neutral")

    def aspects_planet(k, target):
        tgt = getp(k, target)
        if not tgt: return []
        ts = sidx(tgt["sign"])
        hits = []
        for p in k.get("planets", []):
            if p["name"] == target: continue
            ps = sidx(p["sign"])
            d = (ts - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":    ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn":  ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    def aspects_house(k, hnum):
        asc = sidx(k.get("ascendant","Aries"))
        tgt_sign = (asc + hnum - 1) % 12
        hits = []
        for p in k.get("planets", []):
            ps = sidx(p["sign"])
            d = (tgt_sign - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":    ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn":  ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    def occupants(k, hnum):
        return [p["name"] for p in k.get("planets", []) if p["house"] == hnum]

    def kp_sub_lord(longitude):
        """KP Vimshottari sub-lord from a sidereal longitude."""
        lon = longitude % 360.0
        nak_idx = int(lon // NAK_SPAN)
        pos_in_nak = lon - nak_idx * NAK_SPAN       # 0..13.333
        nak_lord = NAK_LORDS[nak_idx]
        # sub-lord sequence starts from nak_lord, cycles 9
        start = KP_SEQ.index(nak_lord)
        frac = 0.0
        for i in range(9):
            sl = KP_SEQ[(start + i) % 9]
            sl_span = NAK_SPAN * (KP_YEARS[sl] / 120.0)
            if pos_in_nak <= frac + sl_span + 1e-9:
                return {"nak_lord": nak_lord, "sub_lord": sl}
            frac += sl_span
        return {"nak_lord": nak_lord, "sub_lord": KP_SEQ[(start + 8) % 9]}

    def planet_house(k, planet_name):
        p = getp(k, planet_name)
        return p["house"] if p else None

    def house_of_sign_lord(k, target_planet_name):
        """Return the house where the sign-lord of a planet sits (i.e., dispositor's house)."""
        p = getp(k, target_planet_name)
        if not p: return None
        lord = SIGN_LORDS_BR[sidx(p["sign"])]
        lp = getp(k, lord)
        return lp["house"] if lp else None

    def name_of(k): return k.get("name") or "partner"

    reasons = []

    # ── 1. DASHA (60 pts) ───────────────────────────────────────────────────────
    # Check MD/AD for each; planets linked to 6/8/12/3 houses OR malefic nature
    # increase breakup risk. Benefic relational dashas reduce risk.
    def score_dasha():
        points = 0
        NEG_HOUSES = {6, 8, 12, 3}   # conflict/break/separation/communication gap
        HOUSE_LABEL = {6:"6th (conflict)", 8:"8th (sudden break)",
                       12:"12th (separation)", 3:"3rd (communication gap)"}
        STRESS = {"Saturn","Rahu","Ketu","Mars"}
        BENEFIC_REL = {"Venus","Moon","Jupiter"}

        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            cd = k.get("currentDasha") or {}
            md, ad = cd.get("maha"), cd.get("antar")
            pd = cd.get("pratyantar")
            for role, weight, planet in [("MD", 18, md), ("AD", 10, ad), ("PD", 5, pd)]:
                if not planet: continue
                pl_house = planet_house(k, planet)
                disp_house = house_of_sign_lord(k, planet)

                # Check placement/dispositor in negative houses
                hit_houses = []
                if pl_house in NEG_HOUSES:   hit_houses.append(pl_house)
                if disp_house in NEG_HOUSES: hit_houses.append(disp_house)
                if hit_houses:
                    h = hit_houses[0]
                    points += weight
                    reasons.append(
                        f"{lbl} running {planet} {role} linked to house {HOUSE_LABEL[h]} — "
                        f"active period activates break tendency"
                    )

                # Stress-nature planet adds risk
                if planet in STRESS:
                    points += int(weight * 0.55)
                    reasons.append(
                        f"{lbl}'s {planet} {role} is a stress-nature planet — "
                        f"timing amplifies tension"
                    )

                # Benefic relational planet in good house reduces risk
                elif planet in BENEFIC_REL and pl_house in (1,4,5,7,9,10,11):
                    points -= int(weight * 0.5)
                    reasons.append(
                        f"{lbl}'s {planet} {role} in house {pl_house} — "
                        f"supportive dasha reducing breakup risk"
                    )
        # clamp dasha portion to [-20, +60]
        return max(-20, min(60, points))

    # ── 2. HOUSE & PLANET AFFLICTION (25 pts) ───────────────────────────────────
    def score_houses():
        points = 0
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            asc = sidx(k.get("ascendant","Aries"))
            seventh_lord = SIGN_LORDS_BR[(asc + 6) % 12]
            seventh_lord_p = getp(k, seventh_lord)

            # 7th house occupants / aspects
            occ7 = occupants(k, 7)
            asp7 = aspects_house(k, 7)
            mal_7 = [p for p in occ7 if p in MALEFIC_BR]
            mal_asp = [p for p in asp7 if p in MALEFIC_BR and p not in occ7]

            if mal_7:
                points += 4 * len(mal_7)
                reasons.append(
                    f"{lbl}'s 7th house occupied by {', '.join(mal_7)} — direct affliction on partnership"
                )
            if "Saturn" in mal_asp:
                points += 3
                reasons.append(f"{lbl}'s Saturn aspects 7th house — emotional distance / coldness")
            if "Mars" in mal_asp:
                points += 3
                reasons.append(f"{lbl}'s Mars aspects 7th house — fights / aggression on partner axis")
            if "Rahu" in mal_asp or "Ketu" in mal_asp:
                points += 2
                reasons.append(f"{lbl}'s Rahu/Ketu influence on 7th axis — karmic confusion in bond")

            # 7th lord weakness
            if seventh_lord_p:
                if seventh_lord_p["house"] in (6,8,12):
                    points += 6
                    reasons.append(
                        f"{lbl}'s 7th lord {seventh_lord} in dusthana house {seventh_lord_p['house']} — "
                        f"weak marriage foundation"
                    )
                d = dignity(seventh_lord, sidx(seventh_lord_p["sign"]))
                if d <= -2:
                    points += 4
                    reasons.append(f"{lbl}'s 7th lord {seventh_lord} debilitated — relationship fragility")

            # Malefics in 2nd (family) and 5th (romance)
            for hnum, label in [(2,"2nd (family/wealth)"), (5,"5th (romance/progeny)")]:
                occ = occupants(k, hnum)
                mal_here = [p for p in occ if p in MALEFIC_BR]
                if mal_here:
                    points += 2
                    reasons.append(f"{lbl} has {', '.join(mal_here)} in {label} — damages supportive pillars")

            # 1-7 Rahu/Ketu axis
            rahu = getp(k, "Rahu")
            ketu = getp(k, "Ketu")
            if rahu and rahu["house"] in (1,7):
                points += 3
                reasons.append(f"{lbl}'s Rahu on 1-7 axis — obsessive / unstable partnership pull")
            if ketu and ketu["house"] in (1,7):
                points += 3
                reasons.append(f"{lbl}'s Ketu on 1-7 axis — detachment urge in relationship")
        # clamp
        return min(25, points)

    # ── 3. VENUS & MOON AFFLICTION (10 pts) ─────────────────────────────────────
    def score_venus_moon():
        points = 0
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            for tgt in ("Venus", "Moon"):
                p = getp(k, tgt)
                if not p: continue
                d = dignity(tgt, sidx(p["sign"]))
                if d <= -2:
                    points += 3
                    reasons.append(
                        f"{lbl}'s {tgt} debilitated in {p['sign']} — " +
                        ("love instability" if tgt == "Venus" else "emotional disconnect")
                    )
                # conjunction or aspect with Saturn/Rahu/Ketu
                same_sign = [q["name"] for q in k.get("planets", [])
                             if q["name"] in ("Saturn","Rahu","Ketu") and q["sign"] == p["sign"]]
                asp_bad = [a for a in aspects_planet(k, tgt) if a in ("Saturn","Rahu","Ketu")]
                total = set(same_sign) | set(asp_bad)
                if total:
                    points += len(total)
                    reasons.append(
                        f"{lbl}'s {tgt} afflicted by {', '.join(sorted(total))} — " +
                        ("love coldness / karmic pull" if tgt == "Venus"
                         else "emotional strain / mood instability")
                    )
        return min(10, points)

    # ── 4. KP SUB-LORD CONFIRMATION (5 pts) ─────────────────────────────────────
    def score_kp():
        points = 0
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            cd = k.get("currentDasha") or {}
            md = cd.get("maha")
            if not md: continue
            md_planet = getp(k, md)
            if not md_planet: continue
            sub = kp_sub_lord(md_planet.get("longitude", 0.0))
            sub_lord = sub["sub_lord"]
            # Where does sub-lord sit, and where does its dispositor sit
            sl_planet = getp(k, sub_lord)
            if not sl_planet:
                continue
            sl_house = sl_planet["house"]
            sl_disp_house = house_of_sign_lord(k, sub_lord)
            flagged = []
            if sl_house in (6, 8, 12):       flagged.append(sl_house)
            if sl_disp_house in (6, 8, 12):  flagged.append(sl_disp_house)
            if flagged:
                points += 3
                reasons.append(
                    f"{lbl}'s KP sub-lord {sub_lord} (of {md} MD) connected to house "
                    f"{flagged[0]} — confirms separation pattern"
                )
            else:
                reasons.append(
                    f"{lbl}'s KP sub-lord {sub_lord} (of {md} MD) not tied to 6/8/12 — "
                    f"no KP separation signature"
                )
        return min(5, points)

    # ── 5. TRANSIT ADJUSTMENT (±10) ─────────────────────────────────────────────
    def score_transit():
        points = 0
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        now = _dt.utcnow()
        jd  = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        transits = {}
        for pname, pid in [("Jupiter",swe.JUPITER),("Saturn",swe.SATURN),
                           ("Mars",swe.MARS),("Rahu",swe.MEAN_NODE)]:
            try:
                r = swe.calc_ut(jd, pid, flags)
                transits[pname] = int((r[0][0] % 360) // 30)
            except Exception: pass
        if "Rahu" in transits:
            transits["Ketu"] = (transits["Rahu"] + 6) % 12

        def asp_signs(planet, ts):
            out = [(ts + 6) % 12]
            if planet == "Jupiter": out += [(ts+4)%12, (ts+8)%12]
            if planet == "Saturn":  out += [(ts+2)%12, (ts+9)%12]
            if planet == "Mars":    out += [(ts+3)%12, (ts+7)%12]
            if planet in ("Rahu","Ketu"): out += [(ts+4)%12, (ts+8)%12]
            return out

        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            asc = sidx(k.get("ascendant","Aries"))
            seventh_sign = (asc + 6) % 12
            venus = getp(k, "Venus"); moon = getp(k, "Moon")
            vs = sidx(venus["sign"]) if venus else None
            ms = sidx(moon["sign"])  if moon  else None
            for tp, tsign in transits.items():
                aspects = asp_signs(tp, tsign)
                for tgt_name, tgt in [("7th house", seventh_sign), ("Venus", vs), ("Moon", ms)]:
                    if tgt is None: continue
                    if tgt in aspects:
                        if tp == "Jupiter":
                            points -= 2
                            reasons.append(f"{lbl}: Jupiter transit aspects {tgt_name} — protection / healing of bond")
                        elif tp == "Saturn":
                            points += 2
                            reasons.append(f"{lbl}: Saturn transit aspects {tgt_name} — delay / separation pressure")
                        elif tp == "Mars":
                            points += 2
                            reasons.append(f"{lbl}: Mars transit aspects {tgt_name} — fight / anger outburst trigger")
                        elif tp in ("Rahu","Ketu"):
                            points += 1
                            reasons.append(f"{lbl}: {tp} transit aspects {tgt_name} — karmic shift / confusion")
        # clamp into [-10, +10]
        return max(-10, min(10, points))

    # ── 6. RUN ALL SECTIONS ─────────────────────────────────────────────────────
    d_pts   = score_dasha()        # range roughly [-20, +60]
    h_pts   = score_houses()       # [0, 25]
    vm_pts  = score_venus_moon()   # [0, 10]
    kp_pts  = score_kp()           # [0, 5]
    t_pts   = score_transit()      # [-10, +10]

    raw = d_pts + h_pts + vm_pts + kp_pts + t_pts
    breakup_score = max(0, min(100, round(raw)))

    if   breakup_score <= 30:  risk = "low"
    elif breakup_score <= 60:  risk = "medium"
    elif breakup_score <= 80:  risk = "high"
    else:                      risk = "very high"

    def sev(val, lo_thresh, hi_thresh):
        if val >= hi_thresh: return "severe"
        if val >= lo_thresh: return "moderate"
        return "low"

    factors = {
        "dasha":      sev(max(0, d_pts), 10, 30),
        "houses":     sev(h_pts, 8, 16),
        "venus_moon": sev(vm_pts, 3, 6),
        "kp":         sev(kp_pts, 2, 4),
    }

    # Dedupe reasons preserving order
    seen = set(); unique_reasons = []
    for r in reasons:
        if r not in seen:
            seen.add(r); unique_reasons.append(r)

    return jsonify({
        "breakup_score": breakup_score,
        "risk_level":    risk,
        "factors":       factors,
        "reasons":       unique_reasons,
        "breakdown": {
            "dasha":      d_pts,
            "houses":     h_pts,
            "venus_moon": vm_pts,
            "kp":         kp_pts,
            "transit":    t_pts,
        },
    })


@app.route("/api/loyalty-check", methods=["POST"])
def loyalty_check():
    """
    Ultra-advanced Vedic + KP Loyalty Engine — BOTH kundlis required.
    Body: { p1, p2 }
    Returns:
      {
        loyalty_score: 0-100,
        loyalty_level: "high|moderate|unstable|risky",
        behavior_type: "loyal|tempted|emotionally unstable|dual-nature",
        time_factor:   "temporary_phase|long_term_pattern",
        factors: { venus, moon, "7th_house", rahu, dasha, kp },
        reasons: [ ... ]
      }
    Scoring: start 50 · Venus ±20 · Moon ±15 · 7th ±15 · Rahu -20 · Cross -10 · Dasha ±10 · KP -10
    """
    data = request.get_json(force=True, silent=True) or {}
    if "p1" not in data or "p2" not in data:
        return jsonify({"error": "Missing p1 or p2"}), 400

    try:
        k1 = calculate_kundli(data["p1"])
        k2 = calculate_kundli(data["p2"])
    except Exception as exc:
        return jsonify({"error": f"Kundli calculation failed: {exc}"}), 500

    SIGNS_L  = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    LORDS_L  = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
                "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
    EXALT_L  = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
    DEBIL_L  = {"Sun":6,"Moon":7,"Mars":3,"Mercury":11,"Jupiter":9,"Venus":5,"Saturn":0}
    OWN_L    = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
                "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
    MALEFIC_L = {"Saturn","Mars","Rahu","Ketu","Sun"}

    KP_SEQ   = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
    KP_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
                "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
    NAK_LORDS = (["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"] * 3)
    NAK_SPAN  = 360.0 / 27.0

    def sidx(sn):
        try: return SIGNS_L.index(sn)
        except: return 0

    def getp(k, name):
        for p in k.get("planets", []):
            if p["name"] == name: return p
        return None

    def getvargap(k, chart, name):
        v = (k.get("divisionalCharts") or {}).get(chart) or {}
        for p in v.get("planets", []):
            if p["name"] == name: return p
        return None

    def dignity(pl, si):
        if EXALT_L.get(pl) == si: return 2
        if DEBIL_L.get(pl) == si: return -2
        if si in OWN_L.get(pl, []): return 1
        return 0

    def dword(d):
        return {2:"exalted",1:"own-sign",0:"neutral",-2:"debilitated"}.get(d,"neutral")

    def aspects_planet(k, target):
        tgt = getp(k, target)
        if not tgt: return []
        ts = sidx(tgt["sign"])
        hits = []
        for p in k.get("planets", []):
            if p["name"] == target: continue
            ps = sidx(p["sign"])
            d = (ts - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":    ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn":  ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    def aspects_house(k, hnum):
        asc = sidx(k.get("ascendant","Aries"))
        tgt_sign = (asc + hnum - 1) % 12
        hits = []
        for p in k.get("planets", []):
            ps = sidx(p["sign"])
            d = (tgt_sign - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":    ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn":  ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    def occupants(k, hnum):
        return [p["name"] for p in k.get("planets", []) if p["house"] == hnum]

    def kp_sub_lord(lon):
        lon = lon % 360.0
        nak_idx = int(lon // NAK_SPAN)
        pos = lon - nak_idx * NAK_SPAN
        nak_lord = NAK_LORDS[nak_idx]
        start = KP_SEQ.index(nak_lord)
        frac = 0.0
        for i in range(9):
            sl = KP_SEQ[(start + i) % 9]
            sp = NAK_SPAN * (KP_YEARS[sl] / 120.0)
            if pos <= frac + sp + 1e-9:
                return {"nak_lord": nak_lord, "sub_lord": sl}
            frac += sp
        return {"nak_lord": nak_lord, "sub_lord": KP_SEQ[(start + 8) % 9]}

    def name_of(k): return k.get("name") or "partner"

    reasons = []

    # ── 1. CROSS-COMPATIBILITY (−10 max penalty) ─────────────────────────────
    # Compare Venus↔Mars (attraction sync) and Moon↔Moon (emotional sync)
    # and Rahu/Ketu cross-hits.
    def cross_mismatch():
        pen = 0
        v1 = getp(k1, "Venus"); v2 = getp(k2, "Venus")
        m1 = getp(k1, "Moon");  m2 = getp(k2, "Moon")
        ma1 = getp(k1, "Mars"); ma2 = getp(k2, "Mars")
        r1 = getp(k1, "Rahu");  r2 = getp(k2, "Rahu")
        k1_ = getp(k1, "Ketu"); k2_ = getp(k2, "Ketu")

        # Venus element vs partner Mars element (fire/earth/air/water harmony)
        ELEM = [0,1,2,3]*3  # 0=fire,1=earth,2=air,3=water by sign%4
        def elem(si): return si % 4
        harm_fire_air = {(0,2),(2,0)}     # fire↔air
        harm_earth_water = {(1,3),(3,1)}  # earth↔water
        pairs = [
            ("A's Venus vs B's Mars", v1, ma2),
            ("B's Venus vs A's Mars", v2, ma1),
        ]
        for lbl, a, b in pairs:
            if not a or not b: continue
            ea, eb = elem(sidx(a["sign"])), elem(sidx(b["sign"]))
            if ea == eb:
                reasons.append(f"{lbl}: same element — natural attraction sync")
            elif (ea,eb) in harm_fire_air or (ea,eb) in harm_earth_water:
                reasons.append(f"{lbl}: complementary elements — healthy spark")
            else:
                pen += 3
                reasons.append(f"{lbl}: element mismatch — attraction drifts over time")

        # Moon-Moon emotional sync (6/8/12 apart from each other = tension)
        if m1 and m2:
            d = abs(sidx(m1["sign"]) - sidx(m2["sign"]))
            d = min(d, 12 - d)
            if d in (5, 6, 7):
                pen += 4
                reasons.append("Moon-Moon axis shows emotional mismatch between partners")
            elif d in (0, 3, 4):
                reasons.append("Moon-Moon axis in supportive rhythm — emotional sync good")

        # Partner Rahu sitting on self Venus/Moon
        def rahu_cross(own_k_lbl, own_v, own_m, partner_rahu, partner_ketu):
            out = 0
            for nm, pl in [("Venus", own_v), ("Moon", own_m)]:
                if not pl: continue
                ps = sidx(pl["sign"])
                for nodep, nodelbl in [(partner_rahu,"Rahu"), (partner_ketu,"Ketu")]:
                    if not nodep: continue
                    if sidx(nodep["sign"]) == ps:
                        out += 2
                        reasons.append(
                            f"{own_k_lbl}'s {nm} conjunct partner's {nodelbl} — karmic obsession / drifting pull"
                        )
            return out
        pen += rahu_cross(name_of(k1), v1, m1, r2, k2_)
        pen += rahu_cross(name_of(k2), v2, m2, r1, k1_)

        return min(10, pen)

    # ── 2. VENUS (±20) ───────────────────────────────────────────────────────
    def venus_section():
        total = 0
        per_person_state = {}
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            pts = 0
            v = getp(k, "Venus")
            if not v: continue
            si = sidx(v["sign"])
            d = dignity("Venus", si)
            # D1 dignity
            if d >= 2:
                pts += 10; reasons.append(f"{lbl}'s Venus exalted in {v['sign']} — deep committed love nature")
            elif d == 1:
                pts += 6;  reasons.append(f"{lbl}'s Venus in own-sign {v['sign']} — natural loyalty in love")
            elif d <= -2:
                pts -= 10; reasons.append(f"{lbl}'s Venus debilitated in {v['sign']} — weak love nature, easily swayed")
            # D9 Venus dignity
            v9 = getvargap(k, "D9", "Venus")
            if v9:
                d9 = dignity("Venus", v9["signIndex"])
                if d9 >= 2:
                    pts += 4; reasons.append(f"{lbl}'s D9 Venus exalted — marriage love is sincere")
                elif d9 <= -2:
                    pts -= 4; reasons.append(f"{lbl}'s D9 Venus debilitated — struggle to maintain marital devotion")
            # Afflictions
            same_sign = {q["name"] for q in k.get("planets", []) if q["sign"] == v["sign"]}
            if "Rahu" in same_sign:
                pts -= 8; reasons.append(f"{lbl}'s Venus conjunct Rahu — illusion / attraction outside relationship")
            if "Mars" in same_sign:
                pts -= 3; reasons.append(f"{lbl}'s Venus conjunct Mars — impulsive passion, fiery attractions")
            if "Saturn" in same_sign:
                pts -= 3; reasons.append(f"{lbl}'s Venus conjunct Saturn — cold / distant in love expression")
            asp = aspects_planet(k, "Venus")
            if "Rahu" in asp and "Rahu" not in same_sign:
                pts -= 4; reasons.append(f"{lbl}'s Venus aspected by Rahu — hidden attractions, fantasy-driven")
            if "Saturn" in asp and "Saturn" not in same_sign:
                pts -= 2; reasons.append(f"{lbl}'s Venus aspected by Saturn — love feels heavy / delayed")

            total += pts
            # derive readable state
            if pts >= 6:   st = "strong and loyal"
            elif pts >= 0: st = "stable"
            elif pts >= -5:st = "weak"
            else:          st = "afflicted / temptation-prone"
            per_person_state[lbl] = st

        total = max(-20, min(20, total))
        # Combined one-line factor
        people_txt = " · ".join(f"{who}: {st}" for who, st in per_person_state.items())
        return total, people_txt

    # ── 3. MOON (±15) ────────────────────────────────────────────────────────
    def moon_section():
        total = 0
        per = {}
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            pts = 0
            m = getp(k, "Moon")
            if not m: continue
            si = sidx(m["sign"])
            d = dignity("Moon", si)
            if d >= 2:
                pts += 8; reasons.append(f"{lbl}'s Moon exalted in {m['sign']} — strong emotional loyalty")
            elif d == 1:
                pts += 5; reasons.append(f"{lbl}'s Moon in own sign — emotionally anchored")
            elif d <= -2:
                pts -= 8; reasons.append(f"{lbl}'s Moon debilitated in {m['sign']} — emotional instability, mood-driven")
            same = {q["name"] for q in k.get("planets", []) if q["sign"] == m["sign"]}
            if "Saturn" in same:
                pts -= 4; reasons.append(f"{lbl}'s Moon conjunct Saturn — emotional coldness / depressive loyalty")
            if "Rahu" in same:
                pts -= 5; reasons.append(f"{lbl}'s Moon conjunct Rahu — restless emotions, craving for novelty")
            if "Ketu" in same:
                pts -= 3; reasons.append(f"{lbl}'s Moon conjunct Ketu — emotional detachment, sudden pull-outs")
            asp = aspects_planet(k, "Moon")
            if "Saturn" in asp and "Saturn" not in same:
                pts -= 2; reasons.append(f"{lbl}'s Moon aspected by Saturn — emotional suppression")
            if "Mars" in asp:
                pts -= 1; reasons.append(f"{lbl}'s Moon influenced by Mars — emotional outbursts")
            # Dependency: Moon in 7th/8th/12th = codependent/secretive
            if m["house"] in (8, 12):
                pts -= 2; reasons.append(f"{lbl}'s Moon in house {m['house']} — hidden emotional undercurrents")
            # D9 Moon
            m9 = getvargap(k, "D9", "Moon")
            if m9:
                d9 = dignity("Moon", m9["signIndex"])
                if d9 >= 2:
                    pts += 3; reasons.append(f"{lbl}'s D9 Moon strong — marital emotions stay loyal")
                elif d9 <= -2:
                    pts -= 3; reasons.append(f"{lbl}'s D9 Moon debilitated — inner mind wavers in marriage")

            total += pts
            if pts >= 5:  st = "stable and loyal"
            elif pts >= 0:st = "steady"
            else:         st = "unstable / afflicted"
            per[lbl] = st

        total = max(-15, min(15, total))
        return total, " · ".join(f"{who}: {st}" for who, st in per.items())

    # ── 4. 7TH HOUSE (±15) ───────────────────────────────────────────────────
    def seventh_section():
        total = 0
        per = {}
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            pts = 5  # baseline +5 commitment credit
            asc = sidx(k.get("ascendant","Aries"))
            lord = LORDS_L[(asc + 6) % 12]
            lord_p = getp(k, lord)
            # occupants & aspects
            occ7 = occupants(k, 7)
            asp7 = aspects_house(k, 7)
            mal_in = [x for x in occ7 if x in MALEFIC_L]
            mal_asp = [x for x in asp7 if x in MALEFIC_L and x not in occ7]
            if mal_in:
                pts -= 3 * min(2, len(mal_in))
                reasons.append(f"{lbl}'s 7th occupied by {', '.join(mal_in)} — malefic influence on commitment")
            if "Rahu" in mal_in or "Rahu" in mal_asp:
                pts -= 3
                reasons.append(f"{lbl}'s Rahu on 7th axis — dual-relationship tendency")
            if "Saturn" in mal_asp:
                pts -= 2
                reasons.append(f"{lbl}'s Saturn aspects 7th — commitment feels burdensome")
            if "Jupiter" in asp7:
                pts += 4
                reasons.append(f"{lbl}'s Jupiter aspects 7th — blessing of sincere commitment")
            if "Venus" in occ7:
                pts += 3
                reasons.append(f"{lbl}'s Venus in 7th — devoted romantic nature")
            if "Moon" in occ7:
                pts += 2
                reasons.append(f"{lbl}'s Moon in 7th — emotionally attached to partnership")
            # 7th lord condition
            if lord_p:
                lsi = sidx(lord_p["sign"])
                ld = dignity(lord, lsi)
                if lord_p["house"] in (6,8,12):
                    pts -= 4
                    reasons.append(f"{lbl}'s 7th lord {lord} in dusthana {lord_p['house']} — commitment weakened")
                if ld >= 1:
                    pts += 3
                    reasons.append(f"{lbl}'s 7th lord {lord} {dword(ld)} — commitment strength supported")
                elif ld <= -2:
                    pts -= 4
                    reasons.append(f"{lbl}'s 7th lord {lord} debilitated — low commitment capacity")
            # D9 Lagna strength (marriage body) — Jupiter/Venus influence
            d9 = k.get("divisionalCharts", {}).get("D9") or {}
            d9p = d9.get("planets", [])
            d9_7 = [q["name"] for q in d9p if q["house"] == 7]
            if any(x in ("Rahu","Ketu","Saturn") for x in d9_7):
                pts -= 3
                reasons.append(f"{lbl}'s D9 7th house has malefic — marriage loyalty tested")
            if "Jupiter" in d9_7 or "Venus" in d9_7:
                pts += 2
                reasons.append(f"{lbl}'s D9 7th has benefic — marital devotion supported")

            total += pts
            if pts >= 6:  st = "strong commitment"
            elif pts >= 0:st = "moderate commitment"
            else:         st = "weak commitment / tested"
            per[lbl] = st

        total = max(-15, min(15, total))
        return total, " · ".join(f"{who}: {st}" for who, st in per.items())

    # ── 5. RAHU IMPACT (−20 max, never positive) ─────────────────────────────
    def rahu_section():
        pen = 0
        per = {}
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            local = 0
            r = getp(k, "Rahu")
            if not r: continue
            h = r["house"]
            # Rahu with Venus/Moon
            v = getp(k, "Venus"); m = getp(k, "Moon")
            if v and v["sign"] == r["sign"]:
                local += 7; reasons.append(f"{lbl}'s Rahu+Venus — strong cheating driver / illusion in love")
            if m and m["sign"] == r["sign"]:
                local += 6; reasons.append(f"{lbl}'s Rahu+Moon — mental restlessness for novelty")
            # Rahu in sensitive houses
            if h == 7:
                local += 5; reasons.append(f"{lbl}'s Rahu in 7th — karmic dual-partnership trigger")
            elif h == 5:
                local += 3; reasons.append(f"{lbl}'s Rahu in 5th — craves thrill in romance")
            elif h == 12:
                local += 4; reasons.append(f"{lbl}'s Rahu in 12th — secretive pleasures tendency")
            # Rahu aspects on love planets
            rahu_asp = aspects_planet(k, "Venus")
            moon_asp = aspects_planet(k, "Moon")
            if "Rahu" in rahu_asp: local += 2
            if "Rahu" in moon_asp: local += 2
            pen += local
            if   local >= 10: st = "strong cheating driver"
            elif local >= 6:  st = "temptation-prone"
            elif local >= 3:  st = "mild restlessness"
            else:             st = "benign"
            per[lbl] = st
        pen = min(20, pen)
        return -pen, " · ".join(f"{who}: {st}" for who, st in per.items())

    # ── 6. DASHA (±10) ───────────────────────────────────────────────────────
    ATTR = {"Venus","Rahu","Mars"}
    DET  = {"Saturn","Ketu"}
    def dasha_section():
        total = 0
        per = {}
        nontransient = 0
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            cd = k.get("currentDasha") or {}
            md, ad, pd = cd.get("maha"), cd.get("antar"), cd.get("pratyantar")
            local_state = []
            for role, w, pl in [("MD", 4, md), ("AD", 2, ad), ("PD", 1, pd)]:
                if not pl: continue
                if pl in ATTR:
                    total -= w
                    local_state.append(f"{pl} {role} attraction phase")
                    reasons.append(f"{lbl}: {pl} {role} — attraction / temptation phase active")
                elif pl in DET:
                    total -= int(w * 0.6)
                    local_state.append(f"{pl} {role} detachment phase")
                    reasons.append(f"{lbl}: {pl} {role} — detachment / coldness phase")
                elif pl in ("Jupiter","Moon"):
                    total += w
                    local_state.append(f"{pl} {role} loyal phase")
                    reasons.append(f"{lbl}: {pl} {role} — supportive loyal period")
            per[lbl] = ", ".join(local_state) if local_state else "neutral period"
        total = max(-10, min(10, total))
        return total, " · ".join(f"{who}: {st}" for who, st in per.items())

    # ── 7. KP CONFIRMATION (−10 max) ─────────────────────────────────────────
    def kp_section():
        pen = 0
        per = {}
        for lbl, k in [(name_of(k1), k1), (name_of(k2), k2)]:
            cd = k.get("currentDasha") or {}
            md = cd.get("maha")
            if not md:
                per[lbl] = "no active MD"
                continue
            md_p = getp(k, md)
            if not md_p:
                per[lbl] = "no data"
                continue
            sub = kp_sub_lord(md_p.get("longitude", 0.0))
            sl = sub["sub_lord"]
            sl_p = getp(k, sl)
            sl_house = sl_p["house"] if sl_p else None
            # sub-lord's dispositor house
            disp_house = None
            if sl_p:
                disp = LORDS_L[sidx(sl_p["sign"])]
                dp = getp(k, disp)
                disp_house = dp["house"] if dp else None

            hit = None
            for h in (sl_house, disp_house):
                if h in (12, 7, 5):
                    hit = h; break
            if hit == 12:
                pen += 6
                reasons.append(f"{lbl}'s KP sub-lord {sl} (of {md} MD) tied to 12th — secret affair signature")
                per[lbl] = f"sub-lord {sl} → 12th (hidden behaviour)"
            elif hit == 7:
                pen += 4
                reasons.append(f"{lbl}'s KP sub-lord {sl} tied to 7th — dual-relationship trigger")
                per[lbl] = f"sub-lord {sl} → 7th (relationship pull)"
            elif hit == 5:
                pen += 2
                reasons.append(f"{lbl}'s KP sub-lord {sl} tied to 5th — romance-chase activation")
                per[lbl] = f"sub-lord {sl} → 5th (romance)"
            else:
                reasons.append(f"{lbl}'s KP sub-lord {sl} not tied to 5/7/12 — no cheating signature")
                per[lbl] = f"sub-lord {sl} — neutral"
        pen = min(10, pen)
        return -pen, " · ".join(f"{who}: {st}" for who, st in per.items())

    # ── RUN ALL ──────────────────────────────────────────────────────────────
    v_pts,   v_txt   = venus_section()
    m_pts,   m_txt   = moon_section()
    s_pts,   s_txt   = seventh_section()
    r_pts,   r_txt   = rahu_section()      # negative or 0
    cross_pen        = cross_mismatch()    # positive 0..10
    d_pts,   d_txt   = dasha_section()
    kp_pts,  kp_txt  = kp_section()        # negative or 0

    start = 50
    raw = start + v_pts + m_pts + s_pts + r_pts - cross_pen + d_pts + kp_pts
    loyalty_score = max(0, min(100, round(raw)))

    # Level
    if   loyalty_score >= 75: level = "high"
    elif loyalty_score >= 55: level = "moderate"
    elif loyalty_score >= 35: level = "unstable"
    else:                     level = "risky"

    # Behavior classification
    # Look for Rahu+Venus signature in either chart
    def has_rahu_venus(k):
        v = getp(k, "Venus"); r = getp(k, "Rahu")
        if v and r and v["sign"] == r["sign"]: return True
        return "Rahu" in aspects_planet(k, "Venus")
    def moon_weak(k):
        m = getp(k, "Moon")
        if not m: return False
        return dignity("Moon", sidx(m["sign"])) <= -2 or \
               any(q["name"] in ("Saturn","Rahu","Ketu") and q["sign"] == m["sign"]
                   for q in k.get("planets", []))

    rahu_venus_flag = has_rahu_venus(k1) or has_rahu_venus(k2)
    moon_weak_flag  = moon_weak(k1) or moon_weak(k2)
    # KP signature + Rahu on 7th axis → dual-nature
    dual_flag = False
    for k in (k1, k2):
        r = getp(k, "Rahu")
        if r and r["house"] in (1,7) and kp_pts <= -4:
            dual_flag = True; break

    if dual_flag:
        behavior = "dual-nature"
    elif rahu_venus_flag and loyalty_score < 65:
        behavior = "tempted"
    elif moon_weak_flag and loyalty_score < 60:
        behavior = "emotionally unstable"
    else:
        behavior = "loyal"

    # Time factor: natal vs only transient
    natal_negative = (v_pts < -4) or (m_pts < -4) or (s_pts < -4) or (r_pts <= -10) or (cross_pen >= 6) or (kp_pts <= -4)
    transient_negative = (d_pts <= -4)
    if natal_negative:
        time_factor = "long_term_pattern"
    elif transient_negative:
        time_factor = "temporary_phase"
    else:
        time_factor = "temporary_phase"

    factors = {
        "venus":     v_txt or "stable",
        "moon":      m_txt or "stable",
        "7th_house": s_txt or "stable",
        "rahu":      r_txt or "benign",
        "dasha":     d_txt or "neutral",
        "kp":        kp_txt or "neutral",
    }

    seen = set(); unique_reasons = []
    for r in reasons:
        if r not in seen:
            seen.add(r); unique_reasons.append(r)

    return jsonify({
        "loyalty_score":  loyalty_score,
        "loyalty_level":  level,
        "behavior_type":  behavior,
        "time_factor":    time_factor,
        "factors":        factors,
        "reasons":        unique_reasons,
        "breakdown": {
            "venus":  v_pts,
            "moon":   m_pts,
            "seventh": s_pts,
            "rahu":   r_pts,
            "cross":  -cross_pen,
            "dasha":  d_pts,
            "kp":     kp_pts,
            "start":  start,
        },
    })


@app.route("/api/will-return", methods=["POST"])
def will_return():
    """
    Will X Return — Vedic (Parashari) + KP reunion-prediction engine.
    PERSON A (p1) is PRIMARY chart. Person B (p2) is secondary / synastry only.
    Body: { p1, p2 }
    Returns:
      {
        return_probability: 0-100,
        return_chance: "unlikely|possible|strong|very strong",
        time_window: "e.g. 2-4 months",
        reunion_type: "temporary|long-term|unstable",
        initiator: "person A|person B|mutual",
        factors: { dasha, transit, love_houses, separation_houses, kp },
        reasons: [ ... ]
      }
    Scoring: start 50 · Dasha ±30 · Transit ±20 · Love houses +15 · Separation -25 · KP ±10
    """
    import swisseph as swe
    from datetime import datetime as _dt

    data = request.get_json(force=True, silent=True) or {}
    if "p1" not in data or "p2" not in data:
        return jsonify({"error": "Missing p1 or p2"}), 400

    try:
        kA = calculate_kundli(data["p1"])
        kB = calculate_kundli(data["p2"])
    except Exception as exc:
        return jsonify({"error": f"Kundli calculation failed: {exc}"}), 500

    SIGNS_R = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
               "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    LORDS_R = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
               "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
    EXALT_R = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
    DEBIL_R = {"Sun":6,"Moon":7,"Mars":3,"Mercury":11,"Jupiter":9,"Venus":5,"Saturn":0}
    OWN_R   = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
               "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
    MALEFIC_R = {"Saturn","Mars","Rahu","Ketu"}

    KP_SEQ   = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
    KP_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
                "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
    NAK_LORDS = (["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"] * 3)
    NAK_SPAN  = 360.0 / 27.0

    def sidx(sn):
        try: return SIGNS_R.index(sn)
        except: return 0

    def getp(k, name):
        for p in k.get("planets", []):
            if p["name"] == name: return p
        return None

    def dignity(pl, si):
        if EXALT_R.get(pl) == si: return 2
        if DEBIL_R.get(pl) == si: return -2
        if si in OWN_R.get(pl, []): return 1
        return 0

    def lord_of_house(k, hnum):
        asc = sidx(k.get("ascendant","Aries"))
        return LORDS_R[(asc + hnum - 1) % 12]

    def aspects_planet(k, target):
        tgt = getp(k, target)
        if not tgt: return []
        ts = sidx(tgt["sign"])
        hits = []
        for p in k.get("planets", []):
            if p["name"] == target: continue
            ps = sidx(p["sign"])
            d = (ts - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":    ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn":  ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    def aspects_house(k, hnum):
        asc = sidx(k.get("ascendant","Aries"))
        tgt_sign = (asc + hnum - 1) % 12
        hits = []
        for p in k.get("planets", []):
            ps = sidx(p["sign"])
            d = (tgt_sign - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":    ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn":  ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    def occupants(k, hnum):
        return [p["name"] for p in k.get("planets", []) if p["house"] == hnum]

    def kp_sub_lord(lon):
        lon = lon % 360.0
        nak_idx = int(lon // NAK_SPAN)
        pos = lon - nak_idx * NAK_SPAN
        nak_lord = NAK_LORDS[nak_idx]
        start = KP_SEQ.index(nak_lord)
        frac = 0.0
        for i in range(9):
            sl = KP_SEQ[(start + i) % 9]
            sp = NAK_SPAN * (KP_YEARS[sl] / 120.0)
            if pos <= frac + sp + 1e-9:
                return {"nak_lord": nak_lord, "sub_lord": sl}
            frac += sp
        return {"nak_lord": nak_lord, "sub_lord": KP_SEQ[(start + 8) % 9]}

    reasons = []
    A_name = kA.get("name") or "You"
    B_name = kB.get("name") or "Partner"

    # Precompute: lords of key houses in A
    lords_A = {h: lord_of_house(kA, h) for h in (2,5,6,7,8,11,12)}

    LOVE_HOUSES = {5, 7, 11}
    SEP_HOUSES  = {6, 8, 12}

    def planet_linked_to_house(k, planet_name, target_house):
        """Is `planet_name` linked (occupies, rules, aspects, or its dispositor sits in) `target_house`?"""
        p = getp(k, planet_name)
        if not p: return False
        # Occupies
        if p["house"] == target_house: return True
        # Rules the sign sitting in that house
        asc = sidx(k.get("ascendant","Aries"))
        target_sign = (asc + target_house - 1) % 12
        if SIGNS_R[target_sign] and LORDS_R[target_sign] == planet_name: return True
        # Aspects the house
        asp = aspects_house(k, target_house)
        if planet_name in asp: return True
        # Dispositor sits in target house
        disp = LORDS_R[sidx(p["sign"])]
        dp = getp(k, disp)
        if dp and dp["house"] == target_house: return True
        return False

    # ── 1. DASHA ANALYSIS (±30) — Person A only ──────────────────────────────
    def score_dasha():
        pts = 0
        cd = kA.get("currentDasha") or {}
        md, ad, pd = cd.get("maha"), cd.get("antar"), cd.get("pratyantar")

        LOVE_LORDS = {lords_A[5], lords_A[7], lords_A[11], "Venus", "Moon"}
        SEP_LORDS  = {lords_A[6], lords_A[8], lords_A[12]}
        CUT_OFF    = {"Saturn","Ketu"}

        state = []
        for role, w, pl in [("MD", 15, md), ("AD", 8, ad), ("PD", 4, pd)]:
            if not pl: continue
            linked_love = any(planet_linked_to_house(kA, pl, h) for h in LOVE_HOUSES)
            linked_sep  = any(planet_linked_to_house(kA, pl, h) for h in SEP_HOUSES)
            is_love_lord = pl in LOVE_LORDS
            is_sep_lord  = pl in SEP_LORDS

            local_pts = 0
            tags = []
            if is_love_lord and linked_love:
                local_pts += w; tags.append(f"{pl} activates 5/7/11")
                reasons.append(f"{A_name}'s {pl} {role} connects to love houses — revival of bond")
            elif linked_love:
                local_pts += int(w * 0.6); tags.append(f"{pl} touches love houses")
                reasons.append(f"{A_name}'s {pl} {role} touches 5/7/11 — supports reconnection")
            if is_sep_lord or linked_sep:
                local_pts -= w; tags.append(f"{pl} activates 6/8/12")
                reasons.append(f"{A_name}'s {pl} {role} tied to 6/8/12 — separation pattern continues")
            if pl in CUT_OFF and not linked_love:
                local_pts -= int(w * 0.5); tags.append(f"{pl} detachment")
                reasons.append(f"{A_name}'s {pl} {role} — cut-off / detachment phase")
            if pl == "Venus" and not is_sep_lord:
                local_pts += int(w * 0.4); tags.append("Venus supports love")
                reasons.append(f"{A_name}'s Venus {role} — love energy active")
            if pl == "Moon" and not is_sep_lord:
                local_pts += int(w * 0.3); tags.append("Moon emotional")
                reasons.append(f"{A_name}'s Moon {role} — emotional opening")

            pts += local_pts
            if tags: state.append(f"{pl} {role}: " + ", ".join(tags))

        pts = max(-30, min(30, pts))
        txt = " · ".join(state) if state else "no active indicators"
        return pts, txt

    # ── 2. TRANSIT TRIGGER (±20) ─────────────────────────────────────────────
    def score_transit():
        pts = 0
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        now = _dt.utcnow()
        jd  = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        transits = {}
        for pname, pid in [("Jupiter",swe.JUPITER),("Saturn",swe.SATURN),
                           ("Mars",swe.MARS),("Rahu",swe.MEAN_NODE),("Venus",swe.VENUS)]:
            try:
                r = swe.calc_ut(jd, pid, flags)
                transits[pname] = int((r[0][0] % 360) // 30)
            except Exception: pass
        if "Rahu" in transits:
            transits["Ketu"] = (transits["Rahu"] + 6) % 12

        def asp_signs(planet, ts):
            out = [(ts + 6) % 12]  # 7th always
            if planet == "Jupiter": out += [(ts+4)%12, (ts+8)%12]
            if planet == "Saturn":  out += [(ts+2)%12, (ts+9)%12]
            if planet == "Mars":    out += [(ts+3)%12, (ts+7)%12]
            if planet in ("Rahu","Ketu"): out += [(ts+4)%12, (ts+8)%12]
            return out

        asc = sidx(kA.get("ascendant","Aries"))
        h5_sign = (asc + 4) % 12
        h7_sign = (asc + 6) % 12
        h11_sign= (asc + 10) % 12
        venus_A = getp(kA, "Venus"); moon_A = getp(kA, "Moon")
        vs = sidx(venus_A["sign"]) if venus_A else None
        ms = sidx(moon_A["sign"])  if moon_A  else None

        state = []
        for tp, ts in transits.items():
            asp = asp_signs(tp, ts) + [ts]  # occupation also counts
            for lbl, tgt in [("5th", h5_sign), ("7th", h7_sign), ("11th", h11_sign),
                             ("Venus", vs), ("Moon", ms)]:
                if tgt is None: continue
                if tgt in asp:
                    if tp == "Jupiter":
                        pts += 4; state.append(f"Jupiter → {lbl}")
                        reasons.append(f"Jupiter transit touches {A_name}'s {lbl} — reunion opportunity")
                    elif tp == "Saturn":
                        pts -= 3; state.append(f"Saturn → {lbl}")
                        reasons.append(f"Saturn transit on {lbl} — delay / karmic test before return")
                    elif tp == "Mars":
                        pts -= 1; state.append(f"Mars → {lbl}")
                        reasons.append(f"Mars transit on {lbl} — impulsive friction triggers")
                    elif tp == "Rahu":
                        pts += 2; state.append(f"Rahu → {lbl}")
                        reasons.append(f"Rahu transit on {lbl} — sudden/unexpected contact")
                    elif tp == "Ketu":
                        pts -= 2; state.append(f"Ketu → {lbl}")
                        reasons.append(f"Ketu transit on {lbl} — detachment / cut-off pressure")
                    elif tp == "Venus":
                        pts += 2; state.append(f"Venus → {lbl}")
                        reasons.append(f"Venus transit on {lbl} — affection window open")

        pts = max(-20, min(20, pts))
        return pts, (" · ".join(sorted(set(state))) if state else "neutral transits")

    # ── 3. LOVE HOUSES score (+15 cap) ───────────────────────────────────────
    def score_love():
        pts = 0
        state = []
        for h, w, lbl in [(5, 4, "5th (romance)"), (7, 5, "7th (relationship)"),
                          (11, 4, "11th (fulfilment)"), (2, 2, "2nd (family)")]:
            lord = lord_of_house(kA, h)
            lp = getp(kA, lord)
            bens_in = [x for x in occupants(kA, h) if x in ("Jupiter","Venus","Moon","Mercury")]
            mal_in  = [x for x in occupants(kA, h) if x in MALEFIC_R]
            bens_asp = [x for x in aspects_house(kA, h) if x in ("Jupiter","Venus")]

            local = 0
            if bens_in:
                local += w; state.append(f"{lbl}: {','.join(bens_in)} inside")
                reasons.append(f"{A_name}'s {lbl} has {', '.join(bens_in)} — strong love indicator")
            if "Jupiter" in bens_asp:
                local += 2; state.append(f"{lbl}: Jupiter aspect")
                reasons.append(f"Jupiter aspects {A_name}'s {lbl} — supports reunion")
            if lp:
                d = dignity(lord, sidx(lp["sign"]))
                if d >= 1 and lp["house"] not in (6,8,12):
                    local += 2; state.append(f"{lord} (lord of {lbl}) strong")
                    reasons.append(f"{A_name}'s {lbl} lord {lord} well-placed — revival possible")
                if d <= -2 or lp["house"] in (6,8,12):
                    local -= 2; state.append(f"{lord} (lord of {lbl}) weak")
                    reasons.append(f"{A_name}'s {lbl} lord {lord} weak / in dusthana — revival hindered")
            if mal_in and "Jupiter" not in bens_asp:
                local -= 1; state.append(f"{lbl}: malefics {','.join(mal_in)}")
            pts += local

        pts = max(0, min(15, pts))
        return pts, (" · ".join(state) if state else "love houses neutral")

    # ── 4. SEPARATION HOUSES (−25 cap) ───────────────────────────────────────
    def score_separation():
        pen = 0
        state = []
        for h, w, lbl in [(6, 5, "6th (conflict)"),
                          (8, 6, "8th (breakup)"),
                          (12,7, "12th (separation)")]:
            mal = [x for x in occupants(kA, h) if x in MALEFIC_R]
            if mal:
                pen += w; state.append(f"{lbl}: {','.join(mal)}")
                reasons.append(f"{A_name}'s {lbl} occupied by {', '.join(mal)} — separation pattern active")
            # lord placement
            lord = lord_of_house(kA, h)
            lp = getp(kA, lord)
            if lp and lp["house"] in (1, 5, 7, 11):
                pen += int(w * 0.6); state.append(f"{lord} (lord of {lbl}) in {lp['house']}")
                reasons.append(
                    f"{A_name}'s {lbl} lord {lord} sits in house {lp['house']} — separation energy "
                    f"bleeds into life/love axis"
                )
            asp = aspects_house(kA, h)
            if "Jupiter" in asp or "Venus" in asp:
                pen -= 2; state.append(f"{lbl}: benefic aspect softens")
                reasons.append(f"Benefic aspect on {A_name}'s {lbl} — softens separation")

        pen = max(0, min(25, pen))
        return -pen, (" · ".join(state) if state else "separation axis quiet")

    # ── 5. KP CONFIRMATION (±10) ─────────────────────────────────────────────
    def score_kp():
        cd = kA.get("currentDasha") or {}
        md = cd.get("maha")
        if not md:
            return 0, "no active MD"
        md_p = getp(kA, md)
        if not md_p:
            return 0, "MD planet missing"
        sub = kp_sub_lord(md_p.get("longitude", 0.0))
        sl = sub["sub_lord"]
        sl_p = getp(kA, sl)
        if not sl_p:
            return 0, f"sub-lord {sl} — no data"
        sl_house = sl_p["house"]
        disp = LORDS_R[sidx(sl_p["sign"])]
        dp = getp(kA, disp)
        disp_house = dp["house"] if dp else None

        hit_love = any(h in LOVE_HOUSES for h in (sl_house, disp_house))
        hit_sep  = any(h in SEP_HOUSES  for h in (sl_house, disp_house))

        if hit_love and not hit_sep:
            reasons.append(
                f"KP sub-lord {sl} (of {md} MD) tied to house "
                f"{next(h for h in (sl_house, disp_house) if h in LOVE_HOUSES)} — return confirmed by KP"
            )
            return 10, f"sub-lord {sl} → love house (confirms)"
        if hit_sep and not hit_love:
            reasons.append(
                f"KP sub-lord {sl} tied to house "
                f"{next(h for h in (sl_house, disp_house) if h in SEP_HOUSES)} — KP rejects return"
            )
            return -10, f"sub-lord {sl} → separation house (rejects)"
        if hit_love and hit_sep:
            reasons.append(f"KP sub-lord {sl} split between love and separation axes — mixed signal")
            return 0, f"sub-lord {sl} mixed"
        return 0, f"sub-lord {sl} neutral (house {sl_house})"

    # ── 6. PERSON B SYNASTRY (adjustment ±5) ─────────────────────────────────
    def synastry_adjust():
        adj = 0
        state = []
        asc_A = sidx(kA.get("ascendant","Aries"))
        targets = {5: (asc_A + 4) % 12, 7: (asc_A + 6) % 12, 11: (asc_A + 10) % 12}
        for hlbl, sign_idx_A in targets.items():
            for pB in kB.get("planets", []):
                if sidx(pB["sign"]) == sign_idx_A:
                    if pB["name"] in ("Venus","Jupiter","Moon"):
                        adj += 2
                        state.append(f"{B_name}'s {pB['name']} on A's {hlbl}th")
                        reasons.append(
                            f"{B_name}'s {pB['name']} overlays {A_name}'s {hlbl}th — pulls partner back in"
                        )
                    elif pB["name"] == "Saturn":
                        adj -= 3
                        state.append(f"{B_name}'s Saturn on A's {hlbl}th")
                        reasons.append(
                            f"{B_name}'s Saturn overlays {A_name}'s {hlbl}th — blocks return"
                        )
                    elif pB["name"] == "Rahu":
                        adj += 1
                        state.append(f"{B_name}'s Rahu on A's {hlbl}th")
                        reasons.append(
                            f"{B_name}'s Rahu overlays {A_name}'s {hlbl}th — sudden magnetic pull"
                        )
                    elif pB["name"] == "Ketu":
                        adj -= 2
                        state.append(f"{B_name}'s Ketu on A's {hlbl}th")
                        reasons.append(
                            f"{B_name}'s Ketu overlays {A_name}'s {hlbl}th — detachment from A"
                        )
        adj = max(-5, min(5, adj))
        return adj, (" · ".join(sorted(set(state))) if state else "no significant synastry overlays")

    # ── RUN ──────────────────────────────────────────────────────────────────
    d_pts,  d_txt  = score_dasha()
    t_pts,  t_txt  = score_transit()
    l_pts,  l_txt  = score_love()
    s_pts,  s_txt  = score_separation()
    kp_pts, kp_txt = score_kp()
    syn_pts, syn_txt = synastry_adjust()

    raw = 50 + d_pts + t_pts + l_pts + s_pts + kp_pts + syn_pts
    prob = max(0, min(100, round(raw)))

    if   prob >= 75: chance = "very strong"
    elif prob >= 55: chance = "strong"
    elif prob >= 35: chance = "possible"
    else:            chance = "unlikely"

    # ── Time window ──────────────────────────────────────────────────────────
    # Use active PD planet's nature + Jupiter/Rahu transit presence
    cd = kA.get("currentDasha") or {}
    pd_planet = cd.get("pratyantar")
    t_txt_lower = t_txt.lower()
    jup_active = "jupiter →" in t_txt_lower
    rahu_active= "rahu →" in t_txt_lower
    sat_active = "saturn →" in t_txt_lower
    ketu_active= "ketu →" in t_txt_lower

    if prob < 35:
        time_window = "6–12 months or longer"
    elif rahu_active and prob >= 55:
        time_window = "2–6 weeks (sudden window)"
    elif jup_active and prob >= 55:
        time_window = "1–3 months (favorable window)"
    elif jup_active:
        time_window = "3–6 months"
    elif sat_active or ketu_active:
        time_window = "6–9 months (delay active)"
    elif pd_planet in ("Venus","Moon","Jupiter"):
        time_window = "within 2–4 months"
    else:
        time_window = "3–6 months"

    # ── Reunion type ─────────────────────────────────────────────────────────
    # Long-term: strong 7th support (benefic in 7 / aspect / D9 strong) + prob≥55
    # Temporary: Rahu dominant
    # Unstable: mixed
    d9 = kA.get("divisionalCharts", {}).get("D9") or {}
    d9_7_occ = [q["name"] for q in d9.get("planets", []) if q["house"] == 7]
    d9_support = any(x in ("Jupiter","Venus") for x in d9_7_occ)
    h7_occ = occupants(kA, 7)
    h7_asp = aspects_house(kA, 7)
    strong_7 = ("Jupiter" in h7_occ or "Venus" in h7_occ
                or "Jupiter" in h7_asp) and d9_support

    rahu_dominant = rahu_active or any(planet_linked_to_house(kA, "Rahu", h) for h in (5,7)) or \
                    ("A's 5th" in syn_txt.lower() and "B_name's rahu" in syn_txt.lower())

    if prob >= 55 and strong_7 and not rahu_dominant:
        reunion_type = "long-term"
    elif rahu_dominant and prob >= 40:
        reunion_type = "temporary"
    elif prob < 40:
        reunion_type = "unstable"
    else:
        reunion_type = "unstable"

    # ── Initiator ────────────────────────────────────────────────────────────
    # A active love planets (Venus/Moon in dasha or angular) → A initiates
    # B's Rahu/Mars overlay on A → B initiates
    md = cd.get("maha"); ad = cd.get("antar")
    A_love_active = md in ("Venus","Moon") or ad in ("Venus","Moon")
    B_push = False
    synB = syn_txt.lower()
    if "rahu on a's" in synB or "mars on a's" in synB: B_push = True
    # Check B's Mars too
    marsB = getp(kB, "Mars"); asc_A = sidx(kA.get("ascendant","Aries"))
    if marsB and sidx(marsB["sign"]) in {(asc_A+4)%12,(asc_A+6)%12,(asc_A+10)%12}:
        B_push = True

    if A_love_active and not B_push:
        initiator = "person A"
    elif B_push and not A_love_active:
        initiator = "person B"
    elif A_love_active and B_push:
        initiator = "mutual"
    else:
        initiator = "mutual"

    factors = {
        "dasha":               d_txt,
        "transit":             t_txt,
        "love_houses":         l_txt,
        "separation_houses":   s_txt,
        "kp":                  kp_txt,
    }

    seen = set(); unique_reasons = []
    for r in reasons:
        if r not in seen:
            seen.add(r); unique_reasons.append(r)

    return jsonify({
        "return_probability": prob,
        "return_chance":      chance,
        "time_window":        time_window,
        "reunion_type":       reunion_type,
        "initiator":          initiator,
        "factors":            factors,
        "reasons":            unique_reasons,
        "breakdown": {
            "start":    50,
            "dasha":    d_pts,
            "transit":  t_pts,
            "love":     l_pts,
            "separation": s_pts,
            "kp":       kp_pts,
            "synastry": syn_pts,
        },
    })


@app.route("/api/future-outcome", methods=["POST"])
def future_outcome():
    """
    Future Relationship Outcome — live, real-time personalized engine.
    Person A primary; Person B used for synastry adjustments.
    Produces: future_score, outcome, confidence, current_phase, next_shift,
              timeline_flow (Now→1m, 1-3m, 3-6m), factors{}, reasons[].
    Every output is deterministic from current Dasha + live transits + D1 + D9.
    """
    import swisseph as swe
    from datetime import datetime as _dt, timedelta as _td

    data = request.get_json(force=True, silent=True) or {}
    if "p1" not in data or "p2" not in data:
        return jsonify({"error": "Missing p1 or p2"}), 400

    try:
        kA = calculate_kundli(data["p1"])
        kB = calculate_kundli(data["p2"])
    except Exception as exc:
        return jsonify({"error": f"Kundli calculation failed: {exc}"}), 500

    SIGNS_F = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
               "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    LORDS_F = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
               "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
    EXALT_F = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
    DEBIL_F = {"Sun":6,"Moon":7,"Mars":3,"Mercury":11,"Jupiter":9,"Venus":5,"Saturn":0}
    OWN_F   = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
               "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
    MALEFIC_F = {"Saturn","Mars","Rahu","Ketu"}
    def sidx(s):
        try: return SIGNS_F.index(s)
        except: return 0
    def getp(k, n):
        for p in k.get("planets", []):
            if p["name"] == n: return p
        return None
    def dignity(pl, si):
        if EXALT_F.get(pl) == si: return 2
        if DEBIL_F.get(pl) == si: return -2
        if si in OWN_F.get(pl, []): return 1
        return 0
    def lord_of(k, h):
        asc = sidx(k.get("ascendant","Aries"))
        return LORDS_F[(asc + h - 1) % 12]
    def occupants(k, h):
        return [p["name"] for p in k.get("planets", []) if p["house"] == h]
    def aspects_house(k, h):
        asc = sidx(k.get("ascendant","Aries"))
        tgt = (asc + h - 1) % 12
        hits = []
        for p in k.get("planets", []):
            d = (tgt - sidx(p["sign"]) + 12) % 12
            ok = d == 6
            if p["name"] == "Mars": ok = ok or d in (3,7)
            if p["name"] == "Jupiter": ok = ok or d in (4,8)
            if p["name"] == "Saturn": ok = ok or d in (2,9)
            if p["name"] in ("Rahu","Ketu"): ok = ok or d in (4,8)
            if ok: hits.append(p["name"])
        return hits

    A_name = kA.get("name") or "You"
    B_name = kB.get("name") or "Partner"
    reasons = []

    LOVE_H = {5, 7, 11}
    SEP_H  = {6, 8, 12}

    def planet_touches_house(k, planet, h):
        p = getp(k, planet)
        if not p: return False
        if p["house"] == h: return True
        asc = sidx(k.get("ascendant","Aries"))
        tgt_sign = (asc + h - 1) % 12
        if LORDS_F[tgt_sign] == planet: return True
        if planet in aspects_house(k, h): return True
        disp = LORDS_F[sidx(p["sign"])]
        dp = getp(k, disp)
        if dp and dp["house"] == h: return True
        return False

    # ── LIVE TRANSITS ────────────────────────────────────────────────────────
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    now = _dt.utcnow()
    jd_now = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    def transit_longitudes(jd):
        t = {}
        for pname, pid in [("Jupiter",swe.JUPITER),("Saturn",swe.SATURN),
                           ("Mars",swe.MARS),("Rahu",swe.MEAN_NODE),
                           ("Venus",swe.VENUS),("Sun",swe.SUN),("Mercury",swe.MERCURY)]:
            try:
                r = swe.calc_ut(jd, pid, flags)
                t[pname] = r[0][0] % 360.0
            except Exception: pass
        if "Rahu" in t:
            t["Ketu"] = (t["Rahu"] + 180) % 360
        return t

    t_now = transit_longitudes(jd_now)
    t_30  = transit_longitudes(jd_now + 30)
    t_90  = transit_longitudes(jd_now + 90)
    t_180 = transit_longitudes(jd_now + 180)

    def asp_signs(planet, lon):
        ts = int(lon // 30)
        out = [(ts + 6) % 12]
        if planet == "Jupiter": out += [(ts+4)%12, (ts+8)%12]
        if planet == "Saturn":  out += [(ts+2)%12, (ts+9)%12]
        if planet == "Mars":    out += [(ts+3)%12, (ts+7)%12]
        if planet in ("Rahu","Ketu"): out += [(ts+4)%12, (ts+8)%12]
        return out + [ts]

    asc_A = sidx(kA.get("ascendant","Aries"))
    h5 = (asc_A + 4) % 12
    h7 = (asc_A + 6) % 12
    h11 = (asc_A + 10) % 12
    venus_A = getp(kA, "Venus"); moon_A = getp(kA, "Moon")
    vsA = sidx(venus_A["sign"]) if venus_A else None
    msA = sidx(moon_A["sign"])  if moon_A  else None

    def transit_impact(t_map):
        """Return (score_delta, hits[list of strings])."""
        pts = 0; hits = []
        for tp, lon in t_map.items():
            asp = asp_signs(tp, lon)
            for lbl, tgt in [("5th",h5),("7th",h7),("11th",h11),("Venus",vsA),("Moon",msA)]:
                if tgt is None: continue
                if tgt in asp:
                    if tp == "Jupiter":    pts += 3; hits.append(f"Jupiter→{lbl}")
                    elif tp == "Saturn":   pts -= 2; hits.append(f"Saturn→{lbl}")
                    elif tp == "Rahu":     pts += 1; hits.append(f"Rahu→{lbl}")
                    elif tp == "Ketu":     pts -= 2; hits.append(f"Ketu→{lbl}")
                    elif tp == "Mars":     pts -= 1; hits.append(f"Mars→{lbl}")
                    elif tp == "Venus":    pts += 2; hits.append(f"Venus→{lbl}")
                    elif tp == "Sun":      pts += 0
                    elif tp == "Mercury":  pts += 0
        return pts, sorted(set(hits))

    tr_now_pts,  tr_now_hits  = transit_impact(t_now)
    tr_30_pts,   tr_30_hits   = transit_impact(t_30)
    tr_90_pts,   tr_90_hits   = transit_impact(t_90)
    tr_180_pts,  tr_180_hits  = transit_impact(t_180)

    for h in tr_now_hits[:6]:
        if "Jupiter" in h: reasons.append(f"Right now Jupiter is triggering {A_name}'s {h.split('→')[1]} — growth window open")
        if "Saturn" in h:  reasons.append(f"Saturn is currently pressing {A_name}'s {h.split('→')[1]} — karmic test live")
        if "Rahu" in h:    reasons.append(f"Rahu live on {A_name}'s {h.split('→')[1]} — unpredictable spike")

    # ── DASHA ANALYSIS ───────────────────────────────────────────────────────
    cd = kA.get("currentDasha") or {}
    md, ad, pd = cd.get("maha"), cd.get("antar"), cd.get("pratyantar")

    def dasha_score_for(pl, weight):
        if not pl: return 0, None
        love_link = any(planet_touches_house(kA, pl, h) for h in LOVE_H)
        sep_link  = any(planet_touches_house(kA, pl, h) for h in SEP_H)
        pP = getp(kA, pl)
        dgn = dignity(pl, sidx(pP["sign"])) if pP else 0

        p = 0
        tag = []
        if love_link and not sep_link:
            p += weight; tag.append("activates love axis")
        if sep_link and not love_link:
            p -= weight; tag.append("activates separation axis")
        if love_link and sep_link:
            p += 0; tag.append("mixed love/separation")
        if pl in ("Venus","Moon","Jupiter") and not sep_link:
            p += int(weight * 0.4); tag.append(f"{pl} benefic force")
        if pl in ("Saturn","Ketu") and not love_link:
            p -= int(weight * 0.4); tag.append(f"{pl} detachment")
        if dgn >= 1:
            p += int(weight * 0.3); tag.append("dignified")
        elif dgn <= -2:
            p -= int(weight * 0.3); tag.append("debilitated")
        return p, f"{pl} — " + ", ".join(tag) if tag else f"{pl} — neutral"

    md_p, md_txt = dasha_score_for(md, 12)
    ad_p, ad_txt = dasha_score_for(ad, 8)
    pd_p, pd_txt = dasha_score_for(pd, 5)
    dasha_total = max(-25, min(25, md_p + ad_p + pd_p))
    if md:
        reasons.append(f"Currently in {md} MD — {md_txt.split(' — ',1)[1] if ' — ' in md_txt else 'neutral influence'}")
    if ad:
        reasons.append(f"Antardasha of {ad} shaping the near-term tone — {ad_txt.split(' — ',1)[1] if ' — ' in ad_txt else 'neutral'}")
    if pd:
        reasons.append(f"Active Pratyantar {pd} is the day-to-day driver right now — {pd_txt.split(' — ',1)[1] if ' — ' in pd_txt else 'neutral'}")

    # ── D9 VALIDATION ────────────────────────────────────────────────────────
    d9 = kA.get("divisionalCharts", {}).get("D9") or {}
    d9_7_occ = [q["name"] for q in d9.get("planets", []) if q.get("house") == 7]
    d9_ben = sum(1 for x in d9_7_occ if x in ("Jupiter","Venus","Moon","Mercury"))
    d9_mal = sum(1 for x in d9_7_occ if x in MALEFIC_F)
    d9_pts = max(-15, min(15, 5*d9_ben - 4*d9_mal))
    if d9_ben > 0:
        reasons.append(f"D9 7th house holds {', '.join(x for x in d9_7_occ if x in ('Jupiter','Venus','Moon','Mercury'))} — marriage layer genuinely supportive")
    if d9_mal > 0:
        reasons.append(f"D9 7th carries malefics ({', '.join(x for x in d9_7_occ if x in MALEFIC_F)}) — long-term strain baked in")
    if not d9_7_occ:
        # check D9 7th lord strength as fallback
        d9_asc = sidx((d9.get("ascendant") or kA.get("ascendant","Aries")))
        d9_7_sign = (d9_asc + 6) % 12
        d9_7_lord = LORDS_F[d9_7_sign]
        d9_lp = None
        for q in d9.get("planets", []):
            if q["name"] == d9_7_lord: d9_lp = q; break
        if d9_lp:
            dg = dignity(d9_7_lord, sidx(d9_lp["sign"]))
            if dg >= 1: d9_pts += 4; reasons.append(f"D9 7th lord {d9_7_lord} dignified — marriage potential steady")
            if dg <= -2: d9_pts -= 5; reasons.append(f"D9 7th lord {d9_7_lord} debilitated — marriage layer weak")

    # ── 7th / 5th ANCHOR ─────────────────────────────────────────────────────
    anchor_pts = 0
    anchor_state = []
    for h, w, lbl in [(7, 4, "7th"), (5, 3, "5th"), (11, 2, "11th")]:
        inside = occupants(kA, h)
        bens   = [x for x in inside if x in ("Jupiter","Venus","Moon","Mercury")]
        mals   = [x for x in inside if x in MALEFIC_F]
        asps   = aspects_house(kA, h)
        if bens:
            anchor_pts += w; anchor_state.append(f"{lbl}: {','.join(bens)} inside")
        if "Jupiter" in asps and "Jupiter" not in bens:
            anchor_pts += 1; anchor_state.append(f"{lbl}: Jupiter aspect")
        if mals and "Jupiter" not in asps:
            anchor_pts -= 1; anchor_state.append(f"{lbl}: {','.join(mals)} malefic")
    anchor_pts = max(-10, min(15, anchor_pts))

    # ── SYNASTRY SOFT INFLUENCE (±5) ─────────────────────────────────────────
    syn_pts = 0; syn_state = []
    for hlbl, sign_idx in [(5,h5),(7,h7),(11,h11)]:
        for pB in kB.get("planets", []):
            if sidx(pB["sign"]) == sign_idx:
                if pB["name"] in ("Venus","Jupiter","Moon"):
                    syn_pts += 2; syn_state.append(f"{B_name}'s {pB['name']} on A's {hlbl}th")
                    reasons.append(f"{B_name}'s {pB['name']} overlays {A_name}'s {hlbl}th — steady emotional pull")
                elif pB["name"] == "Saturn":
                    syn_pts -= 3; syn_state.append(f"{B_name}'s Saturn on A's {hlbl}th")
                    reasons.append(f"{B_name}'s Saturn on {A_name}'s {hlbl}th — long shadow, commitment heavy")
                elif pB["name"] == "Rahu":
                    syn_pts += 1; syn_state.append(f"{B_name}'s Rahu on A's {hlbl}th")
                elif pB["name"] == "Ketu":
                    syn_pts -= 2; syn_state.append(f"{B_name}'s Ketu on A's {hlbl}th")
    syn_pts = max(-5, min(5, syn_pts))

    # Clamp transit score
    transit_pts = max(-15, min(15, tr_now_pts))

    # ── FINAL SCORE ──────────────────────────────────────────────────────────
    raw = 50 + dasha_total + transit_pts + d9_pts + anchor_pts + syn_pts
    future_score = max(0, min(100, round(raw)))

    if   future_score >= 75: outcome_chance = "thriving — long-term trajectory"
    elif future_score >= 60: outcome_chance = "growing — steady positive direction"
    elif future_score >= 45: outcome_chance = "mixed — both sides will be tested"
    elif future_score >= 30: outcome_chance = "strained — heavy work required"
    else:                    outcome_chance = "fading — natural separation path"

    # ── CONFIDENCE ───────────────────────────────────────────────────────────
    # High confidence when dasha is clear, transits strong, signals aligned
    signal_strength = abs(dasha_total) + abs(transit_pts) + abs(d9_pts) + abs(anchor_pts)
    # Conflict = contradictory sign between dasha and transit
    conflict = 0
    if dasha_total > 0 and transit_pts < 0: conflict = abs(transit_pts)
    if dasha_total < 0 and transit_pts > 0: conflict = abs(transit_pts)
    confidence = int(max(40, min(95, 55 + signal_strength * 1.2 - conflict * 1.5)))

    # ── CURRENT PHASE (dynamic text) ─────────────────────────────────────────
    jup_live = any(h.startswith("Jupiter") for h in tr_now_hits)
    sat_live = any(h.startswith("Saturn") for h in tr_now_hits)
    rah_live = any(h.startswith("Rahu") for h in tr_now_hits)
    ketu_live= any(h.startswith("Ketu") for h in tr_now_hits)

    if pd in ("Venus","Moon","Jupiter") and jup_live:
        current_phase = "Active reconnection phase"
    elif pd in ("Saturn","Ketu") and sat_live:
        current_phase = "Karmic testing phase"
    elif sat_live and not jup_live:
        current_phase = "Emotional distance / pressure phase"
    elif rah_live and not jup_live:
        current_phase = "Unstable high-intensity phase"
    elif ketu_live and not jup_live:
        current_phase = "Detachment / release phase"
    elif jup_live:
        current_phase = "Healing & expansion phase"
    elif pd in ("Venus","Moon"):
        current_phase = "Tender emotional opening phase"
    elif dasha_total > 5 and transit_pts >= 0:
        current_phase = "Quiet stabilisation phase"
    elif dasha_total < -5:
        current_phase = "Inner friction phase"
    else:
        current_phase = "Neutral waiting phase"

    # ── NEXT SHIFT ───────────────────────────────────────────────────────────
    delta_30  = tr_30_pts  - tr_now_pts
    delta_90  = tr_90_pts  - tr_now_pts
    delta_180 = tr_180_pts - tr_now_pts

    if abs(delta_30) >= 4:
        horizon_days, horizon_delta = 30, delta_30
    elif abs(delta_90) >= 5:
        horizon_days, horizon_delta = 90, delta_90
    elif abs(delta_180) >= 6:
        horizon_days, horizon_delta = 180, delta_180
    else:
        horizon_days, horizon_delta = 90, delta_90

    horizon_label = "~30 days" if horizon_days == 30 else ("~3 months" if horizon_days == 90 else "~6 months")
    if horizon_delta > 2:
        next_shift = f"Positive shift expected in {horizon_label}"
    elif horizon_delta < -2:
        next_shift = f"Pressure phase continues for next {horizon_label}"
    else:
        next_shift = f"Steady current phase through {horizon_label}"

    # ── TIMELINE FLOW ────────────────────────────────────────────────────────
    def trend_for(prev_pts, pts):
        d = pts - prev_pts
        if pts >= 6 or d >= 4: return "up"
        if pts <= -4 or d <= -4: return "down"
        return "mixed"
    def period_reason(t_map, hits):
        ben_hits = [h for h in hits if h.startswith(("Jupiter","Venus"))]
        mal_hits = [h for h in hits if h.startswith(("Saturn","Ketu"))]
        chaos_hits = [h for h in hits if h.startswith(("Rahu","Mars"))]
        parts = []
        if ben_hits:  parts.append(f"{', '.join(ben_hits[:2])} open growth channels")
        if mal_hits:  parts.append(f"{', '.join(mal_hits[:2])} apply pressure")
        if chaos_hits:parts.append(f"{', '.join(chaos_hits[:2])} bring volatility")
        return " · ".join(parts) if parts else "planetary tone neutral"

    now_trend = trend_for(0, tr_now_pts + dasha_total // 2)
    short_trend = trend_for(tr_now_pts, tr_30_pts)
    mid_trend = trend_for(tr_30_pts, tr_90_pts)

    timeline_flow = [
        {
            "period": "Now → 1 month",
            "trend":  now_trend,
            "reason": f"{pd or md or 'Current dasha'} is shaping tone · " + period_reason(t_now, tr_now_hits),
        },
        {
            "period": "1–3 months",
            "trend":  short_trend,
            "reason": period_reason(t_30, tr_30_hits) + f" · delta {('+' if delta_30>=0 else '')}{delta_30}",
        },
        {
            "period": "3–6 months",
            "trend":  mid_trend,
            "reason": period_reason(t_90, tr_90_hits) + f" · delta {('+' if delta_90>=0 else '')}{delta_90}",
        },
    ]

    factors = {
        "current_dasha":    f"MD {md} / AD {ad} / PD {pd} → {'+' if dasha_total>=0 else ''}{dasha_total}",
        "live_transit":     (", ".join(tr_now_hits[:6]) if tr_now_hits else "no strong transits") + f" → {'+' if transit_pts>=0 else ''}{transit_pts}",
        "d9_marriage":      f"D9 7th: {','.join(d9_7_occ) if d9_7_occ else 'empty'} → {'+' if d9_pts>=0 else ''}{d9_pts}",
        "relationship_anchors": (" · ".join(anchor_state) if anchor_state else "7th/5th/11th quiet") + f" → {'+' if anchor_pts>=0 else ''}{anchor_pts}",
        "partner_synastry": (" · ".join(syn_state) if syn_state else "no significant overlays") + f" → {'+' if syn_pts>=0 else ''}{syn_pts}",
    }

    # Dedupe reasons
    seen = set(); uniq = []
    for r in reasons:
        if r not in seen:
            seen.add(r); uniq.append(r)

    return jsonify({
        "future_score":  future_score,
        "outcome":       outcome_chance,
        "confidence":    confidence,
        "current_phase": current_phase,
        "next_shift":    next_shift,
        "timeline_flow": timeline_flow,
        "factors":       factors,
        "reasons":       uniq,
        "breakdown": {
            "start":      50,
            "dasha":      dasha_total,
            "transit":    transit_pts,
            "d9":         d9_pts,
            "anchors":    anchor_pts,
            "synastry":   syn_pts,
        },
        "generated_at":  now.isoformat() + "Z",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
