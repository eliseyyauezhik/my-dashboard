param(
    [string]$ObsidianRoot = "",
    [switch]$NoObsidianExport
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent $scriptDir
$pythonScript = Join-Path $scriptDir "sync_workspace_data.py"

if (-not (Test-Path -LiteralPath $pythonScript)) {
    throw "Script not found: $pythonScript"
}

$argsList = @($pythonScript)
if ($ObsidianRoot) {
    $argsList += @("--obsidian-root", $ObsidianRoot)
}
if ($NoObsidianExport) {
    $argsList += "--no-obsidian-export"
}

Push-Location $workspaceRoot
try {
    & python @argsList
}
finally {
    Pop-Location
}
