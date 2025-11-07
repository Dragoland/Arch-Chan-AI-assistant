#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Constantes globales para la aplicación Arch-Chan"""

# Versión de la aplicación
APP_VERSION = "2.1"
APP_NAME = "Arch-Chan AI Assistant"

# URLs y endpoints
OLLAMA_API_URL = "http://localhost:11434/api/chat"

# Modelos por defecto
DEFAULT_MODELS = ['arch-chan', 'arch-chan-lite', 'llama3.2:3b', 'gemma:2b']

# Idiomas soportados
SUPPORTED_LANGUAGES = ['es', 'en', 'fr', 'de', 'it']

# Configuración de audio por defecto
DEFAULT_SAMPLE_RATE = "22050"
DEFAULT_SILENCE_THRESHOLD = "5%"

# Límites de la aplicación
MAX_HISTORY_MESSAGES = 20
MAX_RESPONSE_LENGTH = 4000
DEFAULT_TIMEOUT = 120

# Rutas de modelos (se sobreescriben desde config)
TTS_MODEL_ONNX = "es_AR-daniela-high.onnx"
TTS_MODEL_JSON = "es_AR-daniela-high.onnx.json"
WHISPER_MODEL = "ggml-base.bin"
AUDIO_INPUT_FILE = "input.wav"
