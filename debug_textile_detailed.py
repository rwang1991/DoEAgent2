import pandas as pd

# Load and examine the textile dataset
df = pd.read_csv('sample_doe_data.csv', encoding='utf-8')

print("Dataset shape:", df.shape)
print("\nFirst 5 rows:")
print(df.head())

print("\nColumn names and types:")
for col in df.columns:
    print(f"{col}: {df[col].dtype}, unique values: {df[col].nunique()}")

print("\nLooking for process factor columns:")
process_factors = ['dye1', 'dye2', 'Temp', 'Time', 'Na2SO4 (g/L)', 'Dyeing pH']
for factor in process_factors:
    if factor in df.columns:
        print(f"Found {factor}: type={df[factor].dtype}, unique={df[factor].nunique()}, sample values={df[factor].unique()[:5]}")
    else:
        print(f"Missing: {factor}")

print("\nNumeric columns (excluding response DE*cmc):")
numeric_cols = [col for col in df.columns 
               if df[col].dtype in ['int64', 'float64'] 
               and col != 'DE*cmc'
               and df[col].nunique() > 1]
print(f"Found {len(numeric_cols)} numeric columns:")
for col in numeric_cols:
    print(f"  {col}: unique values = {df[col].nunique()}")
