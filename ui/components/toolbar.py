#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QToolBar

from utils.logger import get_logger


class MainToolbar(QToolBar):
    """Barra de herramientas principal de la aplicación"""

    # Señales
    voice_action_triggered = Signal()
    clear_chat_triggered = Signal()
    config_action_triggered = Signal()
    stop_action_triggered = Signal()
    theme_changed = Signal(str)
    model_changed = Signal(str)

    def __init__(self, config_manager, state_manager):
        super().__init__("Herramientas Principales")
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("MainToolbar")

        # Configurar tamaño de iconos
        icon_size_int = self.config_manager.getint("UI", "toolbar_icon_size", 24)
        self.setIconSize(QSize(icon_size_int, icon_size_int))

        self._create_actions()
        self._setup_ui()

        self.logger.info("MainToolbar inicializado")

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

        # Acción de apagado
        self.shutdown_action = QAction("🔌 Salir", self)
        self.shutdown_action.setStatusTip("Cerrar la aplicación")
        self.shutdown_action.triggered.connect(self._on_shutdown_triggered)

        # Acción de temas (para el menú)
        self.theme_action = QAction("Temas", self)

        # Acción de modelos (para el menú)
        self.model_action = QAction("Modelos", self)

    def _setup_ui(self):
        """Configura la interfaz de la barra de herramientas"""
        # Agregar acciones principales
        self.addAction(self.voice_action)
        self.addSeparator()
        self.addAction(self.clear_action)
        self.addAction(self.config_action)
        self.addAction(self.stop_action)
        self.addSeparator()
        self.addAction(self.shutdown_action)
        self.addSeparator()

        # Menú de temas
        self.theme_menu = QMenu("Temas", self)
        self._populate_theme_menu()
        theme_button = self._create_menu_button("🎨 Temas", self.theme_menu)
        self.addWidget(theme_button)

        # Menú de modelos
        self.model_menu = QMenu("Modelos", self)
        self._populate_model_menu()
        model_button = self._create_menu_button("🤖 Modelos", self.model_menu)
        self.addWidget(model_button)

    def _create_menu_button(self, text, menu):
        """Crea un botón con menú desplegable"""
        from PySide6.QtWidgets import QToolButton

        button = QToolButton(self)
        button.setText(text)
        button.setMenu(menu)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        return button

    def _populate_theme_menu(self):
        """Llena el menú de temas"""
        available_themes = self.config_manager.get_available_themes()
        current_theme = self.config_manager.get("UI", "theme", "arch-dark")

        for theme in available_themes:
            action = self.theme_menu.addAction(theme)
            action.setCheckable(True)
            action.setChecked(theme == current_theme)
            action.triggered.connect(
                lambda checked, t=theme: self._on_theme_selected(t)
            )

    def _populate_model_menu(self):
        """Llena el menú de modelos"""
        # Esto debería cargarse dinámicamente desde Ollama
        available_models = ["arch-chan", "arch-chan-lite", "llama3.2:3b", "gemma:2b"]
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
        self.logger.info(f"Tema seleccionado: {theme}")
        self.theme_changed.emit(theme)

        # Actualizar checks en el menú
        for action in self.theme_menu.actions():
            action.setChecked(action.text() == theme)

    def _on_model_selected(self, model: str):
        """Maneja la selección de un modelo"""
        self.logger.info(f"Modelo seleccionado: {model}")
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

    def on_config_changed(self):
        """Maneja cambios en la configuración"""
        # Actualizar tamaño de iconos
        icon_size_int = self.config_manager.getint("UI", "toolbar_icon_size", 24)
        self.setIconSize(QSize(icon_size_int, icon_size_int))
