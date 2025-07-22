# SharePoint URL Conversion for AI Foundry

## Your Current SharePoint Link:
https://microsoftapc-my.sharepoint.com/:x:/g/personal/ruwang_microsoft_com/EVpyobRU8ahOrRssDQceoCkBM9NODXvJg9MOYJoWv7AvIA?e=DCiefg

## Convert to Direct Download URL:

### Step 1: Extract the File ID
From your URL, the file ID is: `EVpyobRU8ahOrRssDQceoCkBM9NODXvJg9MOYJoWv7AvIA`

### Step 2: Create Direct Download URL
Replace the SharePoint viewing URL with a direct download URL:

**Direct Download URL:**
```
https://microsoftapc-my.sharepoint.com/personal/ruwang_microsoft_com/_layouts/15/download.aspx?UniqueId=EVpyobRU8ahOrRssDQceoCkBM9NODXvJg9MOYJoWv7AvIA
```

OR

**Alternative Direct URL (CSV format):**
```
https://microsoftapc-my.sharepoint.com/:x:/g/personal/ruwang_microsoft_com/EVpyobRU8ahOrRssDQceoCkBM9NODXvJg9MOYJoWv7AvIA?download=1
```

## AI Foundry Prompt Using SharePoint URL:

```
I have experimental data from a textile dyeing process optimization study stored on SharePoint. Please analyze this comprehensive DOE dataset to help optimize our dyeing process.

**Data Source:** https://microsoftapc-my.sharepoint.com/:x:/g/personal/ruwang_microsoft_com/EVpyobRU8ahOrRssDQceoCkBM9NODXvJg9MOYJoWv7AvIA?download=1

**Study Background:**
- Industry: Textile dyeing and finishing
- Products: Kickstand and Bucket parts with different surface treatments
- Objective: Optimize color consistency and quality across different dyeing conditions
- Dataset: Comprehensive DOE with multiple configurations and replications

**Experimental Factors (Predictors):**
- dye1: Primary dye concentration (g/L)
- dye2: Secondary dye concentration (g/L)  
- Temp: Dyeing temperature (°C)
- Time: Dyeing time (hours)
- Na2SO4 (g/L): Salt concentration for color fastness
- Dyeing pH: Process pH level

**Response Variables to Optimize:**
- Lvalue: Lightness measurement (target: consistent, appropriate level)
- Avalue: Red-green color axis (target: specific color balance)
- Bvalue: Blue-yellow color axis (target: specific color balance)
- DE*cmc: Color difference from target (target: minimize variation)

**Analysis Request:**
Please use the DOE_Analysis tool to analyze this data with the following parameters:
- Data: [SharePoint URL above]
- Response variables: ["Lvalue", "Avalue", "Bvalue", "DE*cmc"]
- Predictors: ["dye1", "dye2", "Temp", "Time", "Na2SO4 (g/L)", "Dyeing pH"]
- Threshold: 1.5 (for multicollinearity detection)
- Min significant: 2 (factor must be significant in at least 2 models)

**Specific Questions:**
1. Which dyeing parameters most significantly affect color quality?
2. What are the optimal factor settings for minimizing color variation (DE*cmc)?
3. Are there critical interactions between temperature, time, and dye concentrations?
4. How do the optimal settings differ between Kickstand and Bucket parts?
5. Which factors should be most tightly controlled in production for quality assurance?

Please provide actionable recommendations for process optimization and quality control.
```

## Alternative Approaches:

### Option 2: Test Direct URL Access
Try these variations in AI Foundry:

1. **Original with download parameter:**
   ```
   https://microsoftapc-my.sharepoint.com/:x:/g/personal/ruwang_microsoft_com/EVpyobRU8ahOrRssDQceoCkBM9NODXvJg9MOYJoWv7AvIA?e=DCiefg&download=1
   ```

2. **Direct download URL:**
   ```
   https://microsoftapc-my.sharepoint.com/personal/ruwang_microsoft_com/_layouts/15/download.aspx?UniqueId=EVpyobRU8ahOrRssDQceoCkBM9NODXvJg9MOYJoWv7AvIA
   ```

### Option 3: GitHub Upload (Most Reliable)
If SharePoint access doesn't work, upload to GitHub:

1. Create a GitHub repository (can be private)
2. Upload the CSV file
3. Use the raw file URL: `https://raw.githubusercontent.com/[username]/[repo]/main/DOEData_Sample.csv`

### Option 4: OneDrive Public Link
Convert to OneDrive and get a public sharing link with direct download capability.

## Testing the URL:
Before using in AI Foundry, test that the URL works by opening it in a browser - it should directly download the CSV file.
