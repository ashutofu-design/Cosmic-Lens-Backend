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
    email          = db.Column(db.String(255), unique=True, nullable=False)
    password       = db.Column(db.Text, nullable=True)
    google_id      = db.Column(db.String(200), nullable=True)
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
            "email":        self.email,
            "api_key":      self.api_key,
            "is_pro":       self.is_pro and plan_active,
            "plan":         self.plan if plan_active else "free",
            "plan_expiry":  self.plan_expiry.isoformat() if self.plan_expiry else None,
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
        }
