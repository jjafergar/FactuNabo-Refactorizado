"""
Widgets reutilizables de la interfaz.
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class AnimatedButton(QPushButton):
    """Botón con animación de elevación y sombra."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setProperty("class", "AnimatedButton")
        self.setStyleSheet("color: white !important;")

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(18)
        color = QColor(0, 0, 0, 60)
        self._shadow.setColor(color)
        self._shadow.setOffset(0, 4)
        self.setGraphicsEffect(self._shadow)

        self._anim_blur = QPropertyAnimation(self._shadow, b"blurRadius")
        self._anim_blur.setDuration(180)
        self._anim_blur.setEasingCurve(QEasingCurve.OutCubic)

        self._anim_offset = QPropertyAnimation(self._shadow, b"yOffset")
        self._anim_offset.setDuration(180)
        self._anim_offset.setEasingCurve(QEasingCurve.OutCubic)

    def _animate_hover_in(self):
        self._anim_blur.stop()
        self._anim_blur.setStartValue(self._shadow.blurRadius())
        self._anim_blur.setEndValue(30)
        self._anim_blur.start()

        self._anim_offset.stop()
        self._anim_offset.setStartValue(self._shadow.yOffset())
        self._anim_offset.setEndValue(6)
        self._anim_offset.start()

    def _animate_hover_out(self):
        self._anim_blur.stop()
        self._anim_blur.setStartValue(self._shadow.blurRadius())
        self._anim_blur.setEndValue(18)
        self._anim_blur.start()

        self._anim_offset.stop()
        self._anim_offset.setStartValue(self._shadow.yOffset())
        self._anim_offset.setEndValue(4)
        self._anim_offset.start()

    def enterEvent(self, e):
        self._animate_hover_in()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate_hover_out()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._anim_blur.stop()
        self._anim_blur.setStartValue(self._shadow.blurRadius())
        self._anim_blur.setEndValue(10)
        self._anim_blur.start()

        self._anim_offset.stop()
        self._anim_offset.setStartValue(self._shadow.yOffset())
        self._anim_offset.setEndValue(2)
        self._anim_offset.start()

        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        current_pos = e.position().toPoint()
        if self.rect().contains(current_pos):
            self._animate_hover_in()
        else:
            self._animate_hover_out()


class StatusChip(QLabel):
    def __init__(self, status, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setProperty("class", "StatusChip")
        up = (status or "").upper()
        if up in ["ÉXITO", "SUCCESS"]:
            self.setProperty("status", "success")
        elif up in ["DUPLICADO", "DUPLICATE", "ATENCION"]:
            self.setProperty("status", "warning")
        else:
            self.setProperty("status", "NABO!")
        self.setText(up)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(26)


class AnimatedNavList(QListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setProperty("class", "NavList")


class ModernTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setProperty("class", "ModernTable")
        self.setAlternatingRowColors(True)
        self.setMouseTracking(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)


class TableTools(QWidget):
    """
    Barra de herramientas para tablas: búsqueda y densidad.
    """

    def __init__(self, table: QTableWidget, parent=None):
        super().__init__(parent)
        self._table = table
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 8)
        row.setSpacing(8)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Buscar…")
        self.search.textChanged.connect(self._apply_filter)
        self.compact_toggle = QCheckBox("Vista compacta", self)
        self.compact_toggle.setToolTip(
            "Reduce el espaciado en tablas y controles para mostrar más información en menos espacio"
        )
        self.compact_toggle.toggled.connect(self._toggle_density)
        row.addWidget(self.search)
        row.addStretch()
        row.addWidget(self.compact_toggle)

    def _toggle_density(self, checked: bool):
        win = self.window()
        if isinstance(win, QMainWindow):
            win.setProperty("density", "compact" if checked else "")
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    try:
                        widget.style().unpolish(widget)
                        widget.style().polish(widget)
                    except (RuntimeError, AttributeError):
                        pass

    def _apply_filter(self, text: str):
        txt = (text or "").strip().lower()
        for r in range(self._table.rowCount()):
            visible = False
            for c in range(self._table.columnCount()):
                it = self._table.item(r, c)
                if it and txt in str(it.text()).lower():
                    visible = True
                    break
            self._table.setRowHidden(r, not visible)


class StepperWidget(QWidget):
    def __init__(self, steps, parent=None):
        super().__init__(parent)
        self.steps = steps
        self.current_step = 0
        self._init_ui()
        self.set_step(0)

    def _init_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(20, 10, 20, 10)
        self._layout.setSpacing(0)

        self.step_labels = []
        self.step_circles = []
        self.step_lines = []
        self.line_anims = []

        for idx, step_name in enumerate(self.steps):
            container = QVBoxLayout()
            container.setContentsMargins(0, 0, 0, 0)
            container.setSpacing(6)
            container.setAlignment(Qt.AlignCenter)

            circle = QLabel(str(idx + 1))
            circle.setAlignment(Qt.AlignCenter)
            circle.setFixedSize(40, 40)
            circle.setProperty("class", "StepCircle")
            circle.setProperty("state", "pending")
            container.addWidget(circle, alignment=Qt.AlignCenter)
            self.step_circles.append(circle)

            label = QLabel(step_name)
            label.setAlignment(Qt.AlignCenter)
            label.setProperty("class", "StepLabel")
            container.addWidget(label, alignment=Qt.AlignCenter)
            self.step_labels.append(label)

            self._layout.addLayout(container)

            if idx < len(self.steps) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFixedHeight(2)
                line.setMinimumWidth(60)
                line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                line.setProperty("class", "StepLine")
                line.setProperty("state", "pending")
                line.setMaximumWidth(0)
                self.step_lines.append(line)

                anim = QPropertyAnimation(line, b"maximumWidth")
                anim.setDuration(400)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                self.line_anims.append(anim)

                self._layout.addWidget(line, alignment=Qt.AlignVCenter)

    def set_current_step(self, step_index):
        self.set_step(step_index)

    def set_step(self, step_index):
        if not self.step_circles:
            return

        bounded_index = max(0, min(step_index, len(self.step_circles)))
        self.current_step = bounded_index

        for idx, circle in enumerate(self.step_circles):
            if idx < bounded_index:
                state = "completed"
                circle.setText("✓")
            elif idx == bounded_index:
                state = "active"
                circle.setText(str(idx + 1))
            else:
                state = "pending"
                circle.setText(str(idx + 1))

            circle.setProperty("state", state)
            circle.style().unpolish(circle)
            circle.style().polish(circle)

        for idx, line in enumerate(self.step_lines):
            state = "completed" if idx < bounded_index else "pending"
            line.setProperty("state", state)
            line.style().unpolish(line)
            line.style().polish(line)

            target_width = line.minimumWidth() if state == "completed" else 0
            current_width = line.maximumWidth()
            if current_width is None:
                current_width = line.width()

            anim = self.line_anims[idx]
            anim.stop()
            anim.setStartValue(current_width)
            anim.setEndValue(target_width)
            anim.start()


__all__ = [
    "AnimatedButton",
    "StatusChip",
    "AnimatedNavList",
    "ModernTable",
    "TableTools",
    "StepperWidget",
]

