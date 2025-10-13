# Deployment Guide

This project is configured for automated deployment to Azure Container Apps using GitHub Actions.

## Azure Resources

The following Azure resources are configured:

- **Resource Group:** `afs-rg`
- **Container Registry:** `afsregistry.azurecr.io`
- **API Container App:** `afs-api`
- **Web Container App:** `afs-web`
- **Region:** West Europe

## GitHub Actions Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

Runs on pull requests and non-main branches:
- Tests backend code
- Builds Docker images
- Validates docker-compose configuration

### 2. Deployment Workflow (`.github/workflows/deploy-azure.yml`)

Runs on push to `main` branch:
- Builds Docker images for API and Web
- Pushes images to Azure Container Registry
- Deploys to Azure Container Apps
- Configures environment variables

## Required GitHub Secrets

To enable automated deployment, configure these secrets in your GitHub repository:

### Setting up GitHub Secrets:

1. Go to: https://github.com/Julian-Coral/attribute-forecasting-system/settings/secrets/actions

2. Click "New repository secret" and add each of these:

#### AZURE_REGISTRY_USERNAME
```
<your-registry-username>
```
Get this from: Azure Portal → Container Registry → Access keys → Username

#### AZURE_REGISTRY_PASSWORD
```
<your-registry-password>
```
Get this from: Azure Portal → Container Registry → Access keys → Password

#### AZURE_CREDENTIALS

This is a JSON object for Azure Service Principal authentication.

**To create this:**

**Option A: Using Azure Portal (Recommended)**

1. Go to Azure Portal: https://portal.azure.com
2. Open Cloud Shell (icon at top right)
3. Run this command (replace with your subscription ID):

```bash
az ad sp create-for-rbac \
  --name "afs-github-actions" \
  --role contributor \
  --scopes /subscriptions/ea3d99f6-efb7-4b07-afa3-7a12971d39a9/resourceGroups/afs-rg \
  --sdk-auth
```

4. Copy the entire JSON output
5. Add it as the `AZURE_CREDENTIALS` secret in GitHub

**Expected format:**
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "ea3d99f6-efb7-4b07-afa3-7a12971d39a9",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

## Manual Deployment Trigger

You can manually trigger a deployment:

1. Go to: https://github.com/Julian-Coral/attribute-forecasting-system/actions
2. Select "Deploy to Azure Container Apps"
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

## Accessing Your Deployed Application

After deployment, your applications will be available at:

**API:**
```
https://afs-api.{random-id}.westeurope.azurecontainerapps.io
```

**Web:**
```
https://afs-web.{random-id}.westeurope.azurecontainerapps.io
```

To find the exact URLs:
1. Go to Azure Portal
2. Navigate to: Resource Groups → `afs-rg` → Container Apps
3. Click on each app and find the "Application Url" in the Overview section

## Environment Variables

### API Container App
- `DATA_DIR`: `/app/data/seed`
- `ARTIFACTS_DIR`: `/app/artifacts`

### Web Container App
- `VITE_API_BASE`: Automatically configured to point to the API URL

## Monitoring and Logs

### View Logs in Azure Portal:
1. Go to your Container App
2. Click "Log stream" in the left menu
3. View real-time logs

### View GitHub Actions Logs:
1. Go to: https://github.com/Julian-Coral/attribute-forecasting-system/actions
2. Click on any workflow run
3. View detailed logs for each step

## Troubleshooting

### Deployment Fails
- Check GitHub Actions logs for specific errors
- Verify all secrets are configured correctly
- Ensure Azure resources exist and are accessible

### Application Not Responding
- Check Container App logs in Azure Portal
- Verify environment variables are set correctly
- Check if the container is running: Azure Portal → Container App → Revision management

### API Connection Issues
- Verify the API URL in the Web app environment variables
- Check if API ingress is enabled and publicly accessible
- Verify CORS settings if needed

## Cost Estimation

**Monthly costs (approximate):**
- Container Registry (Basic): ~$5
- Container Apps (2 apps, minimal traffic): ~$10-15
- **Total:** ~$15-20/month

**Free tier eligible for new Azure accounts**

## Security Notes

- Container Registry admin credentials are stored as GitHub secrets
- Service Principal has contributor access only to the `afs-rg` resource group
- All connections use HTTPS
- Rotate credentials regularly for security

## Next Steps

1. Configure GitHub secrets (see above)
2. Push code to trigger automatic deployment
3. Monitor deployment in GitHub Actions
4. Access your deployed application
5. Set up custom domain (optional)
6. Configure Application Insights for monitoring (optional)
