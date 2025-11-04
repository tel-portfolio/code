# Network module outputs

output "subnet_id" {
    description = "ID of AKS subnet"
    value = azurerm_subnet.aks_subnet.id
}