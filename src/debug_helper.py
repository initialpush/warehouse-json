"""Отладочный класс DebugHelper: log(), dump(), trace()."""
import functools
import json
import logging


class DebugHelper:
    def __init__(self, enabled=True, log_file=None):
        self.enabled = enabled
        self.logger = logging.getLogger("warehouse")
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            sh = logging.StreamHandler()
            sh.setFormatter(fmt)
            self.logger.addHandler(sh)
            if log_file:
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(fmt)
                self.logger.addHandler(fh)

    def log(self, message, level="info"):
        """Логирование сообщения с уровнем debug/info/warning/error."""
        if self.enabled:
            getattr(self.logger, level)(message)

    def dump(self, obj, title="obj"):
        """Красивый вывод объекта (dict/list/любой объект)."""
        if not self.enabled:
            return
        try:
            text = json.dumps(obj, ensure_ascii=False, indent=2, default=str)
        except TypeError:
            text = repr(obj)
        self.logger.debug("DUMP %s (%s):\n%s", title, type(obj).__name__, text)

    def trace(self, func):
        """Декоратор трассировки: пишет вызов, аргументы и результат."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.log(f"CALL {func.__qualname__} args={args} kwargs={kwargs}", "debug")
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                self.log(f"RAISE {func.__qualname__}: {type(exc).__name__}: {exc}", "error")
                raise
            self.log(f"RETURN {func.__qualname__} -> {result!r}", "debug")
            return result
        return wrapper
