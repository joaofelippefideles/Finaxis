"""Camada de persistência em arquivos JSON.

Toda a leitura/escrita de arquivos fica concentrada aqui (nenhum
``json.load``/``json.dump`` espalhado pelo projeto). A classe ``JsonDatabase``
cuida do IO atômico e dos backups; ``JsonSession`` oferece uma API semelhante à
de uma sessão de banco para os serviços e repositórios.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Type

from app.models.base import JsonModel

logger = logging.getLogger(__name__)

COLLECTIONS: list[str] = [
    "users",
    "categories",
    "accounts",
    "transactions",
    "credit_cards",
    "installments",
    "budgets",
    "payables",
    "receivables",
    "notifications",
    "recurring_transactions",
]


class JsonDataError(RuntimeError):
    """Falha controlada de integridade/IO na leitura de arquivos JSON.

    Sinaliza que uma coleção não pôde ser lida com segurança (arquivo ausente
    de forma inesperada, JSON inválido ou erro de leitura/permissão). A operação
    é interrompida para impedir que uma escrita posterior sobrescreva o conteúdo
    original com uma coleção vazia.
    """


class JsonDatabase:
    """Armazena cada coleção em um arquivo ``<colecao>.json`` (lista de objetos)."""

    def __init__(self, data_dir: str | os.PathLike, backup_dir: str | os.PathLike | None = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = Path(backup_dir) if backup_dir else self.data_dir / "backups"
        self._lock = threading.RLock()
        self._cache: dict[str, list[dict]] = {}
        self._ensure_files()

    # ------------------------------------------------------------------
    # Arquivos
    # ------------------------------------------------------------------
    def path(self, collection: str) -> Path:
        return self.data_dir / f"{collection}.json"

    def _ensure_files(self) -> None:
        for collection in COLLECTIONS:
            if not self.path(collection).exists():
                self._write_file(collection, [])

    def _read_file(self, collection: str) -> list:
        path = self.path(collection)
        if not path.exists():
            # Arquivo ausente só é inicializado vazio no fluxo legítimo de
            # criação (``_ensure_files``). Chegar aqui com o arquivo ausente
            # indica remoção inesperada; falhar é mais seguro do que devolver
            # uma coleção vazia que poderia ser persistida por cima.
            logger.error("Arquivo de dados ausente para a coleção '%s': %s", collection, path)
            raise JsonDataError(
                f"Arquivo de dados ausente para a coleção '{collection}'."
            )
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            logger.error(
                "JSON inválido na coleção '%s' (%s): %s", collection, path, exc
            )
            raise JsonDataError(
                f"JSON inválido na coleção '{collection}'. "
                "A operação foi interrompida para preservar o arquivo original."
            ) from exc
        except OSError as exc:
            logger.error(
                "Falha de leitura na coleção '%s' (%s): %s", collection, path, exc
            )
            raise JsonDataError(
                f"Falha de leitura na coleção '{collection}'. "
                "A operação foi interrompida para preservar o arquivo original."
            ) from exc
        if not isinstance(data, list):
            logger.error(
                "Formato inesperado na coleção '%s' (%s): esperava uma lista, "
                "recebeu %s", collection, path, type(data).__name__,
            )
            raise JsonDataError(
                f"Formato inesperado na coleção '{collection}' (esperava uma lista)."
            )
        return data

    def _write_file(self, collection: str, records: list) -> None:
        path = self.path(collection)
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)

    # ------------------------------------------------------------------
    # Operações
    # ------------------------------------------------------------------
    def all(self, collection: str) -> list[dict]:
        with self._lock:
            if collection not in self._cache:
                self._cache[collection] = self._read_file(collection)
            return self._cache[collection]

    def get(self, collection: str, record_id: str) -> Optional[dict]:
        for record in self.all(collection):
            if record.get("id") == record_id:
                return record
        return None

    def upsert(self, collection: str, record: dict) -> None:
        with self._lock:
            records = self.all(collection)
            for index, existing in enumerate(records):
                if existing.get("id") == record.get("id"):
                    records[index] = record
                    break
            else:
                records.append(record)
            self._write_file(collection, records)

    def delete(self, collection: str, record_id: str) -> None:
        with self._lock:
            records = [r for r in self.all(collection) if r.get("id") != record_id]
            self._cache[collection] = records
            self._write_file(collection, records)

    def wipe(self) -> None:
        """Remove todos os registros de todas as coleções (usado em testes)."""
        with self._lock:
            for collection in COLLECTIONS:
                self._cache[collection] = []
                self._write_file(collection, [])

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------
    def backup(self, tag: str | None = None) -> Path:
        with self._lock:
            stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            name = f"backup-{stamp}" + (f"-{tag}" if tag else "")
            destination = self.backup_dir / name
            destination.mkdir(parents=True, exist_ok=True)
            for collection in COLLECTIONS:
                shutil.copyfile(self.path(collection), destination / f"{collection}.json")
            return destination

    def health(self) -> bool:
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            probe = self.data_dir / ".health"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return True
        except OSError:
            return False


class JsonSession:
    """Sessão de curta duração com mapa de identidade e rastreio de alterações.

    Compatível com o subconjunto usado pelos serviços/repositórios:
    ``get``, ``add``, ``delete``, ``commit``, ``flush``, ``refresh`` e
    ``rollback``. As alterações feitas nos objetos carregados são persistidas
    automaticamente no ``commit``.
    """

    def __init__(self, database: JsonDatabase):
        self._db = database
        self._identity: dict[tuple[str, str], JsonModel] = {}
        self._deleted: list[JsonModel] = []

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------
    def all(self, model: Type[JsonModel]) -> list[JsonModel]:
        collection = model.COLLECTION
        result: dict[str, JsonModel] = {}
        for (coll, obj_id), obj in self._identity.items():
            if coll == collection:
                result[obj_id] = obj
        for record in self._db.all(collection):
            obj_id = record.get("id")
            if obj_id in result:
                continue
            obj = model.from_dict(record)
            self._identity[(collection, obj_id)] = obj
            result[obj_id] = obj
        return list(result.values())

    def get(self, model: Type[JsonModel], obj_id: Optional[str]) -> Optional[JsonModel]:
        if obj_id is None:
            return None
        key = (model.COLLECTION, obj_id)
        if key in self._identity:
            return self._identity[key]
        record = self._db.get(model.COLLECTION, obj_id)
        if record is None:
            return None
        obj = model.from_dict(record)
        self._identity[key] = obj
        return obj

    def find(self, model: Type[JsonModel], **equals: Any) -> Optional[JsonModel]:
        for obj in self.all(model):
            if all(getattr(obj, key, None) == value for key, value in equals.items()):
                return obj
        return None

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------
    def add(self, obj: JsonModel) -> JsonModel:
        self._identity[(obj.COLLECTION, obj.id)] = obj
        return obj

    def delete(self, obj: JsonModel) -> None:
        self._identity.pop((obj.COLLECTION, obj.id), None)
        if obj not in self._deleted:
            self._deleted.append(obj)

    def commit(self) -> None:
        self._persist()

    def flush(self) -> None:
        self._persist()

    def refresh(self, obj: JsonModel) -> JsonModel:
        record = self._db.get(obj.COLLECTION, obj.id)
        if record is not None:
            fresh = obj.__class__.from_dict(record)
            obj.__dict__.update(fresh.__dict__)
        return obj

    def rollback(self) -> None:
        self._identity.clear()
        self._deleted.clear()

    def close(self) -> None:  # compatibilidade com Session.close()
        self._identity.clear()
        self._deleted.clear()

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------
    def _persist(self) -> None:
        with self._db._lock:
            for obj in self._deleted:
                self._db.delete(obj.COLLECTION, obj.id)
            deleted_keys = {(obj.COLLECTION, obj.id) for obj in self._deleted}
            for key, obj in self._identity.items():
                if key in deleted_keys:
                    continue
                self._db.upsert(obj.COLLECTION, obj.to_dict())
            self._deleted.clear()