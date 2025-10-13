# Azure Storage Setup Guide

This guide explains how to set up Azure Blob Storage for dataset management in the Attribute Forecasting System.

## Prerequisites

- Azure subscription
- Azure CLI installed (`az` command)
- Application already deployed to Azure (Container Apps)

## Step 1: Create Azure Storage Account

### Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → "Storage account"
3. Fill in the details:
   - **Subscription**: Select your subscription
   - **Resource group**: Use existing `afs-rg` (or your resource group)
   - **Storage account name**: Choose a unique name (e.g., `afsstorage123`)
   - **Region**: Same as your Container Apps (e.g., West Europe)
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally Redundant Storage) for development, or GRS for production
4. Click "Review + Create" → "Create"

### Using Azure CLI

```bash
# Set variables
RESOURCE_GROUP="afs-rg"
STORAGE_ACCOUNT_NAME="afsstorage123"  # Must be globally unique
LOCATION="westeurope"
CONTAINER_NAME="datasets"

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Get connection string
CONNECTION_STRING=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --output tsv)

echo "Connection String: $CONNECTION_STRING"

# Create blob container
az storage container create \
  --name $CONTAINER_NAME \
  --account-name $STORAGE_ACCOUNT_NAME \
  --connection-string "$CONNECTION_STRING"
```

## Step 2: Configure CORS (for direct browser uploads - optional)

If you plan to upload directly from the browser to Azure Storage (not currently implemented), configure CORS:

```bash
az storage cors add \
  --services b \
  --methods GET POST PUT DELETE OPTIONS \
  --origins "https://your-frontend-url.azurecontainerapps.io" \
  --allowed-headers "*" \
  --exposed-headers "*" \
  --max-age 3600 \
  --account-name $STORAGE_ACCOUNT_NAME \
  --connection-string "$CONNECTION_STRING"
```

## Step 3: Get Storage Credentials

### Option A: Connection String (Development/Testing)

```bash
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --output tsv
```

Copy this connection string for use in GitHub Secrets.

### Option B: Managed Identity (Production - Recommended)

For production, use Managed Identity instead of connection strings:

1. **Enable Managed Identity on Container App:**

```bash
az containerapp identity assign \
  --name afs-api \
  --resource-group $RESOURCE_GROUP \
  --system-assigned
```

2. **Get the Identity Principal ID:**

```bash
PRINCIPAL_ID=$(az containerapp identity show \
  --name afs-api \
  --resource-group $RESOURCE_GROUP \
  --query principalId \
  --output tsv)
```

3. **Grant Storage Blob Data Contributor role:**

```bash
STORAGE_ID=$(az storage account show \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id \
  --output tsv)

az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID
```

4. **Update environment variables:**

For managed identity, set these environment variables in your Container App:
- `STORAGE_MODE=azure`
- `AZURE_STORAGE_ACCOUNT_NAME=afsstorage123`
- Remove `AZURE_STORAGE_CONNECTION_STRING`

## Step 4: Configure GitHub Secrets

Add the Azure Storage connection string to GitHub Secrets:

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the following secret:
   - **Name**: `AZURE_STORAGE_CONNECTION_STRING`
   - **Value**: The connection string from Step 3

## Step 5: Update Local Development Environment

For local development with Azure Storage:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add:
   ```bash
   STORAGE_MODE=azure
   AZURE_STORAGE_CONNECTION_STRING=your-connection-string-here
   AZURE_STORAGE_CONTAINER_NAME=datasets
   ```

3. Or, to use local storage for development:
   ```bash
   STORAGE_MODE=local
   ```

## Step 6: Deploy the Updated Application

The deployment workflow has been updated to include Azure Storage configuration. Simply push your changes:

```bash
git add .
git commit -m "Add Azure Storage integration"
git push origin main
```

The GitHub Actions workflow will automatically:
- Build and deploy the updated API with Azure Storage support
- Configure environment variables for Azure Storage

## Step 7: Verify the Setup

1. **Check the Data Management page:**
   - Navigate to `https://your-app-url/data`
   - Try uploading a CSV or XLSX file

2. **Verify storage in Azure Portal:**
   - Go to your Storage Account
   - Navigate to Containers → `datasets`
   - You should see uploaded files

3. **Check logs:**
   ```bash
   az containerapp logs show \
     --name afs-api \
     --resource-group $RESOURCE_GROUP \
     --follow
   ```

## Supported File Formats

The system supports:
- **CSV files** (`.csv`)
- **Excel files** (`.xlsx`)

## Dataset Types

Files are automatically categorized based on filename:
- Files containing "product" → Products dataset
- Files containing "sales" → Sales dataset
- Files containing "inventory" or "stock" → Inventory dataset

## Data Schemas

### Products
Required columns: `sku`, `style_code`, `style_desc`, `color_name`, `size`, `category`, `price`

### Sales
Required columns: `date`, `store_id`, `channel`, `sku`, `units_sold`, `price`

### Inventory
Required columns: `date`, `store_id`, `sku`, `on_hand`

## Duplicate Detection

The system uses primary keys to detect and handle duplicates:

- **Products**: `sku`
- **Sales**: `date` + `store_id` + `sku`
- **Inventory**: `date` + `store_id` + `sku`

When uploading incremental data:
- **New records** are added
- **Existing records** are updated with new values
- No duplicates are created

## Troubleshooting

### "Upload failed: Connection string not configured"

**Solution**: Ensure `AZURE_STORAGE_CONNECTION_STRING` is set in your environment variables or GitHub Secrets.

### "Container not found"

**Solution**: Create the container manually:
```bash
az storage container create \
  --name datasets \
  --account-name $STORAGE_ACCOUNT_NAME
```

### "Access denied" errors

**Solution**:
1. Verify the connection string is correct
2. Check that the storage account key hasn't been rotated
3. For managed identity, ensure the role assignment is correct

### Files not appearing in Azure Portal

**Solution**:
1. Check the container name matches `AZURE_STORAGE_CONTAINER_NAME`
2. Verify the upload completed successfully in the API logs
3. Refresh the Azure Portal page

## Cost Optimization

Azure Blob Storage pricing is based on:
- **Storage capacity**: Very low cost (~$0.02/GB/month for LRS)
- **Operations**: Small fee per transaction
- **Data transfer**: Outbound data transfer charges

For a forecasting system with typical dataset sizes (100MB-1GB), expect costs under $5/month.

## Security Best Practices

1. **Use Managed Identity in production** instead of connection strings
2. **Rotate storage keys regularly** if using connection strings
3. **Enable firewall rules** to restrict access to specific IPs/VNets
4. **Enable soft delete** for accidental deletion protection:
   ```bash
   az storage blob service-properties delete-policy update \
     --account-name $STORAGE_ACCOUNT_NAME \
     --enable true \
     --days-retained 7
   ```

## Next Steps

After setup:
1. Upload your first dataset via the Data Management page
2. Verify data is stored in Azure Blob Storage
3. Train the model with the new data: `POST /api/v1/train`
4. Generate forecasts: `POST /api/v1/predict`

## Additional Resources

- [Azure Blob Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Azure Storage pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/)
- [Managed Identity Documentation](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/)
