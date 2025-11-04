output "resource_group_name" {
  description = "Resource group name."
  value       = azurerm_resource_group.rg.name
}

output "acr_login_server" {
  description = "Azure Container Registry FQDN."
  value       = module.azure_container_registry.acr_login_server
}

output "aks_cluster_name" {
  description = "AKS cluster name."
  value       = module.aks_cluster.aks_cluster_name
}