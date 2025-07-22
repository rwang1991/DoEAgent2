# PowerShell deployment script for DOE Analysis Azure Function

# Variables
$ResourceGroup = "doe-analysis-rg"
$FunctionAppName = "doe-analysis-func"
$StorageAccountName = "doeanalysisstorage"
$Location = "East US"

# Create resource group
Write-Host "Creating resource group..." -ForegroundColor Green
az group create --name $ResourceGroup --location $Location

# Create storage account
Write-Host "Creating storage account..." -ForegroundColor Green
az storage account create `
  --name $StorageAccountName `
  --location $Location `
  --resource-group $ResourceGroup `
  --sku Standard_LRS

# Create function app
Write-Host "Creating function app..." -ForegroundColor Green
az functionapp create `
  --resource-group $ResourceGroup `
  --consumption-plan-location $Location `
  --runtime python `
  --runtime-version 3.9 `
  --functions-version 4 `
  --name $FunctionAppName `
  --storage-account $StorageAccountName `
  --os-type Linux

# Deploy function code
Write-Host "Deploying function code..." -ForegroundColor Green
func azure functionapp publish $FunctionAppName

# Get function URL
Write-Host "Getting function URL..." -ForegroundColor Green
$FunctionUrl = az functionapp function show `
  --resource-group $ResourceGroup `
  --name $FunctionAppName `
  --function-name DoeAnalysis `
  --query "invokeUrlTemplate" `
  --output tsv

Write-Host "Function deployed successfully!" -ForegroundColor Green
Write-Host "Function URL: $FunctionUrl" -ForegroundColor Yellow
Write-Host "Remember to get the function key from Azure portal for authentication." -ForegroundColor Yellow
