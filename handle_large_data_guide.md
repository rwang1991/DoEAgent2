# Handling Large DOE Data Files - Best Practices Guide

## Current File Size Analysis
- **DOEData_20250622.csv**: 104,390 bytes (~104KB)
- **Base64 encoded**: ~139KB (33% increase)
- **Status**: Manageable but approaching limits

## Problem: Why Large Files Are Challenging

### 1. Azure Functions Limits
- **Request body limit**: 100MB (we're safe)
- **Execution timeout**: 5-10 minutes (risk for very large datasets)
- **Memory limit**: 1.5GB (risk with large datasets)

### 2. AI Foundry Limits
- **Token limits**: Large base64 strings consume many tokens
- **Request timeouts**: Large requests may timeout
- **Processing efficiency**: Base64 encoding is inefficient

### 3. Performance Issues
- **Network transfer**: Large base64 strings slow down requests
- **Memory usage**: Decoding + processing uses 2-3x memory
- **Analysis time**: More data = longer processing time

## Solution 1: Cloud Storage Integration (Recommended)

### A. Azure Blob Storage with SAS Tokens
```python
# Enhanced function to support Azure Blob with SAS
def get_data_from_source(data_input):
    if data_input.startswith('https://') and 'blob.core.windows.net' in data_input:
        # Azure Blob Storage URL with SAS token
        return pd.read_csv(data_input)
    elif data_input.startswith('http'):
        # Generic HTTP URL
        return pd.read_csv(data_input)
    else:
        # Base64 encoded data (fallback for small files)
        csv_data = base64.b64decode(data_input).decode('utf-8')
        return pd.read_csv(StringIO(csv_data))
```

### B. SharePoint Direct Download (Current Implementation)
✅ **Already implemented** - SharePoint URLs work with direct download links

### C. GitHub Raw Files
```python
# Example: https://raw.githubusercontent.com/username/repo/main/data.csv
if 'github.com' in data_input or 'githubusercontent.com' in data_input:
    return pd.read_csv(data_input)
```

## Solution 2: Data Preprocessing and Sampling

### A. Intelligent Sampling for Large Datasets
```python
def smart_sample_large_dataset(df, max_rows=1000):
    """
    Intelligently sample large datasets while preserving DOE structure
    """
    if len(df) <= max_rows:
        return df
    
    # For DOE data, try to preserve experimental design structure
    # Sample proportionally from each factor combination if possible
    if len(df.columns) <= 10:  # Reasonable number of factors
        try:
            # Group by factor combinations and sample proportionally
            factor_cols = [col for col in df.columns if df[col].dtype in ['object', 'category'] or df[col].nunique() <= 10]
            if factor_cols:
                return df.groupby(factor_cols).apply(lambda x: x.sample(min(len(x), max_rows // df.groupby(factor_cols).ngroups))).reset_index(drop=True)
        except:
            pass
    
    # Fallback: random sampling
    return df.sample(n=max_rows, random_state=42)
```

### B. Progressive Analysis
```python
def progressive_doe_analysis(df, response_vars, predictors, max_initial_rows=500):
    """
    Start with smaller sample, then expand if needed
    """
    if len(df) > max_initial_rows:
        # Start with sample
        sample_df = smart_sample_large_dataset(df, max_initial_rows)
        initial_result = perform_doe_analysis(sample_df, response_vars, predictors)
        
        # If initial analysis is successful and shows clear patterns, use full dataset
        if initial_result and any(model.get('summary_of_fit', {}).get('RSquare', 0) > 0.8 for model in initial_result.get('models', {}).values()):
            return perform_doe_analysis(df, response_vars, predictors)
        else:
            return initial_result
    else:
        return perform_doe_analysis(df, response_vars, predictors)
```

## Solution 3: Chunked Processing

### For Very Large Datasets (>10MB)
```python
def chunked_doe_analysis(df, response_vars, predictors, chunk_size=1000):
    """
    Process large datasets in chunks and combine results
    """
    if len(df) <= chunk_size:
        return perform_doe_analysis(df, response_vars, predictors)
    
    chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
    chunk_results = []
    
    for chunk in chunks:
        try:
            result = perform_doe_analysis(chunk, response_vars, predictors)
            if result:
                chunk_results.append(result)
        except Exception as e:
            logging.warning(f"Chunk analysis failed: {e}")
    
    # Combine results (implementation depends on requirements)
    return combine_doe_results(chunk_results)
```

## Solution 4: File Format Optimization

### A. Compressed CSV
```python
import gzip
import io

def handle_compressed_data(data_input):
    if data_input.endswith('.gz'):
        # Handle gzipped CSV files
        response = requests.get(data_input)
        with gzip.open(io.BytesIO(response.content), 'rt') as f:
            return pd.read_csv(f)
```

### B. Parquet Format (Most Efficient)
```python
def handle_parquet_data(data_input):
    if data_input.endswith('.parquet'):
        return pd.read_parquet(data_input)
```

## Solution 5: Enhanced Error Handling and Limits

```python
def validate_dataset_size(df, max_rows=10000, max_memory_mb=100):
    """
    Validate dataset size and provide recommendations
    """
    memory_usage = df.memory_usage(deep=True).sum() / (1024**2)  # MB
    
    if len(df) > max_rows:
        return {
            "status": "warning",
            "message": f"Dataset has {len(df)} rows. Consider sampling for faster analysis.",
            "recommendation": "Use sampling or cloud storage URL"
        }
    
    if memory_usage > max_memory_mb:
        return {
            "status": "error", 
            "message": f"Dataset uses {memory_usage:.1f}MB memory. Too large for processing.",
            "recommendation": "Use smaller sample or optimize data types"
        }
    
    return {"status": "ok"}
```

## Recommended Implementation Strategy

### Phase 1: Enhanced URL Support (Immediate)
1. ✅ SharePoint direct download (already implemented)
2. Add Azure Blob Storage with SAS tokens
3. Add GitHub raw file support
4. Add compressed file support

### Phase 2: Smart Sampling (Next)
1. Implement intelligent sampling for large datasets
2. Add dataset size validation
3. Progressive analysis based on initial results

### Phase 3: Advanced Features (Future)
1. Chunked processing for very large datasets
2. Parquet format support
3. Streaming analysis for real-time data

## AI Foundry Integration Recommendations

### For Large Files in AI Foundry:

1. **Use Cloud URLs** instead of base64 encoding:
```
Instead of: "data": "base64_encoded_massive_string..."
Use: "data": "https://your-storage.blob.core.windows.net/data/doe_data.csv?sas_token"
```

2. **Provide sampling options** in prompts:
```
For large datasets (>1000 rows), I can:
1. Analyze a representative sample for quick insights
2. Use the full dataset for comprehensive analysis
3. Focus on specific factor ranges

Which approach would you prefer?
```

3. **Guide users on data preparation**:
```
For best performance with large DOE datasets:
- Upload to cloud storage (Azure Blob, SharePoint, GitHub)
- Use direct download URLs
- Consider data sampling for exploratory analysis
- Compress files when possible (.gz format)
```

## Current File Assessment

Your **DOEData_20250622.csv** (104KB) is:
- ✅ **Manageable** with current implementation
- ✅ **Works** with base64 encoding
- ✅ **Better** with cloud storage URL
- ⚠️ **Near the limit** for base64 in AI Foundry prompts

## Next Steps

1. **Immediate**: Use SharePoint or Azure Blob for your large file
2. **Short-term**: Implement smart sampling for datasets >1000 rows  
3. **Long-term**: Add support for compressed formats and chunked processing
