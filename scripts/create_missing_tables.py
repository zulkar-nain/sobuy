"""
Script: create_missing_tables.py

Creates any missing SQLAlchemy tables by calling `db.create_all()` inside the app context.

Usage:
    python scripts/create_missing_tables.py

This is safe to run against your development SQLite DB; it will only create missing tables and will not drop or alter existing data.
"""
import os
import sys

# Make sure project root is on sys.path so 'app' package can be imported when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import inspect


def main():
    app = create_app()
    with app.app_context():
        print('Running db.create_all() to ensure missing tables exist...')
        db.create_all()
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f'Tables now present in the database ({len(tables)}):')
        for t in tables:
            print(' -', t)


if __name__ == '__main__':
    main()
