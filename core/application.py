#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from core.config_manager import ConfigManager
from core.dependency_checker import DependencyChecker
from core.state_manager import AppStateManager
from services.system_monitor import SystemMonitor
from ui.main_window import MainWindow
from utils.logger import get_logger


class ArchChanApplication(QObject):
    """Clase principal de la aplicación que coordina todos los módulos"""

    # Señales de la aplicación
    app_initialized = Signal()
    app_shutdown = Signal()
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.logger = get_logger("ArchChanApplication")
        self.config_manager = None
        self.main_window = None
        self.system_monitor = None
        self.state_manager = None

    def start(self):
        """Inicializa y arranca la aplicación"""
        try:
            self.logger.info("Iniciando Arch-Chan AI Assistant v2.1.0...")

            # 1. Inicializar componentes core
            self._initialize_core_components()

            # 2. Verificar dependencias
            self._check_dependencies()

            # 3. Inicializar UI
            self._initialize_ui()

            # 4. Inicializar servicios
            self._initialize_services()

            # 5. Conectar señales
            self._connect_signals()

            self.logger.info("Aplicación inicializada correctamente")
            self.app_initialized.emit()

        except Exception as e:
            self.logger.error(f"Error durante el inicio: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
            raise

    def _initialize_core_components(self):
        """Inicializa los componentes core de la aplicación"""
        self.logger.info("Inicializando componentes core...")
        self.config_manager = ConfigManager()
        self.state_manager = AppStateManager()

        # Crear directorios necesarios
        self._create_application_directories()

    def _create_application_directories(self):
        """Crea los directorios necesarios para la aplicación"""
        self.logger.info("Creando directorios de la aplicación...")
        directories = [
            self.config_manager.project_path,
            self.config_manager.models_path,
            self.config_manager.temp_path,
            self.config_manager.logs_path,
            self.config_manager.configs_path,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directorio verificado/creado: {directory}")

    def _check_dependencies(self):
        """Verifica las dependencias del sistema"""
        self.logger.info("Verificando dependencias del sistema...")
        checker = DependencyChecker()
        checker.check_all_dependencies()
        self.logger.info("Todas las dependencias verificadas correctamente")

    def _initialize_ui(self):
        """Inicializa la interfaz de usuario"""
        self.logger.info("Inicializando interfaz de usuario...")
        self.main_window = MainWindow(
            config_manager=self.config_manager, state_manager=self.state_manager
        )
        self.main_window.show()
        self.logger.info("Interfaz de usuario inicializada correctamente")

    def _initialize_services(self):
        """Inicializa los servicios en segundo plano"""
        self.logger.info("Inicializando servicios...")

        # Monitoreo del sistema
        self.system_monitor = SystemMonitor()
        self.system_monitor.start()

        # Conectar señales del monitor del sistema a la UI
        if (
            self.main_window
            and hasattr(self.main_window, "side_panel")
            and self.main_window.side_panel
        ):

            try:
                self.system_monitor.system_updated.connect(
                    self.main_window.side_panel.update_system_info
                )
                self.logger.info("Sistema de monitoreo conectado al panel lateral")
            except Exception as e:
                self.logger.warning(f"No se pudo conectar el monitor del sistema: {e}")

    def _connect_signals(self):
        """Conecta las señales entre componentes"""
        self.logger.info("Conectando señales entre componentes...")

        if self.main_window:
            if hasattr(self.main_window, "shutdown_requested"):
                self.main_window.shutdown_requested.connect(self.shutdown)

        self.error_occurred.connect(self._handle_error)

    def shutdown(self):
        """Apaga la aplicación de forma ordenada"""
        self.logger.info("Iniciando apagado ordenado de la aplicación...")
        self.app_shutdown.emit()

        # Detener servicios
        if self.system_monitor:
            self.system_monitor.stop()

        # Cerrar ventana principal
        if self.main_window:
            self.main_window.close()

        # Guardar configuración
        if self.config_manager:
            self.config_manager.save_config()

        self.logger.info("Aplicación cerrada correctamente")

    def _handle_error(self, error_message):
        """Maneja errores de la aplicación"""
        self.logger.error(f"Error de aplicación: {error_message}")

        # Podría mostrar un diálogo de error aquí
        try:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                None, "Error de Aplicación", f"Se produjo un error:\n\n{error_message}"
            )
        except:
            pass

    def restart(self):
        """Reinicia la aplicación"""
        self.logger.info("Reiniciando aplicación...")
        self.shutdown()

        # Usar un timer para reiniciar después de que se complete el shutdown
        QTimer.singleShot(1000, self.start)
