"""
Modelos de datos para facturas y conceptos relacionados.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal


@dataclass(frozen=True)
class InvoiceLine:
    """Representa una línea de concepto en una factura."""
    
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal
    retention_rate: Decimal = Decimal("0.0")
    
    @property
    def subtotal(self) -> Decimal:
        """Calcula el subtotal sin impuestos."""
        return self.quantity * self.unit_price
    
    @property
    def tax_amount(self) -> Decimal:
        """Calcula el importe del IVA."""
        return self.subtotal * (self.tax_rate / Decimal("100"))
    
    @property
    def retention_amount(self) -> Decimal:
        """Calcula el importe de la retención."""
        return self.subtotal * (self.retention_rate / Decimal("100"))
    
    @property
    def total(self) -> Decimal:
        """Calcula el total de la línea."""
        return self.subtotal + self.tax_amount - self.retention_amount


@dataclass(frozen=True)
class Customer:
    """Representa un cliente de una factura."""
    
    name: str
    tax_id: str
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "España"
    email: Optional[str] = None


@dataclass(frozen=True)
class Invoice:
    """Representa una factura completa."""
    
    invoice_id: str
    issuer_company: str
    customer: Customer
    issue_date: date
    lines: List[InvoiceLine]
    payment_method: str = "TRANSFERENCIA"
    exercise: Optional[str] = None
    
    @property
    def subtotal(self) -> Decimal:
        """Calcula la base imponible total."""
        return sum(line.subtotal for line in self.lines)
    
    @property
    def total_tax(self) -> Decimal:
        """Calcula el IVA total."""
        return sum(line.tax_amount for line in self.lines)
    
    @property
    def total_retention(self) -> Decimal:
        """Calcula la retención total."""
        return sum(line.retention_amount for line in self.lines)
    
    @property
    def total_amount(self) -> Decimal:
        """Calcula el importe total de la factura."""
        return self.subtotal + self.total_tax - self.total_retention


@dataclass(frozen=True)
class InvoiceValidationError:
    """Representa un error de validación en una factura."""
    
    row_index: int
    field_name: str
    error_message: str
    invoice_id: Optional[str] = None


@dataclass
class InvoiceProcessingResult:
    """Resultado del procesamiento de una factura."""
    
    invoice_id: str
    status: str  # "success", "error", "pending"
    pdf_url: Optional[str] = None
    pdf_local_path: Optional[str] = None
    error_message: Optional[str] = None
    api_response: Optional[dict] = None
    timestamp: datetime = field(default_factory=datetime.now)


__all__ = [
    "InvoiceLine",
    "Customer",
    "Invoice",
    "InvoiceValidationError",
    "InvoiceProcessingResult",
]
