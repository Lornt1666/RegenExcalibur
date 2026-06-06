terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.20.0, < 7.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  prefix = lower(replace(var.resource_prefix, "_", "-"))

  common_labels = merge(
    {
      app         = "regenexcalibur"
      environment = var.environment
      managed_by  = "terraform"
    },
    var.labels
  )

  required_services = toset([
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "eventarc.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com"
  ])
}

resource "google_project_service" "enabled" {
  for_each = local.required_services

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_service_account" "automation" {
  account_id   = "${local.prefix}-automation"
  display_name = "RegenExcalibur deployment automation"
  description  = "Used by controlled deployment automation for RegenExcalibur."

  depends_on = [google_project_service.enabled]
}

resource "google_service_account" "runtime" {
  account_id   = "${local.prefix}-runtime"
  display_name = "RegenExcalibur runtime service account"
  description  = "Runtime identity for Cloud Run and orchestration workloads."

  depends_on = [google_project_service.enabled]
}

resource "google_service_account" "function_runtime" {
  account_id   = "${local.prefix}-function"
  display_name = "RegenExcalibur Cloud Function runtime"
  description  = "Runtime identity for event ingestion functions."

  depends_on = [google_project_service.enabled]
}

resource "google_storage_bucket" "artifacts" {
  name                        = "${local.prefix}-${var.project_id}-${var.environment}-artifacts"
  location                    = var.bucket_location
  uniform_bucket_level_access = true
  force_destroy               = false
  labels                      = local.common_labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.artifact_retention_days
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  depends_on = [google_project_service.enabled]
}

resource "google_pubsub_topic" "agent_tasks" {
  name   = "${local.prefix}-agent-tasks"
  labels = local.common_labels

  depends_on = [google_project_service.enabled]
}

resource "google_pubsub_topic" "mrv_events" {
  name   = "${local.prefix}-mrv-events"
  labels = local.common_labels

  depends_on = [google_project_service.enabled]
}

resource "google_pubsub_subscription" "agent_tasks_worker" {
  name                 = "${local.prefix}-agent-tasks-worker"
  topic                = google_pubsub_topic.agent_tasks.name
  ack_deadline_seconds = 30

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s"
  }

  labels = local.common_labels
}

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "${local.prefix}-containers"
  description   = "Container images for RegenExcalibur services"
  format        = "DOCKER"
  labels        = local.common_labels

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret" "runtime_config" {
  secret_id = "${local.prefix}-runtime-config"

  replication {
    auto {}
  }

  labels = local.common_labels

  depends_on = [google_project_service.enabled]
}

resource "google_project_iam_member" "runtime_project_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_project_iam_member" "function_project_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.function_runtime.email}"
}

resource "google_storage_bucket_iam_member" "runtime_artifact_access" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_storage_bucket_iam_member" "function_artifact_access" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.function_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "runtime_secret_access" {
  secret_id = google_secret_manager_secret.runtime_config.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "function_secret_access" {
  secret_id = google_secret_manager_secret.runtime_config.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.function_runtime.email}"
}

resource "google_service_account_iam_member" "automation_can_act_as_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.automation.email}"
}

resource "google_service_account_iam_member" "automation_can_act_as_function" {
  service_account_id = google_service_account.function_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.automation.email}"
}
