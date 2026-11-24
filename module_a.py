"""Модуль-отправитель: формирует партию товаров и сериализует в JSON."""
import json


class Sender:
    def __init__(self, debug=None):
        self.debug = debug

    def build_batch(self, operation, items):
        """operation: 'income' (приход) или 'outcome' (списание);
        items: список кортежей (sku, name, qty, price)."""
        batch = {
            "operation": operation,
            "items": [
                {"sku": s, "name": n, "qty": q, "price": p}
                for s, n, q, p in items
            ],
        }
        if self.debug:
            self.debug.dump(batch, "batch")
        return batch

    def to_json(self, batch):
        return json.dumps(batch, ensure_ascii=False)
