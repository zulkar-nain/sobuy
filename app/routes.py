import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from app import db
from app.models import Product, User, Order, ProductVisit
from app.forms import LoginForm, ProductUploadForm, PaymentForm, RegistrationForm, CheckoutForm, ProfileForm, ChangePasswordForm, OTPForm
from app.models import Product, User, Order, ProductVisit, OTPToken
from app.email import send_email
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)


@main.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)


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
            'amount': o.total_amount,
            'payment_method': o.payment_method,
            'trx_id': o.trx_id,
            'created_at': o.created_at
        })

    # top products by visits
    top_visits = ProductVisit.query.order_by(ProductVisit.visit_count.desc()).limit(5).all()
    top_products = []
    for pv in top_visits:
        p = Product.query.get(pv.product_id)
        if p:
            top_products.append({'product': p, 'visits': pv.visit_count})

    return render_template('admin_dashboard.html',
                           total_products=total_products,
                           total_orders=total_orders,
                           total_customers=total_customers,
                           recent_orders=recent_orders,
                           top_products=top_products)


@main.route('/admin/products')
@login_required
def view_products():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    products = Product.query.all()
    return render_template('admin_products.html', products=products, title="Manage Products")


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
            colors=colors_csv
        )

        db.session.add(new_product)
        db.session.commit()
        flash('Product uploaded successfully.')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('upload_product.html', form=form)


@main.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
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
    return render_template('product_detail.html', product=product)


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


@main.route('/cart')
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

    return render_template('cart.html', cart=detailed_cart, total_amount=total_amount)


@main.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = CheckoutForm()

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

    if form.validate_on_submit():
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

        # create order record
        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            payment_method=form.payment_method.data,
            trx_id=form.trx_id.data if (form.payment_method.data or '').lower() == 'bkash' else None
        )
        db.session.add(order)
        db.session.commit()

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
        except Exception:
            # don't let email failures block checkout
            current_app.logger.exception('Failed to send order notification emails')

        # clear cart
        session.pop('cart', None)
        flash('Order placed successfully!')
        return redirect(url_for('main.index'))

    return render_template('checkout.html', form=form, total_amount=total_amount)


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