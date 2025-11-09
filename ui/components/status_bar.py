#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Barra de estado completamente reescrita con métricas en tiempo real
y visualización de rendimiento del sistema
"""

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QStatusBar, QWidget

from utils.logger import get_logger


class StatusBar(QStatusBar):
    """Barra de estado avanzada con monitoreo en tiempo real y múltiples indicadores"""

    def __init__(self, config_manager, state_manager):
        super().__init__()
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("StatusBar")

        # Datos de rendimiento
        self.performance_data = {}
        self.current_state = "idle"

        # Configuración de actualización
        self.update_intervals = {
            "time": 1000,  # 1 segundo para la hora
            "performance": 3000,  # 3 segundos para métricas
            "system": 5000,  # 5 segundos para estado del sistema
        }

        self._create_widgets()
        self._setup_timers()
        self._connect_signals()
        self._apply_initial_style()

        self.logger.info("StatusBar avanzado inicializado")

    def _create_widgets(self):
        """Crea todos los widgets de la barra de estado"""
        # Eliminar el mensaje por defecto
        self.clearMessage()

        # Widget contenedor principal
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(6, 2, 6, 2)
        self.main_layout.setSpacing(12)

        # Estado principal de la aplicación
        self.status_indicator = QLabel("🟢")
        self.status_indicator.setFixedWidth(20)
        self.status_label = QLabel("Sistema listo")
        self.status_label.setObjectName("status_label")

        # Información del modelo
        self.model_label = QLabel("Modelo: arch-chan")
        self.model_label.setObjectName("model_label")

        # Estado de voz
        self.voice_label = QLabel("🎤 Voz: Activa")
        self.voice_label.setObjectName("voice_label")

        # Indicador de rendimiento (CPU)
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setObjectName("performance_label")

        # Indicador de memoria
        self.memory_label = QLabel("RAM: 0%")
        self.memory_label.setObjectName("performance_label")

        # Estado de conexión
        self.connection_label = QLabel("🌐 Conectado")
        self.connection_label.setObjectName("connection_label")

        # Hora del sistema
        self.time_label = QLabel()
        self.time_label.setObjectName("time_label")
        self._update_time()

        # Barra de progreso para operaciones
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("status_progress_bar")
        self.progress_bar.setFixedWidth(120)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)

        # Agregar widgets al layout
        self.main_layout.addWidget(self.status_indicator)
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addSpacing(10)

        self.main_layout.addWidget(self.model_label)
        self.main_layout.addWidget(self.voice_label)
        self.main_layout.addWidget(self.cpu_label)
        self.main_layout.addWidget(self.memory_label)
        self.main_layout.addWidget(self.connection_label)

        self.main_layout.addStretch()
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.time_label)

        # Agregar el widget principal a la barra de estado
        self.addPermanentWidget(self.main_widget, 1)

    def _setup_timers(self):
        """Configura los timers para actualizaciones automáticas"""
        # Timer para la hora
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(self.update_intervals["time"])

        # Timer para métricas de rendimiento
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._update_performance_indicators)
        self.performance_timer.start(self.update_intervals["performance"])

        # Timer para estado del sistema
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self._update_system_status)
        self.system_timer.start(self.update_intervals["system"])

        # Timer para animaciones
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(500)

    def _connect_signals(self):
        """Conecta las señales del state manager y otros componentes"""
        if hasattr(self.state_manager, "state_changed"):
            self.state_manager.state_changed.connect(self._on_state_changed)

        if hasattr(self.state_manager, "error_occurred"):
            self.state_manager.error_occurred.connect(self._on_error_occurred)

        if hasattr(self.state_manager, "performance_updated"):
            self.state_manager.performance_updated.connect(self._on_performance_updated)

    def _apply_initial_style(self):
        """Aplica estilos iniciales a la barra de estado"""
        self.setStyleSheet(
            """
            QStatusBar {
                background-color: #2F343F;
                color: #D3DAE3;
                border-top: 1px solid #1A1E26;
                font-size: 10px;
            }
            QLabel#status_label {
                color: #D3DAE3;
                font-weight: bold;
            }
            QLabel#model_label, QLabel#voice_label, QLabel#performance_label {
                color: #7C818C;
                padding: 2px 6px;
                background-color: #383C4A;
                border-radius: 4px;
            }
            QLabel#connection_label {
                color: #33D17A;
                font-weight: bold;
            }
            QLabel#time_label {
                color: #7C818C;
                font-family: monospace;
            }
            QProgressBar#status_progress_bar {
                border: 1px solid #4B5162;
                border-radius: 4px;
                text-align: center;
                background-color: #383C4A;
            }
            QProgressBar#status_progress_bar::chunk {
                background-color: #1793D1;
                border-radius: 3px;
            }
        """
        )

    def _update_time(self):
        """Actualiza la hora del sistema con formato mejorado"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)

    def _update_performance_indicators(self):
        """Actualiza los indicadores de rendimiento del sistema"""
        try:
            if not self.performance_data:
                return

            # Actualizar CPU
            cpu_percent = self.performance_data.get("cpu_percent", 0)
            self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")

            # Color del indicador de CPU según uso
            if cpu_percent > 80:
                self.cpu_label.setStyleSheet("color: #F04A50; font-weight: bold;")
            elif cpu_percent > 60:
                self.cpu_label.setStyleSheet("color: #F27835;")
            else:
                self.cpu_label.setStyleSheet("color: #7C818C;")

            # Actualizar memoria
            memory_percent = self.performance_data.get("memory_percent", 0)
            self.memory_label.setText(f"RAM: {memory_percent:.1f}%")

            # Color del indicador de memoria según uso
            if memory_percent > 85:
                self.memory_label.setStyleSheet("color: #F04A50; font-weight: bold;")
            elif memory_percent > 70:
                self.memory_label.setStyleSheet("color: #F27835;")
            else:
                self.memory_label.setStyleSheet("color: #7C818C;")

        except Exception as e:
            self.logger.debug(f"Error actualizando indicadores de rendimiento: {e}")

    def _update_system_status(self):
        """Actualiza el estado general del sistema"""
        try:
            # Verificar estado de Ollama (simulado)
            ollama_running = self.performance_data.get("ollama_running", False)

            if ollama_running:
                self.connection_label.setText("🌐 Conectado")
                self.connection_label.setStyleSheet(
                    "color: #33D17A; font-weight: bold;"
                )
            else:
                self.connection_label.setText("🔴 Desconectado")
                self.connection_label.setStyleSheet(
                    "color: #F04A50; font-weight: bold;"
                )

            # Verificar temperatura (si está disponible)
            temperature = self.performance_data.get("temperature")
            if temperature and temperature > 75:
                self.showMessage(f"⚠️ Temperatura alta: {temperature}°C", 3000)

        except Exception as e:
            self.logger.debug(f"Error actualizando estado del sistema: {e}")

    def _update_animations(self):
        """Actualiza animaciones y efectos visuales"""
        try:
            if self.current_state == "processing":
                # Animación de puntos suspensivos
                current_text = self.status_label.text()
                if "..." in current_text:
                    base_text = (
                        current_text.replace("...", "")
                        .replace("..", "")
                        .replace(".", "")
                    )
                    dots = (len(current_text) - len(base_text)) % 4
                    self.status_label.setText(base_text + "." * dots)

        except Exception as e:
            self.logger.debug(f"Error en animaciones: {e}")

    def _on_state_changed(self, new_state):
        """Maneja cambios de estado de la aplicación"""
        self.current_state = new_state

        state_config = {
            "idle": ("🟢", "Sistema listo", False),
            "listening": ("🎤", "Grabando audio...", True),
            "processing": ("🤖", "Procesando", True),
            "speaking": ("🔊", "Reproduciendo audio", True),
            "error": ("🔴", "Error del sistema", False),
        }

        indicator, message, show_progress = state_config.get(
            new_state, ("🟡", "Estado desconocido", False)
        )

        self.status_indicator.setText(indicator)
        self.status_label.setText(message)
        self.progress_bar.setVisible(show_progress)

        if show_progress:
            self.progress_bar.setRange(0, 0)  # Progress bar indeterminado
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def _on_error_occurred(self, error_message):
        """Maneja errores del sistema"""
        self.status_indicator.setText("🔴")
        self.status_label.setText(f"Error: {error_message}")
        self.progress_bar.setVisible(False)

        # Mostrar mensaje temporal en la barra de estado
        self.showMessage(f"❌ {error_message}", 5000)

    def _on_performance_updated(self, metrics):
        """Maneja actualizaciones de métricas de rendimiento"""
        self.performance_data.update(metrics)
        self._update_performance_indicators()

    def update_model_info(self, model_name: str):
        """Actualiza la información del modelo activo"""
        self.model_label.setText(f"Modelo: {model_name}")
        self.logger.debug(f"Modelo actualizado en barra de estado: {model_name}")

    def update_voice_status(self, enabled: bool):
        """Actualiza el estado de la funcionalidad de voz"""
        status = "Activa" if enabled else "Inactiva"
        self.voice_label.setText(f"🎤 Voz: {status}")

        # Cambiar color según estado
        if enabled:
            self.voice_label.setStyleSheet("color: #33D17A;")
        else:
            self.voice_label.setStyleSheet("color: #7C818C;")

    def update_connection_status(self, connected: bool, service: str = "Ollama"):
        """Actualiza el estado de conexión con servicios"""
        if connected:
            self.connection_label.setText(f"🌐 {service}: Conectado")
            self.connection_label.setStyleSheet("color: #33D17A; font-weight: bold;")
        else:
            self.connection_label.setText(f"🔴 {service}: Desconectado")
            self.connection_label.setStyleSheet("color: #F04A50; font-weight: bold;")

    def update_performance_metrics(self, metrics: dict):
        """Actualiza las métricas de rendimiento desde fuentes externas"""
        self.performance_data.update(metrics)
        self._update_performance_indicators()

    def set_progress(self, value: int, maximum: int = 100):
        """Establece el progreso de la barra de progreso"""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)

        if value >= maximum:
            # Ocultar la barra cuando se complete
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))

    def show_temp_message(self, message: str, timeout: int = 3000):
        """Muestra un mensaje temporal en la barra de estado"""
        self.showMessage(message, timeout)

    def on_config_changed(self):
        """Maneja cambios en la configuración de la aplicación"""
        try:
            # Recargar intervalos de actualización desde configuración
            performance_interval = self.config_manager.getint(
                "UI", "status_update_interval", 3000
            )
            self.performance_timer.setInterval(performance_interval)

            # Reaplicar estilos si es necesario
            self._apply_initial_style()

            self.logger.debug("Configuración aplicada en StatusBar")

        except Exception as e:
            self.logger.error(f"Error aplicando configuración en StatusBar: {e}")

    def cleanup(self):
        """Limpia recursos y detiene timers"""
        try:
            self.time_timer.stop()
            self.performance_timer.stop()
            self.system_timer.stop()
            self.animation_timer.stop()
            self.logger.info("StatusBar limpiado correctamente")
        except Exception as e:
            self.logger.error(f"Error limpiando StatusBar: {e}")
