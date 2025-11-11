"""
Tests para el servicio de procesamiento de facturas.
"""
import pytest
from decimal import Decimal

from app.services.invoice_processing import InvoiceProcessingService


@pytest.mark.unit
def test_normalize_invoice_id_numeric():
    """Test de normalización de ID numérico."""
    service = InvoiceProcessingService()
    
    assert service.normalize_invoice_id("25042") == "25042"
    assert service.normalize_invoice_id("25042.0") == "25042"
    assert service.normalize_invoice_id("25042.00") == "25042"
    assert service.normalize_invoice_id(25042) == "25042"
    assert service.normalize_invoice_id(25042.0) == "25042"


@pytest.mark.unit
def test_normalize_invoice_id_alphanumeric():
    """Test de normalización de ID alfanumérico."""
    service = InvoiceProcessingService()
    
    assert service.normalize_invoice_id("Int_25003") == "Int_25003"
    assert service.normalize_invoice_id("INT25_005") == "INT25_005"


@pytest.mark.unit
def test_format_currency_eur():
    """Test de formateo de moneda en euros."""
    service = InvoiceProcessingService()
    
    assert service.format_currency_eur(1000) == "1.000,00€"
    assert service.format_currency_eur(1234.56) == "1.234,56€"
    assert service.format_currency_eur(0.5) == "0,50€"
    assert service.format_currency_eur("invalid") == ""


@pytest.mark.unit
def test_parse_amount_from_decimal():
    """Test de parseo de importe desde Decimal."""
    service = InvoiceProcessingService()
    
    result = service.parse_amount(Decimal("1234.56"))
    assert result == Decimal("1234.56")


@pytest.mark.unit
def test_parse_amount_from_number():
    """Test de parseo de importe desde número."""
    service = InvoiceProcessingService()
    
    assert service.parse_amount(1234) == Decimal("1234")
    assert service.parse_amount(1234.56) == Decimal("1234.56")


@pytest.mark.unit
def test_parse_amount_from_string_spanish():
    """Test de parseo de importe desde string en formato español."""
    service = InvoiceProcessingService()
    
    assert service.parse_amount("1.234,56") == Decimal("1234.56")
    assert service.parse_amount("1234,56") == Decimal("1234.56")
    assert service.parse_amount("1.234,56€") == Decimal("1234.56")


@pytest.mark.unit
def test_parse_amount_from_string_english():
    """Test de parseo de importe desde string en formato inglés."""
    service = InvoiceProcessingService()
    
    assert service.parse_amount("1,234.56") == Decimal("1234.56")
    assert service.parse_amount("1234.56") == Decimal("1234.56")


@pytest.mark.unit
def test_parse_amount_invalid():
    """Test de parseo de importe inválido."""
    service = InvoiceProcessingService()
    
    assert service.parse_amount("invalid") == Decimal("0.0")
    assert service.parse_amount(None) == Decimal("0.0")


@pytest.mark.unit
def test_extract_pdf_url_direct():
    """Test de extracción de URL de PDF directa."""
    service = InvoiceProcessingService()
    
    item = {"pdf_url": "https://example.com/invoice.pdf"}
    assert service.extract_pdf_url(item) == "https://example.com/invoice.pdf"


@pytest.mark.unit
def test_extract_pdf_url_nested():
    """Test de extracción de URL de PDF anidada."""
    service = InvoiceProcessingService()
    
    item = {
        "data": {
            "result": {
                "url": "https://example.com/download/invoice.pdf"
            }
        }
    }
    url = service.extract_pdf_url(item)
    assert url is not None
    assert "invoice.pdf" in url


@pytest.mark.unit
def test_extract_pdf_url_not_found():
    """Test de extracción de URL cuando no existe."""
    service = InvoiceProcessingService()
    
    item = {"invoice_id": "25001", "status": "OK"}
    assert service.extract_pdf_url(item) is None


@pytest.mark.unit
def test_validate_invoice_data_valid(sample_dataframe, sample_conceptos_dataframe):
    """Test de validación de datos válidos."""
    service = InvoiceProcessingService()
    
    is_valid, errors = service.validate_invoice_data(
        sample_dataframe,
        sample_conceptos_dataframe
    )
    
    assert is_valid
    assert len(errors) == 0


@pytest.mark.unit
def test_validate_invoice_data_missing_columns():
    """Test de validación con columnas faltantes."""
    import pandas as pd
    
    service = InvoiceProcessingService()
    
    # DataFrame sin columna requerida
    df_factura = pd.DataFrame({"NumFactura": ["25001"]})
    df_conceptos = pd.DataFrame({"NumFactura": ["25001"]})
    
    is_valid, errors = service.validate_invoice_data(df_factura, df_conceptos)
    
    assert not is_valid
    assert len(errors) > 0


@pytest.mark.unit
def test_validate_invoice_data_no_concepts():
    """Test de validación de factura sin conceptos."""
    import pandas as pd
    
    service = InvoiceProcessingService()
    
    df_factura = pd.DataFrame({
        "NumFactura": ["25001"],
        "empresa_emisora": ["Company A"],
        "cliente_nombre": ["Customer 1"]
    })
    
    df_conceptos = pd.DataFrame({
        "NumFactura": ["25002"],  # Diferente factura
        "descripcion": ["Service"],
        "cantidad": [1],
        "precio_unitario": [100]
    })
    
    is_valid, errors = service.validate_invoice_data(df_factura, df_conceptos)
    
    assert not is_valid
    assert any("conceptos" in error.error_message.lower() for error in errors)


@pytest.mark.unit
def test_calculate_invoice_totals(sample_conceptos_dataframe):
    """Test de cálculo de totales de factura."""
    service = InvoiceProcessingService()
    
    base, iva, ret = service.calculate_invoice_totals(
        sample_conceptos_dataframe,
        "25001"
    )
    
    # Factura 25001: (1*100) + (2*200) = 500
    assert base == Decimal("500")
    # IVA 21%: 500 * 0.21 = 105
    assert iva == Decimal("105")
    # Sin retención
    assert ret == Decimal("0")


@pytest.mark.unit
def test_calculate_invoice_totals_with_retention(sample_conceptos_dataframe):
    """Test de cálculo de totales con retención."""
    service = InvoiceProcessingService()
    
    base, iva, ret = service.calculate_invoice_totals(
        sample_conceptos_dataframe,
        "25002"
    )
    
    # Factura 25002: 1*500 = 500
    assert base == Decimal("500")
    # IVA 21%: 500 * 0.21 = 105
    assert iva == Decimal("105")
    # Retención 15%: 500 * 0.15 = 75
    assert ret == Decimal("75")
