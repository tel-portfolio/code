terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.21.1"
    }
    azapi = {
      source  = "hashicorp/azapi"
      version = "~> 1.0"
    }
  }
}
