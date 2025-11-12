#!/usr/bin/env python3
"""
Pre-Deployment Check Script

Run this before pushing to GitHub to ensure everything is ready for deployment.

Usage:
    python scripts/pre_deployment_check.py
"""
import os
import sys
import re

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def check_env_template():
    """Verify .env.template doesn't contain real credentials."""
    print("\n" + "=" * 70)
    print("Checking .env.template for exposed credentials...")
    print("=" * 70)
    
    env_template_path = os.path.join(os.path.dirname(__file__), '..', '.env.template')
    
    if not os.path.exists(env_template_path):
        print("✗ .env.template not found!")
        return False
    
    with open(env_template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patterns that indicate real credentials
    suspicious_patterns = [
        (r'BREVO_API_KEY=xkeysib-[a-f0-9]{64}', 'Real Brevo API key found'),
        (r'SECRET_KEY=[a-f0-9]{32,}', 'Real SECRET_KEY found (should be placeholder)'),
        (r'MAIL_PASSWORD=(?!change-me|your-|replace-|example)', 'Real email password found'),
        (r'@teamsobuy\.shop.*(?<!example\.com)', 'Real email addresses found'),
    ]
    
    issues = []
    for pattern, message in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(message)
    
    if issues:
        print("\n✗ SECURITY ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n  Please replace real credentials with placeholders!")
        return False
    else:
        print("✓ .env.template looks clean (no real credentials detected)")
        return True


def check_env_in_gitignore():
    """Verify .env is in .gitignore."""
    print("\n" + "=" * 70)
    print("Checking .gitignore...")
    print("=" * 70)
    
    gitignore_path = os.path.join(os.path.dirname(__file__), '..', '.gitignore')
    
    if not os.path.exists(gitignore_path):
        print("✗ .gitignore not found!")
        return False
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_entries = ['.env', '*.db', '__pycache__', '/instance/', 'app/static/uploads/']
    missing = []
    
    for entry in required_entries:
        if entry not in content:
            missing.append(entry)
    
    if missing:
        print(f"\n✗ Missing entries in .gitignore: {missing}")
        return False
    else:
        print("✓ .gitignore has all required entries")
        return True


def check_requirements_txt():
    """Verify requirements.txt exists and has key packages."""
    print("\n" + "=" * 70)
    print("Checking requirements.txt...")
    print("=" * 70)
    
    req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    
    if not os.path.exists(req_path):
        print("✗ requirements.txt not found!")
        return False
    
    with open(req_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_packages = [
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-Login',
        'Flask-WTF',
        'Flask-Migrate',
        'python-dotenv',
        'sib-api-v3-sdk',
        'gunicorn'
    ]
    
    missing = []
    for package in required_packages:
        if package.lower() not in content.lower():
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Potentially missing packages: {missing}")
        print("  (They might be listed with different names)")
    else:
        print("✓ All key packages found in requirements.txt")
    
    return True


def check_migration_scripts():
    """Verify important migration scripts exist."""
    print("\n" + "=" * 70)
    print("Checking migration scripts...")
    print("=" * 70)
    
    scripts_dir = os.path.join(os.path.dirname(__file__), '..')
    
    important_scripts = [
        'scripts/production_setup.py',
        'scripts/create_missing_tables.py',
        'scripts/add_blog_slug.py',
    ]
    
    missing = []
    for script in important_scripts:
        if not os.path.exists(os.path.join(scripts_dir, script)):
            missing.append(script)
    
    if missing:
        print(f"\n⚠ Missing scripts: {missing}")
        return False
    else:
        print("✓ All important migration scripts exist")
        return True


def check_models():
    """Quick sanity check on models.py."""
    print("\n" + "=" * 70)
    print("Checking models.py...")
    print("=" * 70)
    
    try:
        from app.models import (
            User, Product, Order, OrderItem, Coupon, CouponUsage,
            BkashNumber, DeliveryFee, BlogPost
        )
        print("✓ All key models can be imported")
        
        # Check if Coupon model has required fields
        coupon_fields = ['code', 'discount_percent', 'max_discount_amount', 'is_active']
        model_fields = dir(Coupon)
        missing = [f for f in coupon_fields if f not in model_fields]
        
        if missing:
            print(f"⚠ Coupon model missing fields: {missing}")
        else:
            print("✓ Coupon model has required fields")
        
        return True
    except ImportError as e:
        print(f"✗ Error importing models: {e}")
        return False


def check_database_file():
    """Check if local database exists."""
    print("\n" + "=" * 70)
    print("Checking local database...")
    print("=" * 70)
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'app.db')
    
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"✓ Database exists (size: {size_mb:.2f} MB)")
        print(f"  Location: {db_path}")
        return True
    else:
        print("⚠ No local database found")
        print("  This is OK if you're setting up for the first time")
        return True


def main():
    """Run all pre-deployment checks."""
    print("\n" + "=" * 70)
    print("SoBuy E-commerce - Pre-Deployment Check")
    print("=" * 70)
    
    checks = [
        ("Environment Template", check_env_template),
        (".gitignore Configuration", check_env_in_gitignore),
        ("Requirements File", check_requirements_txt),
        ("Migration Scripts", check_migration_scripts),
        ("Models Structure", check_models),
        ("Local Database", check_database_file),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Error running {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} checks passed")
    print("=" * 70)
    
    if passed == total:
        print("\n✓ All checks passed! Ready for deployment.")
        print("\nNext steps:")
        print("  1. git add .")
        print("  2. git commit -m 'Your commit message'")
        print("  3. git push origin main")
        print("  4. Follow DEPLOYMENT.md for production deployment")
        return True
    else:
        print("\n✗ Some checks failed. Please fix the issues above before deploying.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
