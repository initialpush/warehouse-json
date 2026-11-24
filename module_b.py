"""Модуль-получатель: разбирает JSON, проверяет данные, ведёт остатки."""
import json

from exceptions import (InsufficientStockError, ProductNotFoundError,
                        ValidationError)


class Receiver:
    def __init__(self, low_stock_threshold=5, debug=None):
        self.stock = {}  # sku -> {"name", "qty", "price"}
        self.threshold = low_stock_threshold
        self.debug = debug

    def parse(self, payload):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Некорректный JSON: {exc}") from exc
        if not isinstance(data, dict) or data.get("operation") not in ("income", "outcome"):
            raise ValidationError("Неизвестная операция")
        if not isinstance(data.get("items"), list) or not data["items"]:
            raise ValidationError("Список товаров пуст или отсутствует")
        for item in data["items"]:
            self._validate_item(item)
        return data

    @staticmethod
    def _validate_item(item):
        if not isinstance(item, dict):
            raise ValidationError("Элемент списка должен быть объектом")
        for key in ("sku", "name", "qty", "price"):
            if key not in item:
                raise ValidationError(f"Нет поля '{key}'")
        if not isinstance(item["qty"], int) or item["qty"] <= 0:
            raise ValidationError("Количество должно быть целым числом > 0")
        if not isinstance(item["price"], (int, float)) or item["price"] < 0:
            raise ValidationError("Цена должна быть числом >= 0")

    def process(self, payload):
        data = self.parse(payload)
        for item in data["items"]:
            if data["operation"] == "income":
                self._income(item)
            else:
                self._outcome(item)
        return len(data["items"])

    def _income(self, item):
        rec = self.stock.setdefault(
            item["sku"], {"name": item["name"], "qty": 0, "price": item["price"]})
        rec["qty"] += item["qty"]
        rec["price"] = item["price"]

    def _outcome(self, item):
        rec = self.stock.get(item["sku"])
        if rec is None:
            raise ProductNotFoundError(f"Товар {item['sku']} не найден")
        if rec["qty"] < item["qty"]:
            raise InsufficientStockError(
                f"Товара {item['sku']}: на складе {rec['qty']}, запрошено {item['qty']}")
        rec["qty"] -= item["qty"]

    def find(self, sku):
        if sku not in self.stock:
            raise ProductNotFoundError(f"Товар {sku} не найден")
        return self.stock[sku]

    def low_stock(self):
        return [s for s, r in self.stock.items() if r["qty"] < self.threshold]

    def report(self):
        lines = ["Артикул | Название | Остаток | Цена"]
        for sku, r in sorted(self.stock.items()):
            lines.append(f"{sku} | {r['name']} | {r['qty']} | {r['price']}")
        total = sum(r["qty"] * r["price"] for r in self.stock.values())
        lines.append(f"Общая стоимость остатков: {total}")
        return "\n".join(lines)
