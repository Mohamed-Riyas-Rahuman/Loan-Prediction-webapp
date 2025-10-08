from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from sqlalchemy import text
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Load environment variables
load_dotenv()  

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Security
secret_key = os.environ.get('SESSION_SECRET')
if not secret_key:
    if os.environ.get('FLASK_ENV') == 'production':
        raise RuntimeError("SESSION_SECRET environment variable must be set in production")
    else:
        secret_key = 'dev-secret-key-change-in-production'
        print("⚠️ Using development secret key")

app.config['SECRET_KEY'] = secret_key

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))

# Database configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///loan_prediction.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app, origins=["*"], supports_credentials=False)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
mail = Mail(app)

# Password reset serializer
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# ================================
# Forms
# ================================
class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

# ================================
# Database Model
# ================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def query_by_username_or_email(identifier):
        return User.query.filter((User.username == identifier) | (User.email == identifier)).first()

    @staticmethod
    def query_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def query_by_username(username):
        return User.query.filter_by(username=username).first()

    def update_password(self, new_password_hash):
        self.password_hash = new_password_hash
        db.session.commit()
        return True

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================================
# Password Reset Helpers
# ================================
def send_password_reset_email(user):
    """Send password reset email (or fallback to console/flash)."""
    try:
        token = serializer.dumps(user.email, salt='password-reset-salt')
        reset_url = url_for('reset_password', token=token, _external=True)

        # Print to console for debugging
        print(f"🔗 Password reset URL for {user.email}: {reset_url}")

        # If email not configured, show link in flash message
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            print("⚠️ Email not configured - reset link shown in flash message")
            flash(f'Password reset link: {reset_url}', 'info')
            return True

        # FIXED: Use the configured sender - now using loanpredictorapp@gmail.com
        msg = Message(
            'Password Reset Request - Loan Prediction System',
            recipients=[user.email],
            sender=app.config['MAIL_DEFAULT_SENDER'],  # ← FIXED: Now uses loanpredictorapp@gmail.com
            body=f"""
Hello {user.username},

You requested a password reset for your Loan Prediction System account.

Click the following link to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you did not request this reset, please ignore this email.

Best regards,
Loan Predictor Team
            """.strip()
        )
        mail.send(msg)
        print(f"✅ Email sent to {user.email}")
        flash('Password reset email has been sent!', 'success')  # ADDED: Success feedback
        return True

    except Exception as e:
        print(f"❌ Error sending reset email: {e}")
        # Still show the link in flash message as fallback
        flash(f'Error sending email. Reset link: {reset_url}', 'error')
        return False

def verify_reset_token(token, expiration=3600):
    try:
        return serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None

# ================================
# Database connection
# ================================
def check_database_connection():
    try:
        db.session.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Database connection failed: {e}")
        return False

def init_db():
    with app.app_context():
        if check_database_connection():
            try:
                db.create_all()
                print("✅ Database tables created")
            except Exception as e:
                print(f"❌ Error creating tables: {e}")
        else:
            print("❌ Cannot create tables - database connection failed")

# Email configuration debug
def check_email_config():
    if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
        print("✅ Email configuration found")
        print(f"📧 Mail server: {app.config.get('MAIL_SERVER')}")
        print(f"📧 Username: {app.config.get('MAIL_USERNAME')}")
        print(f"📧 Sender: {app.config.get('MAIL_DEFAULT_SENDER')}")
    else:
        print("❌ Email not configured - using console fallback")

# ================================
# ML Prediction Function
# ================================
def predict_loan_default(input_data):
    """Enhanced prediction function with multiple factors"""
    print("🎯 Running loan default prediction")
    
    try:
        # Extract values safely
        if isinstance(input_data, dict):
            loan_amount = float(input_data.get('LoanAmount', 10000))
            annual_income = float(input_data.get('AnnualIncome', 50000))
            interest_rate = float(input_data.get('InterestRate', 7.5))
            employment_length = float(input_data.get('EmploymentLength', 5))
            fico_score = float(input_data.get('FicoScore', 700))
            dti_ratio = float(input_data.get('DebtToIncomeRatio', 25.0))
            open_accounts = float(input_data.get('OpenAccounts', 5))
            term = int(input_data.get('Term', 36))
        else:
            # Default values if data structure is unexpected
            loan_amount = 10000
            annual_income = 50000
            interest_rate = 7.5
            employment_length = 5
            fico_score = 700
            dti_ratio = 25.0
            open_accounts = 5
            term = 36

        # Advanced risk calculation with multiple factors
        loan_to_income = loan_amount / annual_income
        fico_factor = (850 - fico_score) / 550  # Normalize FICO score (300-850)
        employment_factor = max(0, 1 - (employment_length / 10))  # More employment = better
        dti_factor = min(1, dti_ratio / 50)  # DTI above 50% is high risk
        interest_factor = interest_rate / 30  # Interest rate impact
        accounts_factor = min(1, open_accounts / 20)  # Too many accounts = risk
        
        # Weighted risk score
        risk_score = (
            loan_to_income * 0.25 +
            fico_factor * 0.20 +
            dti_factor * 0.20 +
            interest_factor * 0.15 +
            employment_factor * 0.10 +
            accounts_factor * 0.10
        )
        
        # Normalize risk score between 0.1 and 0.9
        risk_score = max(0.1, min(0.9, risk_score))
        
        # Determine prediction (1 = default, 0 = no default)
        prediction = 1 if risk_score > 0.5 else 0
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = "High"
        elif risk_score > 0.4:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        print(f"🎯 Prediction result: {prediction}, Probability: {risk_score:.3f}, Risk: {risk_level}")
        
        return prediction, risk_score, risk_level

    except Exception as e:
        print(f"❌ Prediction error: {e}")
        # Return safe default values
        return 0, 0.3, "Low"

# ================================
# Routes
# ================================
@app.route('/')
def home():
    print("🏠 Home page accessed - User:", current_user.is_authenticated)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        
        # Support both username and email login
        user = User.query_by_username_or_email(username)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash('Welcome back, {}!'.format(user.username), 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid username/email or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        print("✅ Form validation successful")  # DEBUG
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        # Check if username or email already exists
        if User.query_by_username(username):
            flash('Username already exists', 'error')
            print("❌ Username exists")  # DEBUG
        elif User.query_by_email(email):
            flash('Email already exists', 'error')
            print("❌ Email exists")  # DEBUG
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
                print("✅ User created, redirecting to login")  # DEBUG
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('Error creating account. Please try again.', 'error')
                print(f"❌ Registration error: {e}")
    else:
        print("❌ Form validation failed:", form.errors)  # DEBUG
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        email = form.email.data
        user = User.query_by_email(email)  
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        if user:
            send_password_reset_email(user)
    return render_template('forgot_password.html', form=form) 

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset link. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))
    
    user = User.query_by_email(email)
    if not user:
        flash('Invalid reset link.', 'error')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        new_password_hash = generate_password_hash(form.password.data)
        
        try:
            user.update_password(new_password_hash)
            flash('Your password has been reset successfully. Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Error updating password. Please try again.', 'error')
            print(f"Password reset error: {e}")
    
    return render_template('reset_password.html', form=form)

# ================================
# PREDICTION ROUTES - FIXED
# ================================
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    """Main prediction endpoint"""
    try:
        data = request.get_json()
        print("🎯 Prediction request received from user:", current_user.username)
        print("📊 Prediction data:", data)
        
        # Validate required fields
        required_fields = ['LoanAmount', 'AnnualIncome', 'InterestRate', 'FicoScore']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'status': 'error'
                }), 400
        
        # Perform prediction
        prediction, probability, risk_level = predict_loan_default(data)
        
        response_data = {
            'prediction': int(prediction),
            'probability': float(probability),
            'risk_level': risk_level,
            'status': 'success',
            'message': f'Prediction completed: {risk_level} risk'
        }
        
        print("✅ Prediction response:", response_data)
        return jsonify(response_data)

    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return jsonify({
            'error': 'Prediction failed. Please check your input values.',
            'status': 'error'
        }), 500

@app.route('/api/predict', methods=['POST'])
@login_required
def predict_api():
    """Alternative prediction endpoint for API consistency"""
    return predict()

@app.route('/predict-page')
@login_required
def predict_page():
    """Prediction page route"""
    return render_template('index.html')

# ================================
# Utility Routes
# ================================
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

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(app.static_folder, 'favicon.ico')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': '✅ Server is running'})

# ================================
# Error Handlers - SIMPLIFIED
# ================================
@app.errorhandler(404)
def not_found_error(error):
    return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500

@app.errorhandler(Exception)
def handle_exception(error):
    return "An error occurred", 500

# ================================
# Main
# ================================
if __name__ == '__main__':
    check_email_config()  # Added email debug
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)