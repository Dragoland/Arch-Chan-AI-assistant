#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ThemeMode(Enum):
    """Modos de tema disponibles"""

    ARCH_DARK = "arch-dark"
    ARCH_LIGHT = "arch-light"
    BLUE_MATRIX = "blue-matrix"
    GREEN_TERMINAL = "green-terminal"
    PURPLE_HAZE = "purple-haze"

    @classmethod
    def get_default(cls):
        """Retorna el tema por defecto"""
        return cls.ARCH_DARK

    @classmethod
    def get_all_themes(cls) -> List[str]:
        """Retorna todos los temas disponibles"""
        return [theme.value for theme in cls]


class AudioQuality(Enum):
    """Calidades de audio disponibles"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def get_default(cls):
        """Retorna la calidad por defecto"""
        return cls.HIGH


@dataclass
class GeneralConfig:
    """Configuración general de la aplicación"""

    model: str = "arch-chan"
    auto_cleanup: bool = True
    max_history: int = 20
    notifications: bool = True
    voice_enabled: bool = True
    theme: ThemeMode = field(default_factory=ThemeMode.get_default)
    language: str = "es"
    auto_update: bool = False
    backup_enabled: bool = True
    startup_minimized: bool = False
    check_updates: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        data = asdict(self)
        data["theme"] = self.theme.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneralConfig":
        """Crea la configuración desde un diccionario"""
        # Crear copia para no modificar el original
        config_data = data.copy()

        # Convertir tema
        if "theme" in config_data:
            try:
                config_data["theme"] = ThemeMode(config_data["theme"])
            except ValueError:
                config_data["theme"] = ThemeMode.get_default()

        return cls(**config_data)

    def validate(self) -> List[str]:
        """Valida la configuración y retorna lista de errores"""
        errors = []

        if not self.model or not self.model.strip():
            errors.append("El modelo no puede estar vacío")

        if self.max_history < 1 or self.max_history > 1000:
            errors.append("El historial máximo debe estar entre 1 y 1000")

        if self.language not in ["es", "en", "fr", "de", "it"]:
            errors.append("Idioma no soportado")

        return errors


@dataclass
class AudioConfig:
    """Configuración de audio"""

    sample_rate: int = 22050
    silence_threshold: str = "5%"
    voice_volume: int = 80
    noise_reduction: bool = True
    audio_quality: AudioQuality = field(default_factory=AudioQuality.get_default)
    input_device: Optional[str] = None
    output_device: Optional[str] = None
    voice_speed: float = 1.0
    voice_pitch: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        data = asdict(self)
        data["audio_quality"] = self.audio_quality.value
        # Remover valores None para compatibilidad
        data = {k: v for k, v in data.items() if v is not None}
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioConfig":
        """Crea la configuración desde un diccionario"""
        config_data = data.copy()

        # Convertir calidad de audio
        if "audio_quality" in config_data:
            try:
                config_data["audio_quality"] = AudioQuality(
                    config_data["audio_quality"]
                )
            except ValueError:
                config_data["audio_quality"] = AudioQuality.get_default()

        return cls(**config_data)

    def validate(self) -> List[str]:
        """Valida la configuración de audio"""
        errors = []

        if self.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            errors.append("Tasa de muestreo no soportada")

        if self.voice_volume < 0 or self.voice_volume > 100:
            errors.append("El volumen debe estar entre 0 y 100")

        if self.voice_speed < 0.5 or self.voice_speed > 2.0:
            errors.append("La velocidad de voz debe estar entre 0.5 y 2.0")

        if self.voice_pitch < 0.5 or self.voice_pitch > 2.0:
            errors.append("El tono de voz debe estar entre 0.5 y 2.0")

        return errors


@dataclass
class UIConfig:
    """Configuración de la interfaz de usuario"""

    window_width: int = 900
    window_height: int = 700
    sidebar_visible: bool = True
    font_size: int = 11
    animations: bool = True
    compact_mode: bool = False
    tray_enabled: bool = True
    always_on_top: bool = False
    opacity: float = 1.0
    chat_font_family: str = "Hack, Monospace"
    show_timestamps: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UIConfig":
        """Crea la configuración desde un diccionario"""
        return cls(**data)

    def validate(self) -> List[str]:
        """Valida la configuración de UI"""
        errors = []

        if self.window_width < 400 or self.window_width > 3840:
            errors.append("Ancho de ventana inválido")

        if self.window_height < 300 or self.window_height > 2160:
            errors.append("Alto de ventana inválido")

        if self.font_size < 8 or self.font_size > 24:
            errors.append("Tamaño de fuente inválido")

        if self.opacity < 0.3 or self.opacity > 1.0:
            errors.append("La opacidad debe estar entre 0.3 y 1.0")

        return errors


@dataclass
class AdvancedConfig:
    """Configuración avanzada"""

    timeout_duration: int = 120
    max_response_length: int = 4000
    retry_attempts: int = 3
    cache_responses: bool = True
    sudo_confirm: bool = True
    block_dangerous: bool = True
    debug_mode: bool = False
    log_level: str = "INFO"
    auto_save: bool = True
    save_interval: int = 30  # segundos
    max_log_files: int = 10
    backup_count: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdvancedConfig":
        """Crea la configuración desde un diccionario"""
        return cls(**data)

    def validate(self) -> List[str]:
        """Valida la configuración avanzada"""
        errors = []

        if self.timeout_duration < 10 or self.timeout_duration > 600:
            errors.append("El timeout debe estar entre 10 y 600 segundos")

        if self.max_response_length < 100 or self.max_response_length > 10000:
            errors.append(
                "La longitud máxima de respuesta debe estar entre 100 y 10000"
            )

        if self.retry_attempts < 0 or self.retry_attempts > 10:
            errors.append("Los intentos de reintento deben estar entre 0 y 10")

        if self.save_interval < 5 or self.save_interval > 300:
            errors.append("El intervalo de guardado debe estar entre 5 y 300 segundos")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append("Nivel de log inválido")

        return errors


@dataclass
class AppConfig:
    """Configuración completa de la aplicación"""

    general: GeneralConfig = field(default_factory=GeneralConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración completa a diccionario"""
        return {
            "general": self.general.to_dict(),
            "audio": self.audio.to_dict(),
            "ui": self.ui.to_dict(),
            "advanced": self.advanced.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """Crea la configuración completa desde un diccionario"""
        return cls(
            general=GeneralConfig.from_dict(data.get("general", {})),
            audio=AudioConfig.from_dict(data.get("audio", {})),
            ui=UIConfig.from_dict(data.get("ui", {})),
            advanced=AdvancedConfig.from_dict(data.get("advanced", {})),
        )

    def validate(self) -> List[str]:
        """Valida toda la configuración"""
        errors = []
        errors.extend(self.general.validate())
        errors.extend(self.audio.validate())
        errors.extend(self.ui.validate())
        errors.extend(self.advanced.validate())
        return errors

    def is_valid(self) -> bool:
        """Verifica si la configuración es válida"""
        return len(self.validate()) == 0
