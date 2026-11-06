import os
import tempfile
import pytest

from babylon60.primitives import (
    cbor_dumps,
    cbor_loads,
    connect,
    parse_yaml,
    dump_yaml,
    Matrix,
    Vector,
    dict_to_vector,
    vector_to_dict,
)


def test_cbor_bft_canonical_serialization() -> None:
    # Test primitive types
    data = {
        "b": 2,
        "a": 1,
        "nested": [True, False, None, 3.14159],
        "bytes": b"\x00\xff",
    }
    encoded = cbor_dumps(data)
    decoded = cbor_loads(encoded)

    assert decoded["a"] == 1
    assert decoded["b"] == 2
    assert decoded["nested"] == [True, False, None, 3.14159]
    assert decoded["bytes"] == b"\x00\xff"

    # Test BFT Canonical order: "a" and "b" keys must produce identical byte output regardless of dict insert order
    data_reordered = {
        "nested": [True, False, None, 3.14159],
        "bytes": b"\x00\xff",
        "a": 1,
        "b": 2,
    }
    encoded_reordered = cbor_dumps(data_reordered)
    assert encoded == encoded_reordered


@pytest.mark.asyncio
async def test_async_db_sovereign_wrapper() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        async with await connect(db_path) as db:
            await db.execute("CREATE TABLE ledger (id INT PRIMARY KEY, tx TEXT)")
            await db.execute("INSERT INTO ledger VALUES (1, 'genesis')")
            await db.commit()

            cursor = await db.execute("SELECT tx FROM ledger WHERE id = 1")
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == "genesis"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_yaml_parser_sovereign() -> None:
    yaml_text = """
    name: BABYLON-60
    version: 4.0
    active: true
    ledger_id: null
    nodes:
      - node1
      - node2
    """
    parsed = parse_yaml(yaml_text)
    assert parsed["name"] == "BABYLON-60"
    assert parsed["version"] == 4.0
    assert parsed["active"] is True
    assert parsed["ledger_id"] is None
    assert parsed["nodes"] == ["node1", "node2"]

    dumped = dump_yaml(parsed)
    assert "name: BABYLON-60" in dumped
    assert "active: true" in dumped


def test_matrix_vector_sovereign() -> None:
    v1 = Vector([1.0, 2.0, 3.0])
    v2 = Vector([4.0, 5.0, 6.0])
    assert v1.dot(v2) == 1.0 * 4.0 + 2.0 * 5.0 + 3.0 * 6.0

    m1 = Matrix(2, 2, 0.0)
    m1[0, 0] = 1.0
    m1[0, 1] = 2.0
    m1[1, 0] = 3.0
    m1[1, 1] = 4.0

    m2 = Matrix(2, 2, 0.0)
    m2[0, 0] = 2.0
    m2[0, 1] = 0.0
    m2[1, 0] = 0.0
    m2[1, 1] = 2.0

    m3 = m1.matmul(m2)
    assert m3[0, 0] == 2.0
    assert m3[0, 1] == 4.0
    assert m3[1, 0] == 6.0
    assert m3[1, 1] == 8.0

    dist = {"A": 0.8, "B": 0.2}
    vec = dict_to_vector(dist, ["A", "B"])
    assert vec[0] == 0.8
    assert vec[1] == 0.2
    d_back = vector_to_dict(vec, ["A", "B"])
    assert abs(d_back["A"] - 0.8) < 1e-6
