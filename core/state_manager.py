#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

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
    STARTING = "starting"
    SHUTTING_DOWN = "shutting_down"


class AppStateManager(QObject):
    """Gestor centralizado del estado de la aplicación"""

    # Señales
    state_changed = Signal(AppState, AppState)  # old_state, new_state
    error_occurred = Signal(str)
    warning_occurred = Signal(str)
    status_message = Signal(str)  # Mensajes de estado general

    def __init__(self):
        super().__init__()
        self.logger = get_logger("AppStateManager")

        # Estado actual y histórico
        self._current_state = AppState.STARTING
        self._previous_state = None
        self._state_history: List[Dict] = []

        # Información de estado
        self._error_message = ""
        self._warning_message = ""
        self._status_message = "Aplicación iniciando..."

        # Tiempos de estado
        self._state_start_time = datetime.now()
        self._app_start_time = datetime.now()

        # Contadores
        self._state_change_count = 0

        self.logger.info("AppStateManager inicializado")

    @property
    def current_state(self) -> AppState:
        """Retorna el estado actual"""
        return self._current_state

    @property
    def previous_state(self) -> Optional[AppState]:
        """Retorna el estado anterior"""
        return self._previous_state

    @property
    def is_busy(self) -> bool:
        """Indica si la aplicación está ocupada"""
        busy_states = [
            AppState.LISTENING,
            AppState.PROCESSING,
            AppState.SPEAKING,
            AppState.UPDATING,
            AppState.STARTING,
            AppState.SHUTTING_DOWN,
        ]
        return self._current_state in busy_states

    @property
    def can_accept_input(self) -> bool:
        """Indica si la aplicación puede aceptar entrada"""
        return self._current_state == AppState.IDLE

    @property
    def is_ready(self) -> bool:
        """Indica si la aplicación está lista para usar"""
        return self._current_state == AppState.IDLE

    def set_state(self, new_state: AppState, reason: str = "") -> bool:
        """
        Cambia el estado de la aplicación

        Args:
            new_state: Nuevo estado
            reason: Razón del cambio (opcional)

        Returns:
            True si el cambio fue exitoso
        """
        if new_state == self._current_state:
            return True

        if not self.can_transition_to(new_state):
            self.logger.warning(
                f"Transición no permitida: {self._current_state.value} -> {new_state.value}"
            )
            return False

        # Registrar cambio de estado
        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state

        # Calcular duración del estado anterior
        state_duration = (datetime.now() - self._state_start_time).total_seconds()
        self._state_start_time = datetime.now()

        # Guardar en historial
        state_record = {
            "from_state": old_state.value,
            "to_state": new_state.value,
            "timestamp": datetime.now(),
            "duration_seconds": state_duration,
            "reason": reason,
        }
        self._state_history.append(state_record)
        self._state_change_count += 1

        # Limitar historial a 100 entradas
        if len(self._state_history) > 100:
            self._state_history = self._state_history[-100:]

        self.logger.info(
            f"Cambio de estado: {old_state.value} -> {new_state.value}"
            + (f" ({reason})" if reason else "")
        )

        self.state_changed.emit(old_state, new_state)
        return True

    def set_idle(self, reason: str = "") -> bool:
        """Establece el estado en IDLE"""
        return self.set_state(AppState.IDLE, reason)

    def set_listening(self, reason: str = "") -> bool:
        """Establece el estado en LISTENING"""
        return self.set_state(AppState.LISTENING, reason)

    def set_processing(self, reason: str = "") -> bool:
        """Establece el estado en PROCESSING"""
        return self.set_state(AppState.PROCESSING, reason)

    def set_speaking(self, reason: str = "") -> bool:
        """Establece el estado en SPEAKING"""
        return self.set_state(AppState.SPEAKING, reason)

    def set_error(self, error_message: str = "", reason: str = "") -> bool:
        """Establece el estado en ERROR"""
        self._error_message = error_message
        success = self.set_state(AppState.ERROR, reason)
        if success and error_message:
            self.error_occurred.emit(error_message)
        return success

    def set_updating(self, reason: str = "") -> bool:
        """Establece el estado en UPDATING"""
        return self.set_state(AppState.UPDATING, reason)

    def set_starting(self, reason: str = "") -> bool:
        """Establece el estado en STARTING"""
        return self.set_state(AppState.STARTING, reason)

    def set_shutting_down(self, reason: str = "") -> bool:
        """Establece el estado en SHUTTING_DOWN"""
        return self.set_state(AppState.SHUTTING_DOWN, reason)

    def get_error_message(self) -> str:
        """Retorna el mensaje de error"""
        return self._error_message

    def clear_error(self) -> bool:
        """Limpia el estado de error y vuelve al estado anterior"""
        if self._current_state == AppState.ERROR:
            target_state = self._previous_state or AppState.IDLE
            success = self.set_state(target_state, "Error cleared")
            if success:
                self._error_message = ""
            return success
        return True

    def set_warning(self, warning_message: str):
        """Establece una advertencia"""
        self._warning_message = warning_message
        self.warning_occurred.emit(warning_message)

    def get_warning_message(self) -> str:
        """Retorna el mensaje de advertencia"""
        return self._warning_message

    def clear_warning(self):
        """Limpia la advertencia actual"""
        self._warning_message = ""

    def set_status_message(self, message: str):
        """Establece un mensaje de estado general"""
        self._status_message = message
        self.status_message.emit(message)

    def get_status_message(self) -> str:
        """Retorna el mensaje de estado general"""
        return self._status_message

    def can_transition_to(self, new_state: AppState) -> bool:
        """Verifica si es posible transicionar a un nuevo estado"""
        transitions = {
            AppState.STARTING: [AppState.IDLE, AppState.ERROR, AppState.SHUTTING_DOWN],
            AppState.IDLE: [
                AppState.LISTENING,
                AppState.PROCESSING,
                AppState.UPDATING,
                AppState.ERROR,
                AppState.SHUTTING_DOWN,
            ],
            AppState.LISTENING: [AppState.PROCESSING, AppState.IDLE, AppState.ERROR],
            AppState.PROCESSING: [AppState.SPEAKING, AppState.IDLE, AppState.ERROR],
            AppState.SPEAKING: [AppState.IDLE, AppState.ERROR],
            AppState.UPDATING: [AppState.IDLE, AppState.ERROR],
            AppState.ERROR: [AppState.IDLE, AppState.SHUTTING_DOWN],
            AppState.SHUTTING_DOWN: [],  # Estado final
        }

        allowed_transitions = transitions.get(self._current_state, [])
        return new_state in allowed_transitions

    def force_state(self, new_state: AppState, reason: str = "") -> bool:
        """Fuerza un cambio de estado (usar con cuidado)"""
        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state

        # Registrar cambio forzado
        state_duration = (datetime.now() - self._state_start_time).total_seconds()
        self._state_start_time = datetime.now()

        state_record = {
            "from_state": old_state.value,
            "to_state": new_state.value,
            "timestamp": datetime.now(),
            "duration_seconds": state_duration,
            "reason": f"FORCED: {reason}",
            "forced": True,
        }
        self._state_history.append(state_record)
        self._state_change_count += 1

        self.logger.warning(
            f"Estado forzado: {old_state.value} -> {new_state.value}"
            + (f" ({reason})" if reason else "")
        )

        self.state_changed.emit(old_state, new_state)
        return True

    def get_state_info(self) -> Dict:
        """Retorna información completa del estado actual"""
        current_duration = (datetime.now() - self._state_start_time).total_seconds()
        total_uptime = (datetime.now() - self._app_start_time).total_seconds()

        return {
            "current_state": self._current_state.value,
            "previous_state": (
                self._previous_state.value if self._previous_state else None
            ),
            "current_state_duration": round(current_duration, 2),
            "total_uptime": round(total_uptime, 2),
            "state_change_count": self._state_change_count,
            "is_busy": self.is_busy,
            "can_accept_input": self.can_accept_input,
            "is_ready": self.is_ready,
            "error_message": self._error_message,
            "warning_message": self._warning_message,
            "status_message": self._status_message,
            "state_history_count": len(self._state_history),
        }

    def get_state_history(self, limit: int = 10) -> List[Dict]:
        """Retorna el historial de estados recientes"""
        return self._state_history[-limit:] if self._state_history else []

    def get_state_statistics(self) -> Dict:
        """Retorna estadísticas de uso de estados"""
        if not self._state_history:
            return {}

        stats = {}
        total_time = 0

        for record in self._state_history:
            state = record["to_state"]
            duration = record.get("duration_seconds", 0)

            if state not in stats:
                stats[state] = {"count": 0, "total_time": 0.0}

            stats[state]["count"] += 1
            stats[state]["total_time"] += duration
            total_time += duration

        # Calcular porcentajes
        for state_data in stats.values():
            if total_time > 0:
                state_data["percentage"] = (state_data["total_time"] / total_time) * 100
            else:
                state_data["percentage"] = 0

        return stats

    def reset(self):
        """Reinicia el estado manager (para testing)"""
        self._current_state = AppState.STARTING
        self._previous_state = None
        self._state_history.clear()
        self._error_message = ""
        self._warning_message = ""
        self._status_message = "Reiniciado"
        self._state_start_time = datetime.now()
        self._app_start_time = datetime.now()
        self._state_change_count = 0
