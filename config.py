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
    # Mail settings (read from environment variables)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    _mail_port = os.environ.get('MAIL_PORT')
    MAIL_PORT = int(_mail_port) if _mail_port else None
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('1', 'true', 'yes')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ('1', 'true', 'yes')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')