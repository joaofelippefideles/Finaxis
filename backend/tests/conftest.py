import os
import tempfile
from pathlib import Path

_TMP_ROOT = tempfile.mkdtemp(prefix="financeiro-test-")
os.environ["DATA_DIR"] = str(Path(_TMP_ROOT) / "data")
os.environ["BACKUP_DIR"] = str(Path(_TMP_ROOT) / "backups")

import pytest
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, database
from app.main import app

API = "/api"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    """Registra um usuário com e-mail aleatório e retorna (headers, user_payload)."""
    import time

    email = f"u.{time.time_ns()}@test.com"
    resp = client.post(
        f"{API}/auth/register",
        json={"name": "Usuário de Teste", "email": email, "password": "senha123"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return headers, data["user"]


@pytest.fixture
def other_auth(client):
    """Usuário secundário para testar isolamento entre contas."""
    import time

    email = f"u2.{time.time_ns()}@test.com"
    resp = client.post(
        f"{API}/auth/register",
        json={"name": "Outro Usuário", "email": email, "password": "senha123"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return headers, data["user"]


@pytest.fixture
def auth2(other_auth):
    return other_auth


@pytest.fixture
def seed_user(auth):
    """Apelido histórico: retorna (headers, dados do usuário)."""
    return auth


@pytest.fixture
def categories(client, auth):
    """Retorna ids das categorias seed do usuário."""
    headers, _ = auth
    resp = client.get(f"{API}/categories", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    helper = {}
    for cat in items:
        key = cat["name"]
        helper.setdefault(key, cat["id"])
    return headers, helper


@pytest.fixture(autouse=True)
def _cleanup():
    """Garante isolamento entre testes limpando o armazenamento JSON."""
    yield
    database.wipe()