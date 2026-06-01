"""Reset career unlock for a user (testing). Run:
  .\\venv\\Scripts\\python.exe scripts\\reset_career_unlock.py
  .\\venv\\Scripts\\python.exe scripts\\reset_career_unlock.py 1
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask_app import app
from models import User, db


def main() -> None:
    uid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    with app.app_context():
        user = User.query.get(uid)
        if not user:
            print(f"User {uid} not found")
            return
        user.career_unlocked = False
        user.career_unlock_order_id = None
        user.career_unlocked_at = None
        db.session.commit()
        print(f"OK: career_unlocked reset for user_id={uid}")


if __name__ == "__main__":
    main()
