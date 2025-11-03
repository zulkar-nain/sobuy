import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

from config import Config


def create_app():
    app = Flask(__name__)
    # load configuration from config.Config which reads environment variables
    app.config.from_object(Config)

    # ensure upload folder exists (config may override)
    app.config['UPLOAD_FOLDER'] = app.config.get('UPLOAD_FOLDER') or os.path.join(app.static_folder, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # Flask-Login uses this to reload the user object from the user ID stored in the session
        return User.query.get(int(user_id))

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app