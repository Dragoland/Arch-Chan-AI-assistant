#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Diálogo de configuración completamente reescrito
Con pestañas organizadas, validación mejorada y vista previa de temas
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.themes.arch_theme import ArchLinuxTheme
from utils.logger import get_logger


class ConfigDialog(QDialog):
    """Diálogo de configuración mejorado con vista previa en tiempo real"""

    config_updated = Signal()

    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.logger = get_logger("ConfigDialog")
        self.config_manager = config_manager
        self.config = config_manager.config
        self.current_theme = self.config_manager.get("UI", "theme", "arch-dark")

        self.setWindowTitle("⚙️ Configuración - Arch-Chan v2.1.0")
        self.setFixedSize(700, 600)
        self.setModal(True)

        self._create_ui()
        self._load_current_config()
        self._setup_theme_preview()

        self.logger.info("ConfigDialog inicializado")

    def _create_ui(self):
        """Crea la interfaz del diálogo con pestañas organizadas"""
        main_layout = QVBoxLayout(self)

        # Título y descripción
        title_label = QLabel("Configuración de Arch-Chan")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1793D1;")

        desc_label = QLabel(
            "Personaliza el comportamiento y apariencia de tu asistente de IA"
        )
        desc_label.setStyleSheet("color: #7C818C; font-size: 11px;")

        main_layout.addWidget(title_label)
        main_layout.addWidget(desc_label)
        main_layout.addSpacing(10)

        # Pestañas principales
        self.tab_widget = QTabWidget()

        # Crear pestañas
        self.general_tab = self._create_general_tab()
        self.appearance_tab = self._create_appearance_tab()
        self.audio_tab = self._create_audio_tab()
        self.advanced_tab = self._create_advanced_tab()

        self.tab_widget.addTab(self.general_tab, "🎯 General")
        self.tab_widget.addTab(self.appearance_tab, "🎨 Apariencia")
        self.tab_widget.addTab(self.audio_tab, "🔊 Audio")
        self.tab_widget.addTab(self.advanced_tab, "⚙️ Avanzado")

        main_layout.addWidget(self.tab_widget)

        # Vista previa del tema
        self._create_theme_preview(main_layout)

        # Botones de acción
        button_box = QDialogButtonBox()
        self.apply_button = button_box.addButton("Aplicar", QDialogButtonBox.ApplyRole)
        self.save_button = button_box.addButton("Guardar", QDialogButtonBox.AcceptRole)
        self.cancel_button = button_box.addButton(
            "Cancelar", QDialogButtonBox.RejectRole
        )

        self.apply_button.clicked.connect(self._apply_config)
        self.save_button.clicked.connect(self._save_config)
        self.cancel_button.clicked.connect(self.reject)

        main_layout.addWidget(button_box)

    def _create_general_tab(self):
        """Crea la pestaña de configuración general"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de modelo de IA
        model_group = QGroupBox("🤖 Modelo de IA")
        model_layout = QFormLayout(model_group)

        self.model_combo = QComboBox()
        self.model_combo.addItems(
            [
                "arch-chan",
                "arch-chan-lite",
                "llama3.2:3b",
                "gemma:2b",
                "mistral:7b",
                "codellama:7b",
            ]
        )
        self.model_combo.setToolTip("Selecciona el modelo de IA a utilizar")
        model_layout.addRow("Modelo principal:", self.model_combo)

        self.auto_update_check = QCheckBox("Buscar actualizaciones automáticamente")
        self.auto_update_check.setToolTip(
            "Buscar nuevas versiones al iniciar la aplicación"
        )
        model_layout.addRow(self.auto_update_check)

        layout.addWidget(model_group)

        # Grupo de comportamiento
        behavior_group = QGroupBox("🔧 Comportamiento")
        behavior_layout = QFormLayout(behavior_group)

        self.auto_cleanup_check = QCheckBox(
            "Limpieza automática de archivos temporales"
        )
        behavior_layout.addRow(self.auto_cleanup_check)

        self.notifications_check = QCheckBox("Mostrar notificaciones del sistema")
        behavior_layout.addRow(self.notifications_check)

        self.backup_check = QCheckBox("Crear backups automáticos de configuración")
        behavior_layout.addRow(self.backup_check)

        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(10, 1000)
        self.max_history_spin.setSuffix(" mensajes")
        self.max_history_spin.setToolTip(
            "Número máximo de mensajes a mantener en el historial"
        )
        behavior_layout.addRow("Máximo historial:", self.max_history_spin)

        layout.addWidget(behavior_group)

        layout.addStretch()
        return tab

    def _create_appearance_tab(self):
        """Crea la pestaña de configuración de apariencia"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de tema
        theme_group = QGroupBox("🎨 Tema y Colores")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        available_themes = ArchLinuxTheme.get_available_themes()
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
            self.theme_combo.addItem(display_name, theme)

        self.theme_combo.currentTextChanged.connect(self._on_theme_preview_changed)
        theme_layout.addRow("Tema de la interfaz:", self.theme_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        self.font_size_spin.setSuffix(" px")
        theme_layout.addRow("Tamaño de fuente base:", self.font_size_spin)

        self.animations_check = QCheckBox("Habilitar animaciones y transiciones")
        theme_layout.addRow(self.animations_check)

        self.compact_mode_check = QCheckBox("Modo compacto (menos espaciado)")
        theme_layout.addRow(self.compact_mode_check)

        layout.addWidget(theme_group)

        # Grupo de ventana
        window_group = QGroupBox("🪟 Ventana e Interfaz")
        window_layout = QFormLayout(window_group)

        self.sidebar_check = QCheckBox("Mostrar panel lateral al iniciar")
        window_layout.addRow(self.sidebar_check)

        self.tray_check = QCheckBox("Minimizar a bandeja del sistema")
        window_layout.addRow(self.tray_check)

        self.always_on_top_check = QCheckBox("Mantener ventana siempre visible")
        window_layout.addRow(self.always_on_top_check)

        layout.addWidget(window_group)

        layout.addStretch()
        return tab

    def _create_audio_tab(self):
        """Crea la pestaña de configuración de audio"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de síntesis de voz
        voice_group = QGroupBox("🎤 Síntesis de Voz (TTS)")
        voice_layout = QFormLayout(voice_group)

        self.voice_enabled_check = QCheckBox("Habilitar síntesis de voz")
        self.voice_enabled_check.toggled.connect(self._on_voice_toggled)
        voice_layout.addRow(self.voice_enabled_check)

        # Volumen de voz
        volume_layout = QHBoxLayout()
        self.voice_volume_slider = QSlider(Qt.Horizontal)
        self.voice_volume_slider.setRange(0, 100)
        self.voice_volume_label = QLabel("80%")
        volume_layout.addWidget(self.voice_volume_slider)
        volume_layout.addWidget(self.voice_volume_label)
        voice_layout.addRow("Volumen de voz:", volume_layout)

        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["16000", "22050", "44100", "48000"])
        voice_layout.addRow("Frecuencia de muestreo:", self.sample_rate_combo)

        self.voice_speed_slider = QSlider(Qt.Horizontal)
        self.voice_speed_slider.setRange(50, 200)
        self.voice_speed_label = QLabel("100%")
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.voice_speed_slider)
        speed_layout.addWidget(self.voice_speed_label)
        voice_layout.addRow("Velocidad de voz:", speed_layout)

        layout.addWidget(voice_group)

        # Grupo de calidad de audio
        quality_group = QGroupBox("🎧 Calidad de Audio")
        quality_layout = QFormLayout(quality_group)

        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(
            ["Baja (8kHz)", "Media (16kHz)", "Alta (44.1kHz)", "Ultra (48kHz)"]
        )
        quality_layout.addRow("Calidad de audio:", self.audio_quality_combo)

        self.noise_reduction_check = QCheckBox("Reducción activa de ruido")
        quality_layout.addRow(self.noise_reduction_check)

        self.echo_cancellation_check = QCheckBox("Cancelación de eco")
        quality_layout.addRow(self.echo_cancellation_check)

        layout.addWidget(quality_group)

        layout.addStretch()
        return tab

    def _create_advanced_tab(self):
        """Crea la pestaña de configuración avanzada"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de rendimiento
        performance_group = QGroupBox("🚀 Rendimiento")
        performance_layout = QFormLayout(performance_group)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSuffix(" segundos")
        performance_layout.addRow("Timeout de comandos:", self.timeout_spin)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setSuffix(" intentos")
        performance_layout.addRow("Reintentos de conexión:", self.retry_spin)

        self.cache_check = QCheckBox("Cachear respuestas de IA")
        performance_layout.addRow(self.cache_check)

        self.parallel_processing_check = QCheckBox("Procesamiento paralelo")
        performance_layout.addRow(self.parallel_processing_check)

        layout.addWidget(performance_group)

        # Grupo de seguridad
        security_group = QGroupBox("🔒 Seguridad")
        security_layout = QFormLayout(security_group)

        self.sudo_confirm_check = QCheckBox(
            "Confirmar comandos con privilegios elevados"
        )
        security_layout.addRow(self.sudo_confirm_check)

        self.danger_check = QCheckBox("Bloquear comandos potencialmente peligrosos")
        security_layout.addRow(self.danger_check)

        self.auto_save_check = QCheckBox(
            "Guardar automáticamente conversaciones importantes"
        )
        security_layout.addRow(self.auto_save_check)

        layout.addWidget(security_group)

        # Grupo de registro
        log_group = QGroupBox("📝 Registro y Logs")
        log_layout = QFormLayout(log_group)

        self.debug_check = QCheckBox("Modo debug (logs detallados)")
        log_layout.addRow(self.debug_check)

        self.log_retention_spin = QSpinBox()
        self.log_retention_spin.setRange(1, 90)
        self.log_retention_spin.setSuffix(" días")
        log_layout.addRow("Retención de logs:", self.log_retention_spin)

        layout.addWidget(log_group)

        layout.addStretch()
        return tab

    def _create_theme_preview(self, parent_layout):
        """Crea la sección de vista previa del tema"""
        preview_group = QGroupBox("👁️ Vista Previa del Tema")
        preview_layout = QVBoxLayout(preview_group)

        self.theme_preview = QTextEdit()
        self.theme_preview.setMaximumHeight(120)
        self.theme_preview.setReadOnly(True)
        self.theme_preview.setPlainText(
            "Esta es una vista previa del tema seleccionado.\n"
            "Texto normal\n"
            "🔧 Mensaje de herramienta\n"
            "👤 Mensaje de usuario\n"
            "🤖 Mensaje del asistente"
        )

        preview_layout.addWidget(self.theme_preview)
        parent_layout.addWidget(preview_group)

    def _setup_theme_preview(self):
        """Configura la vista previa del tema actual"""
        self._update_theme_preview()

    def _update_theme_preview(self):
        """Actualiza la vista previa con el tema seleccionado"""
        try:
            theme_name = self.theme_combo.currentData()
            if not theme_name:
                return

            theme = ArchLinuxTheme.get_theme(theme_name)
            stylesheet = f"""
            QTextEdit {{
                background-color: {theme['background']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Noto Sans', sans-serif;
            }}
            """
            self.theme_preview.setStyleSheet(stylesheet)
        except Exception as e:
            self.logger.debug(f"Error actualizando vista previa del tema: {e}")

    def _on_theme_preview_changed(self):
        """Maneja el cambio de tema en la vista previa"""
        self._update_theme_preview()

    def _on_voice_toggled(self, enabled):
        """Habilita/deshabilita controles de audio según el estado"""
        widgets = [
            self.voice_volume_slider,
            self.voice_volume_label,
            self.sample_rate_combo,
            self.voice_speed_slider,
            self.voice_speed_label,
        ]
        for widget in widgets:
            widget.setEnabled(enabled)

    def _load_current_config(self):
        """Carga la configuración actual en los controles"""
        try:
            # General
            self.model_combo.setCurrentText(
                self.config_manager.get("General", "model", "arch-chan")
            )
            self.auto_update_check.setChecked(
                self.config_manager.getboolean("General", "auto_update", True)
            )
            self.auto_cleanup_check.setChecked(
                self.config_manager.getboolean("General", "auto_cleanup", True)
            )
            self.notifications_check.setChecked(
                self.config_manager.getboolean("General", "notifications", True)
            )
            self.backup_check.setChecked(
                self.config_manager.getboolean("General", "backup_enabled", True)
            )
            self.max_history_spin.setValue(
                self.config_manager.getint("General", "max_history", 100)
            )

            # Apariencia
            current_theme = self.config_manager.get("UI", "theme", "arch-dark")
            theme_index = self.theme_combo.findData(current_theme)
            if theme_index >= 0:
                self.theme_combo.setCurrentIndex(theme_index)

            self.font_size_spin.setValue(
                self.config_manager.getint("UI", "font_size", 11)
            )
            self.animations_check.setChecked(
                self.config_manager.getboolean("UI", "animations", True)
            )
            self.compact_mode_check.setChecked(
                self.config_manager.getboolean("UI", "compact_mode", False)
            )
            self.sidebar_check.setChecked(
                self.config_manager.getboolean("UI", "sidebar_visible", True)
            )
            self.tray_check.setChecked(
                self.config_manager.getboolean("UI", "tray_enabled", True)
            )
            self.always_on_top_check.setChecked(
                self.config_manager.getboolean("UI", "always_on_top", False)
            )

            # Audio
            self.voice_enabled_check.setChecked(
                self.config_manager.getboolean("Audio", "voice_enabled", True)
            )
            self.voice_volume_slider.setValue(
                self.config_manager.getint("Audio", "voice_volume", 80)
            )
            self.sample_rate_combo.setCurrentText(
                self.config_manager.get("Audio", "sample_rate", "22050")
            )
            self.voice_speed_slider.setValue(
                self.config_manager.getint("Audio", "voice_speed", 100)
            )
            self.noise_reduction_check.setChecked(
                self.config_manager.getboolean("Audio", "noise_reduction", True)
            )
            self.echo_cancellation_check.setChecked(
                self.config_manager.getboolean("Audio", "echo_cancellation", True)
            )

            audio_quality = self.config_manager.get("Audio", "audio_quality", "high")
            quality_map = {"low": 0, "medium": 1, "high": 2, "ultra": 3}
            self.audio_quality_combo.setCurrentIndex(quality_map.get(audio_quality, 2))

            # Avanzado
            self.timeout_spin.setValue(
                self.config_manager.getint("Advanced", "timeout_duration", 60)
            )
            self.retry_spin.setValue(
                self.config_manager.getint("Advanced", "retry_attempts", 3)
            )
            self.cache_check.setChecked(
                self.config_manager.getboolean("Advanced", "cache_responses", True)
            )
            self.parallel_processing_check.setChecked(
                self.config_manager.getboolean("Advanced", "parallel_processing", False)
            )
            self.sudo_confirm_check.setChecked(
                self.config_manager.getboolean("Advanced", "sudo_confirm", True)
            )
            self.danger_check.setChecked(
                self.config_manager.getboolean("Advanced", "block_dangerous", True)
            )
            self.auto_save_check.setChecked(
                self.config_manager.getboolean("Advanced", "auto_save", True)
            )
            self.debug_check.setChecked(
                self.config_manager.getboolean("Advanced", "debug_mode", False)
            )
            self.log_retention_spin.setValue(
                self.config_manager.getint("Advanced", "log_retention", 30)
            )

            # Actualizar etiquetas y estados
            self._update_slider_labels()
            self._on_voice_toggled(self.voice_enabled_check.isChecked())

            # Conectar señales de sliders
            self.voice_volume_slider.valueChanged.connect(
                lambda v: self.voice_volume_label.setText(f"{v}%")
            )
            self.voice_speed_slider.valueChanged.connect(
                lambda v: self.voice_speed_label.setText(f"{v}%")
            )

        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            QMessageBox.warning(
                self,
                "Error de Configuración",
                f"No se pudieron cargar algunas opciones de configuración:\n\n{str(e)}",
            )

    def _update_slider_labels(self):
        """Actualiza las etiquetas de los sliders"""
        self.voice_volume_label.setText(f"{self.voice_volume_slider.value()}%")
        self.voice_speed_label.setText(f"{self.voice_speed_slider.value()}%")

    def _apply_config(self):
        """Aplica la configuración sin cerrar el diálogo"""
        try:
            self._save_config_to_manager()
            self.config_updated.emit()

            QMessageBox.information(
                self,
                "Configuración",
                "✅ Configuración aplicada correctamente\n\nLos cambios se han guardado y aplicado a la aplicación.",
            )
            return True

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"❌ Error al aplicar la configuración:\n\n{str(e)}"
            )
            return False

    def _save_config(self):
        """Guarda la configuración y cierra el diálogo"""
        if self._apply_config():
            self.accept()

    def _save_config_to_manager(self):
        """Guarda la configuración en el config manager"""
        # General
        self.config_manager.set("General", "model", self.model_combo.currentText())
        self.config_manager.set(
            "General", "auto_update", str(self.auto_update_check.isChecked())
        )
        self.config_manager.set(
            "General", "auto_cleanup", str(self.auto_cleanup_check.isChecked())
        )
        self.config_manager.set(
            "General", "notifications", str(self.notifications_check.isChecked())
        )
        self.config_manager.set(
            "General", "backup_enabled", str(self.backup_check.isChecked())
        )
        self.config_manager.set(
            "General", "max_history", str(self.max_history_spin.value())
        )

        # Apariencia
        theme_data = self.theme_combo.currentData()
        self.config_manager.set("UI", "theme", theme_data)
        self.config_manager.set("UI", "font_size", str(self.font_size_spin.value()))
        self.config_manager.set(
            "UI", "animations", str(self.animations_check.isChecked())
        )
        self.config_manager.set(
            "UI", "compact_mode", str(self.compact_mode_check.isChecked())
        )
        self.config_manager.set(
            "UI", "sidebar_visible", str(self.sidebar_check.isChecked())
        )
        self.config_manager.set("UI", "tray_enabled", str(self.tray_check.isChecked()))
        self.config_manager.set(
            "UI", "always_on_top", str(self.always_on_top_check.isChecked())
        )

        # Audio
        self.config_manager.set(
            "Audio", "voice_enabled", str(self.voice_enabled_check.isChecked())
        )
        self.config_manager.set(
            "Audio", "voice_volume", str(self.voice_volume_slider.value())
        )
        self.config_manager.set(
            "Audio", "sample_rate", self.sample_rate_combo.currentText()
        )
        self.config_manager.set(
            "Audio", "voice_speed", str(self.voice_speed_slider.value())
        )
        self.config_manager.set(
            "Audio", "noise_reduction", str(self.noise_reduction_check.isChecked())
        )
        self.config_manager.set(
            "Audio", "echo_cancellation", str(self.echo_cancellation_check.isChecked())
        )

        quality_map = {0: "low", 1: "medium", 2: "high", 3: "ultra"}
        self.config_manager.set(
            "Audio",
            "audio_quality",
            quality_map[self.audio_quality_combo.currentIndex()],
        )

        # Avanzado
        self.config_manager.set(
            "Advanced", "timeout_duration", str(self.timeout_spin.value())
        )
        self.config_manager.set(
            "Advanced", "retry_attempts", str(self.retry_spin.value())
        )
        self.config_manager.set(
            "Advanced", "cache_responses", str(self.cache_check.isChecked())
        )
        self.config_manager.set(
            "Advanced",
            "parallel_processing",
            str(self.parallel_processing_check.isChecked()),
        )
        self.config_manager.set(
            "Advanced", "sudo_confirm", str(self.sudo_confirm_check.isChecked())
        )
        self.config_manager.set(
            "Advanced", "block_dangerous", str(self.danger_check.isChecked())
        )
        self.config_manager.set(
            "Advanced", "auto_save", str(self.auto_save_check.isChecked())
        )
        self.config_manager.set(
            "Advanced", "debug_mode", str(self.debug_check.isChecked())
        )
        self.config_manager.set(
            "Advanced", "log_retention", str(self.log_retention_spin.value())
        )

        # Guardar configuración
        self.config_manager.save_config()
        self.logger.info("Configuración guardada exitosamente")

    def get_updated_config(self):
        """Retorna la configuración actualizada"""
        return self.config
