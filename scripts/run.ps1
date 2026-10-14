# ============================================================
# Sobe o servidor da API (Uvicorn) com recarga automática.
# Uso:  powershell -ExecutionPolicy Bypass -File scripts/run.ps1
# ============================================================
param(
    [string]$HostAddr = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "Virtualenv não encontrado. Rode primeiro: scripts\setup.ps1"
}

Write-Host "Iniciando API em http://${HostAddr}:$Port (docs em /docs) ..."
& $python -m uvicorn app.main:app --host $HostAddr --port $Port --reload