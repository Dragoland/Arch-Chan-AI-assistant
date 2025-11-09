#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Optional

from PySide6.QtCore import QObject, Signal, Slot

from utils.logger import get_logger


class BaseWorker(QObject):
    """
    Clase base para todos los workers (Patrón moveToThread)
    Hereda de QObject, no de QThread.
    """

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
        self._should_stop = False

        # Resultados
        self._result: Optional[Any] = None
        self._error: Optional[str] = None

        # Configurar para eliminación segura
        self.setObjectName(f"{self.__class__.__name__}_{id(self)}")

        self.logger.debug(f"{self.__class__.__name__} inicializado")

    @Slot()
    def run(self):
        """Método principal del worker (ahora es un Slot)"""
        if self._is_running:
            self.logger.warning(
                f"Worker {self.__class__.__name__} ya está en ejecución"
            )
            return

        try:
            self._is_running = True
            self._should_stop = False
            self.started.emit()

            self.logger.info(f"Iniciando worker {self.__class__.__name__}")

            # Ejecutar la tarea principal
            self._result = self._execute()

            if self._should_stop:
                self.logger.info(
                    f"Worker {self.__class__.__name__} detenido por solicitud"
                )
                self._result = {"status": "cancelled"}
            else:
                self.logger.info(f"Worker {self.__class__.__name__} completado")

        except Exception as e:
            error_msg = f"Error en worker {self.__class__.__name__}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._error = error_msg
            self._result = {"status": "error", "error": error_msg}
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

    @Slot()
    def stop(self):
        """Solicita la detención del worker (ahora es un Slot)"""
        if self._is_running:
            self.logger.info(f"Solicitando detención de {self.__class__.__name__}")
            self._should_stop = True

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
    def result(self) -> Optional[Any]:
        """Retorna el resultado de la ejecución"""
        return self._result

    @property
    def error(self) -> Optional[str]:
        """Retorna el error ocurrido"""
        return self._error

    def safe_delete(self):
        """Eliminación segura del worker"""
        try:
            if self._is_running:
                self.stop()
            # Desconectar todas las señales
            self.disconnect()
        except Exception as e:
            self.logger.debug(f"Error en safe_delete: {str(e)}")
