#Variables for network module

variable "prefix" {
    description = "Unique prefix for resources"
    type        = string
}

variable "location" {
    description = "Region where network is deployed"
    type        = string
}

variable "resource_group_name" {
    description = "Name of resource group"
    type        = string
}