param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectPath = ".",
    [Parameter(Mandatory = $false)]
    [string]$ArchivePath,
    [Parameter(Mandatory = $false)]
    [switch]$ConfirmRestore
)

$ErrorActionPreference = "Stop"
$resolved = (Resolve-Path -LiteralPath $ProjectPath).Path
$snapshotsDir = Join-Path $resolved ".snapshots"
if (-not (Test-Path -LiteralPath $snapshotsDir)) {
    throw "Snapshots folder not found: $snapshotsDir"
}

if (-not $ArchivePath) {
    $latest = Get-ChildItem -LiteralPath $snapshotsDir -Filter "*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) {
        throw "No snapshots found in: $snapshotsDir"
    }
    $ArchivePath = $latest.FullName
} else {
    $ArchivePath = (Resolve-Path -LiteralPath $ArchivePath).Path
}

if (-not $ConfirmRestore) {
    Write-Output "Restore is destructive."
    Write-Output ("Run with -ConfirmRestore to continue: {0}" -f $ArchivePath)
    exit 0
}

# Safety checkpoint before rollback.
$snapshotScript = Join-Path $PSScriptRoot "snapshot.ps1"
& $snapshotScript -ProjectPath $resolved -Label "pre_restore"

$tmp = Join-Path $env:TEMP ("restore_{0}" -f ([guid]::NewGuid().ToString("N")))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $tmp -Force

    $current = Get-ChildItem -LiteralPath $resolved -Force | Where-Object { $_.Name -ne ".snapshots" }
    foreach ($item in $current) {
        Remove-Item -LiteralPath $item.FullName -Recurse -Force
    }

    $restored = Get-ChildItem -LiteralPath $tmp -Force
    foreach ($item in $restored) {
        Copy-Item -LiteralPath $item.FullName -Destination $resolved -Recurse -Force
    }
}
finally {
    if (Test-Path -LiteralPath $tmp) {
        Remove-Item -LiteralPath $tmp -Recurse -Force
    }
}

Write-Output ("RESTORE_DONE={0}" -f $ArchivePath)
