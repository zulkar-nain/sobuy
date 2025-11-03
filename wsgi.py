"""WSGI entrypoint for Render / Gunicorn

Render/gunicorn will import the `app` callable from this module.
If you need to customize app creation (env vars), set them via Render's dashboard.
"""
from app import create_app

# create the Flask application
app = create_app()

if __name__ == '__main__':
    # for local debugging
    app.run(host='0.0.0.0', port=5000)
