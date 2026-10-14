# ============================================================
# Cria um backup manual dos dados JSON.
# Gera backups\backup-YYYY-MM-DD-HHMMSS\ com todos os .json.
# Uso:  powershell -ExecutionPolicy Bypass -File scripts/backup.ps1
# ============================================================
param(
    [string]$Tag = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$data = Join-Path $root "backend\data"
$backups = Join-Path $root "backend\backups"

if (-not (Test-Path -LiteralPath $data)) {
    Write-Error "Diretório de dados não encontrado: $data"
}

$stamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$name = "backup-$stamp"
if ($Tag) { $name = "$name-$Tag" }
$destination = Join-Path $backups $name
New-Item -ItemType Directory -Force -Path $destination | Out-Null

Get-ChildItem -LiteralPath $data -Filter *.json | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $destination
}

Write-Host "Backup criado em: $destination"