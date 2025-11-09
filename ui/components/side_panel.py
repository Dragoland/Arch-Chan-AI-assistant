#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Panel lateral completamente reescrito para Arch-Chan v2.1
Con métricas del sistema en tiempo real y controles rápidos
"""

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
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
    performance_toggled = Signal(bool)

    def __init__(self, config_manager, state_manager):
        super().__init__()
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("SidePanel")

        self.system_info = {}
        self.metric_widgets = {}
        self.performance_mode = False
        self.session_start = datetime.now()

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
        logo_label.setStyleSheet("font-size: 20px;")

        title_label = QLabel("Arch-Chan v2.1")
        title_label.setObjectName("title_label")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #1793D1;")

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
        separator.setStyleSheet("background-color: #4B5162; margin: 4px 0px;")
        separator.setFixedHeight(1)
        parent_layout.addWidget(separator)

    def _create_system_info_section(self, parent_layout):
        """Crea la sección de información del sistema"""
        # Header de la sección
        section_header = QHBoxLayout()
        sys_info_label = QLabel("MONITOR DEL SISTEMA")
        sys_info_label.setStyleSheet(
            "color: #1793D1; font-weight: bold; font-size: 10px; letter-spacing: 1px;"
        )

        self.performance_toggle = QToolButton()
        self.performance_toggle.setText("📊")
        self.performance_toggle.setCheckable(True)
        self.performance_toggle.setToolTip("Alternar métricas detalladas")
        self.performance_toggle.toggled.connect(self.performance_toggled.emit)
        self.performance_toggle.setFixedSize(24, 24)

        section_header.addWidget(sys_info_label)
        section_header.addStretch()
        section_header.addWidget(self.performance_toggle)

        parent_layout.addLayout(section_header)

        # Métricas del sistema
        metrics = [
            ("CPU", "0%", "cpu"),
            ("Memoria", "0.0/0.0 GB", "memory"),
            ("Disco", "0.0/0.0 GB", "disk"),
            ("Red", "↑0.0 ↓0.0 KB/s", "network"),
            ("Temperatura", "N/A", "temperature"),
            ("Ollama", "Verificando...", "ollama"),
        ]

        for label, default_value, key in metrics:
            widget = self._create_metric_group(label, default_value, "info_value", key)
            parent_layout.addWidget(widget)

        # Barra de uso de CPU (solo en modo rendimiento)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setObjectName("cpu_progress")
        self.cpu_progress.setVisible(False)
        self.cpu_progress.setTextVisible(True)
        self.cpu_progress.setFormat("CPU: %p%")
        parent_layout.addWidget(self.cpu_progress)

    def _create_session_info_section(self, parent_layout):
        """Crea la sección de información de sesión"""
        session_label = QLabel("INFORMACIÓN DE SESIÓN")
        session_label.setStyleSheet(
            "color: #1793D1; font-weight: bold; font-size: 10px; letter-spacing: 1px;"
        )
        parent_layout.addWidget(session_label)

        # Métricas de sesión
        session_metrics = [
            ("Modelo", "arch-chan", "model"),
            ("Mensajes", "0", "messages"),
            ("Activo desde", self._get_current_time(), "uptime"),
        ]

        for label, default_value, key in session_metrics:
            widget = self._create_metric_group(label, default_value, "info_value", key)
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
        voice_btn.setObjectName("quick_control_button")
        voice_btn.clicked.connect(self.voice_action_triggered.emit)
        control_layout.addWidget(voice_btn)

        clear_btn = QPushButton("🗑️ Limpiar Chat")
        clear_btn.setObjectName("quick_control_button")
        clear_btn.clicked.connect(self.clear_chat_triggered.emit)
        control_layout.addWidget(clear_btn)

        config_btn = QPushButton("⚙️ Configuración")
        config_btn.setObjectName("quick_control_button")
        config_btn.clicked.connect(self.config_action_triggered.emit)
        control_layout.addWidget(config_btn)

        stop_btn = QPushButton("⏹️ Detener Todo")
        stop_btn.setObjectName("quick_control_button")
        stop_btn.clicked.connect(self.stop_action_triggered.emit)
        control_layout.addWidget(stop_btn)

        parent_layout.addLayout(control_layout)

    def _create_version_info(self, parent_layout):
        """Crea la información de versión"""
        version_layout = QHBoxLayout()
        version_label = QLabel("v2.1.0 - Arch Linux Native")
        version_label.setStyleSheet("color: #7C818C; font-size: 9px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_layout.addWidget(version_label)
        parent_layout.addLayout(version_layout)

    def _create_metric_group(self, label, value, value_class, key):
        """Crea un grupo de métrica"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 2, 6, 2)

        label_widget = QLabel(f"{label}:")
        label_widget.setProperty("class", "info_label")
        label_widget.setStyleSheet("color: #7C818C; font-size: 10px;")
        label_widget.setFixedWidth(80)

        value_widget = QLabel(value)
        value_widget.setProperty("class", value_class)
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_widget.setStyleSheet(
            "color: #D3DAE3; font-size: 10px; font-weight: bold;"
        )

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)

        # Registrar widget para actualizaciones
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
        if "uptime" in self.metric_widgets:
            self.metric_widgets["uptime"].setText(self.session_start.strftime("%H:%M"))

    def update_system_info(self, system_info):
        """Actualiza la información del sistema"""
        try:
            self.system_info = system_info

            # CPU
            cpu_percent = system_info.get("cpu_percent", 0)
            cpu_text = f"{cpu_percent:.1f}%"
            cpu_class = "info_value_warning" if cpu_percent > 80 else "info_value"
            self._update_metric("cpu", cpu_text, cpu_class)

            # Actualizar barra de progreso de CPU
            if self.performance_mode:
                self.cpu_progress.setValue(int(cpu_percent))
                if cpu_percent > 80:
                    self.cpu_progress.setStyleSheet(
                        "QProgressBar::chunk { background-color: #F04A50; }"
                    )
                elif cpu_percent > 60:
                    self.cpu_progress.setStyleSheet(
                        "QProgressBar::chunk { background-color: #F27835; }"
                    )
                else:
                    self.cpu_progress.setStyleSheet(
                        "QProgressBar::chunk { background-color: #33D17A; }"
                    )

            # Memoria
            memory_used = system_info.get("memory_used_gb", 0)
            memory_total = system_info.get("memory_total_gb", 1)
            memory_percent = system_info.get("memory_percent", 0)
            memory_text = f"{memory_used:.1f}/{memory_total:.1f} GB"
            memory_class = "info_value_warning" if memory_percent > 80 else "info_value"
            self._update_metric("memory", memory_text, memory_class)

            # Disco
            disk_used = system_info.get("disk_used_gb", 0)
            disk_total = system_info.get("disk_total_gb", 1)
            disk_percent = system_info.get("disk_percent", 0)
            disk_text = f"{disk_used:.1f}/{disk_total:.1f} GB"
            disk_class = "info_value_warning" if disk_percent > 90 else "info_value"
            self._update_metric("disk", disk_text, disk_class)

            # Red
            net_sent = system_info.get("network_sent", 0)
            net_recv = system_info.get("network_recv", 0)
            net_text = f"↑{net_sent:.1f} ↓{net_recv:.1f} KB/s"
            self._update_metric("network", net_text, "info_value")

            # Temperatura
            cpu_temp = system_info.get("temperature")
            if cpu_temp is not None:
                temp_text = f"{cpu_temp:.1f}°C"
                temp_class = "info_value_error" if cpu_temp > 80 else "info_value"
            else:
                temp_text = "N/A"
                temp_class = "info_value"
            self._update_metric("temperature", temp_text, temp_class)

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

                # Aplicar estilos según la clase
                if css_class == "info_value_warning":
                    value_widget.setStyleSheet(
                        "color: #F27835; font-size: 10px; font-weight: bold;"
                    )
                elif css_class == "info_value_error":
                    value_widget.setStyleSheet(
                        "color: #F04A50; font-size: 10px; font-weight: bold;"
                    )
                elif css_class == "info_value_success":
                    value_widget.setStyleSheet(
                        "color: #33D17A; font-size: 10px; font-weight: bold;"
                    )
                else:
                    value_widget.setStyleSheet(
                        "color: #D3DAE3; font-size: 10px; font-weight: bold;"
                    )

        except Exception as e:
            self.logger.debug(f"Error actualizando métrica {metric_name}: {e}")

    def update_session_info(self, model_name, message_count):
        """Actualiza la información de sesión"""
        try:
            self._update_metric("model", model_name, "info_value")
            self._update_metric("messages", str(message_count), "info_value")
            self._update_uptime()
        except Exception as e:
            self.logger.error(f"Error actualizando información de sesión: {e}")

    def update_health_status(self, health_status):
        """
        Actualiza el estado de salud del sistema
        Args:
            health_status: String con el estado de salud ("healthy", "warning", "critical")
        """
        try:
            # Mapear estados de salud a clases CSS
            status_map = {
                "healthy": "info_value_success",
                "warning": "info_value_warning",
                "critical": "info_value_error",
                "unknown": "info_value",
            }

            css_class = status_map.get(health_status, "info_value")
            status_text = {
                "healthy": "🟢 Saludable",
                "warning": "🟡 Advertencia",
                "critical": "🔴 Crítico",
                "unknown": "⚪ Desconocido",
            }.get(health_status, "⚪ Desconocido")

            # Actualizar métrica de salud general si existe
            if "health" in self.metric_widgets:
                self._update_metric("health", status_text, css_class)

            # También podemos actualizar el estado de Ollama basado en salud general
            if health_status == "critical":
                ollama_text = "🔴 Crítico"
                ollama_class = "info_value_error"
            elif health_status == "warning":
                ollama_text = "🟡 Advertencia"
                ollama_class = "info_value_warning"
            else:
                # Mantener el estado específico de Ollama si está saludable
                ollama_running = self.system_info.get("ollama_running", False)
                ollama_text = "🟢 Conectado" if ollama_running else "🔴 Desconocido"
                ollama_class = "info_value_success" if ollama_running else "info_value"

            self._update_metric("ollama", ollama_text, ollama_class)

        except Exception as e:
            self.logger.error(f"Error actualizando estado de salud: {e}")

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

    def set_performance_mode(self, enabled: bool):
        """Activa o desactiva el modo rendimiento"""
        self.performance_mode = enabled
        self.performance_toggle.setChecked(enabled)
        self.cpu_progress.setVisible(enabled)

        if enabled:
            self.performance_toggle.setToolTip("Desactivar métricas detalladas")
            self.logger.info("Modo rendimiento activado en SidePanel")
        else:
            self.performance_toggle.setToolTip("Activar métricas detalladas")
            self.logger.info("Modo rendimiento desactivado en SidePanel")

    def on_theme_changed(self, theme_name):
        """Maneja cambios de tema"""
        # Los estilos principales se aplican via QSS
        # Este método puede usarse para ajustes específicos
        pass
