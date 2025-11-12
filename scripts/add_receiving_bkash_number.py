#!/usr/bin/env python3
"""
Migration script to add receiving_bkash_number column to Order table.
This column stores the admin's active bKash receiving number at the time of order placement.

Run this script once to update your existing database:
    python scripts/add_receiving_bkash_number.py
"""
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

def add_receiving_bkash_number_column():
    """Add receiving_bkash_number column to Order table if it doesn't exist."""
    app = create_app()
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("PRAGMA table_info(order)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'receiving_bkash_number' in columns:
                print("✓ Column 'receiving_bkash_number' already exists in Order table.")
                return True
            
            # Add the column
            print("Adding 'receiving_bkash_number' column to Order table...")
            db.session.execute(text(
                "ALTER TABLE 'order' ADD COLUMN receiving_bkash_number VARCHAR(50)"
            ))
            db.session.commit()
            print("✓ Successfully added 'receiving_bkash_number' column to Order table.")
            return True
            
        except Exception as e:
            print(f"✗ Error adding column: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = add_receiving_bkash_number_column()
    sys.exit(0 if success else 1)
