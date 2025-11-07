#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ThemeMode(Enum):
    """Modos de tema disponibles"""

    ARCH_DARK = "arch-dark"
    ARCH_LIGHT = "arch-light"
    BLUE_MATRIX = "blue-matrix"
    GREEN_TERMINAL = "green-terminal"
    PURPLE_HAZE = "purple-haze"


class AudioQuality(Enum):
    """Calidades de audio disponibles"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class GeneralConfig:
    """Configuración general de la aplicación"""

    model: str = "arch-chan"
    auto_cleanup: bool = True
    max_history: int = 20
    notifications: bool = True
    voice_enabled: bool = True
    theme: ThemeMode = ThemeMode.ARCH_DARK
    language: str = "es"
    auto_update: bool = False
    backup_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        data = asdict(self)
        data["theme"] = self.theme.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneralConfig":
        """Crea la configuración desde un diccionario"""
        data["theme"] = ThemeMode(data["theme"])
        return cls(**data)


@dataclass
class AudioConfig:
    """Configuración de audio"""

    sample_rate: int = 22050
    silence_threshold: str = "5%"
    voice_volume: int = 80
    noise_reduction: bool = True
    audio_quality: AudioQuality = AudioQuality.HIGH

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        data = asdict(self)
        data["audio_quality"] = self.audio_quality.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioConfig":
        """Crea la configuración desde un diccionario"""
        data["audio_quality"] = AudioQuality(data["audio_quality"])
        return cls(**data)


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

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return asdict(self)


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

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return asdict(self)


@dataclass
class AppConfig:
    """Configuración completa de la aplicación"""

    general: GeneralConfig
    audio: AudioConfig
    ui: UIConfig
    advanced: AdvancedConfig

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
            general=GeneralConfig.from_dict(data["general"]),
            audio=AudioConfig.from_dict(data["audio"]),
            ui=UIConfig(**data["ui"]),
            advanced=AdvancedConfig(**data["advanced"]),
        )
