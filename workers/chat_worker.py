#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import time
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Signal

from services.command_executor import CommandExecutor
from services.ollama_client import OllamaClient
from services.speech_service import SpeechService
from utils.logger import get_logger
from workers.base_worker import BaseWorker


class ChatWorker(BaseWorker):
    """Worker para procesamiento de chat con IA"""

    # Señales específicas
    response_generated = Signal(dict)  # Respuesta de IA generada
    tool_execution_started = Signal(
        str, str
    )  # Herramienta ejecutada (tipo, comando/query)
    tool_execution_finished = Signal(
        str, dict
    )  # Herramienta finalizada (tipo, resultado)
    processing_step = Signal(str)  # Paso actual del procesamiento

    def __init__(
        self,
        chat_history: List[Dict[str, str]],
        user_input: str,
        model: str = "arch-chan",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.logger = get_logger("ChatWorker")

        self.chat_history = chat_history
        self.user_input = user_input
        self.model = model
        self.config = config or {}

        # Servicios
        self.ollama_client = OllamaClient()
        self.command_executor = CommandExecutor()
        self.speech_service = SpeechService()

        # Conectar señales de servicios
        self._connect_service_signals()

    def _connect_service_signals(self):
        """Conecta las señales de los servicios"""
        self.ollama_client.error_occurred.connect(self.error_occurred)
        self.command_executor.error_occurred.connect(self.error_occurred)

    def _execute(self) -> Dict[str, Any]:
        """
        Ejecuta el procesamiento completo del chat

        Returns:
            Diccionario con el resultado del procesamiento
        """
        try:
            self.processing_step.emit("Analizando intención del usuario...")
            intent = self._analyze_intent(self.user_input)

            self.processing_step.emit("Procesando con modelo de IA...")
            ai_response = self._get_ai_response()

            if self.check_stopped():
                return {"status": "cancelled"}

            # Procesar respuesta de IA
            if self._is_tool_call(ai_response):
                self.processing_step.emit("Ejecutando herramienta...")
                result = self._process_tool_call(ai_response)
            else:
                result = {
                    "status": "success",
                    "type": "text",
                    "content": ai_response.get("message", {}).get("content", ""),
                    "tool_used": None,
                }

            return result

        except Exception as e:
            self.logger.error(f"Error en procesamiento de chat: {e}")
            return {
                "status": "error",
                "error": str(e),
                "type": "text",
                "content": f"Lo siento, ocurrió un error: {e}",
            }

    def _analyze_intent(self, user_input: str) -> str:
        """
        Analiza la intención del usuario

        Args:
            user_input: Entrada del usuario

        Returns:
            Intención detectada
        """
        input_lower = user_input.lower()

        # Patrones para comandos shell
        shell_patterns = [
            r"ejecuta",
            r"corre",
            r"run",
            r"ejecutar",
            r"correr",
            r"instala",
            r"install",
            r"instalar",
            r"remueve",
            r"remove",
            r"muestra",
            r"muéstrame",
            r"show me",
            r"display",
            r"qué procesos",
            r"qué espacio",
            r"cuánto espacio",
        ]

        # Patrones para búsquedas
        search_patterns = [
            r"noticias",
            r"news",
            r"últimas",
            r"recientes",
            r"busca",
            r"search",
            r"búscame",
            r"find",
        ]

        for pattern in shell_patterns:
            if pattern in input_lower:
                return "shell"

        for pattern in search_patterns:
            if pattern in input_lower:
                return "search"

        return "conversation"

    def _get_ai_response(self) -> Dict[str, Any]:
        """
        Obtiene respuesta del modelo de IA

        Returns:
            Respuesta de Ollama
        """
        messages = self.chat_history + [{"role": "user", "content": self.user_input}]

        response = self.ollama_client.chat(
            model=self.model, messages=messages, stream=False
        )

        return response or {}

    def _is_tool_call(self, ai_response: Dict[str, Any]) -> bool:
        """
        Verifica si la respuesta de IA es una llamada a herramienta

        Args:
            ai_response: Respuesta de IA

        Returns:
            True si es una llamada a herramienta
        """
        try:
            content = ai_response.get("message", {}).get("content", "")
            data = json.loads(content)
            return isinstance(data, dict) and "tool" in data
        except:
            return False

    def _process_tool_call(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una llamada a herramienta

        Args:
            ai_response: Respuesta de IA con herramienta

        Returns:
            Resultado del procesamiento
        """
        try:
            content = ai_response.get("message", {}).get("content", "")
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

        except json.JSONDecodeError:
            return {
                "status": "error",
                "error": "Respuesta de IA no es JSON válido",
                "type": "text",
                "content": ai_response.get("message", {}).get("content", ""),
            }

    def _process_shell_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa herramienta de shell

        Args:
            tool_data: Datos de la herramienta

        Returns:
            Resultado de la ejecución
        """
        command = tool_data.get("command", "")
        explanation = tool_data.get("explanation", "Ejecutando comando")

        if not command:
            return {
                "status": "error",
                "error": "Comando vacío",
                "type": "text",
                "content": "El comando proporcionado está vacío",
            }

        # Ejecutar comando
        stdout, stderr, returncode = self.command_executor.execute_command(command)

        # Construir resultado
        result_content = f"{explanation}\n\n"
        result_content += f"**Comando:** `{command}`\n"
        result_content += f"**Código de salida:** {returncode}\n\n"

        if stdout:
            result_content += f"**Salida:**\n{stdout}\n"

        if stderr:
            result_content += f"**Errores:**\n{stderr}\n"

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

    def _process_search_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa herramienta de búsqueda

        Args:
            tool_data: Datos de la herramienta

        Returns:
            Resultado de la búsqueda
        """
        query = tool_data.get("query", "")

        if not query:
            return {
                "status": "error",
                "error": "Consulta de búsqueda vacía",
                "type": "text",
                "content": "La consulta de búsqueda está vacía",
            }

        # Ejecutar búsqueda (usando ddgr)
        search_command = f"ddgr --json -n 5 --unsafe '{query}'"
        stdout, stderr, returncode = self.command_executor.execute_command(
            search_command
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
        except json.JSONDecodeError:
            return {
                "status": "error",
                "error": "No se pudieron analizar los resultados de búsqueda",
                "type": "text",
                "content": f"Realicé la búsqueda pero no pude procesar los resultados. Salida cruda:\n{stdout}",
            }

    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Formatea los resultados de búsqueda

        Args:
            results: Resultados de búsqueda

        Returns:
            Resultados formateados
        """
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

    def get_final_result(self) -> Dict[str, Any]:
        """
        Retorna el resultado final del worker

        Returns:
            Resultado del procesamiento
        """
        return self._result or {}
