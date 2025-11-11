"""
Inicialización centralizada de logging (texto y JSON opcional).
"""
from __future__ import annotations

import json
import logging
import os
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Optional

from .resources import resource_path


class JsonLinesHandler(logging.Handler):
    """
    Escribe eventos en un archivo .jsonl para análisis posterior.
    """

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = self._serialize(record)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception:
            self.handleError(record)

    def _serialize(self, record: logging.LogRecord) -> Dict[str, Any]:
        data = record.__dict__.copy()
        data["level"] = record.levelname
        data["message"] = record.getMessage()
        for k in list(data.keys()):
            if k.startswith("_") or k in {"args", "exc_info", "exc_text", "stack_info"}:
                data.pop(k, None)
        return data


def _default_json_log_path() -> Path:
    base = Path(resource_path("logs"))
    return base / "app_events.jsonl"


def configure_logging(level: int = logging.INFO, json_log: bool = True) -> Logger:
    """
    Configura logging raíz con formato amigable y opcional JSONL.
    """
    logger = logging.getLogger("FactuNabo")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if json_log:
        try:
            json_path = _default_json_log_path()
            logger.addHandler(JsonLinesHandler(json_path))
        except Exception:
            logger.warning("No se pudo inicializar el log JSON estructurado.", exc_info=True)

    return logger


def get_logger(name: Optional[str] = None) -> Logger:
    parent = configure_logging()
    return parent.getChild(name) if name else parent


__all__ = ["configure_logging", "get_logger", "JsonLinesHandler"]

