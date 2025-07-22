# 📋 Enhanced OpenAPI Schema - Version 2.0

## 🎯 **What's Updated**

The OpenAPI schema has been completely enhanced to reflect the new AI Foundry integration capabilities and improved function features.

### ✅ **Key Schema Improvements:**

1. **🔄 AI Foundry Column Mapping Documentation**
   - Clearly documents automatic column name mapping
   - Shows generic → actual column mappings
   - Provides AI Foundry compatibility flags

2. **📊 Flexible Input Format Support**
   - Documents URL, base64, and raw CSV input options
   - Shows multiple request format examples
   - Simplified vs. legacy format schemas

3. **⚡ Enhanced Response Structure**
   - Updated to include `data_info` metadata
   - Documents sampling information
   - Shows actual vs. mapped predictor columns

4. **🛡️ Comprehensive Error Documentation**
   - Error examples with recommendations
   - Column mismatch scenarios
   - Data validation errors

## 📂 **Schema Files Created:**

### 🟢 **Primary Files:**
- `openapi_doe_analysis_enhanced.yaml` - Full YAML specification
- `openapi_doe_analysis_enhanced.json` - JSON format for tools

### 🔄 **Legacy File:**
- `openapi_doe_analysis.yaml` - Original schema (kept for reference)

## 🎯 **Key Schema Features:**

### **1. AI Foundry Integration Section:**
```yaml
x-ai-foundry:
  compatible: true
  auto-mapping: true
  description: "Fully compatible with AI Foundry generic column names"
```

### **2. Column Mapping Documentation:**
```yaml
x-ai-foundry-mapping:
  mappings:
    "Dye Concentration": ["dye1", "dye2", "dye", "concentration"]
    "Temperature": ["Temp", "temperature", "temp"]
    "Time": ["Time", "time"]
    "pH": ["Dyeing pH", "pH", "ph"]
```

### **3. Dual Format Support:**
```yaml
schema:
  oneOf:
    - $ref: '#/components/schemas/SimplifiedFormat'  # AI Foundry preferred
    - $ref: '#/components/schemas/LegacyFormat'      # Backward compatibility
```

### **4. Enhanced Examples:**
- ✅ AI Foundry simplified format
- ✅ AI Foundry with predictor mapping  
- ✅ GitHub URL input
- ✅ Base64 data input
- ✅ Error scenarios with solutions

## 🚀 **For AI Foundry Integration:**

### **Recommended Payload (from schema):**
```json
{
  "data": "https://raw.githubusercontent.com/rwang1991/DoEAgent/refs/heads/main/DOEData_20250622.csv",
  "response_column": "DE*cmc",
  "force_full_dataset": true,
  "threshold": 1.5
}
```

### **Alternative with Mapping:**
```json
{
  "data": "https://raw.githubusercontent.com/rwang1991/DoEAgent/refs/heads/main/DOEData_20250622.csv",
  "response_vars": ["DE*cmc"],
  "predictors": ["Dye Concentration", "Temperature", "Time", "pH"],
  "threshold": 1.5,
  "force_full_dataset": true
}
```

## ✅ **Validation Results:**

**✅ Schema Tested:** Both formats work perfectly
**✅ AI Foundry Compatible:** Automatic column mapping confirmed  
**✅ Error Handling:** Comprehensive error documentation  
**✅ Response Structure:** Enhanced metadata included

## 🎯 **Next Steps:**

1. **Use the enhanced schema** for any API documentation
2. **Share with AI Foundry team** for integration
3. **Reference in future development** for consistency

---

**🎉 The enhanced OpenAPI schema fully documents the AI Foundry integration capabilities and is ready for production use!**
