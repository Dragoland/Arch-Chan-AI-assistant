#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import shlex
import time
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Signal

from services.command_executor import CommandExecutor
from services.ollama_client import OllamaClient
from utils.logger import get_logger
from workers.base_worker import BaseWorker


class ChatWorker(BaseWorker):
    """Worker para procesamiento de chat con IA (Patrón moveToThread)"""

    # Señales específicas
    response_generated = Signal(dict)
    tool_execution_started = Signal(str, str)
    tool_execution_finished = Signal(str, dict)
    processing_step = Signal(str)

    def __init__(
        self,
        chat_history: List[Dict[str, str]],
        user_input: str,
        model: str = "llama2",  # Cambiar a modelo por defecto más común
        config_manager: Optional[Any] = None,
    ):
        super().__init__()
        self.logger = get_logger("ChatWorker")

        self.chat_history = chat_history.copy() if chat_history else []
        self.user_input = user_input
        self.model = model

        # Configuración de seguridad simplificada
        self.block_dangerous = True
        self.sudo_confirm = True

        # Servicios - se inicializarán en el hilo del worker
        self.ollama_client = None
        self.command_executor = None

    def _initialize_services(self):
        """Inicializa los servicios en el hilo del worker"""
        try:
            if self.ollama_client is None:
                self.ollama_client = OllamaClient()
                # Configurar para eliminación segura
                self.ollama_client.setParent(self)
                self.ollama_client.error_occurred.connect(self.error_occurred)

            if self.command_executor is None:
                self.command_executor = CommandExecutor()
                # Configurar para eliminación segura
                self.command_executor.setParent(self)
                self.command_executor.error_occurred.connect(self.error_occurred)

        except Exception as e:
            self.logger.error(f"Error inicializando servicios: {str(e)}")

    def safe_delete(self):
        """Eliminación segura del worker y sus servicios"""
        try:
            # Detener servicios primero
            if self.ollama_client:
                self.ollama_client.safe_delete()
                self.ollama_client = None

            if self.command_executor:
                # CommandExecutor puede tener procesos en ejecución
                self.command_executor.stop_current_command()
                self.command_executor = None

            # Llamar al safe_delete del padre
            super().safe_delete()

        except Exception as e:
            self.logger.debug(f"Error en safe_delete: {str(e)}")

    def _execute(self) -> Dict[str, Any]:
        """
        Ejecuta el procesamiento completo del chat
        """
        try:
            # Inicializar servicios en el hilo del worker
            self._initialize_services()

            if not self.ollama_client:
                return {
                    "status": "error",
                    "type": "text",
                    "content": "Error: No se pudo inicializar el cliente de Ollama",
                }

            self.processing_step.emit("Verificando Ollama...")

            # Verificar que Ollama esté disponible
            if not self.ollama_client.check_health():
                return {
                    "status": "error",
                    "type": "text",
                    "content": "Ollama no está disponible. Por favor, inicia el servicio Ollama primero.",
                }

            if self.check_stopped():
                return {"status": "cancelled"}

            self.processing_step.emit("Procesando con modelo de IA...")
            ai_response = self._get_ai_response()

            if self.check_stopped():
                return {"status": "cancelled"}

            # Procesar respuesta de IA
            if self._is_tool_call(ai_response):
                self.processing_step.emit("Ejecutando herramienta...")
                result = self._process_tool_call(ai_response)
            else:
                content = self._extract_content(ai_response)
                result = {
                    "status": "success",
                    "type": "text",
                    "content": content,
                    "tool_used": None,
                }

            self.response_generated.emit(result)
            return result

        except Exception as e:
            self.logger.error(
                f"Error en procesamiento de chat: {str(e)}", exc_info=True
            )
            error_result = {
                "status": "error",
                "error": str(e),
                "type": "text",
                "content": f"Lo siento, ocurrió un error: {str(e)}",
            }
            self.response_generated.emit(error_result)
            return error_result

    def _extract_content(self, ai_response: Dict[str, Any]) -> str:
        """Extrae contenido de la respuesta de IA"""
        # Múltiples formas de extraer el contenido
        if "message" in ai_response and "content" in ai_response["message"]:
            return ai_response["message"]["content"]
        elif "response" in ai_response:
            return ai_response["response"]
        elif "content" in ai_response:
            return ai_response["content"]
        else:
            return str(ai_response)

    def _get_ai_response(self) -> Dict[str, Any]:
        """
        Obtiene respuesta del modelo de IA con manejo robusto de errores
        """
        if not self.ollama_client:
            return {"message": {"content": "Error: Cliente Ollama no disponible"}}

        messages = self.chat_history + [{"role": "user", "content": self.user_input}]

        try:
            self.logger.info(f"Enviando mensaje a modelo: {self.model}")

            # Primero intentar sin formato JSON (más compatible)
            response = self.ollama_client.chat(
                model=self.model, messages=messages, stream=False
            )

            if response:
                self.logger.info("Respuesta recibida de Ollama")
                return response
            else:
                return {"message": {"content": "Error: Respuesta vacía de Ollama"}}

        except Exception as e:
            self.logger.error(f"Error obteniendo respuesta de IA: {str(e)}")
            return {"message": {"content": f"Error de conexión con Ollama: {str(e)}"}}

    # Resto del código se mantiene igual...
    def _is_tool_call(self, ai_response: Dict[str, Any]) -> bool:
        """Verifica si la respuesta de IA es una llamada a herramienta"""
        try:
            content = self._extract_content(ai_response)
            if not content:
                return False

            data = json.loads(content)
            return isinstance(data, dict) and "tool" in data
        except (json.JSONDecodeError, TypeError):
            return False

    def _process_tool_call(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una llamada a herramienta"""
        try:
            content = self._extract_content(ai_response)
            tool_data = json.loads(content)

            tool_type = tool_data.get("tool", "")
            self.tool_execution_started.emit(tool_type, str(tool_data))

            if tool_type == "shell":
                result = self._process_shell_tool(tool_data)
            elif tool_type == "search":
                result = self._process_search_tool(tool_data)
            else:
                result = {
                    "status": "error",
                    "error": f"Tipo de herramienta no soportada: {tool_type}",
                    "type": "text",
                    "content": f"No puedo ejecutar herramientas de tipo '{tool_type}'",
                }

            self.tool_execution_finished.emit(tool_type, result)
            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Error decodificando JSON: {str(e)}")
            return {
                "status": "error",
                "error": "Respuesta de IA no es JSON válido",
                "type": "text",
                "content": self._extract_content(ai_response),
            }

    def _process_shell_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa herramienta de shell con validación de seguridad"""
        if not self.command_executor:
            return {
                "status": "error",
                "error": "Ejecutor de comandos no disponible",
                "type": "text",
                "content": "El ejecutor de comandos no está disponible",
            }

        command = tool_data.get("command", "")
        explanation = tool_data.get("explanation", "Ejecutando comando")

        if not command:
            return {
                "status": "error",
                "error": "Comando vacío",
                "type": "text",
                "content": "El comando proporcionado está vacío",
            }

        # Validación de seguridad
        try:
            is_safe, validation_error = self._validate_command(command)
            if not is_safe:
                self.logger.warning(
                    f"Comando bloqueado: {command}. Razón: {validation_error}"
                )
                return {
                    "status": "error",
                    "error": "Comando bloqueado por seguridad",
                    "type": "text",
                    "content": f"Lo siento, no puedo ejecutar ese comando. Razón: {validation_error}",
                }
        except Exception as e:
            self.logger.error(f"Error validando comando: {e}")
            return {
                "status": "error",
                "error": f"Error de validación: {e}",
                "type": "text",
            }

        # Ejecutar comando
        stdout, stderr, returncode = self.command_executor.execute_command(command)

        # Construir resultado
        result_content = f"{explanation}\n\n"
        result_content += f"**Comando:** `{command}`\n"
        result_content += f"**Código de salida:** {returncode}\n\n"

        if stdout:
            result_content += f"**Salida:**\n```\n{stdout}\n```\n"
        if stderr:
            result_content += f"**Errores:**\n```\n{stderr}\n```\n"

        return {
            "status": "success",
            "type": "tool_result",
            "tool_type": "shell",
            "command": command,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "content": result_content,
        }

    def _validate_command(self, command: str) -> tuple[bool, str]:
        """Valida un comando antes de ejecutarlo."""
        if not self.block_dangerous:
            self.logger.warning("La validación de comandos peligrosos está desactivada")
            return True, ""

        try:
            parts = shlex.split(command)
            if not parts:
                return False, "Comando vacío"

            # Lista negra de comandos peligrosos
            DANGEROUS_COMMANDS = [
                "rm",
                "mkfs",
                "dd",
                "fdisk",
                "gdisk",
                "parted",
                ":(){:|:&};:",  # Fork bomb
                "shutdown",
                "reboot",
                "halt",
                "poweroff",
                "mv",
            ]

            executable = parts[0]
            if executable in ["sh", "bash"] and len(parts) > 2 and parts[1] == "-c":
                inner_parts = shlex.split(parts[2])
                executable = inner_parts[0] if inner_parts else ""

            if executable in DANGEROUS_COMMANDS:
                return False, f"El comando '{executable}' está bloqueado por seguridad."

            return True, ""

        except Exception as e:
            return False, f"Error al analizar el comando: {str(e)}"

    def _process_search_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa herramienta de búsqueda"""
        if not self.command_executor:
            return {"status": "error", "error": "Ejecutor de comandos no disponible"}

        query = tool_data.get("query", "")
        if not query:
            return {"status": "error", "error": "Consulta de búsqueda vacía"}

        # Ejecutar búsqueda (usando ddgr)
        search_command = f"ddgr --json -n 5 --unsafe '{query}'"
        stdout, stderr, returncode = self.command_executor.execute_command(
            search_command, shell=True
        )

        if returncode != 0:
            return {
                "status": "error",
                "error": f"Búsqueda falló con código {returncode}",
                "type": "text",
                "content": f"No pude realizar la búsqueda. Error: {stderr}",
            }

        # Procesar resultados
        try:
            results = json.loads(stdout)
            formatted_results = self._format_search_results(results)

            return {
                "status": "success",
                "type": "tool_result",
                "tool_type": "search",
                "query": query,
                "results": results,
                "content": f"**Resultados de búsqueda para '{query}':**\n\n{formatted_results}",
            }
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decodificando resultados de búsqueda: {str(e)}")
            return {
                "status": "error",
                "error": "No se pudieron analizar los resultados de búsqueda",
                "type": "text",
                "content": f"Realicé la búsqueda pero no pude procesar los resultados. Salida cruda:\n{stdout}",
            }

    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Formatea los resultados de búsqueda"""
        if not results:
            return "No se encontraron resultados."

        formatted = ""
        for i, result in enumerate(results[:3], 1):
            title = result.get("title", "Sin título")
            abstract = result.get("abstract", "Sin descripción")
            url = result.get("url", "Sin URL")

            formatted += f"{i}. **{title}**\n"
            formatted += f"   {abstract}\n"
            formatted += f"   {url}\n\n"

        return formatted
