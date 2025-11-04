variable "prefix" {
  description = "Unique prefix for all resources"
  type        = string
  default     = "akspipeline"
}

variable "location" {
  description = "Region where resources will be deployed"
  type        = string
  default     = "West US"
}

variable "resource_group_name" {
  description = "Resource Group name"
  type        = string
  default     = "aks-pipeline-rg"
}

variable "image_tag" {
  description = "Tag for container image"
  type = string
  default = "latest"
}