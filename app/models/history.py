"""
Modelos de datos para el historial de envíos.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass(frozen=True)
class HistoryEntry:
    """Representa una entrada en el historial de envíos."""
    
    id: Optional[int]
    invoice_id: str
    company: str
    customer: str
    status: str  # "OK", "ERROR", "PENDIENTE"
    send_date: datetime
    amount: Decimal
    pdf_url: Optional[str] = None
    pdf_local_path: Optional[str] = None
    excel_path: Optional[str] = None
    details: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """Indica si el envío fue exitoso."""
        return self.status == "OK"
    
    @property
    def is_error(self) -> bool:
        """Indica si el envío tuvo error."""
        return self.status == "ERROR"
    
    @property
    def is_pending(self) -> bool:
        """Indica si el envío está pendiente."""
        return self.status == "PENDIENTE"


@dataclass
class HistoryFilter:
    """Filtros para consultar el historial."""
    
    company: Optional[str] = None
    customer: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_text: Optional[str] = None


@dataclass(frozen=True)
class HistoryStats:
    """Estadísticas del historial de envíos."""
    
    total_invoices: int
    successful_invoices: int
    failed_invoices: int
    pending_invoices: int
    total_amount: Decimal
    
    @property
    def success_rate(self) -> float:
        """Calcula el porcentaje de éxito."""
        if self.total_invoices == 0:
            return 0.0
        return (self.successful_invoices / self.total_invoices) * 100


__all__ = ["HistoryEntry", "HistoryFilter", "HistoryStats"]
