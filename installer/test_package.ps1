#requires -Version 5.1
<#
.SYNOPSIS
    Smoke test do pacote: inicia o executavel empacotado, exercita a API
    (registro, login, categorias, contas, lancamentos, relatorios/exportacao),
    reinicia para validar a persistencia em JSON e encerra.

.DESCRIPTION
    Uso:
      powershell -ExecutionPolicy Bypass -File installer\test_package.ps1
      powershell -ExecutionPolicy Bypass -File installer\test_package.ps1 -Exe <caminho>

    Nao abre o navegador (define SCF_NO_BROWSER=1). Requer a porta 8000 livre.
#>

[CmdletBinding()]
param(
    [string]$Exe,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
if (-not $Exe) {
    $Exe = Join-Path $PSScriptRoot "payload\SistemaFinanceiro\SistemaFinanceiro.exe"
}
$Base = "http://127.0.0.1:$Port"
$script:Failures = @()

function Check($name, $condition, $detail) {
    if ($condition) {
        Write-Host ("  [OK]   " + $name) -ForegroundColor Green
    } else {
        Write-Host ("  [FALHA] " + $name + " -> " + $detail) -ForegroundColor Red
        $script:Failures += $name
    }
}

function PostJson($url, $obj, $token) {
    $headers = @{}
    if ($token) { $headers["Authorization"] = "Bearer $token" }
    return Invoke-RestMethod -Method Post -Uri $url -Headers $headers `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes(($obj | ConvertTo-Json -Depth 6)))
}

function GetJson($url, $token) {
    $headers = @{}
    if ($token) { $headers["Authorization"] = "Bearer $token" }
    return Invoke-RestMethod -Method Get -Uri $url -Headers $headers
}

function Wait-Health([int]$Seconds = 40) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $h = Invoke-RestMethod -Method Get -Uri "$Base/health" -TimeoutSec 2
            if ($h.status -eq "ok") { return $true }
        } catch { }
        Start-Sleep -Milliseconds 400
    }
    return $false
}

function Stop-App {
    Get-Process -Name "SistemaFinanceiro" -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 800
}

function Start-App {
    $env:SCF_NO_BROWSER = "1"
    $p = Start-Process -FilePath $Exe -PassThru
    return $p
}

# Garante que o processo seja encerrado mesmo em falha inesperada.
trap { Stop-App; Write-Host ("Interrompido: " + $_) -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------------------
if (-not (Test-Path -LiteralPath $Exe)) { throw "Executavel nao encontrado: $Exe" }
$SourceAppDir = Split-Path -Parent $Exe

# Simula a instalacao real: copia o app para %LOCALAPPDATA% (fora do Desktop,
# que pode estar protegido pelo Windows) e roda a partir de la.
$TestRoot = Join-Path $env:LOCALAPPDATA "SistemaFinanceiroTest"
Get-Process -Name "SistemaFinanceiro" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500
if (Test-Path -LiteralPath $TestRoot) { Remove-Item -LiteralPath $TestRoot -Recurse -Force }
New-Item -ItemType Directory -Path $TestRoot -Force | Out-Null
Copy-Item -Path (Join-Path $SourceAppDir "*") -Destination $TestRoot -Recurse -Force
$Exe = Join-Path $TestRoot "SistemaFinanceiro.exe"
$AppDir = $TestRoot
$DataDir = Join-Path $AppDir "data"
$BackupDir = Join-Path $AppDir "backups"

$inUse = $false
try { Invoke-RestMethod -Method Get -Uri "$Base/health" -TimeoutSec 2 | Out-Null; $inUse = $true } catch { }
if ($inUse) { throw "A porta $Port ja esta em uso. Encerre o processo antes de testar." }

Stop-App
if (Test-Path -LiteralPath $DataDir) { Remove-Item -LiteralPath $DataDir -Recurse -Force }
if (Test-Path -LiteralPath $BackupDir) { Remove-Item -LiteralPath $BackupDir -Recurse -Force }

Write-Host "`n=== 1. Iniciando o executavel ===" -ForegroundColor Cyan
Start-App | Out-Null
Check "Servidor respondeu /health" (Wait-Health 40) "timeout ao aguardar /health"

$second = Start-Process -FilePath $Exe -PassThru
$exited = $false
try { Wait-Process -Id $second.Id -Timeout 20 -ErrorAction Stop; $exited = $true } catch { }
if (-not $exited) { Stop-Process -Id $second.Id -Force -ErrorAction SilentlyContinue }
Check "Segunda instancia encerra sem duplicar servidor" $exited "segunda instancia continuou rodando"

$email = "teste@exemplo.com"
$pass = "senha123"

Write-Host "`n=== 2. Autenticacao ===" -ForegroundColor Cyan
$reg = PostJson "$Base/api/auth/register" @{ name = "Usuario Teste"; email = $email; password = $pass }
Check "Registro cria usuario e retorna token" ($null -ne $reg.access_token) "sem access_token"
$token = $reg.access_token

$login = PostJson "$Base/api/auth/login" @{ email = $email; password = $pass }
Check "Login retorna token" ($null -ne $login.access_token) "sem access_token"

$me = GetJson "$Base/api/auth/me" $token
Check "GET /me retorna o usuario" ($me.email -eq $email) "email divergente"

Write-Host "`n=== 3. CRUD ===" -ForegroundColor Cyan
$cat = PostJson "$Base/api/categories" @{ name = "Alimentacao"; type = "despesa"; color = "#16a34a" } $token
Check "Criar categoria" ($null -ne $cat.id) "sem id"

$acc = PostJson "$Base/api/accounts" @{ name = "Conta Principal"; type = "conta_corrente"; initial_balance = "1000.00" } $token
Check "Criar conta" ($null -ne $acc.id) "sem id"

$tx = PostJson "$Base/api/transactions" @{
    description = "Mercado do mes"
    amount      = "1250.50"
    type        = "despesa"
    date        = "2026-10-08"
    status      = "pago"
    category_id = $cat.id
    account_id  = $acc.id
} $token
Check "Criar lancamento" ($null -ne $tx.id) "sem id"
Check "Valor preservado como decimal" ($tx.amount -eq "1250.50") ("valor=" + $tx.amount)

$list = GetJson "$Base/api/transactions" $token
Check "Listar lancamentos" ((@($list).Count) -ge 1) "lista vazia"

$dash = GetJson "$Base/api/dashboard" $token
Check "Dashboard responde" ($null -ne $dash) "sem dados"

$summary = GetJson "$Base/api/reports/summary?start_date=2026-10-01&end_date=2026-10-31" $token
Check "Relatorio resumo responde" ($null -ne $summary) "sem dados"

Write-Host "`n=== 4. Exportacao ===" -ForegroundColor Cyan
foreach ($fmt in @("csv", "xlsx", "pdf")) {
    try {
        $resp = Invoke-WebRequest -Method Get -UseBasicParsing -Uri "$Base/api/reports/export?fmt=$fmt&start_date=2026-10-01&end_date=2026-10-31" `
            -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 30
        Check ("Exportar " + $fmt) ($resp.StatusCode -eq 200 -and $resp.RawContentLength -gt 0) ("bytes=" + $resp.RawContentLength)
    } catch {
        Check ("Exportar " + $fmt) $false $_.Exception.Message
    }
}

Write-Host "`n=== 5. Encerrando e validando persistencia ===" -ForegroundColor Cyan
Stop-App
Start-Sleep -Seconds 1

$jsonFiles = @(Get-ChildItem -Path $DataDir -Filter "*.json" -ErrorAction SilentlyContinue)
Check "Arquivos JSON criados em data\" ($jsonFiles.Count -ge 10) ("encontrados=" + $jsonFiles.Count)
$usersJson = Join-Path $DataDir "users.json"
Check "users.json existe" (Test-Path -LiteralPath $usersJson) "ausente"
if (Test-Path -LiteralPath $usersJson) {
    $raw = Get-Content -LiteralPath $usersJson -Raw
    Check "Usuario persistido no users.json" ($raw -match [regex]::Escape($email)) "email nao encontrado"
}

Write-Host "`n=== 6. Reinicio: dados devem persistir ===" -ForegroundColor Cyan
Start-App | Out-Null
Check "Servidor reiniciou" (Wait-Health 40) "timeout no reinicio"
$login2 = PostJson "$Base/api/auth/login" @{ email = $email; password = $pass }
Check "Login apos reinicio (persistencia)" ($null -ne $login2.access_token) "login falhou"
$list2 = GetJson "$Base/api/transactions" $login2.access_token
Check "Lancamento persistido" ((@($list2).Count) -ge 1) "lista vazia apos reinicio"
Stop-App

Write-Host ""
if ($script:Failures.Count -eq 0) {
    Write-Host "TODOS OS TESTES PASSARAM" -ForegroundColor Green
    exit 0
} else {
    Write-Host ("FALHAS: " + ($script:Failures -join ", ")) -ForegroundColor Red
    exit 1
}