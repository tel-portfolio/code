# Inputs for AKS

variable "prefix" {
    description = "Unique prefix for all resources"
    type        = string
}

variable "location" {
    description = "Region where resources will be deployed"
   type        = string
}

variable "resource_group_name" {
    description = "Name of Resource Group"
    type        = string
}

variable "subnet_id" {
    description = "ID of AKS subnet"
   type        = string
}