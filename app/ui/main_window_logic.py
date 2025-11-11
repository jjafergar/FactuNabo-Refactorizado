"""
Lógica de interfaz de usuario para MainWindow.
Maneja eventos de UI y actualización de vistas sin lógica de negocio.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Dict, Any
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.controllers.main_controller import MainController
from app.models.history import HistoryFilter

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow


logger = get_logger("ui.main_window_logic")


class MainWindowLogic:
    """
    Maneja la lógica de la interfaz de usuario de MainWindow.
    Actúa como intermediario entre la UI y el controlador de negocio.
    """
    
    def __init__(self, main_window: QMainWindow):
        """
        Inicializa la lógica de UI.
        
        Args:
            main_window: Instancia de MainWindow
        """
        self.ui = main_window
        self.settings = get_settings()
        self.controller = MainController()
        
        # Estado de la UI
        self.current_page_index: int = 0
        self.history_reload_timer: Optional[QTimer] = None
        self.toast_timer: Optional[QTimer] = None
    
    def setup_connections(self) -> None:
        """Configura las conexiones de señales y slots."""
        # Este método se llamaría desde MainWindow.__init__
        # para conectar señales a métodos de esta clase
        pass
    
    def change_page(self, index: int) -> None:
        """
        Cambia la página actual del stacked widget.
        
        Args:
            index: Índice de la página a mostrar
        """
        self.current_page_index = index
        logger.debug(f"Cambiando a página {index}")
        
        # Actualizar badge de notificaciones si es necesario
        if hasattr(self.ui, '_update_send_badge'):
            self.ui._update_send_badge()
    
    def toggle_theme(self, checked: bool) -> None:
        """
        Alterna entre tema claro y oscuro.
        
        Args:
            checked: True para tema oscuro, False para tema claro
        """
        theme = "dark" if checked else "light"
        self.settings.set_value(self.settings.KEY_THEME, theme)
        
        logger.info(f"Tema cambiado a: {theme}")
        
        # Refrescar estilos
        if hasattr(self.ui, '_refresh_styles'):
            self.ui._refresh_styles()
    
    def apply_history_filters(self) -> None:
        """Aplica los filtros seleccionados al historial."""
        # Construir objeto de filtros desde los widgets de la UI
        filters = HistoryFilter()
        
        # Obtener valores de los combos/inputs de filtro
        if hasattr(self.ui, 'combo_filter_company'):
            company = self.ui.combo_filter_company.currentText()
            if company and company != "Todas":
                filters.company = company
        
        if hasattr(self.ui, 'combo_filter_customer'):
            customer = self.ui.combo_filter_customer.currentText()
            if customer and customer != "Todos":
                filters.customer = customer
        
        if hasattr(self.ui, 'combo_filter_status'):
            status = self.ui.combo_filter_status.currentText()
            if status and status != "Todos":
                filters.status = status
        
        # Cargar historial con filtros
        self.load_history_with_filters(filters)
    
    def clear_history_filters(self) -> None:
        """Limpia todos los filtros del historial."""
        if hasattr(self.ui, 'combo_filter_company'):
            self.ui.combo_filter_company.setCurrentIndex(0)
        
        if hasattr(self.ui, 'combo_filter_customer'):
            self.ui.combo_filter_customer.setCurrentIndex(0)
        
        if hasattr(self.ui, 'combo_filter_status'):
            self.ui.combo_filter_status.setCurrentIndex(0)
        
        # Recargar sin filtros
        self.load_history_with_filters(None)
    
    def load_history_with_filters(self, filters: Optional[HistoryFilter]) -> None:
        """
        Carga el historial aplicando filtros y actualiza la tabla.
        
        Args:
            filters: Filtros a aplicar, None para cargar todo
        """
        entries = self.controller.load_history(filters)
        
        # Actualizar tabla de historial
        if hasattr(self.ui, 'table_history'):
            self.ui.table_history.setRowCount(0)
            
            for entry in entries:
                row_position = self.ui.table_history.rowCount()
                self.ui.table_history.insertRow(row_position)
                
                # Aquí iría el código para poblar la tabla
                # (simplificado para este ejemplo)
        
        logger.info(f"Historial cargado: {len(entries)} entradas")
    
    def queue_history_reload(self, apply_filters: bool = True, immediate: bool = False) -> None:
        """
        Programa una recarga del historial con debouncing.
        
        Args:
            apply_filters: Si se deben aplicar los filtros actuales
            immediate: Si se debe recargar inmediatamente
        """
        if self.history_reload_timer is None:
            self.history_reload_timer = QTimer()
            self.history_reload_timer.setSingleShot(True)
            self.history_reload_timer.timeout.connect(self._execute_history_reload)
        
        if immediate:
            self._execute_history_reload()
        else:
            # Debouncing: esperar 500ms antes de recargar
            self.history_reload_timer.start(500)
    
    def _execute_history_reload(self) -> None:
        """Ejecuta la recarga del historial."""
        self.apply_history_filters()
    
    def update_dashboard_stats(self) -> None:
        """Actualiza las estadísticas del dashboard."""
        # Obtener filtros del dashboard
        company = None
        period_days = None
        
        if hasattr(self.ui, 'combo_dashboard_company'):
            company_text = self.ui.combo_dashboard_company.currentText()
            if company_text and company_text != "Todas":
                company = company_text
        
        if hasattr(self.ui, 'combo_dashboard_period'):
            period_text = self.ui.combo_dashboard_period.currentText()
            if "30 días" in period_text:
                period_days = 30
            elif "7 días" in period_text:
                period_days = 7
        
        # Obtener estadísticas
        stats = self.controller.get_history_stats(company, period_days)
        
        # Actualizar widgets del dashboard
        if hasattr(self.ui, 'label_total_invoices'):
            self.ui.label_total_invoices.setText(str(stats.total_invoices))
        
        if hasattr(self.ui, 'label_success_rate'):
            self.ui.label_success_rate.setText(f"{stats.success_rate:.1f}%")
        
        if hasattr(self.ui, 'label_total_amount'):
            from app.services.invoice_processing import get_invoice_processing_service
            service = get_invoice_processing_service()
            amount_text = service.format_currency_eur(stats.total_amount)
            self.ui.label_total_amount.setText(amount_text)
        
        logger.debug("Dashboard actualizado")
    
    def show_toast(
        self,
        message: str,
        duration: int = 3000,
        color_class: str = "info"
    ) -> None:
        """
        Muestra una notificación toast temporal.
        
        Args:
            message: Mensaje a mostrar
            duration: Duración en milisegundos
            color_class: Clase de color (info, success, warning, error)
        """
        if not hasattr(self.ui, 'toast_widget'):
            return
        
        # Configurar el widget toast
        self.ui.toast_widget.setText(message)
        self.ui.toast_widget.setProperty("class", f"toast-{color_class}")
        self.ui.toast_widget.setVisible(True)
        
        # Programar ocultación
        if self.toast_timer is None:
            self.toast_timer = QTimer()
            self.toast_timer.setSingleShot(True)
            self.toast_timer.timeout.connect(self.hide_toast)
        
        self.toast_timer.start(duration)
        
        logger.debug(f"Toast mostrado: {message}")
    
    def hide_toast(self) -> None:
        """Oculta la notificación toast."""
        if hasattr(self.ui, 'toast_widget'):
            self.ui.toast_widget.setVisible(False)
    
    def show_error_dialog(self, title: str, message: str) -> None:
        """
        Muestra un diálogo de error.
        
        Args:
            title: Título del diálogo
            message: Mensaje de error
        """
        QMessageBox.critical(self.ui, title, message)
        logger.error(f"Error mostrado: {title} - {message}")
    
    def show_success_dialog(self, title: str, message: str) -> None:
        """
        Muestra un diálogo de éxito.
        
        Args:
            title: Título del diálogo
            message: Mensaje de éxito
        """
        QMessageBox.information(self.ui, title, message)
        logger.info(f"Éxito mostrado: {title} - {message}")
    
    def show_confirmation_dialog(
        self,
        title: str,
        message: str
    ) -> bool:
        """
        Muestra un diálogo de confirmación.
        
        Args:
            title: Título del diálogo
            message: Mensaje de confirmación
            
        Returns:
            True si el usuario confirma, False en caso contrario
        """
        reply = QMessageBox.question(
            self.ui,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        confirmed = reply == QMessageBox.Yes
        logger.debug(f"Confirmación: {title} - {'Aceptado' if confirmed else 'Cancelado'}")
        
        return confirmed
    
    def populate_filter_combos(self) -> None:
        """Puebla los combos de filtro con datos del historial."""
        # Obtener listas únicas
        companies = self.controller.get_companies_list()
        customers = self.controller.get_customers_list()
        
        # Actualizar combo de empresas
        if hasattr(self.ui, 'combo_filter_company'):
            current_company = self.ui.combo_filter_company.currentText()
            self.ui.combo_filter_company.clear()
            self.ui.combo_filter_company.addItem("Todas")
            self.ui.combo_filter_company.addItems(companies)
            
            # Restaurar selección si existe
            index = self.ui.combo_filter_company.findText(current_company)
            if index >= 0:
                self.ui.combo_filter_company.setCurrentIndex(index)
        
        # Actualizar combo de clientes
        if hasattr(self.ui, 'combo_filter_customer'):
            current_customer = self.ui.combo_filter_customer.currentText()
            self.ui.combo_filter_customer.clear()
            self.ui.combo_filter_customer.addItem("Todos")
            self.ui.combo_filter_customer.addItems(customers)
            
            # Restaurar selección si existe
            index = self.ui.combo_filter_customer.findText(current_customer)
            if index >= 0:
                self.ui.combo_filter_customer.setCurrentIndex(index)
        
        logger.debug("Combos de filtro poblados")
    
    def apply_font_size(self, size_text: str) -> None:
        """
        Aplica un tamaño de fuente global.
        
        Args:
            size_text: Texto del tamaño (ej: "Mediano")
        """
        size_map = {
            "Pequeño": 10,
            "Mediano": 12,
            "Grande": 14,
            "Muy Grande": 16
        }
        
        size = size_map.get(size_text, 12)
        
        # Aplicar tamaño de fuente
        if hasattr(self.ui, 'setStyleSheet'):
            # Aquí iría la lógica para actualizar el stylesheet
            pass
        
        logger.info(f"Tamaño de fuente cambiado a: {size_text} ({size}pt)")
    
    def apply_spacing(self, spacing_text: str) -> None:
        """
        Aplica un espaciado global.
        
        Args:
            spacing_text: Texto del espaciado (ej: "Normal")
        """
        spacing_map = {
            "Compacto": 4,
            "Normal": 8,
            "Amplio": 12,
            "Muy Amplio": 16
        }
        
        spacing = spacing_map.get(spacing_text, 8)
        
        # Aplicar espaciado
        if hasattr(self.ui, 'setStyleSheet'):
            # Aquí iría la lógica para actualizar el stylesheet
            pass
        
        logger.info(f"Espaciado cambiado a: {spacing_text} ({spacing}px)")


__all__ = ["MainWindowLogic"]
