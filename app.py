from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

# Configure authentication backend (supports dictionary fallback)
USE_DICT_STORAGE = os.environ.get('USE_DICT_STORAGE', 'true').lower() == 'true'

if not USE_DICT_STORAGE:
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app, origins=["*"], supports_credentials=False)

if not USE_DICT_STORAGE:
    db = SQLAlchemy(app)
else:
    db = None

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Dictionary storage for users (fallback as requested)
if USE_DICT_STORAGE:
    users_dict = {}
    user_id_counter = 1

# User model (supports both database and dictionary storage)
if USE_DICT_STORAGE:
    # Dictionary-based user class for fallback storage
    class User(UserMixin):
        def __init__(self, id, username, email, password_hash, created_at=None):
            self.id = id
            self.username = username
            self.email = email
            self.password_hash = password_hash
            self.created_at = created_at or datetime.utcnow()
        
        @staticmethod
        def query_by_username(username):
            for user_data in users_dict.values():
                if user_data['username'] == username:
                    return User(**user_data)
            return None
        
        @staticmethod
        def query_by_email(email):
            for user_data in users_dict.values():
                if user_data['email'] == email:
                    return User(**user_data)
            return None
        
        @staticmethod
        def query_by_username_or_email(identifier):
            for user_data in users_dict.values():
                if user_data['username'] == identifier or user_data['email'] == identifier:
                    return User(**user_data)
            return None
        
        def save(self):
            global user_id_counter
            if not hasattr(self, 'id') or self.id is None:
                self.id = user_id_counter
                user_id_counter += 1
            
            users_dict[self.id] = {
                'id': self.id,
                'username': self.username,
                'email': self.email,
                'password_hash': self.password_hash,
                'created_at': self.created_at
            }
            return True
else:
    # SQLAlchemy database model
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(120), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        @staticmethod
        def query_by_username_or_email(identifier):
            return User.query.filter(
                (User.username == identifier) | (User.email == identifier)
            ).first()

@login_manager.user_loader
def load_user(user_id):
    if USE_DICT_STORAGE:
        user_data = users_dict.get(int(user_id))
        if user_data:
            return User(**user_data)
        return None
    else:
        return User.query.get(int(user_id))

# Import your model function (with error handling)
try:
    from model import predict_loan_default
    print("✅ ML model imported successfully")
except ImportError as e:
    print(f"⚠️ Model import error: {e}")
    # Create a mock function as fallback
    def predict_loan_default(input_data):
        print("⚠️ Using mock prediction function (fallback)")
        # Extract values safely from DataFrame
        if hasattr(input_data, 'iloc'):
            # It's a DataFrame
            loan_amount = float(input_data.iloc[0].get('LoanAmount', 10000))
            annual_income = float(input_data.iloc[0].get('AnnualIncome', 50000))
            interest_rate = float(input_data.iloc[0].get('InterestRate', 7.5))
        else:
            # Fallback to dict access
            loan_amount = 10000
            annual_income = 50000
            interest_rate = 7.5

        # Simple risk calculation
        risk_score = (loan_amount / annual_income) * 0.4 + (interest_rate / 10) * 0.3
        risk_score = max(0.1, min(0.9, risk_score))  # Keep between 0.1-0.9

        prediction = 1 if risk_score > 0.5 else 0

        if risk_score > 0.7:
            risk_level = "High"
        elif risk_score > 0.4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        return prediction, risk_score, risk_level

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if username and password:
            # Support both username and email login
            user = User.query_by_username_or_email(username)
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=remember)
                flash('Welcome back, {}!'.format(user.username), 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash('Invalid username/email or password', 'error')
        else:
            flash('Please provide both username/email and password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([username, email, password, confirm_password]):
            flash('Please fill in all fields', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        elif User.query_by_username(username) if USE_DICT_STORAGE else User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        elif User.query_by_email(email) if USE_DICT_STORAGE else User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
        else:
            if USE_DICT_STORAGE:
                new_user = User(
                    id=None,
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                try:
                    new_user.save()
                    flash('Registration successful! Please login.', 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    flash('Error creating account. Please try again.', 'error')
                    print(f"Registration error: {e}")
            else:
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    flash('Registration successful! Please login.', 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    db.session.rollback()
                    flash('Error creating account. Please try again.', 'error')
                    print(f"Registration error: {e}")
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/predict')
@login_required
def predict_page():
    """Display the loan prediction form - requires login"""
    return render_template('predict.html')

@app.route('/api/predict', methods=['POST'])
@login_required
def predict_api():
    """Handle prediction API requests - requires login"""
    try:
        data = request.get_json()
        print("📩 Received data:", data)

        input_data = pd.DataFrame([data])
        prediction, probability, risk_level = predict_loan_default(input_data)
        
        return jsonify({
            'prediction': int(prediction),
            'probability': float(probability),
            'risk_level': risk_level,
            'status': 'success'
        })

    except Exception as e:
        print("❌ Error in prediction:", str(e))
        return jsonify({
            'error': 'Internal server error',
            'status': 'error',
            'note': 'Please check your input values'
        }), 500

@app.route('/api/auth-status')
def auth_status():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email
            }
        })
    else:
        return jsonify({'authenticated': False})

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': '✅ Server is running'})

# Create database tables
def init_db():
    with app.app_context():
        if USE_DICT_STORAGE:
            print("✅ Using dictionary storage for users")
        else:
            # Create all tables
            db.create_all()
            print("✅ Database tables created")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)