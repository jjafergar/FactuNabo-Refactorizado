"""
Servicio para procesamiento de facturas y lógica de negocio.
Extrae la lógica pura de worker.py para mejorar la testabilidad.
"""
from __future__ import annotations

import os
import re
import json
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal

import pandas as pd

from app.core.logging import get_logger
from app.models.invoice import InvoiceProcessingResult, InvoiceValidationError


logger = get_logger("services.invoice_processing")


class InvoiceProcessingService:
    """Servicio para procesamiento de facturas."""
    
    def __init__(self):
        """Inicializa el servicio de procesamiento de facturas."""
        pass
    
    @staticmethod
    def normalize_invoice_id(invoice_id: Any) -> str:
        """
        Normaliza un ID de factura eliminando decimales innecesarios.
        
        Args:
            invoice_id: ID de factura a normalizar
            
        Returns:
            ID normalizado como string
        """
        s = str(invoice_id).strip()
        # Si es numérico (incluye "25042.0"), devolvemos entero sin .0
        if re.fullmatch(r"\d+(?:\.0+)?", s):
            try:
                return str(int(float(s)))
            except Exception:
                return s
        # Si es alfanumérico (p.ej. "Int_25003"), devolvemos tal cual
        return s
    
    @staticmethod
    def format_currency_eur(value: Any) -> str:
        """
        Formatea un valor monetario en formato español (3.976,42€).
        
        Args:
            value: Valor a formatear
            
        Returns:
            String formateado con el símbolo de euro
        """
        try:
            v = float(value)
        except Exception:
            return ""
        s = f"{v:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{s}€"
    
    @staticmethod
    def parse_amount(raw_amount: Any) -> Decimal:
        """
        Parsea un importe desde diferentes formatos a Decimal.
        
        Args:
            raw_amount: Importe en formato string, float o Decimal
            
        Returns:
            Importe como Decimal
        """
        if isinstance(raw_amount, Decimal):
            return raw_amount
        
        if isinstance(raw_amount, (int, float)):
            return Decimal(str(raw_amount))
        
        if isinstance(raw_amount, str):
            # Eliminar símbolos de moneda y espacios
            cleaned = raw_amount.replace("€", "").replace("$", "").strip()
            # Convertir formato español a formato estándar
            if "," in cleaned and "." in cleaned:
                # Formato: 1.234,56 -> 1234.56
                cleaned = cleaned.replace(".", "").replace(",", ".")
            elif "," in cleaned:
                # Formato: 1234,56 -> 1234.56
                cleaned = cleaned.replace(",", ".")
            
            try:
                return Decimal(cleaned)
            except Exception:
                logger.warning(f"No se pudo parsear el importe: {raw_amount}")
                return Decimal("0.0")
        
        return Decimal("0.0")
    
    @staticmethod
    def extract_pdf_url(item: Dict[str, Any]) -> Optional[str]:
        """
        Extrae la URL del PDF de un item de respuesta de la API.
        
        Args:
            item: Diccionario con la respuesta de la API
            
        Returns:
            URL del PDF si se encuentra, None en caso contrario
        """
        # Buscar en campos comunes
        for key in ["pdf_url", "url_pdf", "pdf", "url", "enlace_pdf", "link"]:
            if key in item:
                url = item[key]
                if isinstance(url, str) and url.startswith("http"):
                    return url
        
        # Buscar recursivamente en el diccionario
        def _iter_scalars(obj: Any):
            if isinstance(obj, dict):
                for v in obj.values():
                    yield from _iter_scalars(v)
            elif isinstance(obj, (list, tuple)):
                for v in obj:
                    yield from _iter_scalars(v)
            else:
                yield obj
        
        # Buscar URLs que parezcan PDFs
        for scalar in _iter_scalars(item):
            if isinstance(scalar, str):
                match = re.search(r"https?://[^\s\"'>)]+", scalar)
                if match:
                    url = match.group(0)
                    url_lower = url.lower()
                    if any(keyword in url_lower for keyword in [".pdf", "pdf", "download", "descarga", "ver_afc_api.php"]):
                        return url
        
        return None
    
    @staticmethod
    def read_summary_file(path: str) -> List[Dict[str, Any]]:
        """
        Lee un archivo summary.json y extrae la lista de facturas procesadas.
        
        Args:
            path: Ruta al archivo summary.json
            
        Returns:
            Lista de diccionarios con información de facturas
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                if "proformas_procesadas" in data and isinstance(data["proformas_procesadas"], list):
                    return data["proformas_procesadas"]
                if "items" in data and isinstance(data["items"], list):
                    return data["items"]
                return [data]
            
            if isinstance(data, list):
                return data
            
            return []
        except Exception as e:
            logger.error(f"Error leyendo archivo summary {path}: {e}")
            return []
    
    @staticmethod
    def validate_invoice_data(
        df_factura: pd.DataFrame,
        df_conceptos: pd.DataFrame
    ) -> Tuple[bool, List[InvoiceValidationError]]:
        """
        Valida los datos de facturas y conceptos.
        
        Args:
            df_factura: DataFrame con datos de facturas
            df_conceptos: DataFrame con datos de conceptos
            
        Returns:
            Tupla (es_valido, lista_de_errores)
        """
        errors: List[InvoiceValidationError] = []
        
        # Validar columnas requeridas en facturas
        required_factura_cols = ["NumFactura", "empresa_emisora", "cliente_nombre"]
        for col in required_factura_cols:
            if col not in df_factura.columns:
                errors.append(InvoiceValidationError(
                    row_index=-1,
                    field_name=col,
                    error_message=f"Falta la columna requerida: {col}"
                ))
        
        # Validar columnas requeridas en conceptos
        required_conceptos_cols = ["NumFactura", "descripcion", "cantidad", "precio_unitario"]
        for col in required_conceptos_cols:
            if col not in df_conceptos.columns:
                errors.append(InvoiceValidationError(
                    row_index=-1,
                    field_name=col,
                    error_message=f"Falta la columna requerida en conceptos: {col}"
                ))
        
        # Si faltan columnas críticas, no continuar
        if errors:
            return False, errors
        
        # Validar cada factura
        for idx, row in df_factura.iterrows():
            invoice_id = InvoiceProcessingService.normalize_invoice_id(row.get("NumFactura", ""))
            
            # Validar que tenga número de factura
            if not invoice_id:
                errors.append(InvoiceValidationError(
                    row_index=idx,
                    field_name="NumFactura",
                    error_message="Número de factura vacío"
                ))
            
            # Validar que tenga empresa emisora
            if not row.get("empresa_emisora"):
                errors.append(InvoiceValidationError(
                    row_index=idx,
                    field_name="empresa_emisora",
                    error_message="Empresa emisora vacía",
                    invoice_id=invoice_id
                ))
            
            # Validar que tenga cliente
            if not row.get("cliente_nombre"):
                errors.append(InvoiceValidationError(
                    row_index=idx,
                    field_name="cliente_nombre",
                    error_message="Cliente vacío",
                    invoice_id=invoice_id
                ))
            
            # Validar que tenga conceptos asociados
            conceptos_factura = df_conceptos[
                df_conceptos["NumFactura"].map(InvoiceProcessingService.normalize_invoice_id) == invoice_id
            ]
            
            if len(conceptos_factura) == 0:
                errors.append(InvoiceValidationError(
                    row_index=idx,
                    field_name="conceptos",
                    error_message="La factura no tiene conceptos asociados",
                    invoice_id=invoice_id
                ))
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def calculate_invoice_totals(
        df_conceptos: pd.DataFrame,
        invoice_id: str
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calcula los totales de una factura (base, IVA, retención).
        
        Args:
            df_conceptos: DataFrame con conceptos
            invoice_id: ID de la factura
            
        Returns:
            Tupla (base_imponible, total_iva, total_retencion)
        """
        # Normalizar IDs en el DataFrame
        df_conceptos_norm = df_conceptos.copy()
        df_conceptos_norm["__id_norm__"] = df_conceptos_norm["NumFactura"].map(
            InvoiceProcessingService.normalize_invoice_id
        )
        
        # Filtrar conceptos de esta factura
        conceptos_factura = df_conceptos_norm[df_conceptos_norm["__id_norm__"] == invoice_id]
        
        base_sum = Decimal("0.0")
        iva_sum = Decimal("0.0")
        ret_sum = Decimal("0.0")
        
        for _, concepto in conceptos_factura.iterrows():
            try:
                cantidad = Decimal(str(concepto.get("cantidad", 0)))
                precio = Decimal(str(concepto.get("precio_unitario", 0)))
                iva_pct = Decimal(str(concepto.get("iva_porcentaje", 0)))
                ret_pct = Decimal(str(concepto.get("retencion_porcentaje", 0)))
                
                base = cantidad * precio
                iva = base * (iva_pct / Decimal("100"))
                ret = base * (ret_pct / Decimal("100"))
                
                base_sum += base
                iva_sum += iva
                ret_sum += ret
            except Exception as e:
                logger.warning(f"Error calculando totales para factura {invoice_id}: {e}")
        
        return base_sum, iva_sum, ret_sum


# Instancia global del servicio
_invoice_processing_service: Optional[InvoiceProcessingService] = None


def get_invoice_processing_service() -> InvoiceProcessingService:
    """Obtiene la instancia global del servicio de procesamiento de facturas."""
    global _invoice_processing_service
    if _invoice_processing_service is None:
        _invoice_processing_service = InvoiceProcessingService()
    return _invoice_processing_service


__all__ = ["InvoiceProcessingService", "get_invoice_processing_service"]
