# Outputs from the AKS module

output "aks_cluster_name" {
  description = "The name of the created AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "aks_identity_principal_id" {
  description = "The Principal ID of the AKS cluster's managed identity"
  value       = azurerm_kubernetes_cluster.aks.identity[0].principal_id
}