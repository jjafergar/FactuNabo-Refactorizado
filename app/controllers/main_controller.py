"""
Controlador principal que maneja la lógica de negocio de la aplicación.
Separa la lógica de negocio de la interfaz de usuario.
"""
from __future__ import annotations

from typing import List, Dict, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.services.database import get_connection, fetch_all, execute_many, execute
from app.services.invoice_processing import get_invoice_processing_service
from app.services.offline_service import get_offline_service
from app.services.stats import StatsService
from app.models.invoice import InvoiceValidationError, InvoiceProcessingResult
from app.models.history import HistoryEntry, HistoryFilter, HistoryStats


logger = get_logger("controllers.main")


class MainController:
    """
    Controlador principal que coordina la lógica de negocio.
    Actúa como intermediario entre los servicios y la UI.
    """
    
    def __init__(self):
        """Inicializa el controlador principal."""
        self.settings = get_settings()
        self.invoice_service = get_invoice_processing_service()
        self.offline_service = get_offline_service()
        self.stats_service = StatsService()
        
        # Estado actual
        self.current_excel_path: Optional[str] = None
        self.validation_errors: List[InvoiceValidationError] = []
        self.df_factura: Optional[pd.DataFrame] = None
        self.df_conceptos: Optional[pd.DataFrame] = None
        self.df_factura_historico: Optional[pd.DataFrame] = None
        self.df_conceptos_historico: Optional[pd.DataFrame] = None
    
    def validate_excel_file(
        self,
        path: str,
        df_factura: pd.DataFrame,
        df_conceptos: pd.DataFrame
    ) -> Tuple[bool, List[InvoiceValidationError]]:
        """
        Valida un archivo Excel con facturas.
        
        Args:
            path: Ruta al archivo Excel
            df_factura: DataFrame con datos de facturas
            df_conceptos: DataFrame con datos de conceptos
            
        Returns:
            Tupla (es_valido, lista_de_errores)
        """
        logger.info(f"Validando archivo Excel: {path}")
        
        # Guardar datos en el estado
        self.current_excel_path = path
        self.df_factura = df_factura
        self.df_conceptos = df_conceptos
        
        # Validar usando el servicio
        is_valid, errors = self.invoice_service.validate_invoice_data(df_factura, df_conceptos)
        
        self.validation_errors = errors
        
        if is_valid:
            logger.info(f"Archivo Excel válido: {len(df_factura)} facturas")
        else:
            logger.warning(f"Archivo Excel con {len(errors)} errores de validación")
        
        return is_valid, errors
    
    def get_invoice_totals(self, invoice_id: str) -> Dict[str, Decimal]:
        """
        Obtiene los totales calculados de una factura.
        
        Args:
            invoice_id: ID de la factura
            
        Returns:
            Diccionario con base, iva, retencion y total
        """
        if self.df_conceptos is None:
            return {
                "base": Decimal("0.0"),
                "iva": Decimal("0.0"),
                "retencion": Decimal("0.0"),
                "total": Decimal("0.0")
            }
        
        base, iva, ret = self.invoice_service.calculate_invoice_totals(
            self.df_conceptos,
            invoice_id
        )
        
        total = base + iva - ret
        
        return {
            "base": base,
            "iva": iva,
            "retencion": ret,
            "total": total
        }
    
    def save_to_history(
        self,
        summary_data: List[Dict[str, Any]],
        excel_path: Optional[str] = None
    ) -> int:
        """
        Guarda los resultados de envío en el historial.
        
        Args:
            summary_data: Lista de diccionarios con información de envíos
            excel_path: Ruta al archivo Excel origen
            
        Returns:
            Número de registros guardados
        """
        if not summary_data:
            logger.warning("No hay datos para guardar en el historial")
            return 0
        
        fecha_envio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        excel_path = excel_path or self.current_excel_path
        
        rows_to_insert = []
        
        for item in summary_data:
            # Extraer información del item
            invoice_id = item.get("num_factura", item.get("NumFactura", ""))
            invoice_id = self.invoice_service.normalize_invoice_id(invoice_id)
            
            company = item.get("empresa", item.get("empresa_emisora", ""))
            customer = item.get("cliente", item.get("cliente_nombre", ""))
            status = item.get("estado", item.get("status", "DESCONOCIDO"))
            details = item.get("mensaje", item.get("message", ""))
            
            # Extraer URL del PDF
            pdf_url = self.invoice_service.extract_pdf_url(item)
            
            # Parsear importe
            raw_amount = item.get("importe", item.get("total", 0))
            amount = float(self.invoice_service.parse_amount(raw_amount))
            
            rows_to_insert.append((
                fecha_envio,
                invoice_id,
                company,
                status,
                details,
                pdf_url,
                excel_path,
                None,  # pdf_local_path se actualizará después
                amount,
                customer
            ))
        
        # Insertar en la base de datos
        query = """
            INSERT INTO envios 
            (fecha_envio, num_factura, empresa, estado, detalles, pdf_url, excel_path, 
             pdf_local_path, importe, cliente)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        execute_many(query, rows_to_insert)
        
        logger.info(f"Guardados {len(rows_to_insert)} registros en el historial")
        return len(rows_to_insert)
    
    def update_pdf_paths_in_history(
        self,
        summary_data: List[Dict[str, Any]],
        pdf_dest_dir: str
    ) -> int:
        """
        Actualiza las rutas locales de los PDFs en el historial.
        
        Args:
            summary_data: Lista de diccionarios con información de envíos
            pdf_dest_dir: Directorio donde se descargaron los PDFs
            
        Returns:
            Número de registros actualizados
        """
        updated = 0
        
        for item in summary_data:
            invoice_id = item.get("num_factura", item.get("NumFactura", ""))
            invoice_id = self.invoice_service.normalize_invoice_id(invoice_id)
            
            company = item.get("empresa", item.get("empresa_emisora", ""))
            
            # Buscar archivo PDF en el directorio
            pdf_pattern = f"{company}_{invoice_id}_*.pdf"
            pdf_files = list(Path(pdf_dest_dir).glob(pdf_pattern))
            
            if pdf_files:
                pdf_local_path = str(pdf_files[0])
                
                # Actualizar en la base de datos
                query = """
                    UPDATE envios 
                    SET pdf_local_path = ?
                    WHERE num_factura = ? AND empresa = ?
                    ORDER BY fecha_envio DESC
                    LIMIT 1
                """
                
                execute(query, (pdf_local_path, invoice_id, company))
                updated += 1
        
        logger.info(f"Actualizadas {updated} rutas de PDF en el historial")
        return updated
    
    def load_history(
        self,
        filters: Optional[HistoryFilter] = None
    ) -> List[HistoryEntry]:
        """
        Carga el historial de envíos con filtros opcionales.
        
        Args:
            filters: Filtros a aplicar
            
        Returns:
            Lista de entradas del historial
        """
        query = """
            SELECT id, num_factura, empresa, cliente, estado, fecha_envio, 
                   importe, pdf_url, pdf_local_path, excel_path, detalles
            FROM envios
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.company:
                query += " AND empresa = ?"
                params.append(filters.company)
            
            if filters.customer:
                query += " AND cliente = ?"
                params.append(filters.customer)
            
            if filters.status:
                query += " AND estado = ?"
                params.append(filters.status)
            
            if filters.date_from:
                query += " AND fecha_envio >= ?"
                params.append(filters.date_from.strftime("%Y-%m-%d %H:%M:%S"))
            
            if filters.date_to:
                query += " AND fecha_envio <= ?"
                params.append(filters.date_to.strftime("%Y-%m-%d %H:%M:%S"))
            
            if filters.search_text:
                query += " AND (num_factura LIKE ? OR cliente LIKE ? OR empresa LIKE ?)"
                search_pattern = f"%{filters.search_text}%"
                params.extend([search_pattern, search_pattern, search_pattern])
        
        query += " ORDER BY fecha_envio DESC"
        
        rows = fetch_all(query, params)
        
        entries = []
        for row in rows:
            entry = HistoryEntry(
                id=row[0],
                invoice_id=row[1],
                company=row[2],
                customer=row[3],
                status=row[4],
                send_date=datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"),
                amount=Decimal(str(row[6])),
                pdf_url=row[7],
                pdf_local_path=row[8],
                excel_path=row[9],
                details=row[10]
            )
            entries.append(entry)
        
        logger.debug(f"Cargadas {len(entries)} entradas del historial")
        return entries
    
    def get_history_stats(
        self,
        company: Optional[str] = None,
        period_days: Optional[int] = None
    ) -> HistoryStats:
        """
        Obtiene estadísticas del historial.
        
        Args:
            company: Filtrar por empresa
            period_days: Filtrar por últimos N días
            
        Returns:
            Estadísticas del historial
        """
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'OK' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN estado = 'ERROR' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) as pending,
                SUM(importe) as total_amount
            FROM envios
            WHERE 1=1
        """
        params = []
        
        if company:
            query += " AND empresa = ?"
            params.append(company)
        
        if period_days:
            date_from = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d %H:%M:%S")
            query += " AND fecha_envio >= ?"
            params.append(date_from)
        
        row = fetch_all(query, params)[0]
        
        stats = HistoryStats(
            total_invoices=row[0] or 0,
            successful_invoices=row[1] or 0,
            failed_invoices=row[2] or 0,
            pending_invoices=row[3] or 0,
            total_amount=Decimal(str(row[4] or 0))
        )
        
        return stats
    
    def get_companies_list(self) -> List[str]:
        """
        Obtiene la lista de empresas emisoras únicas del historial.
        
        Returns:
            Lista de nombres de empresas
        """
        query = "SELECT DISTINCT empresa FROM envios WHERE empresa IS NOT NULL ORDER BY empresa"
        rows = fetch_all(query)
        return [row[0] for row in rows]
    
    def get_customers_list(self) -> List[str]:
        """
        Obtiene la lista de clientes únicos del historial.
        
        Returns:
            Lista de nombres de clientes
        """
        query = "SELECT DISTINCT cliente FROM envios WHERE cliente IS NOT NULL ORDER BY cliente"
        rows = fetch_all(query)
        return [row[0] for row in rows]
    
    def clear_history(self) -> None:
        """Limpia todo el historial de envíos."""
        from app.services.database import clear_history
        clear_history()
        logger.info("Historial limpiado completamente")
    
    def process_offline_queue(
        self,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, int]:
        """
        Procesa la cola de envíos offline pendientes.
        
        Args:
            progress_callback: Función para reportar progreso
            
        Returns:
            Diccionario con estadísticas del procesamiento
        """
        pending_items = self.offline_service.get_pending_items()
        
        if not pending_items:
            logger.info("No hay items pendientes en la cola offline")
            return {"processed": 0, "success": 0, "failed": 0}
        
        processed = 0
        success = 0
        failed = 0
        
        for item in pending_items:
            if progress_callback:
                progress_callback(f"Procesando factura {item.invoice_id}...")
            
            # Aquí iría la lógica de reenvío a la API
            # Por ahora solo simulamos el procesamiento
            try:
                # TODO: Implementar lógica de reenvío
                self.offline_service.mark_as_sent(item.id)
                success += 1
            except Exception as e:
                logger.error(f"Error procesando item {item.id}: {e}")
                self.offline_service.mark_as_failed(item.id, str(e))
                failed += 1
            
            processed += 1
        
        logger.info(f"Cola offline procesada: {success} éxitos, {failed} fallos")
        
        return {
            "processed": processed,
            "success": success,
            "failed": failed
        }


__all__ = ["MainController"]
