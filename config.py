#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import configparser
import logging
from pathlib import Path
from datetime import datetime
import sys

# --- Definición de Constantes y Configuración ---

PROJECT_PATH = os.path.expanduser("~/arch-chan-project")
TEMP_PATH = os.path.join(PROJECT_PATH, "temp")
MODELS_PATH = os.path.join(PROJECT_PATH, "models")
LOGS_PATH = os.path.join(PROJECT_PATH, "logs")
CONFIGS_PATH = os.path.join(PROJECT_PATH, "configs")

TTS_MODEL_ONNX = os.path.join(MODELS_PATH, "es_AR-daniela-high.onnx")
TTS_MODEL_JSON = os.path.join(MODELS_PATH, "es_AR-daniela-high.onnx.json")

WHISPER_MODEL = os.path.join(MODELS_PATH, "ggml-base.bin")
AUDIO_INPUT_FILE = os.path.join(TEMP_PATH, "input.wav")

OLLAMA_API_URL = "http://localhost:11434/api/chat"
CONFIG_FILE = os.path.join(PROJECT_PATH, "config.ini")

# Lista de modelos optimizados
DEFAULT_MODELS = ['arch-chan', 'arch-chan-lite', 'llama3.2:3b', 'gemma:2b']

# Variables globales para ejecutables
WHISPER_EXE = "whisper-cli"
PIPER_EXE = "piper-tts"
KDESU_AVAILABLE = None

# Nuevas constantes para mejoras
SUPPORTED_LANGUAGES = ['es', 'en', 'fr', 'de', 'it']
BACKUP_INTERVAL = 5  # minutos

# --- Configuración de Logging ---

def setup_logging():
    """Configura el sistema de logging"""
    Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)

    log_file = os.path.join(LOGS_PATH, f"arch-chan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("ArchChan")

logger = setup_logging()

# --- Manejo de Configuración ---

class ConfigManager:
    """Gestiona la configuración persistente de la aplicación"""

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = CONFIG_FILE

    def load_config(self):
        """Carga la configuración desde archivo o crea una por defecto"""
        defaults = {
            'General': {
                'model': 'arch-chan',
                'auto_cleanup': 'true',
                'max_history': '20',
                'notifications': 'true',
                'voice_enabled': 'true',
                'theme': 'arch-dark',
                'language': 'es',
                'auto_update': 'false',
                'backup_enabled': 'true'
            },
            'Paths': {
                'project_path': PROJECT_PATH,
                'models_path': MODELS_PATH,
                'temp_path': TEMP_PATH,
                'configs_path': CONFIGS_PATH
            },
            'Audio': {
                'sample_rate': '22050',
                'silence_threshold': '5%',
                'voice_volume': '80',
                'noise_reduction': 'true',
                'audio_quality': 'high'
            },
            'UI': {
                'window_width': '900',
                'window_height': '700',
                'sidebar_visible': 'true',
                'font_size': '11',
                'animations': 'true',
                'compact_mode': 'false'
            },
            'Advanced': {
                'timeout_duration': '120',
                'max_response_length': '4000',
                'retry_attempts': '3',
                'cache_responses': 'true'
            }
        }

        # Crear directorios si no existen
        for path in [PROJECT_PATH, MODELS_PATH, TEMP_PATH, LOGS_PATH, CONFIGS_PATH]:
            Path(path).mkdir(parents=True, exist_ok=True)

        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
            
            # Migrar configuraciones antiguas
            self.migrate_old_config()
        else:
            self.config.read_dict(defaults)
            self.save_config()

        return self.config

    def migrate_old_config(self):
        """Migra configuraciones de versiones anteriores"""
        # Migrar sección UI si no existe
        if not self.config.has_section('UI'):
            self.config.add_section('UI')
            self.config.set('UI', 'theme', 'arch-dark')
            self.config.set('UI', 'sidebar_visible', 'true')
            self.config.set('UI', 'font_size', '11')
            self.config.set('UI', 'animations', 'true')
            self.config.set('UI', 'compact_mode', 'false')
        
        # Migrar sección Advanced si no existe
        if not self.config.has_section('Advanced'):
            self.config.add_section('Advanced')
            self.config.set('Advanced', 'timeout_duration', '120')
            self.config.set('Advanced', 'max_response_length', '4000')
            self.config.set('Advanced', 'retry_attempts', '3')
            self.config.set('Advanced', 'cache_responses', 'true')
        
        # Migrar nuevas opciones de General
        if not self.config.has_option('General', 'language'):
            self.config.set('General', 'language', 'es')
        if not self.config.has_option('General', 'auto_update'):
            self.config.set('General', 'auto_update', 'false')
        if not self.config.has_option('General', 'backup_enabled'):
            self.config.set('General', 'backup_enabled', 'true')
            
        # Migrar nuevas opciones de Audio
        if not self.config.has_option('Audio', 'noise_reduction'):
            self.config.set('Audio', 'noise_reduction', 'true')
        if not self.config.has_option('Audio', 'audio_quality'):
            self.config.set('Audio', 'audio_quality', 'high')
            
        self.save_config()

    def save_config(self):
        """Guarda la configuración actual"""
        try:
            # Crear backup antes de guardar
            if self.config.getboolean('General', 'backup_enabled', fallback=True):
                self.create_config_backup()
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.info("Configuración guardada correctamente")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")

    def create_config_backup(self):
        """Crea un backup de la configuración"""
        try:
            backup_dir = os.path.join(CONFIGS_PATH, "backups")
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            
            backup_file = os.path.join(
                backup_dir, 
                f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ini"
            )
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
                
            logger.info(f"Backup de configuración creado: {backup_file}")
        except Exception as e:
            logger.warning(f"No se pudo crear backup: {e}")

    def get_available_themes(self):
        """Retorna la lista de temas disponibles"""
        return ['arch-dark', 'arch-light', 'blue-matrix', 'green-terminal', 'purple-haze']

    def get_available_languages(self):
        """Retorna la lista de idiomas disponibles"""
        return SUPPORTED_LANGUAGES

# --- Excepciones Personalizadas ---

class SecurityError(Exception):
    """Excepción para errores de seguridad"""
    pass

class CommandTimeoutError(Exception):
    """Excepción para timeouts de comandos"""
    pass

class DependencyError(Exception):
    """Excepción para dependencias faltantes"""
    pass

class ModelNotFoundError(Exception):
    """Excepción para modelos no encontrados"""
    pass

# --- Estados de la Aplicación ---

class AppState:
    """Define los estados posibles de la aplicación"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"
    UPDATING = "updating"