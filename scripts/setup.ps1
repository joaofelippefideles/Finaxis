# ============================================================
# Prepara o ambiente de desenvolvimento do backend.
# - cria o virtualenv em backend\.venv
# - instala as dependências
# - cria backend\.env a partir do .env.example (se ainda não existir)
# Uso:  powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
# ============================================================
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$venv = Join-Path $backend ".venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venv)) {
    Write-Host "Criando virtualenv em $venv ..."
    & python -m venv $venv
} else {
    Write-Host "Virtualenv já existe: $venv"
}

Write-Host "Instalando dependências ..."
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $backend "requirements.txt")

$backendEnv = Join-Path $backend ".env"
if (-not (Test-Path -LiteralPath $backendEnv)) {
    Copy-Item -LiteralPath (Join-Path $root ".env.example") -Destination $backendEnv
    Write-Host "backend\.env criado a partir de .env.example (revise os valores)."
}

Write-Host ""
Write-Host "Setup concluído." -ForegroundColor Green
Write-Host "Próximos passos:"
Write-Host "  1) Suba a API:      scripts\run.ps1"
Write-Host "  2) Acesse:          http://127.0.0.1:8000  (docs em /docs)"
Write-Host "Os dados são salvos em backend\data\*.json (criados automaticamente)."