#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from core.config_manager import ConfigManager
from core.dependency_checker import DependencyChecker, DependencyError
from core.state_manager import AppState, AppStateManager
from services.ollama_client import OllamaClient
from services.system_monitor import SystemMonitor
from ui.main_window import MainWindow
from utils.constants import CONFIGS_PATH, LOGS_DIR, MODELS_DIR, PROJECT_DIR, TEMP_DIR
from utils.file_utils import FileUtils
from utils.logger import get_logger


class ArchChanApplication(QObject):
    """Clase principal de la aplicación que coordina todos los módulos"""

    # Señales de la aplicación
    app_initialized = Signal()
    app_shutdown = Signal()
    error_occurred = Signal(str)
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.logger = get_logger("ArchChanApplication")

        # Componentes principales
        self.config_manager: Optional[ConfigManager] = None
        self.state_manager: Optional[AppStateManager] = None
        self.main_window: Optional[MainWindow] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.ollama_client: Optional[OllamaClient] = None

        # Hilos
        self.system_monitor_thread: Optional[QThread] = None

        # Datos
        self.available_models: List[Dict[str, Any]] = []

        # Estado de la aplicación
        self._is_initialized = False
        self._shutdown_requested = False

        self.logger.info("ArchChanApplication instanciada")

    def start(self) -> bool:
        """
        Inicializa y arranca la aplicación

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info("Iniciando Arch-Chan AI Assistant v2.1.0...")

            # 1. Inicializar componentes core PRIMERO
            if not self._initialize_core_components():
                return False

            # 2. Verificar dependencias
            if not self._check_dependencies():
                return False

            # 3. Inicializar servicios
            if not self._initialize_services():
                return False

            # 4. Inicializar UI
            if not self._initialize_ui():
                return False

            # 5. Conectar señales
            self._connect_signals()

            # 6. Verificar estado final
            if not self._finalize_initialization():
                return False

            self._is_initialized = True
            if self.state_manager:
                self.state_manager.set_idle("Aplicación lista")
            self.logger.info("Aplicación inicializada correctamente")
            self.app_initialized.emit()

            return True

        except Exception as e:
            error_msg = f"Error durante el inicio: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._handle_error(error_msg, "Error de inicialización")
            return False

    def _initialize_core_components(self) -> bool:
        """Inicializa los componentes core de la aplicación"""
        try:
            self.logger.info("Inicializando componentes core...")

            # Inicializar state_manager PRIMERO para poder usarlo
            self.state_manager = AppStateManager()
            self.logger.info("AppStateManager inicializado")

            # Configuración
            self.config_manager = ConfigManager()
            self.logger.info("ConfigManager inicializado")

            # Crear directorios necesarios (ahora usando FileUtils)
            self._create_application_directories()

            # Ahora podemos usar state_manager para establecer estado
            if self.state_manager:
                self.state_manager.set_starting("Inicializando componentes core...")

            return True

        except Exception as e:
            error_msg = f"Error inicializando componentes core: {str(e)}"
            self.logger.error(error_msg)
            self._handle_error(error_msg, "Error de componentes core")
            return False

    def _create_application_directories(self):
        """Crea los directorios necesarios para la aplicación"""
        self.logger.info("Creando directorios de la aplicación...")

        # Usar constantes y FileUtils
        directories = [PROJECT_DIR, MODELS_DIR, TEMP_DIR, LOGS_DIR]

        for directory in directories:
            try:
                FileUtils.ensure_directory(str(directory))
                self.logger.debug(f"Directorio verificado/creado: {directory}")
            except Exception as e:
                self.logger.error(f"Error creando directorio {directory}: {str(e)}")

        # Manejar CONFIGS_PATH por separado si está definido
        if "CONFIGS_PATH" in globals():
            try:
                FileUtils.ensure_directory(str(CONFIGS_PATH))
            except Exception as e:
                self.logger.error(f"Error creando CONFIGS_PATH: {str(e)}")

    def _check_dependencies(self) -> bool:
        """Verifica las dependencias del sistema"""
        try:
            self.logger.info("Verificando dependencias del sistema...")
            if self.state_manager:
                self.state_manager.set_status_message("Verificando dependencias...")

            checker = DependencyChecker()
            checker.check_all_dependencies()

            # Verificar requisitos del sistema
            requirements = checker.check_system_requirements()
            for req, met in requirements.items():
                if not met:
                    self.logger.warning(f"Requisito no cumplido: {req}")

            self.logger.info("Todas las dependencias verificadas correctamente")
            return True

        except DependencyError as e:
            error_msg = f"Dependencias faltantes: {str(e)}"
            self.logger.error(error_msg)
            self._handle_error(error_msg, "Dependencias faltantes")

            # Mostrar diálogo de error
            self._show_error_dialog(
                "Dependencias Faltantes",
                f"Faltan las siguientes dependencias:\n\n{str(e)}\n\n"
                "Por favor, instala las dependencias necesarias y reinicia la aplicación.",
            )
            return False

        except Exception as e:
            error_msg = f"Error verificando dependencias: {str(e)}"
            self.logger.error(error_msg)
            self._handle_error(error_msg, "Error de dependencias")
            return False

    def _initialize_services(self) -> bool:
        """Inicializa los servicios en segundo plano"""
        try:
            self.logger.info("Inicializando servicios...")
            if self.state_manager:
                self.state_manager.set_status_message("Inicializando servicios...")

            # Cliente Ollama con diagnóstico mejorado
            self.ollama_client = OllamaClient()

            # Realizar diagnóstico primero
            diagnostic = self.ollama_client.diagnostic_check()
            self.logger.info(f"Diagnóstico de Ollama: {diagnostic}")

            if not diagnostic["api_health"]:
                self.logger.warning(
                    "Ollama no está disponible, continuando en modo offline"
                )
                self.available_models = []
            else:
                self.logger.info("OllamaClient inicializado correctamente")
                # Cargar modelos disponibles
                self.available_models = self.ollama_client.list_models() or []
                if self.available_models:
                    self.logger.info(
                        f"Modelos disponibles: {len(self.available_models)}"
                    )
                else:
                    self.logger.warning("No se encontraron modelos en Ollama")
                    self.available_models = []

            # Monitoreo del sistema (Patrón moveToThread)
            self.system_monitor = SystemMonitor()
            self.system_monitor_thread = QThread()
            self.system_monitor.moveToThread(self.system_monitor_thread)

            # Conectar señales del hilo
            self.system_monitor_thread.started.connect(self.system_monitor.run)
            self.system_monitor.finished.connect(self.system_monitor_thread.quit)
            self.system_monitor.finished.connect(self.system_monitor.deleteLater)
            self.system_monitor_thread.finished.connect(
                self.system_monitor_thread.deleteLater
            )

            # Iniciar hilo
            self.system_monitor_thread.start()
            self.logger.info("SystemMonitor inicializado y movido a hilo")

            return True

        except Exception as e:
            error_msg = f"Error inicializando servicios: {str(e)}"
            self.logger.error(error_msg)
            self._handle_error(error_msg, "Error de servicios")
            return False

    def _initialize_ui(self) -> bool:
        """Inicializa la interfaz de usuario"""
        try:
            self.logger.info("Inicializando interfaz de usuario...")
            if self.state_manager:
                self.state_manager.set_status_message("Inicializando interfaz...")

            app = QApplication.instance()
            if not app:
                self.logger.error("No se encontró instancia de QApplication")
                return False

            self.main_window = MainWindow(
                config_manager=self.config_manager, state_manager=self.state_manager
            )

            if self.ollama_client:
                self.main_window.set_ollama_client(self.ollama_client)

            if hasattr(self.main_window, "set_available_models"):
                self.main_window.set_available_models(self.available_models)

            self.main_window.show()
            self.logger.info("Interfaz de usuario inicializada correctamente")
            return True

        except Exception as e:
            error_msg = f"Error inicializando interfaz de usuario: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._handle_error(error_msg, "Error de interfaz")
            return False

    def _connect_signals(self):
        """Conecta las señales entre componentes"""
        try:
            self.logger.info("Conectando señales entre componentes...")

            if self.state_manager:
                self.state_manager.state_changed.connect(self._on_state_changed)
                self.state_manager.error_occurred.connect(self._on_error_occurred)

            if self.main_window:
                self.main_window.shutdown_requested.connect(self.shutdown)

                # Conectar SystemMonitor al SidePanel
                if (
                    self.system_monitor
                    and hasattr(self.main_window, "side_panel")
                    and self.main_window.side_panel
                ):

                    self.system_monitor.system_updated.connect(
                        self.main_window.side_panel.update_system_info
                    )

                    self.system_monitor.health_status_changed.connect(
                        self.main_window.side_panel.update_health_status
                    )

                    self.logger.info("SystemMonitor conectado al SidePanel")

                # Conectar SystemMonitor al StatusBar
                if (
                    self.system_monitor
                    and hasattr(self.main_window, "status_bar")
                    and self.main_window.status_bar
                ):

                    self.system_monitor.system_updated.connect(
                        self.main_window.status_bar.update_performance_metrics
                    )

                    self.system_monitor.ollama_status_changed.connect(
                        lambda status: self.main_window.status_bar.update_connection_status(
                            status, "Ollama"
                        )
                    )

                    self.logger.info("SystemMonitor conectado al StatusBar")

            self.error_occurred.connect(self._on_global_error)
            self.logger.info("Todas las señales conectadas correctamente")

        except Exception as e:
            self.logger.error(f"Error conectando señales: {str(e)}")

    def _finalize_initialization(self) -> bool:
        """Completa la inicialización de la aplicación"""
        try:
            self.logger.info("Finalizando inicialización...")
            if self.state_manager:
                self.state_manager.set_status_message("Finalizando inicialización...")

            components_ready = all(
                [
                    self.config_manager is not None,
                    self.state_manager is not None,
                    self.main_window is not None,
                ]
            )

            if not components_ready:
                self.logger.error(
                    "No todos los componentes se inicializaron correctamente"
                )
                return False

            self.logger.info("Inicialización completada correctamente")
            return True

        except Exception as e:
            self.logger.error(f"Error finalizando inicialización: {str(e)}")
            return False

    def _on_state_changed(self, old_state: AppState, new_state: AppState):
        """Maneja cambios de estado"""
        self.logger.debug(f"Estado cambiado: {old_state.value} -> {new_state.value}")
        # Propagar cambio de estado a la ventana principal
        if self.main_window:
            self.main_window._on_state_changed(old_state.value, new_state.value)

    def _on_error_occurred(self, error_message: str):
        """Maneja errores del estado manager"""
        self.logger.error(f"Error del estado manager: {error_message}")
        self._show_error_dialog("Error de Aplicación", error_message)

    def _on_global_error(self, error_message: str):
        """Maneja errores globales"""
        self.logger.error(f"Error global: {error_message}")
        self._handle_error(error_message, "Error global")

    def _handle_error(self, error_message: str, context: str = ""):
        """Maneja errores de forma segura, incluso si state_manager no está disponible"""
        try:
            self.logger.error(f"Error ({context}): {error_message}")
            if self.state_manager:
                self.state_manager.set_error(error_message, context)
            else:
                self.error_occurred.emit(error_message)
        except Exception as e:
            self.logger.error(f"Error crítico en manejo de errores: {str(e)}")
            self.logger.error(f"Error original ({context}): {error_message}")

    def _show_error_dialog(self, title: str, message: str):
        """Muestra un diálogo de error"""
        try:
            app = QApplication.instance()
            if app:
                QMessageBox.critical(None, title, message)
        except Exception as e:
            self.logger.error(f"Error mostrando diálogo: {str(e)}")

    def shutdown(self):
        """Apaga la aplicación de forma ordenada"""
        if self._shutdown_requested:
            return
        self._shutdown_requested = True
        self.logger.info("Iniciando apagado ordenado de la aplicación...")

        if self.state_manager:
            self.state_manager.set_shutting_down("Apagando aplicación...")

        self.app_shutdown.emit()

        try:
            # Detener servicios
            if self.system_monitor:
                self.system_monitor.stop()
            if self.system_monitor_thread:
                self.system_monitor_thread.quit()
                self.system_monitor_thread.wait(2000)

            # Guardar configuración
            if self.config_manager:
                self.config_manager.save_config()

            # Cerrar ventana principal (ya se maneja por el evento close)
            if self.main_window:
                self.main_window.close()

            self.logger.info("Aplicación cerrada correctamente")

        except Exception as e:
            self.logger.error(f"Error durante el apagado: {str(e)}")

    def restart(self):
        """Reinicia la aplicación"""
        self.logger.info("Reiniciando aplicación...")
        self.shutdown()
        QTimer.singleShot(1000, self._perform_restart)

    def _perform_restart(self):
        """Ejecuta el reinicio de la aplicación"""
        try:
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            self.logger.error(f"Error reiniciando aplicación: {str(e)}")
            # Intentar reiniciar sin execl
            self.start()

    def is_initialized(self) -> bool:
        """Verifica si la aplicación está inicializada"""
        return self._is_initialized
