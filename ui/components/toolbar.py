#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Barra de herramientas completamente reescrita para Arch-Chan v2.1
Con menus desplegables, iconos y señales mejoradas
"""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QHBoxLayout, QMenu, QToolBar, QToolButton, QWidget

from ui.themes.arch_theme import ArchLinuxTheme
from utils.logger import get_logger


class MainToolbar(QToolBar):
    """Barra de herramientas principal con menus y controles avanzados"""

    # Señales mejoradas
    voice_action_triggered = Signal()
    clear_chat_triggered = Signal()
    config_action_triggered = Signal()
    stop_action_triggered = Signal()
    theme_changed = Signal(str)
    model_changed = Signal(str)
    performance_toggled = Signal(bool)

    def __init__(self, config_manager, state_manager):
        super().__init__("Herramientas Principales")
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("MainToolbar")

        # Configuración inicial
        self.current_theme = self.config_manager.get("UI", "theme", "arch-dark")
        self.current_model = self.config_manager.get("General", "model", "arch-chan")
        self.performance_mode = False

        self._setup_toolbar()
        self._create_actions()
        self._setup_ui()

        self.logger.info("MainToolbar inicializado")

    def _setup_toolbar(self):
        """Configura la barra de herramientas"""
        self.setObjectName("main_toolbar")
        icon_size_int = self.config_manager.getint("UI", "toolbar_icon_size", 24)
        self.setIconSize(QSize(icon_size_int, icon_size_int))
        self.setMovable(False)
        self.setFloatable(False)
        # CORRECCIÓN: Usar el enum Qt.ToolButtonStyle correctamente
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

    def _create_actions(self):
        """Crea las acciones de la barra de herramientas"""
        # Acción de voz
        self.voice_action = QAction("🎤 Voz", self)
        self.voice_action.setStatusTip("Iniciar grabación de voz")
        self.voice_action.triggered.connect(self.voice_action_triggered.emit)

        # Acción de limpiar chat
        self.clear_action = QAction("🗑️ Limpiar", self)
        self.clear_action.setStatusTip("Limpiar historial del chat")
        self.clear_action.triggered.connect(self.clear_chat_triggered.emit)

        # Acción de configuración
        self.config_action = QAction("⚙️ Configurar", self)
        self.config_action.setStatusTip("Abrir configuración")
        self.config_action.triggered.connect(self.config_action_triggered.emit)

        # Acción de detener
        self.stop_action = QAction("⏹️ Detener", self)
        self.stop_action.setStatusTip("Detener operación actual")
        self.stop_action.triggered.connect(self.stop_action_triggered.emit)
        self.stop_action.setEnabled(False)

        # Acción de apagado
        self.shutdown_action = QAction("🔌 Salir", self)
        self.shutdown_action.setStatusTip("Cerrar la aplicación")
        self.shutdown_action.triggered.connect(self._on_shutdown_triggered)

        # Acción de rendimiento
        self.performance_action = QAction("📊 Rendimiento", self)
        self.performance_action.setStatusTip("Alternar modo rendimiento")
        self.performance_action.setCheckable(True)
        self.performance_action.triggered.connect(self.performance_toggled)

    def _setup_ui(self):
        """Configura la interfaz de la barra de herramientas"""
        # Agregar acciones principales
        self.addAction(self.voice_action)
        self.addSeparator()
        self.addAction(self.clear_action)
        self.addAction(self.config_action)
        self.addAction(self.stop_action)
        self.addSeparator()
        self.addAction(self.performance_action)
        self.addAction(self.shutdown_action)
        self.addSeparator()

        # Menú de temas
        self.theme_menu = QMenu("Temas", self)
        self._populate_theme_menu()
        theme_button = self._create_menu_button(
            "🎨 Temas", self.theme_menu, "Cambiar tema visual"
        )
        self.addWidget(theme_button)

        # Menú de modelos
        self.model_menu = QMenu("Modelos", self)
        self._populate_model_menu()
        model_button = self._create_menu_button(
            "🤖 Modelos", self.model_menu, "Cambiar modelo de IA"
        )
        self.addWidget(model_button)

        # Espacio flexible
        self.addWidget(QWidget())  # Espacio flexible
        self.addSeparator()

        # Indicador de estado
        self.status_indicator = QToolButton()
        self.status_indicator.setText("🟢")
        self.status_indicator.setToolTip("Sistema listo")
        self.status_indicator.setEnabled(False)
        self.addWidget(self.status_indicator)

    def _create_menu_button(self, text, menu, tooltip):
        """Crea un botón con menú desplegable"""
        button = QToolButton(self)
        button.setText(text)
        button.setMenu(menu)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setToolTip(tooltip)
        button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        return button

    def _populate_theme_menu(self):
        """Llena el menú de temas"""
        available_themes = ArchLinuxTheme.get_available_themes()
        current_theme = self.config_manager.get("UI", "theme", "arch-dark")

        theme_display_names = {
            "arch-dark": "Arch Dark",
            "arch-light": "Arch Light",
            "blue-matrix": "Blue Matrix",
            "green-terminal": "Green Terminal",
            "purple-haze": "Purple Haze",
            "cyberpunk": "Cyberpunk Neon",
            "sunset-glow": "Sunset Glow",
            "midnight-ocean": "Midnight Ocean",
            "forest-deep": "Forest Deep",
            "neon-dreams": "Neon Dreams",
        }

        for theme in available_themes:
            display_name = theme_display_names.get(theme, theme.title())
            action = self.theme_menu.addAction(display_name)
            action.setCheckable(True)
            action.setChecked(theme == current_theme)
            action.triggered.connect(
                lambda checked, t=theme: self._on_theme_selected(t)
            )

    def _populate_model_menu(self):
        """Llena el menú de modelos"""
        # Esto debería cargarse dinámicamente desde Ollama
        available_models = [
            "arch-chan",
            "arch-chan-lite",
            "llama3.2:3b",
            "gemma:2b",
        ]
        current_model = self.config_manager.get("General", "model", "arch-chan")

        for model in available_models:
            action = self.model_menu.addAction(model)
            action.setCheckable(True)
            action.setChecked(model == current_model)
            action.triggered.connect(
                lambda checked, m=model: self._on_model_selected(m)
            )

    def _on_theme_selected(self, theme: str):
        """Maneja la selección de un tema"""
        self.logger.info(f"Tema seleccionado desde toolbar: {theme}")
        self.theme_changed.emit(theme)

        # Actualizar checks en el menú
        theme_display_names = {
            "arch-dark": "Arch Dark",
            "arch-light": "Arch Light",
            "blue-matrix": "Blue Matrix",
            "green-terminal": "Green Terminal",
            "purple-haze": "Purple Haze",
            "cyberpunk": "Cyberpunk Neon",
            "sunset-glow": "Sunset Glow",
            "midnight-ocean": "Midnight Ocean",
            "forest-deep": "Forest Deep",
            "neon-dreams": "Neon Dreams",
        }

        display_name = theme_display_names.get(theme, theme.title())
        for action in self.theme_menu.actions():
            action.setChecked(action.text() == display_name)

    def _on_model_selected(self, model: str):
        """Maneja la selección de un modelo"""
        self.logger.info(f"Modelo seleccionado desde toolbar: {model}")
        self.model_changed.emit(model)

        # Actualizar checks en el menú
        for action in self.model_menu.actions():
            action.setChecked(action.text() == model)

    def _on_shutdown_triggered(self):
        """Maneja la acción de apagado"""
        self.logger.info("Solicitud de apagado desde la barra de herramientas")
        from PySide6.QtWidgets import QApplication

        QApplication.instance().quit()

    def update_state(self, state):
        """Actualiza el estado de la barra de herramientas"""
        is_busy = state not in ["idle", "error"]

        self.voice_action.setEnabled(not is_busy)
        self.clear_action.setEnabled(not is_busy)
        self.config_action.setEnabled(not is_busy)
        self.stop_action.setEnabled(is_busy)

        # Actualizar indicador de estado
        state_icons = {
            "idle": "🟢",
            "listening": "🎤",
            "processing": "🔄",
            "speaking": "🔊",
            "error": "🔴",
        }
        icon = state_icons.get(state, "🟡")
        self.status_indicator.setText(icon)
        self.status_indicator.setToolTip(f"Estado: {state}")

    def on_config_changed(self):
        """Maneja cambios en la configuración"""
        # Actualizar tamaño de iconos
        icon_size_int = self.config_manager.getint("UI", "toolbar_icon_size", 24)
        self.setIconSize(QSize(icon_size_int, icon_size_int))

        # Actualizar tema actual
        new_theme = self.config_manager.get("UI", "theme", "arch-dark")
        if new_theme != self.current_theme:
            self.current_theme = new_theme
            self._update_theme_menu_checks()

        # Actualizar modelo actual
        new_model = self.config_manager.get("General", "model", "arch-chan")
        if new_model != self.current_model:
            self.current_model = new_model
            self._update_model_menu_checks()

    def _update_theme_menu_checks(self):
        """Actualiza las marcas del menú de temas"""
        theme_display_names = {
            "arch-dark": "Arch Dark",
            "arch-light": "Arch Light",
            "blue-matrix": "Blue Matrix",
            "green-terminal": "Green Terminal",
            "purple-haze": "Purple Haze",
            "cyberpunk": "Cyberpunk Neon",
            "sunset-glow": "Sunset Glow",
            "midnight-ocean": "Midnight Ocean",
            "forest-deep": "Forest Deep",
            "neon-dreams": "Neon Dreams",
        }

        display_name = theme_display_names.get(
            self.current_theme, self.current_theme.title()
        )
        for action in self.theme_menu.actions():
            action.setChecked(action.text() == display_name)

    def _update_model_menu_checks(self):
        """Actualiza las marcas del menú de modelos"""
        for action in self.model_menu.actions():
            action.setChecked(action.text() == self.current_model)

    def set_performance_mode(self, enabled: bool):
        """Activa o desactiva el modo rendimiento"""
        self.performance_mode = enabled
        self.performance_action.setChecked(enabled)
        if enabled:
            self.performance_action.setText("📊 Rendimiento: ON")
            self.performance_action.setToolTip("Desactivar modo rendimiento")
        else:
            self.performance_action.setText("📊 Rendimiento: OFF")
            self.performance_action.setToolTip("Activar modo rendimiento")
