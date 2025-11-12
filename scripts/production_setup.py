#!/usr/bin/env python3
"""
Production Setup Script for SoBuy E-commerce

This script ensures all necessary database tables exist on the production server.
Run this after deploying new code to production.

Usage:
    python scripts/production_setup.py

What this script does:
1. Creates any missing database tables (Coupon, CouponUsage, BkashNumber, DeliveryFee, etc.)
2. Verifies all expected tables exist
3. Reports any issues

This is SAFE to run multiple times - it only creates missing tables.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import inspect, text


def verify_tables():
    """Verify all expected tables exist in the database."""
    expected_tables = {
        'user', 'product', 'order', 'order_item', 'product_visit',
        'otp_token', 'home_slider_image', 'blog_post', 'blog_comment',
        'blog_like', 'blog_visit', 'bkash_number', 'delivery_fee',
        'newsletter_subscriber', 'coupon', 'coupon_usage'
    }
    
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        
        missing_tables = expected_tables - existing_tables
        extra_tables = existing_tables - expected_tables
        
        print("=" * 70)
        print("DATABASE TABLE VERIFICATION")
        print("=" * 70)
        
        if missing_tables:
            print(f"\n⚠ MISSING TABLES ({len(missing_tables)}):")
            for table in sorted(missing_tables):
                print(f"  - {table}")
            return False
        else:
            print("\n✓ All expected tables exist!")
        
        print(f"\n✓ Total tables in database: {len(existing_tables)}")
        for table in sorted(existing_tables):
            print(f"  - {table}")
        
        if extra_tables:
            print(f"\nℹ Extra tables (not in expected list): {', '.join(sorted(extra_tables))}")
        
        print("\n" + "=" * 70)
        return True


def create_missing_tables():
    """Create any missing tables."""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 70)
        print("CREATING MISSING TABLES")
        print("=" * 70)
        
        try:
            print("\nRunning db.create_all()...")
            db.create_all()
            print("✓ db.create_all() completed successfully")
            return True
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return False


def check_coupon_columns():
    """Verify Coupon and CouponUsage tables have correct columns."""
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("\n" + "=" * 70)
        print("VERIFYING COUPON SYSTEM TABLES")
        print("=" * 70)
        
        # Check Coupon table
        if 'coupon' in inspector.get_table_names():
            coupon_columns = {col['name'] for col in inspector.get_columns('coupon')}
            expected_coupon_cols = {
                'id', 'code', 'discount_percent', 'max_discount_amount',
                'max_uses_per_user', 'max_total_uses', 'total_uses',
                'is_active', 'expiry_date', 'created_at'
            }
            missing = expected_coupon_cols - coupon_columns
            if missing:
                print(f"\n⚠ Coupon table missing columns: {missing}")
                return False
            else:
                print("\n✓ Coupon table has all required columns")
        
        # Check CouponUsage table
        if 'coupon_usage' in inspector.get_table_names():
            usage_columns = {col['name'] for col in inspector.get_columns('coupon_usage')}
            expected_usage_cols = {'id', 'coupon_id', 'user_id', 'order_id', 'used_at'}
            missing = expected_usage_cols - usage_columns
            if missing:
                print(f"⚠ CouponUsage table missing columns: {missing}")
                return False
            else:
                print("✓ CouponUsage table has all required columns")
        
        # Check Order table for coupon fields
        if 'order' in inspector.get_table_names():
            order_columns = {col['name'] for col in inspector.get_columns('order')}
            coupon_fields = {'coupon_id', 'discount_amount'}
            missing = coupon_fields - order_columns
            if missing:
                print(f"⚠ Order table missing coupon columns: {missing}")
                return False
            else:
                print("✓ Order table has coupon discount columns")
        
        print("\n" + "=" * 70)
        return True


def main():
    """Main setup routine."""
    print("\n" + "=" * 70)
    print("SoBuy E-commerce Production Setup")
    print("=" * 70)
    
    # Step 1: Create missing tables
    if not create_missing_tables():
        print("\n✗ Failed to create tables. Please check the error above.")
        return False
    
    # Step 2: Verify all tables exist
    if not verify_tables():
        print("\n✗ Some tables are still missing after db.create_all()")
        print("   You may need to run Flask-Migrate: flask db upgrade")
        return False
    
    # Step 3: Verify coupon system
    if not check_coupon_columns():
        print("\n⚠ Coupon system tables need migration")
        print("   This is expected if you haven't run migrations yet.")
    
    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Verify your .env file has correct settings")
    print("2. Test the application: python run.py")
    print("3. Create admin user if needed")
    print("4. Configure Brevo API key for email")
    print("5. Add delivery fee options via admin panel")
    print("6. Add active bKash number via admin panel")
    print("\n" + "=" * 70)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
