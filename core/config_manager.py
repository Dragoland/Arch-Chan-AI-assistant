#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from utils.logger import get_logger


class ConfigManager:
    """Gestiona la configuración persistente de la aplicación"""

    def __init__(self):
        self.logger = get_logger("ConfigManager")
        self.config = configparser.ConfigParser()

        # Definir rutas por defecto
        self.project_path = os.path.expanduser("~/arch-chan-project")
        self.models_path = os.path.join(self.project_path, "models")
        self.temp_path = os.path.join(self.project_path, "temp")
        self.logs_path = os.path.join(self.project_path, "logs")
        self.configs_path = os.path.join(self.project_path, "configs")

        self.config_file = os.path.join(self.project_path, "config.ini")

        # Cargar configuración al inicializar
        self.load_config()

    def load_config(self):
        """Carga la configuración desde archivo o crea una por defecto"""
        self.logger.info("Cargando configuración...")
        defaults = self._get_default_config()

        if os.path.exists(self.config_file):
            self.logger.info(f"Configuración encontrada en: {self.config_file}")
            self.config.read(self.config_file, encoding="utf-8")
            self._migrate_old_config()
        else:
            self.logger.info("Creando configuración por defecto...")
            self.config.read_dict(defaults)
            self.save_config()

        return self.config

    def _get_default_config(self) -> Dict[str, Dict[str, Any]]:
        """Retorna la configuración por defecto"""
        return {
            "General": {
                "model": "arch-chan",
                "auto_cleanup": "true",
                "max_history": "20",
                "notifications": "true",
                "voice_enabled": "true",
                "theme": "arch-dark",
                "language": "es",
                "auto_update": "false",
                "backup_enabled": "true",
            },
            "Paths": {
                "project_path": self.project_path,
                "models_path": self.models_path,
                "temp_path": self.temp_path,
                "configs_path": self.configs_path,
            },
            "Audio": {
                "sample_rate": "22050",
                "silence_threshold": "5%",
                "voice_volume": "80",
                "noise_reduction": "true",
                "audio_quality": "high",
            },
            "UI": {
                "window_width": "900",
                "window_height": "700",
                "sidebar_visible": "true",
                "font_size": "11",
                "animations": "true",
                "compact_mode": "false",
                "tray_enabled": "true",
            },
            "Advanced": {
                "timeout_duration": "120",
                "max_response_length": "4000",
                "retry_attempts": "3",
                "cache_responses": "true",
                "sudo_confirm": "true",
                "block_dangerous": "true",
                "debug_mode": "false",
            },
        }

    def _migrate_old_config(self):
        """Migra configuraciones de versiones anteriores"""
        # Por ahora solo log, implementar migración real si es necesario
        self.logger.info("Verificando migración de configuración...")

    def save_config(self):
        """Guarda la configuración actual en archivo"""
        try:
            if self.getboolean("General", "backup_enabled", fallback=True):
                self._create_config_backup()

            with open(self.config_file, "w", encoding="utf-8") as f:
                self.config.write(f)
            self.logger.info("Configuración guardada correctamente")
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")

    def _create_config_backup(self):
        """Crea un backup de la configuración"""
        try:
            backup_dir = os.path.join(self.configs_path, "backups")
            Path(backup_dir).mkdir(parents=True, exist_ok=True)

            backup_file = os.path.join(
                backup_dir,
                f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ini",
            )

            with open(backup_file, "w", encoding="utf-8") as f:
                self.config.write(f)

            self.logger.info(f"Backup de configuración creado: {backup_file}")
        except Exception as e:
            self.logger.warning(f"No se pudo crear backup: {e}")

    # Métodos de conveniencia para acceder a la configuración
    def get(self, section: str, option: str, fallback: Any = None) -> Any:
        """Obtiene un valor de configuración"""
        try:
            return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def getboolean(self, section: str, option: str, fallback: bool = False) -> bool:
        """Obtiene un valor booleano de configuración"""
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def getint(self, section: str, option: str, fallback: int = 0) -> int:
        """Obtiene un valor entero de configuración"""
        try:
            return self.config.getint(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def getfloat(self, section: str, option: str, fallback: float = 0.0) -> float:
        """Obtiene un valor float de configuración"""
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def set(self, section: str, option: str, value: Any):
        """Establece un valor de configuración"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def get_available_themes(self) -> List[str]:
        """Retorna la lista de temas disponibles"""
        return [
            "arch-dark",
            "arch-light",
            "blue-matrix",
            "green-terminal",
            "purple-haze",
        ]

    def get_available_languages(self) -> List[str]:
        """Retorna la lista de idiomas disponibles"""
        return ["es", "en", "fr", "de", "it"]
