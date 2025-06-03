# Core Infrastructure Outputs
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.algo_functionapp_rg.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.algo_functionapp_rg.location
}

# Storage Outputs
output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.storage_functionapp.name
}

output "storage_account_primary_connection_string" {
  description = "Primary connection string for the storage account"
  value       = azurerm_storage_account.storage_functionapp.primary_connection_string
  sensitive   = true
}

# Key Vault Outputs
output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.functionapp_kv.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.functionapp_kv.vault_uri
}

# Database Outputs
output "mysql_server_name" {
  description = "Name of the MySQL server"
  value       = azurerm_mysql_flexible_server.mysql_server.name
}

output "mysql_server_fqdn" {
  description = "Fully qualified domain name of the MySQL server"
  value       = azurerm_mysql_flexible_server.mysql_server.fqdn
}

output "mysql_databases" {
  description = "List of MySQL databases created"
  value = {
    algo_data    = azurerm_mysql_flexible_database.algo_data.name
    market_cache = azurerm_mysql_flexible_database.market_cache.name
  }
}

# Networking Outputs
output "virtual_network_name" {
  description = "Name of the virtual network"
  value       = azurerm_virtual_network.algo_vnet.name
}

output "virtual_network_address_space" {
  description = "Address space of the virtual network"
  value       = azurerm_virtual_network.algo_vnet.address_space
}

output "subnets" {
  description = "Information about created subnets"
  value = {
    algo_subnet = {
      name             = azurerm_subnet.algo_subnet.name
      address_prefixes = azurerm_subnet.algo_subnet.address_prefixes
    }
    function_subnet = {
      name             = azurerm_subnet.function_subnet.name
      address_prefixes = azurerm_subnet.function_subnet.address_prefixes
    }
  }
}

output "nat_gateway_public_ip" {
  description = "Public IP address of the NAT Gateway"
  value       = azurerm_public_ip.nat_gateway_ip.ip_address
}

# Function App Outputs
output "function_app_name" {
  description = "Name of the Function App"
  value       = azurerm_linux_function_app.algo_functionapp.name
}

output "function_app_default_hostname" {
  description = "Default hostname of the Function App"
  value       = azurerm_linux_function_app.algo_functionapp.default_hostname
}

output "function_app_identity" {
  description = "Managed identity information for the Function App"
  value = {
    principal_id = azurerm_linux_function_app.algo_functionapp.identity[0].principal_id
    tenant_id    = azurerm_linux_function_app.algo_functionapp.identity[0].tenant_id
  }
}

output "service_plan_name" {
  description = "Name of the App Service Plan"
  value       = azurerm_service_plan.algo_functionapp_plan.name
}

output "service_plan_sku" {
  description = "SKU of the App Service Plan"
  value       = azurerm_service_plan.algo_functionapp_plan.sku_name
}

# Monitoring Outputs
output "application_insights_name" {
  description = "Name of Application Insights"
  value       = azurerm_application_insights.insights.name
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.insights.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.insights.connection_string
  sensitive   = true
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "deployment_timestamp" {
  description = "Timestamp of the deployment"
  value       = timestamp()
}

# Cost Management Information
output "estimated_monthly_cost_notes" {
  description = "Notes about estimated costs"
  value = {
    function_app_plan = "EP1 Elastic Premium: ~$150-200/month"
    mysql_server     = "B_Standard_B1ms: ~$15-20/month"
    nat_gateway      = "Standard NAT Gateway: ~$45/month + data processing"
    storage_account  = "Standard LRS: ~$1-5/month"
    key_vault       = "Standard: ~$3/month + operations"
    note            = "Actual costs may vary based on usage patterns"
  }
}