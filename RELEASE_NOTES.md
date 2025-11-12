# Release Notes - Version 2.0

## Release Date: November 12, 2025

## Major Features Added

### 1. Coupon Discount System
- **Coupon Management**: Admins can create and manage discount coupons
- **Coupon Application**: Customers can apply coupon codes during checkout
- **Features**:
  - Percentage-based discounts with optional maximum cap
  - Usage limits per user and total
  - Expiry date support
  - Usage tracking and history
  - Validation (expiry, usage limits, active status)

### 2. Enhanced Invoice Display
- **Payment Method**: Shows "COD" instead of "cash_on_delivery"
- **bKash Information**:
  - Receiving Number: Shows admin's active bKash number
  - Sending Number: Shows customer's bKash number
  - Transaction ID: Shows bKash transaction ID
- **Professional Layout**: Improved invoice formatting

### 3. Profile Order Management
- **Invoice Access**: "View Invoice" button for each order in profile
- **Order History**: Better organized order display

### 4. Admin Order Management
- **Delete Orders**: Admins can now delete orders with confirmation
- **Cascade Delete**: Automatically removes associated order items

### 5. Checkout Improvements
- **Discount Display**: Shows detailed breakdown:
  - Subtotal (cart items)
  - Discount (with coupon code, if applied)
  - Delivery Fee (with method name)
  - Total (final amount)
- **Consistent Calculations**: Same logic across cart, delivery selection, and checkout

## Database Changes

### New Tables
- `coupon`: Stores discount coupon configurations
- `coupon_usage`: Tracks coupon usage by users

### Updated Tables
- `order`:
  - Added `coupon_id` (foreign key to coupon table)
  - Added `discount_amount` (actual discount applied)

## Files Added/Modified

### New Files
- `scripts/production_setup.py`: Production database setup script
- `scripts/pre_deployment_check.py`: Pre-deployment validation
- `DEPLOYMENT.md`: Comprehensive deployment guide

### Modified Files
- `app/models.py`: Added Coupon and CouponUsage models
- `app/routes.py`:
  - Added coupon application logic in cart
  - Added coupon removal endpoint
  - Added discount calculation in checkout
  - Added order delete endpoint
  - Updated invoice route to pass active bKash number
- `app/templates/cart.html`: Added coupon input and discount display
- `app/templates/checkout.html`: Added order summary with discount breakdown
- `app/templates/invoice.html`: Improved payment info display
- `app/templates/profile.html`: Added invoice link buttons
- `app/templates/admin_orders.html`: Added delete button
- `.env.template`: Cleaned up (removed exposed credentials)

## Bug Fixes
- Fixed: Cart delivery selection now includes coupon discount in calculations
- Fixed: Checkout page properly calculates total with discount
- Fixed: Invoice displays human-readable payment method
- Fixed: bKash receiving number shows admin's number, not customer's

## Security Improvements
- Removed exposed credentials from .env.template
- Added pre-deployment security checks
- Proper sanitization of admin flash messages

## Deployment Requirements

### Prerequisites
- Python 3.8+
- SQLite or PostgreSQL database
- Brevo API account (for emails)
- Active bKash number configured

### Migration Steps
1. Pull latest code from GitHub
2. Run `python scripts/production_setup.py`
3. Verify all tables created
4. Restart application service

## Configuration Needed

### Admin Panel Setup
1. **Delivery Fees**: Configure delivery options and costs
2. **bKash Number**: Set active receiving number
3. **Coupons**: Create discount coupons as needed

### Environment Variables
- `BREVO_API_KEY`: Your Brevo API key
- `SECRET_KEY`: Random secret string
- `MAIL_DEFAULT_SENDER`: Default sender email
- `ORDER_NOTIFICATION_RECIPIENTS`: Admin email addresses

## Testing Checklist

### Customer Flow
- [ ] Register account with OTP
- [ ] Browse and add products to cart
- [ ] Apply valid coupon code
- [ ] Try invalid/expired coupon
- [ ] Select delivery option
- [ ] Complete checkout with bKash
- [ ] View invoice from profile
- [ ] Verify discount shown correctly

### Admin Flow
- [ ] Login to admin panel
- [ ] Create new coupon
- [ ] Edit/deactivate coupon
- [ ] View order list
- [ ] Update order status
- [ ] Delete test order
- [ ] Configure delivery fees
- [ ] Set active bKash number

## Known Issues
None

## Rollback Plan
If issues occur, restore database from backup:
```bash
cp backups/app.db.backup.TIMESTAMP instance/app.db
sudo systemctl restart zulkar-sobuy-webapp
```

## Support
- Documentation: See DEPLOYMENT.md
- Pre-deployment check: `python scripts/pre_deployment_check.py`
- Production setup: `python scripts/production_setup.py`

---

## Next Steps After Deployment
1. Create initial coupons for promotions
2. Configure delivery fees for your regions
3. Test complete customer journey
4. Monitor application logs
5. Verify email delivery working

## Contributors
- Zulkar Nain

## Version History
- v2.0 (Nov 12, 2025): Coupon system, invoice improvements, order management
- v1.0 (Previous): Initial e-commerce platform
