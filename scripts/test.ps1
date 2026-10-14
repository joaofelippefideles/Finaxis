# ============================================================
# Executa a suíte de testes automatizados (pytest).
# Os testes usam um diretório temporário para os JSONs,
# portanto os dados reais em backend\data NÃO são afetados.
# Uso:  powershell -ExecutionPolicy Bypass -File scripts/test.ps1
# ============================================================
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "Virtualenv não encontrado. Rode primeiro: scripts\setup.ps1"
}

& $python -m pytest (Join-Path $backend "tests") -v