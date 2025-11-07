#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
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
    QVBoxLayout,
    QWidget,
)

from utils.logger import get_logger


class ConfigDialog(QDialog):
    """Diálogo de configuración mejorado con pestañas"""

    config_updated = Signal()  # Se emite cuando la configuración se actualiza

    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.logger = get_logger("ConfigDialog")
        self.config_manager = config_manager
        self.config = config_manager.config

        self.setWindowTitle("Configuración - Arch-Chan v2.1")
        self.setFixedSize(600, 500)

        self._create_ui()
        self._load_current_config()

    def _create_ui(self):
        """Crea la interfaz del diálogo"""
        layout = QVBoxLayout(self)

        # Pestañas
        self.tabs = QTabWidget()

        # Pestaña General
        self.general_tab = self._create_general_tab()
        self.tabs.addTab(self.general_tab, "General")

        # Pestaña Audio
        self.audio_tab = self._create_audio_tab()
        self.tabs.addTab(self.audio_tab, "Audio")

        # Pestaña Interfaz
        self.ui_tab = self._create_ui_tab()
        self.tabs.addTab(self.ui_tab, "Interfaz")

        # Pestaña Avanzado
        self.advanced_tab = self._create_advanced_tab()
        self.tabs.addTab(self.advanced_tab, "Avanzado")

        layout.addWidget(self.tabs)

        # Botones
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("💾 Guardar")
        self.save_button.clicked.connect(self._save_config)

        self.cancel_button = QPushButton("❌ Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        self.apply_button = QPushButton("⚡ Aplicar")
        self.apply_button.clicked.connect(self._apply_config)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _create_general_tab(self):
        """Crea la pestaña de configuración general"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de modelo
        model_group = QGroupBox("Modelo de IA")
        model_layout = QFormLayout(model_group)

        self.model_combo = QComboBox()
        self.model_combo.addItems(
            ["arch-chan", "arch-chan-lite", "llama3.2:3b", "gemma:2b"]
        )
        model_layout.addRow("Modelo principal:", self.model_combo)

        self.auto_update_check = QCheckBox("Buscar actualizaciones automáticamente")
        model_layout.addRow(self.auto_update_check)

        layout.addWidget(model_group)

        # Grupo de comportamiento
        behavior_group = QGroupBox("Comportamiento")
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
        self.max_history_spin.setRange(5, 100)
        self.max_history_spin.setSuffix(" mensajes")
        behavior_layout.addRow("Máximo historial:", self.max_history_spin)

        layout.addWidget(behavior_group)

        layout.addStretch()
        return tab

    def _create_audio_tab(self):
        """Crea la pestaña de configuración de audio"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de voz
        voice_group = QGroupBox("Síntesis de Voz")
        voice_layout = QFormLayout(voice_group)

        self.voice_enabled_check = QCheckBox("Habilitar síntesis de voz")
        voice_layout.addRow(self.voice_enabled_check)

        self.voice_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.voice_volume_slider.setRange(0, 100)
        self.voice_volume_label = QLabel("80%")
        voice_layout.addRow("Volumen de voz:", self.voice_volume_slider)
        voice_layout.addRow("", self.voice_volume_label)

        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["16000", "22050", "44100"])
        voice_layout.addRow("Frecuencia de muestreo:", self.sample_rate_combo)

        self.noise_reduction_check = QCheckBox("Reducción de ruido en audio")
        voice_layout.addRow(self.noise_reduction_check)

        layout.addWidget(voice_group)

        # Grupo de calidad
        quality_group = QGroupBox("Calidad de Audio")
        quality_layout = QFormLayout(quality_group)

        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["Baja", "Media", "Alta"])
        quality_layout.addRow("Calidad de audio:", self.audio_quality_combo)

        self.silence_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.silence_threshold_slider.setRange(1, 20)
        self.silence_threshold_label = QLabel("5%")
        quality_layout.addRow("Umbral de silencio:", self.silence_threshold_slider)
        quality_layout.addRow("", self.silence_threshold_label)

        layout.addWidget(quality_group)

        layout.addStretch()
        return tab

    def _create_ui_tab(self):
        """Crea la pestaña de configuración de interfaz"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de tema
        theme_group = QGroupBox("Apariencia")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Arch Dark", "Arch Light", "Blue Matrix"])
        theme_layout.addRow("Tema:", self.theme_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        self.font_size_spin.setSuffix(" px")
        theme_layout.addRow("Tamaño de fuente:", self.font_size_spin)

        self.animations_check = QCheckBox("Habilitar animaciones")
        theme_layout.addRow(self.animations_check)

        self.compact_mode_check = QCheckBox("Modo compacto")
        theme_layout.addRow(self.compact_mode_check)

        layout.addWidget(theme_group)

        # Grupo de ventana
        window_group = QGroupBox("Ventana")
        window_layout = QFormLayout(window_group)

        self.sidebar_check = QCheckBox("Mostrar panel lateral")
        window_layout.addRow(self.sidebar_check)

        self.tray_check = QCheckBox("Minimizar a bandeja del sistema")
        window_layout.addRow(self.tray_check)

        layout.addWidget(window_group)

        layout.addStretch()
        return tab

    def _create_advanced_tab(self):
        """Crea la pestaña de configuración avanzada"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de rendimiento
        performance_group = QGroupBox("Rendimiento")
        performance_layout = QFormLayout(performance_group)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(30, 300)
        self.timeout_spin.setSuffix(" segundos")
        performance_layout.addRow("Timeout de comandos:", self.timeout_spin)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setSuffix(" intentos")
        performance_layout.addRow("Reintentos:", self.retry_spin)

        self.cache_check = QCheckBox("Cachear respuestas")
        performance_layout.addRow(self.cache_check)

        layout.addWidget(performance_group)

        # Grupo de seguridad
        security_group = QGroupBox("Seguridad")
        security_layout = QFormLayout(security_group)

        self.sudo_confirm_check = QCheckBox("Confirmar comandos sudo")
        security_layout.addRow(self.sudo_confirm_check)

        self.danger_check = QCheckBox("Bloquear comandos peligrosos")
        security_layout.addRow(self.danger_check)

        layout.addWidget(security_group)

        # Grupo de logs
        log_group = QGroupBox("Registro y Logs")
        log_layout = QFormLayout(log_group)

        self.debug_check = QCheckBox("Modo debug (logs detallados)")
        log_layout.addRow(self.debug_check)

        layout.addWidget(log_group)

        layout.addStretch()
        return tab

    def _load_current_config(self):
        """Carga la configuración actual en los controles"""
        # General
        self.model_combo.setCurrentText(
            self.config.get("General", "model", fallback="arch-chan")
        )
        self.auto_update_check.setChecked(
            self.config.getboolean("General", "auto_update", fallback=False)
        )
        self.auto_cleanup_check.setChecked(
            self.config.getboolean("General", "auto_cleanup", fallback=True)
        )
        self.notifications_check.setChecked(
            self.config.getboolean("General", "notifications", fallback=True)
        )
        self.backup_check.setChecked(
            self.config.getboolean("General", "backup_enabled", fallback=True)
        )
        self.max_history_spin.setValue(
            self.config.getint("General", "max_history", fallback=20)
        )

        # Audio
        self.voice_enabled_check.setChecked(
            self.config.getboolean("General", "voice_enabled", fallback=True)
        )
        self.voice_volume_slider.setValue(
            self.config.getint("Audio", "voice_volume", fallback=80)
        )
        self.sample_rate_combo.setCurrentText(
            self.config.get("Audio", "sample_rate", fallback="22050")
        )
        self.noise_reduction_check.setChecked(
            self.config.getboolean("Audio", "noise_reduction", fallback=True)
        )

        audio_quality = self.config.get("Audio", "audio_quality", fallback="high")
        quality_map = {"low": "Baja", "medium": "Media", "high": "Alta"}
        self.audio_quality_combo.setCurrentText(quality_map.get(audio_quality, "Alta"))

        silence_threshold = self.config.get(
            "Audio", "silence_threshold", fallback="5%"
        ).rstrip("%")
        self.silence_threshold_slider.setValue(int(silence_threshold))

        # UI
        theme = self.config.get("UI", "theme", fallback="arch-dark")
        theme_map = {
            "arch-dark": "Arch Dark",
            "arch-light": "Arch Light",
            "blue-matrix": "Blue Matrix",
        }
        self.theme_combo.setCurrentText(theme_map.get(theme, "Arch Dark"))

        self.font_size_spin.setValue(self.config.getint("UI", "font_size", fallback=11))
        self.animations_check.setChecked(
            self.config.getboolean("UI", "animations", fallback=True)
        )
        self.compact_mode_check.setChecked(
            self.config.getboolean("UI", "compact_mode", fallback=False)
        )
        self.sidebar_check.setChecked(
            self.config.getboolean("UI", "sidebar_visible", fallback=True)
        )
        self.tray_check.setChecked(
            self.config.getboolean("UI", "tray_enabled", fallback=True)
        )

        # Avanzado
        self.timeout_spin.setValue(
            self.config.getint("Advanced", "timeout_duration", fallback=120)
        )
        self.retry_spin.setValue(
            self.config.getint("Advanced", "retry_attempts", fallback=3)
        )
        self.cache_check.setChecked(
            self.config.getboolean("Advanced", "cache_responses", fallback=True)
        )
        self.sudo_confirm_check.setChecked(
            self.config.getboolean("Advanced", "sudo_confirm", fallback=True)
        )
        self.danger_check.setChecked(
            self.config.getboolean("Advanced", "block_dangerous", fallback=True)
        )
        self.debug_check.setChecked(
            self.config.getboolean("Advanced", "debug_mode", fallback=False)
        )

        # Conectar señales para actualizaciones en tiempo real
        self.voice_volume_slider.valueChanged.connect(
            lambda v: self.voice_volume_label.setText(f"{v}%")
        )
        self.silence_threshold_slider.valueChanged.connect(
            lambda v: self.silence_threshold_label.setText(f"{v}%")
        )

    def _save_config(self):
        """Guarda la configuración y cierra el diálogo"""
        if self._apply_config():
            self.accept()

    def _apply_config(self):
        """Aplica la configuración sin cerrar el diálogo"""
        try:
            # General
            self.config.set("General", "model", self.model_combo.currentText())
            self.config.set(
                "General", "auto_update", str(self.auto_update_check.isChecked())
            )
            self.config.set(
                "General", "auto_cleanup", str(self.auto_cleanup_check.isChecked())
            )
            self.config.set(
                "General", "notifications", str(self.notifications_check.isChecked())
            )
            self.config.set(
                "General", "backup_enabled", str(self.backup_check.isChecked())
            )
            self.config.set(
                "General", "max_history", str(self.max_history_spin.value())
            )
            self.config.set(
                "General", "voice_enabled", str(self.voice_enabled_check.isChecked())
            )

            # Audio
            self.config.set(
                "Audio", "voice_volume", str(self.voice_volume_slider.value())
            )
            self.config.set(
                "Audio", "sample_rate", self.sample_rate_combo.currentText()
            )
            self.config.set(
                "Audio", "noise_reduction", str(self.noise_reduction_check.isChecked())
            )

            audio_quality_map = {"Baja": "low", "Media": "medium", "Alta": "high"}
            self.config.set(
                "Audio",
                "audio_quality",
                audio_quality_map[self.audio_quality_combo.currentText()],
            )
            self.config.set(
                "Audio",
                "silence_threshold",
                f"{self.silence_threshold_slider.value()}%",
            )

            # UI
            theme_map = {
                "Arch Dark": "arch-dark",
                "Arch Light": "arch-light",
                "Blue Matrix": "blue-matrix",
            }
            self.config.set("UI", "theme", theme_map[self.theme_combo.currentText()])
            self.config.set("UI", "font_size", str(self.font_size_spin.value()))
            self.config.set("UI", "animations", str(self.animations_check.isChecked()))
            self.config.set(
                "UI", "compact_mode", str(self.compact_mode_check.isChecked())
            )
            self.config.set(
                "UI", "sidebar_visible", str(self.sidebar_check.isChecked())
            )
            self.config.set("UI", "tray_enabled", str(self.tray_check.isChecked()))

            # Avanzado
            self.config.set(
                "Advanced", "timeout_duration", str(self.timeout_spin.value())
            )
            self.config.set("Advanced", "retry_attempts", str(self.retry_spin.value()))
            self.config.set(
                "Advanced", "cache_responses", str(self.cache_check.isChecked())
            )
            self.config.set(
                "Advanced", "sudo_confirm", str(self.sudo_confirm_check.isChecked())
            )
            self.config.set(
                "Advanced", "block_dangerous", str(self.danger_check.isChecked())
            )
            self.config.set("Advanced", "debug_mode", str(self.debug_check.isChecked()))

            self.config_manager.save_config()
            self.config_updated.emit()

            QMessageBox.information(
                self, "Configuración", "✅ Configuración aplicada correctamente"
            )
            return True

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"❌ Error al guardar configuración: {str(e)}"
            )
            return False
