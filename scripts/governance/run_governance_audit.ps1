param(
    [string]$WorkspaceRoot = "",
    [string]$KnowledgeBaseRoot = "",
    [switch]$IncludeSnapshots
)

$ErrorActionPreference = "Stop"

if (-not $WorkspaceRoot) {
    $WorkspaceRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
}

$governanceConfig = Join-Path $WorkspaceRoot "config\agent_data_governance.json"
if ((-not $KnowledgeBaseRoot) -and (Test-Path -LiteralPath $governanceConfig)) {
    try {
        $configJson = Get-Content -LiteralPath $governanceConfig -Raw -Encoding utf8 | ConvertFrom-Json
        $KnowledgeBaseRoot = $configJson.dataRoots.knowledgeBase
    }
    catch {
        $KnowledgeBaseRoot = ""
    }
}

$dateTag = Get-Date -Format "yyyy-MM-dd"
$reportPath = Join-Path $WorkspaceRoot ("docs\governance_audit_{0}.md" -f $dateTag)
$snapshotScript = Join-Path $WorkspaceRoot "scripts\versioning\snapshot.ps1"
$checks = @()

function Add-Check {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Detail
    )
    $script:checks += [PSCustomObject]@{
        Name = $Name
        Status = $Status
        Detail = $Detail
    }
}

function Test-RequiredPath {
    param(
        [string]$Label,
        [string]$PathValue
    )
    if (Test-Path -LiteralPath $PathValue) {
        Add-Check -Name $Label -Status "OK" -Detail $PathValue
    }
    else {
        Add-Check -Name $Label -Status "FAIL" -Detail $PathValue
    }
}

Test-RequiredPath -Label "dashboard_data.json" -PathValue (Join-Path $WorkspaceRoot "data\dashboard_data.json")
Test-RequiredPath -Label "projects.json" -PathValue (Join-Path $WorkspaceRoot "projects.json")
Test-RequiredPath -Label "idea_inbox.json" -PathValue (Join-Path $WorkspaceRoot "data\idea_inbox.json")
Test-RequiredPath -Label "personal_system_profile.json" -PathValue (Join-Path $WorkspaceRoot "config\personal_system_profile.json")
Test-RequiredPath -Label "agent_data_governance.json" -PathValue (Join-Path $WorkspaceRoot "config\agent_data_governance.json")
Test-RequiredPath -Label "workspace/governance_regulation" -PathValue (Join-Path $WorkspaceRoot "docs\universal_agent_operating_regulation.md")
Test-RequiredPath -Label "workspace/governance_checklist" -PathValue (Join-Path $WorkspaceRoot "docs\agent_governance_checklist.md")

if ($KnowledgeBaseRoot) {
    Test-RequiredPath -Label "knowledgebase/root" -PathValue $KnowledgeBaseRoot
    Test-RequiredPath -Label "knowledgebase/config_dir" -PathValue (Join-Path $KnowledgeBaseRoot "Config")
    Test-RequiredPath -Label "knowledgebase/dashboards_dir" -PathValue (Join-Path $KnowledgeBaseRoot "Dashboards")
}
else {
    Add-Check -Name "knowledgebase/root" -Status "FAIL" -Detail "not resolved from config"
}

if ($IncludeSnapshots) {
    try {
        & $snapshotScript -ProjectPath $WorkspaceRoot -Label "governance_audit" | Out-Null
        Add-Check -Name "workspace_snapshot" -Status "OK" -Detail "snapshot created"
    }
    catch {
        Add-Check -Name "workspace_snapshot" -Status "FAIL" -Detail $_.Exception.Message
    }

    if ($KnowledgeBaseRoot -and (Test-Path -LiteralPath $KnowledgeBaseRoot)) {
        try {
            & $snapshotScript -ProjectPath $KnowledgeBaseRoot -Label "governance_audit" | Out-Null
            Add-Check -Name "knowledgebase_snapshot" -Status "OK" -Detail "snapshot created"
        }
        catch {
            Add-Check -Name "knowledgebase_snapshot" -Status "FAIL" -Detail $_.Exception.Message
        }
    }
}

try {
    python -m py_compile (Join-Path $WorkspaceRoot "scripts\dashboard\sync_workspace_data.py") `
        (Join-Path $WorkspaceRoot "scripts\dashboard\dashboard_server.py") `
        (Join-Path $WorkspaceRoot "scripts\governance\build_governance_docs.py") | Out-Null
    Add-Check -Name "python_compile" -Status "OK" -Detail "key scripts compiled"
}
catch {
    Add-Check -Name "python_compile" -Status "FAIL" -Detail $_.Exception.Message
}

try {
    node --check (Join-Path $WorkspaceRoot "app.js") | Out-Null
    node --check (Join-Path $WorkspaceRoot "mindmap.js") | Out-Null
    Add-Check -Name "node_syntax" -Status "OK" -Detail "app.js + mindmap.js"
}
catch {
    Add-Check -Name "node_syntax" -Status "FAIL" -Detail $_.Exception.Message
}

try {
    $secretPattern = '(?i)((api[_-]?key|token|secret|password)\s*[:=]\s*[''""][^''""]+|BEGIN PRIVATE KEY|Bearer\s+[A-Za-z0-9._-]+)'
    $secretHits = rg -n -P $secretPattern `
        $WorkspaceRoot `
        --glob "!*.zip" `
        --glob "!.snapshots/**" `
        --glob "!node_modules/**" `
        --glob "!__pycache__/**" `
        --glob "!docs/**" `
        --glob "!data/mindmap.json" `
        --glob "!data/dashboard_data.json" `
        --glob "!projects.json" `
        --glob "!scripts/governance/run_governance_audit.ps1"
    if ($LASTEXITCODE -eq 0 -and $secretHits) {
        $preview = ($secretHits | Select-Object -First 5) -join "; "
        Add-Check -Name "secret_scan" -Status "WARN" -Detail $preview
    }
    else {
        Add-Check -Name "secret_scan" -Status "OK" -Detail "no obvious secret patterns in workspace"
    }
}
catch {
    Add-Check -Name "secret_scan" -Status "FAIL" -Detail $_.Exception.Message
}

$lines = @(
    "# Governance Audit",
    "",
    "Updated: $(Get-Date -Format s)",
    "",
    "## Results"
)

foreach ($check in $checks) {
    $lines += "- **$($check.Name)** [$($check.Status)] - $($check.Detail)"
}

$failCount = @($checks | Where-Object { $_.Status -eq "FAIL" }).Count
$warnCount = @($checks | Where-Object { $_.Status -eq "WARN" }).Count
$okCount = @($checks | Where-Object { $_.Status -eq "OK" }).Count

$lines += ""
$lines += "## Summary"
$lines += "- OK: $okCount"
$lines += "- WARN: $warnCount"
$lines += "- FAIL: $failCount"

Set-Content -Path $reportPath -Value ($lines -join "`r`n") -Encoding utf8
Write-Output ("GOVERNANCE_AUDIT={0}" -f $reportPath)
