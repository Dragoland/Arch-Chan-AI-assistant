#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
from typing import Any, Dict, List, Optional

import requests
from PySide6.QtCore import QObject, Signal

from utils.constants import OLLAMA_API_URL
from utils.logger import get_logger


class OllamaClient(QObject):
    """Cliente mejorado para interactuar con la API de Ollama"""

    # Señales
    response_received = Signal(dict)  # Respuesta completa de Ollama
    stream_chunk_received = Signal(dict)  # Chunk de streaming
    error_occurred = Signal(str)  # Error en la comunicación
    models_updated = Signal(list)  # Lista de modelos disponible
    model_download_progress = Signal(
        str, float
    )  # Progreso de descarga (modelo, porcentaje)

    def __init__(self, base_url: str = OLLAMA_API_URL):
        super().__init__()
        self.logger = get_logger("OllamaClient")
        self.base_url = base_url
        self.timeout = 120  # segundos
        self.max_retries = 3
        self.retry_delay = 2  # segundos

        self.logger.info(f"OllamaClient inicializado con URL: {base_url}")

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

        Args:
            model: Nombre del modelo a usar
            messages: Lista de mensajes en formato {role, content}
            stream: Si se desea streaming de la respuesta
            options: Opciones adicionales para el modelo
            format: Formato de respuesta esperado (ej: json)

        Returns:
            Respuesta de Ollama o None en caso de error
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

                response = requests.post(
                    f"{self.base_url}/chat",
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
                    error_msg = f"Timeout al comunicarse con Ollama después de {self.timeout} segundos"
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
                    error_msg = "No se pudo conectar con Ollama. Verifica que el servicio esté ejecutándose."
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
                    error_msg = f"Error en la comunicación con Ollama: {e}"
                    self.logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return None
                else:
                    self.logger.warning(
                        f"Error en intento {attempt + 1}: {e}, reintentando..."
                    )
                    time.sleep(self.retry_delay)

        return None

    def _handle_stream_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Maneja una respuesta de streaming de Ollama

        Args:
            response: Respuesta de streaming

        Returns:
            Diccionario con la respuesta completa
        """
        full_response = {
            "model": "",
            "message": {"role": "assistant", "content": ""},
            "done": False,
        }

        try:
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    self.stream_chunk_received.emit(chunk)

                    if chunk.get("done"):
                        full_response["done"] = True
                        full_response["model"] = chunk.get("model", "")
                        break

                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        full_response["message"]["content"] += content

            return full_response

        except Exception as e:
            error_msg = f"Error procesando stream de Ollama: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return full_response

    def list_models(self) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene la lista de modelos disponibles en Ollama

        Returns:
            Lista de modelos o None en caso de error
        """
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            self.models_updated.emit(models)
            self.logger.info(f"Modelos disponibles: {len(models)}")
            return models

        except Exception as e:
            error_msg = f"Error obteniendo modelos de Ollama: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def pull_model(self, model: str) -> bool:
        """
        Descarga un modelo de Ollama

        Args:
            model: Nombre del modelo a descargar

        Returns:
            True si la descarga fue exitosa
        """
        try:
            self.logger.info(f"Iniciando descarga del modelo: {model}")
            response = requests.post(
                f"{self.base_url}/pull",
                json={"name": model},
                stream=True,
                timeout=300,  # 5 minutos para la descarga
            )
            response.raise_for_status()

            # Procesar stream de progreso
            total_size = 0
            downloaded_size = 0

            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    status = chunk.get("status", "")

                    # Calcular progreso si está disponible
                    if "completed" in chunk and "total" in chunk:
                        completed = chunk["completed"]
                        total = chunk["total"]
                        if total > 0:
                            progress = (completed / total) * 100
                            self.model_download_progress.emit(model, progress)

                    self.logger.info(f"Progreso de descarga de {model}: {status}")

                    if chunk.get("done", False):
                        self.logger.info(f"Descarga de {model} completada")
                        self.model_download_progress.emit(model, 100.0)
                        return True

            return False

        except Exception as e:
            error_msg = f"Error descargando modelo {model}: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def delete_model(self, model: str) -> bool:
        """
        Elimina un modelo de Ollama

        Args:
            model: Nombre del modelo a eliminar

        Returns:
            True si la eliminación fue exitosa
        """
        try:
            self.logger.info(f"Eliminando modelo: {model}")
            response = requests.delete(
                f"{self.base_url}/delete", json={"name": model}, timeout=30
            )
            response.raise_for_status()
            self.logger.info(f"Modelo {model} eliminado correctamente")
            return True

        except Exception as e:
            error_msg = f"Error eliminando modelo {model}: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def check_health(self) -> bool:
        """
        Verifica que Ollama esté saludable

        Returns:
            True si Ollama responde correctamente
        """
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada de un modelo

        Args:
            model: Nombre del modelo

        Returns:
            Información del modelo o None
        """
        try:
            response = requests.post(
                f"{self.base_url}/show", json={"name": model}, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.warning(
                f"No se pudo obtener información del modelo {model}: {e}"
            )
            return None

    def create_custom_model(self, modelfile_content: str, model_name: str) -> bool:
        """
        Crea un modelo personalizado desde un Modelfile

        Args:
            modelfile_content: Contenido del Modelfile
            model_name: Nombre del nuevo modelo

        Returns:
            True si la creación fue exitosa
        """
        try:
            self.logger.info(f"Creando modelo personalizado: {model_name}")
            response = requests.post(
                f"{self.base_url}/create",
                json={"name": model_name, "modelfile": modelfile_content},
                timeout=120,
            )
            response.raise_for_status()
            self.logger.info(f"Modelo {model_name} creado correctamente")
            return True

        except Exception as e:
            error_msg = f"Error creando modelo {model_name}: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
