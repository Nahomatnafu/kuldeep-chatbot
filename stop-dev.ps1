param(
    [switch]$PortsOnly
)

$rootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidsFile = Join-Path $rootPath ".dev-pids"

function Kill-Tree {
    param([int]$ProcessId)
    $children = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $ProcessId }
    foreach ($child in $children) { Kill-Tree -ProcessId $child.ProcessId }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

$killed = @()

if (-not $PortsOnly -and (Test-Path $pidsFile)) {
    $savedPids = Get-Content $pidsFile | Where-Object { $_ -match "^\d+$" } | ForEach-Object { [int]$_ }
    foreach ($p in $savedPids) {
        if (Get-Process -Id $p -ErrorAction SilentlyContinue) {
            Write-Host "Killing shell PID $p and its children..."
            Kill-Tree -ProcessId $p
            $killed += $p
        }
    }
    Remove-Item $pidsFile -ErrorAction SilentlyContinue
}

foreach ($port in @(5000, 3000)) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        foreach ($c in $conn) {
            if ($killed -notcontains $c.OwningProcess) {
                Write-Host "Killing PID $($c.OwningProcess) still holding port $port..."
                Kill-Tree -ProcessId $c.OwningProcess
                $killed += $c.OwningProcess
            }
        }
    }
}

if ($killed.Count -eq 0) {
    Write-Host "Nothing to stop - no dev processes found."
} else {
    Write-Host "Done. Stopped $($killed.Count) process(es)."
}