"""
Database connection for Cosmic Lens.

HOW TO SWITCH DATABASES (when moving to VS Code or any server):
  Just set the DATABASE_URL environment variable:
  
  PostgreSQL:  postgresql://user:password@host:5432/dbname
  SQLite:      sqlite:///./cosmic_lens.db
  
  If DATABASE_URL is not set, falls back to SQLite automatically.
"""

import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_database_url():
    url = os.environ.get("DATABASE_URL", "")
    if url:
        # Fix for some providers that return postgres:// instead of postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    # Fallback: SQLite for local development
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return f"sqlite:///{os.path.join(base_dir, 'cosmic_lens.db')}"


def init_db(app):
    url = get_database_url()
    app.config["SQLALCHEMY_DATABASE_URI"] = url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
    db_type = "PostgreSQL" if "postgresql" in url else "SQLite"
    print(f"[DB] Connected to {db_type}")
