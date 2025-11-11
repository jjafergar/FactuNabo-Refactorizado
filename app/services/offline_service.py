"""
Servicio para gestionar la cola de envíos offline.
Refactorizado para usar el gestor de conexiones centralizado.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Optional

from app.core.logging import get_logger
from app.core.resources import DB_PATH
from app.services.database import get_connection, execute, fetch_all, fetch_one
from app.models.offline_queue import OfflineQueueItem


logger = get_logger("services.offline")


class OfflineQueueService:
    """Servicio para gestionar la cola de envíos offline."""
    
    def __init__(self):
        """Inicializa el servicio de cola offline."""
        pass
    
    def add_to_queue(
        self,
        xml_content: bytes,
        invoice_id: str,
        company: str,
        exercise: str,
        customer_doc: str,
        api_key: str
    ) -> int:
        """
        Añade un envío a la cola offline.
        
        Args:
            xml_content: Contenido XML de la factura
            invoice_id: Número de factura
            company: Empresa emisora
            exercise: Ejercicio fiscal
            customer_doc: Documento del cliente
            api_key: Clave API para el envío
            
        Returns:
            ID del elemento en la cola
        """
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
            INSERT INTO offline_queue 
            (xml_content, num_factura, empresa, ejercicio, cliente_doc, api_key, fecha_creacion, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')
        """
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (xml_content, invoice_id, company, exercise, customer_doc, api_key, fecha_creacion)
            )
            queue_id = cursor.lastrowid
            conn.commit()
        
        logger.info(f"Factura {invoice_id} añadida a cola offline con ID {queue_id}")
        return queue_id
    
    def get_pending_items(self, limit: int = 50) -> List[OfflineQueueItem]:
        """
        Obtiene items pendientes de la cola.
        
        Args:
            limit: Número máximo de items a obtener
            
        Returns:
            Lista de items pendientes
        """
        query = """
            SELECT id, xml_content, num_factura, empresa, ejercicio, 
                   cliente_doc, api_key, intentos, fecha_creacion, ultimo_intento
            FROM offline_queue
            WHERE estado = 'PENDIENTE'
            ORDER BY fecha_creacion ASC
            LIMIT ?
        """
        
        rows = fetch_all(query, (limit,))
        
        items = []
        for row in rows:
            item = OfflineQueueItem(
                id=row[0],
                xml_content=row[1],
                invoice_id=row[2],
                company=row[3],
                exercise=row[4],
                customer_doc=row[5],
                api_key=row[6],
                attempts=row[7],
                created_at=datetime.strptime(row[8], "%Y-%m-%d %H:%M:%S"),
                last_attempt=datetime.strptime(row[9], "%Y-%m-%d %H:%M:%S") if row[9] else None,
                status="PENDIENTE"
            )
            items.append(item)
        
        logger.debug(f"Obtenidos {len(items)} items pendientes de la cola")
        return items
    
    def mark_as_sent(self, queue_id: int) -> None:
        """
        Marca un item como enviado exitosamente.
        
        Args:
            queue_id: ID del elemento en la cola
        """
        query = """
            UPDATE offline_queue
            SET estado = 'ENVIADO', ultimo_intento = ?
            WHERE id = ?
        """
        
        execute(query, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), queue_id))
        logger.info(f"Item {queue_id} marcado como enviado")
    
    def mark_as_failed(self, queue_id: int, error_msg: str, max_retries: int = 3) -> None:
        """
        Marca un item como fallido o incrementa intentos.
        
        Args:
            queue_id: ID del elemento en la cola
            error_msg: Mensaje de error
            max_retries: Número máximo de reintentos
        """
        # Obtener intentos actuales
        query_select = "SELECT intentos FROM offline_queue WHERE id = ?"
        row = fetch_one(query_select, (queue_id,))
        
        if row:
            intentos = row[0] + 1
            estado = "FALLIDO" if intentos >= max_retries else "PENDIENTE"
            
            query_update = """
                UPDATE offline_queue
                SET estado = ?, intentos = ?, ultimo_intento = ?
                WHERE id = ?
            """
            
            execute(
                query_update,
                (estado, intentos, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), queue_id)
            )
            
            logger.warning(
                f"Item {queue_id} marcado como {estado} "
                f"(intento {intentos}/{max_retries}): {error_msg}"
            )
    
    def clear_sent_items(self) -> int:
        """
        Elimina items enviados de la cola.
        
        Returns:
            Número de items eliminados
        """
        query_count = "SELECT COUNT(*) FROM offline_queue WHERE estado = 'ENVIADO'"
        count_row = fetch_one(query_count)
        count = count_row[0] if count_row else 0
        
        query_delete = "DELETE FROM offline_queue WHERE estado = 'ENVIADO'"
        execute(query_delete)
        
        logger.info(f"Eliminados {count} items enviados de la cola")
        return count
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas de la cola.
        
        Returns:
            Diccionario con estadísticas por estado
        """
        query = "SELECT estado, COUNT(*) FROM offline_queue GROUP BY estado"
        rows = fetch_all(query)
        
        stats = {}
        for row in rows:
            stats[row[0]] = row[1]
        
        logger.debug(f"Estadísticas de cola: {stats}")
        return stats
    
    def get_total_pending(self) -> int:
        """
        Obtiene el número total de items pendientes.
        
        Returns:
            Número de items pendientes
        """
        query = "SELECT COUNT(*) FROM offline_queue WHERE estado = 'PENDIENTE'"
        row = fetch_one(query)
        return row[0] if row else 0


# Instancia global del servicio
_offline_service: Optional[OfflineQueueService] = None


def get_offline_service() -> OfflineQueueService:
    """Obtiene la instancia global del servicio de cola offline."""
    global _offline_service
    if _offline_service is None:
        _offline_service = OfflineQueueService()
    return _offline_service


__all__ = ["OfflineQueueService", "get_offline_service"]
