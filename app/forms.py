from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, FileField, TextAreaField, HiddenField, SelectField, BooleanField, IntegerField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, NumberRange
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)], render_kw={"placeholder": "Username"})
    email = StringField('Email', validators=[DataRequired(), Length(max=120)], render_kw={"placeholder": "you@example.com"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('An account with that email already exists.')


class OTPForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(), Length(min=4, max=10)], render_kw={"placeholder": "Enter the code sent to your email"})
    submit = SubmitField('Verify')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)], render_kw={"placeholder": "Username"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "******************"})
    submit = SubmitField('Login')


class ProductUploadForm(FlaskForm):
    id = HiddenField('Product ID')
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    # We accept one or multiple files from the request.files in the view; keep a FileField for single-file fallback
    image = FileField('Product Image')
    existing_image_urls = HiddenField('Existing Image URLs')
    # comma-separated colors (e.g. Red, Blue, #ffffff)
    colors = StringField('Colors (comma-separated)', render_kw={"placeholder": "Red, Blue, #ffffff"})
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')], validators=[DataRequired()])
    submit = SubmitField('Save Product')

class PaymentForm(FlaskForm):
    trx_id = StringField('bKash TrxID')
    submit = SubmitField('Confirm Order')


class CheckoutForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    address = TextAreaField('Delivery Address', validators=[DataRequired(), Length(min=5, max=500)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=6, max=20)])
    payment_method = StringField('Payment Method', validators=[DataRequired()])
    trx_id = StringField('bKash TrxID')
    bkash_number = StringField('bKash Number')
    save_to_profile = BooleanField('Save to profile as my address')
    submit = SubmitField('Place Order')

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        pm = (self.payment_method.data or '').lower()
        if pm == 'bkash':
            if not (self.trx_id.data and self.trx_id.data.strip()):
                self.trx_id.errors.append('Transaction ID is required for bKash payments.')
                return False
            if not (self.bkash_number.data and self.bkash_number.data.strip()):
                self.bkash_number.errors.append('Your bKash number is required for bKash payments.')
                return False
        return True


class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    phone = StringField('Phone', validators=[Length(max=30)])
    address = TextAreaField('Address', validators=[Length(max=500)])
    submit = SubmitField('Save')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')


class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    body = TextAreaField('Body', validators=[DataRequired(), Length(min=10)])
    image = FileField('Image')
    status = SelectField('Status', choices=[('published','Published'), ('draft','Draft')], validators=[DataRequired()])
    submit = SubmitField('Save Post')


class CommentForm(FlaskForm):
    body = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Post Comment')


class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired(), Length(min=3, max=50)], render_kw={"placeholder": "e.g., SAVE20"})
    discount_percent = FloatField('Discount Percent', validators=[DataRequired(), NumberRange(min=0, max=100)], render_kw={"placeholder": "e.g., 20"})
    max_discount_amount = FloatField('Max Discount Amount (optional)', validators=[Optional()], render_kw={"placeholder": "e.g., 500"})
    max_uses_per_user = IntegerField('Max Uses Per User (optional)', validators=[Optional(), NumberRange(min=1)], render_kw={"placeholder": "Leave empty for unlimited"})
    max_total_uses = IntegerField('Max Total Uses (optional)', validators=[Optional(), NumberRange(min=1)], render_kw={"placeholder": "Leave empty for unlimited"})
    expiry_date = DateTimeLocalField('Expiry Date (optional)', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    is_active = BooleanField('Active')
    submit = SubmitField('Save Coupon')