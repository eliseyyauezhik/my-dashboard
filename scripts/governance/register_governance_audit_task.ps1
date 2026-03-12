param(
    [string]$TaskName = "AIWorkspaceGovernanceAudit",
    [int]$IntervalMinutes = 1440
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$auditScript = Join-Path $scriptDir "run_governance_audit.ps1"
if (-not (Test-Path -LiteralPath $auditScript)) {
    throw "Audit script not found: $auditScript"
}

if ($IntervalMinutes -lt 60) {
    throw "IntervalMinutes should be >= 60"
}

$action = New-ScheduledTaskAction `
    -Execute "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$auditScript`""

$triggerLogon = New-ScheduledTaskTrigger -AtLogOn
$startTime = (Get-Date).AddMinutes(5)
$repeatDuration = New-TimeSpan -Days 3650
$triggerRepeat = New-ScheduledTaskTrigger -Once -At $startTime `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration $repeatDuration

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger @($triggerLogon, $triggerRepeat) `
    -Settings $settings `
    -Description "Periodic governance audit for AI Workspace, KnowledgeBase and sync outputs." `
    -Force | Out-Null

Write-Host "Scheduled task '$TaskName' registered. Interval: $IntervalMinutes min."
