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
    Select-Object -ExpandProperty IPAddress
  foreach ($ip in $ips) {
    Write-Output "LAN_URL: http://$ip`:$selectedPort/index.html"
  }
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
