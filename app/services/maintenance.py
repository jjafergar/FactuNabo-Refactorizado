"""
Servicios de mantenimiento: health checks, copias de seguridad y actualización de plantillas.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

from app.core.logging import get_logger
from app.core.resources import DB_PATH, USERS_PATH, resource_path
from app.services.database import get_connection


logger = get_logger("services.maintenance")


def run_health_checks(pdf_destination: str, browser_info: str) -> List[Dict[str, str]]:
    """
    Ejecuta una serie de comprobaciones y devuelve la lista de resultados.
    """
    results: List[Dict[str, str]] = []

    # Comprobación de base de datos
    try:
        with get_connection(readonly=True) as conn:
            conn.execute("SELECT 1")
        results.append({"nombre": "Base de datos", "estado": "OK", "detalle": "Conexión correcta a SQLite."})
    except Exception as exc:
        logger.exception("Health check DB falló")
        results.append({"nombre": "Base de datos", "estado": "ERROR", "detalle": str(exc)})

    # Carpeta de logs
    logs_dir = Path(resource_path("logs"))
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        test_file = logs_dir / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        results.append({"nombre": "Carpeta de logs", "estado": "OK", "detalle": str(logs_dir)})
    except Exception as exc:
        logger.exception("Health check logs falló")
        results.append({"nombre": "Carpeta de logs", "estado": "ERROR", "detalle": str(exc)})

    # Destino de PDFs
    try:
        pdf_path = Path(pdf_destination or "")
        if not pdf_path.exists():
            pdf_path.mkdir(parents=True, exist_ok=True)
        test_file = pdf_path / ".pdf_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        results.append({"nombre": "Destino PDFs", "estado": "OK", "detalle": str(pdf_path)})
    except Exception as exc:
        logger.exception("Health check destino PDF falló")
        results.append({"nombre": "Destino PDFs", "estado": "ERROR", "detalle": str(exc)})

    # Navegador detectado
    if browser_info:
        results.append({"nombre": "Navegador", "estado": "OK", "detalle": browser_info})
    else:
        results.append({"nombre": "Navegador", "estado": "ADVERTENCIA", "detalle": "No se detectó Chrome/Edge."})

    return results


def create_backup(backup_dir: Optional[Path] = None) -> Path:
    """
    Crea un backup comprimido de la base de datos y users.json.
    """
    backup_dir = backup_dir or Path(resource_path("backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = backup_dir / f"backup_factunabo_{timestamp}.zip"

    import zipfile

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(DB_PATH):
            zf.write(DB_PATH, arcname="factunabo_history.db")
        if os.path.exists(USERS_PATH):
            zf.write(USERS_PATH, arcname="users.json")

    logger.info("Backup creado en %s", archive_path)
    return archive_path


def check_remote_template_version(url: str, current_checksum: str) -> Dict[str, str]:
    """
    Comprueba la versión remota de la plantilla comparando firmas SHA256.
    """
    result = {"estado": "ERROR", "detalle": "URL no configurada"}
    if not url:
        return result

    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()
        remote_checksum = response.headers.get("X-Checksum-SHA256", "")
        if remote_checksum and remote_checksum == current_checksum:
            result = {"estado": "OK", "detalle": "La plantilla está actualizada."}
        else:
            result = {"estado": "ADVERTENCIA", "detalle": "Hay una versión diferente disponible."}
    except Exception as exc:
        logger.exception("Error comprobando la versión remota de la plantilla")
        result = {"estado": "ERROR", "detalle": str(exc)}
    return result


def download_template(url: str, destination: Path) -> Path:
    """
    Descarga una plantilla desde la URL indicada y la guarda en destino.
    """
    if not url:
        raise ValueError("La URL de actualización no está configurada.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    destination.write_bytes(response.content)
    logger.info("Plantilla descargada en %s", destination)
    return destination


def compute_file_checksum(path: Path) -> str:
    """
    Calcula el SHA256 del fichero indicado.
    """
    import hashlib

    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


__all__ = [
    "run_health_checks",
    "create_backup",
    "check_remote_template_version",
    "download_template",
    "compute_file_checksum",
]

