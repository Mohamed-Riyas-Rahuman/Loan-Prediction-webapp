import pandas as pd
import numpy as np
import joblib
import os
import pickle
import numpy as np

# Load your pre-trained model and preprocessing pipeline
try:
    # Try to load your actual trained model
    model = joblib.load('models/loan_default_model.pkl')
    preprocessor = joblib.load('models/preprocessor.pkl')
    feature_names = joblib.load('models/feature_names.pkl')
    print("Successfully loaded trained model and preprocessor")
    MODEL_LOADED = True
except Exception as e:
    # Fall back to mock implementation if model files aren't available
    model = None
    preprocessor = None
    feature_names = None
    print(f"Using mock implementation: {e}")
    MODEL_LOADED = False

def predict_loan_default(input_data):
    """
    Predict loan default probability using the trained model
    
    Parameters:
    input_data (DataFrame): Input data with features for prediction
    
    Returns:
    tuple: (prediction, probability, risk_level)
    """
    
    # If we have a trained model, use it for prediction
    if MODEL_LOADED:
        try:
            # Ensure the input data has all required columns
            input_data = ensure_columns(input_data)
            
            # Preprocess the input data (same as during training)
            if preprocessor is not None:
                processed_data = preprocessor.transform(input_data)
            else:
                processed_data = input_data
            
            # Make prediction
            if model is not None:
                prediction = model.predict(processed_data)
                probability = model.predict_proba(processed_data)[0][1]  # Probability of default (class 1)
            else:
                return mock_prediction(input_data)
            
            # Determine risk level based on probability
            risk_level = determine_risk_level(probability)
            
            return prediction[0], probability, risk_level
            
        except Exception as e:
            print(f"Error in model prediction: {e}")
            # Fall back to mock implementation if there's an error
            return mock_prediction(input_data)
    
    else:
        # Use mock implementation if no trained model is available
        return mock_prediction(input_data)

def ensure_columns(input_data):
    """
    Ensure the input data has all required columns
    Add missing columns with default values if necessary
    """
    if not feature_names:
        return input_data
    
    # Get all expected columns from the preprocessor
    all_columns = []
    all_columns.extend(feature_names.get('numeric_cols', []))
    all_columns.extend(feature_names.get('low_card_cat', []))
    all_columns.extend(feature_names.get('high_card_cat', []))
    
    # Add missing columns with default values
    for col in all_columns:
        if col not in input_data.columns:
            # Use appropriate default values based on column type
            if col in feature_names.get('numeric_cols', []):
                input_data[col] = 0  # Default for numeric columns
            else:
                input_data[col] = 0  # Default for categorical columns
    
    # Reorder columns to match training data
    if all_columns:
        input_data = input_data.reindex(columns=all_columns, fill_value=0)
    
    return input_data

def determine_risk_level(probability):
    """Determine risk level based on probability"""
    if probability > 0.7:
        return "High"
    elif probability > 0.4:
        return "Medium"
    else:
        return "Low"

def mock_prediction(input_data):
    """
    Improved mock prediction function with more realistic risk assessment
    """
    try:
        # Extract values from input data with defaults - handle DataFrame case
        if hasattr(input_data, 'iloc'):
            # It's a DataFrame
            row = input_data.iloc[0]
            loan_amount = float(row.get('LoanAmount', 10000))
            annual_income = float(row.get('AnnualIncome', 50000))
            interest_rate = float(row.get('InterestRate', 7.5))
            dti = float(row.get('DebtToIncomeRatio', 20))
            emp_length = float(row.get('EmploymentLength', 5))
            fico = float(row.get('FicoScore', 700))
        else:
            # Fallback defaults
            loan_amount = 10000.0
            annual_income = 50000.0
            interest_rate = 7.5
            dti = 20.0
            emp_length = 5.0
            fico = 700.0
        
        # Calculate key ratios with more nuanced approach
        loan_to_income = loan_amount / annual_income
        # Normalize this ratio (typical acceptable range is up to 3-4x income for mortgages)
        loan_to_income_factor = min(loan_to_income / 4, 1.0) * 0.25
        
        # Debt-to-income ratio factor (should be under 0.43 for most loans)
        dti_factor = min(dti / 43, 1.0) * 0.25
        
        # Interest rate factor (higher rates are riskier)
        interest_factor = min(interest_rate / 15, 1.0) * 0.15
        
        # Employment stability factor (longer employment is better)
        employment_factor = (1 - min(emp_length / 10, 1.0)) * 0.15
        
        # Credit score factor (higher FICO is better)
        fico_factor = (1 - min((fico - 300) / 550, 1.0)) * 0.20
        
        # Calculate overall risk score
        risk_score = (
            loan_to_income_factor +
            dti_factor + 
            interest_factor +
            employment_factor +
            fico_factor
        )
        
        # Ensure risk score is between 0 and 1
        risk_score = max(0, min(1, risk_score))
        
        # Determine prediction and risk level
        prediction = 1 if risk_score > 0.5 else 0  # 1 = default, 0 = no default
        probability = risk_score
        
        if risk_score > 0.7:
            risk_level = "High"
        elif risk_score > 0.4:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        return prediction, probability, risk_level
        
    except Exception as e:
        print(f"Error in mock prediction: {e}")
        # Fallback to simple calculation if something goes wrong
        loan_amount = 10000.0
        annual_income = 50000.0
        interest_rate = 7.5
        dti = 20.0
        
        risk_score = (loan_amount / annual_income) * 0.4 + (dti / 100) * 0.3 + (interest_rate / 10) * 0.3
        risk_score = max(0, min(1, risk_score))
        prediction = 1 if risk_score > 0.5 else 0
        probability = risk_score
        risk_level = "High" if risk_score > 0.7 else "Medium" if risk_score > 0.4 else "Low"
        return prediction, probability, risk_level

# Test function to verify model loading
def test_model_loading():
    """Test if the model loaded correctly"""
    if MODEL_LOADED:
        print("✓ Model loaded successfully")
        print(f"✓ Model type: {type(model).__name__}")
        print(f"✓ Preprocessor type: {type(preprocessor).__name__}")
        return True
    else:
        print("✗ Model not loaded - using mock implementation")
        return False

# Run test when module is imported
test_model_loading()