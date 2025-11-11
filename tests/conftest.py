"""
Configuración de pytest y fixtures compartidas.
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Añadir el directorio raíz al path para imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Crea un directorio temporal para tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Crea una ruta para una base de datos temporal."""
    return temp_dir / "test.db"


@pytest.fixture
def mock_db_path(temp_db_path: Path, monkeypatch):
    """Mockea la ruta de la base de datos para tests."""
    monkeypatch.setattr("app.core.resources.DB_PATH", str(temp_db_path))
    monkeypatch.setattr("app.services.database.DB_PATH", str(temp_db_path))
    return temp_db_path


@pytest.fixture
def sample_invoice_data():
    """Datos de ejemplo para una factura."""
    return {
        "invoice_id": "25001",
        "company": "Test Company SL",
        "customer": "Test Customer",
        "amount": 1000.00,
        "status": "OK"
    }


@pytest.fixture
def sample_dataframe():
    """DataFrame de ejemplo con datos de facturas."""
    import pandas as pd
    
    data = {
        "NumFactura": ["25001", "25002", "25003"],
        "empresa_emisora": ["Company A", "Company B", "Company A"],
        "cliente_nombre": ["Customer 1", "Customer 2", "Customer 3"],
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_conceptos_dataframe():
    """DataFrame de ejemplo con conceptos."""
    import pandas as pd
    
    data = {
        "NumFactura": ["25001", "25001", "25002"],
        "descripcion": ["Servicio 1", "Servicio 2", "Servicio 3"],
        "cantidad": [1, 2, 1],
        "precio_unitario": [100.0, 200.0, 500.0],
        "iva_porcentaje": [21, 21, 21],
        "retencion_porcentaje": [0, 0, 15]
    }
    
    return pd.DataFrame(data)
