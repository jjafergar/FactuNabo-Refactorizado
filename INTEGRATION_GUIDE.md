# Guía de Integración de Controladores

Esta guía documenta cómo integrar los nuevos controladores (`MainController` y `MainWindowLogic`) en la clase `MainWindow` de `main.py`.

## Estado Actual

✅ **Completado:**
- Controladores inicializados en `__init__`
- `MainController` disponible como `self.controller`
- `MainWindowLogic` disponible como `self.ui_logic`
- Método `save_summary_to_history` refactorizado como ejemplo

## Patrón de Refactorización

### 1. Métodos de Lógica de Negocio → MainController

**Antes:**
```python
def load_history(self):
    """Carga el historial desde la base de datos."""
    query = "SELECT * FROM envios ORDER BY fecha_envio DESC"
    rows = fetch_all(query)
    
    for row in rows:
        # Procesar y mostrar en la tabla
        ...
```

**Después:**
```python
def load_history(self):
    """Carga el historial desde la base de datos."""
    # Delegar al controlador
    entries = self.controller.load_history()
    
    # Actualizar la UI
    self._populate_history_table(entries)
```

### 2. Métodos de UI → MainWindowLogic

**Antes:**
```python
def show_toast(self, message: str):
    """Muestra una notificación toast."""
    self.toast.setText(message)
    self.toast.show()
    self.toast_timer.start(3000)
```

**Después:**
```python
def show_toast(self, message: str, duration: int = 3000):
    """Muestra una notificación toast."""
    # Delegar a la lógica de UI
    self.ui_logic.show_toast(message, duration)
```

### 3. Métodos Mixtos → Separar Responsabilidades

**Antes:**
```python
def apply_filters(self):
    """Aplica filtros y recarga el historial."""
    # Construir query SQL
    query = "SELECT * FROM envios WHERE 1=1"
    params = []
    
    if self.combo_company.currentText() != "Todas":
        query += " AND empresa = ?"
        params.append(self.combo_company.currentText())
    
    # Ejecutar query
    rows = fetch_all(query, params)
    
    # Actualizar tabla
    self.table_history.setRowCount(0)
    for row in rows:
        # Poblar tabla...
```

**Después:**
```python
def apply_filters(self):
    """Aplica filtros y recarga el historial."""
    # Delegar construcción de filtros a UI logic
    filters = self.ui_logic.build_history_filters()
    
    # Delegar query al controlador
    entries = self.controller.load_history(filters)
    
    # Delegar actualización de tabla a UI logic
    self.ui_logic.update_history_table(entries)
```

## Métodos Prioritarios para Refactorizar

### Alta Prioridad (Lógica de Negocio Crítica)

1. **`select_excel()`** - Validación de archivos Excel
   ```python
   # Usar: self.controller.validate_excel_file(path, df_factura, df_conceptos)
   ```

2. **`load_history_data()`** - Carga de historial
   ```python
   # Usar: self.controller.load_history(filters)
   ```

3. **`calculate_invoice_totals()`** - Cálculo de totales
   ```python
   # Usar: self.controller.get_invoice_totals(invoice_id)
   ```

4. **`update_dashboard_stats()`** - Estadísticas del dashboard
   ```python
   # Usar: self.controller.get_history_stats(company, period_days)
   ```

### Media Prioridad (Gestión de Estado)

5. **`clear_history()`** - Limpieza de historial
   ```python
   # Usar: self.controller.clear_history()
   ```

6. **`populate_filter_combos()`** - Poblar combos de filtro
   ```python
   # Usar: self.controller.get_companies_list()
   # Usar: self.controller.get_customers_list()
   ```

### Baja Prioridad (UI Pura)

7. **`toggle_theme()`** - Cambio de tema
   ```python
   # Usar: self.ui_logic.toggle_theme(checked)
   ```

8. **`apply_font_size()`** - Cambio de tamaño de fuente
   ```python
   # Usar: self.ui_logic.apply_font_size(size_text)
   ```

9. **`show_error()`** / **`show_success()`** - Diálogos
   ```python
   # Usar: self.ui_logic.show_error_dialog(title, message)
   # Usar: self.ui_logic.show_success_dialog(title, message)
   ```

## Ejemplo Completo: Refactorización de `select_excel()`

### Antes (Código Original)

```python
def select_excel(self, path=None):
    """Selecciona y valida un archivo Excel."""
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
        
        # Validar columnas requeridas
        required_cols = ["NumFactura", "empresa_emisora", "cliente_nombre"]
        for col in required_cols:
            if col not in df_factura.columns:
                self.show_error(f"Falta la columna: {col}")
                return
        
        # Guardar estado
        self.current_excel_path = path
        self.df_factura = df_factura
        self.df_conceptos = df_conceptos
        
        # Actualizar UI
        self.show_toast(f"✅ Cargadas {len(df_factura)} facturas")
        self.btn_send.setEnabled(True)
        
    except Exception as e:
        self.show_error(f"Error leyendo Excel: {e}")
```

### Después (Con Controladores)

```python
def select_excel(self, path=None):
    """Selecciona y valida un archivo Excel."""
    if not path:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel", "", "Excel (*.xlsx *.xls)"
        )
    
    if not path:
        return
    
    try:
        # Leer Excel (esto puede quedarse aquí o moverse a un servicio)
        df_factura = pd.read_excel(path, sheet_name="Facturas")
        df_conceptos = pd.read_excel(path, sheet_name="Conceptos")
        
        # Delegar validación al controlador
        is_valid, errors = self.controller.validate_excel_file(
            path, df_factura, df_conceptos
        )
        
        if not is_valid:
            # Mostrar errores usando UI logic
            error_msg = "\n".join([f"- {e.error_message}" for e in errors[:5]])
            self.ui_logic.show_error_dialog(
                "Errores de Validación",
                f"Se encontraron {len(errors)} errores:\n\n{error_msg}"
            )
            return
        
        # Guardar estado (esto eventualmente también irá al controlador)
        self.current_excel_path = path
        self.df_factura = df_factura
        self.df_conceptos = df_conceptos
        
        # Actualizar UI usando UI logic
        self.ui_logic.show_toast(
            f"✅ Cargadas {len(df_factura)} facturas",
            color_class="success"
        )
        self.btn_send.setEnabled(True)
        
    except Exception as e:
        self.ui_logic.show_error_dialog("Error", f"Error leyendo Excel: {e}")
```

## Beneficios de la Refactorización

1. **Testabilidad:** La lógica de negocio en `MainController` puede ser testeada sin UI
2. **Mantenibilidad:** Cambios en la lógica no afectan la UI y viceversa
3. **Reutilización:** Los controladores pueden ser usados desde otras partes de la app
4. **Claridad:** Cada clase tiene una responsabilidad única y clara

## Próximos Pasos

1. Refactorizar los métodos de alta prioridad listados arriba
2. Mover más lógica de negocio a `MainController`
3. Mover más lógica de UI a `MainWindowLogic`
4. Reducir `MainWindow` a un simple orquestador
5. Añadir tests para cada método refactorizado

## Notas Importantes

- **No es necesario refactorizar todo de una vez:** Hazlo incrementalmente
- **Mantén compatibilidad:** Puedes llamar al controlador Y mantener el código viejo temporalmente
- **Testea cada cambio:** Asegúrate de que la app sigue funcionando después de cada refactorización
- **Documenta los cambios:** Añade comentarios `# [REFACTORIZADO]` para rastrear el progreso
