# Quick Deployment Reference

## Pre-Deployment (Local)
```powershell
# 1. Run pre-deployment check
python scripts/pre_deployment_check.py

# 2. If all checks pass, commit and push
git add .
git commit -m "Add coupon system and invoice improvements"
git push origin main
```

## Production Deployment (SSH to Server)
```bash
# 1. Backup database
cd /home/sobuy/sobuy-app
cp instance/app.db backups/app.db.backup.$(date +%Y%m%d_%H%M%S)

# 2. Pull latest code
git pull origin main

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run database setup
python scripts/production_setup.py

# 6. Restart service
sudo systemctl restart zulkar-sobuy-webapp

# 7. Check status
sudo systemctl status zulkar-sobuy-webapp

# 8. Monitor logs
sudo journalctl -u zulkar-sobuy-webapp -f
```

## Environment Variables to Check (.env on server)
```bash
SECRET_KEY=<long-random-string>
BREVO_API_KEY=<your-brevo-api-key>
MAIL_PROVIDER=brevo
MAIL_DEFAULT_SENDER="SoBuy <noreply@teamsobuy.shop>"
ORDER_NOTIFICATION_RECIPIENTS=admin@teamsobuy.shop
```

## Post-Deployment Verification
1. Visit website - check it loads
2. Register test account - verify OTP email
3. Add product to cart
4. Apply coupon code
5. Complete checkout
6. View invoice from profile
7. Admin: Delete test order

## Troubleshooting Quick Commands
```bash
# View recent errors
sudo journalctl -u zulkar-sobuy-webapp -p err -n 20

# Restart if hung
sudo systemctl restart zulkar-sobuy-webapp

# Check database tables
python -c "from app import create_app, db; from sqlalchemy import inspect; app = create_app(); app.app_context().push(); print(inspect(db.engine).get_table_names())"

# Test Brevo email
python scripts/test_brevo_api.py
```

## Emergency Rollback
```bash
# Stop service
sudo systemctl stop zulkar-sobuy-webapp

# Restore database
cp backups/app.db.backup.YYYYMMDD_HHMMSS instance/app.db

# Revert code (find commit hash first with: git log --oneline)
git reset --hard <previous-commit-hash>

# Start service
sudo systemctl start zulkar-sobuy-webapp
```

## Key File Locations
- Application: `/home/sobuy/sobuy-app`
- Database: `/home/sobuy/sobuy-app/instance/app.db`
- Backups: `/home/sobuy/sobuy-app/backups/`
- Logs: `sudo journalctl -u zulkar-sobuy-webapp`
- Service: `sudo systemctl status zulkar-sobuy-webapp`

## New Features to Configure
1. **Admin Panel → Delivery Fees**: Add delivery options
2. **Admin Panel → bKash Number**: Set active receiving number
3. **Admin Panel → Coupons**: Create discount codes

## Success Indicators
✅ Service status shows "active (running)"
✅ Website loads without errors
✅ OTP emails arrive in inbox
✅ Coupon codes apply successfully
✅ Invoice shows correct formatting
✅ No errors in journalctl logs
