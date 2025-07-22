# Large DOE Dataset Example - Your Actual Data

## Dataset Overview
- **File**: DOEData_20250622.csv
- **Size**: 298 rows × 65 columns (~211 KB)
- **Type**: Color/dyeing process optimization experiment
- **Memory**: 211.5 KB (manageable but benefits from cloud storage)

## Key Variables Identified

### Response Variables (Color measurements):
- `Lvalue`, `Avalue`, `Bvalue` - Primary color coordinates
- `L.F2_avg1,2`, `A.F2_avg1,2`, `B.F2_avg1,2` - Averaged measurements
- `Gloss_avg1,2` - Gloss measurements
- `DE*cmc` - Color difference metric

### Predictor Variables (Process factors):
- `dye1` - Dye 1 concentration (3 levels)
- `dye2` - Dye 2 concentration (3 levels) 
- `Temp` - Temperature (3 levels)
- `Time` - Process time (3 levels)
- `Dyeing pH` - pH level (constant at 6.8)
- `Na2SO4 (g/L)` - Salt concentration (constant at 1)

## Recommended Approach for This Dataset

### Option 1: Direct Analysis (Small-Medium Size)
Since your dataset is 298 rows, it's in the manageable range for direct analysis:

```json
{
  "data": "base64_encoded_data_or_url",
  "response_vars": ["Lvalue", "Avalue", "Bvalue"],
  "predictors": ["dye1", "dye2", "Temp", "Time"],
  "max_rows": 500,
  "force_full_dataset": true
}
```

### Option 2: Cloud Storage (Recommended)
Upload to cloud storage for better performance and token efficiency:

```json
{
  "data": "https://your-storage.blob.core.windows.net/data/DOEData_20250622.csv",
  "response_vars": ["Lvalue", "Avalue", "Bvalue", "DE*cmc"],
  "predictors": ["dye1", "dye2", "Temp", "Time"],
  "max_rows": 300
}
```

## AI Foundry Prompt Examples for Your Data

### Prompt 1: Comprehensive Color Optimization
```
I have a textile dyeing DOE dataset with 298 experimental runs. Please analyze this data to optimize our color matching process:

Response variables: Lvalue, Avalue, Bvalue, DE*cmc
Process factors: dye1, dye2, Temp, Time

Key questions:
1. Which factors most significantly affect each color coordinate?
2. Are there interaction effects between dye concentrations and process conditions?
3. What process settings minimize color variation (DE*cmc)?
4. How can we achieve target color values while maintaining consistency?

The dataset includes multiple measurements per condition, so the analysis should be robust.
```

### Prompt 2: Process Troubleshooting
```
Our dyeing process is showing high color variation. I have experimental data from 298 runs with different factor combinations:

[Provide your data via URL or base64]

Factors tested: dye1, dye2, Temp, Time
Quality metrics: Lvalue, Avalue, Bvalue, Gloss_avg1,2, DE*cmc

Please help identify:
1. Primary sources of color variation
2. Which factor combinations lead to poor color consistency?
3. Optimal factor settings for stable color production
4. Whether there are any problematic factor interactions

Focus on minimizing DE*cmc (color difference) while maintaining target L, A, B values.
```

### Prompt 3: Focused Analysis on Color Coordinates
```
I need to optimize a textile dyeing process specifically for color accuracy. My DOE data has 298 experiments with varying:

- dye1 concentration (3 levels)
- dye2 concentration (3 levels)
- Temperature (3 levels)
- Time (3 levels)

Target: Minimize color difference while achieving specific L*a*b* color coordinates.

Please analyze the effects on:
1. Lvalue (lightness) - target around 45-50
2. Avalue (red-green) - target around 5-8
3. Bvalue (yellow-blue) - target around 15-20
4. DE*cmc (overall color difference) - minimize

What process conditions would you recommend for consistent color matching?
```

## Expected Analysis Results

Given your dataset structure, the analysis should reveal:

### Factor Significance
- **dye1 & dye2**: Likely primary drivers of color coordinates
- **Temperature**: May affect dye uptake and final color
- **Time**: Could influence color development and uniformity
- **Interactions**: dye1:dye2, dye1:Temp, etc.

### Model Quality
- **R² values**: Expected 0.85-0.95 for well-controlled DOE
- **RMSE**: Should be low for color coordinates
- **Significant effects**: 8-12 terms including interactions

### Optimization Insights
- **Desirability functions**: For multi-response optimization
- **Robust settings**: Factor combinations with low variation
- **Trade-offs**: Between color accuracy and process efficiency

## Implementation Strategy

### Phase 1: Upload to Cloud Storage
```bash
# Upload to Azure Blob Storage
az storage blob upload \
  --account-name yourstorageaccount \
  --container-name doedata \
  --name DOEData_20250622.csv \
  --file DOEData_20250622.csv \
  --auth-mode login
```

### Phase 2: Test with AI Foundry
Use the comprehensive prompt above with your cloud storage URL.

### Phase 3: Iterate Based on Results
- Refine factor ranges based on significance
- Focus on key interactions
- Validate with confirmation runs

## Performance Expectations

- **Processing time**: 15-30 seconds (full dataset)
- **Memory usage**: ~15-20 MB during analysis
- **Token consumption**: ~2000-3000 tokens (with URL)
- **Model quality**: High (controlled experimental design)

## Alternative Analysis Scenarios

### Scenario 1: Quick Screening (Sampled Analysis)
```json
{
  "max_rows": 150,
  "force_full_dataset": false
}
```
→ Fast screening of main effects

### Scenario 2: Detailed Modeling (Full Dataset)
```json
{
  "max_rows": 500, 
  "force_full_dataset": true
}
```
→ Comprehensive analysis with all interactions

### Scenario 3: Response-Specific Analysis
Analyze each color coordinate separately for focused insights.

## Key Benefits for Your Dataset

1. **Perfect size**: Not too large, not too small for DOE analysis
2. **Rich factor space**: 3^4 design allows interaction detection  
3. **Multiple responses**: Comprehensive color characterization
4. **Controlled experiment**: Clean data with minimal noise
5. **Practical application**: Direct process optimization insights

Your dataset is an excellent candidate for both base64 encoding and cloud storage approaches, with cloud storage being recommended for better AI Foundry integration.
