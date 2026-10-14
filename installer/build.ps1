#requires -Version 5.1
<#
.SYNOPSIS
    Gera o executavel do Finaxis (Sistema de Controle Financeiro Pessoal) e (se
    disponivel) compila o instalador do Inno Setup.

.DESCRIPTION
    Etapas:
      1. cria/atualiza um ambiente virtual LIMPO de build (backend\.venv-build);
      2. instala requirements.txt + PyInstaller;
      3. gera o executavel com PyInstaller (onedir) em installer/output;
      4. monta a pasta de payload (exe + frontend + docs);
      5. compila installer/SistemaFinanceiro.iss se o Inno Setup estiver
         instalado; caso contrario, informa como instala-lo.

Uso:
    powershell -ExecutionPolicy Bypass -File installer\build.ps1
    powershell -ExecutionPolicy Bypass -File installer\build.ps1 -SkipInstaller
#>

[CmdletBinding()]
param(
    [switch]$SkipBuild,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$Installer = $PSScriptRoot
$Root = Split-Path -Parent $Installer
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BuildVenv = Join-Path $Backend ".venv-build"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
$Output = Join-Path $Installer "output"
$DistPath = Join-Path $Output "pyinstaller"
$WorkPath = Join-Path $Output "build"
$Payload = Join-Path $Installer "payload"
$PayloadApp = Join-Path $Payload "SistemaFinanceiro"
$VersionFile = Join-Path $Installer "version.txt"
$Version = (Get-Content -LiteralPath $VersionFile -Raw).Trim()

function Write-Step($message) { Write-Host "`n=== $message ===" -ForegroundColor Cyan }

function Remove-Safe($path) {
    if (-not (Test-Path -LiteralPath $path)) { return }
    for ($i = 1; $i -le 6; $i++) {
        try {
            Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop
            return
        } catch {
            if ($i -eq 6) { throw }
            Write-Host "  aguardando liberar $path (tentativa $i)..." -ForegroundColor DarkYellow
            Start-Sleep -Milliseconds 700
        }
    }
}

function Get-BasePython {
    $venvPy = Join-Path $Backend ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPy) { return $venvPy }
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    throw "Python nao encontrado. Instale o Python 3.11+ e tente novamente."
}

if (-not (Test-Path -LiteralPath $BuildPython)) {
    Write-Step "Criando ambiente de build limpo em $BuildVenv"
    $base = Get-BasePython
    if ($base -eq "py") { & py -3 -m venv $BuildVenv } else { & $base -m venv $BuildVenv }
    if (-not $?) { throw "Falha ao criar o ambiente de build." }
}

Write-Step "Instalando dependencias de empacotamento"
& $BuildPython -m pip install --upgrade pip --quiet
& $BuildPython -m pip install -r (Join-Path $Backend "requirements.txt") --quiet
& $BuildPython -m pip install "pyinstaller>=6.0" --quiet
if (-not $?) { throw "Falha ao instalar dependencias." }

if (-not $SkipBuild) {
    Write-Step "Empacotando com PyInstaller (pode levar alguns minutos)"
    if (Test-Path -LiteralPath $DistPath) { Remove-Safe $DistPath }
    & $BuildPython -m PyInstaller `
        --noconfirm --clean `
        --distpath $DistPath `
        --workpath $WorkPath `
        (Join-Path $Installer "SistemaFinanceiro.spec")
    if (-not $?) { throw "Falha no PyInstaller." }
}

if (-not (Test-Path -LiteralPath (Join-Path $DistPath "SistemaFinanceiro\SistemaFinanceiro.exe"))) {
    throw "Executavel nao encontrado em $DistPath. Rode sem -SkipBuild."
}

Write-Step "Preparando payload em $PayloadApp"
if (Test-Path -LiteralPath $Payload) { Remove-Safe $Payload }
New-Item -ItemType Directory -Path $PayloadApp -Force | Out-Null
Copy-Item -Path (Join-Path $DistPath "SistemaFinanceiro\*") -Destination $PayloadApp -Recurse -Force
Copy-Item -LiteralPath $Frontend -Destination (Join-Path $PayloadApp "frontend") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $Root "README.md") -Destination $PayloadApp -Force
if (Test-Path -LiteralPath (Join-Path $Root "docs")) {
    Copy-Item -LiteralPath (Join-Path $Root "docs") -Destination $PayloadApp -Recurse -Force
}

if ($SkipInstaller) {
    Write-Host "`n[Inno] Ignorado (-SkipInstaller). Payload pronto em $PayloadApp" -ForegroundColor Yellow
    exit 0
}

$isccCandidates = @(
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $iscc) {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
}

if (-not $iscc) {
    Write-Host "`n[Inno] ATENCAO: o Inno Setup nao esta instalado." -ForegroundColor Yellow
    Write-Host "       Instale-o para gerar o instalador .exe:" -ForegroundColor Yellow
    Write-Host "         winget install --id JRSoftware.InnoSetup -e" -ForegroundColor Yellow
    Write-Host "  Script do instalador: $Installer\SistemaFinanceiro.iss"
    Write-Host "  Payload pronto em:    $PayloadApp"
    exit 3
}

Write-Step "Compilando instalador com Inno Setup"
& $iscc "/DAppVersion=$Version" "/DSourceDir=$PayloadApp" (Join-Path $Installer "SistemaFinanceiro.iss")
if (-not $?) { throw "Falha ao compilar o instalador com o Inno Setup." }

Write-Host "`nOK. Instalador gerado em $Output" -ForegroundColor Green