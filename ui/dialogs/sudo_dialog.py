#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from utils.logger import get_logger


class SudoDialog(QDialog):
    """Diálogo de confirmación para comandos sudo"""

    # Señales
    approved = Signal(bool)  # True si se aprueba, False si se cancela

    def __init__(self, parent, command: str, tool_name: str = "kdesu"):
        super().__init__(parent)
        self.logger = get_logger("SudoDialog")
        self.command = command
        self.tool_name = tool_name

        self.setWindowTitle("🔐 Confirmación de Sudo")
        self.setFixedSize(500, 300)

        self._create_ui()

    def _create_ui(self):
        """Crea la interfaz del diálogo"""
        layout = QVBoxLayout(self)

        # Mensaje de advertencia
        warning_label = QLabel(
            f"¿Permitir que Arch-Chan ejecute este comando con elevación de privilegios?\n\n"
            f"<b>Comando:</b>\n<code>{self.command}</code>\n\n"
            f"Usando: <b>{self.tool_name}</b>\n\n"
            "⚠️ <i>Asegúrate de que confías en este comando antes de continuar.</i>"
        )
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        # Checkbox para recordar (opcional)
        self.remember_check = QCheckBox(
            "Recordar esta decisión para comandos similares"
        )
        layout.addWidget(self.remember_check)

        # Botones
        button_layout = QHBoxLayout()

        self.yes_button = QPushButton("✅ Ejecutar")
        self.yes_button.clicked.connect(self._on_approved)

        self.no_button = QPushButton("❌ Cancelar")
        self.no_button.clicked.connect(self._on_rejected)

        button_layout.addWidget(self.yes_button)
        button_layout.addWidget(self.no_button)

        layout.addLayout(button_layout)

    def _on_approved(self):
        """Maneja la aprobación del comando"""
        self.logger.info(f"Comando sudo aprobado: {self.command}")
        self.approved.emit(True)
        self.accept()

    def _on_rejected(self):
        """Maneja el rechazo del comando"""
        self.logger.info(f"Comando sudo rechazado: {self.command}")
        self.approved.emit(False)
        self.reject()

    def get_remember_decision(self) -> bool:
        """Retorna si se debe recordar la decisión"""
        return self.remember_check.isChecked()
