API = "/api"


def test_seed_categories_available(client, categories):
    headers, cats = categories
    assert len(cats) >= 12
    assert cats["Salário"]
    assert cats["Alimentação"]
    assert cats["Fatura de cartão"]


def test_create_custom_category(client, categories):
    headers, _ = categories
    resp = client.post(
        f"{API}/categories",
        json={"name": "Pets", "type": "despesa"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Pets"
    assert resp.json()["type"] == "despesa"


def test_toggle_category(client, categories):
    headers, cats = categories
    cat_id = cats["Lazer"]
    resp = client.patch(f"{API}/categories/{cat_id}/toggle?active=false", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["active"] is False


def test_update_category(client, categories):
    headers, cats = categories
    resp = client.put(
        f"{API}/categories/{cats['Transporte']}",
        json={"name": "Mobilidade"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Mobilidade"


def test_delete_category_removes_it(client, categories):
    headers, _ = categories
    new = client.post(
        f"{API}/categories",
        json={"name": "Serviços", "type": "despesa"},
        headers=headers,
    ).json()
    resp = client.delete(f"{API}/categories/{new['id']}", headers=headers)
    assert resp.status_code == 204
    assert client.get(f"{API}/categories/{new['id']}", headers=headers).status_code == 404


def test_foreign_category_not_accessible(client, categories, other_auth):
    headers_a, cats = categories
    headers_b, _ = other_auth
    assert client.get(f"{API}/categories/{cats['Lazer']}", headers=headers_b).status_code == 404