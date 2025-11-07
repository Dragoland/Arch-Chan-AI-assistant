#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from utils.logger import get_logger


class SidePanel(QWidget):
    """Panel lateral con información del sistema y controles rápidos"""

    # Señales
    voice_action_triggered = Signal()
    clear_chat_triggered = Signal()
    config_action_triggered = Signal()
    stop_action_triggered = Signal()
    toggle_panel_triggered = Signal()

    def __init__(self, config_manager, state_manager):
        super().__init__()
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("SidePanel")

        self.system_info = {}
        self.metric_widgets = {}  # CORREGIDO: Diccionario para tracking de widgets

        self._create_ui()
        self._setup_initial_values()

        self.logger.info("SidePanel inicializado")

    def _create_ui(self):
        """Crea la interfaz del panel lateral"""
        self.setObjectName("system_info_frame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header del panel
        self._create_header(layout)

        # Separador
        self._add_separator(layout)

        # Información del sistema
        self._create_system_info_section(layout)

        # Separador
        self._add_separator(layout)

        # Información de sesión
        self._create_session_info_section(layout)

        # Separador
        self._add_separator(layout)

        # Controles rápidos
        self._create_quick_controls(layout)

        # Espacio flexible
        layout.addStretch()

        # Información de versión
        self._create_version_info(layout)

    def _create_header(self, parent_layout):
        """Crea el header del panel lateral"""
        header_layout = QHBoxLayout()

        # Logo y título
        logo_label = QLabel("🐧")
        logo_label.setObjectName("arch_logo")
        logo_label.setFixedSize(32, 32)

        title_label = QLabel("Arch-Chan v2.1")
        title_label.setObjectName("title_label")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold;")

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Botón para colapsar panel
        self.collapse_button = QToolButton()
        self.collapse_button.setText("◀")
        self.collapse_button.setToolTip("Colapsar panel lateral")
        self.collapse_button.setFixedSize(24, 24)
        self.collapse_button.clicked.connect(self.toggle_panel_triggered.emit)
        header_layout.addWidget(self.collapse_button)

        parent_layout.addLayout(header_layout)

    def _add_separator(self, parent_layout):
        """Añade un separador"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #4B5162; margin: 4px 0px;")
        separator.setFixedHeight(1)
        parent_layout.addWidget(separator)

    def _create_system_info_section(self, parent_layout):
        """Crea la sección de información del sistema"""
        sys_info_label = QLabel("MONITOR DEL SISTEMA")
        sys_info_label.setStyleSheet(
            "color: #1793D1; font-weight: bold; font-size: 10px; letter-spacing: 1px;"
        )
        parent_layout.addWidget(sys_info_label)

        # Métricas del sistema
        metrics = [
            ("CPU", "0%"),
            ("Memoria", "0.0/0.0 GB"),
            ("Disco", "0.0/0.0 GB"),
            ("Red", "↑0.0 ↓0.0 KB/s"),
            ("Temperatura", "N/A"),
            ("Ollama", "Verificando..."),
        ]

        for label, default_value in metrics:
            widget = self._create_metric_group(label, default_value, "info_value")
            parent_layout.addWidget(widget)

    def _create_session_info_section(self, parent_layout):
        """Crea la sección de información de sesión"""
        session_label = QLabel("INFORMACIÓN DE SESIÓN")
        session_label.setStyleSheet(
            "color: #1793D1; font-weight: bold; font-size: 10px; letter-spacing: 1px;"
        )
        parent_layout.addWidget(session_label)

        # Métricas de sesión
        session_metrics = [
            ("Modelo", "arch-chan"),
            ("Mensajes", "0"),
            ("Activo desde", self._get_current_time()),
        ]

        for label, default_value in session_metrics:
            widget = self._create_metric_group(label, default_value, "info_value")
            parent_layout.addWidget(widget)

    def _create_quick_controls(self, parent_layout):
        """Crea la sección de controles rápidos"""
        controls_label = QLabel("CONTROLES RÁPIDOS")
        controls_label.setStyleSheet(
            "color: #1793D1; font-weight: bold; font-size: 10px; letter-spacing: 1px;"
        )
        parent_layout.addWidget(controls_label)

        # Botones de control
        control_layout = QVBoxLayout()
        control_layout.setSpacing(6)

        voice_btn = QPushButton("🎤 Iniciar Voz")
        voice_btn.clicked.connect(self.voice_action_triggered.emit)
        control_layout.addWidget(voice_btn)

        clear_btn = QPushButton("🗑️ Limpiar Chat")
        clear_btn.clicked.connect(self.clear_chat_triggered.emit)
        control_layout.addWidget(clear_btn)

        config_btn = QPushButton("⚙️ Configuración")
        config_btn.clicked.connect(self.config_action_triggered.emit)
        control_layout.addWidget(config_btn)

        stop_btn = QPushButton("⏹️ Detener Todo")
        stop_btn.clicked.connect(self.stop_action_triggered.emit)
        control_layout.addWidget(stop_btn)

        parent_layout.addLayout(control_layout)

    def _create_version_info(self, parent_layout):
        """Crea la información de versión"""
        version_layout = QHBoxLayout()
        version_label = QLabel("v2.1 - Arch Linux Native")
        version_label.setStyleSheet("color: #7C818C; font-size: 9px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_layout.addWidget(version_label)
        parent_layout.addLayout(version_layout)

    def _create_metric_group(self, label, value, value_class="info_value"):
        """Crea un grupo de métrica"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 2, 6, 2)

        label_widget = QLabel(f"{label}:")
        label_widget.setProperty("class", "info_label")
        label_widget.setFixedWidth(80)

        value_widget = QLabel(value)
        value_widget.setProperty("class", value_class)
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)

        # CORREGIDO: Usar diccionario para tracking
        key = label.lower().replace(" ", "_")
        self.metric_widgets[key] = value_widget

        return widget

    def _setup_initial_values(self):
        """Configura los valores iniciales"""
        self._update_uptime()

    def _get_current_time(self):
        """Obtiene la hora actual formateada"""
        return datetime.now().strftime("%H:%M")

    def _update_uptime(self):
        """Actualiza el tiempo de actividad"""
        if "activo_desde" in self.metric_widgets:
            self.metric_widgets["activo_desde"].setText(self._get_current_time())

    def update_system_info(self, system_info):
        """Actualiza la información del sistema"""
        try:
            self.system_info = system_info

            # CPU
            cpu_text = f"{system_info.get('cpu', 0):.1f}%"
            cpu_class = (
                "info_value_warning" if system_info.get("cpu", 0) > 80 else "info_value"
            )
            self._update_metric("cpu", cpu_text, cpu_class)

            # Memoria
            memory_used = system_info.get("memory_used", 0)
            memory_total = system_info.get("memory_total", 1)
            memory_text = f"{memory_used:.1f}/{memory_total:.1f} GB"
            memory_class = (
                "info_value_warning"
                if system_info.get("memory_percent", 0) > 80
                else "info_value"
            )
            self._update_metric("memoria", memory_text, memory_class)

            # Disco
            disk_used = system_info.get("disk_used", 0)
            disk_total = system_info.get("disk_total", 1)
            disk_text = f"{disk_used:.1f}/{disk_total:.1f} GB"
            disk_class = (
                "info_value_warning"
                if system_info.get("disk_percent", 0) > 90
                else "info_value"
            )
            self._update_metric("disco", disk_text, disk_class)

            # Red
            net_sent = system_info.get("network_sent", 0)
            net_recv = system_info.get("network_recv", 0)
            net_text = f"↑{net_sent:.1f} ↓{net_recv:.1f} KB/s"
            self._update_metric("red", net_text, "info_value")

            # Temperatura
            cpu_temp = system_info.get("cpu_temp")
            if cpu_temp is not None:
                temp_text = f"{cpu_temp:.1f}°C"
                temp_class = "info_value_error" if cpu_temp > 80 else "info_value"
            else:
                temp_text = "N/A"
                temp_class = "info_value"
            self._update_metric("temperatura", temp_text, temp_class)

            # Ollama
            ollama_running = system_info.get("ollama_running", False)
            ollama_text = "🟢 Conectado" if ollama_running else "🔴 Desconectado"
            ollama_class = (
                "info_value_success" if ollama_running else "info_value_error"
            )
            self._update_metric("ollama", ollama_text, ollama_class)

        except Exception as e:
            self.logger.error(f"Error actualizando información del sistema: {e}")

    def _update_metric(self, metric_name, text, css_class):
        """Actualiza una métrica específica"""
        try:
            if metric_name in self.metric_widgets:
                value_widget = self.metric_widgets[metric_name]
                value_widget.setText(text)
                value_widget.setProperty("class", css_class)
                # Forzar actualización de estilo
                value_widget.style().unpolish(value_widget)
                value_widget.style().polish(value_widget)
        except Exception as e:
            self.logger.debug(f"Error actualizando métrica {metric_name}: {e}")

    def update_session_info(self, model_name, message_count):
        """Actualiza la información de sesión"""
        try:
            self._update_metric("modelo", model_name, "info_value")
            self._update_metric("mensajes", str(message_count), "info_value")
            self._update_uptime()
        except Exception as e:
            self.logger.error(f"Error actualizando información de sesión: {e}")

    def on_config_changed(self):
        """Maneja cambios en la configuración"""
        # Reaplicar estilos si es necesario
        pass

    def toggle_collapse_button(self, is_collapsed):
        """Alterna el botón de colapsar"""
        if is_collapsed:
            self.collapse_button.setText("▶")
            self.collapse_button.setToolTip("Expandir panel lateral")
        else:
            self.collapse_button.setText("◀")
            self.collapse_button.setToolTip("Colapsar panel lateral")
