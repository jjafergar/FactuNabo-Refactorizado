"""
Modelos de datos para la cola de envíos offline.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OfflineQueueItem:
    """Representa un elemento en la cola de envíos offline."""
    
    id: Optional[int]
    xml_content: bytes
    invoice_id: str
    company: str
    exercise: str
    customer_doc: str
    api_key: str
    created_at: datetime
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    status: str = "PENDIENTE"  # "PENDIENTE", "PROCESADO", "ERROR"
    error_message: Optional[str] = None
    
    @property
    def is_pending(self) -> bool:
        """Indica si el elemento está pendiente."""
        return self.status == "PENDIENTE"
    
    @property
    def is_processed(self) -> bool:
        """Indica si el elemento fue procesado."""
        return self.status == "PROCESADO"
    
    @property
    def is_error(self) -> bool:
        """Indica si el elemento tiene error."""
        return self.status == "ERROR"
    
    @property
    def should_retry(self) -> bool:
        """Indica si se debe reintentar el envío."""
        return self.is_pending and self.attempts < 3


__all__ = ["OfflineQueueItem"]
