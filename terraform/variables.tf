variable "location" {
  description = "Azure region for deployment"
  type        = string
  default     = "West US 2"
}

variable "environment" {
  description = "Environment type (dev, prod, live)"
  type        = string
  default     = "live"
}

# MySQL variables (keep password as sensitive variable)
variable "sql_admin_user" {
  description = "MySQL administrator login name"
  type        = string
  default     = "mysqladmin"
}

variable "sql_admin_password" {
  description = "MySQL administrator password (stored in Terraform Cloud as sensitive)"
  type        = string
  sensitive   = true
}

# Alpaca Trading API (keep as sensitive variables)
variable "alpaca_api_key" {
  description = "API key for Alpaca trading account (stored in Terraform Cloud as sensitive)"
  type        = string
  sensitive   = true
}

variable "alpaca_secret_key" {
  description = "Secret key for Alpaca trading account (stored in Terraform Cloud as sensitive)"
  type        = string
  sensitive   = true
}

# Marketstack API
variable "marketstack_api_key" {
  description = "API key for Marketstack financial data (stored in Terraform Cloud as sensitive)"
  type        = string
  sensitive   = true
}

# SendGrid Email Service
variable "sendgrid_api_key" {
  description = "API key for SendGrid email delivery (stored in Terraform Cloud as sensitive)"
  type        = string
  sensitive   = true
}

# Non-sensitive configuration variables
variable "alpaca_base_url" {
  description = "Base URL for Alpaca API (e.g., https://paper-api.alpaca.markets)"
  type        = string
  default     = "https://paper-api.alpaca.markets"
}

variable "watchlist_spreadsheet_id" {
  description = "Google Sheets document ID for the stock watchlist"
  type        = string
}

variable "watchlist_range" {
  description = "Cell range in the watchlist spreadsheet to read (e.g., Sheet1!A2:A100)"
  type        = string
  default     = "Sheet1!A2:A100"
}

variable "email_recipients" {
  description = "Comma-separated list of alert recipient emails"
  type        = string
}

variable "simulation_mode" {
  description = "Enable simulation mode for trading logic"
  type        = string
  default     = "true"
}