# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
    name = "${var.prefix}-aks-cluster"
    location = var.location
    resource_group_name = var.resource_group_name
    dns_prefix = "${var.prefix}-aks"

    default_node_pool {
        name = "default"
        node_count = 1
        vm_size = "Standard_B2s"
        vnet_subnet_id = var.subnet_id
    }

    #Define internal network for cluster
    network_profile {
        network_plugin = "kubenet"
        service_cidr = "10.1.0.0/16"
        dns_service_ip = "10.1.0.10"
    }

    # Assign Managed Identity to cluster
    identity {
        type = "SystemAssigned"
    }

    #Setup RBAC to allow Cluster to pull image from private registry
    role_based_access_control_enabled = true
    azure_policy_enabled = true
}
