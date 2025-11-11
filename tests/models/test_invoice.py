"""
Tests para los modelos de datos de facturas.
"""
import pytest
from decimal import Decimal
from datetime import date

from app.models.invoice import (
    InvoiceLine,
    Customer,
    Invoice,
    InvoiceValidationError,
    InvoiceProcessingResult
)


@pytest.mark.unit
def test_invoice_line_creation():
    """Test de creación de línea de factura."""
    line = InvoiceLine(
        description="Servicio de consultoría",
        quantity=Decimal("2"),
        unit_price=Decimal("100.00"),
        tax_rate=Decimal("21"),
        retention_rate=Decimal("15")
    )
    
    assert line.description == "Servicio de consultoría"
    assert line.quantity == Decimal("2")
    assert line.unit_price == Decimal("100.00")


@pytest.mark.unit
def test_invoice_line_subtotal():
    """Test de cálculo de subtotal."""
    line = InvoiceLine(
        description="Servicio",
        quantity=Decimal("2"),
        unit_price=Decimal("100.00"),
        tax_rate=Decimal("21")
    )
    
    assert line.subtotal == Decimal("200.00")


@pytest.mark.unit
def test_invoice_line_tax_amount():
    """Test de cálculo de IVA."""
    line = InvoiceLine(
        description="Servicio",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        tax_rate=Decimal("21")
    )
    
    assert line.tax_amount == Decimal("21.00")


@pytest.mark.unit
def test_invoice_line_retention_amount():
    """Test de cálculo de retención."""
    line = InvoiceLine(
        description="Servicio",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        tax_rate=Decimal("21"),
        retention_rate=Decimal("15")
    )
    
    assert line.retention_amount == Decimal("15.00")


@pytest.mark.unit
def test_invoice_line_total():
    """Test de cálculo de total de línea."""
    line = InvoiceLine(
        description="Servicio",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        tax_rate=Decimal("21"),
        retention_rate=Decimal("15")
    )
    
    # 100 + 21 - 15 = 106
    assert line.total == Decimal("106.00")


@pytest.mark.unit
def test_customer_creation():
    """Test de creación de cliente."""
    customer = Customer(
        name="Test Customer SL",
        tax_id="B12345678",
        address="Calle Test 123",
        postal_code="28001",
        city="Madrid"
    )
    
    assert customer.name == "Test Customer SL"
    assert customer.tax_id == "B12345678"
    assert customer.country == "España"  # Valor por defecto


@pytest.mark.unit
def test_invoice_creation():
    """Test de creación de factura completa."""
    customer = Customer(
        name="Test Customer",
        tax_id="B12345678"
    )
    
    lines = [
        InvoiceLine(
            description="Servicio 1",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("21")
        ),
        InvoiceLine(
            description="Servicio 2",
            quantity=Decimal("2"),
            unit_price=Decimal("50.00"),
            tax_rate=Decimal("21")
        )
    ]
    
    invoice = Invoice(
        invoice_id="25001",
        issuer_company="Test Company SL",
        customer=customer,
        issue_date=date(2025, 1, 1),
        lines=lines
    )
    
    assert invoice.invoice_id == "25001"
    assert len(invoice.lines) == 2


@pytest.mark.unit
def test_invoice_subtotal():
    """Test de cálculo de base imponible total."""
    customer = Customer(name="Test", tax_id="B12345678")
    
    lines = [
        InvoiceLine(
            description="Servicio 1",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("21")
        ),
        InvoiceLine(
            description="Servicio 2",
            quantity=Decimal("2"),
            unit_price=Decimal("50.00"),
            tax_rate=Decimal("21")
        )
    ]
    
    invoice = Invoice(
        invoice_id="25001",
        issuer_company="Test Company",
        customer=customer,
        issue_date=date(2025, 1, 1),
        lines=lines
    )
    
    # 100 + (2 * 50) = 200
    assert invoice.subtotal == Decimal("200.00")


@pytest.mark.unit
def test_invoice_total_tax():
    """Test de cálculo de IVA total."""
    customer = Customer(name="Test", tax_id="B12345678")
    
    lines = [
        InvoiceLine(
            description="Servicio",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("21")
        )
    ]
    
    invoice = Invoice(
        invoice_id="25001",
        issuer_company="Test Company",
        customer=customer,
        issue_date=date(2025, 1, 1),
        lines=lines
    )
    
    # 100 * 0.21 = 21
    assert invoice.total_tax == Decimal("21.00")


@pytest.mark.unit
def test_invoice_total_amount():
    """Test de cálculo de importe total."""
    customer = Customer(name="Test", tax_id="B12345678")
    
    lines = [
        InvoiceLine(
            description="Servicio",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("21"),
            retention_rate=Decimal("15")
        )
    ]
    
    invoice = Invoice(
        invoice_id="25001",
        issuer_company="Test Company",
        customer=customer,
        issue_date=date(2025, 1, 1),
        lines=lines
    )
    
    # 100 + 21 - 15 = 106
    assert invoice.total_amount == Decimal("106.00")


@pytest.mark.unit
def test_invoice_immutability():
    """Test de inmutabilidad de Invoice."""
    customer = Customer(name="Test", tax_id="B12345678")
    
    invoice = Invoice(
        invoice_id="25001",
        issuer_company="Test Company",
        customer=customer,
        issue_date=date(2025, 1, 1),
        lines=[]
    )
    
    # Intentar modificar debería fallar
    with pytest.raises(Exception):
        invoice.invoice_id = "25002"


@pytest.mark.unit
def test_validation_error_creation():
    """Test de creación de error de validación."""
    error = InvoiceValidationError(
        row_index=5,
        field_name="cliente_nombre",
        error_message="Cliente vacío",
        invoice_id="25001"
    )
    
    assert error.row_index == 5
    assert error.field_name == "cliente_nombre"
    assert error.invoice_id == "25001"


@pytest.mark.unit
def test_processing_result_creation():
    """Test de creación de resultado de procesamiento."""
    result = InvoiceProcessingResult(
        invoice_id="25001",
        status="success",
        pdf_url="https://example.com/invoice.pdf"
    )
    
    assert result.invoice_id == "25001"
    assert result.status == "success"
    assert result.timestamp is not None
