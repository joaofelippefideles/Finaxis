# Guia de Execução (Desenvolvimento) — Finaxis (Sistema de Controle Financeiro Pessoal)

Como executar o projeto em modo de desenvolvimento, rodar os testes e gerar os
artefatos de distribuição (executável e instalador).

---

## 1. Pré-requisitos

- **Python 3.12+** (testado com 3.14).
- **Node.js** (apenas para os testes do frontend).
- **[Inno Setup 6](https://jrsoftware.org/isdl.php)** (apenas para gerar o
  instalador; o executável é gerado sem ele).

---

## 2. Preparar o ambiente

```powershell
# Cria backend\.venv, instala dependências e o backend\.env
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

# (opcional) cria as pastas data/ e backups/
powershell -ExecutionPolicy Bypass -File scripts\create_data.ps1
```

Dependências ficam em `backend\requirements.txt` (sem banco de dados externo).

---

## 3. Executar em desenvolvimento

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8000/`
- Documentação interativa (Swagger): `http://127.0.0.1:8000/docs`

Ou manualmente:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend
```

> Os dados são gravados em `backend\data`. Para usar outro diretório, defina
> `DATA_DIR` e `BACKUP_DIR` (variáveis de ambiente ou `backend\.env`).

---

## 4. Testes

### Backend (pytest)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

Os testes usam um diretório temporário e limpam os dados a cada teste
(`conftest.py`), sem tocar em `backend\data`.

### Frontend (Node test runner)

```powershell
node --test frontend\tests\api-download.test.js
```

### Verificação de sintaxe JavaScript

```powershell
Get-ChildItem -Recurse frontend\assets\js -Filter *.js |
  ForEach-Object { node --check $_.FullName }
```

### Teste do pacote empacotado (executável)

```powershell
powershell -ExecutionPolicy Bypass -File installer\test_package.ps1
```

Valida: inicialização, `/health`, instância única, autenticação, CRUD,
relatórios/exportações (CSV/XLSX/PDF) e persistência após reinício.

---

## 5. Backup dos dados

```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup.ps1
# ou, com etiqueta:
powershell -ExecutionPolicy Bypass -File scripts\backup.ps1 -Tag antes-de-atualizar
```

Cria `backups\backup-AAAA-MM-DD-HHMMSS\` com todas as coleções JSON.

---

## 6. Gerar o executável (PyInstaller)

```powershell
powershell -ExecutionPolicy Bypass -File installer\build.ps1 -SkipInstaller
```

- Cria um ambiente **limpo** de build em `backend\.venv-build`.
- Gera o executável **onedir** em `installer\output\pyinstaller\SistemaFinanceiro`.
- Monta o **payload** em `installer\payload\SistemaFinanceiro`:
  ```
  SistemaFinanceiro\
  ├── SistemaFinanceiro.exe     (inicializador: servidor + janela de controle)
  ├── _internal\                (runtime Python + dependências)
  ├── frontend\                 (interface web)
  ├── docs\ , README.md
  └── (data\ e backups\ são criados em tempo de execução)
  ```

O launcher (`installer\launcher.py`) é a porta de entrada: cria `data`/`backups`,
inicia o Uvicorn em `127.0.0.1:8000`, abre o navegador e permite encerrar com
segurança, garantindo **instância única**.

### Depuração do executável

Se o executável falhar ao iniciar sem mensagem (é um app sem console), veja
`data\startup-error.log` e `logs\app.log`. Para gerar uma versão com console:

```powershell
$env:SCF_CONSOLE = "1"
backend\.venv-build\Scripts\python.exe -m PyInstaller --noconfirm --clean installer\SistemaFinanceiro.spec
```

---

## 7. Gerar o instalador (Inno Setup)

```powershell
powershell -ExecutionPolicy Bypass -File installer\build.ps1
```

Se o Inno Setup estiver instalado, o resultado é:

```
dist\FinaxisSetup.exe
```

Caso não esteja, instale-o e repita:

```powershell
winget install --id JRSoftware.InnoSetup -e
```

O script de instalação está em `installer\SistemaFinanceiro.iss` e o Identificador
de aplicação (GUID) garante que **atualizações preservem os dados** do usuário.

---

## 8. Empacotamento de código-fonte (ZIP)

```powershell
powershell -ExecutionPolicy Bypass -File installer\make_source_zip.ps1
```

Gera `dist\Finaxis-Fonte.zip` (sem ambientes virtuais,
dados, backups nem artefatos de build).

---

## 9. Estrutura do repositório

```
backend\        API FastAPI + persistência JSON + testes
frontend\       Interface web (HTML/CSS/JS)
installer\      Empacotamento: launcher, spec, iss, scripts de build/teste
scripts\        Automação de desenvolvimento (setup, run, test, backup...)
docs\           Guias de instalação, uso e execução
```

---

## 10. Solução de problemas

| Sintoma | Solução |
| --- | --- |
| `ModuleNotFoundError: email_validator` | Instale as dependências: `pip install -r backend\requirements.txt`. |
| PyInstaller falha ao apagar arquivos | Antivírus pode reter `.pyd`; o `build.ps1` já tenta novamente. |
| Porta 8000 ocupada | Encerre o processo anterior antes de iniciar novamente. |
| Executável não abre | Verifique `data\startup-error.log`. |