"""
Utilidades de rutas y constantes compartidas en toda la aplicación.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache


@lru_cache(maxsize=128)
def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta absoluta del recurso tanto en desarrollo como en binarios.
    Usa caché para evitar recomputar rutas con frecuencia durante el ciclo de vida.
    """
    if getattr(sys, "frozen", False):
        exec_dir = os.path.dirname(sys.executable)
        candidate = os.path.join(exec_dir, relative_path)
        if os.path.exists(candidate) or not hasattr(sys, "_MEIPASS"):
            return candidate
        return os.path.join(sys._MEIPASS, relative_path)  # type: ignore[attr-defined]

    base_path = os.path.abspath(os.path.dirname(__file__))
    # __file__ apunta a app/core/, necesitamos subir al raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(base_path))
    return os.path.join(project_root, relative_path)


# Paleta de colores y constantes visuales (mantiene la estética actual)
COLOR_PRIMARY = "#A0BF6E"
COLOR_SUCCESS = "#34C759"
COLOR_WARNING = "#FF9500"
COLOR_ERROR = "#FF3B30"
COLOR_BACKGROUND = "#F2F2F7"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#000000"
COLOR_SECONDARY_TEXT = "#8E8E93"
COLOR_BORDER = "#C6C6C8"
COLOR_SIDEBAR = "#FAFAFA"
COLOR_SIDEBAR_DARK = "#1C1C1E"
COLOR_DARK_BG = "#000000"
COLOR_DARK_CARD = "#1C1C1E"
COLOR_DARK_TEXT = "#FFFFFF"
COLOR_DARK_BORDER = "#38383A"


RESOURCE_DIR = resource_path("resources")
DB_PATH = resource_path("factunabo_history.db")
USERS_PATH = resource_path("users.json")

__all__ = [
    "resource_path",
    "COLOR_PRIMARY",
    "COLOR_SUCCESS",
    "COLOR_WARNING",
    "COLOR_ERROR",
    "COLOR_BACKGROUND",
    "COLOR_CARD",
    "COLOR_TEXT",
    "COLOR_SECONDARY_TEXT",
    "COLOR_BORDER",
    "COLOR_SIDEBAR",
    "COLOR_SIDEBAR_DARK",
    "COLOR_DARK_BG",
    "COLOR_DARK_CARD",
    "COLOR_DARK_TEXT",
    "COLOR_DARK_BORDER",
    "RESOURCE_DIR",
    "DB_PATH",
    "USERS_PATH",
]

