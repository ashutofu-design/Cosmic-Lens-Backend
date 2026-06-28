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

from sqlalchemy import text
from urllib.parse import urlparse



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





def _sqlite_has_column(conn, table: str, column: str) -> bool:

    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()

    return any(row[1] == column for row in rows)





def _sqlite_add_column(conn, table: str, column: str, ddl: str) -> bool:

    if _sqlite_has_column(conn, table, column):

        return False

    conn.execute(text(ddl))

    print(f"[DB] SQLite added {table}.{column}", flush=True)

    return True





def run_schema_migrations() -> None:

    """Idempotent column migrations (safe to call on every startup or after a schema error)."""

    url = get_database_url()

    try:

        with db.engine.connect() as conn:

            if "postgresql" in url:

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR(64) UNIQUE"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20) UNIQUE"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS country_code VARCHAR(4) DEFAULT '91'"

                ))

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

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "

                    "astrovastu_room_credits INTEGER NOT NULL DEFAULT 0"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "

                    "astrovastu_floor_scan_wallet TEXT NOT NULL DEFAULT '{}'"

                ))

                conn.execute(text(

                    "ALTER TABLE business_vastu_logs ADD COLUMN IF NOT EXISTS report_json TEXT"

                ))

                conn.execute(text(

                    "ALTER TABLE astrovastu_pro_logs ADD COLUMN IF NOT EXISTS report_json TEXT"

                ))

                conn.execute(text(

                    "ALTER TABLE astrovastu_pro_logs ADD COLUMN IF NOT EXISTS property_name VARCHAR(120)"

                ))

                conn.execute(text(

                    "CREATE INDEX IF NOT EXISTS ix_avpl_property_name ON astrovastu_pro_logs (property_name)"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(4)"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS career_unlocked BOOLEAN NOT NULL DEFAULT FALSE"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS career_unlock_order_id VARCHAR(200)"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS career_unlocked_at TIMESTAMP"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS personal_name_locked BOOLEAN NOT NULL DEFAULT FALSE"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS personal_phone_locked BOOLEAN NOT NULL DEFAULT FALSE"

                ))

                conn.execute(text(

                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS cosmo_user_id VARCHAR(16)"

                ))

                try:

                    conn.execute(text(

                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_cosmo_user_id ON users (cosmo_user_id)"

                    ))

                except Exception:

                    pass

                for _uq_sql in (
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS answer_text TEXT",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS answer_source VARCHAR(40)",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS llm_model VARCHAR(80)",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS completion_tokens INTEGER",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS total_tokens INTEGER",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS cached_tokens INTEGER",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS cost_usd DOUBLE PRECISION",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS cost_inr DOUBLE PRECISION",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS engine_tag VARCHAR(40)",
                    "ALTER TABLE user_questions ADD COLUMN IF NOT EXISTS llm_context_json TEXT",
                ):
                    try:
                        conn.execute(text(_uq_sql))
                    except Exception:
                        pass

                for _tbl_sql in (
                    """
                    CREATE TABLE IF NOT EXISTS question_user_signals (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        question_id VARCHAR(36),
                        signals_json TEXT NOT NULL DEFAULT '{}',
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS user_ask_profiles (
                        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                        profile_json TEXT NOT NULL DEFAULT '{}',
                        question_count INTEGER NOT NULL DEFAULT 0,
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS ix_q_signals_user_created ON question_user_signals (user_id, created_at)",
                ):
                    try:
                        conn.execute(text(_tbl_sql))
                    except Exception:
                        pass

                if os.environ.get("COSMIC_WIPE_USERS") == "1":

                    try:

                        conn.execute(text(

                            "TRUNCATE TABLE profiles, kundlis, otp_requests, users RESTART IDENTITY CASCADE"

                        ))

                        print("[DB] WIPED users/profiles/kundlis/otp_requests (COSMIC_WIPE_USERS=1)")

                    except Exception as e:

                        print(f"[DB] Wipe skipped (table may not exist yet): {e}")

            else:

                _sqlite_add_column(

                    conn, "users", "api_key",

                    "ALTER TABLE users ADD COLUMN api_key VARCHAR(64)",

                )

                _sqlite_add_column(

                    conn, "users", "phone",

                    "ALTER TABLE users ADD COLUMN phone VARCHAR(20)",

                )

                _sqlite_add_column(

                    conn, "users", "country_code",

                    "ALTER TABLE users ADD COLUMN country_code VARCHAR(4) DEFAULT '91'",

                )

                _sqlite_add_column(

                    conn, "profiles", "birth_key",

                    "ALTER TABLE profiles ADD COLUMN birth_key VARCHAR(120)",

                )

                _sqlite_add_column(

                    conn, "profiles", "deleted_at",

                    "ALTER TABLE profiles ADD COLUMN deleted_at TIMESTAMP",

                )

                _sqlite_add_column(

                    conn, "business_vastu_logs", "report_json",

                    "ALTER TABLE business_vastu_logs ADD COLUMN report_json TEXT",

                )

                _sqlite_add_column(

                    conn, "astrovastu_pro_logs", "report_json",

                    "ALTER TABLE astrovastu_pro_logs ADD COLUMN report_json TEXT",

                )

                _sqlite_add_column(

                    conn, "astrovastu_pro_logs", "property_name",

                    "ALTER TABLE astrovastu_pro_logs ADD COLUMN property_name VARCHAR(120)",

                )

                _sqlite_add_column(

                    conn, "users", "preferred_language",

                    "ALTER TABLE users ADD COLUMN preferred_language VARCHAR(4)",

                )

                _sqlite_add_column(

                    conn, "users", "astrovastu_room_credits",

                    "ALTER TABLE users ADD COLUMN astrovastu_room_credits INTEGER DEFAULT 0",

                )

                _sqlite_add_column(

                    conn, "users", "astrovastu_floor_scan_wallet",

                    "ALTER TABLE users ADD COLUMN astrovastu_floor_scan_wallet TEXT DEFAULT '{}'",

                )

                _sqlite_add_column(

                    conn, "users", "career_unlocked",

                    "ALTER TABLE users ADD COLUMN career_unlocked BOOLEAN DEFAULT 0",

                )

                _sqlite_add_column(

                    conn, "users", "career_unlock_order_id",

                    "ALTER TABLE users ADD COLUMN career_unlock_order_id VARCHAR(200)",

                )

                _sqlite_add_column(

                    conn, "users", "career_unlocked_at",

                    "ALTER TABLE users ADD COLUMN career_unlocked_at TIMESTAMP",

                )

                _sqlite_add_column(

                    conn, "users", "personal_name_locked",

                    "ALTER TABLE users ADD COLUMN personal_name_locked BOOLEAN DEFAULT 0",

                )

                _sqlite_add_column(

                    conn, "users", "personal_phone_locked",

                    "ALTER TABLE users ADD COLUMN personal_phone_locked BOOLEAN DEFAULT 0",

                )

                _sqlite_add_column(

                    conn, "users", "cosmo_user_id",

                    "ALTER TABLE users ADD COLUMN cosmo_user_id VARCHAR(16)",

                )

                for _tbl, _col, _sql in (
                    ("user_questions", "answer_text", "ALTER TABLE user_questions ADD COLUMN answer_text TEXT"),
                    ("user_questions", "answer_source", "ALTER TABLE user_questions ADD COLUMN answer_source VARCHAR(40)"),
                    ("user_questions", "llm_model", "ALTER TABLE user_questions ADD COLUMN llm_model VARCHAR(80)"),
                    ("user_questions", "prompt_tokens", "ALTER TABLE user_questions ADD COLUMN prompt_tokens INTEGER"),
                    ("user_questions", "completion_tokens", "ALTER TABLE user_questions ADD COLUMN completion_tokens INTEGER"),
                    ("user_questions", "total_tokens", "ALTER TABLE user_questions ADD COLUMN total_tokens INTEGER"),
                    ("user_questions", "cached_tokens", "ALTER TABLE user_questions ADD COLUMN cached_tokens INTEGER"),
                    ("user_questions", "cost_usd", "ALTER TABLE user_questions ADD COLUMN cost_usd REAL"),
                    ("user_questions", "cost_inr", "ALTER TABLE user_questions ADD COLUMN cost_inr REAL"),
                    ("user_questions", "engine_tag", "ALTER TABLE user_questions ADD COLUMN engine_tag VARCHAR(40)"),
                    ("user_questions", "llm_context_json", "ALTER TABLE user_questions ADD COLUMN llm_context_json TEXT"),
                ):
                    _sqlite_add_column(conn, _tbl, _col, _sql)

            conn.commit()

    except Exception as e:

        print(f"[DB] Migration note: {e}", flush=True)


def ensure_user_auth_columns() -> None:
    """Best-effort User columns for login routes (each ALTER committed separately)."""
    url = get_database_url()
    if "postgresql" in url:
        statements = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS cosmo_user_id VARCHAR(16)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS personal_name_locked BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS personal_phone_locked BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS career_unlocked BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(4)",
        ]
    else:
        statements = []

    for sql in statements:
        try:
            with db.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
        except Exception as e:
            print(f"[DB] ensure_user_auth_columns: {e}", flush=True)


def init_db(app):

    url = get_database_url()

    app.config["SQLALCHEMY_DATABASE_URI"] = url

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():

        db.create_all()

        run_schema_migrations()
        try:
            from cosmo_user_id import backfill_missing_cosmo_user_ids

            n = backfill_missing_cosmo_user_ids()
            if n:
                print(f"[DB] Backfilled {n} cosmo_user_id(s)", flush=True)
        except Exception as bf_exc:
            print(f"[DB] cosmo_user_id backfill note: {bf_exc}", flush=True)

    db_type = "PostgreSQL" if "postgresql" in url else "SQLite"
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "local"
        port = parsed.port or (5432 if "postgresql" in url else None)
        dbname = (parsed.path or "").lstrip("/") or ""
        safe = f"{parsed.scheme}://{host}{(':'+str(port)) if port else ''}/{dbname}" if parsed.scheme else db_type
    except Exception:
        safe = db_type

    # Connection smoke-check + useful startup logging (never prints password).
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        print(f"[DB] Connected db={db_type} url={safe}", flush=True)
    except Exception as e:
        print(f"[DB] Connect FAILED db={db_type} url={safe} err={type(e).__name__}: {e}", flush=True)
        # Don't crash on startup — existing flows may still run in degraded mode.


