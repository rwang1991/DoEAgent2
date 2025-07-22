import requests
import pandas as pd
from io import StringIO

# Download and examine the actual dataset used in the test
url = "https://raw.githubusercontent.com/rwang1991/DoEAgent/refs/heads/main/DOEData_20250622.csv"
response = requests.get(url)
df = pd.read_csv(StringIO(response.text))

print("Dataset shape:", df.shape)
print("\nColumns and their types:")
for col in df.columns[:20]:  # Show first 20 columns
    print(f"{col}: {df[col].dtype}, unique values: {df[col].nunique()}")

print("\nLooking for process factor columns...")
process_factors = ['dye1', 'dye2', 'Temp', 'Time', 'Na2SO4 (g/L)', 'Dyeing pH']
for factor in process_factors:
    if factor in df.columns:
        print(f"✓ Found {factor}: type={df[factor].dtype}, unique={df[factor].nunique()}")
        print(f"  Sample values: {sorted(df[factor].unique())[:10]}")
    else:
        print(f"✗ Missing: {factor}")

print("\nPotential predictors (numeric, >1 unique values, not response):")
numeric_cols = [col for col in df.columns 
               if df[col].dtype in ['int64', 'float64'] 
               and col != 'DE*cmc'
               and df[col].nunique() > 1]

print(f"Found {len(numeric_cols)} potential predictors:")
for i, col in enumerate(numeric_cols[:15]):  # Show first 15
    print(f"  {i+1:2d}. {col}: {df[col].nunique()} unique values")
