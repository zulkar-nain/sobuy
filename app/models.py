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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'cash' or 'bkash'
    trx_id = db.Column(db.String(100), nullable=True)  # For Bkash payments
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, paid, shipped, cancelled
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

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