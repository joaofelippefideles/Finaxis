@echo off
setlocal
cd /d "%~dp0"
title Finaxis - Inicializador

echo ==========================================
echo           FINAXIS 2.0
echo ==========================================
echo.

if not exist "app.py" (
    echo ERRO: app.py nao foi encontrado.
    echo Extraia este pacote mantendo os arquivos na mesma pasta.
    pause
    exit /b 1
)

where py >nul 2>nul
if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
        echo ERRO: Python nao foi encontrado neste computador.
        echo Instale o Python 3 e marque a opcao "Add Python to PATH".
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
) else (
    set "PYTHON_CMD=py -3"
)

if not exist ".venv\Scripts\python.exe" (
    echo Preparando o ambiente do Finaxis. Isso acontece apenas na primeira execucao...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto erro
)

".venv\Scripts\python.exe" -c "import streamlit" >nul 2>nul
if errorlevel 1 (
    echo Instalando as dependencias. Isso pode demorar na primeira vez...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto erro
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto erro
)

echo.
echo Iniciando o Finaxis...
echo O navegador sera aberto automaticamente.
echo Para encerrar o sistema, feche esta janela.
echo.
start "" "http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501
if errorlevel 1 goto erro
exit /b 0

:erro
echo.
echo O Finaxis nao conseguiu iniciar. Leia a mensagem de erro acima.
pause
exit /b 1
