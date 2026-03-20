variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-south1"  # Mumbai — closest to Bengaluru
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"  # Cheapest. Scale up: db-g1-small, db-custom-2-4096
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "api_min_instances" {
  description = "Minimum Cloud Run instances for API (0 = scale to zero)"
  type        = number
  default     = 0  # Set to 1 in production for MCP SSE availability
}
