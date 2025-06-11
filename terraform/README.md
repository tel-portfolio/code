## empire-functionapp — Quick‑Start

Deploys an Azure Function App for a Python-based stock trading algorithm and portfolio management system. This build uses Terraform remote backend to store sensitive variables before they are stored in Azure Key Vault. Calculates and executes trades before market close, using a MySQL backend.


## Prereqs

Terraform 1.3+

Azure CLI (logged in)

Terraform Cloud account (for remote state)

Python function code (deployed separately)


## What It Does

    Creates a Linux-based Azure Function App using Python 3.11.

    Sets up an Azure MySQL Flexible Server with two databases:

        algo_data for tracking trades and positions

        market_cache for caching market data

    Stores API keys and secrets in Azure Key Vault.

    Connects Application Insights for monitoring.

    Whitelists Function App IPs in MySQL firewall rules.

    Uses remote Terraform backend for shared state and automation.


## Setup
Clone the repo and cd into the folder.

Set required values in terraform.tfvars or through the Terraform Cloud Variables UI.

(First run only) Apply the function app to fetch outbound IPs:

    terraform apply -target=azurerm_linux_function_app.algo_functionapp
    terraform apply


## Notes
The algorithm logic (Python) should be deployed via Azure CLI or GitHub Actions.

Firewall rules use Function App IPs, which must be created before MySQL rules are applied.

Store sensitive inputs (like API keys) in Terraform Cloud or environment variables, not in code.

Cost estimate: ~$25–50/month for low-to-moderate daily trading workloads.
