from app import create_app, db

# Create the Flask app instance
app = create_app()

# Push an application context
with app.app_context():
    # Now you can use the 'db' object
    db.create_all()
    print("Database tables created successfully in instance/app.db")