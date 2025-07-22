# Azure Function Deployment Guide for DOE Analysis

## Prerequisites

1. **Azure CLI installed and logged in**
   ```bash
   az login
   ```

2. **Azure Functions Core Tools installed**
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```

3. **Python 3.12** (which you already have)

## Deployment Options

### Option 1: PowerShell Script (Windows - Recommended)
```powershell
.\deploy_azure.ps1
```

### Option 2: Bash Script (Cross-platform)
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 3: Manual Deployment Steps

1. **Create Resource Group**
   ```bash
   az group create --name rg-doe-analysis --location "East US"
   ```

2. **Create Storage Account**
   ```bash
   az storage account create \
     --name storedoe$(Get-Random) \
     --resource-group rg-doe-analysis \
     --location "East US" \
     --sku Standard_LRS
   ```

3. **Create Function App**
   ```bash
   az functionapp create \
     --resource-group rg-doe-analysis \
     --consumption-plan-location "East US" \
     --runtime python \
     --runtime-version 3.12 \
     --functions-version 4 \
     --name doe-analysis-$(Get-Random) \
     --storage-account your-storage-name \
     --os-type Linux
   ```

4. **Deploy Function Code**
   ```bash
   func azure functionapp publish your-function-app-name --python
   ```

## What the Deployment Creates

- **Resource Group**: Container for all resources
- **Storage Account**: Required for Function App state and triggers
- **Function App**: Serverless compute service running your DOE analysis
- **Function**: The actual DOE analysis endpoint

## After Deployment

1. **Test the Function**
   - The script will create `test_function_azure.py` with your Azure details
   - Run: `python test_function_azure.py`

2. **Get Function URL**
   - Format: `https://your-function-app.azurewebsites.net/api/DoeAnalysis`
   - The script will display the exact URL

3. **Function Authentication**
   - Function key will be automatically retrieved
   - Use in headers: `x-functions-key: your-function-key`

## AI Foundry Integration

Use the deployed function URL in your AI Foundry configuration:

```json
{
  "endpoint": "https://your-function-app.azurewebsites.net/api/DoeAnalysis",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "x-functions-key": "your-function-key"
  }
}
```

## Monitoring and Management

- **Azure Portal**: Monitor function performance and logs
- **Application Insights**: Detailed telemetry (automatically configured)
- **Cost Management**: Track consumption costs

## Scaling

The function automatically scales based on demand:
- **Cold Start**: ~2-5 seconds for first request
- **Warm**: ~100-500ms for subsequent requests
- **Auto-scaling**: Up to 200 concurrent instances

## Security

- **Function Keys**: Secure access to your endpoint
- **HTTPS Only**: All traffic encrypted
- **CORS**: Configure allowed origins if needed

## Troubleshooting

1. **Deployment Issues**
   - Check Azure CLI login: `az account show`
   - Verify resource names are unique
   - Check quota limits in your subscription

2. **Function Issues**
   - Check logs in Azure Portal
   - Test locally first: `func start`
   - Verify all dependencies in requirements.txt

3. **Performance Issues**
   - Monitor in Application Insights
   - Consider Premium plan for consistent performance
   - Optimize code for cold start performance
