"""
Modelos de datos para usuarios y autenticación.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class User:
    """Representa un usuario del sistema."""
    
    username: str
    password_hash: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    def verify_password(self, password_hash: str) -> bool:
        """Verifica si el hash de contraseña coincide."""
        return self.password_hash == password_hash


@dataclass
class UserSession:
    """Representa una sesión de usuario activa."""
    
    username: str
    login_time: datetime
    remember_me: bool = False


__all__ = ["User", "UserSession"]
