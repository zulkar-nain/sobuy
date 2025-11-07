from app import db
from flask_login import UserMixin # Import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model): # Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # allow nullable for backwards compatibility with existing users created before email was required
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='customer')  # 'admin' or 'customer'
    # Optional contact details
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    # account status
    is_banned = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            # Unsupported/unknown hash format stored in DB (e.g. a non-werkzeug format)
            # Treat as password mismatch rather than crashing the app.
            return False
        except Exception:
            # Any other unexpected error while checking password should not bring down the app.
            return False

    @property
    def is_admin(self):
        return self.role == 'admin'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    # store comma-separated URLs for multiple images
    image_url = db.Column(db.Text, nullable=True)
    # optional comma-separated color names/hex values
    colors = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active') # active, inactive
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'cash' or 'bkash'
    trx_id = db.Column(db.String(100), nullable=True)  # For Bkash payments
    bkash_number = db.Column(db.String(50), nullable=True)  # The customer-provided sending number
    delivery_type = db.Column(db.String(50), nullable=True)
    delivery_fee = db.Column(db.Float, nullable=True, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, Processing, Shipped, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # relationships (optional)
    order = db.relationship('Order', backref=db.backref('items', lazy='joined'))
    product = db.relationship('Product', backref=db.backref('order_items', lazy='dynamic'))

class ProductVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    visit_count = db.Column(db.Integer, default=0)
    last_visited = db.Column(db.DateTime, default=db.func.current_timestamp())


class OTPToken(db.Model):
    """One-time tokens for email verification during signup or other flows."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    username = db.Column(db.String(80), nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    otp_code = db.Column(db.String(10), nullable=False)
    used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class HomeSliderImage(db.Model):
    """Images used in the homepage 'Discover Our New Collection' slider/hero background.
    Admins can upload multiple images; they will be shown (first by default) behind the hero section.
    """
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(300), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='published')  # published, draft
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class BlogComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class BlogLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class BlogVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    visit_count = db.Column(db.Integer, default=0)
    last_visited = db.Column(db.DateTime, default=db.func.current_timestamp())


class BkashNumber(db.Model):
    """Stores bKash receiving numbers; one can be active at a time."""
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class DeliveryFee(db.Model):
    """Stores configurable delivery fee amounts per delivery option/key."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), nullable=False, unique=True)  # e.g. express_inside, regular_inside, regular_outside
    label = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class NewsletterSubscriber(db.Model):
    """Stores emails of customers who subscribe to the site newsletter."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())