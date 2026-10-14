# Finaxis — Sistema de Controle Financeiro Pessoal

Aplicação web completa (API + SPA) para controle de finanças pessoais, desenvolvida
como projeto da disciplina de **Paradigmas de Linguagens de Programação em Python**.

O sistema permite gerir **contas**, **lançamentos**, **cartões de crédito** (com
faturas e parcelamentos), **contas a pagar/receber**, **orçamentos**, **lançamentos
recorrentes**, **notificações** e **relatórios exportáveis** (CSV, XLSX e PDF).

## Stack

- **Backend:** FastAPI + Pydantic v2
- **Persistência:** arquivos **JSON** locais (`backend/data/*.json`) — sem banco de dados externo
- **Autenticação:** JWT (PyJWT) com hashing de senha
- **Frontend:** SPA em HTML/CSS/JavaScript puro, servida pelo próprio FastAPI
- **Relatórios:** `openpyxl` (Excel) e `fpdf2` (PDF)
- **Testes:** `pytest` + `httpx` (TestClient)

## Estrutura do projeto

```
.
├── backend/
│   ├── app/                 # código da aplicação
│   │   ├── api/routes/      # endpoints REST
│   │   ├── core/            # configuração, segurança, dependências
│   │   ├── database/        # sessão JSON (fachada de persistência)
│   │   ├── models/          # modelos (classes simples persistidas em JSON)
│   │   ├── repositories/    # acesso a dados (+ json_database.py)
│   │   ├── schemas/         # modelos Pydantic (request/response)
│   │   ├── services/        # regras de negócio
│   │   └── utils/           # utilidades (datas, dinheiro)
│   ├── data/                # dados do usuário (*.json) — criado em runtime
│   ├── backups/             # backups manuais dos dados
│   ├── tests/               # suíte de testes (pytest)
│   └── requirements.txt
├── frontend/                # SPA (HTML/CSS/JS)
├── installer/               # empacotamento: launcher, spec, iss, build/teste
├── scripts/                 # automação (setup, run, test, create_data, backup)
│   └── legacy/              # ferramentas opcionais (migração de PostgreSQL antigo)
├── docs/                    # guias de instalação, uso e execução
├── dist/                    # artefatos gerados (instalador + ZIP de fontes)
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## Instalação (usuário final, Windows)

O projeto é distribuído como um instalador **autocontido**
(`FinaxisSetup.exe`), que **não exige Python nem banco de dados**.
Passo a passo, local dos dados e desinstalação estão em
[`docs/GUIA-DE-INSTALACAO.md`](docs/GUIA-DE-INSTALACAO.md).

## Empacotamento (desenvolvedor)

```powershell
# Executável + instalador (requer Inno Setup 6)
powershell -ExecutionPolicy Bypass -File installer\build.ps1

# Apenas o executável autocontido
powershell -ExecutionPolicy Bypass -File installer\build.ps1 -SkipInstaller

# Testa o pacote (auth, CRUD, relatórios, instância única, persistência)
powershell -ExecutionPolicy Bypass -File installer\test_package.ps1

# ZIP do código-fonte
powershell -ExecutionPolicy Bypass -File installer\make_source_zip.ps1
```

Detalhes em [`docs/GUIA-DE-EXECUCAO.md`](docs/GUIA-DE-EXECUCAO.md) e uso em
[`docs/GUIA-DE-USO.md`](docs/GUIA-DE-USO.md).

## Requisitos

- Python 3.12+ (testado com 3.14)
- Nenhum banco de dados ou serviço externo é necessário

## Execução com Docker (opcional)

```bash
docker compose up --build
```

- Aplicação: http://localhost:8000
- Documentação (Swagger): http://localhost:8000/docs

Os dados são gravados no volume `financeiro_data` (mapeado para `backend/data`).

## Execução local (recomendado)

1. **Preparar o ambiente** (cria `backend\.venv`, instala dependências e o `.env`):

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
   ```

   Opcionalmente, garanta os diretórios de dados/backup:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/create_data.ps1
   ```

2. **Subir a API**:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/run.ps1
   ```

3. Acesse http://127.0.0.1:8000 (docs em http://127.0.0.1:8000/docs).

> Os arquivos de dados são criados automaticamente no primeiro acesso em
> `backend/data/`. Para ajustar os caminhos, use `DATA_DIR` e `BACKUP_DIR` no `.env`.

## Testes

Os testes usam um diretório **temporário** para os JSONs e limpam os dados entre
casos — os dados reais em `backend/data` não são afetados.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test.ps1
```

Ou, diretamente:

```powershell
cd backend
.venv\Scripts\python.exe -m pytest tests -v
```

A suíte cobre autenticação, contas, categorias, transações (incl. cartão/parcelamento),
contas a pagar/receber, orçamentos, dashboard, relatórios/exportações, busca,
notificações, configurações e lançamentos recorrentes.

Testes do frontend (download autenticado das exportações), requer Node.js:

```bash
node --test frontend/tests/api-download.test.js
```

## Backup e migração de dados

- **Backup manual:**

  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/backup.ps1 [-Tag nome]
  ```

  Gera `backend/backups/backup-YYYY-MM-DD-HHMMSS/` com todos os `.json`.

- **Migração de um PostgreSQL antigo — OPCIONAL / LEGADA:**

  > ⚠️ Esta ferramenta **não faz parte da aplicação**. Ela só serve para quem
  > possui uma instalação **antiga** (versões anteriores com PostgreSQL) e quer
  > reaproveitar os dados. **Não é necessária** para instalar, iniciar, testar
  > nem usar o sistema atual, e **não é usada pelo instalador**. O driver
  > `psycopg` **não** está no `requirements.txt`.

  ```bash
  # SOMENTE se você tem um banco PostgreSQL antigo com dados para migrar:
  pip install "psycopg[binary]"
  python scripts/legacy/migrate_to_json.py --dsn "postgresql://postgres:postgres@localhost:5432/financeiro" --out backend/data
  ```

  Depois disso, o `psycopg` pode ser desinstalado e o PostgreSQL desativado.

## Independência de PostgreSQL

A aplicação principal é **100% independente de PostgreSQL**:

- A única persistência é JSON (`backend/data/*.json`).
- `SQLAlchemy`, `Alembic`, `psycopg`/`psycopg2`, `DATABASE_URL` e `create_db.ps1`
  foram **removidos**.
- Instalação nova, testes e instalador **não exigem** nenhum banco de dados.
- O único resquício é `scripts/legacy/migrate_to_json.py`, uma ferramenta legada
  opcional (não importada, não obrigatória).

## Variáveis de ambiente

Veja `.env.example`. Principais:

| Variável | Descrição | Padrão |
| --- | --- | --- |
| `DATA_DIR` | Diretório dos arquivos JSON | `data` |
| `BACKUP_DIR` | Diretório de backups | `backups` |
| `SECRET_KEY` | Chave de assinatura JWT | `change-me-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token | `1440` |
| `CORS_ORIGINS` | Origens permitidas (JSON) | `["*"]` |
| `FRONTEND_DIR` | Caminho do frontend | `frontend` |
| `LOG_LEVEL` | Nível de log | `INFO` |

`DATA_DIR`/`BACKUP_DIR` são resolvidos relativos à pasta `backend/` quando não
absolutos. A pasta de dados e os arquivos de coleção são criados automaticamente.

## Formatos de dados

Cada coleção (`users`, `accounts`, `transactions`, `categories`, `credit_cards`,
`installments`, `budgets`, `payables`, `receivables`, `notifications`,
`recurring_transactions`) fica em um arquivo `<colecao>.json` contendo uma lista de
objetos. Convenções:

- **Identificadores:** UUID em string (independem da posição no arquivo).
- **Valores monetários:** string decimal (ex.: `"123.45"`), convertidos para `Decimal`.
- **Datas:** `YYYY-MM-DD`; **datas/horas:** ISO 8601.
- **Escritas atômicas:** temp file + `os.replace`, protegidas por lock.

## Principais endpoints

Todos sob o prefixo `/api` (ver `/docs` para a lista completa).

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`
- `GET/POST/PUT/DELETE /accounts`
- `GET/POST/PUT/DELETE /categories`, `PATCH /categories/{id}/toggle`
- `GET/POST/PUT/DELETE /transactions`
- `GET/POST /cards`, `GET /cards/{id}/invoices`, `POST /cards/{id}/invoices/{month}/pay`
- `GET/POST/PUT/DELETE /payables`, `POST /payables/{id}/pay|reopen`
- `GET/POST/PUT/DELETE /receivables`, `POST /receivables/{id}/receive|cancel`
- `GET/POST/PUT/DELETE /budgets`
- `GET/POST/PUT/DELETE /recurring`, `POST /recurring/process`
- `GET /dashboard`
- `GET /reports/summary`, `GET /reports/export?fmt=csv|xlsx|pdf`
- `GET /search?q=...`
- `GET /notifications`, `POST /notifications/generate`, `GET /notifications/unread-count`
- `GET /settings`, `PUT /settings/profile|preferences|password`

## Notas de implementação

- Valores monetários são tratados como `Decimal`; a API serializa como string.
- A segurança usa tokens JWT (Bearer) e o isolamento por usuário é aplicado em
  todas as consultas.
- As categorias padrão são criadas automaticamente no cadastro de cada usuário.
- A camada de persistência (`app/repositories/json_database.py`) concentra o acesso
  aos arquivos; os serviços usam uma sessão (`JsonSession`) com mapa de identidade
  e rastreio de alterações que persiste no `commit()`.