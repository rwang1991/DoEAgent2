#!/usr/bin/env python3
"""
Test the DOE function with pharmaceutical formulation data
"""

import json
import requests

# Test data from the user's request
pharma_data = """Ingredient_A,Ingredient_B,Mix_Time,Temperature,Dissolution,Hardness,Content_Uniformity
10,5,15,25,78.5,45.2,98.7
20,5,15,25,82.1,47.8,99.1
10,15,15,25,79.8,44.6,98.9
20,15,15,25,85.3,49.2,99.4
10,5,30,25,81.2,46.1,99.0
20,5,30,25,84.7,48.9,99.3
10,15,30,25,82.6,45.8,99.2
20,15,30,25,87.9,50.5,99.6
10,5,15,40,77.3,43.8,98.5
20,5,15,40,80.9,46.5,98.9
10,15,15,40,78.1,43.2,98.7
20,15,15,40,83.4,47.1,99.2
10,5,30,40,79.7,44.9,98.8
20,5,30,40,83.2,47.6,99.1
10,15,30,40,80.4,44.3,99.0
20,15,30,40,86.1,49.8,99.5"""

# Test payload exactly as AI Foundry would send it
test_payload = {
    "data": pharma_data,
    "response_column": "Dissolution,Hardness,Content_Uniformity",
    "force_full_dataset": True,
    "threshold": 1.5
}

print("Testing pharmaceutical formulation data...")
print("="*60)
print("Payload:")
print(json.dumps(test_payload, indent=2))
print("="*60)

# Test locally by importing the function
try:
    import sys
    sys.path.append(r'c:\Users\ruwang\source\repos\Temp\DoE\DoeAnalysis')
    from DoeAnalysis import main
    
    # Create a mock request object
    class MockRequest:
        def get_json(self):
            return test_payload
    
    # Test the function
    mock_req = MockRequest()
    result = main(mock_req)
    
    print("Function Response:")
    print(f"Status Code: {result.status_code}")
    print("Response Body:")
    response_data = json.loads(result.get_body())
    print(json.dumps(response_data, indent=2, default=str))
    
except Exception as e:
    print(f"Local test failed: {e}")
    print("\nTrying remote test...")
    
    # Test remote endpoint
    try:
        url = "https://func-rui-test-doe-westus-e8fjc0c7cthbhzbg.westus-01.azurewebsites.net/api/doeanalysis"
        response = requests.post(url, json=test_payload, timeout=60)
        
        print(f"Remote Response Status: {response.status_code}")
        print("Remote Response Body:")
        print(json.dumps(response.json(), indent=2, default=str))
        
    except Exception as remote_error:
        print(f"Remote test also failed: {remote_error}")
