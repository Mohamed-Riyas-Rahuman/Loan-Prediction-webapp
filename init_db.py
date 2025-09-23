from app import app, db

# Make sure app context is active
with app.app_context():
    db.create_all()  # This creates loan_prediction.db and all tables
    print("✅ loan_prediction.db created with all tables!")
