# Scaling and Optimization Guide

## Cloud Run

- Start with minimum instances set to zero for development.
- Use request concurrency based on endpoint cost and latency.
- Increase CPU and memory only after reviewing logs and traces.
- Keep `/healthz` lightweight.

## Pub/Sub

- Monitor undelivered messages and oldest unacked message age.
- Use dead-letter topics for production workflows.
- Keep messages small and store large payloads in Cloud Storage.

## Cloud Functions

- Use Gen2 functions for better concurrency and Cloud Run integration.
- Tune retry policies to avoid runaway retries.
- Use structured logs for correlation.

## Vertex AI

- Use regional resources near the data and services.
- Track model job cost by labels and job display names.
- Separate experimentation from production pipelines.

## Storage

- Use lifecycle rules for artifacts.
- Keep sensitive objects private.
- Use signed URLs only for time-bound access.

## Cost Controls

- Apply environment labels.
- Review Cloud Billing reports after first deployment.
- Use budgets and alerts before production rollout.
- Keep dry-run mode in local development.
