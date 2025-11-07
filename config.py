import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    # prefer a provided DATABASE_URL (Render will set this when you add a managed DB)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PAYMENT_OPTIONS = ['Cash on Delivery', 'Bkash']
    # upload folder can be configured via env var in production (use S3 for durability)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'app', 'static', 'uploads')
    # recipients for order notifications (comma-separated)
    ORDER_NOTIFICATION_RECIPIENTS = os.environ.get('ORDER_NOTIFICATION_RECIPIENTS')
    EMPLOYEE_RECIPIENTS = os.environ.get('EMPLOYEE_RECIPIENTS') or 'teamsobuy@gmail.com' # Replace with actual employee email(s)

    # email settings
    MAIL_PROVIDER = os.environ.get('MAIL_PROVIDER') or 'brevo'
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@teamsobuy.shop'
    BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL') or 'noreply@teamsobuy.shop'

    