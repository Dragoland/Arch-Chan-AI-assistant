#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Optional

from PySide6.QtCore import QMutex, QThread, QWaitCondition, Signal

from utils.logger import get_logger


class BaseWorker(QThread):
    """Clase base para todos los workers de la aplicación"""

    # Señales base
    started = Signal()  # Worker iniciado
    finished = Signal()  # Worker finalizado
    error_occurred = Signal(str)  # Error ocurrido
    progress_updated = Signal(int)  # Progreso actualizado (0-100)

    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)

        # Control de ejecución
        self._is_running = False
        self._is_paused = False
        self._should_stop = False

        # Sincronización
        self.mutex = QMutex()
        self.condition = QWaitCondition()

        # Resultados
        self._result: Optional[Any] = None
        self._error: Optional[str] = None

        self.logger.debug(f"{self.__class__.__name__} inicializado")

    def run(self):
        """Método principal del worker"""
        try:
            self._is_running = True
            self._should_stop = False
            self.started.emit()

            self.logger.info(f"Iniciando worker {self.__class__.__name__}")

            # Ejecutar la tarea principal
            self._result = self._execute()

            self.logger.info(f"Worker {self.__class__.__name__} completado")

        except Exception as e:
            error_msg = f"Error en worker {self.__class__.__name__}: {e}"
            self.logger.error(error_msg)
            self._error = error_msg
            self.error_occurred.emit(error_msg)

        finally:
            self._is_running = False
            self.finished.emit()

    def _execute(self) -> Any:
        """
        Método abstracto que debe ser implementado por las subclases

        Returns:
            Resultado de la ejecución
        """
        raise NotImplementedError("Las subclases deben implementar _execute()")

    def stop(self):
        """Solicita la detención del worker"""
        self.logger.info(f"Solicitando detención de {self.__class__.__name__}")
        self._should_stop = True
        self.resume()  # Reanudar si está pausado para que pueda detenerse

    def pause(self):
        """Pausa la ejecución del worker"""
        if self._is_running and not self._is_paused:
            self.logger.info(f"Pausando {self.__class__.__name__}")
            self._is_paused = True

    def resume(self):
        """Reanuda la ejecución del worker"""
        if self._is_running and self._is_paused:
            self.logger.info(f"Reanudando {self.__class__.__name__}")
            self._is_paused = False
            self.condition.wakeAll()

    def wait_if_paused(self):
        """Espera si el worker está pausado"""
        while self._is_paused and not self._should_stop:
            self.mutex.lock()
            self.condition.wait(self.mutex)
            self.mutex.unlock()

    def check_stopped(self) -> bool:
        """
        Verifica si se ha solicitado la detención

        Returns:
            True si se debe detener la ejecución
        """
        return self._should_stop

    def update_progress(self, value: int):
        """
        Actualiza el progreso del worker

        Args:
            value: Valor de progreso (0-100)
        """
        self.progress_updated.emit(max(0, min(100, value)))

    @property
    def is_running(self) -> bool:
        """Indica si el worker está ejecutándose"""
        return self._is_running

    @property
    def is_paused(self) -> bool:
        """Indica si el worker está pausado"""
        return self._is_paused

    @property
    def result(self) -> Optional[Any]:
        """Retorna el resultado de la ejecución"""
        return self._result

    @property
    def error(self) -> Optional[str]:
        """Retorna el error ocurrido"""
        return self._error

    @property
    def was_successful(self) -> bool:
        """Indica si la ejecución fue exitosa"""
        return self._result is not None and self._error is None
