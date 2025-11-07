#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ui.components.chat_panel import ChatPanel
from ui.components.side_panel import SidePanel
from ui.components.status_bar import StatusBar
from ui.components.toolbar import MainToolbar
from ui.themes.arch_theme import ArchLinuxTheme
from utils.logger import get_logger


class MainWindow(QMainWindow):
    """Ventana principal modularizada de Arch-Chan"""

    # Señales
    shutdown_requested = Signal()
    theme_changed = Signal(str)
    model_changed = Signal(str)

    def __init__(self, config_manager, state_manager):
        super().__init__()
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("MainWindow")

        self.toolbar = None
        self.chat_panel = None
        self.side_panel = None
        self.status_bar = None
        self.side_panel_collapsed = False

        self._setup_window()
        self._create_ui()
        self._apply_theme()
        self._connect_signals()

        self.logger.info("MainWindow inicializada correctamente")

    def _setup_window(self):
        """Configura la ventana principal"""
        self.setWindowTitle("Arch-Chan AI Assistant v2.1.0")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)

    def _create_ui(self):
        """Crea la interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(12)

        # Crear componentes
        try:
            self.side_panel = SidePanel(self.config_manager, self.state_manager)
            self.chat_panel = ChatPanel(self.config_manager, self.state_manager)
            self.toolbar = MainToolbar(self.config_manager, self.state_manager)
            self.status_bar = StatusBar(self.config_manager, self.state_manager)

            # Agregar componentes al layout
            self.main_layout.addWidget(self.side_panel, 1)  # 25% del ancho
            self.main_layout.addWidget(self.chat_panel, 3)  # 75% del ancho

            # Configurar barra de herramientas y estado
            self.addToolBar(self.toolbar)
            self.setStatusBar(self.status_bar)

        except Exception as e:
            self.logger.error(f"Error creando componentes UI: {e}")
            raise

    def _apply_theme(self):
        """Aplica el tema actual a la ventana"""
        try:
            current_theme = self.config_manager.get("UI", "theme", "arch-dark")
            stylesheet = ArchLinuxTheme.get_stylesheet(current_theme)
            self.setStyleSheet(stylesheet)
            self.logger.info(f"Tema aplicado: {current_theme}")
        except Exception as e:
            self.logger.error(f"Error aplicando tema: {e}")

    def _connect_signals(self):
        """Conecta las señales entre componentes - CORREGIDO: Conexiones completas"""
        try:
            # Conectar señales del toolbar
            if self.toolbar:
                self.toolbar.voice_action_triggered.connect(self._on_voice_action)
                self.toolbar.clear_chat_triggered.connect(self._on_clear_chat)
                self.toolbar.config_action_triggered.connect(self._show_config_dialog)
                self.toolbar.stop_action_triggered.connect(self._on_stop_action)
                self.toolbar.theme_changed.connect(self._on_theme_changed)
                self.toolbar.model_changed.connect(self._on_model_changed)

            # Conectar señales del side panel
            if self.side_panel:
                self.side_panel.voice_action_triggered.connect(self._on_voice_action)
                self.side_panel.clear_chat_triggered.connect(self._on_clear_chat)
                self.side_panel.config_action_triggered.connect(
                    self._show_config_dialog
                )
                self.side_panel.stop_action_triggered.connect(self._on_stop_action)
                self.side_panel.toggle_panel_triggered.connect(self._toggle_side_panel)

            # Conectar señales del chat panel
            if self.chat_panel:
                self.chat_panel.model_changed.connect(self._on_model_changed)
                self.chat_panel.theme_change_requested.connect(
                    self._on_theme_change_requested
                )

            # Conectar señales de estado
            if self.state_manager:
                if hasattr(self.state_manager, "state_changed"):
                    self.state_manager.state_changed.connect(self._on_state_changed)
                if hasattr(self.state_manager, "error_occurred"):
                    self.state_manager.error_occurred.connect(self._on_error_occurred)

        except Exception as e:
            self.logger.error(f"Error conectando señales: {e}")

    def _on_voice_action(self):
        """Maneja la acción de voz"""
        if self.chat_panel and hasattr(self.chat_panel, "start_voice_flow"):
            self.chat_panel.start_voice_flow()

    def _on_clear_chat(self):
        """Maneja la limpieza del chat"""
        if self.chat_panel and hasattr(self.chat_panel, "clear_chat"):
            self.chat_panel.clear_chat()

    def _on_stop_action(self):
        """Maneja la acción de detener"""
        if self.chat_panel and hasattr(self.chat_panel, "worker_stop_requested"):
            self.chat_panel.worker_stop_requested.emit()

    def _toggle_side_panel(self):
        """Alterna la visibilidad del panel lateral"""
        self.side_panel_collapsed = not self.side_panel_collapsed
        self.side_panel.setVisible(not self.side_panel_collapsed)
        self.side_panel.toggle_collapse_button(self.side_panel_collapsed)

        # Ajustar proporciones del layout
        if self.side_panel_collapsed:
            self.main_layout.setStretchFactor(self.side_panel, 0)
            self.main_layout.setStretchFactor(self.chat_panel, 1)
        else:
            self.main_layout.setStretchFactor(self.side_panel, 1)
            self.main_layout.setStretchFactor(self.chat_panel, 3)

    def _on_model_changed(self, model_name):
        """Maneja el cambio de modelo"""
        self.model_changed.emit(model_name)
        self.config_manager.set("General", "model", model_name)
        self.config_manager.save_config()

        # Actualizar componentes
        if self.status_bar and hasattr(self.status_bar, "update_model_info"):
            self.status_bar.update_model_info(model_name)
        if self.side_panel and hasattr(self.side_panel, "update_session_info"):
            # Necesitamos obtener el conteo actual de mensajes
            message_count = (
                len(self.chat_panel.chat_history)
                if hasattr(self.chat_panel, "chat_history")
                else 0
            )
            self.side_panel.update_session_info(model_name, message_count)

        self.logger.info(f"Modelo cambiado a: {model_name}")

    def _on_theme_changed(self, theme_name):
        """Maneja el cambio de tema desde el toolbar"""
        self._on_theme_change_requested(theme_name)

    def _on_theme_change_requested(self, theme_name):
        """Maneja la solicitud de cambio de tema"""
        self.theme_changed.emit(theme_name)
        self.config_manager.set("UI", "theme", theme_name)
        self.config_manager.save_config()
        self.logger.info(f"Tema cambiado a: {theme_name}")
        self._apply_theme()

    def _on_state_changed(self, old_state, new_state):
        """Maneja cambios de estado de la aplicación"""
        # Actualizar componentes según el estado
        if self.toolbar and hasattr(self.toolbar, "update_state"):
            self.toolbar.update_state(new_state)

    def _on_error_occurred(self, error_message):
        """Maneja errores de la aplicación"""
        self.logger.error(f"Error en aplicación: {error_message}")
        QMessageBox.critical(self, "Error", f"Se produjo un error:\n\n{error_message}")

    def _show_config_dialog(self):
        """Muestra el diálogo de configuración"""
        try:
            from ui.dialogs.config_dialog import ConfigDialog

            dialog = ConfigDialog(self, self.config_manager)
            if dialog.exec():
                # Recargar configuración y aplicar cambios
                self.config_manager.load_config()
                self._apply_theme()

                # Notificar a los componentes sobre cambios de configuración
                components = [
                    self.chat_panel,
                    self.side_panel,
                    self.status_bar,
                    self.toolbar,
                ]
                for component in components:
                    if component and hasattr(component, "on_config_changed"):
                        component.on_config_changed()

        except Exception as e:
            self.logger.error(f"Error mostrando diálogo de configuración: {e}")
            QMessageBox.critical(
                self, "Error", f"No se pudo abrir la configuración:\n\n{str(e)}"
            )

    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        self.logger.info("Cerrando ventana principal...")
        self.shutdown_requested.emit()
        event.accept()

    def add_chat_message(self, sender, message, is_tool=False):
        """Añade un mensaje al chat y actualiza la UI"""
        if self.chat_panel and hasattr(self.chat_panel, "add_chat_message"):
            self.chat_panel.add_chat_message(sender, message, is_tool)

        # Actualizar contador en side panel
        if self.side_panel and hasattr(self.side_panel, "update_session_info"):
            current_model = self.config_manager.get("General", "model", "arch-chan")
            message_count = (
                len(self.chat_panel.chat_history)
                if hasattr(self.chat_panel, "chat_history")
                else 0
            )
            self.side_panel.update_session_info(current_model, message_count)
