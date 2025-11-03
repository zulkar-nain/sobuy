from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
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
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    # We accept one or multiple files from the request.files in the view; keep a FileField for single-file fallback
    image = FileField('Product Image')
    # comma-separated colors (e.g. Red, Blue, #ffffff)
    colors = StringField('Colors (comma-separated)', render_kw={"placeholder": "Red, Blue, #ffffff"})
    submit = SubmitField('Upload Product')

class PaymentForm(FlaskForm):
    trx_id = StringField('bKash TrxID')
    submit = SubmitField('Confirm Order')


class CheckoutForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    address = TextAreaField('Delivery Address', validators=[DataRequired(), Length(min=5, max=500)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=6, max=20)])
    payment_method = StringField('Payment Method', validators=[DataRequired()])
    trx_id = StringField('bKash TrxID')
    submit = SubmitField('Place Order')

    def validate_trx_id(self, field):
        # If payment method is bkash require trx_id
        pm = (self.payment_method.data or '').lower()
        if pm == 'bkash' and not (field.data and field.data.strip()):
            raise ValidationError('Transaction ID is required for bKash payments.')


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