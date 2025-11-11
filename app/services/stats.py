"""
Servicios de estadísticas y métricas con cache ligero.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.core.logging import get_logger
from app.services.database import get_connection


logger = get_logger("services.stats")


@dataclass
class DashboardStats:
    total_success: int
    month_count: int
    month_total: float


class StatsService:
    """
    Gestiona métricas de dashboard con cache e invalidación explícita.
    """

    def __init__(self, ttl_seconds: int = 2) -> None:
        self._cache: Optional[DashboardStats] = None
        self._last_updated: Optional[datetime] = None
        self._ttl = timedelta(seconds=ttl_seconds)

    def invalidate(self) -> None:
        self._cache = None
        self._last_updated = None

    def get_dashboard_stats(self, force: bool = False) -> DashboardStats:
        if (
            not force
            and self._cache is not None
            and self._last_updated is not None
            and datetime.now() - self._last_updated < self._ttl
        ):
            return self._cache

        try:
            with get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM envios WHERE estado = 'ÉXITO'")
                total_success = cursor.fetchone()[0] or 0

                month_key = datetime.now().strftime("%Y-%m")
                cursor.execute(
                    """
                    SELECT COUNT(*), COALESCE(SUM(importe), 0.0)
                    FROM envios
                    WHERE (estado LIKE 'ÉXITO%' OR estado IN ('OK', 'SUCCESS'))
                      AND strftime('%Y-%m', fecha_envio) = ?
                    """,
                    (month_key,),
                )
                month_count, month_total = cursor.fetchone() or (0, 0.0)
        except Exception:
            logger.exception("Error calculando estadísticas de dashboard")
            return DashboardStats(0, 0, 0.0)

        stats = DashboardStats(total_success=total_success, month_count=month_count or 0, month_total=float(month_total or 0.0))
        self._cache = stats
        self._last_updated = datetime.now()
        return stats


__all__ = ["StatsService", "DashboardStats"]

