param(
  [string]$ExportsRoot = "C:\Users\Kogan\Downloads\Telegram Desktop",
  [string]$ObsidianRoot = "D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\KnowledgeBase"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent $scriptDir
$workspaceRoot = Split-Path -Parent $workspaceRoot

Push-Location $workspaceRoot
try {
  python "scripts\telegram_desktop\build_telegram_intelligence.py" `
    --exports-root $ExportsRoot `
    --obsidian-root $ObsidianRoot
} finally {
  Pop-Location
}
