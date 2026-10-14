"""Camada base dos modelos persistidos em JSON.

Cada modelo declara seus campos em ``_fields`` no formato::

    nome: (tipo, valor_padrao)

onde ``tipo`` é um dos identificadores abaixo ou uma tupla ``(ENUM, EnumClass)``.
Os valores são convertidos automaticamente para/desde JSON (Decimal vira
string, date/datetime viram ISO 8601 e enums viram o seu ``value``).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

STR = "str"
INT = "int"
BOOL = "bool"
DECIMAL = "decimal"
DATE = "date"
DATETIME = "datetime"
JSON = "json"
ENUM = "enum"


def gen_uuid() -> str:
    """Gera um identificador único e estável (não depende da posição no array)."""
    return str(uuid.uuid4())


class JsonModel:
    COLLECTION: str = ""
    _fields: dict[str, tuple[Any, Any]] = {}

    def __init__(self, **kwargs: Any) -> None:
        for name, (_, default) in self._fields.items():
            if name in kwargs:
                setattr(self, name, kwargs[name])
            else:
                setattr(self, name, default() if callable(default) else default)
        for key, value in kwargs.items():
            if key not in self._fields:
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        return {name: self._encode(name, getattr(self, name, None)) for name in self._fields}

    @classmethod
    def _encode(cls, name: str, value: Any) -> Any:
        if value is None:
            return None
        kind = cls._fields[name][0]
        if isinstance(kind, tuple) and kind[0] == ENUM:
            return getattr(value, "value", value)
        if kind in (DATE, DATETIME):
            return value.isoformat() if hasattr(value, "isoformat") else value
        if kind == DECIMAL:
            return str(value)
        return value

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JsonModel":
        kwargs = {name: cls._decode(name, data[name]) for name in cls._fields if name in data}
        return cls(**kwargs)

    @classmethod
    def _decode(cls, name: str, value: Any) -> Any:
        if value is None:
            return None
        kind = cls._fields[name][0]
        if isinstance(kind, tuple) and kind[0] == ENUM:
            enum_cls = kind[1]
            try:
                return enum_cls(value)
            except ValueError:
                return value
        if kind == DATE:
            return date.fromisoformat(value) if isinstance(value, str) else value
        if kind == DATETIME:
            return datetime.fromisoformat(value) if isinstance(value, str) else value
        if kind == DECIMAL:
            return Decimal(str(value))
        return value