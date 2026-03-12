param(
  [string]$ObsidianRoot = "",
  [string]$ExportsRoot = "C:\Users\Kogan\Downloads\Telegram Desktop"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

function Resolve-ObsidianRoot {
  param([string]$ExplicitPath)

  if ($ExplicitPath -and (Test-Path -LiteralPath $ExplicitPath)) {
    return $ExplicitPath
  }

  $diskCandidates = Get-ChildItem -Path 'D:\*' -Directory -ErrorAction SilentlyContinue |
    Where-Object { Test-Path (Join-Path $_.FullName 'Yandex.Disk') }

  foreach ($diskCandidate in $diskCandidates) {
    $syncRoot = Join-Path $diskCandidate.FullName 'Yandex.Disk'
    $knowledgeBase = Get-ChildItem -Path $syncRoot -Directory -Recurse -Filter 'KnowledgeBase' -ErrorAction SilentlyContinue |
      Select-Object -First 1
    if ($knowledgeBase) {
      return $knowledgeBase.FullName
    }
  }

  return ""
}

$resolvedObsidianRoot = Resolve-ObsidianRoot -ExplicitPath $ObsidianRoot

Push-Location $workspaceRoot
try {
  if ($resolvedObsidianRoot) {
    python "scripts\dashboard\sync_workspace_data.py" --obsidian-root $resolvedObsidianRoot
    python "scripts\telegram_desktop\build_telegram_intelligence.py" `
      --exports-root $ExportsRoot `
      --obsidian-root $resolvedObsidianRoot
    python "scripts\dashboard\sync_workspace_data.py" --obsidian-root $resolvedObsidianRoot
    python "scripts\governance\build_governance_docs.py" `
      --obsidian-root $resolvedObsidianRoot
  } else {
    python "scripts\dashboard\sync_workspace_data.py" --no-obsidian-export
    python "scripts\telegram_desktop\build_telegram_intelligence.py" `
      --exports-root $ExportsRoot
    python "scripts\dashboard\sync_workspace_data.py" --no-obsidian-export
    python "scripts\governance\build_governance_docs.py" `
      --no-obsidian-export
  }
} finally {
  Pop-Location
}
