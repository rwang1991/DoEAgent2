#!/bin/bash

# Deploy Azure Function for DOE Analysis
# This script creates the necessary Azure resources and deploys the function

# Configuration (you can modify these)
RESOURCE_GROUP_NAME="rg-doe-analysis"
FUNCTION_APP_NAME="doe-analysis-$RANDOM"
STORAGE_ACCOUNT_NAME="storedoe$RANDOM"
LOCATION="East US"

echo "🚀 Starting Azure Function Deployment for DOE Analysis"
echo "================================================================================================="

# Display deployment parameters
echo "📝 Deployment Parameters:"
echo "  Resource Group: $RESOURCE_GROUP_NAME"
echo "  Function App: $FUNCTION_APP_NAME"
echo "  Storage Account: $STORAGE_ACCOUNT_NAME"
echo "  Location: $LOCATION"
echo ""

# Check if logged into Azure
echo "🔐 Checking Azure login status..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

ACCOUNT=$(az account show --query "user.name" -o tsv)
echo "✅ Logged in as: $ACCOUNT"

# Create Resource Group
echo "📦 Creating resource group..."
if az group create --name $RESOURCE_GROUP_NAME --location "$LOCATION"; then
    echo "✅ Resource group created successfully"
else
    echo "❌ Failed to create resource group"
    exit 1
fi

# Create Storage Account
echo "💾 Creating storage account..."
if az storage account create \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --location "$LOCATION" \
    --sku Standard_LRS; then
    echo "✅ Storage account created successfully"
else
    echo "❌ Failed to create storage account"
    exit 1
fi

# Create Function App
echo "⚡ Creating Function App..."
if az functionapp create \
    --resource-group $RESOURCE_GROUP_NAME \
    --consumption-plan-location "$LOCATION" \
    --runtime python \
    --runtime-version 3.12 \
    --functions-version 4 \
    --name $FUNCTION_APP_NAME \
    --storage-account $STORAGE_ACCOUNT_NAME \
    --os-type Linux; then
    echo "✅ Function App created successfully"
else
    echo "❌ Failed to create Function App"
    exit 1
fi

# Deploy the function
echo "🚢 Deploying function code..."
if func azure functionapp publish $FUNCTION_APP_NAME --python; then
    echo "✅ Function deployed successfully"
else
    echo "❌ Failed to deploy function"
    exit 1
fi

# Get function URL
echo "🔗 Getting function URL..."
FUNCTION_URL=$(az functionapp function show \
    --resource-group $RESOURCE_GROUP_NAME \
    --name $FUNCTION_APP_NAME \
    --function-name DoeAnalysis \
    --query "invokeUrlTemplate" -o tsv 2>/dev/null)

if [ -n "$FUNCTION_URL" ]; then
    BASE_URL=$(echo $FUNCTION_URL | sed 's/{.*}//')
    echo "✅ Function URL: $BASE_URL"
else
    BASE_URL="https://$FUNCTION_APP_NAME.azurewebsites.net/api/DoeAnalysis"
    echo "✅ Function URL (estimated): $BASE_URL"
fi

# Get function key (for secured access)
echo "🔑 Getting function key..."
FUNCTION_KEY=$(az functionapp keys list --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP_NAME --query "functionKeys.default" -o tsv 2>/dev/null)
if [ -n "$FUNCTION_KEY" ]; then
    echo "✅ Function key retrieved"
else
    echo "⚠️  Function key not found, function may be accessible without key"
    FUNCTION_KEY=""
fi

# Update test script with Azure details
echo "📝 Updating test script..."
cp test_function.py test_function_azure.py
sed -i "s|azure_url = \"https://your-function-app.azurewebsites.net/api/DoeAnalysis\"|azure_url = \"$BASE_URL\"|g" test_function_azure.py
if [ -n "$FUNCTION_KEY" ]; then
    sed -i "s|azure_key = \"your-function-key\"|azure_key = \"$FUNCTION_KEY\"|g" test_function_azure.py
fi
echo "✅ Created test_function_azure.py with Azure details"

# Final summary
echo ""
echo "🎉 Deployment Complete!"
echo "================================================================================================="
echo "📊 DOE Analysis Function Details:"
echo "  Function App Name: $FUNCTION_APP_NAME"
echo "  Function URL: $BASE_URL"
if [ -n "$FUNCTION_KEY" ]; then
    echo "  Function Key: $FUNCTION_KEY"
fi
echo "  Resource Group: $RESOURCE_GROUP_NAME"
echo ""
echo "🧪 Testing:"
echo "  Run: python test_function_azure.py"
echo ""
echo "🔗 AI Foundry Integration:"
echo "  Use the URL above in your AI Foundry configuration"
if [ -n "$FUNCTION_KEY" ]; then
    echo "  Include the function key in your headers: x-functions-key: $FUNCTION_KEY"
fi

echo ""
echo "💡 Next Steps:"
echo "  1. Test the deployed function with test_function_azure.py"
echo "  2. Configure AI Foundry to use the function URL"
echo "  3. Monitor function performance in Azure Portal"
