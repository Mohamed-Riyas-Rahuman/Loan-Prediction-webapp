// Loan Prediction System - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Flash message auto-hide
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            if (message.parentNode) {
                message.remove();
            }
        }, 5000);
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            // Add any additional form validation logic here
        });
    });

    // Initialize tooltips if using Bootstrap tooltips
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Prediction Form Handling
    const predictionForm = document.getElementById('predictionForm');
    if (predictionForm) {
        predictionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Elements to control display
            const submitBtn = this.querySelector('button[type="submit"]');
            const loadingIndicator = document.getElementById('loadingIndicator');
            const predictionResult = document.getElementById('predictionResult');
            
            // Show loading state and hide results
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Predicting...';
            submitBtn.disabled = true;
            
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (predictionResult) predictionResult.style.display = 'none';
            
            // Get form data - using exact field names from HTML form
            const formData = {
                LoanAmount: parseFloat(document.getElementById('LoanAmount').value),
                EmploymentLength: parseFloat(document.getElementById('EmploymentLength').value),
                FicoScore: parseFloat(document.getElementById('FicoScore').value),
                InterestRate: parseFloat(document.getElementById('InterestRate').value),
                AnnualIncome: parseFloat(document.getElementById('AnnualIncome').value),
                OpenAccounts: parseFloat(document.getElementById('OpenAccounts').value),
                DebtToIncomeRatio: parseFloat(document.getElementById('DebtToIncomeRatio').value),
                Term: document.getElementById('Term').value,
                HomeOwnership: document.getElementById('HomeOwnership').value
            };
            
            // Log the data being sent (for debugging)
            console.log('Sending prediction data:', formData);
            
            // Make API request to the endpoint
            // NOTE: The endpoint is '/api/predict' in the Flask app, not '/predict_loan' 
            fetch('/api/predict', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.error || `HTTP error! status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Prediction response:', data);
                
                if (data.status === 'success') {
                    // Display prediction result
                    displayResult(data, formData);
                } else {
                    throw new Error(data.error || 'Prediction failed');
                }
            })
            .catch(error => {
                console.error('Prediction error:', error);
                displayError(error.message);
            })
            .finally(() => {
                // Restore button state and hide loading
                submitBtn.innerHTML = '<i class="fas fa-calculator me-2"></i>Predict Loan Risk';
                submitBtn.disabled = false;
                if (loadingIndicator) loadingIndicator.style.display = 'none';
            });
        });
    }

    // Display result function
    function displayResult(result, formData) {
        const resultBox = document.getElementById('resultBox');
        if (!resultBox) return;
        
        resultBox.style.display = 'block';
        
        // Ensure we have valid values
        const riskPercent = (result.probability * 100).toFixed(1);
        const riskLevel = result.risk_level || "Unknown";
        
        let resultHTML;
        if (riskLevel.includes("High")) {
            resultHTML = `<h4 class="text-danger"><i class="fas fa-exclamation-triangle me-2"></i>High Risk: ${riskPercent}%</h4>
                        <p>This loan application shows a high risk of default based on our analysis.</p>
                        <div class="progress my-3">
                        <div class="progress-bar bg-danger" role="progressbar" style="width: ${riskPercent}%;" 
                                aria-valuenow="${riskPercent}" aria-valuemin="0" aria-valuemax="100">${riskPercent}%</div>
                        </div>
                        ${provideRiskFeedback(formData)}
                        <p class="mt-3"><strong>Recommendation:</strong> Reject application or require significant collateral</p>`;
            resultBox.className = 'result-box alert alert-danger';
        } else if (riskLevel.includes("Medium")) {
            resultHTML = `<h4 class="text-warning"><i class="fas fa-exclamation-circle me-2"></i>Medium Risk: ${riskPercent}%</h4>
                        <p>This loan application shows a moderate risk of default.</p>
                        <div class="progress my-3">
                        <div class="progress-bar bg-warning" role="progressbar" style="width: ${riskPercent}%;" 
                                aria-valuenow="${riskPercent}" aria-valuemin="0" aria-valuemax="100">${riskPercent}%</div>
                        </div>
                        ${provideRiskFeedback(formData)}
                        <p class="mt-3"><strong>Recommendation:</strong> Proceed with caution - consider additional guarantees</p>`;
            resultBox.className = 'result-box alert alert-warning';
        } else {
            resultHTML = `<h4 class="text-success"><i class="fas fa-check-circle me-2"></i>Low Risk: ${riskPercent}%</h4>
                        <p>This loan application shows a low risk of default.</p>
                        <div class="progress my-3">
                        <div class="progress-bar bg-success" role="progressbar" style="width: ${riskPercent}%;" 
                                aria-valuenow="${riskPercent}" aria-valuemin="0" aria-valuemax="100">${riskPercent}%</div>
                        </div>
                        ${provideRiskFeedback(formData)}
                        <p class="mt-3"><strong>Recommendation:</strong> Approve application</p>`;
            resultBox.className = 'result-box alert alert-success';
        }
        
        resultBox.innerHTML = resultHTML;
        
        // Scroll to result
        resultBox.scrollIntoView({ behavior: 'smooth' });
    }

    // Display error function
    function displayError(message) {
        const resultBox = document.getElementById('resultBox');
        if (!resultBox) return;
        
        resultBox.style.display = 'block';
        resultBox.className = 'result-box alert alert-danger';
        resultBox.innerHTML = `<h4 class="text-danger"><i class="fas fa-times-circle me-2"></i>Error</h4>
                             <p>${message}</p>
                             <p>Please check your input values and try again.</p>`;
        
        // Scroll to result
        resultBox.scrollIntoView({ behavior: 'smooth' });
    }

    // Risk feedback function
    function provideRiskFeedback(formData) {
        const feedback = [];
        const loanToIncome = formData.LoanAmount / formData.AnnualIncome;
        
        if (loanToIncome > 4) {
            feedback.push("Your loan amount is very high relative to your income");
        } else if (loanToIncome > 2.5) {
            feedback.push("Your loan amount is high relative to your income");
        }
        
        if (formData.DebtToIncomeRatio > 43) {
            feedback.push("Your debt-to-income ratio is above recommended levels");
        } else if (formData.DebtToIncomeRatio > 36) {
            feedback.push("Your debt-to-income ratio is elevated");
        }
        
        if (formData.InterestRate > 12) {
            feedback.push("Your interest rate is quite high");
        }
        
        if (formData.FicoScore < 650) {
            feedback.push("Your credit score is below ideal range");
        }
        
        if (formData.EmploymentLength < 2) {
            feedback.push("Your employment history is relatively short");
        }
        
        if (formData.OpenAccounts > 10) {
            feedback.push("You have many open credit accounts");
        }
        
        if (feedback.length > 0) {
            return `<div class="mt-3">
                <h5><i class="fas fa-chart-bar me-2"></i>Key Factors:</h5>
                <ul class="text-start">
                    ${feedback.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>`;
        }
        
        return `<div class="mt-3">
            <h5><i class="fas fa-chart-bar me-2"></i>Key Factors:</h5>
            <p>Your financial profile shows good indicators for loan approval.</p>
        </div>`;
    }
});