#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum

from PySide6.QtCore import QObject, Signal

from utils.logger import get_logger


class AppState(Enum):
    """Estados posibles de la aplicación"""

    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"
    UPDATING = "updating"


class AppStateManager(QObject):
    """Gestor centralizado del estado de la aplicación"""

    # Señales
    state_changed = Signal(AppState, AppState)  # old_state, new_state
    error_occurred = Signal(str)
    warning_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.logger = get_logger("AppStateManager")
        self._current_state = AppState.IDLE
        self._previous_state = None
        self._error_message = ""
        self._warning_message = ""

        self.logger.info("AppStateManager inicializado")

    @property
    def current_state(self):
        """Retorna el estado actual"""
        return self._current_state

    @property
    def previous_state(self):
        """Retorna el estado anterior"""
        return self._previous_state

    @property
    def is_busy(self):
        """Indica si la aplicación está ocupada"""
        return self._current_state not in [AppState.IDLE, AppState.ERROR]

    @property
    def can_accept_input(self):
        """Indica si la aplicación puede aceptar entrada"""
        return self._current_state == AppState.IDLE

    def set_state(self, new_state):
        """Cambia el estado de la aplicación"""
        if new_state == self._current_state:
            return

        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state

        self.logger.info(f"Cambio de estado: {old_state.value} -> {new_state.value}")
        self.state_changed.emit(old_state, new_state)

    def set_idle(self):
        """Establece el estado en IDLE"""
        self.set_state(AppState.IDLE)

    def set_listening(self):
        """Establece el estado en LISTENING"""
        self.set_state(AppState.LISTENING)

    def set_processing(self):
        """Establece el estado en PROCESSING"""
        self.set_state(AppState.PROCESSING)

    def set_speaking(self):
        """Establece el estado en SPEAKING"""
        self.set_state(AppState.SPEAKING)

    def set_error(self, error_message=""):
        """Establece el estado en ERROR"""
        self._error_message = error_message
        self.set_state(AppState.ERROR)
        if error_message:
            self.error_occurred.emit(error_message)

    def set_updating(self):
        """Establece el estado en UPDATING"""
        self.set_state(AppState.UPDATING)

    def get_error_message(self):
        """Retorna el mensaje de error"""
        return self._error_message

    def clear_error(self):
        """Limpia el estado de error"""
        if self._current_state == AppState.ERROR:
            self.set_state(self._previous_state or AppState.IDLE)
        self._error_message = ""

    def set_warning(self, warning_message):
        """Establece una advertencia"""
        self._warning_message = warning_message
        self.warning_occurred.emit(warning_message)

    def get_warning_message(self):
        """Retorna el mensaje de advertencia"""
        return self._warning_message

    def can_transition_to(self, new_state):
        """Verifica si es posible transicionar a un nuevo estado"""
        transitions = {
            AppState.IDLE: [
                AppState.LISTENING,
                AppState.PROCESSING,
                AppState.UPDATING,
                AppState.ERROR,
            ],
            AppState.LISTENING: [AppState.PROCESSING, AppState.IDLE, AppState.ERROR],
            AppState.PROCESSING: [AppState.SPEAKING, AppState.IDLE, AppState.ERROR],
            AppState.SPEAKING: [AppState.IDLE, AppState.ERROR],
            AppState.ERROR: [AppState.IDLE],
            AppState.UPDATING: [AppState.IDLE, AppState.ERROR],
        }

        return new_state in transitions.get(self._current_state, [])

    def force_state(self, new_state):
        """Fuerza un cambio de estado (usar con cuidado)"""
        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state

        self.logger.warning(f"Estado forzado: {old_state.value} -> {new_state.value}")
        self.state_changed.emit(old_state, new_state)

    def get_state_info(self):
        """Retorna información del estado actual"""
        return {
            "current_state": self._current_state.value,
            "previous_state": (
                self._previous_state.value if self._previous_state else None
            ),
            "is_busy": self.is_busy,
            "can_accept_input": self.can_accept_input,
            "error_message": self._error_message,
            "warning_message": self._warning_message,
        }
