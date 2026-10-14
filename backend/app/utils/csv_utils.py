import csv
import io
from typing import Any, Dict, List, Optional

from app.utils.money import parse_brl_amount
from app.utils.dates import parse_iso_or_br


EXPECTED_HEADERS_ALIASES = {
    "descricao": "description",
    "descrição": "description",
    "valor": "amount",
    "tipo": "type",
    "data": "date",
    "categoria": "category",
    "conta": "account",
    "observacao": "observation",
    "observação": "observation",
    "status": "status",
    "carteira": "account",
}


def parse_csv_bytes(data: bytes) -> List[Dict[str, Any]]:
    """Lê um CSV (utf-8 ou latin-1) e devolve linhas normalizadas."""
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if not reader.fieldnames:
        reader = csv.DictReader(io.StringIO(text), delimiter=",")
    rows = []
    for row in reader:
        normalized = {}
        for k, v in row.items():
            key = (k or "").strip().lower()
            key = EXPECTED_HEADERS_ALIASES.get(key, key)
            normalized[key] = (v or "").strip()
        rows.append(normalized)
    return rows


def standardize_type(value: str) -> Optional[str]:
    v = value.strip().lower()
    mapping = {
        "receita": "income",
        "receitas": "income",
        "entrada": "income",
        "income": "income",
        "despesa": "expense",
        "despesas": "expense",
        "saida": "expense",
        "saída": "expense",
        "gasto": "expense",
        "expense": "expense",
        "transf": "transfer",
        "transferencia": "transfer",
        "transferência": "transfer",
    }
    return mapping.get(v)


def standardize_status(value: str) -> Optional[str]:
    v = value.strip().lower()
    mapping = {
        "pendente": "pending",
        "pago": "paid",
        "quitado": "paid",
        "recebido": "received",
        "cancelado": "canceled",
        "cancelada": "canceled",
    }
    return mapping.get(v)