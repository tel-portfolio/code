resource "azurerm_resource_group" "rg" {
    name = var.resource_group_name
    location = var.location
}

# Private Azure Container Registry
resource "azurerm_container_registry" "acr" {
    name = "${var.prefix}acr"
    resource_group_name = azurerm_resource_group.rg.name
    location = azurerm_resource_group.rg.location
    sku = "Basic"
    admin_enabled = true
}

# Virtual Network
resource "azurerm_virtual_network" "vnet" {
    name = "${var.prefix}-vnet"
    address_space = ["10.0.0.0/16"]
    location = azurerm_resource_group.rg.location
    resource_group_name = azurerm_resource_group.rg.name
}

# Vnet Subnet
resource "azurerm_subnet" "aks_subnet" {
    name = "aks-subnet"
    resource_group_name = azurerm_resource_group.rg.name
    virtual_network_name = azurerm_virtual_network.vnet.name
    address_prefixes = ["10.0.1.0/24"]
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
    name = "${var.prefix}-aks-cluster"
    location = azurerm_resource_group.rg.location
    resource_group_name = azurerm_resource_group.rg.name
    dns_prefix = "${var.prefix}-aks"

    default_node_pool {
        name = "default"
        node_count = 1
        vm_size = "Standard_B2s"
        vnet_subnet_id = azurerm_subnet.aks_subnet.id
    }

    # Assign Managed Identity to cluster
    identity {
        type = "SystemAssigned"
    }

    #Setup RBAC to allow Cluster to pull image from private registry
    role_based_access_control_enabled = true
    azure_policy_enabled = true
    
    depends_on = [
        azurerm_container_registry.acr
    ]
}

# Give AKS cluster identity 'ArcPull' role on the ACR
resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  
  depends_on = [
    azurerm_kubernetes_cluster.aks
  ]
}