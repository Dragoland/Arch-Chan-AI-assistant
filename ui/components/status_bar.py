#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QStatusBar

from utils.logger import get_logger


class StatusBar(QStatusBar):
    """Barra de estado mejorada de la aplicación"""

    def __init__(self, config_manager, state_manager):
        super().__init__()
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("StatusBar")

        self._create_widgets()
        self._setup_timers()
        self._connect_signals()

        self.logger.info("StatusBar inicializado")

    def _create_widgets(self):
        """Crea los widgets de la barra de estado"""
        # Estado principal
        self.status_label = QLabel("🟢 Sistema listo")
        self.addWidget(self.status_label)

        # Separador
        separator1 = QLabel("|")
        self.addPermanentWidget(separator1)

        # Información de modelo
        self.model_label = QLabel("Modelo: arch-chan")
        self.addPermanentWidget(self.model_label)

        # Separador
        separator2 = QLabel("|")
        self.addPermanentWidget(separator2)

        # Estado de voz
        self.voice_label = QLabel("🎤 Voz: Activa")
        self.addPermanentWidget(self.voice_label)

        # Separador
        separator3 = QLabel("|")
        self.addPermanentWidget(separator3)

        # Hora del sistema
        self.time_label = QLabel()
        self._update_time()
        self.addPermanentWidget(self.time_label)

    def _setup_timers(self):
        """Configura los timers de actualización"""
        # Timer para la hora
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(60000)  # Actualizar cada minuto

        # Timer para estado del sistema
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self._update_system_status)
        self.system_timer.start(5000)  # Actualizar cada 5 segundos

    def _connect_signals(self):
        """Conecta las señales del state manager"""
        if hasattr(self.state_manager, "state_changed"):
            self.state_manager.state_changed.connect(self._on_state_changed)

        if hasattr(self.state_manager, "error_occurred"):
            self.state_manager.error_occurred.connect(self._on_error_occurred)

    def _update_time(self):
        """Actualiza la hora en la barra de estado"""
        current_time = datetime.now().strftime("%H:%M")
        self.time_label.setText(current_time)

    def _update_system_status(self):
        """Actualiza el estado del sistema con información en tiempo real"""
        try:
            # Simular verificación de servicios (en implementación real, verificar Ollama, etc.)
            import random

            services_ok = random.choice(
                [True, True, True, False]
            )  # 75% de probabilidad de OK

            if services_ok:
                self.connection_indicator = "🌐 Conectado"
            else:
                self.connection_indicator = "🔴 Desconectado"

        except Exception as e:
            self.logger.debug(f"Error actualizando estado del sistema: {e}")

    def _on_state_changed(self, old_state, new_state):
        """Maneja cambios de estado"""
        state_messages = {
            "idle": "🟢 Sistema listo",
            "listening": "🎤 Grabando audio...",
            "processing": "🤖 Procesando con IA...",
            "speaking": "🔊 Reproduciendo respuesta...",
            "error": "🔴 Error en el sistema",
        }

        message = state_messages.get(
            new_state.value if hasattr(new_state, "value") else str(new_state),
            "🟡 Estado desconocido",
        )
        self.status_label.setText(message)

    def _on_error_occurred(self, error_message):
        """Maneja errores del sistema"""
        self.status_label.setText(f"🔴 Error: {error_message}")

    def update_model_info(self, model_name: str):
        """Actualiza la información del modelo"""
        self.model_label.setText(f"Modelo: {model_name}")

    def update_voice_status(self, enabled: bool):
        """Actualiza el estado de voz"""
        status = "Activa" if enabled else "Inactiva"
        self.voice_label.setText(f"🎤 Voz: {status}")

    def show_message(self, message: str, timeout: int = 0):
        """
        Muestra un mensaje en la barra de estado

        Args:
            message: Mensaje a mostrar
            timeout: Tiempo en milisegundos (0 para permanente)
        """
        self.showMessage(message, timeout)

    def on_config_changed(self):
        """Maneja cambios en la configuración"""
        # Reaplicar estilos si es necesario
        pass
