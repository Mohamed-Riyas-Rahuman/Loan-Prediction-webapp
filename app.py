from flask import Flask, render_template, request, jsonify
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