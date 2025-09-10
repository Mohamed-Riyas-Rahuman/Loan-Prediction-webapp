'''from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from model import predict_loan_default  # We'll create this next

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from the request
        data = request.get_json()
        print("Received data:", data)
        
        # Convert to DataFrame for processing
        input_data = pd.DataFrame([data])
        
        # Get prediction
        prediction, probability, risk_level = predict_loan_default(input_data)
        print(f"Prediction: {prediction}, Probability: {probability}, Risk Level: {risk_level}")
        
        return jsonify({
            'prediction': int(prediction),
            'probability': float(probability),
            'risk_level': risk_level,
            'status': 'success'
        })
        
    except Exception as e:
        print("Error in prediction:", str(e))
        return jsonify({'error': str(e), 'status': 'error'})

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # For cross-origin requests
import pandas as pd
import numpy as np
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Import your model function (with error handling)
try:
    from model import predict_loan_default
    print("✅ ML model imported successfully")
except ImportError as e:
    print(f"⚠️ Model import error: {e}")
    # Create a mock function as fallback
    def predict_loan_default(input_data):
        print("⚠️ Using mock prediction function (fallback)")
        loan_amount = input_data.get('LoanAmount', [10000])[0] if hasattr(input_data, 'get') else 10000
        annual_income = input_data.get('AnnualIncome', [50000])[0] if hasattr(input_data, 'get') else 50000
        interest_rate = input_data.get('InterestRate', [7.5])[0] if hasattr(input_data, 'get') else 7.5

        # Simple risk calculation
        risk_score = (loan_amount / annual_income) * 0.4 + (interest_rate / 10) * 0.3
        risk_score = max(0, min(1, risk_score))

        prediction = 1 if risk_score > 0.5 else 0

        if risk_score > 0.7:
            risk_level = "High"
        elif risk_score > 0.4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        return prediction, risk_score, risk_level


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from the request
        data = request.get_json()
        print("📩 Received data:", data)

        # Convert to DataFrame for processing
        input_data = pd.DataFrame([data])

        # Get prediction
        prediction, probability, risk_level = predict_loan_default(input_data)
        print(f"✅ Prediction: {prediction}, Probability: {probability}, Risk Level: {risk_level}")

        return jsonify({
            'prediction': int(prediction),
            'probability': float(probability),
            'risk_level': risk_level,
            'status': 'success'
        })

    except Exception as e:
        print("❌ Error in prediction:", str(e))
        # Return a mock response instead of error
        try:
            # Try to extract values from request
            loan_amount = data.get('LoanAmount', 10000)
            annual_income = data.get('AnnualIncome', 50000)

            # Simple fallback calculation
            risk_score = (loan_amount / annual_income) * 0.4
            risk_score = max(0, min(1, risk_score))

            return jsonify({
                'prediction': 1 if risk_score > 0.5 else 0,
                'probability': float(risk_score),
                'risk_level': 'High' if risk_score > 0.7 else 'Medium' if risk_score > 0.4 else 'Low',
                'status': 'success',
                'note': '⚠️ Using fallback calculation'
            })
        except:
            return jsonify({
                'error': str(e),
                'status': 'error',
                'note': 'Please check your input values'
            })


# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': '✅ Server is running'})


if __name__ == '__main__':
    # Use Render's port environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run in production mode (debug=False)
    app.run(host='0.0.0.0', port=port, debug=False)
'''  
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS  # For cross-origin requests
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app)  # Enable CORS for all routes
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

@login_manager.user_loader
def load_user(user_id):
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
        loan_amount = input_data.get('LoanAmount', [10000])[0] if hasattr(input_data, 'get') else 10000
        annual_income = input_data.get('AnnualIncome', [50000])[0] if hasattr(input_data, 'get') else 50000
        interest_rate = input_data.get('InterestRate', [7.5])[0] if hasattr(input_data, 'get') else 7.5

        # Simple risk calculation
        risk_score = (loan_amount / annual_income) * 0.4 + (interest_rate / 10) * 0.3
        risk_score = max(0, min(1, risk_score))

        prediction = 1 if risk_score > 0.5 else 0

        if risk_score > 0.7:
            risk_level = "High"
        elif risk_score > 0.4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        return prediction, risk_score, risk_level

# Create database tables and admin user
with app.app_context():
    db.create_all()
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@loanapp.com',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created: admin / admin123")

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        else:
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

# Protected routes
@app.route('/dashboard')
@login_required
def dashboard():
    user_count = User.query.count()
    return render_template('dashboard.html', user=current_user, user_count=user_count)

@app.route('/')
def home():
    return render_template('index.html', user=current_user)

@app.route('/predict', methods=['POST'])
@login_required  # Require login for predictions
def predict():
    try:
        # Get data from the request
        data = request.get_json()
        print("📩 Received data:", data)

        # Convert to DataFrame for processing
        input_data = pd.DataFrame([data])

        # Get prediction
        prediction, probability, risk_level = predict_loan_default(input_data)
        print(f"✅ Prediction: {prediction}, Probability: {probability}, Risk Level: {risk_level}")

        return jsonify({
            'prediction': int(prediction),
            'probability': float(probability),
            'risk_level': risk_level,
            'status': 'success'
        })

    except Exception as e:
        print("❌ Error in prediction:", str(e))
        # Return a mock response instead of error
        try:
            # Try to extract values from request
            loan_amount = data.get('LoanAmount', 10000)
            annual_income = data.get('AnnualIncome', 50000)

            # Simple fallback calculation
            risk_score = (loan_amount / annual_income) * 0.4
            risk_score = max(0, min(1, risk_score))

            return jsonify({
                'prediction': 1 if risk_score > 0.5 else 0,
                'probability': float(risk_score),
                'risk_level': 'High' if risk_score > 0.7 else 'Medium' if risk_score > 0.4 else 'Low',
                'status': 'success',
                'note': '⚠️ Using fallback calculation'
            })
        except:
            return jsonify({
                'error': str(e),
                'status': 'error',
                'note': 'Please check your input values'
            })

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': '✅ Server is running'})

if __name__ == '__main__':
    # Use Render's port environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run in production mode (debug=False)
    app.run(host='0.0.0.0', port=port, debug=False)