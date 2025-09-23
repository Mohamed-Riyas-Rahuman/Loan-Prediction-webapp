// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing app...");
    
    // Initialize tooltips
    const tooltipElements = document.querySelectorAll('.tooltip-icon');
    tooltipElements.forEach(el => {
        el.addEventListener('mouseenter', showTooltip);
        el.addEventListener('mouseleave', hideTooltip);
    });
    
    // Initialize charts
    initializeCharts();
    
    // Initialize feature importance visualization
    initializeFeatureImportance();
    
    // Form submission handler (only if form exists)
    const predictionForm = document.getElementById('predictionForm');
    if (predictionForm) {
        predictionForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log("Form submitted");
        
        // Show loading indicator
        document.getElementById('loadingIndicator').style.display = 'block';
        document.getElementById('predictionResult').style.display = 'none';
        
        // Get form values
        const formData = {
            LoanAmount: parseFloat(document.getElementById('loanAmount').value),
            InterestRate: parseFloat(document.getElementById('interestRate').value),
            Term: document.getElementById('term').value,
            EmploymentLength: parseFloat(document.getElementById('empLength').value),
            AnnualIncome: parseFloat(document.getElementById('annualIncome').value),
            DebtToIncomeRatio: parseFloat(document.getElementById('dti').value),
            FicoScore: document.getElementById('fico') ? parseFloat(document.getElementById('fico').value) : 700,
            OpenAccounts: document.getElementById('openAccounts') ? parseFloat(document.getElementById('openAccounts').value) : 5,
            HomeOwnership: document.getElementById('homeOwnership') ? document.getElementById('homeOwnership').value : 'MORTGAGE'
        };
        
        console.log("Form data:", formData);
        
        try {
            // Validate form data
            if (!validateFormData(formData)) {
                throw new Error('Please check your input values. All fields are required.');
            }
            
            // Make API call to Flask backend
            console.log("Making API call to /api/predict");
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            console.log("Response status:", response.status);
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const result = await response.json();
            console.log("Server response:", result);
            
            if (result.status === 'success') {
                console.log("Success response, displaying result");
                displayResult(result, formData);
            } else {
                throw new Error(result.error || 'Unknown error occurred');
            }
            
        } catch (error) {
            console.error("Error occurred:", error);
            displayError(error.message);
        } finally {
            // Hide loading indicator
            document.getElementById('loadingIndicator').style.display = 'none';
        }
        });
    }
    
    // Add input validation as users type
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', validateNumberInput);
    });
});

// Tooltip functions
function showTooltip(e) {
    const tooltipText = e.target.getAttribute('title');
    if (!tooltipText) return;
    
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.innerHTML = tooltipText;
    tooltip.style.position = 'absolute';
    tooltip.style.background = 'rgba(44, 62, 80, 0.9)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '8px 12px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '14px';
    tooltip.style.zIndex = '1000';
    tooltip.style.maxWidth = '250px';
    
    // Position tooltip
    const rect = e.target.getBoundingClientRect();
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
    
    document.body.appendChild(tooltip);
    e.target.setAttribute('data-original-title', tooltipText);
    e.target.removeAttribute('title');
}

function hideTooltip(e) {
    const tooltips = document.querySelectorAll('.custom-tooltip');
    tooltips.forEach(tooltip => tooltip.remove());
    
    // Restore title attribute for next time
    const tooltipText = e.target.getAttribute('data-original-title');
    if (tooltipText) {
        e.target.setAttribute('title', tooltipText);
    }
}

// Chart functions
function initializeCharts() {
    // Distribution Chart
    const distCtx = document.getElementById('distributionChart');
    if (distCtx) {
        const distChart = new Chart(distCtx, {
            type: 'doughnut',
            data: {
                labels: ['Non-Default', 'Default'],
                datasets: [{
                    label: 'Number of Loans',
                    data: [32000, 8000],
                    backgroundColor: ['#4ca1af', '#2c3e50'],
                    borderWidth: 0,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw.toLocaleString()} (${((context.raw/40000)*100).toFixed(1)}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Correlation Chart
    const corrCtx = document.getElementById('correlationChart');
    if (corrCtx) {
        const corrChart = new Chart(corrCtx, {
            type: 'bar',
            data: {
                labels: ['Income', 'Loan Amount', 'Interest Rate', 'Term', 'Employment', 'FICO Score'],
                datasets: [{
                    label: 'Correlation with Default',
                    data: [-0.32, 0.45, 0.67, 0.21, -0.29, -0.58],
                    backgroundColor: '#4ca1af',
                    borderWidth: 0,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        min: -1,
                        title: {
                            display: true,
                            text: 'Correlation Coefficient'
                        }
                    }
                }
            }
        });
    }
}

// Feature importance visualization
function initializeFeatureImportance() {
    const features = [
        {name: 'Interest Rate', importance: 0.92},
        {name: 'Debt-to-Income Ratio', importance: 0.87},
        {name: 'Annual Income', importance: 0.78},
        {name: 'FICO Score', importance: 0.76},
        {name: 'Loan Amount', importance: 0.75},
        {name: 'Employment Length', importance: 0.68},
        {name: 'Number of Open Accounts', importance: 0.62},
        {name: 'Home Ownership', importance: 0.55},
        {name: 'Loan Term', importance: 0.48},
        {name: 'Years of Credit History', importance: 0.38}
    ];

    const featureContainer = document.getElementById('featureImportance');
    if (featureContainer) {
        features.forEach(feature => {
            const barDiv = document.createElement('div');
            barDiv.className = 'feature-importance-bar';
            barDiv.style.width = `${feature.importance * 100}%`;
            barDiv.innerHTML = `<span>${feature.name} (${feature.importance.toFixed(2)})</span>`;
            featureContainer.appendChild(barDiv);
        });
    }
}

// Form validation functions
function validateFormData(formData) {
    console.log("Validating form data:", formData);
    // Basic validation - check if required fields have values
    return formData.LoanAmount && formData.AnnualIncome && 
           formData.InterestRate && formData.DebtToIncomeRatio;
}

function validateNumberInput(e) {
    const input = e.target;
    const min = parseFloat(input.min) || 0;
    const max = parseFloat(input.max) || Infinity;
    const value = parseFloat(input.value);
    
    if (isNaN(value) || value < min || value > max) {
        input.classList.add('is-invalid');
    } else {
        input.classList.remove('is-invalid');
    }
}

// provideRiskFeedback function
function provideRiskFeedback(formData) {
    console.log("Generating feedback for form data:", formData);
    
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
    
    console.log("Generated feedback items:", feedback);
    
    if (feedback.length > 0) {
        return `<div class="mt-3">
            <h5>Key Factors:</h5>
            <ul class="text-start">
                ${feedback.map(item => `<li>${item}</li>`).join('')}
            </ul>
        </div>`;
    }
    
    return `<div class="mt-3">
        <h5>Key Factors:</h5>
        <p>Your financial profile shows good indicators for loan approval.</p>
    </div>`;
}

// displayResult function
function displayResult(result, formData) {
    console.log("Displaying result:", result);
    console.log("Form data passed to displayResult:", formData);
    
    const resultBox = document.getElementById('predictionResult');
    if (!resultBox) {
        console.error("Result box element not found!");
        return;
    }
    
    resultBox.style.display = 'block';
    
    // Ensure we have valid values
    const riskPercent = (result.probability * 100).toFixed(1);
    const predictionText = result.prediction === 1 ? "High Default Risk" : "Low Default Risk";
    
    console.log("Risk percent:", riskPercent);
    console.log("Prediction text:", predictionText);
    
    // Get feedback - check if formData is valid
    let feedback = '';
    if (formData && typeof formData === 'object' && formData.LoanAmount) {
        feedback = provideRiskFeedback(formData);
        console.log("Feedback HTML:", feedback);
    } else {
        console.error("FormData is invalid or missing:", formData);
        feedback = `<div class="mt-3">
            <h5>Key Factors:</h5>
            <p>Unable to provide detailed feedback due to missing form data.</p>
        </div>`;
    }
    
    // Determine risk level if not provided by server
     let riskLevel = (result.risk_level || '').toString().toLowerCase();
     if (!riskLevel) {
    riskLevel = riskPercent > 70 ? "high" : riskPercent > 40 ? "medium" : "low";
      }

   let resultHTML;
   if (riskLevel.includes("high")) {
        resultHTML = `<h4 class="text-danger">${predictionText}: ${riskPercent}%</h4>
                      <p>This loan application shows a high risk of default based on our analysis.</p>
                      <div class="progress my-3">
                        <div class="progress-bar bg-danger" role="progressbar" style="width: ${riskPercent}%;" 
                             aria-valuenow="${riskPercent}" aria-valuemin="0" aria-valuemax="100">${riskPercent}%</div>
                      </div>
                      ${feedback}
                      <p class="mt-3">Recommendation: <strong>Reject application</strong> or require significant collateral</p>`;
        resultBox.className = 'result-box alert alert-danger';
    } else if (riskLevel.includes("medium")) {
        resultHTML = `<h4 class="text-warning">${predictionText}: ${riskPercent}%</h4>
                      <p>This loan application shows a moderate risk of default.</p>
                      <div class="progress my-3">
                        <div class="progress-bar bg-warning" role="progressbar" style="width: ${riskPercent}%;" 
                             aria-valuenow="${riskPercent}" aria-valuemin="0" aria-valuemax="100">${riskPercent}%</div>
                      </div>
                      ${feedback}
                      <p class="mt-3">Recommendation: <strong>Approve with higher interest rate</strong> or require collateral</p>`;
        resultBox.className = 'result-box alert alert-warning';
    } else {
        resultHTML = `<h4 class="text-success">${predictionText}: ${riskPercent}%</h4>
                      <p>This loan application shows a low risk of default.</p>
                      <div class="progress my-3">
                        <div class="progress-bar bg-success" role="progressbar" style="width: ${riskPercent}%;" 
                             aria-valuenow="${riskPercent}" aria-valuemin="0" aria-valuemax="100">${riskPercent}%</div>
                      </div>
                      ${feedback}
                      <p class="mt-3">Recommendation: <strong>Approve application</strong> with standard terms</p>`;
        resultBox.className = 'result-box alert alert-success';
    }
    
    console.log("Final HTML to display:", resultHTML);
    resultBox.innerHTML = resultHTML;
    
    // Animate the progress bar
    animateProgressBar();
}

function animateProgressBar() {
    const progressBar = document.querySelector('.progress-bar');
    if (!progressBar) {
        console.error("Progress bar element not found!");
        return;
    }
    
    const width = progressBar.style.width;
    progressBar.style.width = '0%';
    
    setTimeout(() => {
        progressBar.style.transition = 'width 1s ease-in-out';
        progressBar.style.width = width;
    }, 100);
}

function displayError(error) {
    console.error("Displaying error:", error);
    const resultBox = document.getElementById('predictionResult');
    if (!resultBox) {
        console.error("Result box element not found for error display!");
        return;
    }
    
    resultBox.style.display = 'block';
    resultBox.innerHTML = `<h4 class="text-danger">Error</h4>
                          <p>${error}</p>
                          <p>Please check your inputs and try again.</p>`;
    resultBox.className = 'result-box alert alert-danger';
}

// Utility function to format numbers with commas
function formatNumber(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}