"""
Tests para el servicio de base de datos.
"""
import pytest
from pathlib import Path

from app.services.database import (
    init_database,
    get_connection,
    execute,
    execute_many,
    fetch_all,
    fetch_one,
    clear_history
)


@pytest.mark.unit
@pytest.mark.database
def test_init_database(mock_db_path):
    """Test de inicialización de la base de datos."""
    init_database()
    
    # Verificar que el archivo de BD existe
    assert Path(mock_db_path).exists()
    
    # Verificar que las tablas existen
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar tabla envios
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='envios'"
        )
        assert cursor.fetchone() is not None
        
        # Verificar tabla offline_queue
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='offline_queue'"
        )
        assert cursor.fetchone() is not None


@pytest.mark.unit
@pytest.mark.database
def test_execute_and_fetch(mock_db_path):
    """Test de inserción y consulta de datos."""
    init_database()
    
    # Insertar datos de prueba
    execute(
        "INSERT INTO envios (fecha_envio, num_factura, empresa, estado) VALUES (?, ?, ?, ?)",
        ("2025-01-01 12:00:00", "25001", "Test Company", "OK")
    )
    
    # Consultar datos
    rows = fetch_all("SELECT num_factura, empresa FROM envios WHERE num_factura = ?", ("25001",))
    
    assert len(rows) == 1
    assert rows[0][0] == "25001"
    assert rows[0][1] == "Test Company"


@pytest.mark.unit
@pytest.mark.database
def test_execute_many(mock_db_path):
    """Test de inserción múltiple."""
    init_database()
    
    # Insertar múltiples registros
    data = [
        ("2025-01-01 12:00:00", "25001", "Company A", "OK"),
        ("2025-01-02 12:00:00", "25002", "Company B", "OK"),
        ("2025-01-03 12:00:00", "25003", "Company A", "ERROR"),
    ]
    
    execute_many(
        "INSERT INTO envios (fecha_envio, num_factura, empresa, estado) VALUES (?, ?, ?, ?)",
        data
    )
    
    # Verificar que se insertaron todos
    rows = fetch_all("SELECT COUNT(*) FROM envios")
    assert rows[0][0] == 3


@pytest.mark.unit
@pytest.mark.database
def test_fetch_one(mock_db_path):
    """Test de consulta de un solo registro."""
    init_database()
    
    execute(
        "INSERT INTO envios (fecha_envio, num_factura, empresa, estado) VALUES (?, ?, ?, ?)",
        ("2025-01-01 12:00:00", "25001", "Test Company", "OK")
    )
    
    row = fetch_one("SELECT num_factura FROM envios WHERE num_factura = ?", ("25001",))
    
    assert row is not None
    assert row[0] == "25001"


@pytest.mark.unit
@pytest.mark.database
def test_fetch_one_not_found(mock_db_path):
    """Test de consulta que no encuentra resultados."""
    init_database()
    
    row = fetch_one("SELECT num_factura FROM envios WHERE num_factura = ?", ("99999",))
    
    assert row is None


@pytest.mark.unit
@pytest.mark.database
def test_clear_history(mock_db_path):
    """Test de limpieza del historial."""
    init_database()
    
    # Insertar datos
    execute(
        "INSERT INTO envios (fecha_envio, num_factura, empresa, estado) VALUES (?, ?, ?, ?)",
        ("2025-01-01 12:00:00", "25001", "Test Company", "OK")
    )
    
    # Verificar que hay datos
    rows = fetch_all("SELECT COUNT(*) FROM envios")
    assert rows[0][0] == 1
    
    # Limpiar historial
    clear_history()
    
    # Verificar que no hay datos
    rows = fetch_all("SELECT COUNT(*) FROM envios")
    assert rows[0][0] == 0


@pytest.mark.unit
@pytest.mark.database
def test_connection_context_manager(mock_db_path):
    """Test del context manager de conexión."""
    init_database()
    
    # Usar el context manager
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
    
    # La conexión debe estar cerrada después del context manager
    # (no hay forma directa de verificar esto en sqlite3, pero el test
    # no debe fallar)


@pytest.mark.unit
@pytest.mark.database
def test_readonly_connection(mock_db_path):
    """Test de conexión en modo solo lectura."""
    init_database()
    
    # Insertar datos con conexión normal
    execute(
        "INSERT INTO envios (fecha_envio, num_factura, empresa, estado) VALUES (?, ?, ?, ?)",
        ("2025-01-01 12:00:00", "25001", "Test Company", "OK")
    )
    
    # Leer con conexión readonly
    with get_connection(readonly=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT num_factura FROM envios WHERE num_factura = ?", ("25001",))
        result = cursor.fetchone()
        assert result[0] == "25001"
