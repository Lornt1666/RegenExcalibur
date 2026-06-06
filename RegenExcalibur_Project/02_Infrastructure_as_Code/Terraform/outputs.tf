output "artifact_bucket_name" {
  description = "Cloud Storage bucket for RegenExcalibur artifacts."
  value       = google_storage_bucket.artifacts.name
}

output "agent_tasks_topic" {
  description = "Pub/Sub topic used for agent task messages."
  value       = google_pubsub_topic.agent_tasks.name
}

output "mrv_events_topic" {
  description = "Pub/Sub topic used for MRV audit events."
  value       = google_pubsub_topic.mrv_events.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository."
  value       = google_artifact_registry_repository.containers.name
}

output "runtime_service_account_email" {
  description = "Cloud Run and orchestration runtime identity."
  value       = google_service_account.runtime.email
}

output "function_service_account_email" {
  description = "Cloud Function runtime identity."
  value       = google_service_account.function_runtime.email
}

output "runtime_config_secret" {
  description = "Secret Manager secret for runtime configuration."
  value       = google_secret_manager_secret.runtime_config.id
}
