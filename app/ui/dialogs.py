"""
Diálogos reutilizables (health check, visor JSON, progreso).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets import AnimatedButton


class HealthCheckDialog(QDialog):
    def __init__(self, results: Iterable[dict], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Diagnóstico del sistema")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)

        title = QLabel("Resultados de las comprobaciones")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setProperty("class", "ModernList")
        layout.addWidget(self.list_widget)

        for item in results:
            nombre = item.get("nombre", "Chequeo")
            estado = item.get("estado", "DESCONOCIDO")
            detalle = item.get("detalle", "")
            text = f"{nombre} – {estado}\n{detalle}"
            lw_item = QListWidgetItem(text)
            lw_item.setData(Qt.UserRole, item)
            if estado.upper() == "OK":
                lw_item.setForeground(Qt.darkGreen)
            elif estado.upper() == "ADVERTENCIA":
                lw_item.setForeground(Qt.darkYellow)
            else:
                lw_item.setForeground(Qt.red)
            self.list_widget.addItem(lw_item)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class JsonViewerDialog(QDialog):
    def __init__(self, json_path: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(json_path.name)
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(QLabel(f"Archivo: {json_path}"))
        header.addStretch()
        layout.addLayout(header)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.text_edit.setPlainText(formatted)
        except Exception as exc:
            self.text_edit.setPlainText(f"No se pudo cargar el JSON:\n{exc}")


class BackupSummaryDialog(QDialog):
    def __init__(self, backup_path: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Copia de seguridad")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)

        label = QLabel(f"Copia creada en:\n{backup_path}")
        label.setWordWrap(True)
        layout.addWidget(label)

        open_button = AnimatedButton("Abrir Carpeta")
        open_button.clicked.connect(lambda: self._open_parent(backup_path))
        layout.addWidget(open_button, alignment=Qt.AlignRight)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _open_parent(self, backup_path: Path):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(backup_path.parent)))

