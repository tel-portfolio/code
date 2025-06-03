# Configurations
resource "random_string" "suffix" {
  length  = 4
  upper   = false
  numeric = true
  special = false
}

terraform {
  backend "remote" {
    organization = "TelPortfolio"
    workspaces {
      name = "Functionapp-Live"
    }
  }
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

data "azurerm_client_config" "current" {}

# Create Resource Group
resource "azurerm_resource_group" "algo_functionapp_rg" {
  name     = "rg-functionapp-${var.environment}"
  location = var.location
}

# -- Storage Account --
resource "azurerm_storage_account" "storage_functionapp" {
  name                     = "storagefapp${var.environment}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.algo_functionapp_rg.name
  location                 = azurerm_resource_group.algo_functionapp_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = var.environment
  }
}

# -- Azure Key Vault --
resource "azurerm_key_vault" "functionapp_kv" {
  name                       = "kv-${var.environment}-functionapp"
  location                   = azurerm_resource_group.algo_functionapp_rg.location
  resource_group_name        = azurerm_resource_group.algo_functionapp_rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  tags = {
    environment = var.environment
  }

  lifecycle {
    ignore_changes = [
    ]
  }
}

#Key Vault Access Policy
# Access Policy for Terraform
resource "azurerm_key_vault_access_policy" "terraform_policy" {
  key_vault_id = azurerm_key_vault.functionapp_kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete"
  ]
}

# Access Policy for Functionapp
resource "azurerm_key_vault_access_policy" "funcapp_policy" {
  key_vault_id = azurerm_key_vault.functionapp_kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_function_app.algo_functionapp.identity[0].principal_id

  secret_permissions = [
    "Get",
    "List"
  ]

  depends_on = [azurerm_linux_function_app.algo_functionapp]
}

resource "azurerm_key_vault_secret" "sql_admin_password" {
  name         = "sql-admin-password"
  value        = var.sql_admin_password
  key_vault_id = azurerm_key_vault.functionapp_kv.id

  depends_on = [azurerm_key_vault_access_policy.terraform_policy]
}

resource "azurerm_key_vault_secret" "alpaca_api_key" {
  name         = "alpaca-api-key"
  value        = var.alpaca_api_key
  key_vault_id = azurerm_key_vault.functionapp_kv.id

  depends_on = [azurerm_key_vault_access_policy.terraform_policy]
}

resource "azurerm_key_vault_secret" "alpaca_secret_key" {
  name         = "alpaca-secret-key"
  value        = var.alpaca_secret_key
  key_vault_id = azurerm_key_vault.functionapp_kv.id

  depends_on = [azurerm_key_vault_access_policy.terraform_policy]
}

resource "azurerm_key_vault_secret" "marketstack_api_key" {
  name         = "marketstack-api-key"
  value        = var.marketstack_api_key
  key_vault_id = azurerm_key_vault.functionapp_kv.id

  depends_on = [azurerm_key_vault_access_policy.terraform_policy]
}

resource "azurerm_key_vault_secret" "sendgrid_api_key" {
  name         = "sendgrid-api-key"
  value        = var.sendgrid_api_key
  key_vault_id = azurerm_key_vault.functionapp_kv.id

  depends_on = [azurerm_key_vault_access_policy.terraform_policy]
}

# -- Virtual Network --
resource "azurerm_virtual_network" "algo_vnet" {
  name                = "vnet-algo-${var.environment}"
  location            = azurerm_resource_group.algo_functionapp_rg.location
  resource_group_name = azurerm_resource_group.algo_functionapp_rg.name
  address_space       = ["10.0.0.0/16"]

  tags = {
    environment = var.environment
  }
}

resource "azurerm_subnet" "algo_subnet" {
  name                 = "subnet-algo-${var.environment}"
  resource_group_name  = azurerm_resource_group.algo_functionapp_rg.name
  virtual_network_name = azurerm_virtual_network.algo_vnet.name
  address_prefixes     = ["10.0.1.0/24"]

  delegation {
    name = "fs"
    service_delegation {
      name = "Microsoft.DBforMySQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

resource "azurerm_subnet" "function_subnet" {
  name                 = "subnet-function-${var.environment}"
  resource_group_name  = azurerm_resource_group.algo_functionapp_rg.name
  virtual_network_name = azurerm_virtual_network.algo_vnet.name
  address_prefixes     = ["10.0.2.0/24"]

  delegation {
    name = "webapp"
    service_delegation {
      name = "Microsoft.Web/serverFarms"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/action"
      ]
    }
  }
}

resource "azurerm_private_dns_zone" "mysql_dns" {
  name                = "privatelink.mysql.database.azure.com"
  resource_group_name = azurerm_resource_group.algo_functionapp_rg.name

  tags = {
    environment = var.environment
  }
}

resource "azurerm_private_dns_zone_virtual_network_link" "mysql_dns_link" {
  name                  = "mysql-dns-link"
  resource_group_name   = azurerm_resource_group.algo_functionapp_rg.name
  private_dns_zone_name = azurerm_private_dns_zone.mysql_dns.name
  virtual_network_id    = azurerm_virtual_network.algo_vnet.id

  tags = {
    environment = var.environment
  }
}

# -- MySQL Server --
resource "azurerm_mysql_flexible_server" "mysql_server" {
  name                   = "mysql-${var.environment}-server"
  resource_group_name    = azurerm_resource_group.algo_functionapp_rg.name
  location               = azurerm_resource_group.algo_functionapp_rg.location
  administrator_login    = var.sql_admin_user
  administrator_password = var.sql_admin_password
  backup_retention_days  = 7
  sku_name              = "B_Standard_B1ms"
  version               = "8.0.21"

  delegated_subnet_id    = azurerm_subnet.algo_subnet.id
  private_dns_zone_id    = azurerm_private_dns_zone.mysql_dns.id

  storage {
    auto_grow_enabled = true
    size_gb          = 20
  }

  tags = {
    environment = var.environment
  }

  depends_on = [
    azurerm_subnet.algo_subnet,
    azurerm_private_dns_zone_virtual_network_link.mysql_dns_link
  ]
}

# MySQL databases
resource "azurerm_mysql_flexible_database" "algo_data" {
  name                = "algo_data"
  resource_group_name = azurerm_resource_group.algo_functionapp_rg.name
  server_name         = azurerm_mysql_flexible_server.mysql_server.name
  charset             = "utf8"
  collation           = "utf8_unicode_ci"
}

resource "azurerm_mysql_flexible_database" "market_cache" {
  name                = "market_cache"
  resource_group_name = azurerm_resource_group.algo_functionapp_rg.name
  server_name         = azurerm_mysql_flexible_server.mysql_server.name
  charset             = "utf8"
  collation           = "utf8_unicode_ci"
}

# NAT Gateway for outbound internet access (COMMENT OUT TO SAVE COSTS)
resource "azurerm_public_ip" "nat_gateway_ip" {
  name                = "natgw-pip-${var.environment}"
  location            = azurerm_resource_group.algo_functionapp_rg.location
  resource_group_name = azurerm_resource_group.algo_functionapp_rg.name
  allocation_method   = "Static"
  sku                 = "Standard"
  
  tags = {
    environment = var.environment
  }
}

resource "azurerm_nat_gateway" "algo_nat" {
  name                = "natgw-${var.environment}"
  location            = azurerm_resource_group.algo_functionapp_rg.location
  resource_group_name = azurerm_resource_group.algo_functionapp_rg.name
  sku_name           = "Standard"
  
  tags = {
    environment = var.environment
  }
}

resource "azurerm_nat_gateway_public_ip_association" "algo_nat_ip" {
  nat_gateway_id       = azurerm_nat_gateway.algo_nat.id
  public_ip_address_id = azurerm_public_ip.nat_gateway_ip.id
}

resource "azurerm_subnet_nat_gateway_association" "function_nat" {
  subnet_id      = azurerm_subnet.function_subnet.id
  nat_gateway_id = azurerm_nat_gateway.algo_nat.id
}

# -- Function App --
resource "azurerm_service_plan" "algo_functionapp_plan" {
  name                = "empire-algo-${var.environment}"
  location            = azurerm_resource_group.algo_functionapp_rg.location
  resource_group_name = azurerm_resource_group.algo_functionapp_rg.name
  os_type             = "Linux"
  sku_name            = "EP1"  # Elastic Premium instead of Y1

  tags = {
    environment = var.environment
  }
}

resource "azurerm_application_insights" "insights" {
  name                = "appi-functionapp-${var.environment}"
  location            = azurerm_resource_group.algo_functionapp_rg.location
  resource_group_name = azurerm_resource_group.algo_functionapp_rg.name
  application_type    = "web"

  tags = {
    environment = var.environment
  }
}

resource "azurerm_linux_function_app" "algo_functionapp" {
  name                       = "empire-algo-${var.environment}"
  resource_group_name        = azurerm_resource_group.algo_functionapp_rg.name
  location                   = azurerm_resource_group.algo_functionapp_rg.location
  service_plan_id            = azurerm_service_plan.algo_functionapp_plan.id
  storage_account_name       = azurerm_storage_account.storage_functionapp.name
  storage_account_access_key = azurerm_storage_account.storage_functionapp.primary_access_key
  https_only                 = true

  site_config {
    application_insights_connection_string = azurerm_application_insights.insights.connection_string
    
    application_stack {
      python_version = "3.11"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
  }

  app_settings = {
    FUNCTIONS_EXTENSION_VERSION = "~4"

    ALGO_DB_HOST = azurerm_mysql_flexible_server.mysql_server.fqdn
    ALGO_DB_USER = var.sql_admin_user
    ALGO_DB_NAME = azurerm_mysql_flexible_database.market_cache.name

    CACHE_DB_HOST = azurerm_mysql_flexible_server.mysql_server.fqdn
    CACHE_DB_USER = var.sql_admin_user
    CACHE_DB_NAME = azurerm_mysql_flexible_database.algo_data.name

    ALGO_DB_PASSWORD            = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.functionapp_kv.name};SecretName=sql-admin-password)"
    CACHE_DB_PASSWORD           = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.functionapp_kv.name};SecretName=sql-admin-password)"
    ALPACA_API_KEY              = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.functionapp_kv.name};SecretName=alpaca-api-key)"
    ALPACA_SECRET_KEY           = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.functionapp_kv.name};SecretName=alpaca-secret-key)"
    MARKETSTACK_API_KEY         = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.functionapp_kv.name};SecretName=marketstack-api-key)"
    SENDGRID_API_KEY            = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.functionapp_kv.name};SecretName=sendgrid-api-key)"

    ALPACA_BASE_URL             = var.alpaca_base_url
    WATCHLIST_SPREADSHEET_ID    = var.watchlist_spreadsheet_id
    WATCHLIST_RANGE             = var.watchlist_range
    EMAIL_RECIPIENTS            = var.email_recipients
    SIMULATION_MODE             = var.simulation_mode
    AZURE_STORAGE_CONNECTION_STRING = azurerm_storage_account.storage_functionapp.primary_connection_string
  }

  depends_on = [
    azurerm_key_vault_secret.sql_admin_password,
    azurerm_key_vault_secret.alpaca_api_key,
    azurerm_key_vault_secret.alpaca_secret_key,
    azurerm_key_vault_secret.marketstack_api_key,
    azurerm_key_vault_secret.sendgrid_api_key,
    azurerm_key_vault_access_policy.terraform_policy
  ]
}

# VNet Integration for Function App
resource "azurerm_app_service_virtual_network_swift_connection" "function_vnet_integration" {
  app_service_id = azurerm_linux_function_app.algo_functionapp.id
  subnet_id      = azurerm_subnet.function_subnet.id
}