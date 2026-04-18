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
        # Safe migration: add api_key column if it doesn't exist
        try:
            import os
            from sqlalchemy import text
            with db.engine.connect() as conn:
                if "postgresql" in url:
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR(64) UNIQUE"
                    ))
                    # Phone-OTP auth columns
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20) UNIQUE"
                    ))
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS country_code VARCHAR(4) DEFAULT '91'"
                    ))
                    # Drop NOT NULL on email (phone is the new canonical identity).
                    # IF EXISTS guard handles re-runs.
                    try:
                        conn.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))
                    except Exception:
                        pass
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_users_phone ON users(phone)"
                    ))
                    conn.execute(text(
                        "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS birth_key VARCHAR(120)"
                    ))
                    conn.execute(text(
                        "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP"
                    ))
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_profiles_birth_key ON profiles(birth_key)"
                    ))
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_profiles_deleted_at ON profiles(deleted_at)"
                    ))
                    # Phase-2 AstroVastu unlock model — one-time room credits column.
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                        "astrovastu_room_credits INTEGER NOT NULL DEFAULT 0"
                    ))
                    # One-time pre-launch wipe of legacy email/google users.
                    # GUARDED behind COSMIC_WIPE_USERS env var so it never runs by accident.
                    if os.environ.get("COSMIC_WIPE_USERS") == "1":
                        try:
                            conn.execute(text("TRUNCATE TABLE profiles, kundlis, otp_requests, users RESTART IDENTITY CASCADE"))
                            print("[DB] WIPED users/profiles/kundlis/otp_requests (COSMIC_WIPE_USERS=1)")
                        except Exception as e:
                            print(f"[DB] Wipe skipped (table may not exist yet): {e}")
                else:
                    # SQLite doesn't support IF NOT EXISTS on ALTER TABLE.
                    # Note: SQLite cannot drop NOT NULL via ALTER, but the dev DB will
                    # be recreated on first run for a clean local schema if missing.
                    for stmt in (
                        "ALTER TABLE users ADD COLUMN api_key VARCHAR(64)",
                        "ALTER TABLE users ADD COLUMN phone VARCHAR(20)",
                        "ALTER TABLE users ADD COLUMN country_code VARCHAR(4) DEFAULT '91'",
                        "ALTER TABLE profiles ADD COLUMN birth_key VARCHAR(120)",
                        "ALTER TABLE profiles ADD COLUMN deleted_at TIMESTAMP",
                    ):
                        try:
                            conn.execute(text(stmt))
                        except Exception:
                            pass
                conn.commit()
        except Exception as e:
            print(f"[DB] Migration note: {e}")
    db_type = "PostgreSQL" if "postgresql" in url else "SQLite"
    print(f"[DB] Connected to {db_type}")
