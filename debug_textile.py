#!/usr/bin/env python3
"""
Debug the textile dataset issue
"""

import json
import requests

textile_payload = {
    "data": "https://raw.githubusercontent.com/rwang1991/DoEAgent/refs/heads/main/DOEData_20250622.csv",
    "response_column": "DE*cmc",
    "force_full_dataset": True,
    "threshold": 1.5
}

url = "https://func-rui-test-doe-westus-e8fjc0c7cthbhzbg.westus-01.azurewebsites.net/api/doeanalysis"

try:
    response = requests.post(url, json=textile_payload, timeout=60)
    result = response.json()
    
    print("Debug Textile Dataset Response:")
    print("="*50)
    print(f"Status: {response.status_code}")
    print(f"Models returned: {list(result.get('models', {}).keys())}")
    print(f"Data info: {result.get('data_info', {})}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    
    # Check if the response column is correctly parsed
    response_vars = result.get('data_info', {}).get('response_variables', [])
    print(f"Response variables parsed: {response_vars}")
    
    # Check predictors
    predictors = result.get('data_info', {}).get('predictors_used', [])
    print(f"Predictors used: {predictors}")
    
except Exception as e:
    print(f"Error: {e}")
