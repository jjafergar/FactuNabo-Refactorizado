from __future__ import annotations

"""
Wrapper ligero sobre QSettings para centralizar claves y valores por defecto.
"""

from typing import Any, Optional

from PySide6.QtCore import QSettings


class AppSettings:
    """
    Pequeño helper para acceder a QSettings con claves centralizadas.
    """

    ORGANIZATION = "FactuNabo"
    APPLICATION = "FactuNaboApp"

    KEY_ACCENT_COLOR = "accent_color"
    KEY_SPACING = "spacing"
    KEY_THEME = "theme"
    KEY_PDF_DEST = "pdf_destination"
    KEY_API_URL = "api/url"
    KEY_API_TOKEN = "api/token"
    KEY_API_USER = "api/user"
    KEY_API_TIMEOUT = "api/timeout"
    KEY_TEMPLATE_URL = "templates/update_url"

    def __init__(self) -> None:
        self._settings = QSettings(self.ORGANIZATION, self.APPLICATION)

    def value(self, key: str, default: Optional[Any] = None) -> Any:
        return self._settings.value(key, default)

    def set_value(self, key: str, value: Any) -> None:
        self._settings.setValue(key, value)

    # Compatibilidad con código existente (nomenclatura Qt)
    def setValue(self, key: str, value: Any) -> None:
        self.set_value(key, value)

    def remove(self, key: str) -> None:
        self._settings.remove(key)

    def sync(self) -> None:
        self._settings.sync()


def get_settings() -> AppSettings:
    return AppSettings()


__all__ = ["AppSettings", "get_settings"]

