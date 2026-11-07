$base = if ($env:VOZLOCAL_HOME) { $env:VOZLOCAL_HOME } else { Join-Path (Split-Path $PSScriptRoot -Parent) 'voz-local-data' }
$script = Join-Path $PSScriptRoot 'read_selection.ahk'
Get-CimInstance Win32_Process -Filter "Name='AutoHotkey64.exe'" | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($script) } | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
$pidFile = Join-Path $base 'reader.pid'
if (Test-Path -LiteralPath $pidFile) {
    $serverPid = 0
    if ([int]::TryParse((Get-Content -LiteralPath $pidFile -Raw).Trim(), [ref]$serverPid)) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$serverPid"
        if ($process -and $process.CommandLine -and $process.CommandLine.Contains((Join-Path $PSScriptRoot 'server.py'))) {
            Get-CimInstance Win32_Process -Filter "ParentProcessId=$serverPid" | Where-Object { $_.CommandLine -and $_.CommandLine.Contains((Join-Path $PSScriptRoot 'server.py')) } | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
            Stop-Process -Id $serverPid -ErrorAction SilentlyContinue
        }
    }
    Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
}
