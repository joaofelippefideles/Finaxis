import pytest

from app.repositories.json_database import COLLECTIONS, JsonDatabase, JsonDataError


def _db(tmp_path) -> JsonDatabase:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return JsonDatabase(data_dir)


def test_missing_collection_is_initialized_empty_on_creation(tmp_path):
    db = _db(tmp_path)
    assert db.all("users") == []
    for collection in COLLECTIONS:
        assert (tmp_path / "data" / f"{collection}.json").exists()


def test_valid_file_is_loaded(tmp_path):
    db = _db(tmp_path)
    (tmp_path / "data" / "users.json").write_text('[{"id": "u1"}]', encoding="utf-8")
    fresh = JsonDatabase(tmp_path / "data")
    assert fresh.all("users") == [{"id": "u1"}]


def test_invalid_json_raises_and_preserves_original(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    corrupted = "{ isto nao e um json valido"
    (data_dir / "users.json").write_text(corrupted, encoding="utf-8")

    db = JsonDatabase(data_dir)
    with pytest.raises(JsonDataError):
        db.all("users")

    with pytest.raises(JsonDataError):
        db.upsert("users", {"id": "novo"})

    assert (data_dir / "users.json").read_text(encoding="utf-8") == corrupted


def test_read_error_raises(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "users.json").mkdir()

    db = JsonDatabase(data_dir)
    with pytest.raises(JsonDataError):
        db.all("users")


def test_removed_file_after_init_raises(tmp_path):
    db = _db(tmp_path)
    (tmp_path / "data" / "users.json").unlink()
    with pytest.raises(JsonDataError):
        db.all("users")


def test_write_after_read_error_does_not_recreate_file(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "users.json").mkdir()

    db = JsonDatabase(data_dir)
    with pytest.raises(JsonDataError):
        db.upsert("users", {"id": "novo"})

    assert (data_dir / "users.json").is_dir()
