[CmdletBinding()]
param(
    [string]$ManifestPath = '',
    [string]$DestinationRoot,
    [string]$ReportPath,
    [switch]$Execute,
    [switch]$IncludeDisabled,
    [switch]$IncludeHeavyArtifacts
)

$ErrorActionPreference = 'Stop'
$script:ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

if (-not $ManifestPath) {
    $ManifestPath = Join-Path $script:ScriptRoot 'projects_manifest.json'
}

function Get-Manifest {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Manifest not found: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json
}

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Test-PathInside {
    param(
        [string]$ChildPath,
        [string]$ParentPath
    )

    $child = [IO.Path]::GetFullPath($ChildPath).TrimEnd('\')
    $parent = [IO.Path]::GetFullPath($ParentPath).TrimEnd('\')
    return $child.StartsWith($parent, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-ExistingExcludePaths {
    param(
        [string]$RootPath,
        [string[]]$Names
    )

    $paths = New-Object System.Collections.Generic.List[string]
    foreach ($name in $Names) {
        $candidate = Join-Path $RootPath $name
        if (Test-Path -LiteralPath $candidate) {
            [void]$paths.Add($candidate)
        }
    }
    return $paths
}

function Invoke-DirectoryCopy {
    param(
        [string]$SourcePath,
        [string]$DestinationPath,
        [bool]$ShouldExecute,
        [bool]$IncludeHeavy
    )

    $defaultExcludes = @(
        '.git',
        '.hg',
        '.svn',
        'node_modules',
        '.venv',
        'venv',
        '__pycache__',
        '.pytest_cache',
        '.mypy_cache',
        '.ruff_cache',
        '.cache',
        '.next',
        '.parcel-cache'
    )

    $excludePaths = @()
    if (-not $IncludeHeavy) {
        $excludePaths = Get-ExistingExcludePaths -RootPath $SourcePath -Names $defaultExcludes
    }

    $robocopyArgs = @(
        $SourcePath,
        $DestinationPath,
        '/E',
        '/R:1',
        '/W:1',
        '/COPY:DAT',
        '/DCOPY:DAT',
        '/XJ',
        '/NFL',
        '/NDL',
        '/NP'
    )

    if ($excludePaths.Count -gt 0) {
        $robocopyArgs += '/XD'
        $robocopyArgs += $excludePaths
    }

    if (-not $ShouldExecute) {
        return [PSCustomObject]@{
            ExitCode = 0
            Command = 'robocopy ' + ($robocopyArgs -join ' ')
            Excluded = ($excludePaths -join '; ')
        }
    }

    Ensure-Directory -Path $DestinationPath
    & robocopy @robocopyArgs | Out-Null
    $exitCode = $LASTEXITCODE

    if ($exitCode -ge 8) {
        throw "Robocopy failed for '$SourcePath' -> '$DestinationPath' with exit code $exitCode"
    }

    return [PSCustomObject]@{
        ExitCode = $exitCode
        Command = 'robocopy ' + ($robocopyArgs -join ' ')
        Excluded = ($excludePaths -join '; ')
    }
}

$manifest = Get-Manifest -Path $ManifestPath

$resolvedDestinationRoot = if ($DestinationRoot) { $DestinationRoot } else { $manifest.destinationRoot }
if (-not $resolvedDestinationRoot) {
    throw 'Destination root is not set.'
}

$resolvedReportPath = if ($ReportPath) {
    $ReportPath
} else {
    $reportDir = if ($manifest.reportDirectory) { $manifest.reportDirectory } else { (Join-Path $resolvedDestinationRoot '_migration_reports') }
    Ensure-Directory -Path $reportDir
    Join-Path $reportDir ("migration_report_{0}.csv" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
}

Ensure-Directory -Path $resolvedDestinationRoot

$items = @($manifest.items)
if (-not $IncludeDisabled) {
    $items = $items | Where-Object { $_.enabled -ne $false }
}

$results = foreach ($item in $items) {
    $sourcePath = [string]$item.sourcePath
    $destinationPath = Join-Path $resolvedDestinationRoot ([string]$item.relativeDestination)
    $kind = if ($item.kind) { [string]$item.kind } else { 'directory' }

    $status = 'planned'
    $message = ''
    $command = ''
    $excluded = ''

    if (-not (Test-Path -LiteralPath $sourcePath)) {
        $status = 'missing_source'
        $message = 'Source path does not exist.'
    } elseif (Test-PathInside -ChildPath $destinationPath -ParentPath $sourcePath) {
        $status = 'blocked'
        $message = 'Destination is inside source; copy skipped to avoid recursion.'
    } elseif (([IO.Path]::GetFullPath($sourcePath).TrimEnd('\')) -eq ([IO.Path]::GetFullPath($destinationPath).TrimEnd('\'))) {
        $status = 'blocked'
        $message = 'Source and destination are identical.'
    } else {
        try {
            if ($kind -eq 'directory') {
                $copyResult = Invoke-DirectoryCopy -SourcePath $sourcePath -DestinationPath $destinationPath -ShouldExecute:$Execute.IsPresent -IncludeHeavy:$IncludeHeavyArtifacts.IsPresent
                $command = $copyResult.Command
                $excluded = $copyResult.Excluded
                $status = if ($Execute) { 'copied' } else { 'dry_run' }
            } else {
                Ensure-Directory -Path (Split-Path -Parent $destinationPath)
                $command = "Copy-Item -LiteralPath `"$sourcePath`" -Destination `"$destinationPath`""
                if ($Execute) {
                    Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
                    $status = 'copied'
                } else {
                    $status = 'dry_run'
                }
            }
        } catch {
            $status = 'error'
            $message = $_.Exception.Message
        }
    }

    [PSCustomObject]@{
        Timestamp = (Get-Date).ToString('s')
        Mode = if ($Execute) { 'execute' } else { 'dry-run' }
        Name = [string]$item.name
        Group = [string]$item.group
        Kind = $kind
        SourcePath = $sourcePath
        DestinationPath = $destinationPath
        Status = $status
        Message = $message
        ExcludedPaths = $excluded
        Notes = [string]$item.notes
        Command = $command
    }
}

$results | Export-Csv -Path $resolvedReportPath -NoTypeInformation -Encoding utf8

$summary = [PSCustomObject]@{
    manifest = $ManifestPath
    destinationRoot = $resolvedDestinationRoot
    report = $resolvedReportPath
    mode = if ($Execute) { 'execute' } else { 'dry-run' }
    total = $results.Count
    copied = (@($results | Where-Object { $_.Status -eq 'copied' })).Count
    dryRun = (@($results | Where-Object { $_.Status -eq 'dry_run' })).Count
    missing = (@($results | Where-Object { $_.Status -eq 'missing_source' })).Count
    blocked = (@($results | Where-Object { $_.Status -eq 'blocked' })).Count
    errors = (@($results | Where-Object { $_.Status -eq 'error' })).Count
}

$summary | ConvertTo-Json -Depth 3
