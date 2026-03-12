param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectPath = ".",
    [Parameter(Mandatory = $false)]
    [string]$Label = "manual"
)

$ErrorActionPreference = "Stop"
$resolved = (Resolve-Path -LiteralPath $ProjectPath).Path
$snapshotsDir = Join-Path $resolved ".snapshots"
if (-not (Test-Path -LiteralPath $snapshotsDir)) {
    New-Item -ItemType Directory -Path $snapshotsDir | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$safeLabel = ($Label -replace "[^a-zA-Z0-9_-]", "_")
$archive = Join-Path $snapshotsDir ("snapshot_{0}_{1}.zip" -f $stamp, $safeLabel)

# Keep snapshots small and avoid recursive archive-in-archive.
$items = Get-ChildItem -LiteralPath $resolved -Force | Where-Object {
    $_.Name -notin @(".snapshots", ".git", "node_modules", "__pycache__")
}

if (-not $items) {
    throw "No files to snapshot in: $resolved"
}

Compress-Archive -Path ($items.FullName) -DestinationPath $archive -CompressionLevel Optimal
Write-Output ("SNAPSHOT_CREATED={0}" -f $archive)
