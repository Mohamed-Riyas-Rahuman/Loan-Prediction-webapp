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
import os
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Secret key
secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SECRET_KEY'] = secret_key

# Flask-Mail config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))

# Database config
database_url = os.environ.get('DATABASE_URL', 'sqlite:///loan_prediction.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions
CORS(app, origins=["*"], supports_credentials=False)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# =======================
# Forms
# =======================
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

# =======================
# Models
# =======================
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

# =======================
# Helper functions
# =======================
def send_password_reset_email(user):
    try:
        token = serializer.dumps(user.email, salt='password-reset-salt')
        reset_url = url_for('reset_password', token=token, _external=True)
        flash(f'Password reset link: {reset_url}', 'info')

        if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
            msg = Message(
                'Password Reset Request',
                recipients=[user.email],
                sender="Loan Predictor <riyasss035@gmail.com>",
                body=f"Hello {user.username},\nClick here to reset: {reset_url}"
            )
            mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def verify_reset_token(token, expiration=3600):
    try:
        return serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None

def predict_loan_default(input_data):
    # Mock function
    loan_amount = float(input_data.iloc[0].get('LoanAmount', 10000))
    annual_income = float(input_data.iloc[0].get('AnnualIncome', 50000))
    interest_rate = float(input_data.iloc[0].get('InterestRate', 7.5))
    risk_score = (loan_amount / annual_income) * 0.4 + (interest_rate / 10) * 0.3
    risk_score = max(0.1, min(0.9, risk_score))
    prediction = 1 if risk_score > 0.5 else 0
    if risk_score > 0.7:
        risk_level = "High"
    elif risk_score > 0.4:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    return prediction, risk_score, risk_level

# =======================
# Routes
# =======================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query_by_username_or_email(form.username.data)
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
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
        if User.query_by_username(form.username.data):
            flash('Username already exists', 'error')
        elif User.query_by_email(form.email.data):
            flash('Email already exists', 'error')
        else:
            user = User(username=form.username.data,
                        email=form.email.data,
                        password_hash=generate_password_hash(form.password.data))
            db.session.add(user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query_by_email(form.email.data)
        flash('If an account with that email exists, a reset link has been sent.', 'info')
        if user:
            send_password_reset_email(user)
        return redirect(url_for('login'))
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired link.', 'error')
        return redirect(url_for('forgot_password'))
    user = User.query_by_email(email)
    if not user:
        flash('Invalid reset link.', 'error')
        return redirect(url_for('forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.update_password(generate_password_hash(form.password.data))
        flash('Password reset successful.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

# GET page for prediction form
@app.route('/predict')
@login_required
def predict_page():
    return render_template('predict.html')

# POST API for predictions
@app.route('/api/predict', methods=['POST'])
@login_required
def predict_api():
    try:
        data = request.get_json()
        input_df = pd.DataFrame([data])
        prediction, probability, risk_level = predict_loan_default(input_df)
        return jsonify({
            'prediction': int(prediction),
            'probability': float(probability),
            'risk_level': risk_level,
            'status': 'success'
        })
    except Exception as e:
        print("Prediction error:", e)
        return jsonify({'error': 'Internal server error', 'status': 'error'}), 500

# Static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Server running'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    db.create_all()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
