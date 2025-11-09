#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List

from PySide6.QtCore import QObject, QThread

from utils.logger import get_logger


class ThreadManager(QObject):
    """Gestiona todos los hilos y workers de la aplicación"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger("ThreadManager")

        # Registro de hilos y workers
        self._threads: Dict[str, QThread] = {}
        self._workers: Dict[str, QObject] = {}

        self.logger.info("ThreadManager inicializado")

    def register_worker(self, name: str, worker: QObject, thread: QThread = None):
        """Registra un worker con su hilo"""
        try:
            if thread is None:
                thread = QThread()

            # Mover worker al hilo
            worker.moveToThread(thread)

            # Conectar señales del hilo
            thread.started.connect(worker.run)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)

            # Guardar referencias
            self._threads[name] = thread
            self._workers[name] = worker

            self.logger.info(f"Worker '{name}' registrado correctamente")

        except Exception as e:
            self.logger.error(f"Error registrando worker '{name}': {str(e)}")

    def start_worker(self, name: str):
        """Inicia un worker"""
        if name in self._threads:
            thread = self._threads[name]
            if not thread.isRunning():
                thread.start()
                self.logger.info(f"Worker '{name}' iniciado")
            else:
                self.logger.warning(f"Worker '{name}' ya está ejecutándose")
        else:
            self.logger.error(f"Worker '{name}' no encontrado")

    def stop_worker(self, name: str):
        """Detiene un worker de forma segura"""
        if name in self._workers:
            worker = self._workers[name]
            if hasattr(worker, "stop"):
                worker.stop()

            # Esperar a que termine
            if name in self._threads:
                thread = self._threads[name]
                if thread.isRunning():
                    thread.quit()
                    if not thread.wait(3000):  # Esperar 3 segundos
                        thread.terminate()
                        thread.wait(1000)

            self.logger.info(f"Worker '{name}' detenido")

    def stop_all_workers(self):
        """Detiene todos los workers de forma segura"""
        self.logger.info("Deteniendo todos los workers...")

        for name in list(self._workers.keys()):
            self.stop_worker(name)

        # Limpiar registros
        self._threads.clear()
        self._workers.clear()

        self.logger.info("Todos los workers detenidos")

    def get_worker(self, name: str) -> QObject:
        """Obtiene un worker por nombre"""
        return self._workers.get(name)

    def is_worker_running(self, name: str) -> bool:
        """Verifica si un worker está ejecutándose"""
        if name in self._threads:
            return self._threads[name].isRunning()
        return False

    def __del__(self):
        """Destructor - asegura que todos los hilos se detengan"""
        self.stop_all_workers()
