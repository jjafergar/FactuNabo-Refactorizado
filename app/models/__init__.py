"""
Modelos de datos (dataclasses y validadores) usados por la aplicación.
"""

from app.models.invoice import (
    Invoice,
    InvoiceLine,
    Customer,
    InvoiceValidationError,
    InvoiceProcessingResult,
)
from app.models.user import User, UserSession
from app.models.history import HistoryEntry, HistoryFilter, HistoryStats
from app.models.offline_queue import OfflineQueueItem

__all__ = [
    "Invoice",
    "InvoiceLine",
    "Customer",
    "InvoiceValidationError",
    "InvoiceProcessingResult",
    "User",
    "UserSession",
    "HistoryEntry",
    "HistoryFilter",
    "HistoryStats",
    "OfflineQueueItem",
]
