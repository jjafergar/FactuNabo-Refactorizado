"""
rectificativa_dialog.py
Asistente gráfico para crear facturas rectificativas en FactuNabo
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QLineEdit, QTextEdit, QGroupBox, QRadioButton,
    QButtonGroup, QWidget, QStackedWidget, QMessageBox, QCompleter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Optional, Dict, List
import pandas as pd


class RectificativaDialog(QDialog):
    """
    Diálogo asistente para crear facturas rectificativas.
    
    Flujo:
    1. Seleccionar el motivo de rectificación (R1-R4)
    2. Seleccionar la factura original a rectificar
    3. Elegir modalidad (Sustitución o Diferencias)
    4. Confirmar y generar
    """
    
    factura_created = Signal(dict)  # Emite los datos de la factura rectificativa creada
    
    def __init__(self, parent=None, facturas_disponibles: Optional[pd.DataFrame] = None):
        super().__init__(parent)
        self.facturas_disponibles = facturas_disponibles if facturas_disponibles is not None else pd.DataFrame()
        self.factura_seleccionada = None
        self.datos_rectificativa = {}
        
        self.setWindowTitle("Crear Factura Rectificativa")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        self._init_ui()
        
    def _init_ui(self):
        """Inicializa la interfaz del asistente"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Asistente de Factura Rectificativa")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("Te guiaremos paso a paso para crear tu factura rectificativa")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Contenedor de pasos
        self.stacked_widget = QStackedWidget()
        
        # Paso 1: Selección del motivo
        self.page_motivo = self._create_page_motivo()
        self.stacked_widget.addWidget(self.page_motivo)
        
        # Paso 2: Selección de factura original
        self.page_factura = self._create_page_factura()
        self.stacked_widget.addWidget(self.page_factura)
        
        # Paso 3: Modalidad de rectificación
        self.page_modalidad = self._create_page_modalidad()
        self.stacked_widget.addWidget(self.page_modalidad)
        
        # Paso 4: Confirmación
        self.page_confirmacion = self._create_page_confirmacion()
        self.stacked_widget.addWidget(self.page_confirmacion)
        
        layout.addWidget(self.stacked_widget)
        
        # Botones de navegación
        btn_layout = QHBoxLayout()
        
        self.btn_anterior = QPushButton("⬅️ Anterior")
        self.btn_anterior.clicked.connect(self._go_previous)
        self.btn_anterior.setEnabled(False)
        
        self.btn_siguiente = QPushButton("Siguiente ➡️")
        self.btn_siguiente.clicked.connect(self._go_next)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_anterior)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_siguiente)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def _create_page_motivo(self) -> QWidget:
        """Crea la página de selección del motivo"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Título del paso
        step_label = QLabel("Paso 1 de 4: ¿Qué necesitas corregir?")
        step_font = QFont()
        step_font.setPointSize(12)
        step_font.setBold(True)
        step_label.setFont(step_font)
        layout.addWidget(step_label)
        
        layout.addSpacing(20)
        
        # Descripción
        desc = QLabel("Selecciona el motivo de la rectificación:")
        layout.addWidget(desc)
        
        # ComboBox con los motivos
        self.combo_motivo = QComboBox()
        self.combo_motivo.addItem("", "")  # Opción vacía
        self.combo_motivo.addItem(
            "🔄 Error en IVA, descuentos o devoluciones (R1)",
            "R1"
        )
        self.combo_motivo.addItem(
            "⚖️ Cliente en concurso de acreedores (R2)",
            "R2"
        )
        self.combo_motivo.addItem(
            "💸 Crédito incobrable (R3)",
            "R3"
        )
        self.combo_motivo.addItem(
            "📝 Error en datos del cliente o descripción (R4)",
            "R4"
        )
        self.combo_motivo.currentIndexChanged.connect(self._on_motivo_changed)
        layout.addWidget(self.combo_motivo)
        
        layout.addSpacing(20)
        
        # Área de explicación
        self.text_explicacion = QTextEdit()
        self.text_explicacion.setReadOnly(True)
        self.text_explicacion.setMaximumHeight(200)
        self.text_explicacion.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; padding: 10px;")
        layout.addWidget(self.text_explicacion)
        
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def _create_page_factura(self) -> QWidget:
        """Crea la página de selección de factura original"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Título del paso
        step_label = QLabel("Paso 2 de 4: ¿Qué factura quieres rectificar?")
        step_font = QFont()
        step_font.setPointSize(12)
        step_font.setBold(True)
        step_label.setFont(step_font)
        layout.addWidget(step_label)
        
        layout.addSpacing(20)
        
        # Selector de factura
        label = QLabel("Número de factura original:")
        layout.addWidget(label)
        
        self.combo_factura = QComboBox()
        self.combo_factura.setEditable(True)
        self.combo_factura.setInsertPolicy(QComboBox.NoInsert)
        
        # Poblar con facturas disponibles
        if not self.facturas_disponibles.empty:
            facturas_list = []
            for _, row in self.facturas_disponibles.iterrows():
                num_factura = str(row.get("NumFactura", ""))
                cliente = str(row.get("cliente_nombre", ""))
                fecha = str(row.get("fecha_emision", ""))
                facturas_list.append(f"{num_factura} - {cliente} ({fecha})")
            
            self.combo_factura.addItems(facturas_list)
            
            # Añadir autocompletado
            completer = QCompleter(facturas_list)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.combo_factura.setCompleter(completer)
        
        self.combo_factura.currentIndexChanged.connect(self._on_factura_changed)
        layout.addWidget(self.combo_factura)
        
        layout.addSpacing(20)
        
        # Información de la factura seleccionada
        info_group = QGroupBox("Información de la factura")
        info_layout = QVBoxLayout()
        
        self.label_factura_info = QLabel("Selecciona una factura para ver sus detalles")
        self.label_factura_info.setWordWrap(True)
        self.label_factura_info.setStyleSheet("padding: 10px;")
        info_layout.addWidget(self.label_factura_info)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def _create_page_modalidad(self) -> QWidget:
        """Crea la página de selección de modalidad"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Título del paso
        step_label = QLabel("Paso 3 de 4: ¿Cómo quieres rectificar?")
        step_font = QFont()
        step_font.setPointSize(12)
        step_font.setBold(True)
        step_label.setFont(step_font)
        layout.addWidget(step_label)
        
        layout.addSpacing(20)
        
        # Descripción
        desc = QLabel("Elige la modalidad de rectificación:")
        layout.addWidget(desc)
        
        # Grupo de botones de radio
        self.button_group_modalidad = QButtonGroup()
        
        # Opción 1: Por Sustitución
        self.radio_sustitucion = QRadioButton()
        self.button_group_modalidad.addButton(self.radio_sustitucion, 0)
        
        sustitucion_layout = QVBoxLayout()
        sustitucion_title = QLabel("🔄 Por Sustitución (S)")
        sustitucion_title_font = QFont()
        sustitucion_title_font.setBold(True)
        sustitucion_title.setFont(sustitucion_title_font)
        sustitucion_desc = QLabel(
            "Anula completamente la factura original y la reemplaza por una nueva.\n"
            "• Usa esta opción cuando hay múltiples errores\n"
            "• La factura original queda completamente anulada\n"
            "• Ideal para errores en datos del cliente o cambios sustanciales"
        )
        sustitucion_desc.setWordWrap(True)
        sustitucion_desc.setStyleSheet("color: #666; margin-left: 20px;")
        
        sustitucion_container = QWidget()
        sustitucion_container_layout = QHBoxLayout()
        sustitucion_container_layout.addWidget(self.radio_sustitucion)
        sustitucion_container_layout.addLayout(sustitucion_layout)
        sustitucion_container_layout.addStretch()
        sustitucion_container.setLayout(sustitucion_container_layout)
        
        sustitucion_layout.addWidget(sustitucion_title)
        sustitucion_layout.addWidget(sustitucion_desc)
        
        layout.addWidget(sustitucion_container)
        layout.addSpacing(15)
        
        # Opción 2: Por Diferencias
        self.radio_diferencias = QRadioButton()
        self.button_group_modalidad.addButton(self.radio_diferencias, 1)
        
        diferencias_layout = QVBoxLayout()
        diferencias_title = QLabel("📊 Por Diferencias (I)")
        diferencias_title_font = QFont()
        diferencias_title_font.setBold(True)
        diferencias_title.setFont(diferencias_title_font)
        diferencias_desc = QLabel(
            "Solo ajusta las diferencias (positivas o negativas) sobre la factura original.\n"
            "• La factura original sigue siendo válida\n"
            "• Solo se corrige el importe específico\n"
            "• Ideal para abonos, devoluciones o ajustes de precio"
        )
        diferencias_desc.setWordWrap(True)
        diferencias_desc.setStyleSheet("color: #666; margin-left: 20px;")
        
        diferencias_container = QWidget()
        diferencias_container_layout = QHBoxLayout()
        diferencias_container_layout.addWidget(self.radio_diferencias)
        diferencias_container_layout.addLayout(diferencias_layout)
        diferencias_container_layout.addStretch()
        diferencias_container.setLayout(diferencias_container_layout)
        
        diferencias_layout.addWidget(diferencias_title)
        diferencias_layout.addWidget(diferencias_desc)
        
        layout.addWidget(diferencias_container)
        
        # Seleccionar "Por Diferencias" por defecto
        self.radio_diferencias.setChecked(True)
        
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def _create_page_confirmacion(self) -> QWidget:
        """Crea la página de confirmación"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Título del paso
        step_label = QLabel("Paso 4 de 4: Confirmación")
        step_font = QFont()
        step_font.setPointSize(12)
        step_font.setBold(True)
        step_label.setFont(step_font)
        layout.addWidget(step_label)
        
        layout.addSpacing(20)
        
        # Resumen
        desc = QLabel("Revisa los datos de tu factura rectificativa:")
        layout.addWidget(desc)
        
        # Área de resumen
        self.text_resumen = QTextEdit()
        self.text_resumen.setReadOnly(True)
        self.text_resumen.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px;")
        layout.addWidget(self.text_resumen)
        
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def _on_motivo_changed(self, index: int):
        """Maneja el cambio de motivo"""
        motivo = self.combo_motivo.currentData()
        
        explicaciones = {
            "R1": """<h3>Error en IVA, descuentos o devoluciones (R1)</h3>
<p><b>Cuándo usar:</b></p>
<ul>
<li>Has aplicado un tipo de IVA incorrecto</li>
<li>Necesitas aplicar un descuento posterior a la emisión</li>
<li>El cliente devuelve mercancía (factura de abono)</li>
<li>Error fundado en derecho</li>
</ul>
<p><b>Base legal:</b> Art. 80.1, 80.2 y 80.6 de la Ley del IVA</p>""",
            
            "R2": """<h3>Cliente en concurso de acreedores (R2)</h3>
<p><b>Cuándo usar:</b></p>
<ul>
<li>El cliente ha entrado en concurso de acreedores</li>
<li>No puede pagar la factura por esta causa</li>
</ul>
<p><b>Base legal:</b> Art. 80.3 de la Ley del IVA</p>""",
            
            "R3": """<h3>Crédito incobrable (R3)</h3>
<p><b>Cuándo usar:</b></p>
<ul>
<li>Has agotado las vías de reclamación</li>
<li>El crédito se declara total o parcialmente incobrable</li>
</ul>
<p><b>Base legal:</b> Art. 80.4 de la Ley del IVA</p>""",
            
            "R4": """<h3>Error en datos o descripción (R4)</h3>
<p><b>Cuándo usar:</b></p>
<ul>
<li>Error en el NIF, nombre o dirección del cliente</li>
<li>Error en la descripción del producto/servicio</li>
<li>Error en la fecha o número de factura</li>
<li>Cualquier otro error no incluido en R1, R2 o R3</li>
</ul>
<p><b>Base legal:</b> Resto de causas de rectificación</p>"""
        }
        
        if motivo in explicaciones:
            self.text_explicacion.setHtml(explicaciones[motivo])
        else:
            self.text_explicacion.clear()
    
    def _on_factura_changed(self, index: int):
        """Maneja el cambio de factura seleccionada"""
        if index < 0 or self.facturas_disponibles.empty:
            return
        
        # Obtener la factura seleccionada
        self.factura_seleccionada = self.facturas_disponibles.iloc[index]
        
        # Mostrar información
        num_factura = self.factura_seleccionada.get("NumFactura", "")
        cliente = self.factura_seleccionada.get("cliente_nombre", "")
        fecha = self.factura_seleccionada.get("fecha_emision", "")
        total = self.factura_seleccionada.get("total_ah", 0)
        
        info_html = f"""
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 5px;"><b>Número:</b></td><td style="padding: 5px;">{num_factura}</td></tr>
<tr><td style="padding: 5px;"><b>Cliente:</b></td><td style="padding: 5px;">{cliente}</td></tr>
<tr><td style="padding: 5px;"><b>Fecha:</b></td><td style="padding: 5px;">{fecha}</td></tr>
<tr><td style="padding: 5px;"><b>Total:</b></td><td style="padding: 5px;">{total} €</td></tr>
</table>
"""
        self.label_factura_info.setText(info_html)
    
    def _go_previous(self):
        """Va al paso anterior"""
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)
            self._update_buttons()
    
    def _go_next(self):
        """Va al siguiente paso o finaliza"""
        current_index = self.stacked_widget.currentIndex()
        
        # Validar el paso actual antes de avanzar
        if not self._validate_current_step():
            return
        
        if current_index < self.stacked_widget.count() - 1:
            # Si estamos en el penúltimo paso, generar el resumen
            if current_index == self.stacked_widget.count() - 2:
                self._generate_resumen()
            
            self.stacked_widget.setCurrentIndex(current_index + 1)
            self._update_buttons()
        else:
            # Último paso: crear la factura rectificativa
            self._create_rectificativa()
    
    def _validate_current_step(self) -> bool:
        """Valida el paso actual"""
        current_index = self.stacked_widget.currentIndex()
        
        if current_index == 0:  # Paso 1: Motivo
            if not self.combo_motivo.currentData():
                QMessageBox.warning(self, "Validación", "Por favor, selecciona un motivo de rectificación.")
                return False
        
        elif current_index == 1:  # Paso 2: Factura
            if self.factura_seleccionada is None:
                QMessageBox.warning(self, "Validación", "Por favor, selecciona la factura que quieres rectificar.")
                return False
        
        elif current_index == 2:  # Paso 3: Modalidad
            if not self.button_group_modalidad.checkedButton():
                QMessageBox.warning(self, "Validación", "Por favor, selecciona una modalidad de rectificación.")
                return False
        
        return True
    
    def _update_buttons(self):
        """Actualiza el estado de los botones"""
        current_index = self.stacked_widget.currentIndex()
        
        # Botón Anterior
        self.btn_anterior.setEnabled(current_index > 0)
        
        # Botón Siguiente/Crear
        if current_index == self.stacked_widget.count() - 1:
            self.btn_siguiente.setText("✅ Crear Rectificativa")
        else:
            self.btn_siguiente.setText("Siguiente ➡️")
    
    def _generate_resumen(self):
        """Genera el resumen para la confirmación"""
        motivo_text = self.combo_motivo.currentText()
        motivo_code = self.combo_motivo.currentData()
        
        num_factura = self.factura_seleccionada.get("NumFactura", "")
        cliente = self.factura_seleccionada.get("cliente_nombre", "")
        
        modalidad_id = self.button_group_modalidad.checkedId()
        modalidad_text = "Por Sustitución (S)" if modalidad_id == 0 else "Por Diferencias (I)"
        modalidad_code = "S" if modalidad_id == 0 else "I"
        
        resumen_html = f"""
<h2>Resumen de la Factura Rectificativa</h2>

<table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
<tr style="background-color: #f0f0f0;">
    <td style="padding: 10px; border: 1px solid #ddd;"><b>Motivo:</b></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{motivo_text}</td>
</tr>
<tr>
    <td style="padding: 10px; border: 1px solid #ddd;"><b>Código:</b></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{motivo_code}</td>
</tr>
<tr style="background-color: #f0f0f0;">
    <td style="padding: 10px; border: 1px solid #ddd;"><b>Factura Original:</b></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{num_factura}</td>
</tr>
<tr>
    <td style="padding: 10px; border: 1px solid #ddd;"><b>Cliente:</b></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{cliente}</td>
</tr>
<tr style="background-color: #f0f0f0;">
    <td style="padding: 10px; border: 1px solid #ddd;"><b>Modalidad:</b></td>
    <td style="padding: 10px; border: 1px solid #ddd;">{modalidad_text}</td>
</tr>
</table>

<div style="margin-top: 20px; padding: 15px; background-color: #e8f5e9; border-left: 4px solid #4caf50;">
<p><b>✅ Todo listo para crear la factura rectificativa</b></p>
<p>Al hacer clic en "Crear Rectificativa", se generará una nueva factura con los datos correctos.</p>
</div>
"""
        
        self.text_resumen.setHtml(resumen_html)
        
        # Guardar los datos para la creación
        self.datos_rectificativa = {
            "tipo_factura": motivo_code,
            "factura_rectificativa_numero": num_factura,
            "factura_rectificativa_tipo": modalidad_code,
            "factura_original": self.factura_seleccionada
        }
    
    def _create_rectificativa(self):
        """Crea la factura rectificativa y cierra el diálogo"""
        # Emitir señal con los datos
        self.factura_created.emit(self.datos_rectificativa)
        
        # Cerrar el diálogo
        self.accept()
