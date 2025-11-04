# Outputs from the ACR module

output "acr_id" {
  description = "ID of the ACR resource"
  value       = azurerm_container_registry.acr.id
}

output "acr_login_server" {
  description = "FQDN of the ACR"
  value       = azurerm_container_registry.acr.login_server
}