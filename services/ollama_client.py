#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
from typing import Any, Dict, List, Optional

import requests
from PySide6.QtCore import QObject, Signal

from utils.constants import OLLAMA_BASE_URL
from utils.logger import get_logger


class OllamaClient(QObject):
    """Cliente mejorado para interactuar con la API de Ollama"""

    # Señales
    response_received = Signal(dict)
    stream_chunk_received = Signal(dict)
    error_occurred = Signal(str)
    models_updated = Signal(list)
    model_download_progress = Signal(str, float)
    connection_status_changed = Signal(bool)

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        super().__init__()
        self.logger = get_logger("OllamaClient")
        self.base_url = base_url.rstrip("/")
        self.timeout = 30
        self.max_retries = 2
        self.retry_delay = 1

        # Configurar session con mejores timeouts
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "Arch-Chan-AI-Assistant/2.1.0",
            }
        )

        # Adapter con timeouts más agresivos para health checks
        self.session.mount(
            "http://",
            requests.adapters.HTTPAdapter(
                max_retries=1, pool_connections=10, pool_maxsize=10
            ),
        )

        self.logger.info(f"OllamaClient inicializado con URL: {self.base_url}")

    def test_connection(self) -> Dict[str, Any]:
        """Método de prueba para diagnóstico"""
        result = {
            "base_url": self.base_url,
            "health_check": self.check_health(),
            "models": None,
            "error": None,
        }

        try:
            if result["health_check"]:
                result["models"] = self.list_models()
        except Exception as e:
            result["error"] = str(e)

        return result

    def check_health(self) -> bool:
        """
        Verifica que Ollama esté saludable con múltiples métodos
        """
        # Método 1: Verificar conectividad básica
        if not self._check_connectivity():
            self.connection_status_changed.emit(False)
            return False

        # Método 2: Verificar API
        if not self._check_api_health():
            self.connection_status_changed.emit(False)
            return False

        self.connection_status_changed.emit(True)
        return True

    def _check_connectivity(self) -> bool:
        """Verifica conectividad básica con el servidor"""
        try:
            # Intentar conectar al puerto
            response = self.session.get(
                f"{self.base_url}",
                timeout=2,
                params={"_t": int(time.time())},  # Evitar cache
            )
            # Cualquier respuesta indica que el servicio está arriba
            self.logger.debug(f"Connectivity check: {response.status_code}")
            return response.status_code < 500
        except requests.exceptions.ConnectionError:
            self.logger.debug("No se puede conectar al puerto 11434")
            return False
        except requests.exceptions.Timeout:
            self.logger.debug("Timeout en verificación de conectividad")
            return False
        except Exception as e:
            self.logger.debug(f"Error en verificación de conectividad: {e}")
            return False

    def _check_api_health(self) -> bool:
        """Verifica que la API de Ollama esté funcionando"""
        endpoints = [
            f"{self.base_url}/api/tags",
            f"{self.base_url}/api/version",
            f"{self.base_url}/api/models",  # Algunas versiones usan este endpoint
        ]

        for endpoint in endpoints:
            try:
                self.logger.debug(f"Probando endpoint: {endpoint}")
                response = self.session.get(
                    endpoint, timeout=3, params={"_t": int(time.time())}  # Evitar cache
                )

                if response.status_code == 200:
                    self.logger.info(f"Ollama API saludable en {endpoint}")
                    return True
                else:
                    self.logger.debug(
                        f"Endpoint {endpoint} respondió con {response.status_code}"
                    )

            except requests.exceptions.RequestException as e:
                self.logger.debug(f"Error en endpoint {endpoint}: {e}")
                continue
            except Exception as e:
                self.logger.debug(f"Error inesperado en {endpoint}: {e}")
                continue

        self.logger.warning("Ningún endpoint de Ollama respondió correctamente")
        return False

    def list_models(self) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene la lista de modelos disponibles
        """
        endpoints = [f"{self.base_url}/api/tags", f"{self.base_url}/api/models"]

        for endpoint in endpoints:
            try:
                self.logger.debug(f"Obteniendo modelos desde: {endpoint}")
                response = self.session.get(endpoint, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    # Manejar diferentes formatos de respuesta
                    if "models" in data:
                        models = data["models"]
                    elif isinstance(data, list):
                        models = data
                    else:
                        models = []

                    self.logger.info(f"Modelos disponibles: {len(models)}")
                    self.models_updated.emit(models)
                    return models

            except Exception as e:
                self.logger.debug(f"Error obteniendo modelos desde {endpoint}: {e}")
                continue

        error_msg = "No se pudieron obtener los modelos de Ollama"
        self.logger.error(error_msg)
        self.error_occurred.emit(error_msg)
        return None

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
        format: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Envía un mensaje de chat a Ollama
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": options
            or {"temperature": 0.7, "top_k": 40, "top_p": 0.9, "num_ctx": 4096},
        }

        if format:
            payload["format"] = format

        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"Enviando chat a Ollama (modelo: {model}, mensajes: {len(messages)})"
                )

                response = self.session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout,
                    stream=stream,
                )
                response.raise_for_status()

                if stream:
                    return self._handle_stream_response(response)
                else:
                    result = response.json()
                    self.response_received.emit(result)
                    return result

            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    error_msg = f"Timeout al comunicarse con Ollama"
                    self.logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return None
                else:
                    self.logger.warning(
                        f"Timeout en intento {attempt + 1}, reintentando..."
                    )
                    time.sleep(self.retry_delay)

            except requests.exceptions.ConnectionError:
                if attempt == self.max_retries - 1:
                    error_msg = "No se pudo conectar con Ollama"
                    self.logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return None
                else:
                    self.logger.warning(
                        f"Error de conexión en intento {attempt + 1}, reintentando..."
                    )
                    time.sleep(self.retry_delay)

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    error_msg = f"Error en la comunicación con Ollama: {str(e)}"
                    self.logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return None
                else:
                    self.logger.warning(
                        f"Error en intento {attempt + 1}: {str(e)}, reintentando..."
                    )
                    time.sleep(self.retry_delay)

            except Exception as e:
                if attempt == self.max_retries - 1:
                    error_msg = f"Error inesperado: {str(e)}"
                    self.logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return None
                else:
                    self.logger.warning(
                        f"Error inesperado en intento {attempt + 1}: {str(e)}"
                    )
                    time.sleep(self.retry_delay)

        return None

    def _handle_stream_response(self, response: requests.Response) -> Dict[str, Any]:
        """Maneja una respuesta de streaming de Ollama"""
        full_response = {
            "model": "",
            "message": {"role": "assistant", "content": ""},
            "done": False,
        }

        try:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                        self.stream_chunk_received.emit(chunk)

                        if chunk.get("done"):
                            full_response["done"] = True
                            full_response["model"] = chunk.get("model", "")
                            for key in chunk:
                                if key not in full_response:
                                    full_response[key] = chunk[key]
                            break

                        if "message" in chunk and "content" in chunk["message"]:
                            content = chunk["message"]["content"]
                            full_response["message"]["content"] += content

                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Error decodificando chunk JSON: {str(e)}")
                        continue

            return full_response

        except Exception as e:
            error_msg = f"Error procesando stream de Ollama: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return full_response

    def wait_for_ollama(self, max_wait: int = 10, check_interval: int = 2) -> bool:
        """
        Espera a que Ollama esté disponible
        """
        import time

        self.logger.info(
            f"Esperando a que Ollama esté disponible (máximo {max_wait} segundos)..."
        )

        start_time = time.time()
        checks = 0

        while time.time() - start_time < max_wait:
            checks += 1
            self.logger.debug(f"Verificación #{checks} de Ollama...")

            if self.check_health():
                elapsed = time.time() - start_time
                self.logger.info(
                    f"Ollama está disponible después de {elapsed:.1f} segundos"
                )
                return True

            self.logger.debug(
                f"Ollama no disponible, reintentando en {check_interval} segundos..."
            )
            time.sleep(check_interval)

        self.logger.warning(f"Ollama no disponible después de {max_wait} segundos")
        return False

    def diagnostic_check(self) -> Dict[str, Any]:
        """
        Realiza una verificación de diagnóstico completa
        """
        result = {
            "base_url": self.base_url,
            "connectivity": False,
            "api_health": False,
            "models_available": False,
            "model_count": 0,
            "endpoints_tested": [],
            "error": None,
        }

        try:
            # Verificar conectividad básica
            result["connectivity"] = self._check_connectivity()

            # Verificar API
            result["api_health"] = self._check_api_health()

            # Verificar modelos
            if result["api_health"]:
                models = self.list_models()
                if models:
                    result["models_available"] = True
                    result["model_count"] = len(models)
                    result["models"] = [
                        model.get("name", "Unknown") for model in models
                    ]

        except Exception as e:
            result["error"] = str(e)

        self.logger.info(f"Diagnóstico de Ollama: {result}")
        return result

    def pull_model(self, model: str) -> bool:
        """Descarga un modelo de Ollama"""
        try:
            self.logger.info(f"Iniciando descarga del modelo: {model}")
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                stream=True,
                timeout=300,
            )
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    line = line.strip()
                    if line.startswith("data: "):
                        line = line[6:]

                    try:
                        chunk = json.loads(line)
                        status = chunk.get("status", "")

                        if "completed" in chunk and "total" in chunk:
                            completed = chunk["completed"]
                            total = chunk["total"]
                            if total > 0:
                                progress = (completed / total) * 100
                                self.model_download_progress.emit(model, progress)

                        self.logger.debug(f"Progreso de descarga de {model}: {status}")

                        if chunk.get("status") == "success":
                            self.logger.info(f"Descarga de {model} completada")
                            self.model_download_progress.emit(model, 100.0)
                            return True

                    except json.JSONDecodeError:
                        continue

            return False

        except Exception as e:
            error_msg = f"Error descargando modelo {model}: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada de un modelo"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/show", json={"name": model}, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.warning(
                f"No se pudo obtener información del modelo {model}: {str(e)}"
            )
            return None

    def __del__(self):
        """Cleanup - MEJORADO"""
        try:
            if hasattr(self, "session"):
                self.session.close()
        except Exception as e:
            # Solo log, no emitir señales en destructor
            pass

    def safe_delete(self):
        """Eliminación segura del cliente"""
        try:
            self.disconnect()  # Desconectar todas las señales
            if hasattr(self, "session"):
                self.session.close()
        except Exception as e:
            self.logger.debug(f"Error en safe_delete: {str(e)}")
