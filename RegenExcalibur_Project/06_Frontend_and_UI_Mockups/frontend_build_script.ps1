$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir = Join-Path $ScriptDir "UI_prototypes"
$DistDir = Join-Path $ScriptDir "dist"

if (Test-Path $DistDir) {
  Remove-Item -LiteralPath $DistDir -Recurse -Force
}

New-Item -ItemType Directory -Path $DistDir | Out-Null
Copy-Item -Path (Join-Path $SourceDir "*.html") -Destination $DistDir
Copy-Item -Path (Join-Path $SourceDir "*.css") -Destination $DistDir

Write-Host "Frontend prototype built at $DistDir"
