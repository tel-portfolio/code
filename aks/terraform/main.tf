resource "azurerm_resource_group" "rg" {
    name = var.resource_group_name
    location = var.location
}

module "virtual_network" {
    source = "./modules/network"
    location = azurerm_resource_group.rg.location
    resource_group_name = azurerm_resource_group.rg.name
    prefix = var.prefix
}

module "azure_container_registry" {
    source = "./modules/acr"
    location = azurerm_resource_group.rg.location
    resource_group_name = azurerm_resource_group.rg.name
    prefix = var.prefix
}

module "aks_cluster" {
    source = "./modules/aks"
    location = azurerm_resource_group.rg.location
    resource_group_name = azurerm_resource_group.rg.name
    prefix = var.prefix

    subnet_id = module.virtual_network.subnet_id
    
    depends_on = [
        module.azure_container_registry
    ]
}

# Give AKS cluster identity 'ArcPull' role on the ACR
resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = module.azure_container_registry.acr_id
  role_definition_name = "AcrPull"
  principal_id         = module.aks_cluster.aks_identity_principal_id
  
  depends_on = [
    module.aks_cluster
  ]
}