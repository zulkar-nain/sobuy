import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session, abort, Response
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session, jsonify
import csv
import io
from app import db
from app.models import (
    Product, User, Order, ProductVisit, HomeSliderImage, OrderItem,
    OTPToken, BlogPost, BlogComment, BlogLike, BlogVisit, BkashNumber
)
from app.models import DeliveryFee
from app.utils import render_markdown_safe, safe_admin_flash, generate_slug
from app.forms import (
    LoginForm, ProductUploadForm, PaymentForm, RegistrationForm, CheckoutForm,
    ProfileForm, ChangePasswordForm, OTPForm, BlogPostForm, CommentForm
)
from app.email import send_email
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import OperationalError, IntegrityError
from werkzeug.utils import secure_filename
from flask import make_response

main = Blueprint('main', __name__)


@main.route('/subscribe', methods=['POST'])
def subscribe_newsletter():
    # simple newsletter subscription endpoint used by footer form
    email = (request.form.get('email') or '').strip().lower()
    # basic validation
    if not email or '@' not in email:
        flash('Please provide a valid email address to subscribe.')
        return redirect(request.referrer or url_for('main.index'))
    try:
        # avoid importing at module import time (models live at top but safe)
        from app.models import NewsletterSubscriber
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing:
            flash('You are already subscribed to our newsletter.')
            return redirect(request.referrer or url_for('main.index'))
        sub = NewsletterSubscriber(email=email)
        db.session.add(sub)
        try:
            db.session.commit()
            flash('Thank you — your email has been added to our newsletter list.')
        except IntegrityError:
            # race or duplicate insertion -> already subscribed
            db.session.rollback()
            flash('You are already subscribed to our newsletter.')
            return redirect(request.referrer or url_for('main.index'))
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Failed to subscribe email to newsletter')
        flash('Failed to subscribe. Please try again later.')
    return redirect(request.referrer or url_for('main.index'))


@main.route('/')
def index():
    # only show active products to customers
    products = Product.query.filter_by(status='active').all()
    # load active slider images for the hero section (ordered by position)
    try:
        slider_images = HomeSliderImage.query.filter_by(active=True).order_by(HomeSliderImage.position.asc()).all()
    except Exception:
        slider_images = []
    # recent blog posts for homepage (show latest 3 published)
    try:
        recent_posts = BlogPost.query.filter_by(status='published').order_by(BlogPost.created_at.desc()).limit(3).all()
    except Exception:
        recent_posts = []
    return render_template('index.html', products=products, slider_images=slider_images, recent_posts=recent_posts)


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # create OTP token and email it
        email = form.email.data.strip().lower()
        username = form.username.data.strip()
        password_hash = generate_password_hash(form.password.data)

        # generate 6-digit OTP
        import random
        otp_code = f"{random.randint(100000, 999999)}"
        expires = datetime.utcnow() + timedelta(minutes=15)

        token = OTPToken(email=email, username=username, password_hash=password_hash, otp_code=otp_code, expires_at=expires)
        db.session.add(token)
        db.session.commit()

        # send OTP email
        subject = 'Your SoBuy signup code'
        text = render_template('email/otp.txt', otp=otp_code, expires=expires, username=username)
        html = render_template('email/otp.html', otp=otp_code, expires=expires, username=username)
        recipients = email
        send_email(subject, recipients, text, html)

        # save pending email in session so we can prefill verify form
        session['pending_signup_email'] = email
        flash('An OTP has been sent to your email. Please enter it to complete signup.')
        return redirect(url_for('main.verify_signup'))

    return render_template('register.html', title='Register', form=form)


@main.route('/verify-signup', methods=['GET', 'POST'])
def verify_signup():
    # verify OTP for signup
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = OTPForm()
    pending_email = session.get('pending_signup_email')
    if not pending_email:
        flash('No pending signup found. Please register first.')
        return redirect(url_for('main.register'))

    if form.validate_on_submit():
        entered = form.otp.data.strip()
        # find latest unused token for email
        token = OTPToken.query.filter_by(email=pending_email, otp_code=entered, used=False).order_by(OTPToken.created_at.desc()).first()
        if not token:
            flash('Invalid or expired code. Please try again or request a new signup code.')
            return redirect(url_for('main.verify_signup'))
        if token.expires_at < datetime.utcnow():
            flash('OTP has expired. Please register again to receive a new code.')
            return redirect(url_for('main.register'))

        # create user
        new_user = User(username=token.username, email=token.email)
        new_user.password_hash = token.password_hash
        db.session.add(new_user)
        token.used = True
        db.session.commit()

        login_user(new_user)
        session.pop('pending_signup_email', None)
        flash('Signup complete — you are now logged in.')
        return redirect(url_for('main.index'))

    return render_template('verify_signup.html', form=form, email=pending_email)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            # prevent banned users from logging in
            try:
                if getattr(user, 'is_banned', False):
                    return redirect(url_for('main.banned'))
            except Exception:
                pass
            login_user(user)
            flash('You have been logged in successfully.')
            if user.is_admin:
                return redirect(url_for('main.admin_dashboard'))
            return redirect(url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    # aggregate stats
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(role='customer').count()

    # recent orders (include username)
    recent_raw = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_orders = []
    for o in recent_raw:
        user = User.query.get(o.user_id)
        recent_orders.append({
            'id': o.id,
            'username': user.username if user else 'Unknown',
            'user_email': user.email if user else None,
            'amount': o.total_amount,
            'payment_method': o.payment_method,
            'trx_id': getattr(o, 'trx_id', None),
            'bkash_number': getattr(o, 'bkash_number', None),
            'status': o.status,
            'created_at': o.created_at
        })

    # top products by visits
    top_visits = ProductVisit.query.order_by(ProductVisit.visit_count.desc()).limit(5).all()
    top_products = []
    for pv in top_visits:
        p = Product.query.get(pv.product_id)
        if p:
            # count how many distinct orders included this product
            try:
                order_count = db.session.query(func.count(func.distinct(OrderItem.order_id))).filter(OrderItem.product_id == p.id).scalar() or 0
            except Exception:
                order_count = 0
            top_products.append({'product': p, 'visits': pv.visit_count, 'order_count': int(order_count)})

    # additional admin insights
    try:
        revenue_total = db.session.query(func.coalesce(func.sum(Order.total_amount), 0.0)).scalar() or 0.0
        revenue_last_30 = db.session.query(func.coalesce(func.sum(Order.total_amount), 0.0)).filter(Order.created_at >= (datetime.utcnow() - timedelta(days=30))).scalar() or 0.0
        orders_by_status_raw = db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
        orders_by_status = {status: count for status, count in orders_by_status_raw}
    except Exception:
        revenue_total = 0.0
        revenue_last_30 = 0.0
        orders_by_status = {}

    recent_signups = User.query.order_by(User.created_at.desc()).limit(10).all()

    # load homepage slider images for management UI
    try:
        slider_images = HomeSliderImage.query.order_by(HomeSliderImage.position.asc()).all()
    except Exception:
        slider_images = []
    # current active bKash receiving number
    try:
        active_bkash = BkashNumber.query.filter_by(active=True).first()
    except Exception:
        active_bkash = None

    return render_template('admin_dashboard.html',
                           total_products=total_products,
                           total_orders=total_orders,
                           total_customers=total_customers,
                           recent_orders=recent_orders,
                           top_products=top_products,
                           slider_images=slider_images,
                           active_bkash=active_bkash,
                           revenue_total=revenue_total,
                           revenue_last_30=revenue_last_30,
                           orders_by_status=orders_by_status,
                           recent_signups=recent_signups)


@main.route('/admin/delivery-fees', methods=['GET', 'POST'])
@login_required
def admin_delivery_fees():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))

    # ensure default fee rows exist (keys and labels)
    defaults = [
        ('express_inside', 'Express delivery (Inside Dhaka, within 24 hours)'),
        ('regular_inside', 'Regular Delivery (Inside Dhaka)'),
        ('regular_outside', 'Regular Delivery (Outside Dhaka)')
    ]
    try:
        for key, label in defaults:
            if not DeliveryFee.query.filter_by(key=key).first():
                db.session.add(DeliveryFee(key=key, label=label, amount=0.0))
        db.session.commit()
    except Exception:
        db.session.rollback()

    fees = DeliveryFee.query.order_by(DeliveryFee.id.asc()).all()

    if request.method == 'POST':
        try:
            for f in fees:
                val = request.form.get(f'amount_{f.key}')
                if val is not None:
                    try:
                        f.amount = float(val)
                    except Exception:
                        f.amount = 0.0
            db.session.commit()
            flash('Delivery fees updated.')
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Failed to update delivery fees')
            flash('Failed to save delivery fees.')
        return redirect(url_for('main.admin_delivery_fees'))

    return render_template('admin_delivery_fees.html', fees=fees)



@main.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    try:
        users = User.query.order_by(User.created_at.desc()).all()
    except OperationalError:
        # If the column/table is missing (schema drift), attempt to create missing tables and retry once
        try:
            db.create_all()
            users = User.query.order_by(User.created_at.desc()).all()
        except Exception:
            current_app.logger.exception('Failed to load users or create tables')
            users = []
    return render_template('admin_users.html', users=users)


@main.route('/admin/user/<int:user_id>/ban', methods=['POST'])
@login_required
def admin_ban_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    # prevent banning admins
    if user.is_admin:
        flash('Cannot ban an admin user.')
        return redirect(url_for('main.admin_users'))
    user.is_banned = True
    db.session.commit()
    safe_admin_flash(f'User {user.username} has been banned.', display=f'User {user.username} has been banned.')
    return redirect(url_for('main.admin_users'))


@main.route('/admin/user/<int:user_id>/unban', methods=['POST'])
@login_required
def admin_unban_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    safe_admin_flash(f'User {user.username} has been unbanned.', display=f'User {user.username} has been unbanned.')
    return redirect(url_for('main.admin_users'))


@main.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    # prevent deleting admins
    if user.is_admin:
        flash('Cannot delete an admin user.')
        return redirect(url_for('main.admin_users'))
    db.session.delete(user)
    db.session.commit()
    safe_admin_flash(f'User {user.username} has been deleted.', display=f'User {user.username} has been deleted.')
    return redirect(url_for('main.admin_users'))



@main.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    except Exception:
        orders = []
    # import User locally to avoid circular top-level hits in some environments
    from app.models import User
    return render_template('admin_orders.html', orders=orders, User=User)


@main.route('/admin/subscribers')
@login_required
def admin_subscribers():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    try:
        from app.models import NewsletterSubscriber
        subs = NewsletterSubscriber.query.order_by(NewsletterSubscriber.created_at.desc()).all()
    except Exception:
        current_app.logger.exception('Failed to load subscribers')
        subs = []
    return render_template('admin_subscribers.html', subs=subs)


@main.route('/admin/subscribers/export')
@login_required
def admin_subscribers_export():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    try:
        from app.models import NewsletterSubscriber
        subs = NewsletterSubscriber.query.order_by(NewsletterSubscriber.created_at.desc()).all()

        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['id', 'email', 'created_at'])
        for s in subs:
            created = s.created_at.isoformat() if getattr(s, 'created_at', None) else ''
            writer.writerow([s.id, s.email, created])

        output = si.getvalue()
        si.close()
        return Response(output, mimetype='text/csv', headers={
            'Content-Disposition': 'attachment; filename=newsletter_subscribers.csv'
        })
    except Exception:
        current_app.logger.exception('Failed to export subscribers')
        flash('Failed to export subscribers.')
        return redirect(url_for('main.admin_subscribers'))


# ====================== COUPON MANAGEMENT ======================

@main.route('/admin/coupons')
@login_required
def admin_coupons():
    """Admin page to manage discount coupons."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    try:
        from app.models import Coupon
        coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    except Exception:
        current_app.logger.exception('Failed to load coupons')
        coupons = []
    return render_template('admin_coupons.html', coupons=coupons)


@main.route('/admin/coupons/create', methods=['GET', 'POST'])
@login_required
def admin_coupon_create():
    """Create a new coupon."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    from app.forms import CouponForm
    from app.models import Coupon
    
    form = CouponForm()
    if form.validate_on_submit():
        try:
            # Check if code already exists
            existing = Coupon.query.filter_by(code=form.code.data.strip().upper()).first()
            if existing:
                flash('A coupon with this code already exists.', 'danger')
                return render_template('admin_coupon_form.html', form=form, is_edit=False)
            
            coupon = Coupon(
                code=form.code.data.strip().upper(),
                discount_percent=form.discount_percent.data,
                max_discount_amount=form.max_discount_amount.data,
                max_uses_per_user=form.max_uses_per_user.data,
                max_total_uses=form.max_total_uses.data,
                expiry_date=form.expiry_date.data,
                is_active=form.is_active.data
            )
            db.session.add(coupon)
            db.session.commit()
            safe_admin_flash(f'Coupon created: {coupon.code}', 'Coupon created successfully.')
            return redirect(url_for('main.admin_coupons'))
        except Exception:
            current_app.logger.exception('Failed to create coupon')
            db.session.rollback()
            flash('Failed to create coupon.', 'danger')
    
    return render_template('admin_coupon_form.html', form=form, is_edit=False)


@main.route('/admin/coupons/<int:coupon_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_coupon_edit(coupon_id):
    """Edit an existing coupon."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    from app.forms import CouponForm
    from app.models import Coupon
    
    coupon = Coupon.query.get_or_404(coupon_id)
    form = CouponForm(obj=coupon)
    
    if form.validate_on_submit():
        try:
            # Check if code change conflicts with existing
            if form.code.data.strip().upper() != coupon.code:
                existing = Coupon.query.filter_by(code=form.code.data.strip().upper()).first()
                if existing:
                    flash('A coupon with this code already exists.', 'danger')
                    return render_template('admin_coupon_form.html', form=form, is_edit=True, coupon=coupon)
            
            coupon.code = form.code.data.strip().upper()
            coupon.discount_percent = form.discount_percent.data
            coupon.max_discount_amount = form.max_discount_amount.data
            coupon.max_uses_per_user = form.max_uses_per_user.data
            coupon.max_total_uses = form.max_total_uses.data
            coupon.expiry_date = form.expiry_date.data
            coupon.is_active = form.is_active.data
            
            db.session.commit()
            safe_admin_flash(f'Coupon updated: {coupon.code}', 'Coupon updated successfully.')
            return redirect(url_for('main.admin_coupons'))
        except Exception:
            current_app.logger.exception('Failed to update coupon')
            db.session.rollback()
            flash('Failed to update coupon.', 'danger')
    
    return render_template('admin_coupon_form.html', form=form, is_edit=True, coupon=coupon)


@main.route('/admin/coupons/<int:coupon_id>/delete', methods=['POST'])
@login_required
def admin_coupon_delete(coupon_id):
    """Delete a coupon."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    try:
        from app.models import Coupon
        coupon = Coupon.query.get_or_404(coupon_id)
        code = coupon.code
        db.session.delete(coupon)
        db.session.commit()
        safe_admin_flash(f'Coupon deleted: {code}', 'Coupon deleted successfully.')
    except Exception:
        current_app.logger.exception('Failed to delete coupon')
        db.session.rollback()
        flash('Failed to delete coupon.', 'danger')
    
    return redirect(url_for('main.admin_coupons'))


@main.route('/admin/coupons/<int:coupon_id>/toggle', methods=['POST'])
@login_required
def admin_coupon_toggle(coupon_id):
    """Toggle coupon active status."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    try:
        from app.models import Coupon
        coupon = Coupon.query.get_or_404(coupon_id)
        coupon.is_active = not coupon.is_active
        db.session.commit()
        status = 'activated' if coupon.is_active else 'deactivated'
        safe_admin_flash(f'Coupon {status}: {coupon.code}', f'Coupon {status}.')
    except Exception:
        current_app.logger.exception('Failed to toggle coupon status')
        db.session.rollback()
        flash('Failed to toggle coupon status.', 'danger')
    
    return redirect(url_for('main.admin_coupons'))



def sitemap():
    """Generate a sitemap including product detail and a few static pages."""
    try:
        pages = []
        # static pages
        pages.append(url_for('main.index', _external=True))
        pages.append(url_for('main.blog_list', _external=True))
        pages.append(url_for('main.cart', _external=True))
        pages.append(url_for('main.login', _external=True))

        # products
        from app.models import Product
        for p in Product.query.filter_by(status='active').all():
            try:
                pages.append(url_for('main.product_detail', product_id=p.id, _external=True))
            except Exception:
                continue

        # blog posts
        for post in BlogPost.query.filter_by(status='published').all():
            try:
                pages.append(url_for('main.blog_detail', slug=post.slug, _external=True))
            except Exception:
                continue

        sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for page in pages:
            sitemap_xml.append('<url>')
            sitemap_xml.append(f'<loc>{page}</loc>')
            sitemap_xml.append('</url>')
        sitemap_xml.append('</urlset>')
        response = make_response('\n'.join(sitemap_xml))
        response.headers['Content-Type'] = 'application/xml'
        return response
    except Exception:
        current_app.logger.exception('Failed to generate sitemap')
        return redirect(url_for('main.index'))


@main.route('/robots.txt')
def robots_txt():
    lines = [
        "User-agent: *",
        "Disallow: /admin",
        "Disallow: /instance",
        "Allow: /",
        f"Sitemap: {url_for('main.sitemap', _external=True)}"
    ]
    response = make_response('\n'.join(lines))
    response.headers['Content-Type'] = 'text/plain'
    return response



@main.route('/banned')
def banned():
    return render_template('banned.html')



@main.route('/admin/order/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.admin_dashboard'))

    new_status = (request.form.get('status') or '').strip()
    allowed = ['Pending', 'Processing', 'Shipped', 'Completed', 'Cancelled']
    if new_status not in allowed:
        flash('Invalid status selected.')
        return redirect(url_for('main.admin_dashboard'))

    order = Order.query.get_or_404(order_id)
    old_status = order.status
    if old_status == new_status:
        flash('Status unchanged.')
        return redirect(url_for('main.admin_dashboard'))

    order.status = new_status
    db.session.commit()
    # Record full detail in server logs and flash an admin-only message
    safe_admin_flash(f'Order #{order.id} status updated from {old_status} to {new_status}.',
                     display=f'Order #{order.id} status updated to {new_status}.')

    # send emails on specific transitions
    try:
        user = User.query.get(order.user_id)
        if new_status == 'Shipped' and user and getattr(user, 'email', None):
            text = render_template('email/order_shipped.txt', order=order, user=user)
            html = render_template('email/order_shipped.html', order=order, user=user)
            send_email(f'Your SoBuy order #{order.id} is being shipped', user.email, text, html)
        if new_status == 'Completed' and user and getattr(user, 'email', None):
            text = render_template('email/order_completed.txt', order=order, user=user)
            html = render_template('email/order_completed.html', order=order, user=user)
            send_email(f'Your SoBuy order #{order.id} is complete — thank you!', user.email, text, html)
    except Exception:
        current_app.logger.exception('Failed to send order status change email')

    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/products')
@login_required
def view_products():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    products = Product.query.all()
    return render_template('admin_products.html', products=products, title="Manage Products")



@main.route('/admin/slider/upload', methods=['POST'])
@login_required
def upload_slider_images():
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.admin_dashboard'))

    upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    files = request.files.getlist('slider_images')
    # fallback if single
    if not files or all(getattr(f, 'filename', '') == '' for f in files):
        flash('No files selected for upload.')
        return redirect(url_for('main.admin_dashboard'))

    # find current max position
    try:
        max_pos = db.session.query(db.func.max(HomeSliderImage.position)).scalar() or 0
    except Exception:
        max_pos = 0

    added = []
    for file in files:
        if file and getattr(file, 'filename', None):
            filename = secure_filename(file.filename)
            unique = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(upload_folder, unique)
            file.save(filepath)
            url = f"/static/uploads/{unique}"
            max_pos += 1
            img = HomeSliderImage(image_url=url, position=max_pos, active=True)
            db.session.add(img)
            added.append(url)

    try:
        db.session.commit()
    except OperationalError:
        # likely table missing (new model). Try to create missing tables and retry once.
        current_app.logger.warning('OperationalError during slider image commit; attempting to create missing tables and retry')
        try:
            db.create_all()
            db.session.commit()
        except Exception:
            current_app.logger.exception('Failed to create missing tables or commit after retry')
            flash('Failed to save slider images due to a database error. Please run `init_db.py` to create missing tables or check logs.')
            return redirect(url_for('main.admin_dashboard'))

    if added:
        flash(f'Uploaded {len(added)} slider image(s).')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/slider/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_slider_image(image_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.admin_dashboard'))
    img = HomeSliderImage.query.get_or_404(image_id)
    # attempt to delete file from disk
    try:
        parts = img.image_url.split('/')
        filename = parts[-1]
        upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
        filepath = os.path.join(upload_folder, filename)
        try:
            common = os.path.commonpath([os.path.abspath(filepath), os.path.abspath(upload_folder)])
        except Exception:
            common = None
        if common == os.path.abspath(upload_folder) and os.path.exists(filepath):
            os.remove(filepath)
            current_app.logger.info('Deleted slider image file from disk: %s', filepath)
    except Exception:
        current_app.logger.exception('Failed to delete slider file: %s', getattr(img, 'image_url', None))

    db.session.delete(img)
    db.session.commit()
    flash('Slider image removed.')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/bkash/set', methods=['POST'])
@login_required
def set_bkash_number():
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.index'))
    num = (request.form.get('bkash_number') or '').strip()
    if not num:
        flash('Please provide a bKash number.')
        return redirect(url_for('main.admin_dashboard'))
    try:
        # deactivate existing
        BkashNumber.query.update({BkashNumber.active: False})
        # see if number already exists
        existing = BkashNumber.query.filter_by(number=num).first()
        if existing:
            existing.active = True
        else:
            b = BkashNumber(number=num, active=True)
            db.session.add(b)
        db.session.commit()
        flash(f'Active bKash number set to {num}.')
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Failed to set active bKash number')
        flash('Failed to set active bKash number due to a server error.')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/bkash/remove', methods=['POST'])
@login_required
def remove_bkash_number():
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.index'))
    try:
        # deactivate all bKash numbers
        BkashNumber.query.update({BkashNumber.active: False})
        db.session.commit()
        flash('Active bKash number has been removed/disabled.')
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Failed to remove active bKash number')
        flash('Failed to remove active bKash number due to a server error.')
    return redirect(url_for('main.admin_dashboard'))



@main.route('/_debug/slider')
def debug_slider_json():
    """Return JSON array of active slider image URLs to help debugging client/server mismatch."""
    try:
        imgs = HomeSliderImage.query.filter_by(active=True).order_by(HomeSliderImage.position.asc()).all()
        urls = [i.image_url for i in imgs]
        return jsonify({'count': len(urls), 'slides': urls})
    except Exception:
        return jsonify({'count': 0, 'slides': []})



@main.route('/_test/slider')
def test_slider_page():
    """Render a dedicated test page for the slider to isolate issues with the homepage."""
    try:
        imgs = HomeSliderImage.query.filter_by(active=True).order_by(HomeSliderImage.position.asc()).all()
    except Exception:
        imgs = []
    return render_template('slider_test.html', slider_images=imgs)


@main.route('/admin/upload', methods=['GET', 'POST'])
@login_required
def upload_product():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))

    form = ProductUploadForm()
    if form.validate_on_submit():
        # parse colors from form (comma-separated string)
        colors_raw = request.form.get('colors') or (getattr(form, 'colors', None) and getattr(form.colors, 'data', None))
        colors_list = []
        if colors_raw:
            colors_list = [c.strip() for c in colors_raw.split(',') if c.strip()]
        colors_csv = ",".join(colors_list) if colors_list else None

        # ensure upload folder exists
        upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        # collect files from request (support multiple)
        saved_urls = []
        files = request.files.getlist('image')
        # fallback to single WTForms field if no list
        if not files or all(getattr(f, 'filename', '') == '' for f in files):
            single = getattr(form, 'image', None)
            if single and getattr(single, 'data', None) and getattr(single.data, 'filename', None):
                files = [single.data]

        for file in files:
            if file and getattr(file, 'filename', None):
                filename = secure_filename(file.filename)
                unique = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(upload_folder, unique)
                file.save(filepath)
                saved_urls.append(f"/static/uploads/{unique}")

        image_urls_csv = ",".join(saved_urls) if saved_urls else None

        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_url=image_urls_csv,
            colors=colors_csv,
            status=form.status.data if getattr(form, 'status', None) else 'active'
        )

        db.session.add(new_product)
        db.session.commit()
        flash('Product uploaded successfully.')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('upload_product.html', form=form)


@main.route('/admin/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    # debug logging to help diagnose why admins may be redirected
    try:
        current_app.logger.info('edit_product called: user_id=%s username=%s is_admin=%s product_id=%s',
                                getattr(current_user, 'id', None),
                                getattr(current_user, 'username', None),
                                getattr(current_user, 'role', None),
                                product_id)
    except Exception:
        pass

    product = Product.query.get_or_404(product_id)
    form = ProductUploadForm(obj=product)

    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        # coerce price to float safely
        try:
            product.price = float(form.price.data)
        except Exception:
            flash('Invalid price value.')
            return render_template('upload_product.html', form=form, product=product, title='Edit Product')

        # Handle colors
        colors_raw = request.form.get('colors') or (getattr(form, 'colors', None) and getattr(form.colors, 'data', None))
        colors_list = []
        if colors_raw:
            colors_list = [c.strip() for c in colors_raw.split(',') if c.strip()]
        product.colors = ",".join(colors_list) if colors_list else None

        # Handle image uploads
        upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        saved_urls = []
        # Preserve existing images if no new images are uploaded
        if product.image_url:
            saved_urls.extend(product.image_url.split(','))

        # Handle image removals requested by the admin (checkboxes named 'remove_image')
        remove_list = request.form.getlist('remove_image') or []
        # normalize values (strip)
        remove_list = [r.strip() for r in remove_list if r and r.strip()]
        if remove_list:
            # debug log current saved urls and removals requested
            current_app.logger.info('Requested image removals: %s', remove_list)
            initial_saved = list(saved_urls)
            # Remove from saved_urls and delete files from disk
            for rem in remove_list:
                # remove if present in saved_urls
                if rem in saved_urls:
                    try:
                        saved_urls.remove(rem)
                        current_app.logger.info('Removed image reference from product: %s', rem)
                    except ValueError:
                        current_app.logger.warning('Tried to remove image not in saved_urls: %s', rem)
                    # delete file from disk if it lives under uploads
                    try:
                        # expected format: /static/uploads/<filename>
                        parts = rem.split('/')
                        filename = parts[-1]
                        upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
                        filepath = os.path.join(upload_folder, filename)
                        # safety: ensure file is inside upload folder
                        try:
                            common = os.path.commonpath([os.path.abspath(filepath), os.path.abspath(upload_folder)])
                        except Exception:
                            common = None
                        if common == os.path.abspath(upload_folder):
                            if os.path.exists(filepath):
                                os.remove(filepath)
                                current_app.logger.info('Deleted image file from disk: %s', filepath)
                            else:
                                current_app.logger.info('Image file not found on disk (no delete): %s', filepath)
                        else:
                            current_app.logger.warning('Skipped deleting file outside upload folder: %s', filepath)
                    except Exception:
                        current_app.logger.exception('Failed to remove image file: %s', rem)
            # report which images were actually removed from the product
            removed_actual = [r for r in initial_saved if r not in saved_urls]
            if removed_actual:
                # Do NOT flash removed image paths to users. Keep only server-side logs.
                try:
                    removed_names = [r.split('/')[-1] for r in removed_actual]
                except Exception:
                    removed_names = removed_actual
                # Log the removal for admins/debugging but do not surface the filename/path in UI
                current_app.logger.info('Removed images for product %s: %s', product_id, removed_actual)

        files = request.files.getlist('image')
        if not files or all(getattr(f, 'filename', '') == '' for f in files):
            single = getattr(form, 'image', None)
            if single and getattr(single, 'data', None) and getattr(single.data, 'filename', None):
                files = [single.data]

        for file in files:
            if file and getattr(file, 'filename', None):
                filename = secure_filename(file.filename)
                unique = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(upload_folder, unique)
                file.save(filepath)
                saved_urls.append(f"/static/uploads/{unique}")
        
        # Remove duplicates and update image_url
        product.image_url = ",".join(list(set(saved_urls))) if saved_urls else None
        # update status from the form
        try:
            product.status = form.status.data
        except Exception:
            pass

        db.session.commit()
        flash('Product updated successfully.')
        return redirect(url_for('main.view_products'))

    # Pre-populate colors field for GET request
    if request.method == 'GET':
        form.colors.data = product.colors
        # ensure status field is prefilled when editing (some DBs/models may miss it)
        try:
            form.status.data = product.status
        except Exception:
            pass

    # If POST and form didn't validate, surface errors to the admin
    if request.method == 'POST' and not form.validate_on_submit():
        errs = []
        for field, e_list in form.errors.items():
            for e in e_list:
                errs.append(f"{field}: {e}")
        if errs:
            flash('Could not update product: ' + '; '.join(errs))

    return render_template('upload_product.html', form=form, product=product, title='Edit Product')


@main.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    # if product is not active, only allow admins to preview it
    try:
        is_active = getattr(product, 'status', 'active') == 'active'
    except Exception:
        is_active = True
    if not is_active:
        if not (current_user.is_authenticated and getattr(current_user, 'is_admin', False)):
            # don't reveal the existence of inactive products to customers
            abort(404)
    # record product visit (create or increment)
    try:
        pv = ProductVisit.query.filter_by(product_id=product.id).first()
        if pv:
            pv.visit_count = pv.visit_count + 1
            pv.last_visited = db.func.current_timestamp()
        else:
            pv = ProductVisit(product_id=product.id, visit_count=1)
            db.session.add(pv)
        db.session.commit()
    except Exception:
        # avoid breaking product page on db errors
        db.session.rollback()
    # other recent active products (exclude current)
    try:
        other_products = Product.query.filter(Product.id != product.id, Product.status == 'active').order_by(Product.created_at.desc()).limit(8).all()
    except Exception:
        other_products = []
    return render_template('product_detail.html', product=product, other_products=other_products)


@main.route('/blogs')
def blog_list():
    # show published blog posts
    try:
        posts = BlogPost.query.filter_by(status='published').order_by(BlogPost.created_at.desc()).all()
    except Exception:
        posts = []
    return render_template('blog_list.html', posts=posts)


@main.route('/blog/<int:post_id>')
def blog_detail_redirect(post_id):
    """Redirect old numeric blog post IDs to slug-based URLs for backward compatibility."""
    post = BlogPost.query.get_or_404(post_id)
    return redirect(url_for('main.blog_detail', slug=post.slug), code=301)


@main.route('/blog/<slug>', methods=['GET', 'POST'])
def blog_detail(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    # increment visit count
    try:
        bv = BlogVisit.query.filter_by(post_id=post.id).first()
        if bv:
            bv.visit_count = bv.visit_count + 1
            bv.last_visited = db.func.current_timestamp()
        else:
            bv = BlogVisit(post_id=post.id, visit_count=1)
            db.session.add(bv)
        db.session.commit()
    except Exception:
        db.session.rollback()

    # comments + like info
    raw_comments = BlogComment.query.filter_by(post_id=post.id).order_by(BlogComment.created_at.asc()).all()
    comments = []
    for c in raw_comments:
        try:
            u = User.query.get(c.user_id)
            username = u.username if u else 'User'
        except Exception:
            username = 'User'
        comments.append({'body': c.body, 'username': username, 'created_at': c.created_at})
    try:
        like_count = BlogLike.query.filter_by(post_id=post.id).count()
    except Exception:
        like_count = 0
    user_liked = False
    if current_user.is_authenticated:
        user_liked = BlogLike.query.filter_by(post_id=post.id, user_id=current_user.id).first() is not None

    # visit count (safe read)
    try:
        bv = BlogVisit.query.filter_by(post_id=post.id).first()
        visit_count = bv.visit_count if bv else 0
    except Exception:
        visit_count = 0

    # reading time (estimate) and author
    try:
        words = len((post.body or '').split())
        reading_minutes = max(1, int(round(words / 200.0)))
    except Exception:
        reading_minutes = None
    try:
        author = User.query.get(post.author_id) if post.author_id else None
        author_name = author.username if author else None
    except Exception:
        author_name = None

    # render markdown to sanitized HTML and TOC
    try:
        post_html, toc_html = render_markdown_safe(post.body)
    except Exception:
        post_html, toc_html = (post.body or '', '')

    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You must be signed in to comment.')
            return redirect(url_for('main.login'))
        comment = BlogComment(post_id=post.id, user_id=current_user.id, body=form.body.data)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted.')
        return redirect(url_for('main.blog_detail', post_id=post.id))

    # related posts (recent other posts)
    try:
        related = BlogPost.query.filter(BlogPost.id != post.id, BlogPost.status == 'published').order_by(BlogPost.created_at.desc()).limit(3).all()
    except Exception:
        related = []

    # featured products for sidebar: prefer top visited products, fallback to newest
    try:
        top_visits = ProductVisit.query.order_by(ProductVisit.visit_count.desc()).limit(4).all()
        featured_products = []
        for pv in top_visits:
            p = Product.query.get(pv.product_id)
            if p and getattr(p, 'status', 'active') == 'active':
                featured_products.append(p)
        if not featured_products:
            featured_products = Product.query.filter_by(status='active').order_by(Product.created_at.desc()).limit(4).all()
    except Exception:
        try:
            featured_products = Product.query.filter_by(status='active').order_by(Product.created_at.desc()).limit(4).all()
        except Exception:
            featured_products = []

    return render_template('blog_detail.html', post=post, post_html=post_html, toc_html=toc_html, comments=comments, like_count=like_count, user_liked=user_liked, form=form, visit_count=visit_count, reading_minutes=reading_minutes, author_name=author_name, related=related, featured_products=featured_products)


@main.route('/blog/<slug>/comment', methods=['POST'])
@login_required
def post_comment(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    form = CommentForm()
    if form.validate_on_submit():
        comment = BlogComment(post_id=post.id, user_id=current_user.id, body=form.body.data)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted.')
    else:
        flash('Could not post comment. Ensure the comment is not empty.')
    return redirect(url_for('main.blog_detail', slug=post.slug))


@main.route('/blog/<slug>/like', methods=['POST'])
@login_required
def toggle_like(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    existing = BlogLike.query.filter_by(post_id=post.id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('You unliked the post.')
    else:
        like = BlogLike(post_id=post.id, user_id=current_user.id)
        db.session.add(like)
        db.session.commit()
        flash('You liked the post.')
    return redirect(url_for('main.blog_detail', slug=post.slug))


@main.route('/admin/blogs')
@login_required
def admin_blogs():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    try:
        posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    except Exception:
        posts = []
    # attach visit counts
    posts_with_visits = []
    for p in posts:
        try:
            visits = BlogVisit.query.filter_by(post_id=p.id).first()
            vcount = visits.visit_count if visits else 0
        except Exception:
            vcount = 0
        try:
            comment_count = BlogComment.query.filter_by(post_id=p.id).count()
        except Exception:
            comment_count = 0
        try:
            like_count = BlogLike.query.filter_by(post_id=p.id).count()
        except Exception:
            like_count = 0
        posts_with_visits.append({'post': p, 'visits': vcount, 'comments': int(comment_count), 'likes': int(like_count)})
    return render_template('admin_blog_posts.html', posts=posts_with_visits)


@main.route('/admin/blog/create', methods=['GET', 'POST'])
@login_required
def admin_create_blog():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    form = BlogPostForm()
    if form.validate_on_submit():
        upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        image_url = None
        file = request.files.get('image')
        if file and getattr(file, 'filename', None):
            filename = secure_filename(file.filename)
            unique = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(upload_folder, unique)
            file.save(filepath)
            image_url = f"/static/uploads/{unique}"

        slug = generate_slug(form.title.data, BlogPost)
        post = BlogPost(title=form.title.data, slug=slug, body=form.body.data, image_url=image_url, author_id=current_user.id, status=form.status.data)
        db.session.add(post)
        db.session.commit()
        flash('Blog post created.')
        return redirect(url_for('main.admin_blogs'))
    return render_template('upload_blog.html', form=form)


@main.route('/admin/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_blog(post_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = generate_slug(form.title.data, BlogPost, existing_id=post.id)
        post.body = form.body.data
        post.status = form.status.data
        file = request.files.get('image')
        if file and getattr(file, 'filename', None):
            upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(file.filename)
            unique = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(upload_folder, unique)
            file.save(filepath)
            post.image_url = f"/static/uploads/{unique}"
        db.session.commit()
        flash('Blog post updated.')
        return redirect(url_for('main.admin_blogs'))
    return render_template('upload_blog.html', form=form, post=post)


@main.route('/admin/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def admin_delete_blog(post_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.index'))
    post = BlogPost.query.get_or_404(post_id)
    # attempt to delete image file
    try:
        if post.image_url:
            parts = post.image_url.split('/')
            filename = parts[-1]
            upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
            filepath = os.path.join(upload_folder, filename)
            try:
                common = os.path.commonpath([os.path.abspath(filepath), os.path.abspath(upload_folder)])
            except Exception:
                common = None
            if common == os.path.abspath(upload_folder) and os.path.exists(filepath):
                os.remove(filepath)
    except Exception:
        current_app.logger.exception('Failed to remove blog image file')
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted.')
    return redirect(url_for('main.admin_blogs'))


@main.route('/admin/comments')
@login_required
def admin_comments():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    try:
        raw = BlogComment.query.order_by(BlogComment.created_at.desc()).limit(200).all()
    except Exception:
        raw = []
    comments = []
    for c in raw:
        try:
            u = User.query.get(c.user_id)
            username = u.username if u else 'User'
        except Exception:
            username = 'User'
        try:
            post = BlogPost.query.get(c.post_id)
            post_slug = post.slug if post else None
        except Exception:
            post_slug = None
        comments.append({'id': c.id, 'post_id': c.post_id, 'post_slug': post_slug, 'body': c.body, 'created_at': c.created_at, 'username': username})
    return render_template('admin_comments.html', comments=comments)


@main.route('/admin/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def admin_delete_comment(comment_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.index'))
    c = BlogComment.query.get_or_404(comment_id)
    db.session.delete(c)
    db.session.commit()
    flash('Comment deleted.')
    return redirect(url_for('main.admin_comments'))


@main.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    # read available colors from model (comma-separated)
    colors = []
    if getattr(product, 'colors', None):
        colors = [c.strip() for c in (product.colors or "").split(',') if c.strip()]

    selected_color = (request.form.get('color') or '').strip()
    if colors and not selected_color:
        flash('Please select a color before adding to cart.')
        return redirect(request.referrer or url_for('main.product_detail', product_id=product.id))

    # quantity
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    color_key = selected_color or ''
    cart_key = f"{product_id}:{color_key}"

    cart = session.get('cart', {})
    cart[cart_key] = cart.get(cart_key, 0) + quantity
    session['cart'] = cart

    flash(f'"{product.name}" has been added to your cart.')
    return redirect(request.referrer or url_for('main.index'))


@main.route('/cart', methods=['GET', 'POST'])
def cart():
    cart = session.get('cart', {}) or {}
    detailed_cart = []
    total_amount = 0.0
    for composite_key, quantity in cart.items():
        try:
            pid_str, color = composite_key.split(':', 1)
            pid = int(pid_str)
        except Exception:
            continue
        product = Product.query.get(pid)
        if not product:
            continue
        item_total = product.price * quantity
        total_amount += item_total

        # images
        images = []
        if getattr(product, 'image_url', None):
            images = [u.strip() for u in (product.image_url or "").split(',') if u.strip()]

        detailed_cart.append({
            'product_id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': quantity,
            'total': item_total,
            'color': color if color else None,
            'image': images[0] if images else None
        })

    # load delivery fee options
    try:
        fees = DeliveryFee.query.order_by(DeliveryFee.id.asc()).all()
    except Exception:
        fees = []

    # validate any delivery stored in session — if it doesn't match current fee keys, clear it
    try:
        sel = session.get('delivery')
        if sel and fees:
            valid_keys = {f.key for f in fees}
            if sel.get('key') not in valid_keys:
                session.pop('delivery', None)
                sel = None
    except Exception:
        # if session isn't available or unexpected data, quietly continue
        sel = session.get('delivery')

    # clear any existing delivery on a plain GET so nothing is preselected by default
    if request.method == 'GET':
        session.pop('delivery', None)

    # handle POST when user selects a delivery option
    if request.method == 'POST':
        sel = (request.form.get('delivery_option') or '').strip()
        coupon_data = session.get('coupon')
        if not sel:
            flash('Please select a delivery option before proceeding to checkout.')
            return render_template('cart.html', cart=detailed_cart, total_amount=total_amount, fees=fees, selected=session.get('delivery'), coupon=coupon_data)
        # find fee row
        chosen = None
        for f in fees:
            if f.key == sel:
                chosen = f
                break
        if not chosen:
            flash('Invalid delivery option selected.')
            return render_template('cart.html', cart=detailed_cart, total_amount=total_amount, fees=fees, selected=session.get('delivery'), coupon=coupon_data)
        session['delivery'] = {'key': chosen.key, 'label': chosen.label, 'amount': float(chosen.amount)}
        return redirect(url_for('main.checkout'))

    # Get applied coupon from session
    coupon_data = session.get('coupon')

    return render_template('cart.html', cart=detailed_cart, total_amount=total_amount, fees=fees, selected=session.get('delivery'), coupon=coupon_data)


@main.route('/cart/set-delivery', methods=['POST'])
def set_delivery_ajax():
    """AJAX endpoint to set delivery option in session and return updated totals.
    Expects JSON: { key: 'express_inside' }
    Returns JSON with delivery details and recalculated totals.
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        data = {}
    sel = (data.get('key') or '').strip()

    # load fees
    try:
        fees = DeliveryFee.query.order_by(DeliveryFee.id.asc()).all()
    except Exception:
        fees = []

    if not sel:
        return jsonify({'success': False, 'error': 'No delivery option provided.'}), 400

    chosen = None
    for f in fees:
        if f.key == sel:
            chosen = f
            break
    if not chosen:
        return jsonify({'success': False, 'error': 'Invalid delivery option.'}), 400

    # persist in session
    session['delivery'] = {'key': chosen.key, 'label': chosen.label, 'amount': float(chosen.amount)}

    # recompute cart subtotal
    cart = session.get('cart', {}) or {}
    subtotal = 0.0
    for composite_key, quantity in cart.items():
        try:
            pid_str, _ = composite_key.split(':', 1)
            pid = int(pid_str)
        except Exception:
            continue
        product = Product.query.get(pid)
        if not product:
            continue
        subtotal += (product.price * quantity)

    delivery_amount = float(chosen.amount)
    grand_total = subtotal + delivery_amount

    return jsonify({
        'success': True,
        'delivery': {'key': chosen.key, 'label': chosen.label, 'amount': delivery_amount},
        'subtotal': round(subtotal, 2),
        'delivery_amount': round(delivery_amount, 2),
        'grand_total': round(grand_total, 2)
    })


@main.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    """Apply a coupon code to the current cart session."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Please log in to use coupons.'}), 401
    
    try:
        data = request.get_json(force=True) if request.is_json else request.form
    except Exception:
        data = request.form
    
    code = (data.get('code') or '').strip().upper()
    if not code:
        return jsonify({'success': False, 'error': 'Please enter a coupon code.'}), 400
    
    from app.models import Coupon, CouponUsage
    
    # Find coupon
    coupon = Coupon.query.filter_by(code=code).first()
    if not coupon:
        return jsonify({'success': False, 'error': 'Invalid coupon code.'}), 400
    
    # Validate coupon
    if not coupon.is_active:
        return jsonify({'success': False, 'error': 'This coupon is not active.'}), 400
    
    if coupon.expiry_date and datetime.utcnow() > coupon.expiry_date:
        return jsonify({'success': False, 'error': 'This coupon has expired.'}), 400
    
    # Check total usage limit
    if coupon.max_total_uses and coupon.total_uses >= coupon.max_total_uses:
        return jsonify({'success': False, 'error': 'This coupon has reached its usage limit.'}), 400
    
    # Check per-user usage limit
    if coupon.max_uses_per_user:
        user_usage_count = CouponUsage.query.filter_by(
            coupon_id=coupon.id,
            user_id=current_user.id
        ).count()
        if user_usage_count >= coupon.max_uses_per_user:
            return jsonify({'success': False, 'error': 'You have already used this coupon the maximum number of times.'}), 400
    
    # Calculate discount
    cart = session.get('cart', {}) or {}
    subtotal = 0.0
    for composite_key, quantity in cart.items():
        try:
            pid_str, _ = composite_key.split(':', 1)
            pid = int(pid_str)
        except Exception:
            continue
        product = Product.query.get(pid)
        if not product:
            continue
        subtotal += (product.price * quantity)
    
    if subtotal <= 0:
        return jsonify({'success': False, 'error': 'Your cart is empty.'}), 400
    
    discount_amount = (subtotal * coupon.discount_percent) / 100.0
    
    # Apply max discount cap if set
    if coupon.max_discount_amount and discount_amount > coupon.max_discount_amount:
        discount_amount = coupon.max_discount_amount
    
    discount_amount = round(discount_amount, 2)
    
    # Store coupon in session
    session['coupon'] = {
        'id': coupon.id,
        'code': coupon.code,
        'discount_percent': coupon.discount_percent,
        'discount_amount': discount_amount
    }
    
    # Recalculate totals
    delivery = session.get('delivery', {})
    delivery_amount = float(delivery.get('amount', 0.0)) if delivery else 0.0
    grand_total = subtotal - discount_amount + delivery_amount
    
    return jsonify({
        'success': True,
        'coupon': {
            'code': coupon.code,
            'discount_percent': coupon.discount_percent,
            'discount_amount': discount_amount
        },
        'subtotal': round(subtotal, 2),
        'discount_amount': round(discount_amount, 2),
        'delivery_amount': round(delivery_amount, 2),
        'grand_total': round(grand_total, 2)
    })


@main.route('/cart/remove-coupon', methods=['POST'])
def remove_coupon():
    """Remove the applied coupon from session."""
    session.pop('coupon', None)
    
    # Recalculate totals
    cart = session.get('cart', {}) or {}
    subtotal = 0.0
    for composite_key, quantity in cart.items():
        try:
            pid_str, _ = composite_key.split(':', 1)
            pid = int(pid_str)
        except Exception:
            continue
        product = Product.query.get(pid)
        if not product:
            continue
        subtotal += (product.price * quantity)
    
    delivery = session.get('delivery', {})
    delivery_amount = float(delivery.get('amount', 0.0)) if delivery else 0.0
    grand_total = subtotal + delivery_amount
    
    return jsonify({
        'success': True,
        'subtotal': round(subtotal, 2),
        'delivery_amount': round(delivery_amount, 2),
        'grand_total': round(grand_total, 2)
    })



@login_required
def checkout():
    form = CheckoutForm()

    # Prefill form fields from user's profile when available (GET or initial render)
    if current_user.is_authenticated:
        try:
            if not form.name.data:
                form.name.data = current_user.username or ''
            if not form.phone.data and getattr(current_user, 'phone', None):
                form.phone.data = current_user.phone
            if not form.address.data and getattr(current_user, 'address', None):
                form.address.data = current_user.address
        except Exception:
            # don't block checkout on prefill errors
            current_app.logger.exception('Failed to prefill checkout form from user profile')

    # compute total amount from cart
    cart = session.get('cart', {}) or {}
    total_amount = 0.0
    for composite_key, quantity in cart.items():
        try:
            pid_str, _ = composite_key.split(':', 1)
            pid = int(pid_str)
        except Exception:
            continue
        product = Product.query.get(pid)
        if not product:
            continue
        total_amount += product.price * quantity

    # active receiving bKash number to show during checkout
    try:
        active_bkash = BkashNumber.query.filter_by(active=True).first()
    except Exception:
        active_bkash = None

    # require delivery selection present in session when accessing checkout
    delivery = session.get('delivery')
    if not delivery:
        flash('Please choose a delivery option from the cart before proceeding to checkout.')
        return redirect(url_for('main.cart'))

    # add delivery fee to total amount
    try:
        delivery_fee_amount = float(delivery.get('amount', 0.0))
    except Exception:
        delivery_fee_amount = 0.0
    total_amount += delivery_fee_amount

    if form.validate_on_submit():
        # Prevent bKash orders when there is no active receiving number
        pm = (form.payment_method.data or '').lower()
        if pm == 'bkash' and not active_bkash:
            flash('bKash is currently unavailable. Please choose another payment method.')
            return render_template('checkout.html', form=form, total_amount=total_amount, active_bkash=active_bkash, delivery=delivery)
        # build items summary from cart for email
        cart_items = []
        for composite_key, quantity in cart.items():
            try:
                pid_str, color = composite_key.split(':', 1)
                pid = int(pid_str)
            except Exception:
                continue
            product = Product.query.get(pid)
            if not product:
                continue
            cart_items.append({
                'product_id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'color': color or None
            })

        # Get coupon discount from session if applied
        coupon_data = session.get('coupon')
        discount_amount = 0.0
        coupon_id = None
        
        if coupon_data:
            coupon_id = coupon_data.get('id')
            discount_amount = coupon_data.get('discount_amount', 0.0)

        # create order record
        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            payment_method=form.payment_method.data,
            trx_id=form.trx_id.data if (form.payment_method.data or '').lower() == 'bkash' else None,
            bkash_number=form.bkash_number.data if (form.payment_method.data or '').lower() == 'bkash' else None,
            delivery_type=delivery.get('key') if delivery else None,
            delivery_fee=delivery.get('amount') if delivery else 0.0,
            coupon_id=coupon_id,
            discount_amount=discount_amount
        )
        # If requested, save phone/address to user's profile (only set if missing)
        try:
            if getattr(form, 'save_to_profile', None) and form.save_to_profile.data and current_user.is_authenticated:
                updated = False
                if (not getattr(current_user, 'phone', None)) and form.phone.data:
                    current_user.phone = form.phone.data
                    updated = True
                if (not getattr(current_user, 'address', None)) and form.address.data:
                    current_user.address = form.address.data
                    updated = True
                if updated:
                    db.session.add(current_user)
        except Exception:
            current_app.logger.exception('Failed to save profile info from checkout')
        db.session.add(order)
        # flush to populate order.id so we can create OrderItem rows in the same transaction
        db.session.flush()

        # persist each cart item as an OrderItem
        try:
            for item in cart_items:
                oi = OrderItem(order_id=order.id, product_id=item['product_id'], quantity=item['quantity'], unit_price=item['price'])
                db.session.add(oi)
        except Exception:
            current_app.logger.exception('Failed to create order items')

        # commit order and items together
        db.session.commit()

        # Track coupon usage if a coupon was applied
        if coupon_id:
            try:
                from app.models import Coupon, CouponUsage
                coupon = Coupon.query.get(coupon_id)
                if coupon:
                    # Increment total usage count
                    coupon.total_uses += 1
                    db.session.add(coupon)
                    
                    # Create usage record
                    usage = CouponUsage(
                        coupon_id=coupon_id,
                        user_id=current_user.id,
                        order_id=order.id
                    )
                    db.session.add(usage)
                    db.session.commit()
            except Exception:
                current_app.logger.exception('Failed to track coupon usage')
                # Don't rollback the order - coupon tracking failure shouldn't break checkout

        # send email notifications (customer + admins)
        try:
            # prepare templates
            text = render_template('email/order.txt', order=order, items=cart_items, user=current_user)
            html = render_template('email/order.html', order=order, items=cart_items, user=current_user)

            # send to customer
            if getattr(current_user, 'email', None):
                send_email(f'Your SoBuy order #{order.id}', current_user.email, text, html)

            # send to admins
            admins = current_app.config.get('ORDER_NOTIFICATION_RECIPIENTS')
            if admins:
                send_email(f'New order #{order.id}', admins, text, html)

            # send to employees
            employees = current_app.config.get('EMPLOYEE_RECIPIENTS')
            if employees:
                send_email(f'New order #{order.id}', employees, text, html)
        except Exception:
            # don't let email failures block checkout
            current_app.logger.exception('Failed to send order notification emails')

        # clear cart
        session.pop('cart', None)
        session.pop('delivery', None)
        session.pop('coupon', None)
        flash('Order placed successfully!')

        return redirect(url_for('main.order_invoice', order_id=order.id))

    return render_template('checkout.html', form=form, total_amount=total_amount, active_bkash=active_bkash, delivery=delivery)


@main.route('/create-admin')
def create_admin():
    if User.query.filter_by(role='admin').first():
        return 'Admin user already exists.'
    admin_user = User(username='admin', role='admin')
    # give a default email to satisfy the model; please change this after first login
    admin_user.email = 'admin@localhost'
    admin_user.set_password('admin')
    db.session.add(admin_user)
    db.session.commit()
    return 'Admin user created successfully. Username: admin, Password: admin'


@main.route('/order/<int:order_id>/invoice')
@login_required
def order_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    # only the order owner or an admin may view the invoice
    if not (current_user.is_authenticated and (current_user.is_admin or current_user.id == order.user_id)):
        flash('You do not have permission to view this invoice.')
        return redirect(url_for('main.index'))

    try:
        items = OrderItem.query.filter_by(order_id=order.id).all()
    except Exception:
        items = []

    # load the user who placed the order for address/name/contact
    user = User.query.get(order.user_id)
    # resolve delivery label if possible
    delivery_label = None
    try:
        if order.delivery_type:
            df = DeliveryFee.query.filter_by(key=order.delivery_type).first()
            if df:
                delivery_label = df.label
    except Exception:
        delivery_label = None

    return render_template('invoice.html', order=order, items=items, user=user, delivery_label=delivery_label)


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # save profile fields
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        # don't allow changing username here for simplicity
        db.session.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('main.profile'))

    # user orders
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('profile.html', form=form, orders=orders)


@main.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.')
            return redirect(url_for('main.change_password'))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password changed successfully.')
        return redirect(url_for('main.profile'))
    return render_template('change_password.html', form=form)


@main.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get('product_id')
    color = (request.form.get('color') or '').strip()
    if not product_id:
        return redirect(url_for('main.cart'))
    cart = session.get('cart', {})
    key = f"{product_id}:{color}"
    if key in cart:
        del cart[key]
        session['cart'] = cart
        flash('Item removed from cart.')
    return redirect(url_for('main.cart'))


@main.route('/admin/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete products.')
        return redirect(url_for('main.index'))
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/debug-user')
@login_required
def admin_debug_user():
    # small debug endpoint to inspect current_user and session for admin troubleshooting
    out = []
    try:
        out.append(f"current_user: id={getattr(current_user, 'id', None)}, username={getattr(current_user,'username',None)}, role={getattr(current_user,'role',None)}, is_authenticated={current_user.is_authenticated}")
    except Exception as e:
        out.append(f"current_user read error: {e}")
    try:
        out.append(f"session keys: {list(session.keys())}")
    except Exception as e:
        out.append(f"session read error: {e}")
    # show request headers
    headers = dict(request.headers)
    out.append(f"remote_addr: {request.remote_addr}")
    out.append(f"headers: { {k: headers.get(k) for k in ['User-Agent','Referer','Host','Cookie'] } }")
    return '<pre>' + '\n'.join(out) + '</pre>'



@main.route('/admin/delete-image', methods=['POST'])
@login_required
def admin_delete_image():
    # AJAX endpoint to remove a single image from a product and delete the file
    if not current_user.is_admin:
        return jsonify({'error': 'forbidden'}), 403

    data = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    image = data.get('image')
    if not product_id or not image:
        return jsonify({'error': 'missing product_id or image'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'product not found'}), 404

    saved = product.image_url.split(',') if product.image_url else []
    if image not in saved:
        return jsonify({'error': 'image not associated with product'}), 400

    # remove reference
    try:
        saved.remove(image)
    except ValueError:
        pass

    # delete file from disk if inside upload folder
    try:
        parts = image.split('/')
        filename = parts[-1]
        upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.static_folder, 'uploads')
        filepath = os.path.join(upload_folder, filename)
        try:
            common = os.path.commonpath([os.path.abspath(filepath), os.path.abspath(upload_folder)])
        except Exception:
            common = None
        if common == os.path.abspath(upload_folder) and os.path.exists(filepath):
            os.remove(filepath)
            current_app.logger.info('Deleted image file via AJAX: %s', filepath)
        else:
            current_app.logger.info('Skipped deleting file (not found or outside upload folder): %s', filepath)
    except Exception:
        current_app.logger.exception('Error deleting image file via AJAX: %s', image)

    product.image_url = ",".join(saved) if saved else None
    db.session.commit()
    return jsonify({'ok': True, 'images': saved})