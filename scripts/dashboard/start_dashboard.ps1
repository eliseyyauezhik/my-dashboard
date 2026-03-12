param(
  [Alias("Host")]
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8891,
  [switch]$Lan,
  [switch]$Open
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptsDir = Split-Path -Parent $scriptDir
$workspaceRoot = Split-Path -Parent $scriptsDir
$serverScript = Join-Path $scriptDir "dashboard_server.py"

function Test-PortFree {
  param(
    [string]$BindHost,
    [int]$Port
  )

  try {
    $ip = [System.Net.IPAddress]::Parse($BindHost)
  } catch {
    $ip = [System.Net.IPAddress]::Loopback
  }

  try {
    $listener = [System.Net.Sockets.TcpListener]::new($ip, $Port)
    $listener.Start()
    $listener.Stop()
    return $true
  } catch {
    return $false
  }
}

if (-not (Test-Path -LiteralPath $serverScript)) {
  throw "Script not found: $serverScript"
}

$effectiveHost = $BindHost
if ($Lan -and $BindHost -eq "127.0.0.1") {
  $effectiveHost = "0.0.0.0"
}

$selectedPort = $Port
for ($i = 0; $i -lt 20; $i++) {
  if (Test-PortFree -BindHost $effectiveHost -Port $selectedPort) { break }
  $selectedPort++
}

if (-not (Test-PortFree -BindHost $effectiveHost -Port $selectedPort)) {
  throw "No free port found in range $Port..$($Port + 19) for host $effectiveHost"
}

$url = "http://$effectiveHost`:$selectedPort/index.html"
Write-Output "DASHBOARD_SERVER: $url"

if ($effectiveHost -eq "0.0.0.0") {
  $ips = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '169.254*' -and $_.IPAddress -ne '127.0.0.1' } |
    Select-Object InterfaceAlias, IPAddress
  $profiles = Get-NetConnectionProfile -ErrorAction SilentlyContinue | Group-Object -Property InterfaceAlias -AsHashTable -AsString

  foreach ($entry in $ips) {
    $ip = $entry.IPAddress
    $alias = $entry.InterfaceAlias
    $category = $profiles[$alias].NetworkCategory
    if ($category -eq "Public") {
      Write-Output "LAN_WARN: Interface '$alias' is Public. Windows Firewall will likely block phone access until you switch to Private or add a firewall rule."
      Write-Output "LAN_TIP: Switch to Private (Settings -> Network) OR run as Admin: Set-NetConnectionProfile -InterfaceAlias '$alias' -NetworkCategory Private"
    }
    Write-Output "LAN_URL: http://$ip`:$selectedPort/index.html"
  }

  Write-Output "LAN_TIP: If LAN_URL does not open from phone, allow inbound TCP port $selectedPort in Windows Firewall (run PowerShell as Admin)."
  Write-Output "LAN_TIP: Private only (recommended): New-NetFirewallRule -DisplayName 'My Dashboard $selectedPort' -Direction Inbound -Action Allow -Protocol TCP -LocalPort $selectedPort -Profile Private"
  Write-Output "LAN_TIP: Public too (risky): New-NetFirewallRule -DisplayName 'My Dashboard $selectedPort (Public)' -Direction Inbound -Action Allow -Protocol TCP -LocalPort $selectedPort -Profile Public"
}

Push-Location $workspaceRoot
try {
  if ($Open) {
    Start-Process $url | Out-Null
  }
  & python $serverScript --host $effectiveHost --port $selectedPort
} finally {
  Pop-Location
}
