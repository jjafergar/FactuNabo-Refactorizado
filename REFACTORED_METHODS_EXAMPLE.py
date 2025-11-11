"""
Ejemplos de métodos refactorizados para MainWindow.
Este archivo muestra cómo quedarían los métodos después de la refactorización completa.
NO es código ejecutable, es solo referencia.
"""

# ============================================================================
# EJEMPLO 1: Método de lógica de negocio refactorizado
# ============================================================================

def load_history_data_BEFORE(self):
    """Versión ANTES: Lógica de negocio mezclada con UI."""
    query = """
        SELECT id, num_factura, empresa, cliente, estado, fecha_envio, 
               importe, pdf_url, pdf_local_path, excel_path, detalles
        FROM envios
        ORDER BY fecha_envio DESC
    """
    
    rows = fetch_all(query)
    
    self.table_history.setRowCount(0)
    for row in rows:
        row_position = self.table_history.rowCount()
        self.table_history.insertRow(row_position)
        
        # Poblar celdas...
        self.table_history.setItem(row_position, 0, QTableWidgetItem(row[1]))
        # ... más código de UI


def load_history_data_AFTER(self):
    """Versión DESPUÉS: Delegado al controlador."""
    # Obtener datos del controlador
    entries = self.controller.load_history()
    
    # Actualizar UI
    self._populate_history_table(entries)


def _populate_history_table(self, entries):
    """Método auxiliar para poblar la tabla (UI pura)."""
    self.table_history.setRowCount(0)
    
    for entry in entries:
        row_position = self.table_history.rowCount()
        self.table_history.insertRow(row_position)
        
        self.table_history.setItem(row_position, 0, QTableWidgetItem(entry.invoice_id))
        self.table_history.setItem(row_position, 1, QTableWidgetItem(entry.company))
        self.table_history.setItem(row_position, 2, QTableWidgetItem(entry.customer))
        # ... más columnas


# ============================================================================
# EJEMPLO 2: Método de UI refactorizado
# ============================================================================

def show_toast_BEFORE(self, message: str, duration: int = 3000):
    """Versión ANTES: Lógica de UI directa."""
    self.toast.setText(message)
    self.toast.setProperty("class", "toast-info")
    self.toast.adjustSize()
    
    width = self.toast.width() + 40
    self.toast.setFixedWidth(width)
    
    start_y = self.height()
    end_y = self.height() - self.toast.height() - 20
    start_x = (self.width() - width) // 2
    
    start_rect = QRect(start_x, start_y, width, self.toast.height())
    end_rect = QRect(start_x, end_y, width, self.toast.height())
    
    self.toast.setGeometry(start_rect)
    self.toast.show()
    
    self.toast_anim.stop()
    self.toast_anim.setDuration(400)
    self.toast_anim.setStartValue(start_rect)
    self.toast_anim.setEndValue(end_rect)
    self.toast_anim.start()
    
    self.toast_timer.stop()
    self.toast_timer.start(duration)


def show_toast_AFTER(self, message: str, duration: int = 3000, color_class: str = "info"):
    """Versión DESPUÉS: Delegado a UI logic."""
    # Delegar toda la lógica de animación
    self.ui_logic.show_toast(message, duration, color_class)


# ============================================================================
# EJEMPLO 3: Método mixto refactorizado
# ============================================================================

def apply_history_filters_BEFORE(self):
    """Versión ANTES: Mezcla de lógica de negocio y UI."""
    # Construir query
    query = "SELECT * FROM envios WHERE 1=1"
    params = []
    
    # Obtener valores de los combos
    company = self.combo_filter_company.currentText()
    if company and company != "Todas":
        query += " AND empresa = ?"
        params.append(company)
    
    customer = self.combo_filter_customer.currentText()
    if customer and customer != "Todos":
        query += " AND cliente = ?"
        params.append(customer)
    
    status = self.combo_filter_status.currentText()
    if status and status != "Todos":
        query += " AND estado = ?"
        params.append(status)
    
    query += " ORDER BY fecha_envio DESC"
    
    # Ejecutar query
    rows = fetch_all(query, params)
    
    # Actualizar tabla
    self.table_history.setRowCount(0)
    for row in rows:
        # Poblar tabla...
        pass
    
    # Actualizar estadísticas
    self.label_total_filtered.setText(f"{len(rows)} facturas")


def apply_history_filters_AFTER(self):
    """Versión DESPUÉS: Separación clara de responsabilidades."""
    # 1. Construir filtros (UI logic)
    filters = self.ui_logic.build_history_filters_from_ui()
    
    # 2. Obtener datos (Controller)
    entries = self.controller.load_history(filters)
    
    # 3. Actualizar UI (UI logic)
    self.ui_logic.update_history_table(entries)
    self.ui_logic.update_filter_stats(len(entries))


# ============================================================================
# EJEMPLO 4: Validación de Excel refactorizada
# ============================================================================

def select_excel_BEFORE(self, path=None):
    """Versión ANTES: Todo mezclado."""
    if not path:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel", "", "Excel (*.xlsx *.xls)"
        )
    
    if not path:
        return
    
    try:
        # Leer Excel
        df_factura = pd.read_excel(path, sheet_name="Facturas")
        df_conceptos = pd.read_excel(path, sheet_name="Conceptos")
        
        # Validar columnas
        required_cols = ["NumFactura", "empresa_emisora", "cliente_nombre"]
        missing_cols = [col for col in required_cols if col not in df_factura.columns]
        
        if missing_cols:
            QMessageBox.critical(
                self,
                "Error de Validación",
                f"Faltan columnas requeridas: {', '.join(missing_cols)}"
            )
            return
        
        # Validar que haya datos
        if len(df_factura) == 0:
            QMessageBox.warning(self, "Advertencia", "El archivo no contiene facturas")
            return
        
        # Validar conceptos
        for idx, row in df_factura.iterrows():
            invoice_id = str(row["NumFactura"])
            conceptos = df_conceptos[df_conceptos["NumFactura"] == invoice_id]
            
            if len(conceptos) == 0:
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    f"La factura {invoice_id} no tiene conceptos asociados"
                )
                return
        
        # Guardar estado
        self.current_excel_path = path
        self.df_factura = df_factura
        self.df_conceptos = df_conceptos
        
        # Actualizar UI
        self.label_file_name.setText(os.path.basename(path))
        self.btn_send.setEnabled(True)
        self.show_toast(f"✅ Cargadas {len(df_factura)} facturas")
        
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Error leyendo Excel: {e}")


def select_excel_AFTER(self, path=None):
    """Versión DESPUÉS: Separación de responsabilidades."""
    # 1. Diálogo de selección (UI)
    if not path:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel", "", "Excel (*.xlsx *.xls)"
        )
    
    if not path:
        return
    
    try:
        # 2. Leer Excel (esto podría ir a un servicio también)
        df_factura = pd.read_excel(path, sheet_name="Facturas")
        df_conceptos = pd.read_excel(path, sheet_name="Conceptos")
        
        # 3. Validar usando el controlador
        is_valid, errors = self.controller.validate_excel_file(
            path, df_factura, df_conceptos
        )
        
        if not is_valid:
            # Mostrar errores usando UI logic
            self.ui_logic.show_validation_errors(errors)
            return
        
        # 4. Guardar estado (esto también podría ir al controlador)
        self.current_excel_path = path
        self.df_factura = df_factura
        self.df_conceptos = df_conceptos
        
        # 5. Actualizar UI usando UI logic
        self.ui_logic.update_file_selection(path, len(df_factura))
        self.ui_logic.show_toast(
            f"✅ Cargadas {len(df_factura)} facturas",
            color_class="success"
        )
        self.btn_send.setEnabled(True)
        
    except Exception as e:
        self.ui_logic.show_error_dialog("Error", f"Error leyendo Excel: {e}")


# ============================================================================
# EJEMPLO 5: Estadísticas del dashboard refactorizadas
# ============================================================================

def update_dashboard_stats_BEFORE(self):
    """Versión ANTES: Query SQL directa en la UI."""
    # Obtener filtros
    company = self.dash_combo_empresas.currentText()
    period = self.dash_combo_periodo.currentText()
    
    # Construir query
    query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN estado = 'ÉXITO' THEN 1 ELSE 0 END) as success,
            SUM(importe) as total_amount
        FROM envios
        WHERE 1=1
    """
    params = []
    
    if company and company != "Todas":
        query += " AND empresa = ?"
        params.append(company)
    
    if "30 días" in period:
        from datetime import datetime, timedelta
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        query += " AND fecha_envio >= ?"
        params.append(date_from)
    
    # Ejecutar query
    row = fetch_one(query, params)
    
    # Actualizar labels
    self.label_total_invoices.setText(str(row[0] or 0))
    self.label_success_invoices.setText(str(row[1] or 0))
    
    success_rate = (row[1] / row[0] * 100) if row[0] > 0 else 0
    self.label_success_rate.setText(f"{success_rate:.1f}%")
    
    amount = row[2] or 0
    self.label_total_amount.setText(f"{amount:,.2f}€".replace(",", "X").replace(".", ",").replace("X", "."))


def update_dashboard_stats_AFTER(self):
    """Versión DESPUÉS: Delegado al controlador."""
    # 1. Obtener filtros de la UI
    company = self.dash_combo_empresas.currentText()
    company = None if company == "Todas" else company
    
    period_text = self.dash_combo_periodo.currentText()
    period_days = 30 if "30 días" in period_text else None
    
    # 2. Obtener estadísticas del controlador
    stats = self.controller.get_history_stats(company, period_days)
    
    # 3. Actualizar UI usando UI logic
    self.ui_logic.update_dashboard_stats_display(stats)


# ============================================================================
# RESUMEN DE BENEFICIOS
# ============================================================================

"""
BENEFICIOS DE LA REFACTORIZACIÓN:

1. TESTABILIDAD
   - La lógica de negocio puede ser testeada sin UI
   - Los tests son más rápidos y confiables
   - No se necesita QApplication para testear lógica

2. MANTENIBILIDAD
   - Cambios en la lógica no afectan la UI
   - Cambios en la UI no afectan la lógica
   - Más fácil de entender y modificar

3. REUTILIZACIÓN
   - Los controladores pueden ser usados desde CLI
   - Los controladores pueden ser usados desde otras ventanas
   - La lógica de negocio es independiente de Qt

4. CLARIDAD
   - Cada clase tiene una responsabilidad única
   - El código es más legible
   - Más fácil para nuevos desarrolladores

5. ESCALABILIDAD
   - Más fácil añadir nuevas funcionalidades
   - Más fácil refactorizar partes específicas
   - Mejor preparado para crecimiento futuro
"""
