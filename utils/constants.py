#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Constantes globales para la aplicación Arch-Chan"""

import os
from pathlib import Path

from config import CONFIGS_PATH

# Versión de la aplicación
APP_VERSION = "2.1"
APP_NAME = "Arch-Chan AI Assistant"

# URLs y endpoints
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/api"
OLLAMA_CHAT_URL = f"{OLLAMA_API_URL}/chat"
OLLAMA_TAGS_URL = f"{OLLAMA_API_URL}/tags"
OLLAMA_GENERATE_URL = f"{OLLAMA_API_URL}/generate"
OLLAMA_EMBEDDINGS_URL = f"{OLLAMA_API_URL}/embeddings"
OLLAMA_PULL_URL = f"{OLLAMA_API_URL}/pull"
OLLAMA_DELETE_URL = f"{OLLAMA_API_URL}/delete"
OLLAMA_SHOW_URL = f"{OLLAMA_API_URL}/show"
OLLAMA_CREATE_URL = f"{OLLAMA_API_URL}/create"
OLLAMA_VERSION_URL = f"{OLLAMA_API_URL}/version"
OLLAMA_PS_URL = f"{OLLAMA_API_URL}/ps"


# Modelos por defecto
DEFAULT_MODELS = ["arch-chan", "arch-chan-lite", "llama3.2:3b", "gemma:2b"]

# Idiomas soportados
SUPPORTED_LANGUAGES = ["es", "en", "fr", "de", "it"]

# Configuración de audio por defecto
DEFAULT_SAMPLE_RATE = 22050
DEFAULT_SILENCE_THRESHOLD = "5%"

# Límites de la aplicación
MAX_HISTORY_MESSAGES = 20
MAX_RESPONSE_LENGTH = 4000
DEFAULT_TIMEOUT = 120

# Rutas de la aplicación
HOME_DIR = Path.home()
PROJECT_DIR = HOME_DIR / "arch-chan-project"
MODELS_DIR = PROJECT_DIR / "models"
TEMP_DIR = PROJECT_DIR / "temp"
LOGS_DIR = PROJECT_DIR / "logs"
CONFIG_FILE = PROJECT_DIR / "config.ini"

# Rutas de modelos de voz (relativas a MODELS_DIR)
TTS_MODEL_ONNX = "es_AR-daniela-high.onnx"
TTS_MODEL_JSON = "es_AR-daniela-high.onnx.json"
WHISPER_MODEL = "ggml-base.bin"
AUDIO_INPUT_FILE = "input.wav"

# Crear directorios si no existen
for directory in [PROJECT_DIR, MODELS_DIR, TEMP_DIR, LOGS_DIR]:
    if isinstance(directory, Path):
        directory.mkdir(parents=True, exist_ok=True)
    else:
        # Si es un string, convertirlo a Path
        Path(directory).expanduser().mkdir(parents=True, exist_ok=True)

# Manejar CONFIGS_PATH por separado si existe
if "CONFIGS_PATH" in globals():
    configs_path = Path(CONFIGS_PATH).expanduser()
    configs_path.mkdir(parents=True, exist_ok=True)
