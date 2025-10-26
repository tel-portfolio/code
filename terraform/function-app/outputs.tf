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

# NEW: Function App IP Information
output "function_app_outbound_ips" {
  description = "Current outbound IP addresses for the Function App"
  value       = azurerm_linux_function_app.algo_functionapp.outbound_ip_addresses
}

output "function_app_possible_outbound_ips" {
  description = "All possible outbound IP addresses for the Function App"
  value       = azurerm_linux_function_app.algo_functionapp.possible_outbound_ip_addresses
}

output "function_app_firewall_summary" {
  description = "Summary of firewall rules created for Function App access"
  value = {
    current_ip_rules    = length(local.function_app_outbound_ips)
    possible_ip_rules   = length(local.unique_possible_ips)
    total_rules        = length(local.function_app_outbound_ips) + length(local.unique_possible_ips)
    current_ips        = local.function_app_outbound_ips
    additional_ips     = local.unique_possible_ips
  }
}

output "service_plan_name" {
  description = "Name of the App Service Plan"
  value       = azurerm_service_plan.algo_functionapp_plan.name
}

output "service_plan_sku" {
  description = "SKU of the App Service Plan (should be Y1 for consumption)"
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

# Cost Management Information (UPDATED for consumption plan)
output "estimated_monthly_cost_notes" {
  description = "Notes about estimated costs for consumption plan"
  value = {
    function_app_plan   = "Y1 Consumption: Pay per execution (~$5-20/month depending on usage)"
    mysql_server       = "B_Standard_B1ms: ~$15-20/month"
    storage_account    = "Standard LRS: ~$1-5/month"
    key_vault         = "Standard: ~$3/month + operations"
    networking        = "No NAT Gateway or VNet costs - included with consumption plan"
    total_estimate    = "~$25-50/month (massive savings from ~$250/month premium plan)"
    note              = "Actual costs may vary based on function execution frequency"
  }
}

# Security Information
output "security_summary" {
  description = "Summary of security implementations"
  value = {
    key_vault_secrets     = "All sensitive data stored in Azure Key Vault"
    mysql_access         = "Public endpoint with specific IP firewall rules"
    function_app_auth    = "Managed identity for Key Vault access"
    ssl_enforcement      = "HTTPS-only connections enforced"
    firewall_approach    = "Dynamic IP whitelisting (no broad 0.0.0.0 rules)"
  }
}