# Inputs for the ACR module

variable "prefix" {
  description = "A unique prefix for all resources"
  type        = string
}

variable "location" {
  description = "The Azure region where resources will be deployed"
  type        = string
}

variable "resource_group_name" {
  description = "The name of the Azure Resource Group"
  type        = string
}