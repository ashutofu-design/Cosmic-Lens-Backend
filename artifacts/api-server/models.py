"""
Database models for Cosmic Lens.
Uses SQLAlchemy — works with PostgreSQL (production) and SQLite (local dev).
To switch databases: just change DATABASE_URL environment variable.
"""

from database import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False, default="")
    email      = db.Column(db.String(255), unique=True, nullable=False)
    password   = db.Column(db.Text, nullable=True)
    google_id  = db.Column(db.String(200), nullable=True)
    is_pro     = db.Column(db.Boolean, default=False, nullable=False)
    is_admin   = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kundli     = db.relationship("Kundli", backref="user", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "is_pro":     self.is_pro,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_admin_dict(self):
        return {
            "id":          self.id,
            "name":        self.name,
            "email":       self.email,
            "is_pro":      self.is_pro,
            "is_admin":    self.is_admin,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "has_kundli":  self.kundli is not None,
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
