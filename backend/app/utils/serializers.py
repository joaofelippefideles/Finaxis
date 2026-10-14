from datetime import datetime, date
from decimal import Decimal
from typing import Any


def jsonify(obj: Any) -> Any:
    """Converte objetos comuns (date, datetime, Decimal) para tipos JSON serializáveis."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonify(v) for v in obj]
    if hasattr(obj, "__dict__"):
        return jsonify(obj.__dict__)
    return obj