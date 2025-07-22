# DOE Analysis Azure Function

This Azure Function provides a REST API for Design of Experiments (DOE) analysis, compatible with AI Foundry integration.

## Overview

The function performs comprehensive DOE analysis including:
- Response Surface Methodology (RSM) modeling
- Factor effect screening with LogWorth analysis
- Model simplification with hierarchical term preservation
- JMP-style diagnostic outputs
- Lack of fit analysis
- Coded and uncoded parameter estimates

## API Endpoint

**POST** `/api/DoeAnalysis`

### Request Format

```json
{
  "data": "base64_encoded_csv_data_or_url",
  "response_vars": ["Lvalue", "Avalue", "Bvalue"],
  "predictors": ["dye1", "dye2", "Time", "Temp"],
  "threshold": 1.3,
  "min_significant": 2
}
```

### Parameters

- `data`: Base64 encoded CSV data or URL to CSV file
- `response_vars`: Array of response variable column names
- `predictors`: Array of predictor variable column names  
- `threshold`: LogWorth threshold for factor significance (default: 1.3)
- `min_significant`: Minimum number of responses where factor must be significant (default: 2)

### Response Format

```json
{
  "summary": {
    "full_model_effects": [...],
    "simplified_factors": [...],
    "condition_number": 12.34,
    "simplified_model_effects": [...],
    "parameters": {...}
  },
  "models": {
    "Lvalue": {
      "summary_of_fit": {
        "r_squared": 0.95,
        "adjusted_r_squared": 0.94,
        "rmse": 0.123,
        "mean_response": 45.6,
        "observations": 30
      },
      "anova_table": [...],
      "coded_parameters": {...},
      "uncoded_parameters": [...],
      "lack_of_fit": {...},
      "residuals": {...}
    }
  }
}
```

## Local Development

1. Install Azure Functions Core Tools
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run locally:
   ```bash
   func start
   ```

## Deployment to Azure

1. Create Azure Function App with Python runtime
2. Deploy using Azure Functions Core Tools:
   ```bash
   func azure functionapp publish <function-app-name>
   ```

## AI Foundry Integration

This function is designed to work with AI Foundry as a custom skill. The structured JSON response format allows AI Foundry to:

1. Parse and understand DOE analysis results
2. Make recommendations based on factor significance
3. Generate insights about model quality and fit
4. Provide optimization suggestions

### Sample AI Foundry Usage

```python
import requests
import base64
import json

# Prepare your data
with open('doe_data.csv', 'rb') as f:
    csv_data = base64.b64encode(f.read()).decode('utf-8')

# Call the function
response = requests.post(
    'https://your-function-app.azurewebsites.net/api/DoeAnalysis',
    json={
        'data': csv_data,
        'response_vars': ['Lvalue', 'Avalue', 'Bvalue'],
        'predictors': ['dye1', 'dye2', 'Time', 'Temp']
    },
    headers={'x-functions-key': 'your-function-key'}
)

results = response.json()
```

## Data Format Requirements

CSV data should have columns matching the specified predictors and response variables:

```csv
dye1,dye2,Time,Temp,Lvalue,Avalue,Bvalue
1.0,2.0,30,150,45.2,12.3,8.7
1.5,2.5,35,160,47.1,13.1,9.2
...
```

## Error Handling

The function returns appropriate HTTP status codes:
- 200: Success
- 400: Bad request (missing data, invalid format, missing columns)
- 500: Internal server error

Error responses include descriptive error messages in JSON format.
