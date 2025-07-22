import logging
import json
import pandas as pd
import numpy as np
from itertools import combinations
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from sklearn.preprocessing import StandardScaler
from patsy import dmatrix
from statsmodels.stats.outliers_influence import OLSInfluence
from scipy.stats import f
import warnings
import base64
from io import StringIO
import azure.functions as func
import requests
import gzip
import io
from urllib.parse import urlparse

warnings.filterwarnings("ignore")

def validate_dataset_size(df, max_rows=5000, max_memory_mb=50):
    """
    Validate dataset size and provide recommendations
    """
    memory_usage = df.memory_usage(deep=True).sum() / (1024**2)  # MB
    
    if len(df) > max_rows:
        return {
            "status": "warning",
            "message": f"Dataset has {len(df)} rows. Consider sampling for faster analysis.",
            "recommendation": "Large dataset detected. Using intelligent sampling for optimal performance.",
            "original_rows": len(df),
            "memory_mb": round(memory_usage, 2)
        }
    
    if memory_usage > max_memory_mb:
        return {
            "status": "error", 
            "message": f"Dataset uses {memory_usage:.1f}MB memory. Too large for processing.",
            "recommendation": "Dataset too large. Please use a smaller sample or contact support."
        }
    
    return {
        "status": "ok", 
        "rows": len(df), 
        "memory_mb": round(memory_usage, 2)
    }

def smart_sample_large_dataset(df, max_rows=1000, preserve_structure=True):
    """
    Intelligently sample large datasets while preserving DOE structure
    """
    if len(df) <= max_rows:
        return df, False
    
    logging.info(f"Sampling large dataset: {len(df)} rows -> {max_rows} rows")
    
    if preserve_structure:
        # For DOE data, try to preserve experimental design structure
        try:
            # Identify potential factor columns (categorical or low-cardinality numeric)
            factor_cols = []
            for col in df.columns:
                if df[col].dtype == 'object' or df[col].dtype.name == 'category':
                    factor_cols.append(col)
                elif df[col].dtype in ['int64', 'float64'] and df[col].nunique() <= 20:
                    # Likely discrete factor levels
                    factor_cols.append(col)
            
            if factor_cols and len(factor_cols) <= 6:  # Reasonable number of factors
                # Group by factor combinations and sample proportionally
                groups = df.groupby(factor_cols)
                n_groups = groups.ngroups
                
                if n_groups > 0 and n_groups <= max_rows:
                    samples_per_group = max(1, max_rows // n_groups)
                    sampled_df = groups.apply(
                        lambda x: x.sample(min(len(x), samples_per_group), random_state=42)
                    ).reset_index(drop=True)
                    
                    if len(sampled_df) <= max_rows * 1.2:  # Allow 20% over-sampling
                        return sampled_df, True
        except Exception as e:
            logging.warning(f"Structured sampling failed: {e}")
    
    # Fallback: stratified random sampling
    try:
        # Try to stratify by response variables if they exist
        response_candidates = [col for col in df.columns if 'response' in col.lower() or 'yield' in col.lower() or 'quality' in col.lower()]
        if response_candidates:
            # Create quartiles for stratification
            stratify_col = response_candidates[0]
            df['_quartile'] = pd.qcut(df[stratify_col], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')
            sampled_df = df.groupby('_quartile').apply(
                lambda x: x.sample(min(len(x), max_rows // 4), random_state=42)
            ).reset_index(drop=True).drop('_quartile', axis=1)
            
            if len(sampled_df) > 0:
                return sampled_df, True
    except Exception as e:
        logging.warning(f"Stratified sampling failed: {e}")
    
    # Final fallback: simple random sampling
    sampled_df = df.sample(n=min(max_rows, len(df)), random_state=42)
    return sampled_df, True

def get_data_from_source(data_input, max_file_size_mb=10):
    """
    Enhanced data loading with support for multiple sources and formats
    Handles: URLs, base64, raw CSV text, and various file formats
    """
    try:
        # Check if input is a URL
        if data_input.startswith('http'):
            # URL-based input
            try:
                # Handle compressed files
                if data_input.endswith('.gz'):
                    response = requests.get(data_input, timeout=30)
                    response.raise_for_status()
                    
                    # Check file size
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > max_file_size_mb * 1024 * 1024:
                        raise ValueError(f"File too large: {int(content_length)/(1024*1024):.1f}MB > {max_file_size_mb}MB")
                    
                    with gzip.open(io.BytesIO(response.content), 'rt') as f:
                        return pd.read_csv(f)
                
                elif data_input.endswith('.parquet'):
                    # Parquet format support
                    return pd.read_parquet(data_input)
                
                else:
                    # Standard CSV from URL
                    response = requests.get(data_input, timeout=30)
                    response.raise_for_status()
                    
                    # Check file size
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > max_file_size_mb * 1024 * 1024:
                        raise ValueError(f"File too large: {int(content_length)/(1024*1024):.1f}MB > {max_file_size_mb}MB")
                    
                    return pd.read_csv(StringIO(response.text))
            
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to fetch data from URL: {str(e)}. Please ensure the URL is publicly accessible and returns CSV data.")
        
        # Check if input looks like base64 (no commas, headers, or newlines in first 100 chars)
        elif len(data_input) > 100 and ',' not in data_input[:100] and '\n' not in data_input[:100] and not data_input[:100].strip().lower().startswith(('temp', 'dye', 'time', 'pressure', 'yield')):
            # Likely base64 encoded CSV data
            try:
                # Check base64 string size (rough estimate)
                estimated_size_mb = len(data_input) * 0.75 / (1024 * 1024)  # Base64 is ~33% larger
                if estimated_size_mb > max_file_size_mb:
                    raise ValueError(f"Base64 data too large: ~{estimated_size_mb:.1f}MB > {max_file_size_mb}MB")
                
                csv_data = base64.b64decode(data_input).decode('utf-8')
                return pd.read_csv(StringIO(csv_data))
            except Exception as e:
                # If base64 decode fails, treat as raw CSV
                logging.warning(f"Base64 decode failed, treating as raw CSV: {str(e)}")
                return pd.read_csv(StringIO(data_input))
        
        else:
            # Assume raw CSV text data (from AI Foundry direct paste)
            try:
                # Check size
                estimated_size_mb = len(data_input.encode('utf-8')) / (1024 * 1024)
                if estimated_size_mb > max_file_size_mb:
                    raise ValueError(f"CSV data too large: {estimated_size_mb:.1f}MB > {max_file_size_mb}MB")
                
                return pd.read_csv(StringIO(data_input))
            except Exception as e:
                raise ValueError(f"Failed to parse CSV data: {str(e)}. Please ensure data is in valid CSV format.")
    
    except Exception as e:
        if "Failed to" in str(e):
            raise  # Re-raise our custom errors
        else:
            raise ValueError(f"Failed to load data: {str(e)}")
        

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Enhanced Azure Function for DOE (Design of Experiments) Analysis
    Supports large datasets with intelligent sampling and multiple data sources
    
    Expected JSON input (AI Foundry format):
    {
        "data": "github_url_or_base64_or_raw_csv",
        "response_column": "DE*cmc",
        "max_samples": 100
    }
    
    OR Legacy format:
    {
        "data": "base64_encoded_csv_data" or "http://url_to_csv_file",
        "response_vars": ["Lvalue", "Avalue", "Bvalue"],
        "predictors": ["dye1", "dye2", "Time", "Temp"],
        "threshold": 1.3,
        "min_significant": 2,
        "max_rows": 1000,
        "force_full_dataset": false
    }
    """
    
    logging.info('Enhanced DOE Analysis function triggered.')
    
    try:
        # Parse request
        req_body = req.get_json()
        if not req_body:
            logging.error("No JSON body provided")
            return func.HttpResponse(
                json.dumps({"error": "No JSON body provided. Please send data as JSON."}),
                status_code=400,
                mimetype="application/json"
            )
        
        logging.info(f"Request body keys: {list(req_body.keys())}")
        logging.info(f"Request size: {len(str(req_body))} characters")
        
        # Extract parameters with flexible format support
        data_input = req_body.get('data')
        
        # Support both new simplified format and legacy format
        if 'response_column' in req_body:
            # New simplified format (for AI Foundry)
            response_column = req_body.get('response_column', 'DE*cmc')
            # Handle multiple response variables in comma-separated format
            if ',' in response_column:
                response_vars = [col.strip() for col in response_column.split(',')]
            else:
                response_vars = [response_column]
            # Use auto-detection if no predictors specified
            predictors = req_body.get('predictors', None)  # Changed to None for auto-detection
            threshold = req_body.get('threshold', 1.3)
            min_significant = req_body.get('min_significant', 1)
            max_rows = req_body.get('max_samples', req_body.get('max_rows', 1000))
            force_full = req_body.get('force_full_dataset', False)
        else:
            # Legacy format (backward compatibility)
            response_vars = req_body.get('response_vars', ["Lvalue", "Avalue", "Bvalue"])
            predictors = req_body.get('predictors', ["dye1", "dye2", "Time", "Temp"])
            threshold = req_body.get('threshold', 1.3)
            min_significant = req_body.get('min_significant', 2)
            max_rows = req_body.get('max_rows', 1000)
            force_full = req_body.get('force_full_dataset', False)
        
        if not data_input:
            logging.error("No data provided in request")
            return func.HttpResponse(
                json.dumps({"error": "No data provided. Please include 'data' field with CSV content, URL, or base64 data."}),
                status_code=400,
                mimetype="application/json"
            )
        
        logging.info(f"Data input type: {'URL' if data_input.startswith('http') else 'CSV/Base64'}")
        logging.info(f"Data input size: {len(data_input)} characters")
        logging.info(f"Response vars: {response_vars}")
        logging.info(f"Predictors: {predictors}")
        
        # Load data with enhanced error handling
        try:
            df_raw = get_data_from_source(data_input)
            logging.info(f"Successfully loaded data: {len(df_raw)} rows, {len(df_raw.columns)} columns")
        except ValueError as e:
            return func.HttpResponse(
                json.dumps({"error": str(e)}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate dataset size
        size_validation = validate_dataset_size(df_raw)
        
        if size_validation["status"] == "error":
            return func.HttpResponse(
                json.dumps({"error": size_validation["message"], "recommendation": size_validation["recommendation"]}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Handle large datasets with intelligent sampling
        was_sampled = False
        sampling_info = {}
        
        if not force_full and len(df_raw) > max_rows:
            df_analysis, was_sampled = smart_sample_large_dataset(df_raw, max_rows)
            sampling_info = {
                "original_rows": len(df_raw),
                "sampled_rows": len(df_analysis),
                "sampling_method": "intelligent_sampling",
                "note": "Large dataset detected. Using representative sample for analysis."
            }
            logging.info(f"Applied sampling: {len(df_raw)} -> {len(df_analysis)} rows")
        else:
            df_analysis = df_raw
        # Auto-detect available predictors from the data if not specified
        if predictors is None:
            # Auto-detect all potential predictors (exclude response variables)
            # Prioritize known experimental factors over measurement columns
            all_numeric_cols = [col for col in df_analysis.columns 
                              if df_analysis[col].dtype in ['int64', 'float64'] 
                              and col not in response_vars 
                              and df_analysis[col].nunique() > 1]
            
            # Define exact process factor names for textile datasets
            textile_factors = ['dye1', 'dye2', 'Temp', 'Time']
            pharma_factors = ['Ingredient_A_mg', 'Ingredient_B_mg', 'Ingredient_C_mg', 'Ingredient_D_mg']
            
            # Check if this looks like a textile dataset
            found_textile_factors = [col for col in textile_factors if col in all_numeric_cols]
            found_pharma_factors = [col for col in pharma_factors if col in all_numeric_cols]
            
            if len(found_textile_factors) >= 3:  # Textile dataset
                available_predictors = found_textile_factors
                logging.info(f"Detected textile dataset, using factors: {available_predictors}")
            elif len(found_pharma_factors) >= 3:  # Pharma dataset
                available_predictors = found_pharma_factors
                logging.info(f"Detected pharma dataset, using factors: {available_predictors}")
            else:
                # General auto-detection with keyword prioritization
                factor_keywords = ['ingredient', 'mix', 'concentration', 'pressure', 'catalyst', 
                                 'speed', 'flow', 'rate', 'config']
                
                priority_predictors = []
                other_predictors = []
                
                for col in all_numeric_cols:
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in factor_keywords):
                        priority_predictors.append(col)
                    else:
                        other_predictors.append(col)
                
                # Use priority predictors first, then others if needed
                available_predictors = priority_predictors + other_predictors[:max(0, 8-len(priority_predictors))]
                logging.info(f"General auto-detection, using predictors: {available_predictors}")
        else:
            # Use specified predictors, but also check available ones for fallback
            available_predictors = [col for col in df_analysis.columns if col in predictors]
            if not available_predictors:
                # Fallback: try to identify numeric columns that could be predictors (exclude response variables)
                available_predictors = [col for col in df_analysis.columns 
                                      if df_analysis[col].dtype in ['int64', 'float64'] 
                                      and col not in response_vars 
                                      and df_analysis[col].nunique() > 1][:8]  # Increased limit for pharma data
        
        # Auto-map common AI Foundry column names to actual column names
        def map_ai_foundry_columns(pred_list, actual_columns):
            """Map AI Foundry generic names to actual column names"""
            mapped_predictors = []
            column_mapping = {
                "Dye Concentration": ["dye1", "dye2", "dye", "concentration"],
                "Temperature": ["Temp", "temperature", "temp"],
                "Time": ["Time", "time", "Mix_Time", "mix_time"],
                "pH": ["Dyeing pH", "pH", "ph"],
                "Pressure": ["Pressure", "pressure"],
                "Flow Rate": ["Flow", "flow_rate", "flowrate"],
                # Pharmaceutical formulation mappings
                "Ingredient A": ["Ingredient_A", "ingredient_a", "component_a"],
                "Ingredient B": ["Ingredient_B", "ingredient_b", "component_b"],
                "Mix Time": ["Mix_Time", "mix_time", "mixing_time"],
                "Mixing Time": ["Mix_Time", "mix_time", "mixing_time"]
            }
            
            for pred in pred_list:
                if pred in actual_columns:
                    # Direct match
                    mapped_predictors.append(pred)
                elif pred in column_mapping:
                    # Try to map AI Foundry name to actual columns
                    for candidate in column_mapping[pred]:
                        if candidate in actual_columns:
                            mapped_predictors.append(candidate)
                            logging.info(f"Mapped '{pred}' → '{candidate}'")
                            break
                    else:
                        logging.warning(f"Could not map AI Foundry column '{pred}' to any actual column")
                else:
                    logging.warning(f"Unknown predictor column: {pred}")
            
            return mapped_predictors
        
        # Apply AI Foundry column mapping
        if predictors is not None:
            mapped_predictors = map_ai_foundry_columns(predictors, df_analysis.columns)
        else:
            # Use all available predictors when none specified
            mapped_predictors = available_predictors
            logging.info(f"Auto-detected predictors: {mapped_predictors}")
        
        # Filter out constant predictors (no variation)
        variable_predictors = []
        for pred in mapped_predictors:
            if pred in df_analysis.columns:
                if df_analysis[pred].nunique() > 1:  # Has variation
                    variable_predictors.append(pred)
                else:
                    logging.warning(f"Skipping constant predictor: {pred} (only {df_analysis[pred].nunique()} unique value)")
        
        # If no variable predictors from specified list, auto-detect from available
        if not variable_predictors:
            for pred in available_predictors:
                if pred in df_analysis.columns and df_analysis[pred].nunique() > 1:
                    variable_predictors.append(pred)
        
        final_predictors = variable_predictors
        logging.info(f"Using predictors with variation: {final_predictors}")
        
        # Validate columns
        missing_response = [r for r in response_vars if r not in df_analysis.columns]
        if missing_response:
            return func.HttpResponse(
                json.dumps({"error": f"Missing response column(s): {missing_response}. Available columns: {list(df_analysis.columns)}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not final_predictors:
            return func.HttpResponse(
                json.dumps({"error": "No predictors with variation found in the data. All potential predictors appear to be constant."}),
                status_code=400,
                mimetype="application/json"
            )
        
        if len(final_predictors) < 2:
            return func.HttpResponse(
                json.dumps({"error": f"Insufficient predictors with variation: {final_predictors}. Need at least 2 variable predictors for modeling."}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Perform DOE analysis
        result = perform_doe_analysis(df_analysis, response_vars, final_predictors, threshold, min_significant)
        
        # Add metadata about data processing
        result["data_info"] = {
            "size_validation": size_validation,
            "was_sampled": was_sampled,
            "sampling_info": sampling_info if was_sampled else None,
            "analysis_rows": len(df_analysis),
            "analysis_columns": len(df_analysis.columns),
            "predictors_used": final_predictors,
            "response_variables": response_vars
        }
        
        return func.HttpResponse(
            json.dumps(result, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in DOE analysis: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

def perform_doe_analysis(df_raw, response_vars, predictors, threshold, min_significant):
    """Perform the DOE analysis and return structured results"""
    
    results = {
        "summary": {},
        "models": {},
        "diagnostics": {}
    }
    
    # Filter predictors to only those with variation
    variable_predictors = []
    for pred in predictors:
        if pred in df_raw.columns and df_raw[pred].nunique() > 1:
            variable_predictors.append(pred)
        else:
            logging.warning(f"Skipping predictor {pred}: not found or no variation")
    
    if len(variable_predictors) < 2:
        return {"error": f"Insufficient variable predictors. Found: {variable_predictors}. Need at least 2 for modeling."}
    
    # Standardize data
    scaler = StandardScaler()
    df = df_raw.copy()
    
    try:
        df[variable_predictors] = scaler.fit_transform(df[variable_predictors])
    except Exception as e:
        logging.error(f"Error in data standardization: {e}")
        return {"error": f"Data standardization failed: {str(e)}"}
    
    # Create RSM terms (simplified for limited data)
    def create_rsm_terms(terms):
        # Quote terms with special characters
        quoted_terms = [f"Q('{t}')" if '*' in t or ' ' in t or '(' in t else t for t in terms]
        
        if len(terms) <= 4:
            # For small number of predictors, use linear + interactions only
            linear = quoted_terms
            inter = [f"{a}:{b}" for a, b in combinations(quoted_terms, 2)]
            return linear + inter
        else:
            # Full RSM for larger designs
            linear = quoted_terms
            square = [f"I({t}**2)" for t in quoted_terms]
            inter = [f"{a}:{b}" for a, b in combinations(quoted_terms, 2)]
            return linear + square + inter
    
    rsm_terms = create_rsm_terms(variable_predictors)
    
    # Full model LogWorth scanning
    effect_summary_all = pd.DataFrame()
    for y in response_vars:
        try:
            # Use Q() to properly quote column names with special characters
            y_quoted = f"Q('{y}')" if '*' in y or ' ' in y or '(' in y else y
            predictor_terms = [f"Q('{term}')" if '*' in term or ' ' in term or '(' in term else term for term in rsm_terms]
            
            formula = f"{y_quoted} ~ " + " + ".join(predictor_terms)
            model = smf.ols(formula, data=df).fit()
            anova_tbl = anova_lm(model, typ=3).reset_index()
            anova_tbl = anova_tbl.rename(columns={"index": "Factor"})
            anova_tbl = anova_tbl[anova_tbl["Factor"] != "Residual"]
            anova_tbl["LogWorth"] = -np.log10(anova_tbl["PR(>F)"].replace(0, 1e-16))
            temp = anova_tbl[["Factor", "LogWorth"]].copy()
            temp.columns = ["Factor", y]
            effect_summary_all = pd.merge(effect_summary_all, temp, on="Factor", how="outer") if not effect_summary_all.empty else temp
        except Exception as e:
            logging.warning(f"Error in full model for {y}: {str(e)}")
            continue
    
    if effect_summary_all.empty:
        return {"error": "Unable to build any models with the provided data"}
    
    effect_summary_all = effect_summary_all.fillna(0)
    effect_summary_all["Median_LogWorth"] = effect_summary_all[response_vars].median(axis=1)
    effect_summary_all["Max_LogWorth"] = effect_summary_all[response_vars].max(axis=1)
    effect_summary_all["Appears_Significant"] = (effect_summary_all[response_vars] > threshold).sum(axis=1)
    effect_summary_all = effect_summary_all.sort_values("Max_LogWorth", ascending=False)
    
    # Get simplified factors
    def get_simplified_factors(effect_matrix, threshold, min_significant):
        factors = effect_matrix[
            (effect_matrix["Max_LogWorth"] >= threshold) |
            (effect_matrix["Appears_Significant"] >= min_significant)
        ]["Factor"].tolist()
        if "Intercept" in factors:
            factors.remove("Intercept")
        hierarchical_terms = set(factors)
        for f in factors:
            if ":" in f:
                parts = f.split(":")
                hierarchical_terms |= {parts[0].strip(), parts[1].strip()}
            if "I(" in f:
                base = f.split("(")[1].split("**")[0].strip()
                hierarchical_terms.add(base)
        return sorted(hierarchical_terms)
    
    simplified_factors = get_simplified_factors(effect_summary_all, threshold, min_significant)
    
    # Config combination for lack of fit
    df_raw["Config_combo"] = df_raw[variable_predictors].astype(str).agg("_".join, axis=1)
    df["Config_combo"] = df_raw["Config_combo"]
    
    # Collinearity check
    condition_number = None
    try:
        if simplified_factors:
            x = dmatrix(" + ".join(simplified_factors), data=df, return_type="dataframe")
            xtx = x.T @ x
            condition_number = float(np.linalg.cond(xtx.values))
    except Exception as e:
        logging.warning(f"Error in collinearity check: {str(e)}")
    
    # Store summary results
    results["summary"] = {
        "full_model_effects": effect_summary_all.to_dict('records'),
        "simplified_factors": simplified_factors,
        "condition_number": condition_number,
        "parameters": {
            "threshold": threshold,
            "min_significant": min_significant,
            "response_variables": response_vars,
            "predictors": variable_predictors
        }
    }
    
    # Build simplified models for each response variable
    simplified_logworth_df = pd.DataFrame()
    for y in response_vars:
        try:
            # Properly quote column names for statsmodels formula
            y_quoted = f"Q('{y}')" if '*' in y or ' ' in y or '(' in y else y
            
            if not simplified_factors:
                # Use linear terms only if no simplified factors identified
                predictor_terms = [f"Q('{p}')" if '*' in p or ' ' in p or '(' in p else p for p in variable_predictors]
                formula = f"{y_quoted} ~ " + " + ".join(predictor_terms)
            else:
                factor_terms = [f"Q('{f}')" if '*' in f or ' ' in f or '(' in f else f for f in simplified_factors]
                formula = f"{y_quoted} ~ " + " + ".join(factor_terms)
            
            model_fit = smf.ols(formula=formula, data=df).fit()
            
            # ANOVA table
            anova_tbl = anova_lm(model_fit, typ=3).reset_index()
            anova_tbl = anova_tbl.rename(columns={"index": "Factor"})
            anova_tbl = anova_tbl[anova_tbl["Factor"] != "Residual"]
            anova_tbl["LogWorth"] = -np.log10(anova_tbl["PR(>F)"].replace(0, 1e-16))
            temp = anova_tbl[["Factor", "LogWorth"]].copy()
            temp.columns = ["Factor", y]
            simplified_logworth_df = pd.merge(simplified_logworth_df, temp, on="Factor", how="outer") if not simplified_logworth_df.empty else temp
            
            # Model metrics
            y_true = df[y]
            y_pred = model_fit.fittedvalues
            resid = model_fit.resid
            rmse = np.sqrt(model_fit.mse_resid)
            
            # Lack of fit analysis
            lack_of_fit_results = jmp_lack_of_fit_analysis(y, df_raw.copy(), model_fit)
            
            # Parameter estimates
            coef_tbl = model_fit.summary2().tables[1].copy()
            coef_tbl["LogWorth"] = -np.log10(coef_tbl["P>|t|"].replace(0, 1e-16))
            
            # Uncoded parameter estimates
            uncoded_estimates = calculate_uncoded_estimates(coef_tbl, scaler, variable_predictors, y_true)
            
            # Store model results
            results["models"][y] = {
                "summary_of_fit": {
                    "r_squared": float(model_fit.rsquared),
                    "adjusted_r_squared": float(model_fit.rsquared_adj),
                    "rmse": float(rmse),
                    "mean_response": float(y_true.mean()),
                    "observations": int(model_fit.nobs)
                },
                "anova_table": anova_tbl.to_dict('records'),
                "coded_parameters": {k: {
                    "coefficient": float(v["Coef."]),
                    "std_error": float(v["Std.Err."]),
                    "t_value": float(v["t"]),
                    "p_value": float(v["P>|t|"]),
                    "logworth": float(v["LogWorth"])
                } for k, v in coef_tbl.to_dict('index').items()},
                "uncoded_parameters": uncoded_estimates,
                "lack_of_fit": lack_of_fit_results,
                "residuals": {
                    "raw_residuals": [float(x) for x in resid.tolist()],
                    "predicted_values": [float(x) for x in y_pred.tolist()],
                    "actual_values": [float(x) for x in y_true.tolist()]
                }
            }
            
        except Exception as e:
            logging.error(f"Error processing model for {y}: {str(e)}")
            results["models"][y] = {"error": str(e)}
    
    # Simplified model summary
    if not simplified_logworth_df.empty:
        simplified_logworth_df = simplified_logworth_df.fillna(0)
        simplified_logworth_df["Median_LogWorth"] = simplified_logworth_df[response_vars].median(axis=1)
        simplified_logworth_df["Max_LogWorth"] = simplified_logworth_df[response_vars].max(axis=1)
        simplified_logworth_df["Appears_Significant"] = (simplified_logworth_df[response_vars] > threshold).sum(axis=1)
        simplified_logworth_df = simplified_logworth_df.sort_values("Max_LogWorth", ascending=False)
        
        results["summary"]["simplified_model_effects"] = simplified_logworth_df.to_dict('records')
    
    return results

def jmp_lack_of_fit_analysis(y, df_raw, model_fit):
    """Perform JMP-style lack of fit analysis"""
    try:
        df_raw["_fitted"] = model_fit.fittedvalues
        df_raw["_Config"] = df_raw["Config_combo"]
        
        # Group-level metrics
        group_df = df_raw.groupby("_Config").agg(
            local_avg=(y, "mean"),
            fitted_val=("_fitted", "mean"),
            count=("_Config", "count")
        ).reset_index()
        
        group_df["ss_lof_component"] = group_df["count"] * (group_df["local_avg"] - group_df["fitted_val"])**2
        ss_lack = group_df["ss_lof_component"].sum()
        df_lack = len(group_df) - model_fit.df_model - 1
        
        df_merge = df_raw.merge(group_df[["_Config", "local_avg"]], on="_Config", how="left")
        df_merge["ss_pure"] = (df_merge[y] - df_merge["local_avg"])**2
        ss_pure = df_merge["ss_pure"].sum()
        df_pure = df_merge.shape[0] - len(group_df)
        
        if df_lack > 0 and df_pure > 0:
            ms_lack = ss_lack / df_lack
            ms_pure = ss_pure / df_pure
            F_lof = ms_lack / ms_pure if ms_pure > 0 else None
            p_lof = 1 - f.cdf(F_lof, df_lack, df_pure) if F_lof is not None else None
        else:
            ms_lack = ms_pure = F_lof = p_lof = None
        
        return {
            "lack_of_fit": {
                "df": int(df_lack) if df_lack > 0 else None,
                "ss": float(ss_lack),
                "ms": float(ms_lack) if ms_lack is not None else None
            },
            "pure_error": {
                "df": int(df_pure) if df_pure > 0 else None,
                "ss": float(ss_pure),
                "ms": float(ms_pure) if ms_pure is not None else None
            },
            "total_error": {
                "df": int(df_lack + df_pure) if df_lack > 0 and df_pure > 0 else None,
                "ss": float(ss_lack + ss_pure)
            },
            "f_ratio": float(F_lof) if F_lof is not None else None,
            "prob_f": float(p_lof) if p_lof is not None else None
        }
    except Exception as e:
        logging.warning(f"Error in lack of fit analysis: {str(e)}")
        return {"error": str(e)}

def calculate_uncoded_estimates(coef_tbl, scaler, predictors, y_true):
    """Calculate uncoded parameter estimates"""
    try:
        X_mean = scaler.mean_
        X_scale = scaler.scale_
        uncoded = []
        
        for pname in coef_tbl.index:
            if pname == "Intercept":
                continue
            coef_coded = coef_tbl.loc[pname, "Coef."]
            if pname.startswith("I("):
                var = pname.split("(")[1].split("**")[0].strip()
                if var in predictors:
                    i = predictors.index(var)
                    beta_uncoded = coef_coded / (X_scale[i] ** 2)
                else:
                    continue
            elif ":" in pname:
                parts = pname.split(":")
                var1, var2 = parts[0].strip(), parts[1].strip()
                if var1 in predictors and var2 in predictors:
                    i1, i2 = predictors.index(var1), predictors.index(var2)
                    beta_uncoded = coef_coded / (X_scale[i1] * X_scale[i2])
                else:
                    continue
            else:
                if pname.strip() in predictors:
                    i = predictors.index(pname.strip())
                    beta_uncoded = coef_coded / X_scale[i]
                else:
                    continue
            uncoded.append({"term": pname, "estimate": float(beta_uncoded)})
        
        # Calculate intercept
        mean_Y = y_true.mean()
        intercept_uncoded = mean_Y
        for item in uncoded:
            pname = item["term"]
            beta_uncoded = item["estimate"]
            if pname.startswith("I(") or ":" in pname:
                continue
            var = pname.strip()
            if var in predictors:
                i = predictors.index(var)
                intercept_uncoded -= beta_uncoded * X_mean[i]
        
        uncoded.insert(0, {"term": "Intercept", "estimate": float(intercept_uncoded)})
        return uncoded
        
    except Exception as e:
        logging.warning(f"Error calculating uncoded estimates: {str(e)}")
        return {"error": str(e)}
