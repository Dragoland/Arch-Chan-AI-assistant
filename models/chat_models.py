#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageRole(Enum):
    """Roles de los mensajes en el chat"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(Enum):
    """Tipos de mensajes"""

    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"


@dataclass
class ChatMessage:
    """Modelo para un mensaje de chat"""

    role: MessageRole
    content: str
    timestamp: datetime
    message_type: MessageType = MessageType.TEXT
    tool_name: Optional[str] = None
    tool_parameters: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None
    message_id: Optional[str] = None

    def __post_init__(self):
        """Inicialización posterior para asegurar valores por defecto"""
        if self.tool_parameters is None:
            self.tool_parameters = {}
        if self.tool_result is None and self.message_type == MessageType.TOOL_RESULT:
            self.tool_result = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el mensaje a diccionario"""
        data = asdict(self)
        data["role"] = self.role.value
        data["message_type"] = self.message_type.value
        data["timestamp"] = self.timestamp.isoformat()

        # CORREGIDO: Limpiar valores None
        if data["tool_parameters"] is None:
            data["tool_parameters"] = {}
        if data["tool_result"] is None:
            data["tool_result"] = {}

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Crea un mensaje desde un diccionario"""
        # CORREGIDO: Manejar conversiones de manera segura
        try:
            data["role"] = MessageRole(data["role"])
        except ValueError:
            data["role"] = MessageRole.USER

        try:
            data["message_type"] = MessageType(data["message_type"])
        except ValueError:
            data["message_type"] = MessageType.TEXT

        data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # CORREGIDO: Asegurar valores por defecto
        if "tool_parameters" not in data or data["tool_parameters"] is None:
            data["tool_parameters"] = {}
        if "tool_result" not in data or data["tool_result"] is None:
            data["tool_result"] = {}
        if "message_id" not in data:
            data["message_id"] = None

        return cls(**data)


@dataclass
class ChatSession:
    """Modelo para una sesión de chat"""

    session_id: str
    created_at: datetime
    messages: List[ChatMessage]
    title: Optional[str] = None
    model_used: str = "arch-chan"
    total_tokens: int = 0

    def __post_init__(self):
        """Inicialización posterior"""
        if self.messages is None:
            self.messages = []

    def add_message(self, message: ChatMessage):
        """Añade un mensaje a la sesión"""
        self.messages.append(message)

    def get_last_message(self) -> Optional[ChatMessage]:
        """Obtiene el último mensaje de la sesión"""
        return self.messages[-1] if self.messages else None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la sesión a diccionario"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "title": self.title,
            "model_used": self.model_used,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        """Crea una sesión desde un diccionario"""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["messages"] = [ChatMessage.from_dict(msg) for msg in data["messages"]]

        # CORREGIDO: Valores por defecto
        if "title" not in data:
            data["title"] = None
        if "model_used" not in data:
            data["model_used"] = "arch-chan"
        if "total_tokens" not in data:
            data["total_tokens"] = 0

        return cls(**data)


@dataclass
class ToolCall:
    """Modelo para una llamada a herramienta"""

    tool_name: str
    parameters: Dict[str, Any]
    call_id: str
    timestamp: datetime

    def __post_init__(self):
        """Inicialización posterior"""
        if self.parameters is None:
            self.parameters = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la llamada a herramienta a diccionario"""
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "call_id": self.call_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ToolResult:
    """Modelo para el resultado de una herramienta"""

    call_id: str
    result: Any
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        return {
            "call_id": self.call_id,
            "result": self.result,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }
