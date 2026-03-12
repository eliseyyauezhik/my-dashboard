param(
  [Alias("Host")]
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8891,
  [switch]$Lan,
  [switch]$Open
)

$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "scripts\\dashboard\\start_dashboard.ps1"

if (-not (Test-Path -LiteralPath $script)) {
  throw "Script not found: $script"
}

& $script -BindHost $BindHost -Port $Port -Lan:$Lan -Open:$Open
