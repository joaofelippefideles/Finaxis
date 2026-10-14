# ============================================================
# Cria o diretório de dados local (JSON) do projeto.
# Os arquivos de coleção são criados automaticamente no primeiro
# acesso, mas este script garante que a pasta exista.
# Uso:  powershell -ExecutionPolicy Bypass -File scripts/create_data.ps1
# ============================================================
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$data = Join-Path $backend "data"
$backups = Join-Path $backend "backups"

New-Item -ItemType Directory -Force -Path $data | Out-Null
New-Item -ItemType Directory -Force -Path $backups | Out-Null

Write-Host "Diretórios prontos:"
Write-Host "  dados:   $data"
Write-Host "  backups: $backups"
Write-Host "Os arquivos .json são criados sob demanda pela aplicação."