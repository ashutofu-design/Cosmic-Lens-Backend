"""
Database models for Cosmic Lens.
Uses SQLAlchemy — works with PostgreSQL (production) and SQLite (local dev).
To switch databases: just change DATABASE_URL environment variable.
"""

from database import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(200), nullable=False, default="")
    # Phone-OTP is the canonical identity. Email kept nullable for legacy/demo only.
    phone          = db.Column(db.String(20), unique=True, nullable=True, index=True)   # E.164 e.g. +919876543210
    country_code   = db.Column(db.String(4),  nullable=True, default="91")
    email          = db.Column(db.String(255), unique=True, nullable=True)             # legacy/demo only
    password       = db.Column(db.Text, nullable=True)                                  # legacy
    google_id      = db.Column(db.String(200), nullable=True)                          # legacy
    api_key        = db.Column(db.String(64), unique=True, nullable=True)
    is_pro         = db.Column(db.Boolean, default=False, nullable=False)
    is_admin       = db.Column(db.Boolean, default=False, nullable=False)

    # ── Subscription ──────────────────────────────────────────────────────────
    plan           = db.Column(db.String(20), default="free", nullable=False)   # free / trial / basic / pro / elite
    plan_expiry    = db.Column(db.DateTime, nullable=True)                       # when paid plan expires
    plan_order_id  = db.Column(db.String(200), nullable=True)                   # last Cashfree order ID

    # ── Free Trial ────────────────────────────────────────────────────────────
    trial_started_at = db.Column(db.DateTime, nullable=True)                    # when 7-day trial began
    trial_used       = db.Column(db.Boolean, default=False, nullable=False)     # one-time eligibility flag

    # ── Daily AI question quota ───────────────────────────────────────────────
    daily_questions_used = db.Column(db.Integer, default=0, nullable=False)
    daily_questions_date = db.Column(db.String(10), default="", nullable=False) # YYYY-MM-DD

    # ── Preferred response language (overrides per-question detection) ────────
    # Allowed: "en" | "hi" | "hn" | NULL (auto-detect from each question)
    preferred_language = db.Column(db.String(4), nullable=True)

    # ── Daily Kundli generation quota ─────────────────────────────────────────
    daily_kundlis_used = db.Column(db.Integer, default=0, nullable=False)
    daily_kundlis_date = db.Column(db.String(10), default="", nullable=False)   # YYYY-MM-DD

    # ── Monthly AstroVastu PRO quota ──────────────────────────────────────────
    monthly_astrovastu_pro_used  = db.Column(db.Integer, default=0, nullable=False)
    monthly_astrovastu_pro_month = db.Column(db.String(7),  default="", nullable=False)  # YYYY-MM

    # ── AstroVastu one-time room credits (Phase 2 unlock model) ──────────────
    # PRO Home scan credits. ₹199 grants +1, ₹499 bundle grants +3. Decrements on each
    # AstroVastu PRO scan. (Basic AstroVastu is free — does not consume credits.)
    # Column name kept for backward-compat; semantic is now "PRO Home scan credits".
    # BASIC scan only when user has neither Pro plan nor unlocked property.
    astrovastu_room_credits = db.Column(db.Integer, default=0, nullable=False)

    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    last_active    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kundli = db.relationship("Kundli", backref="user", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        plan_active = (
            self.plan != "free"
            and self.plan_expiry is not None
            and self.plan_expiry > datetime.utcnow()
        )
        return {
            "id":           self.id,
            "name":         self.name,
            "phone":        self.phone or "",
            "country_code": self.country_code or "",
            "email":        self.email or "",   # kept for backward compat; empty for new OTP users
            "api_key":      self.api_key,
            "is_pro":       self.is_pro and plan_active,
            "plan":         self.plan if plan_active else "free",
            "plan_expiry":  self.plan_expiry.isoformat() if self.plan_expiry else None,
            "preferred_language": self.preferred_language,   # null → auto-detect
            "created_at":   self.created_at.isoformat() if self.created_at else None,
        }

    def to_admin_dict(self):
        return {
            "id":           self.id,
            "name":         self.name,
            "email":        self.email,
            "is_pro":       self.is_pro,
            "is_admin":     self.is_admin,
            "plan":         self.plan,
            "plan_expiry":  self.plan_expiry.isoformat() if self.plan_expiry else None,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "last_active":  self.last_active.isoformat() if self.last_active else None,
            "has_kundli":   self.kundli is not None,
        }


class Kundli(db.Model):
    __tablename__ = "kundlis"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    name       = db.Column(db.String(200))
    dob        = db.Column(db.String(50))   # "DD/MM/YYYY"
    tob        = db.Column(db.String(50))   # "HH:MM AM/PM"
    pob        = db.Column(db.String(300))  # place of birth
    lat        = db.Column(db.Float)
    lon        = db.Column(db.Float)
    tz         = db.Column(db.Float)
    chart_data = db.Column(db.Text)         # JSON string of full kundli calculation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":      self.id,
            "user_id": self.user_id,
            "name":    self.name,
            "dob":     self.dob,
            "tob":     self.tob,
            "pob":     self.pob,
            "lat":     self.lat,
            "lon":     self.lon,
            "tz":      self.tz,
        }


class Profile(db.Model):
    """Multi-profile cloud storage — each user can have many saved kundlis (self + family)."""
    __tablename__ = "profiles"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id     = db.Column(db.String(64), nullable=False, index=True)   # client-generated id (stable across sync)
    name          = db.Column(db.String(200), nullable=False, default="")
    gender        = db.Column(db.String(20), default="")
    relation      = db.Column(db.String(50), default="")                   # Self / Wife / Father / ...
    is_primary    = db.Column(db.Boolean, default=False, nullable=False)
    birth_data    = db.Column(db.Text)                                     # JSON
    chart_data    = db.Column(db.Text)                                     # JSON (kundli)
    # Dedup key: sha-ish key from (dob, tob, lat≈, lon≈) — used by /api/kundli
    # to return a cached chart when the same user re-requests identical birth data
    # WITHOUT consuming a daily generation slot.
    birth_key     = db.Column(db.String(120), nullable=True, index=True)
    # Soft-delete: when set, profile is in "Recently Deleted" (24-hr restore window).
    # NULL = active. Set to a timestamp to soft-delete.
    deleted_at    = db.Column(db.DateTime, nullable=True, index=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "client_id", name="uq_user_client_profile"),)

    def to_dict(self):
        import json as _json
        def _load(s):
            if not s: return None
            try: return _json.loads(s)
            except Exception: return None
        return {
            "id":          self.client_id,
            "name":        self.name,
            "gender":      self.gender or "",
            "relation":    self.relation or "",
            "isPrimary":   self.is_primary,
            "birthData":   _load(self.birth_data),
            "kundli":      _load(self.chart_data),
            "updatedAt":   self.updated_at.isoformat() if self.updated_at else None,
            "deletedAt":   self.deleted_at.isoformat() if self.deleted_at else None,
        }


class OtpRequest(db.Model):
    """
    One row per OTP send. Used to enforce cooldowns, retry limits, and verification.
    Verified rows are kept for audit. A nightly purge can drop rows > 30 days old
    (not implemented yet — table stays small at expected volumes).
    """
    __tablename__ = "otp_requests"

    id          = db.Column(db.Integer, primary_key=True)
    phone       = db.Column(db.String(20), nullable=False, index=True)        # canonical +ccNNNNN
    otp_hash    = db.Column(db.Text, nullable=False)
    expires_at  = db.Column(db.DateTime, nullable=False, index=True)
    attempts    = db.Column(db.Integer, default=0, nullable=False)
    verified    = db.Column(db.Boolean, default=False, nullable=False)
    ip          = db.Column(db.String(64), default="", nullable=False)        # for audit only
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class AstroVastuBasicLog(db.Model):
    """
    One row per BASIC AstroVastu check. Used for analytics + future ML training.
    Kept lean — full kundli is not duplicated (already in users.kundli).
    """
    __tablename__ = "astrovastu_basic_logs"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                            nullable=True, index=True)        # nullable for anon preview
    room_type   = db.Column(db.String(40), nullable=False)
    direction   = db.Column(db.String(20), nullable=False)
    verdict     = db.Column(db.String(40), nullable=False)
    severity    = db.Column(db.String(20), nullable=False, default="minor")
    multiplier  = db.Column(db.Float, nullable=False, default=1.0)
    lagna       = db.Column(db.String(20), nullable=True)
    mahadasha   = db.Column(db.String(20), nullable=True)
    sade_sati   = db.Column(db.Boolean, default=False, nullable=False)
    plan        = db.Column(db.String(20), default="free", nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        db.Index("ix_avbl_user_created", "user_id", "created_at"),
    )


class AstroVastuPropertyUnlock(db.Model):
    """
    Phase-2 lifetime per-property unlock for ₹2,999 Full-Home tier (and future
    Business tiers ₹999/₹1,499/₹2,999). One row per (user, property_name).
    Once unlocked, that property name has UNLIMITED PRO scans forever — no
    monthly quota, no room credits consumed.
    """
    __tablename__ = "astrovastu_property_unlocks"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    property_name = db.Column(db.String(120), nullable=False)        # user-chosen label e.g. "Mumbai Flat"
    tier          = db.Column(db.String(40),  nullable=False, default="full_home_2999")
    order_id      = db.Column(db.String(200), nullable=True)         # Cashfree order id (Phase 3)
    amount_paid   = db.Column(db.Integer,     nullable=False, default=0)   # in INR rupees
    unlocked_at   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "property_name", name="uq_avpu_user_property"),
        db.Index("ix_avpu_user_unlocked", "user_id", "unlocked_at"),
    )


class AstroVastuPurchase(db.Model):
    """
    Phase-2 transaction log for every AstroVastu one-time payment intent.
    Status lifecycle: created → paid / failed / expired. The Cashfree webhook
    (Phase 3) flips status & triggers credit/unlock grant idempotently.
    """
    __tablename__ = "astrovastu_purchases"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    sku           = db.Column(db.String(40),  nullable=False)        # 1room_199 / bundle_499 / full_home_2999 / shop_999 / office_1499 / factory_2999
    amount        = db.Column(db.Integer,     nullable=False)        # INR rupees
    property_name = db.Column(db.String(120), nullable=True)         # required for unlock-tier SKUs
    order_id      = db.Column(db.String(200), nullable=True, unique=True)
    status        = db.Column(db.String(20),  nullable=False, default="created")  # created/paid/failed/expired
    granted       = db.Column(db.Boolean,     nullable=False, default=False)      # idempotent grant flag
    created_at    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    paid_at       = db.Column(db.DateTime, nullable=True)


class BusinessVastuLog(db.Model):
    """Phase-4 — one row per Business Vastu deep-scan (analytics + audit)."""
    __tablename__ = "business_vastu_logs"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    business_type  = db.Column(db.String(20),  nullable=False)        # shop / office / factory
    property_name  = db.Column(db.String(120), nullable=True)
    rooms_count    = db.Column(db.Integer, nullable=False, default=0)
    overall_score  = db.Column(db.Integer, nullable=False, default=0)  # 0-100
    avoid_count    = db.Column(db.Integer, nullable=False, default=0)
    adjust_count   = db.Column(db.Integer, nullable=False, default=0)
    ideal_count    = db.Column(db.Integer, nullable=False, default=0)
    partner_count  = db.Column(db.Integer, nullable=False, default=0)
    has_muhurat    = db.Column(db.Boolean, nullable=False, default=False)
    lagna          = db.Column(db.String(20), nullable=True)
    mahadasha      = db.Column(db.String(20), nullable=True)
    floor_plan     = db.Column(db.Text, nullable=False, default="[]")  # JSON
    via            = db.Column(db.String(20), nullable=False, default="property_unlock")
    plan           = db.Column(db.String(20), default="free", nullable=False)
    report_json    = db.Column(db.Text, nullable=True)                    # full bilingual report JSON for PDF render
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        db.Index("ix_bvl_user_created", "user_id", "created_at"),
    )


class AstroVastuProLog(db.Model):
    """
    One row per PRO AstroVastu deep-scan. Stores the input floor plan + summary
    metrics (full per-room JSON kept lean). Used for analytics & ML.
    """
    __tablename__ = "astrovastu_pro_logs"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    rooms_count  = db.Column(db.Integer, nullable=False, default=0)
    overall_score= db.Column(db.Integer, nullable=False, default=0)   # 0-100
    avoid_count  = db.Column(db.Integer, nullable=False, default=0)
    adjust_count = db.Column(db.Integer, nullable=False, default=0)
    ideal_count  = db.Column(db.Integer, nullable=False, default=0)
    lagna        = db.Column(db.String(20), nullable=True)
    mahadasha    = db.Column(db.String(20), nullable=True)
    sade_sati    = db.Column(db.Boolean, default=False, nullable=False)
    floor_plan   = db.Column(db.Text, nullable=False, default="[]")    # JSON of input rooms
    plan         = db.Column(db.String(20), default="free", nullable=False)
    property_name= db.Column(db.String(120), nullable=True, index=True)   # owner-supplied label, e.g. "Mumbai Flat"
    report_json  = db.Column(db.Text, nullable=True)                     # full bilingual report JSON for PDF render
    created_at   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        db.Index("ix_avpl_user_created", "user_id", "created_at"),
    )


def compute_birth_key(birth_data) -> str:
    """
    Deterministic dedup key for a kundli computation. Two birth-data inputs
    producing the same key are considered identical for caching purposes.
    Uses date + time + ~11m geographic precision. Name excluded (math doesn't
    depend on name).
    """
    if not birth_data or not isinstance(birth_data, dict):
        return ""
    try:
        d   = int(birth_data.get("day", 0))
        m   = int(birth_data.get("month", 0))
        y   = int(birth_data.get("year", 0))
        h   = int(birth_data.get("hour", 0))
        mn  = int(birth_data.get("minute", 0))
        ampm = str(birth_data.get("ampm", "")).upper().strip()
        lat = float(birth_data.get("lat", 0))
        lon = float(birth_data.get("lon", 0))
        return f"{y:04d}-{m:02d}-{d:02d}|{h:02d}:{mn:02d}{ampm}|{lat:.4f},{lon:.4f}"
    except (TypeError, ValueError):
        return ""
