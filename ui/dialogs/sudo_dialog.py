#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Diálogo de confirmación sudo completamente reescrito
Con mejoras de seguridad y experiencia de usuario
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from utils.logger import get_logger


class SudoDialog(QDialog):
    """Diálogo de confirmación para comandos sudo con análisis de seguridad"""

    # Señales
    approved = Signal(bool)  # True si se aprueba, False si se cancela

    def __init__(self, parent, command: str, tool_name: str = "kdesu"):
        super().__init__(parent)
        self.logger = get_logger("SudoDialog")
        self.command = command
        self.tool_name = tool_name
        self.remember_decision = False

        self.setWindowTitle("🔐 Confirmación de Privilegios Elevados")
        self.setFixedSize(600, 450)
        self.setModal(True)

        self._create_ui()
        self._analyze_command()

        self.logger.info(f"SudoDialog creado para comando: {command}")

    def _create_ui(self):
        """Crea la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Título y advertencia
        title_label = QLabel("Confirmación de Ejecución con Sudo")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #F27835;")

        warning_label = QLabel(
            "Se requiere elevación de privilegios para ejecutar este comando:"
        )
        warning_label.setStyleSheet("color: #7C818C; font-size: 11px;")

        layout.addWidget(title_label)
        layout.addWidget(warning_label)
        layout.addSpacing(8)

        # Comando a ejecutar
        command_frame = QFrame()
        command_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2F343F; 
                border-radius: 8px;
                border: 1px solid #4B5162;
            }
        """
        )
        command_layout = QVBoxLayout(command_frame)
        command_layout.setContentsMargins(12, 8, 12, 8)

        command_label = QLabel("Comando a ejecutar:")
        command_label.setStyleSheet(
            "font-weight: bold; color: #D3DAE3; font-size: 11px;"
        )

        self.command_display = QTextEdit()
        self.command_display.setPlainText(self.command)
        self.command_display.setReadOnly(True)
        self.command_display.setStyleSheet(
            """
            QTextEdit {
                background-color: #383C4A;
                color: #D3DAE3;
                border: 1px solid #4B5162;
                border-radius: 6px;
                font-family: 'Hack', 'Fira Code', monospace;
                font-size: 10px;
                padding: 8px;
                selection-background-color: #1793D1;
            }
        """
        )
        self.command_display.setFixedHeight(80)

        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_display)
        layout.addWidget(command_frame)

        # Análisis de seguridad
        self.security_frame = QFrame()
        self.security_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2F343F; 
                border-radius: 8px;
                border: 1px solid #4B5162;
            }
        """
        )
        security_layout = QVBoxLayout(self.security_frame)
        security_layout.setContentsMargins(12, 8, 12, 8)

        security_label = QLabel("Análisis de Seguridad:")
        security_label.setStyleSheet(
            "font-weight: bold; color: #D3DAE3; font-size: 11px;"
        )

        self.security_analysis = QLabel()
        self.security_analysis.setWordWrap(True)
        self.security_analysis.setStyleSheet(
            "color: #7C818C; font-size: 10px; line-height: 1.4;"
        )

        security_layout.addWidget(security_label)
        security_layout.addWidget(self.security_analysis)
        layout.addWidget(self.security_frame)

        # Información de la herramienta
        tool_frame = QFrame()
        tool_frame.setStyleSheet(
            "background-color: #383C4A; border-radius: 6px; padding: 8px;"
        )
        tool_layout = QHBoxLayout(tool_frame)

        tool_info = QLabel(f"🔧 Herramienta: <b>{self.tool_name}</b>")
        tool_info.setStyleSheet("color: #7C818C; font-size: 10px;")

        tool_layout.addWidget(tool_info)
        tool_layout.addStretch()
        layout.addWidget(tool_frame)

        # Opciones de recordar
        self.remember_check = QCheckBox(
            "Recordar esta decisión para comandos similares (por 5 minutos)"
        )
        self.remember_check.setStyleSheet("color: #7C818C; font-size: 10px;")
        layout.addWidget(self.remember_check)

        # Botones
        button_layout = QHBoxLayout()

        self.yes_button = QPushButton("✅ Ejecutar Comando")
        self.yes_button.setStyleSheet(
            """
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2ECC71;
            }
            QPushButton:pressed {
                background-color: #219653;
            }
        """
        )
        self.yes_button.clicked.connect(self._on_approved)

        self.no_button = QPushButton("❌ Cancelar")
        self.no_button.setStyleSheet(
            """
            QPushButton {
                background-color: #E74C3C;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #EC7063;
            }
            QPushButton:pressed {
                background-color: #C0392B;
            }
        """
        )
        self.no_button.clicked.connect(self._on_rejected)

        # Botón de detalles avanzados
        self.details_button = QPushButton("🔍 Más Detalles")
        self.details_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5DADE2;
            }
        """
        )
        self.details_button.clicked.connect(self._show_advanced_details)

        button_layout.addWidget(self.details_button)
        button_layout.addStretch()
        button_layout.addWidget(self.no_button)
        button_layout.addWidget(self.yes_button)

        layout.addLayout(button_layout)

    def _analyze_command(self):
        """Analiza el comando para detectar posibles riesgos"""
        risk_level = "medio"
        warnings = []
        suggestions = []

        # Análisis básico de comandos peligrosos
        dangerous_patterns = {
            "rm -rf /": {
                "level": "CRÍTICO",
                "message": "Este comando puede borrar todo el sistema",
            },
            "dd if=": {
                "level": "ALTO",
                "message": "Comando de bajo nivel que puede dañar discos",
            },
            "mkfs": {
                "level": "ALTO",
                "message": "Comando de formateo de sistemas de archivos",
            },
            "chmod 777": {
                "level": "MEDIO",
                "message": "Permisos excesivamente abiertos",
            },
            "passwd": {
                "level": "MEDIO",
                "message": "Modificación de contraseñas del sistema",
            },
            "useradd": {
                "level": "MEDIO",
                "message": "Creación de usuarios del sistema",
            },
            "systemctl": {
                "level": "BAJO",
                "message": "Control de servicios del sistema",
            },
            "pacman -R": {
                "level": "ALTO",
                "message": "Eliminación de paquetes del sistema",
            },
            "pacman -S": {
                "level": "MEDIO",
                "message": "Instalación de paquetes del sistema",
            },
        }

        for pattern, info in dangerous_patterns.items():
            if pattern in self.command:
                warnings.append(f"{info['level']}: {info['message']}")

        # Sugerencias basadas en el comando
        if "apt" in self.command or "pacman" in self.command:
            suggestions.append("Este comando modifica paquetes del sistema")
        if "service" in self.command or "systemctl" in self.command:
            suggestions.append("Este comando afecta servicios del sistema")
        if "network" in self.command.lower() or "netplan" in self.command:
            suggestions.append("Este comando modifica configuración de red")

        # Determinar nivel de riesgo
        if any("CRÍTICO" in w for w in warnings):
            risk_level = "crítico"
            color = "#E74C3C"
        elif any("ALTO" in w for w in warnings):
            risk_level = "alto"
            color = "#F39C12"
        elif any("MEDIO" in w for w in warnings):
            risk_level = "medio"
            color = "#F1C40F"
        else:
            risk_level = "bajo"
            color = "#27AE60"

        # Construir mensaje de análisis
        analysis_text = f"""
        <div style='color: {color}; font-weight: bold; font-size: 11px;'>
        ⚠️ Nivel de riesgo: {risk_level.upper()}
        </div>
        """

        if warnings:
            analysis_text += "<div style='margin-top: 8px; font-size: 10px;'><b>Advertencias detectadas:</b><ul style='margin: 4px 0;'>"
            for warning in warnings:
                analysis_text += f"<li>{warning}</li>"
            analysis_text += "</ul></div>"

        if suggestions:
            analysis_text += "<div style='margin-top: 8px; font-size: 10px;'><b>Recomendaciones:</b><ul style='margin: 4px 0;'>"
            for suggestion in suggestions:
                analysis_text += f"<li>{suggestion}</li>"
            analysis_text += "</ul></div>"

        if not warnings and not suggestions:
            analysis_text += "<div style='margin-top: 8px; font-size: 10px;'>No se detectaron patrones peligrosos conocidos.</div>"

        analysis_text += f"""
        <div style='margin-top: 8px; font-size: 9px; color: #7C818C;'>
        <b>Herramienta:</b> {self.tool_name} • <b>Longitud:</b> {len(self.command)} caracteres
        </div>
        """

        self.security_analysis.setText(analysis_text)

    def _show_advanced_details(self):
        """Muestra detalles avanzados del análisis"""
        details_text = f"""
        <h3>Análisis Detallado del Comando</h3>
        <p><b>Comando completo:</b><br><code>{self.command}</code></p>
        <p><b>Herramienta de elevación:</b> {self.tool_name}</p>
        <p><b>Longitud:</b> {len(self.command)} caracteres</p>
        <p><b>Caracteres especiales:</b> {sum(1 for c in self.command if not c.isalnum() and c not in ' /.-_')}</p>
        
        <h4>Posibles riesgos identificados:</h4>
        <ul>
            <li>Ejecución con privilegios de root</li>
            <li>Modificación del sistema de archivos</li>
            <li>Cambios en la configuración del sistema</li>
            <li>Instalación/remoción de software</li>
        </ul>
        
        <p><i>Si no confías en este comando, es mejor cancelar la ejecución.</i></p>
        """

        QMessageBox.information(self, "🔍 Análisis Detallado", details_text)

    def _on_approved(self):
        """Maneja la aprobación del comando"""
        self.remember_decision = self.remember_check.isChecked()
        self.logger.info(f"Comando sudo aprobado: {self.command}")
        self.approved.emit(True)
        self.accept()

    def _on_rejected(self):
        """Maneja el rechazo del comando"""
        self.remember_decision = self.remember_check.isChecked()
        self.logger.info(f"Comando sudo rechazado: {self.command}")
        self.approved.emit(False)
        self.reject()

    def get_remember_decision(self) -> bool:
        """Retorna si se debe recordar la decisión"""
        return self.remember_decision

    def get_risk_level(self) -> str:
        """Retorna el nivel de riesgo detectado"""
        analysis_text = self.security_analysis.text()
        if "crítico" in analysis_text.lower():
            return "critical"
        elif "alto" in analysis_text.lower():
            return "high"
        elif "medio" in analysis_text.lower():
            return "medium"
        else:
            return "low"

    def get_command_hash(self) -> str:
        """Retorna un hash del comando para identificar comandos similares"""
        import hashlib

        return hashlib.md5(self.command.encode()).hexdigest()[:8]
