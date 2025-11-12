"""WSGI entrypoint for Render / Gunicorn

Render/gunicorn will import the `app` callable from this module.
If you need to customize app creation (env vars), set them via Render's dashboard.
"""
import os
from dotenv import load_dotenv

# Load .env file before creating the app
# This is critical for production when using Gunicorn
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from app import create_app

# create the Flask application
app = create_app()

if __name__ == '__main__':
    # for local debugging
    app.run(host='0.0.0.0', port=5000)
