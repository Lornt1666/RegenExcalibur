param(
  [Parameter(Mandatory = $true)]
  [string]$ProjectId,

  [string]$Region = "us-central1",
  [string]$Environment = "dev",
  [switch]$Apply
)

$ErrorActionPreference = "Stop"

foreach ($tool in @("gcloud", "terraform")) {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
    throw "Required tool not found: $tool"
  }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformDir = Resolve-Path (Join-Path $ScriptDir "..\Terraform")

Write-Host "Enabling required APIs for $ProjectId."
gcloud services enable `
  serviceusage.googleapis.com `
  iam.googleapis.com `
  run.googleapis.com `
  cloudfunctions.googleapis.com `
  storage.googleapis.com `
  pubsub.googleapis.com `
  secretmanager.googleapis.com `
  monitoring.googleapis.com `
  logging.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  eventarc.googleapis.com `
  aiplatform.googleapis.com `
  --project $ProjectId

Push-Location $TerraformDir
try {
  terraform init
  terraform plan `
    "-var=project_id=$ProjectId" `
    "-var=region=$Region" `
    "-var=environment=$Environment" `
    -out=tfplan

  if ($Apply) {
    Write-Host "Applying Terraform plan."
    terraform apply tfplan
  } else {
    Write-Host "Dry run complete. Re-run with -Apply to provision resources."
  }
}
finally {
  Pop-Location
}
