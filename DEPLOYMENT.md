# SoBuy E-commerce Deployment Guide

## Pre-Deployment Checklist

### 1. Clean Up Local Environment
```bash
# Remove any temporary files, __pycache__, etc.
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 2. Verify .env.template is Clean
- ✅ .env.template should NOT contain real credentials
- ✅ Only placeholder values like "your-api-key-here"
- ✅ Never commit the actual .env file

### 3. Test Locally
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the application
python run.py

# Test key features:
# - User registration with OTP
# - Add product to cart
# - Apply coupon code
# - Select delivery option
# - Complete checkout
# - View invoice from profile
# - Admin: Create/delete orders
```

## GitHub Deployment

### Step 1: Commit and Push Changes
```powershell
# Check what files will be committed
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add coupon discount system, invoice improvements, and order management

- Add coupon application and validation system
- Fix invoice to show COD label and bKash receiving number
- Add order deletion for admins
- Add invoice link to user profile
- Update checkout to calculate and display coupon discounts
- Clean up .env.template (remove exposed credentials)"

# Push to GitHub
git push origin main
```

### Step 2: Verify GitHub Push
- Go to https://github.com/zulkar-nain/sobuy
- Check that all files are updated
- Verify .env.template doesn't have real credentials

## DigitalOcean Production Deployment

### Step 1: SSH to Production Server
```bash
ssh your-username@your-server-ip
# Or use PuTTY/other SSH client on Windows
```

### Step 2: Navigate to Application Directory
```bash
cd /home/sobuy/sobuy-app
```

### Step 3: Backup Current Database
```bash
# Create backup directory if it doesn't exist
mkdir -p backups

# Backup current database with timestamp
cp instance/app.db backups/app.db.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup was created
ls -lh backups/
```

### Step 4: Pull Latest Code from GitHub
```bash
# Fetch latest changes
git fetch origin main

# Show what will change
git log HEAD..origin/main --oneline

# Pull the changes
git pull origin main
```

### Step 5: Update Environment Configuration
```bash
# Edit .env file (use nano or vim)
nano .env

# Ensure these are set correctly:
# - SECRET_KEY (long random string)
# - BREVO_API_KEY (your actual Brevo API key)
# - MAIL_DEFAULT_SENDER (noreply@teamsobuy.shop)
# - MAIL_PROVIDER=brevo
# - ORDER_NOTIFICATION_RECIPIENTS (your admin emails)

# Save and exit (Ctrl+X, Y, Enter in nano)
```

### Step 6: Activate Virtual Environment
```bash
# Activate the virtual environment
source venv/bin/activate
# Or if using a different path:
# source .venv/bin/activate
```

### Step 7: Install/Update Dependencies
```bash
# Update pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 8: Run Database Setup Script
```bash
# This creates any missing tables (Coupon, CouponUsage, etc.)
python scripts/production_setup.py

# The script will:
# ✓ Create missing tables
# ✓ Verify all tables exist
# ✓ Check coupon system columns
```

### Step 9: Run Blog Slug Migration (if needed)
```bash
# Add slugs to existing blog posts
python scripts/add_blog_slug.py
```

### Step 10: Restart the Application
```bash
# Restart the systemd service
sudo systemctl restart zulkar-sobuy-webapp

# Check service status
sudo systemctl status zulkar-sobuy-webapp

# If there are errors, check logs
sudo journalctl -u zulkar-sobuy-webapp -n 50
```

### Step 11: Verify Deployment
```bash
# Check if app is running
curl -I http://localhost:8000

# You should see HTTP 200 OK or 302 redirect
```

## Post-Deployment Testing

### Test on Production Website

1. **Test User Registration**
   - Register new account
   - Verify OTP email arrives
   - Check Brevo logs if emails not received

2. **Test Shopping Flow**
   - Browse products
   - Add to cart
   - Apply coupon code
   - Select delivery option
   - Complete checkout with bKash
   - Verify invoice shows correct details

3. **Test Invoice Display**
   - Check payment method shows "COD" not "cash_on_delivery"
   - For bKash orders, verify receiving number is admin's number
   - Verify sending number is customer's input
   - Check invoice accessible from profile page

4. **Test Admin Functions**
   - Login as admin
   - View orders list
   - Delete test order
   - Update order status
   - Create/manage coupons

## Troubleshooting

### Issue: Email Not Sending
```bash
# Test Brevo API key
python scripts/test_brevo_api.py

# Check if sender email is verified in Brevo dashboard
# https://app.brevo.com/settings/senders
```

### Issue: Missing Tables Error
```bash
# Run setup script again
python scripts/production_setup.py

# Or manually create tables
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Issue: Coupon System Not Working
```bash
# Verify tables exist
python -c "from app import create_app, db; from sqlalchemy import inspect; app = create_app(); app.app_context().push(); print(inspect(db.engine).get_table_names())"

# Check for 'coupon' and 'coupon_usage' in the output
```

### Issue: Application Won't Start
```bash
# Check error logs
sudo journalctl -u zulkar-sobuy-webapp -n 100 --no-pager

# Check if port is in use
sudo lsof -i :8000

# Restart service
sudo systemctl restart zulkar-sobuy-webapp
```

### Issue: Static Files Not Loading
```bash
# Check static files directory
ls -la app/static/

# Ensure uploads directory exists
mkdir -p app/static/uploads
chmod 755 app/static/uploads
```

## Important Production Configuration

### Admin Panel Access
1. Create admin user (if not exists):
```bash
python -c "from app import create_app, db; from app.models import User; app = create_app(); app.app_context().push(); u = User.query.filter_by(username='admin').first(); u.is_admin = True if u else None; db.session.commit() if u else print('User not found')"
```

### Configure Delivery Fees
1. Login as admin
2. Go to Admin Dashboard → Delivery Fees
3. Add delivery options (e.g., "Inside Dhaka", "Outside Dhaka")

### Configure Active bKash Number
1. Login as admin
2. Go to Admin Dashboard
3. Add bKash receiving number and set as active

### Create Discount Coupons
1. Login as admin
2. Go to Coupons section
3. Create coupons with:
   - Code (e.g., "SAVE10")
   - Discount percentage
   - Maximum discount cap
   - Usage limits
   - Expiry date

## Rollback Plan (If Something Goes Wrong)

```bash
# Stop the application
sudo systemctl stop zulkar-sobuy-webapp

# Restore database from backup
cp backups/app.db.backup.YYYYMMDD_HHMMSS instance/app.db

# Revert to previous git commit
git log --oneline  # Find the commit hash to revert to
git reset --hard <previous-commit-hash>

# Restart application
sudo systemctl start zulkar-sobuy-webapp
```

## Monitoring After Deployment

```bash
# Watch application logs in real-time
sudo journalctl -u zulkar-sobuy-webapp -f

# Check for errors
sudo journalctl -u zulkar-sobuy-webapp -p err -n 50

# Monitor system resources
htop

# Check disk space
df -h
```

## Success Criteria

- ✅ Application starts without errors
- ✅ User registration with OTP works
- ✅ Coupon codes can be applied
- ✅ Checkout calculates discount correctly
- ✅ Invoice displays properly formatted
- ✅ Admin can manage orders
- ✅ No error logs in journalctl

## Support Contacts

- **Application Logs**: `sudo journalctl -u zulkar-sobuy-webapp`
- **Brevo Dashboard**: https://app.brevo.com
- **GitHub Repository**: https://github.com/zulkar-nain/sobuy

---

**Last Updated**: November 12, 2025
**Version**: 2.0 (Coupon System Release)
