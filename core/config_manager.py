#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.constants import (
    CONFIG_FILE,
    CONFIGS_PATH,
    LOGS_DIR,
    MODELS_DIR,
    PROJECT_DIR,
    TEMP_DIR,
)
from utils.logger import get_logger


class ConfigManager:
    """Gestiona la configuración persistente de la aplicación"""

    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger("ConfigManager")
        self.config = configparser.ConfigParser()

        # Usar rutas de constants.py - asegurar que son Path objects
        self.project_path = Path(PROJECT_DIR)
        self.models_path = Path(MODELS_DIR)
        self.temp_path = Path(TEMP_DIR)
        self.logs_path = Path(LOGS_DIR)
        self.configs_path = (
            Path(CONFIGS_PATH) if CONFIGS_PATH else self.project_path / "config"
        )

        # Usar ruta personalizada o la por defecto
        if config_path:
            self.config_file = Path(config_path)
        else:
            self.config_file = Path(CONFIG_FILE)

        # Cargar configuración al inicializar
        self.load_config()

    def load_config(self) -> configparser.ConfigParser:
        """Carga la configuración desde archivo o crea una por defecto"""
        self.logger.info("Cargando configuración...")

        # NOTA: La creación de directorios se movió a main.py/application.py

        defaults = self._get_default_config()

        if self.config_file.exists():
            self.logger.info(f"Configuración encontrada en: {self.config_file}")
            try:
                self.config.read(self.config_file, encoding="utf-8")
                self._migrate_old_config()
                self._validate_config(defaults)
            except Exception as e:
                self.logger.error(f"Error cargando configuración: {str(e)}")
                self.logger.info("Usando configuración por defecto...")
                self.config.read_dict(defaults)
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
                "language": "es",
                "auto_update": "false",
                "backup_enabled": "true",
                "startup_minimized": "false",
            },
            "Paths": {
                "project_path": str(self.project_path),
                "models_path": str(self.models_path),
                "temp_path": str(self.temp_path),
                "logs_path": str(self.logs_path),
                "configs_path": str(self.configs_path),
            },
            "Audio": {
                "voice_enabled": "true",
                "sample_rate": "22050",
                "silence_threshold": "5%",
                "voice_volume": "80",
                "noise_reduction": "true",
                "audio_quality": "high",
                "input_device": "",
                "output_device": "",
            },
            "UI": {
                "theme": "arch-dark",
                "window_width": "900",
                "window_height": "700",
                "sidebar_visible": "true",
                "font_size": "11",
                "animations": "true",
                "compact_mode": "false",
                "tray_enabled": "true",
                "always_on_top": "false",
            },
            "Advanced": {
                "timeout_duration": "120",
                "max_response_length": "4000",
                "retry_attempts": "3",
                "cache_responses": "true",
                "sudo_confirm": "true",
                "block_dangerous": "true",
                "debug_mode": "false",
                "log_level": "INFO",
            },
        }

    def _migrate_old_config(self):
        """Migra configuraciones de versiones anteriores"""
        pass

    def _validate_config(self, defaults: Dict[str, Dict[str, Any]]):
        """Valida la configuración cargada y añade claves faltantes"""
        try:
            for section, options in defaults.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                    self.logger.info(f"Sección faltante '{section}' añadida a config")

                for option, default_value in options.items():
                    if not self.config.has_option(section, option):
                        self.config.set(section, option, str(default_value))
                        self.logger.info(
                            f"Opción faltante '{section}.{option}' añadida con valor por defecto"
                        )

            # Validar valores numéricos
            required_int_fields = {
                "General": ["max_history"],
                "UI": ["window_width", "window_height", "font_size"],
                "Audio": ["sample_rate", "voice_volume"],
                "Advanced": [
                    "timeout_duration",
                    "max_response_length",
                    "retry_attempts",
                ],
            }

            for section, fields in required_int_fields.items():
                for field in fields:
                    try:
                        self.config.getint(section, field)
                    except (ValueError, configparser.NoOptionError):
                        self.logger.warning(
                            f"Valor inválido para {section}.{field}, usando valor por defecto"
                        )
                        self.config.set(section, field, defaults[section][field])

            self.logger.info("Validación y migración de configuración completada")
        except Exception as e:
            self.logger.error(f"Error validando configuración: {str(e)}")

    def save_config(self) -> bool:
        """Guarda la configuración actual en archivo"""
        try:
            if self.getboolean("General", "backup_enabled", fallback=True):
                self._create_config_backup()

            # Asegurar que el directorio existe
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                self.config.write(f)

            self.logger.info("Configuración guardada correctamente")
            return True

        except Exception as e:
            self.logger.error(f"Error guardando configuración: {str(e)}")
            return False

    def _create_config_backup(self):
        """Crea un backup de la configuración"""
        try:
            # CORRECCIÓN: Asegurar que configs_path es Path antes de usar /
            backup_dir = Path(self.configs_path) / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"config_backup_{timestamp}.ini"

            with open(backup_file, "w", encoding="utf-8") as f:
                self.config.write(f)

            self._cleanup_old_backups(backup_dir)

        except Exception as e:
            self.logger.warning(f"No se pudo crear backup: {str(e)}")

    def _cleanup_old_backups(self, backup_dir: Path, keep_count: int = 5):
        """Limpia backups antiguos"""
        try:
            # CORRECCIÓN: Usar stat().st_mtime en lugar de os.path.getmtime
            backup_files = sorted(
                backup_dir.glob("config_backup_*.ini"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
        except Exception as e:
            self.logger.warning(f"Error limpiando backups antiguos: {str(e)}")

    # Métodos de conveniencia (get, getboolean, getint, getfloat, set)
    def get(self, section: str, option: str, fallback: Any = None) -> Any:
        try:
            return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def getboolean(self, section: str, option: str, fallback: bool = False) -> bool:
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def getint(self, section: str, option: str, fallback: int = 0) -> int:
        try:
            return self.config.getint(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def getfloat(self, section: str, option: str, fallback: float = 0.0) -> float:
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def set(self, section: str, option: str, value: Any) -> bool:
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section, option, str(value))
            return True
        except Exception as e:
            self.logger.error(f"Error estableciendo configuración: {str(e)}")
            return False

    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Retorna toda la configuración como diccionario"""
        settings = {}
        for section in self.config.sections():
            settings[section] = dict(self.config.items(section))
        return settings

    def get_available_languages(self) -> List[str]:
        """Retorna la lista de idiomas disponibles"""
        return ["es", "en", "fr", "de", "it", "pt", "ru", "ja", "zh"]

    def reset_to_defaults(self) -> bool:
        """Restablece la configuración a los valores por defecto"""
        try:
            defaults = self._get_default_config()
            self.config.read_dict(defaults)
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error restableciendo configuración: {str(e)}")
            return False
