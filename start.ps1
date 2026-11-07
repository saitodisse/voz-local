$ErrorActionPreference = 'Stop'
$base = if ($env:VOZLOCAL_HOME) { $env:VOZLOCAL_HOME } else { Join-Path (Split-Path $PSScriptRoot -Parent) 'voz-local-data' }
$python = Join-Path $base '.venv\Scripts\python.exe'
$ahk = Join-Path $env:LOCALAPPDATA 'Programs\AutoHotkey\v2\AutoHotkey64.exe'
if (-not (Test-Path -LiteralPath $ahk)) { $ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe' }
try {
    if (-not (Test-Path -LiteralPath $python)) { throw 'Ambiente Python não encontrado. Consulte o README.pt-BR.md.' }
    if (-not (Test-Path -LiteralPath $ahk)) { throw 'AutoHotkey v2 não encontrado.' }
    $listener = Get-NetTCPConnection -LocalPort 8888 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) { throw 'A porta 8888 já está em uso. Encerre o leitor anterior antes de iniciar este projeto.' }
    $script = Join-Path $PSScriptRoot 'read_selection.ahk'
    $existing = Get-CimInstance Win32_Process -Filter "Name='AutoHotkey64.exe'" | Where-Object { $_.CommandLine -and ($_.CommandLine.Contains('Ler selecao.ahk') -or $_.CommandLine.Contains($script)) }
    if ($existing) { throw 'Um atalho de leitura já está ativo. Encerre-o antes de iniciar este projeto.' }
    $server = Start-Process -FilePath $python -ArgumentList ('-X utf8 "' + (Join-Path $PSScriptRoot 'server.py') + '"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $base 'reader.log') -RedirectStandardError (Join-Path $base 'reader-error.log') -PassThru
    $server.Id | Set-Content -LiteralPath (Join-Path $base 'reader.pid')
    $ready = $false
    for ($i=0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        try { $reply = Invoke-RestMethod 'http://127.0.0.1:8888/health' -TimeoutSec 1; if ($reply.status -eq 'ready') { $ready = $true; break } } catch {}
        if ($server.HasExited) { break }
    }
    if (-not $ready) { throw 'O servidor não iniciou. Consulte reader-error.log na pasta de dados.' }
    Start-Process -FilePath $ahk -ArgumentList ('"' + $script + '"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null
    Start-Process 'http://127.0.0.1:8888/'
} catch {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($_.Exception.Message, 'Voice Local Resident') | Out-Null
    exit 1
}
