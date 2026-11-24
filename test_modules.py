import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from debug_helper import DebugHelper
from exceptions import (InsufficientStockError, ProductNotFoundError,
                        ValidationError)
from module_a import Sender
from module_b import Receiver


def make_payload(op, items):
    s = Sender()
    return s.to_json(s.build_batch(op, items))


@pytest.fixture
def receiver():
    r = Receiver(low_stock_threshold=5)
    r.process(make_payload("income", [("A1", "Молоко", 10, 80), ("A2", "Сыр", 3, 400)]))
    return r


def test_build_batch_structure():
    batch = Sender().build_batch("income", [("A1", "Молоко", 1, 50)])
    assert batch["operation"] == "income"
    assert batch["items"][0]["sku"] == "A1"


def test_json_roundtrip_keeps_cyrillic():
    s = Sender()
    payload = s.to_json(s.build_batch("income", [("A1", "Хлеб", 2, 40)]))
    assert "Хлеб" in payload
    assert json.loads(payload)["items"][0]["name"] == "Хлеб"


def test_income_increases_stock(receiver):
    receiver.process(make_payload("income", [("A1", "Молоко", 5, 80)]))
    assert receiver.find("A1")["qty"] == 15


def test_outcome_decreases_stock(receiver):
    receiver.process(make_payload("outcome", [("A1", "Молоко", 4, 80)]))
    assert receiver.find("A1")["qty"] == 6


def test_outcome_more_than_stock(receiver):
    with pytest.raises(InsufficientStockError):
        receiver.process(make_payload("outcome", [("A1", "Молоко", 100, 80)]))


def test_outcome_unknown_sku(receiver):
    with pytest.raises(ProductNotFoundError):
        receiver.process(make_payload("outcome", [("ZZ", "?", 1, 1)]))


def test_invalid_json(receiver):
    with pytest.raises(ValidationError):
        receiver.process("{broken")


def test_negative_qty_rejected(receiver):
    with pytest.raises(ValidationError):
        receiver.process(make_payload("income", [("A1", "Молоко", -1, 80)]))


def test_unknown_operation(receiver):
    with pytest.raises(ValidationError):
        receiver.process(json.dumps({"operation": "move", "items": [1]}))


def test_low_stock(receiver):
    assert receiver.low_stock() == ["A2"]


def test_report_contains_total(receiver):
    assert "Общая стоимость остатков: 2000" in receiver.report()


def test_debug_helper_trace_returns_value():
    dbg = DebugHelper(enabled=True)

    @dbg.trace
    def add(x, y):
        return x + y

    assert add(1, 2) == 3
