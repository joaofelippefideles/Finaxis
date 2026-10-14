#requires -Version 5.1
<#
.SYNOPSIS
    Gera um ZIP com o codigo-fonte do projeto para distribuicao.

.DESCRIPTION
    Cria dist\Finaxis-Fonte.zip excluindo ambientes
    virtuais, dados, backups, logs, caches e artefatos de build.

Uso:
    powershell -ExecutionPolicy Bypass -File installer\make_source_zip.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $Root "dist"
$Zip = Join-Path $Dist "Finaxis-Fonte.zip"
$Stage = Join-Path $env:TEMP ("scf-source-" + [guid]::NewGuid().ToString("N"))

$excludeDirs = @(
    "__pycache__", ".venv", ".venv-build", "venv", "env",
    "data", "backups", "logs", "output", "payload", "build",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".git", ".vscode", ".idea"
)

function Copy-Tree($source, $target) {
    if (-not (Test-Path -LiteralPath $source)) { return }
    robocopy $source $target /E /XD $excludeDirs /XF *.pyc *.pyo .env *.log /NFL /NDL /NJH /NJS /NP /R:1 /W:1 | Out-Null
}

Write-Host "Preparando fontes em staging..."
New-Item -ItemType Directory -Path $Stage -Force | Out-Null

Copy-Tree (Join-Path $Root "backend")   (Join-Path $Stage "backend")
Copy-Tree (Join-Path $Root "frontend")  (Join-Path $Stage "frontend")
Copy-Tree (Join-Path $Root "installer") (Join-Path $Stage "installer")
Copy-Tree (Join-Path $Root "scripts")   (Join-Path $Stage "scripts")
Copy-Tree (Join-Path $Root "docs")      (Join-Path $Stage "docs")

foreach ($file in @("README.md", "docker-compose.yml", "Dockerfile", ".env.example", ".gitignore")) {
    $src = Join-Path $Root $file
    if (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination $Stage -Force }
}

New-Item -ItemType Directory -Path $Dist -Force | Out-Null
if (Test-Path -LiteralPath $Zip) { Remove-Item -LiteralPath $Zip -Force }

Write-Host "Compactando para $Zip ..."
Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $Zip -Force

Remove-Item -LiteralPath $Stage -Recurse -Force -ErrorAction SilentlyContinue

$size = [math]::Round((Get-Item -LiteralPath $Zip).Length / 1MB, 2)
Write-Host "OK: $Zip ($size MB)" -ForegroundColor Green