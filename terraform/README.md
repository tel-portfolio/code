# Azure Algorithmic Trading Infrastructure

## Overview
Brief description of what this project does - automated trading infrastructure using Azure services.

## Architecture
High-level description of the architecture and design decisions.

### Key Components
- **Azure Function App**: Serverless compute for trading algorithms
- **MySQL Flexible Server**: Database for market data and trading history
- **Azure Key Vault**: Secure storage for API keys and secrets
- **Virtual Network**: Private networking with subnet delegation
- **NAT Gateway**: Outbound internet connectivity for the function app
- **Application Insights**: Monitoring and logging

### Architecture Diagram
```
[Add a simple ASCII diagram or link to an image]
```

## Prerequisites
- Azure subscription
- Terraform >= 1.0
- Azure CLI
- Terraform Cloud account (optional, for remote state)

## Required API Keys
You'll need to obtain the following API keys:
- **Alpaca Trading API**: For executing trades
- **Marketstack API**: For market data
- **SendGrid API**: For email notifications

## Deployment

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/azure-algo-trading
cd azure-algo-trading
```

### 2. Configure Variables
Set the following sensitive variables in Terraform Cloud or create a `terraform.tfvars` file:

```hcl
# Required sensitive variables
sql_admin_password = "your-secure-password"
alpaca_api_key = "your-alpaca-api-key"
alpaca_secret_key = "your-alpaca-secret-key"
marketstack_api_key = "your-marketstack-api-key"
sendgrid_api_key = "your-sendgrid-api-key"
email_recipients = "your-email@example.com"

# Optional overrides
environment = "dev"
location = "East US"
```

### 3. Initialize and Deploy
```bash
terraform init
terraform plan
terraform apply
```

## Configuration

### Environment Variables
The Function App uses these environment variables:
- `ALGO_DB_*`: Database connection settings
- `ALPACA_*`: Trading API credentials
- `MARKETSTACK_API_KEY`: Market data API
- `SENDGRID_API_KEY`: Email notification service
- `SIMULATION_MODE`: Set to "true" for paper trading

### Database Setup
The infrastructure creates two MySQL databases:
- `algo_data`: Stores trading algorithms and strategies
- `market_cache`: Caches market data for performance

## Security Features
- All secrets stored in Azure Key Vault
- System-assigned managed identity for Key Vault access
- Private networking with VNet integration
- Database isolated in private subnet
- HTTPS-only enforcement

## Cost Estimation
Estimated monthly costs (may vary by usage):
- Function App (EP1): ~$150-200
- MySQL Server: ~$15-20
- NAT Gateway: ~$45 + data processing
- Storage & Key Vault: ~$5-10
- **Total**: ~$215-275/month

## Monitoring
- Application Insights for function monitoring
- MySQL metrics available in Azure portal
- Key Vault access logs
- VNet flow logs (if enabled)

## Troubleshooting

### Common Issues
1. **Key Vault Access Denied**: Ensure the Function App's managed identity has proper access policies
2. **Database Connection Timeout**: Check VNet integration and subnet delegation
3. **Function App Cold Start**: Consider using EP1 plan for better performance

### Useful Commands
```bash
# View Function App logs
az functionapp log tail --name empire-algo-live --resource-group rg-functionapp-live

# Test Key Vault access
az keyvault secret show --vault-name kv-live-functionapp --name alpaca-api-key

# Check database connectivity
az mysql flexible-server show --name mysql-live-server --resource-group rg-functionapp-live
```

## Development

### Local Development
For local development of the Python functions:
1. Install Azure Functions Core Tools
2. Set up local.settings.json with development values
3. Use Azure Storage Emulator or connection string

### Testing
- Unit tests for trading algorithms
- Integration tests with paper trading APIs
- Infrastructure testing with Terratest

## Contributing
Guidelines for contributing to the project.

## License
Specify your license.

## Disclaimer
**Important**: This is educational/portfolio code. Do not use in production trading without proper testing and risk management. Trading involves financial risk.

## Contact
Your contact information or GitHub profile.