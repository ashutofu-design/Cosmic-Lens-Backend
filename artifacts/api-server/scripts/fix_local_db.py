#!/usr/bin/env python3

"""One-shot local DB repair — adds missing columns (e.g. astrovastu_floor_scan_wallet)."""

import os

import sys



sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



from flask import Flask

from database import db, get_database_url, init_db, run_schema_migrations

from sqlalchemy import inspect





def main():

    app = Flask(__name__)

    init_db(app)

    with app.app_context():

        run_schema_migrations()

        cols = [c["name"] for c in inspect(db.engine).get_columns("users")]

        ok = "astrovastu_floor_scan_wallet" in cols

        print(f"DB: {get_database_url()}")

        print(f"users.astrovastu_floor_scan_wallet present: {ok}")

        if not ok:

            sys.exit(1)





if __name__ == "__main__":

    main()

