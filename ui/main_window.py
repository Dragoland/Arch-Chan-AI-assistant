#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ventana principal completamente reescrita de Arch-Chan
Con mejoras de rendimiento, nuevos temas y correcciones integrales
"""

import random

import psutil
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from services.system_monitor import SystemMonitor
from ui.components.chat_panel import ChatPanel
from ui.components.side_panel import SidePanel
from ui.components.status_bar import StatusBar
from ui.components.toolbar import MainToolbar
from ui.themes.arch_theme import ArchLinuxTheme
from utils.logger import get_logger
from workers.chat_worker import ChatWorker
from workers.thread_manager import ThreadManager
from workers.voice_worker import VoiceWorker


class MainWindow(QMainWindow):
    """Ventana principal rediseñada con mejoras de rendimiento y nuevos temas"""

    shutdown_requested = Signal()
    theme_changed = Signal(str)
    model_changed = Signal(str)
    performance_metrics_updated = Signal(dict)

    def __init__(self, config_manager, state_manager):
        super().__init__()
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("MainWindow")
        self.thread_manager = ThreadManager()

        # Componentes UI
        self.toolbar = None
        self.chat_panel = None
        self.side_panel = None
        self.status_bar = None
        self.ollama_client = None  # Inicializar como None

        # Estado de la interfaz
        self.side_panel_collapsed = False
        self.current_theme = "arch-dark"
        self.performance_data = {}

        # Timers para actualizaciones
        self.performance_timer = QTimer()
        self.ui_update_timer = QTimer()

        self._setup_window()
        self._create_ui()
        self._apply_theme()
        self._connect_signals()
        self._setup_timers()

        self.logger.info("MainWindow inicializada correctamente con mejoras v2.1")

    def debug_signal_connections(self):
        """Diagnóstico de conexiones de señales - para debugging"""
        try:
            self.logger.info("=== DIAGNÓSTICO DE CONEXIONES DE SEÑALES ===")

            # Verificar toolbar
            if self.toolbar:
                self.logger.info(
                    f"Toolbar - performance_toggled existe: {hasattr(self.toolbar, 'performance_toggled')}"
                )
                if hasattr(self.toolbar, "performance_toggled"):
                    # Verificar si la señal está conectada
                    connections = self.toolbar.performance_toggled.receivers()
                    self.logger.info(
                        f"Toolbar - Conexiones a performance_toggled: {connections}"
                    )

            # Verificar side panel
            if self.side_panel:
                self.logger.info(
                    f"SidePanel - performance_toggled existe: {hasattr(self.side_panel, 'performance_toggled')}"
                )
                if hasattr(self.side_panel, "performance_toggled"):
                    connections = self.side_panel.performance_toggled.receivers()
                    self.logger.info(
                        f"SidePanel - Conexiones a performance_toggled: {connections}"
                    )

            # Verificar nuestro slot
            self.logger.info(
                f"MainWindow - _on_performance_toggled existe: {hasattr(self, '_on_performance_toggled')}"
            )

        except Exception as e:
            self.logger.error(f"Error en diagnóstico de señales: {e}")

    def setup_workers(self):
        """Configura todos los workers"""
        # Chat worker
        chat_worker = ChatWorker([], "", "llama2")
        self.thread_manager.register_worker("chat", chat_worker)

        # Voice worker
        voice_worker = VoiceWorker()
        self.thread_manager.register_worker("voice", voice_worker)

        # System monitor
        system_monitor = SystemMonitor()
        self.thread_manager.register_worker("system_monitor", system_monitor)

    def closeEvent(self, event):
        """Maneja el cierre de la aplicación de forma segura"""
        self.thread_manager.stop_all_workers()
        event.accept()

    def set_ollama_client(self, ollama_client):
        """Establece el cliente de Ollama"""
        self.ollama_client = ollama_client
        # Propagarlo a los componentes que lo necesiten
        if self.chat_panel and hasattr(self.chat_panel, "set_ollama_client"):
            self.chat_panel.set_ollama_client(ollama_client)

    def _setup_window(self):
        """Configuración avanzada de la ventana principal"""
        self.setWindowTitle("Arch-Chan AI Assistant v2.1.0 - Native Arch Linux")
        self.setGeometry(150, 100, 1400, 900)
        self.setMinimumSize(1100, 750)

        # Configuración de la ventana
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setDockNestingEnabled(True)

    def _create_ui(self):
        """Crea la interfaz de usuario con layout mejorado"""
        # Widget central con mejoras de rendimiento
        central_widget = QWidget()
        central_widget.setObjectName("main_central_widget")
        self.setCentralWidget(central_widget)

        # Layout principal con márgenes optimizados
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)

        try:
            # Crear componentes con gestión de errores mejorada
            self.side_panel = SidePanel(self.config_manager, self.state_manager)
            self.chat_panel = ChatPanel(self.config_manager, self.state_manager)
            self.toolbar = MainToolbar(self.config_manager, self.state_manager)
            self.status_bar = StatusBar(self.config_manager, self.state_manager)

            # Configurar proporciones responsivas
            self.main_layout.addWidget(self.side_panel, 1)  # 25% del ancho
            self.main_layout.addWidget(self.chat_panel, 3)  # 75% del ancho

            # Configurar barra de herramientas y estado
            self.addToolBar(Qt.TopToolBarArea, self.toolbar)
            self.setStatusBar(self.status_bar)

            # Aplicar estilos iniciales
            self._apply_component_styles()

        except Exception as e:
            self.logger.error(f"Error crítico creando componentes UI: {e}")
            QMessageBox.critical(
                self,
                "Error de Inicialización",
                f"No se pudieron cargar los componentes de la interfaz:\n\n{str(e)}",
            )
            raise

    def _apply_theme(self):
        """Aplica el tema actual con soporte para nuevos temas"""
        try:
            self.current_theme = self.config_manager.get("UI", "theme", "arch-dark")
            stylesheet = ArchLinuxTheme.get_stylesheet(self.current_theme)
            self.setStyleSheet(stylesheet)

            # Actualizar componentes individuales
            if self.chat_panel:
                self.chat_panel.on_theme_changed(self.current_theme)
            if self.side_panel:
                self.side_panel.on_theme_changed(self.current_theme)

            self.logger.info(f"Tema aplicado exitosamente: {self.current_theme}")

        except Exception as e:
            self.logger.error(f"Error aplicando tema {self.current_theme}: {e}")
            # Fallback a tema por defecto
            try:
                fallback_stylesheet = ArchLinuxTheme.get_stylesheet("arch-dark")
                self.setStyleSheet(fallback_stylesheet)
            except Exception as fallback_error:
                self.logger.error(f"Error incluso con tema fallback: {fallback_error}")

    def _apply_component_styles(self):
        """Aplica estilos específicos a componentes individuales"""
        try:
            # Configurar propiedades visuales específicas
            self.setProperty("class", "main_window")
            self.centralWidget().setProperty("class", "central_widget")

        except Exception as e:
            self.logger.debug(f"Error aplicando estilos de componentes: {e}")

    def _connect_signals(self):
        """Conexión completa y robusta de todas las señales"""

        from PySide6.QtCore import QTimer

        QTimer.singleShot(100, self.debug_signal_connections)

        try:
            # Conexiones del toolbar
            if self.toolbar:
                self.toolbar.voice_action_triggered.connect(self._on_voice_action)
                self.toolbar.clear_chat_triggered.connect(self._on_clear_chat)
                self.toolbar.config_action_triggered.connect(self._show_config_dialog)
                self.toolbar.stop_action_triggered.connect(self._on_stop_action)
                self.toolbar.theme_changed.connect(self._on_theme_changed)
                self.toolbar.model_changed.connect(self._on_model_changed)
                if hasattr(self.toolbar, "performance_toggled"):
                    self.toolbar.performance_toggled.connect(
                        lambda enabled: self._on_performance_toggled(enabled)
                    )

            # Conexiones del side panel
            if self.side_panel:
                self.side_panel.voice_action_triggered.connect(self._on_voice_action)
                self.side_panel.clear_chat_triggered.connect(self._on_clear_chat)
                self.side_panel.config_action_triggered.connect(
                    self._show_config_dialog
                )
                self.side_panel.stop_action_triggered.connect(self._on_stop_action)
                self.side_panel.toggle_panel_triggered.connect(self._toggle_side_panel)
                if hasattr(self.side_panel, "performance_toggled"):
                    self.side_panel.performance_toggled.connect(
                        lambda enabled: self._on_performance_toggled(enabled)
                    )

            # Conexiones del chat panel
            if self.chat_panel:
                self.chat_panel.model_changed.connect(self._on_model_changed)
                self.chat_panel.theme_change_requested.connect(
                    self._on_theme_change_requested
                )
                self.chat_panel.performance_metrics_updated.connect(
                    self._on_performance_metrics_updated
                )

            # Conexiones del state manager
            if self.state_manager:
                if hasattr(self.state_manager, "state_changed"):
                    self.state_manager.state_changed.connect(self._on_state_changed)
                if hasattr(self.state_manager, "error_occurred"):
                    self.state_manager.error_occurred.connect(self._on_error_occurred)
                if hasattr(self.state_manager, "performance_updated"):
                    self.state_manager.performance_updated.connect(
                        self._on_performance_updated
                    )

            # Conexiones de la barra de estado
            if self.status_bar:
                self.performance_metrics_updated.connect(
                    self.status_bar.update_performance_metrics
                )

            self.logger.info("Todas las señales conectadas exitosamente")

        except Exception as e:
            self.logger.error(f"Error conectando señales: {e}")

    def _setup_timers(self):
        """Configura los timers para actualizaciones automáticas"""
        # Timer para métricas de rendimiento
        self.performance_timer.timeout.connect(self._update_performance_metrics)
        self.performance_timer.start(2000)  # Actualizar cada 2 segundos

        # Timer para actualizaciones de UI
        self.ui_update_timer.timeout.connect(self._update_ui_elements)
        self.ui_update_timer.start(1000)  # Actualizar cada segundo

    def _update_performance_metrics(self):
        """Actualiza las métricas de rendimiento del sistema"""
        try:
            # Obtener métricas reales del sistema
            metrics = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_gb": psutil.virtual_memory().used / (1024**3),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_percent": psutil.disk_usage("/").percent,
                "disk_used_gb": psutil.disk_usage("/").used / (1024**3),
                "disk_total_gb": psutil.disk_usage("/").total / (1024**3),
                "temperature": self._get_cpu_temperature(),
                "ollama_running": self._check_ollama_running(),
            }

            self.performance_data = metrics
            self.performance_metrics_updated.emit(metrics)

            # Actualizar side panel si existe
            if self.side_panel and hasattr(self.side_panel, "update_system_info"):
                self.side_panel.update_system_info(metrics)

        except Exception as e:
            self.logger.debug(f"Error actualizando métricas de rendimiento: {e}")

    def _get_cpu_temperature(self):
        """Obtiene la temperatura de la CPU si está disponible"""
        try:
            # Intentar obtener temperatura en sistemas Linux
            import os

            if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp = int(f.read().strip()) / 1000.0
                    return temp
        except:
            pass
        return None

    def _check_ollama_running(self):
        """Verifica si Ollama está ejecutándose"""
        try:
            if self.ollama_client and hasattr(self.ollama_client, "is_running"):
                return self.ollama_client.is_running()

            # Verificar por proceso
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] and "ollama" in proc.info["name"].lower():
                    return True
            return False
        except:
            return False

    def _update_ui_elements(self):
        """Actualiza elementos de la UI que necesitan refresco frecuente"""
        try:
            # Actualizar hora en la barra de estado
            if self.status_bar:
                self.status_bar._update_time()

            # Actualizar información de sesión en side panel
            if self.side_panel and hasattr(self.side_panel, "_update_uptime"):
                self.side_panel._update_uptime()

        except Exception as e:
            self.logger.debug(f"Error actualizando elementos UI: {e}")

    def _on_voice_action(self):
        """Maneja la acción de voz con mejor manejo de estado"""
        try:
            if self.chat_panel:
                self.chat_panel.start_voice_flow()
                self.logger.info("Flujo de voz iniciado desde la interfaz")
        except Exception as e:
            self.logger.error(f"Error iniciando flujo de voz: {e}")
            self._show_error_dialog(
                "Error de Voz", "No se pudo iniciar el reconocimiento de voz"
            )

    def _on_clear_chat(self):
        """Maneja la limpieza del chat con confirmación"""
        try:
            reply = QMessageBox.question(
                self,
                "Confirmar Limpieza",
                "¿Estás seguro de que quieres limpiar todo el historial del chat?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.chat_panel:
                    self.chat_panel.clear_chat()
                    self.logger.info("Chat limpiado por el usuario")
        except Exception as e:
            self.logger.error(f"Error limpiando chat: {e}")

    def _on_stop_action(self):
        """Maneja la acción de detener procesos en ejecución"""
        try:
            if self.chat_panel and hasattr(self.chat_panel, "stop_generation"):
                self.chat_panel.stop_generation()
                self.logger.info("Generación detenida por el usuario")
        except Exception as e:
            self.logger.error(f"Error enviando señal de detención: {e}")

    def _toggle_side_panel(self):
        """Alterna la visibilidad del panel lateral con animación"""
        self.side_panel_collapsed = not self.side_panel_collapsed

        # Animación suave de transición
        if self.side_panel_collapsed:
            self.side_panel.setVisible(False)
            self.main_layout.setStretchFactor(self.side_panel, 0)
            self.main_layout.setStretchFactor(self.chat_panel, 1)
        else:
            self.side_panel.setVisible(True)
            self.main_layout.setStretchFactor(self.side_panel, 1)
            self.main_layout.setStretchFactor(self.chat_panel, 3)

        # Actualizar botón de colapsar
        if self.side_panel and hasattr(self.side_panel, "toggle_collapse_button"):
            self.side_panel.toggle_collapse_button(self.side_panel_collapsed)

        self.logger.info(
            f"Panel lateral {'colapsado' if self.side_panel_collapsed else 'expandido'}"
        )

    def _on_model_changed(self, model_name):
        """Maneja el cambio de modelo con actualización completa"""
        try:
            self.model_changed.emit(model_name)
            self.config_manager.set("General", "model", model_name)
            self.config_manager.save_config()

            # Actualizar todos los componentes
            if self.status_bar:
                self.status_bar.update_model_info(model_name)

            if self.side_panel:
                message_count = (
                    len(self.chat_panel.chat_history)
                    if hasattr(self.chat_panel, "chat_history")
                    else 0
                )
                self.side_panel.update_session_info(model_name, message_count)

            if self.chat_panel:
                self.chat_panel.on_model_changed(model_name)

            self.logger.info(f"Modelo cambiado exitosamente a: {model_name}")

        except Exception as e:
            self.logger.error(f"Error cambiando modelo a {model_name}: {e}")
            self._show_error_dialog(
                "Error de Modelo", f"No se pudo cambiar al modelo {model_name}"
            )

    def _on_theme_changed(self, theme_name):
        """Maneja el cambio de tema desde el toolbar"""
        self._on_theme_change_requested(theme_name)

    def _on_theme_change_requested(self, theme_name):
        """Maneja la solicitud de cambio de tema con validación"""
        try:
            available_themes = ArchLinuxTheme.get_available_themes()
            if theme_name not in available_themes:
                self.logger.warning(f"Tema no disponible: {theme_name}")
                theme_name = "arch-dark"  # Fallback al tema por defecto

            self.theme_changed.emit(theme_name)
            self.config_manager.set("UI", "theme", theme_name)
            self.config_manager.save_config()
            self.logger.info(f"Tema cambiado exitosamente a: {theme_name}")

            # Re-aplicar el tema
            self._apply_theme()

        except Exception as e:
            self.logger.error(f"Error cambiando tema a {theme_name}: {e}")
            self._show_error_dialog(
                "Error de Tema", f"No se pudo aplicar el tema {theme_name}"
            )

    def _on_state_changed(self, old_state, new_state):
        """Maneja cambios de estado de la aplicación"""
        # CORRECCIÓN: Pasar solo el nuevo estado como string
        components = [self.toolbar, self.chat_panel, self.status_bar]
        for component in components:
            if component and hasattr(component, "update_state"):
                component.update_state(new_state)

    def _on_error_occurred(self, error_message):
        """Maneja errores de la aplicación con diálogo de error"""
        self.logger.error(f"Error en aplicación: {error_message}")
        self._show_error_dialog("Error del Sistema", error_message)

    def _on_performance_toggled(self, enabled):
        """Maneja la activación/desactivación de métricas de rendimiento - MEJORADO"""
        try:
            self.logger.info(
                f"Modo rendimiento: {'activado' if enabled else 'desactivado'}"
            )

            if enabled:
                self.performance_timer.start(2000)  # Actualizar cada 2 segundos
                # Activar métricas adicionales si es necesario
                if hasattr(self, "ui_update_timer"):
                    self.ui_update_timer.start(1000)
                self.logger.info("Métricas de rendimiento activadas")
            else:
                self.performance_timer.stop()
                # No detener el ui_update_timer ya que es necesario para la UI básica
                self.logger.info("Métricas de rendimiento desactivadas")

            # Actualizar estado en componentes si es necesario
            if self.status_bar and hasattr(self.status_bar, "set_performance_mode"):
                self.status_bar.set_performance_mode(enabled)

            # Actualizar también el side_panel y toolbar
            if self.side_panel and hasattr(self.side_panel, "set_performance_mode"):
                self.side_panel.set_performance_mode(enabled)

            if self.toolbar and hasattr(self.toolbar, "set_performance_mode"):
                self.toolbar.set_performance_mode(enabled)

        except Exception as e:
            self.logger.error(f"Error en _on_performance_toggled: {e}")

    def _on_performance_metrics_updated(self, metrics):
        """Maneja actualizaciones de métricas de rendimiento"""
        self.performance_data = metrics

    def _on_performance_updated(self, metrics):
        """Maneja actualizaciones de rendimiento del state manager"""
        self.performance_data.update(metrics)

    def _show_config_dialog(self):
        """Muestra el diálogo de configuración mejorado"""
        try:
            # Importación diferida para evitar importaciones circulares
            from ui.dialogs.config_dialog import ConfigDialog

            dialog = ConfigDialog(self, self.config_manager)

            # Conectar señal si existe
            if hasattr(dialog, "config_updated"):
                dialog.config_updated.connect(self._on_config_updated)

            if dialog.exec():
                self.logger.info("Configuración actualizada desde diálogo")
            else:
                self.logger.info("Diálogo de configuración cancelado")

        except ImportError as e:
            self.logger.error(f"No se pudo importar ConfigDialog: {e}")
            self._show_error_dialog(
                "Error de Configuración",
                "El diálogo de configuración no está disponible en este momento.",
            )
        except Exception as e:
            self.logger.error(f"Error mostrando diálogo de configuración: {e}")
            self._show_error_dialog(
                "Error de Configuración",
                f"No se pudo abrir la configuración:\n\n{str(e)}",
            )

    def _on_config_updated(self):
        """Maneja actualizaciones de configuración"""
        try:
            # Recargar configuración
            self.config_manager.load_config()

            # Aplicar cambios
            self._apply_theme()

            # Notificar a los componentes sobre cambios
            components = [
                self.chat_panel,
                self.side_panel,
                self.status_bar,
                self.toolbar,
            ]
            for component in components:
                if component and hasattr(component, "on_config_changed"):
                    component.on_config_changed()

            self.logger.info(
                "Configuración aplicada exitosamente a todos los componentes"
            )

        except Exception as e:
            self.logger.error(f"Error aplicando configuración actualizada: {e}")

    def _show_error_dialog(self, title, message):
        """Muestra un diálogo de error estandarizado"""
        QMessageBox.critical(self, title, message)

    def add_chat_message(self, sender, message, is_tool=False):
        """Añade un mensaje al chat y actualiza la UI completamente"""
        try:
            if self.chat_panel:
                self.chat_panel.add_chat_message(sender, message, is_tool)

            # Actualizar información de sesión en side panel
            if self.side_panel:
                current_model = self.config_manager.get("General", "model", "arch-chan")
                message_count = (
                    len(self.chat_panel.chat_history)
                    if hasattr(self.chat_panel, "chat_history")
                    else 0
                )
                self.side_panel.update_session_info(current_model, message_count)

        except Exception as e:
            self.logger.error(f"Error añadiendo mensaje al chat: {e}")

    def closeEvent(self, event):
        """Maneja el cierre de la ventana con confirmación"""
        try:
            reply = QMessageBox.question(
                self,
                "Confirmar Salida",
                "¿Estás seguro de que quieres salir de Arch-Chan?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info("Cerrando ventana principal...")
                # Detener timers
                self.performance_timer.stop()
                self.ui_update_timer.stop()
                # Emitir señal de apagado
                self.shutdown_requested.emit()
                event.accept()
            else:
                event.ignore()

        except Exception as e:
            self.logger.error(f"Error durante el cierre: {e}")
            event.accept()

    def get_performance_data(self):
        """Retorna las métricas de rendimiento actuales"""
        return self.performance_data

    def get_current_theme(self):
        """Retorna el tema actual"""
        return self.current_theme
