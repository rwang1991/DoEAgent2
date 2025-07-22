# Deployment Commands for Your Specific Azure Environment

## Your Azure Configuration
- **Subscription**: AMO-CloudServices-Sandbox
- **Resource Group**: rg-rui-test  
- **Function App**: func-rui-test-doe
- **Storage Account**: stamosandboxdennistest
- **Location**: West US

## Step-by-Step Deployment Commands

### Step 1: Set the Correct Subscription
```bash
az account set --subscription "AMO-CloudServices-Sandbox"
az account show --query "name" -o tsv
```

### Step 2: Create Resource Group (if it doesn't exist)
```bash
az group create --name "rg-rui-test" --location "West US"
```

### Step 3: Check if Storage Account Exists
```bash
az storage account show --name "stamosandboxdennistest" --resource-group "rg-rui-test"
```

### Step 4: Create Storage Account (if it doesn't exist)
```bash
az storage account create \
  --name "stamosandboxdennistest" \
  --resource-group "rg-rui-test" \
  --location "West US" \
  --sku Standard_LRS
```

### Step 5: Create Function App
```bash
az functionapp create \
  --resource-group "rg-rui-test" \
  --consumption-plan-location "West US" \
  --runtime python \
  --runtime-version 3.12 \
  --functions-version 4 \
  --name "func-rui-test-doe" \
  --storage-account "stamosandboxdennistest" \
  --os-type Linux
```

### Step 6: Deploy Function Code
```bash
func azure functionapp publish func-rui-test-doe --python
```

### Step 7: Get Function URL
```bash
az functionapp function show \
  --resource-group "rg-rui-test" \
  --name "func-rui-test-doe" \
  --function-name DoeAnalysis \
  --query "invokeUrlTemplate" -o tsv
```

### Step 8: Get Function Key (Optional)
```bash
az functionapp keys list \
  --name "func-rui-test-doe" \
  --resource-group "rg-rui-test" \
  --query "functionKeys.default" -o tsv
```

## Expected Function URL
After deployment, your function will be available at:
`https://func-rui-test-doe.azurewebsites.net/api/DoeAnalysis`

## Testing the Deployed Function
Once deployed, you can test it with:
```bash
python test_function.py
```
(Update the Azure URL in the test script)
