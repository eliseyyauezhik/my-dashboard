param(
    [string]$TaskName = "AIWorkspaceInterestMonitoring",
    [int]$IntervalMinutes = 60
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$syncScript = Join-Path $scriptDir "sync_all_sources.ps1"
if (-not (Test-Path -LiteralPath $syncScript)) {
    throw "Sync script not found: $syncScript"
}

if ($IntervalMinutes -lt 15) {
    throw "IntervalMinutes should be >= 15"
}

$action = New-ScheduledTaskAction `
    -Execute "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$syncScript`""

$triggerLogon = New-ScheduledTaskTrigger -AtLogOn
$startTime = (Get-Date).AddMinutes(2)
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
    -Description "Refresh AI Workspace, Telegram intelligence and monitoring recommendations." `
    -Force | Out-Null

Write-Host "Scheduled task '$TaskName' registered. Interval: $IntervalMinutes min."
