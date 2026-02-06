# Azure Deployment Guide

This guide will help you deploy the GitHub Maintainer Activity Dashboard to Azure App Service on Linux.

## Prerequisites

- Azure subscription
- Azure CLI installed (optional, for command-line deployment)
- GitHub token with appropriate permissions

## Files Prepared for Deployment

- `startup.sh` - Gunicorn startup script for Azure
- `requirements.txt` - Updated with gunicorn
- `.deployment` - Azure deployment configuration

## Deploy via Azure Portal

1. **Go to Azure Portal**: https://portal.azure.com

2. **Create Web App**:
   - Click "Create a resource" → "Web App"
   - **Basics**:
     - Subscription: Choose your subscription
     - Resource Group: Create new (e.g., `ps-engagement-rg`)
     - Name: Choose unique name (e.g., `ps-engagement-dashboard`)
     - Publish: **Code**
     - Runtime stack: **Python 3.11** (or your version)
     - Operating System: **Linux**
     - Region: Choose closest to you
   - **App Service Plan**:
     - For testing: Free F1
     - For production: Basic B1 (~$13/month)
   - Click "Review + Create" → "Create"

3. **Deploy Code**:
   - Go to your App Service
   - Left menu: **Deployment Center**
   - Choose deployment method:
     - **Local Git**: Get Git URL and push
     - **GitHub**: Connect your repository
     - **VS Code**: Use Azure App Service extension
     - **ZIP Deploy**: Upload ZIP file

4. **Configure Environment Variables**:
   - Go to: **Configuration** → **Application settings**
   - Click "+ New application setting" for each:
     - `GITHUB_TOKEN`: Your GitHub personal access token
     - `GITHUB_OWNER`: PowerShell (or your target)
     - `GITHUB_REPO`: PowerShell (or your target)
     - `FLASK_DEBUG`: False (for production)
     - `FLASK_SECRET_KEY`: Generate a strong secret key
   - Click "Save"

5. **Configure Startup Command** (if not auto-detected):
   - Go to: **Configuration** → **General settings**
   - Startup Command: `startup.sh`
   - Click "Save"

6. **Access Your App**:
   - URL: `https://your-app-name.azurewebsites.net`


## Environment Variables Required in Azure

Set these in Configuration → Application settings:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxx...` |
| `GITHUB_OWNER` | Repository owner | `PowerShell` |
| `GITHUB_REPO` | Repository name | `PowerShell` |
| `FLASK_DEBUG` | Debug mode (set to False) | `False` |
| `FLASK_SECRET_KEY` | Flask secret key | Generate strong key |

## Monitoring and Logs

### View Logs in Portal
- Go to your App Service
- **Monitoring** → **Log stream**

### View Logs via CLI
```powershell
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP
```

### Enable Application Logging
- **Monitoring** → **App Service logs**
- Enable "Application Logging (Filesystem)"
- Set Level to "Information" or "Error"

## Troubleshooting

### App doesn't start
- Check startup command: `startup.sh`
- Check Python version matches runtime
- View logs for specific errors

### Environment variables not working
- Verify they're set in Configuration → Application settings
- Restart the app after setting variables

### GitHub API errors
- Verify GITHUB_TOKEN is valid
- Check token has required permissions

## Cost Optimization

- **Free F1**: Free, but sleeps after 60 min CPU/day
- **Basic B1**: ~$13/month, always on
- **Standard S1**: ~$70/month, includes auto-scaling

Start with Free or Basic B1 for development and testing.

## Custom Domain (Optional)

After deployment, you can add a custom domain:
1. **Settings** → **Custom domains**
2. Follow the instructions to verify domain ownership
3. Add DNS records as specified

Requires Basic tier or higher.

## SSL/HTTPS

Azure provides free SSL certificate for *.azurewebsites.net domains automatically.

For custom domains:
- Use **TLS/SSL settings** to add certificate
- Azure can provide free managed certificate (requires Standard tier)

## Next Steps

1. Deploy the application
2. Set environment variables
3. Test the `/health` endpoint
4. Monitor logs for any issues
5. Access your dashboard at your Azure URL
