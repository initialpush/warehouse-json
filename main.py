"""Интеграция модулей: отправитель -> JSON -> получатель."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from debug_helper import DebugHelper
from exceptions import WarehouseError
from module_a import Sender
from module_b import Receiver


def load_config():
    path = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = load_config()
    dbg = DebugHelper(enabled=cfg["debug"], log_file=cfg["log_file"])
    sender = Sender(dbg)
    receiver = Receiver(cfg["low_stock_threshold"], dbg)
    receiver.process = dbg.trace(receiver.process)

    income = sender.build_batch("income", [
        ("A-100", "Молоко 1л", 20, 85.5),
        ("A-200", "Хлеб", 10, 45),
        ("A-300", "Сыр", 4, 420),
    ])
    dbg.log("Приход товаров")
    receiver.process(sender.to_json(income))

    outcome = sender.build_batch("outcome", [("A-100", "Молоко 1л", 5, 85.5)])
    dbg.log("Списание товаров")
    receiver.process(sender.to_json(outcome))

    for title, payload in [
        ("Списание больше остатка",
         sender.to_json(sender.build_batch("outcome", [("A-300", "Сыр", 99, 420)]))),
        ("Неизвестный товар",
         sender.to_json(sender.build_batch("outcome", [("X-999", "?", 1, 1)]))),
        ("Битый JSON", "{not json"),
    ]:
        try:
            receiver.process(payload)
        except WarehouseError as exc:
            dbg.log(f"{title}: {type(exc).__name__}: {exc}", "warning")

    print("\n" + receiver.report())
    print("Низкий запас:", receiver.low_stock())


if __name__ == "__main__":
    main()
