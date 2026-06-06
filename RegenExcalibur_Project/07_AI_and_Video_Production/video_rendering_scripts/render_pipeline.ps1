param(
  [string]$FramesDir = "frames",
  [string]$Output = "regenexcalibur_render.mp4",
  [int]$Fps = 24
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  throw "ffmpeg is required for local rendering."
}

if (-not (Test-Path $FramesDir)) {
  throw "Frame directory not found: $FramesDir"
}

ffmpeg -y `
  -framerate $Fps `
  -i (Join-Path $FramesDir "frame_%04d.png") `
  -c:v libx264 `
  -pix_fmt yuv420p `
  $Output

Write-Host "Rendered $Output"
