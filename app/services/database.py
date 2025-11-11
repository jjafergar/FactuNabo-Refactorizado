"""
Servicios de acceso a la base de datos SQLite utilizados por la aplicación.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterable, Optional, Sequence, Tuple

from app.core.resources import DB_PATH
from app.core.logging import get_logger


logger = get_logger("services.database")


@contextmanager
def get_connection(readonly: bool = False):
    """
    Devuelve un contexto con conexión a la base de datos.
    Si `readonly` es True, abre la DB en modo inmutable.
    """
    if readonly:
        uri = f"file:{DB_PATH}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    """
    Crea tablas e índices requeridos. Idempotente.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS envios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_envio TEXT NOT NULL,
                num_factura TEXT,
                empresa TEXT,
                estado TEXT,
                detalles TEXT,
                pdf_url TEXT,
                excel_path TEXT,
                pdf_local_path TEXT,
                importe REAL DEFAULT 0.0,
                cliente TEXT
            )
            """
        )

        for stmt in [
            "ALTER TABLE envios ADD COLUMN importe REAL DEFAULT 0.0",
            "ALTER TABLE envios ADD COLUMN cliente TEXT",
            "ALTER TABLE envios ADD COLUMN pdf_local_path TEXT",
        ]:
            try:
                cursor.execute(stmt)
            except sqlite3.OperationalError:
                pass

        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_fecha_envio ON envios(fecha_envio)",
            "CREATE INDEX IF NOT EXISTS idx_empresa ON envios(empresa)",
            "CREATE INDEX IF NOT EXISTS idx_estado ON envios(estado)",
            "CREATE INDEX IF NOT EXISTS idx_num_factura ON envios(num_factura)",
            "CREATE INDEX IF NOT EXISTS idx_cliente ON envios(cliente)",
        ]:
            try:
                cursor.execute(stmt)
            except sqlite3.OperationalError as e:
                logger.warning("Error creando índice: %s", e)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS offline_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                xml_content BLOB NOT NULL,
                num_factura TEXT NOT NULL,
                empresa TEXT NOT NULL,
                ejercicio TEXT,
                cliente_doc TEXT,
                api_key TEXT,
                fecha_creacion TEXT NOT NULL,
                intentos INTEGER DEFAULT 0,
                ultimo_intento TEXT,
                estado TEXT DEFAULT 'PENDIENTE'
            )
            """
        )
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_queue_estado ON offline_queue(estado)",
            "CREATE INDEX IF NOT EXISTS idx_queue_fecha ON offline_queue(fecha_creacion)",
        ]:
            try:
                cursor.execute(stmt)
            except sqlite3.OperationalError as e:
                logger.warning("Error creando índice cola offline: %s", e)
        conn.commit()


def execute_many(query: str, params_seq: Iterable[Sequence]) -> None:
    with get_connection() as conn:
        conn.executemany(query, params_seq)
        conn.commit()


def execute(query: str, params: Optional[Sequence] = None) -> None:
    with get_connection() as conn:
        conn.execute(query, params or [])
        conn.commit()


def fetch_all(query: str, params: Optional[Sequence] = None) -> Sequence[Tuple]:
    with get_connection(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(query, params or [])
        return cur.fetchall()


def fetch_one(query: str, params: Optional[Sequence] = None):
    with get_connection(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(query, params or [])
        return cur.fetchone()


def clear_history() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM envios")
        conn.commit()
        cursor.execute("VACUUM")
        conn.commit()


__all__ = [
    "get_connection",
    "init_database",
    "execute_many",
    "execute",
    "fetch_all",
    "fetch_one",
    "clear_history",
]

