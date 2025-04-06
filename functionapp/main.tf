# Variables
variable "mysql_admin_password" {
  description = "The admin password for the MySQL Flexible Server"
  type        = string
  sensitive   = true
}
variable "alpacas_api_key" {
  description = "Alpacas API Key"
  type        = string
  sensitive   = true
}
variable "alpacas_secret_key" {
  description = "Alpacas Secret Key"
  type        = string
  sensitive   = true
}
variable "marketstack_api_key" {
  description = "Marketstack API"
  type        = string
  sensitive   = true
}
variable "send_grid_api" {
  description = "Sendgrid API"
  type        = string
  sensitive   = true
}

# Use Azure Provider
provider "azurerm" {
    features {}

    client_id       = "fake_value"
    client_secret   = "fake_value"
    tenant_id       = "fake_value"
    subscription_id = "fake_value"
}

# Generate a random suffix for resource names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Resource Group
resource "azurerm_resource_group" "algo_rg" {
    name     = "algo-function-app"
    location = "West US 2"
}

# Virtual Network
resource "azurerm_virtual_network" "vnet" {
    name                = "algo_function_vnet"
    location            = azurerm_resource_group.algo_rg.location
    resource_group_name = azurerm_resource_group.algo_rg.name
    address_space       = ["10.0.0.0/16"]
}

# Subnet for MySQL Flexible Server (delegated)
resource "azurerm_subnet" "mysql_subnet" {
    name                 = "mysql_subnet"
    resource_group_name  = azurerm_resource_group.algo_rg.name
    virtual_network_name = azurerm_virtual_network.vnet.name
    address_prefixes     = ["10.0.1.0/24"]

    delegation {
        name = "mysql-delegation"
        service_delegation {
            name    = "Microsoft.DBforMySQL/flexibleServers"
            actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
        }
    }
}

# Subnet for Function App VNet Integration
resource "azurerm_subnet" "function_subnet" {
    name                 = "function_subnet"
    resource_group_name  = azurerm_resource_group.algo_rg.name
    virtual_network_name = azurerm_virtual_network.vnet.name
    address_prefixes     = ["10.0.2.0/24"]
}

# Subnet for Private Endpoint (non-delegated)
resource "azurerm_subnet" "private_endpoint_subnet" {
    name                 = "private_endpoint_subnet"
    resource_group_name  = azurerm_resource_group.algo_rg.name
    virtual_network_name = azurerm_virtual_network.vnet.name
    address_prefixes     = ["10.0.3.0/24"]
}

# Private DNS for MySQL
resource "azurerm_private_dns_zone" "mysql_private_dns" {
    name                = "privatelink.mysql.database.azure.com"
    resource_group_name = azurerm_resource_group.algo_rg.name
}

# Link Private DNS Zone to VNET
resource "azurerm_private_dns_zone_virtual_network_link" "mysql_vnet_link" {
    name                  = "mysql-vnet-link"
    private_dns_zone_name = azurerm_private_dns_zone.mysql_private_dns.name
    virtual_network_id    = azurerm_virtual_network.vnet.id
    resource_group_name   = azurerm_resource_group.algo_rg.name
}

# MySQL Flexible Server
resource "azurerm_mysql_flexible_server" "mysql_server" {
    name                = "mysql-flexible-${random_string.suffix.result}"
    resource_group_name = azurerm_resource_group.algo_rg.name
    location            = azurerm_resource_group.algo_rg.location
    administrator_login = "mysqladmin"
    administrator_password = var.mysql_admin_password

    sku_name = "GP_Standard_D2ds_v4"

    storage {
        size_gb = 32
    }

    depends_on = [
      azurerm_private_dns_zone.mysql_private_dns,
      azurerm_private_dns_zone_virtual_network_link.mysql_vnet_link
    ]
}

# Private Endpoint for MySQL (use non-delegated subnet)
resource "azurerm_private_endpoint" "mysql_private_endpoint" {
    name                = "mysql-private-endpoint"
    location            = azurerm_resource_group.algo_rg.location
    resource_group_name = azurerm_resource_group.algo_rg.name
    subnet_id           = azurerm_subnet.private_endpoint_subnet.id

    private_service_connection {
      name                           = "mysql-private-connection"
      private_connection_resource_id = azurerm_mysql_flexible_server.mysql_server.id
      subresource_names              = ["mysqlServer"]
      is_manual_connection           = false
    }
}

# Create MySQL Databases
resource "azurerm_mysql_flexible_database" "database1" {
  name                = "algo_data"
  resource_group_name = azurerm_resource_group.algo_rg.name
  server_name         = azurerm_mysql_flexible_server.mysql_server.name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
  depends_on          = [azurerm_mysql_flexible_server.mysql_server]
}

resource "azurerm_mysql_flexible_database" "database2" {
  name                = "cache"
  resource_group_name = azurerm_resource_group.algo_rg.name
  server_name         = azurerm_mysql_flexible_server.mysql_server.name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
  depends_on          = [azurerm_mysql_flexible_server.mysql_server]
}

# Storage Account
resource "azurerm_storage_account" "function_storage" {
    name                     = "funcstorage${random_string.suffix.result}"
    resource_group_name      = azurerm_resource_group.algo_rg.name
    location                 = azurerm_resource_group.algo_rg.location
    account_tier             = "Standard"
    account_replication_type = "LRS"
}

# Function App Service Plan (Premium)
resource "azurerm_service_plan" "function_plan" {
    name                = "func-app-service-plan-${random_string.suffix.result}"
    resource_group_name = azurerm_resource_group.algo_rg.name
    location            = azurerm_resource_group.algo_rg.location
    os_type             = "Linux"
    sku_name            = "P1v2"
}

# Function App with VNet Integration
resource "azurerm_linux_function_app" "algo_function" {
    name                       = "algo-function-app"
    resource_group_name        = azurerm_resource_group.algo_rg.name
    location                   = azurerm_resource_group.algo_rg.location
    service_plan_id            = azurerm_service_plan.function_plan.id
    storage_account_name       = azurerm_storage_account.function_storage.name
    storage_account_access_key = azurerm_storage_account.function_storage.primary_access_key

    app_settings = {
      FUNCTIONS_WORKER_RUNTIME = "python"
      # Algo Database
      ALGO_DB_HOST               = azurerm_mysql_flexible_server.mysql_server.fqdn
      ALGO_DB_NAME       = azurerm_mysql_flexible_database.database1.name
      ALGO_DB_USER               = azurerm_mysql_flexible_server.mysql_server.administrator_login
      ALGO_DB_PASSWORD           = var.mysql_admin_password
      # Cache Database
      CACHE_DB_HOST               = azurerm_mysql_flexible_server.mysql_server.fqdn
      CACHE_DB_NAME       = azurerm_mysql_flexible_database.database2.name
      CACHE_DB_USER               = azurerm_mysql_flexible_server.mysql_server.administrator_login
      CACHE_DB_PASSWORD           = var.mysql_admin_password
      # Alpacas
      ALPACA_API_KEY = var.alpacas_api_key
      ALPACA_SECRET_KEY = var.alpacas_secret_key
      # Marketstack
      MARKETSTACK_API_KEY = var.marketstack_api_key
      # Sendgrid
      SENDGRID_API_KEY = var.send_grid_api
    }

    site_config {
      application_stack {
        python_version = "3.9"
      }
      vnet_route_all_enabled = true
    }

    depends_on = [
      azurerm_mysql_flexible_server.mysql_server,
      azurerm_mysql_flexible_database.database1,
      azurerm_mysql_flexible_database.database2,
      azurerm_service_plan.function_plan,
      azurerm_private_endpoint.mysql_private_endpoint
    ]
}
