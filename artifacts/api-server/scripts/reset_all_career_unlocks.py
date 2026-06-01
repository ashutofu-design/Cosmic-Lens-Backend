"""Reset career_unlocked for ALL users (testing). Run:
  .\\venv\\Scripts\\python.exe scripts\\reset_all_career_unlocks.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask_app import app
from models import User, db


def main() -> None:
    with app.app_context():
        n = User.query.update(
            {
                User.career_unlocked: False,
                User.career_unlock_order_id: None,
                User.career_unlocked_at: None,
            }
        )
        db.session.commit()
        print(f"OK: reset career_unlocked for {n} user(s)")


if __name__ == "__main__":
    main()
