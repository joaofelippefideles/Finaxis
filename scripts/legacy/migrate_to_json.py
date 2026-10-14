"""FERRAMENTA LEGADA OPCIONAL — NÃO faz parte da aplicação.

============================================================================
 MIGRAÇÃO PONTUAL DE UM POSTGRESQL ANTIGO  ->  ARQUIVOS JSON
============================================================================

Este script existe APENAS para quem possui uma instalação ANTIGA do sistema
(versões anteriores que usavam PostgreSQL) e quer aproveitar os dados.

Ele NÃO é necessário para:
  - instalar o sistema em um computador novo;
  - iniciar a aplicação;
  - executar os testes;
  - gerar o instalador;
  - usar o sistema (a persistência é 100% JSON).

Este arquivo:
  - NÃO é importado pela aplicação;
  - NÃO é referenciado pelo backend, pelos testes ou pelos scripts ativos;
  - só funciona se o driver opcional ``psycopg`` estiver instalado
    (*não* consta no ``requirements.txt`` principal).

O sistema principal é totalmente independente de PostgreSQL: SQLAlchemy,
Alembic e ``psycopg`` foram removidos das dependências de runtime.

--------------------------------------------------------------------------
Como usar (somente em uma máquina que já teve o sistema PostgreSQL)
--------------------------------------------------------------------------

1. Instale o driver opcional (apenas nesta migração):

       pip install "psycopg[binary]"

2. Exporte os dados para a pasta de dados JSON:

       python scripts/legacy/migrate_to_json.py \
           --dsn "postgresql://postgres:postgres@localhost:5432/financeiro" \
           --out backend/data

3. Pronto. O restante do sistema continuará lendo apenas os ``.json``.
   Você pode desinstalar o ``psycopg`` e desativar o PostgreSQL após isso.

Se você nunca usou PostgreSQL, ignore este arquivo.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

# Tabela do PostgreSQL antigo -> nome do arquivo de coleção JSON.
TABLES: dict[str, str] = {
    "users": "users",
    "categories": "categories",
    "accounts": "accounts",
    "transactions": "transactions",
    "credit_cards": "credit_cards",
    "installments": "installments",
    "budgets": "budgets",
    "payables": "payables",
    "receivables": "receivables",
    "notifications": "notifications",
    "recurring_transactions": "recurring_transactions",
}


def _to_jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, dict)):
        return value
    return getattr(value, "value", str(value))


def _write_collection(destination: Path, name: str, records: list[dict]) -> None:
    path = destination / f"{name}.json"
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    tmp.replace(path)


def migrate(dsn: str, out_dir: Path) -> int:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        print(
            "Este script é uma ferramenta LEGADA OPCIONAL.\n"
            "O driver 'psycopg' não está instalado (e não faz parte das\n"
            "dependências do projeto). Só o instale se realmente precisar\n"
            "migrar dados de uma instalação antiga com PostgreSQL.\n\n"
            '    pip install "psycopg[binary]"\n',
            file=sys.stderr,
        )
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0

    with psycopg.connect(dsn) as conn:
        for table, collection in TABLES.items():
            try:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(f'SELECT * FROM "{table}"')
                    rows = cur.fetchall()
            except Exception as exc:  # tabela ausente ou inacessível
                print(f"[skip] {table}: {exc}")
                continue

            records = [
                {key: _to_jsonable(value) for key, value in row.items()}
                for row in rows
            ]
            _write_collection(out_dir, collection, records)
            total += len(records)
            print(f"[ok]   {table} -> {collection}.json ({len(records)} registros)")

    print(f"\nMigração concluída: {total} registros gravados em {out_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ferramenta legada opcional: exporta um PostgreSQL antigo para JSON."
    )
    parser.add_argument("--dsn", required=True, help="String de conexão do PostgreSQL antigo")
    parser.add_argument(
        "--out",
        default="backend/data",
        help="Diretório de saída dos JSONs (padrão: backend/data)",
    )
    args = parser.parse_args()
    return migrate(args.dsn, Path(args.out))


if __name__ == "__main__":
    raise SystemExit(main())