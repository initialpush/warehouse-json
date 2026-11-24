"""Пользовательские исключения проекта."""


class WarehouseError(Exception):
    """Базовое исключение проекта."""


class ValidationError(WarehouseError):
    """Входные данные не прошли проверку."""


class InsufficientStockError(WarehouseError):
    """Недостаточно товара на складе для списания."""


class ProductNotFoundError(WarehouseError):
    """Товар с указанным артикулом не найден."""
