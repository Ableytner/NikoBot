import json
import pathlib
import os

import pytest

from src.nikobot.util import error, storage

def test_basestorage_getitem():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage._store["key1"] = "value"
    assert BaseStorage["key1"] == "value"

    BaseStorage._store["key1"] = {}
    BaseStorage._store["key1"]["key2"] = "value2"
    assert BaseStorage["key1"]["key2"] == "value2"

def test_basestorage_getitem_multi():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage._store["key1"] = {}
    BaseStorage._store["key1"]["key2"] = "value2"
    assert BaseStorage["key1.key2"] == "value2"

    BaseStorage._store["key1"] = {}
    BaseStorage._store["key1"]["key2"] = {}
    BaseStorage._store["key1"]["key2"]["key3"] = {}
    BaseStorage._store["key1"]["key2"]["key3"]["key4"] = {}
    BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"] = {}
    BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"]["key6"] = "values"
    assert BaseStorage["key1.key2.key3.key4.key5.key6"] == "values"

def test_basestorage_getitem_keytype():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    with pytest.raises(TypeError):
        BaseStorage[None]
    with pytest.raises(TypeError):
        BaseStorage[10]
    with pytest.raises(TypeError):
        BaseStorage[list(("1",))]

def test_basestorage_getitem_valuetype():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage._store["key1"] = ["1", 2, None]
    assert BaseStorage["key1"] == ["1", 2, None]

def test_basestorage_getitem_wrong_key():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    with pytest.raises(error.KeyNotFound):
        BaseStorage["key1"]
    with pytest.raises(error.KeyNotFound):
        BaseStorage["key1.key2"]
    with pytest.raises(error.KeyNotFound):
        BaseStorage["key1.key2.key3.key4.key5.key6"]

def test_basestorage_setitem():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage["key1"] = "value"
    assert BaseStorage._store["key1"] == "value"

    BaseStorage["key1"] = {}
    BaseStorage["key1"]["key2"] = "value2"
    assert BaseStorage._store["key1"]["key2"] == "value2"

def test_basestorage_setitem_multi():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage["key1"] = {}
    BaseStorage["key1.key2"] = "value2"
    assert BaseStorage._store["key1"]["key2"] == "value2"

    BaseStorage["key1"] = {}
    BaseStorage["key1.key2"] = {}
    BaseStorage["key1.key2.key3"] = {}
    BaseStorage["key1.key2.key3.key4"] = {}
    BaseStorage["key1.key2.key3.key4.key5"] = {}
    BaseStorage["key1.key2.key3.key4.key5.key6"] = "values"
    assert BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"]["key6"] == "values"

def test_basestorage_setitem_create_subdict():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage["key1.key2"] = "value2"
    assert isinstance(BaseStorage._store["key1"], dict)
    assert BaseStorage._store["key1"]["key2"] == "value2"

    BaseStorage["key1.key2"] = {}

    BaseStorage["key1.key2.key3.key4.key5.key6"] = "values"
    assert isinstance(BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"], dict)
    assert BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"]["key6"] == "values"

def test_basestorage_setitem_keytype():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    with pytest.raises(TypeError):
        BaseStorage[None] = "value"
    with pytest.raises(TypeError):
        BaseStorage[10] = "value"
    with pytest.raises(TypeError):
        BaseStorage[list(("1",))] = "value"

def test_basestorage_setitem_valuetype():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage["key1"] = ["1", 2, None]
    assert BaseStorage._store["key1"] == ["1", 2, None]

    class CustomType():
        pass
    custom_item = CustomType()
    BaseStorage["key1"] = custom_item
    assert BaseStorage._store["key1"] == custom_item

def test_basestorage_delitem():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage._store["key1"] = "value"
    del BaseStorage["key1"]
    assert "key1" not in BaseStorage._store

def test_basestorage_delitem_multi():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    BaseStorage._store["key1"] = {}
    BaseStorage._store["key1"]["key2"] = "value2"
    del BaseStorage["key1.key2"]
    assert isinstance(BaseStorage._store["key1"], dict)
    assert "key2" not in BaseStorage._store["key1"]

    BaseStorage._store["key1"] = {}
    BaseStorage._store["key1"]["key2"] = {}
    BaseStorage._store["key1"]["key2"]["key3"] = {}
    BaseStorage._store["key1"]["key2"]["key3"]["key4"] = {}
    BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"] = {}
    BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"]["key6"] = "values"
    del BaseStorage["key1.key2.key3.key4.key5.key6"]
    assert isinstance(BaseStorage._store["key1"], dict)
    assert isinstance(BaseStorage._store["key1"]["key2"], dict)
    assert isinstance(BaseStorage._store["key1"]["key2"]["key3"], dict)
    assert isinstance(BaseStorage._store["key1"]["key2"]["key3"]["key4"], dict)
    assert isinstance(BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"], dict)
    assert "key2" not in BaseStorage._store["key1"]["key2"]["key3"]["key4"]["key5"]

def test_basestorage_delitem_keytype():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    with pytest.raises(TypeError):
        del BaseStorage[None]
    with pytest.raises(TypeError):
        del BaseStorage[10]
    with pytest.raises(TypeError):
        del BaseStorage[list(("1",))]

def test_basestorage_delitem_wrong_key():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    with pytest.raises(error.KeyNotFound):
        del BaseStorage["key1"]
    with pytest.raises(error.KeyNotFound):
        del BaseStorage["key1.key2"]
    with pytest.raises(error.KeyNotFound):
        del BaseStorage["key1.key2.key3.key4.key5.key6"]

def test_basestorage_contains():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    assert not BaseStorage.contains("key1")
    assert not "key1" in BaseStorage

    BaseStorage["key1"] = "value"
    assert BaseStorage.contains("key1")
    assert "key1" in BaseStorage

def test_basestorage_contains_multi():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    assert not BaseStorage.contains("key1.key2")
    assert not "key1.key2" in BaseStorage

    BaseStorage["key1.key2"] = "value2"
    assert BaseStorage.contains("key1.key2")
    assert "key1.key2" in BaseStorage

    del BaseStorage["key1"]

    assert not BaseStorage.contains("key1.key2.key3.key4.key5.key6")
    assert not "key1.key2.key3.key4.key5.key6" in BaseStorage

    BaseStorage["key1.key2.key3.key4.key5.key6"] = "values"
    assert BaseStorage.contains("key1.key2.key3.key4.key5.key6")
    assert "key1.key2.key3.key4.key5.key6" in BaseStorage

def test_basestorage_contains_keytype():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    with pytest.raises(TypeError):
        None in BaseStorage
    with pytest.raises(TypeError):
        10 in BaseStorage
    with pytest.raises(TypeError):
        list(("1",)) in BaseStorage

def test_basestorage_contains_item():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    assert not BaseStorage.contains_item("key1", "value")

    BaseStorage["key1"] = "value"
    assert BaseStorage.contains_item("key1", "value")

def test_basestorage_contains_item_multi():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    assert not BaseStorage.contains_item("key1.key2", "value")

    BaseStorage["key1.key2"] = "value2"
    assert BaseStorage.contains_item("key1.key2", "value2")

    del BaseStorage["key1"]

    assert not BaseStorage.contains_item("key1.key2.key3.key4.key5.key6", "values")

    BaseStorage["key1.key2.key3.key4.key5.key6"] = "values"
    assert BaseStorage.contains_item("key1.key2.key3.key4.key5.key6", "values")

def test_basestorage_contains_item_keytype():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    with pytest.raises(TypeError):
        BaseStorage.contains_item(None, "value")
    with pytest.raises(TypeError):
        BaseStorage.contains_item(10, "value")
    with pytest.raises(TypeError):
        BaseStorage.contains_item(list(("1",)), "value")

def test_basestorage_contains_item_valuetype():
    BaseStorage = storage._BaseStorage.__new__(storage._BaseStorage)
    BaseStorage._store = {}

    assert not BaseStorage.contains_item("key1", ["1", 2, None])

    BaseStorage["key1"] = ["1", 2, None]
    assert BaseStorage.contains_item("key1", ["1", 2, None])

def test_volatilestorage_inheritance():
    VolatileStorage = storage._VolatileStorage.__new__(storage._VolatileStorage)
    VolatileStorage._store = {}

    assert isinstance(VolatileStorage, storage._BaseStorage)
    assert not isinstance(VolatileStorage, storage._PersistentStorage)

def test_volatilestorage_valuetype():
    VolatileStorage = storage._VolatileStorage.__new__(storage._VolatileStorage)
    VolatileStorage._store = {}

    VolatileStorage["key1"] = ["1", 2, None]
    assert VolatileStorage["key1"] == ["1", 2, None]

    class CustomType():
        pass
    custom_item = CustomType()
    VolatileStorage["key1"] = custom_item
    assert VolatileStorage["key1"] == custom_item

def test_persistentstorage_inheritance():
    PersistentStorage = storage._PersistentStorage.__new__(storage._PersistentStorage)
    PersistentStorage._store = {}

    assert isinstance(PersistentStorage, storage._BaseStorage)
    assert not isinstance(PersistentStorage, storage._VolatileStorage)

def test_persistentstorage_valuetype():
    PersistentStorage = storage._PersistentStorage.__new__(storage._PersistentStorage)
    PersistentStorage._store = {}

    PersistentStorage["key1"] = "value"
    assert PersistentStorage["key1"] == "value"
    PersistentStorage["key1"] = 10
    assert PersistentStorage["key1"] == 10
    PersistentStorage["key1"] = ["1", "2"]
    assert PersistentStorage["key1"] == ["1", "2"]
    PersistentStorage["key1"] = {"key": "item"}
    assert PersistentStorage["key1"] == {"key": "item"}

    class CustomType():
        pass

    with pytest.raises(TypeError):
        PersistentStorage["key1"] = CustomType()

def test_persistentstorage_load_file():
    PersistentStorage = storage._PersistentStorage.__new__(storage._PersistentStorage)
    PersistentStorage._store = {}

    filepath = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "..", "test_run", "storage.json").resolve())
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    pathlib.Path.unlink(filepath, missing_ok=True)
    PersistentStorage["storage_file"] = filepath

    with open(filepath, "w") as f:
        json.dump({
            "key1": "value",
            "key2": [
                "value21",
                "value22",
                "value23"
            ],
            "key3": None,
            "key4": 10
        }, f)

    PersistentStorage._load_from_disk()

    assert PersistentStorage["key1"] == "value"
    assert PersistentStorage["key2"] == ["value21", "value22", "value23"]
    assert PersistentStorage["key3"] == None
    assert PersistentStorage["key4"] == 10

    os.remove(filepath)

def test_persistentstorage_save_file():
    PersistentStorage = storage._PersistentStorage.__new__(storage._PersistentStorage)
    PersistentStorage._store = {}

    filepath = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "..", "test_run", "storage.json").resolve())
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    pathlib.Path.unlink(filepath, missing_ok=True)
    PersistentStorage["storage_file"] = filepath

    PersistentStorage["key1"] = "value"
    PersistentStorage["key2"] = ["value21", "value22", "value23"]
    PersistentStorage["key3"] = None
    PersistentStorage["key4"] = 10

    PersistentStorage._save_to_disk()

    assert os.path.isfile(filepath)
    with open(filepath, "w") as f:
        data = json.load(f)
    assert data["key1"] == "value"
    assert data["key2"] == ["value21", "value22", "value23"]
    assert data["key3"] == None
    assert data["key4"] == 10

    os.remove(filepath)

def test_persistentstorage_save_file_empty():
    PersistentStorage = storage._PersistentStorage.__new__(storage._PersistentStorage)
    PersistentStorage._store = {}

    filepath = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "..", "test_run", "storage.json").resolve())
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    pathlib.Path.unlink(filepath, missing_ok=True)
    storage.VolatileStorage["storage_file"] = filepath

    PersistentStorage._save_to_disk()

    assert not os.path.isfile(filepath)
