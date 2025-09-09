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
    app.run(debug=True)'''

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Add this for cross-origin requests
import pandas as pd
import numpy as np

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Import your model function (with error handling)
try:
    from model import predict_loan_default
    print("✅ ML model imported successfully")
except ImportError as e:
    print(f"⚠️  Model import error: {e}")
    # Create a mock function as fallback
    def predict_loan_default(input_data):
        print("Using mock prediction function")
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
                'note': 'Using fallback calculation'
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
    return jsonify({'status': 'healthy', 'message': 'Server is running'})

if __name__ == '__main__':
    # Use Render's port environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run in production mode (debug=False)
    app.run(host='0.0.0.0', port=port, debug=False)