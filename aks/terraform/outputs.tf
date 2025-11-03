output "resource_group_name" {
  description = "Resource group name."
  value       = azurerm_resource_group.rg.name
}

output "acr_login_server" {
  description = "Azure Container Registry FQDN."
  value       = azurerm_container_registry.acr.login_server
}

output "aks_cluster_name" {
  description = "AKS cluster name."
  value       = azurerm_kubernetes_cluster.aks.name
}