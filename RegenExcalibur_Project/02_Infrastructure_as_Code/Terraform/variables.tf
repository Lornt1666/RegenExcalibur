variable "project_id" {
  description = "Target GCP project ID."
  type        = string

  validation {
    condition     = length(var.project_id) > 3
    error_message = "project_id must be a valid GCP project ID."
  }
}

variable "region" {
  description = "Primary GCP region for regional resources."
  type        = string
  default     = "us-central1"
}

variable "bucket_location" {
  description = "Cloud Storage bucket location."
  type        = string
  default     = "US"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "environment must use lowercase letters, numbers, and hyphens only."
  }
}

variable "resource_prefix" {
  description = "Prefix used for named GCP resources."
  type        = string
  default     = "regenexcalibur"

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+$", var.resource_prefix))
    error_message = "resource_prefix may contain letters, numbers, underscores, and hyphens."
  }
}

variable "artifact_retention_days" {
  description = "Number of days before artifacts move to NEARLINE storage."
  type        = number
  default     = 30

  validation {
    condition     = var.artifact_retention_days >= 7
    error_message = "artifact_retention_days must be at least 7."
  }
}

variable "labels" {
  description = "Additional labels applied to supported resources."
  type        = map(string)
  default     = {}
}
