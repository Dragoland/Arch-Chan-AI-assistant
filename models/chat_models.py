#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageRole(Enum):
    """Roles de los mensajes en el chat"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

    @classmethod
    def from_string(cls, role_str: str) -> "MessageRole":
        """Convierte string a MessageRole de forma segura"""
        try:
            return cls(role_str)
        except ValueError:
            return cls.USER


class MessageType(Enum):
    """Tipos de mensajes"""

    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SYSTEM = "system"
    WARNING = "warning"

    @classmethod
    def from_string(cls, type_str: str) -> "MessageType":
        """Convierte string a MessageType de forma segura"""
        try:
            return cls(type_str)
        except ValueError:
            return cls.TEXT


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
    message_id: str = None
    tokens: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Inicialización posterior para asegurar valores por defecto"""
        if self.tool_parameters is None:
            self.tool_parameters = {}
        if self.tool_result is None and self.message_type == MessageType.TOOL_RESULT:
            self.tool_result = {}
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el mensaje a diccionario"""
        data = asdict(self)
        data["role"] = self.role.value
        data["message_type"] = self.message_type.value
        data["timestamp"] = self.timestamp.isoformat()

        # Limpiar valores None
        data = {k: v for k, v in data.items() if v is not None}

        # Asegurar valores por defecto para diccionarios
        if "tool_parameters" not in data:
            data["tool_parameters"] = {}
        if "tool_result" not in data:
            data["tool_result"] = {}
        if "metadata" not in data:
            data["metadata"] = {}

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Crea un mensaje desde un diccionario"""
        # Crear copia para no modificar el original
        msg_data = data.copy()

        # Convertir role
        try:
            msg_data["role"] = MessageRole(msg_data["role"])
        except (ValueError, KeyError):
            msg_data["role"] = MessageRole.USER

        # Convertir message_type
        try:
            msg_data["message_type"] = MessageType(msg_data.get("message_type", "text"))
        except (ValueError, KeyError):
            msg_data["message_type"] = MessageType.TEXT

        # Convertir timestamp
        timestamp_str = msg_data.get("timestamp")
        if timestamp_str:
            try:
                msg_data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                msg_data["timestamp"] = datetime.now()
        else:
            msg_data["timestamp"] = datetime.now()

        # Asegurar valores por defecto
        if "tool_parameters" not in msg_data or msg_data["tool_parameters"] is None:
            msg_data["tool_parameters"] = {}
        if "tool_result" not in msg_data or msg_data["tool_result"] is None:
            msg_data["tool_result"] = {}
        if "message_id" not in msg_data or msg_data["message_id"] is None:
            msg_data["message_id"] = str(uuid.uuid4())
        if "tokens" not in msg_data:
            msg_data["tokens"] = 0
        if "metadata" not in msg_data or msg_data["metadata"] is None:
            msg_data["metadata"] = {}

        return cls(**msg_data)

    @classmethod
    def create_user_message(cls, content: str, **kwargs) -> "ChatMessage":
        """Crea un mensaje de usuario"""
        return cls(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now(),
            message_type=MessageType.TEXT,
            **kwargs,
        )

    @classmethod
    def create_assistant_message(cls, content: str, **kwargs) -> "ChatMessage":
        """Crea un mensaje del asistente"""
        return cls(
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
            message_type=MessageType.TEXT,
            **kwargs,
        )

    @classmethod
    def create_tool_call(
        cls, tool_name: str, parameters: Dict[str, Any], **kwargs
    ) -> "ChatMessage":
        """Crea un mensaje de llamada a herramienta"""
        return cls(
            role=MessageRole.ASSISTANT,
            content=f"Calling tool: {tool_name}",
            timestamp=datetime.now(),
            message_type=MessageType.TOOL_CALL,
            tool_name=tool_name,
            tool_parameters=parameters,
            **kwargs,
        )

    @classmethod
    def create_tool_result(cls, tool_name: str, result: Any, **kwargs) -> "ChatMessage":
        """Crea un mensaje de resultado de herramienta"""
        return cls(
            role=MessageRole.TOOL,
            content=f"Tool result: {tool_name}",
            timestamp=datetime.now(),
            message_type=MessageType.TOOL_RESULT,
            tool_name=tool_name,
            tool_result=result,
            **kwargs,
        )

    @classmethod
    def create_error_message(cls, error: str, **kwargs) -> "ChatMessage":
        """Crea un mensaje de error"""
        return cls(
            role=MessageRole.SYSTEM,
            content=f"Error: {error}",
            timestamp=datetime.now(),
            message_type=MessageType.ERROR,
            **kwargs,
        )

    def is_tool_call(self) -> bool:
        """Verifica si es una llamada a herramienta"""
        return self.message_type == MessageType.TOOL_CALL

    def is_tool_result(self) -> bool:
        """Verifica si es un resultado de herramienta"""
        return self.message_type == MessageType.TOOL_RESULT

    def is_error(self) -> bool:
        """Verifica si es un mensaje de error"""
        return self.message_type == MessageType.ERROR

    def get_content_preview(self, max_length: int = 100) -> str:
        """Obtiene una vista previa del contenido"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."


@dataclass
class ChatSession:
    """Modelo para una sesión de chat"""

    session_id: str
    created_at: datetime
    messages: List[ChatMessage] = field(default_factory=list)
    title: Optional[str] = None
    model_used: str = "arch-chan"
    total_tokens: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Inicialización posterior"""
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}

    def add_message(self, message: ChatMessage):
        """Añade un mensaje a la sesión"""
        self.messages.append(message)
        self.total_tokens += message.tokens

    def get_last_message(self) -> Optional[ChatMessage]:
        """Obtiene el último mensaje de la sesión"""
        return self.messages[-1] if self.messages else None

    def get_message_count(self) -> int:
        """Obtiene el número total de mensajes"""
        return len(self.messages)

    def get_user_messages(self) -> List[ChatMessage]:
        """Obtiene todos los mensajes del usuario"""
        return [msg for msg in self.messages if msg.role == MessageRole.USER]

    def get_assistant_messages(self) -> List[ChatMessage]:
        """Obtiene todos los mensajes del asistente"""
        return [msg for msg in self.messages if msg.role == MessageRole.ASSISTANT]

    def clear_messages(self):
        """Limpia todos los mensajes de la sesión"""
        self.messages.clear()
        self.total_tokens = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la sesión a diccionario"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "title": self.title,
            "model_used": self.model_used,
            "total_tokens": self.total_tokens,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        """Crea una sesión desde un diccionario"""
        # Manejar conversión de created_at
        created_at_str = data.get("created_at")
        if created_at_str:
            try:
                data["created_at"] = datetime.fromisoformat(created_at_str)
            except (ValueError, TypeError):
                data["created_at"] = datetime.now()
        else:
            data["created_at"] = datetime.now()

        # Convertir mensajes
        messages_data = data.get("messages", [])
        data["messages"] = [ChatMessage.from_dict(msg) for msg in messages_data]

        # Valores por defecto
        if "title" not in data:
            data["title"] = None
        if "model_used" not in data:
            data["model_used"] = "arch-chan"
        if "total_tokens" not in data:
            data["total_tokens"] = 0
        if "metadata" not in data or data["metadata"] is None:
            data["metadata"] = {}

        return cls(**data)

    @classmethod
    def create_new(
        cls, session_id: Optional[str] = None, model_used: str = "arch-chan", **kwargs
    ) -> "ChatSession":
        """Crea una nueva sesión de chat"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        return cls(
            session_id=session_id,
            created_at=datetime.now(),
            model_used=model_used,
            **kwargs,
        )

    def generate_title(self) -> str:
        """Genera un título automático para la sesión basado en el primer mensaje"""
        if not self.messages:
            return "Nueva conversación"

        first_user_message = next(
            (msg for msg in self.messages if msg.role == MessageRole.USER), None
        )
        if first_user_message:
            preview = first_user_message.get_content_preview(50)
            return f"Chat: {preview}"

        return "Conversación con Arch-Chan"


@dataclass
class ToolCall:
    """Modelo para una llamada a herramienta"""

    tool_name: str
    parameters: Dict[str, Any]
    call_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Inicialización posterior"""
        if self.parameters is None:
            self.parameters = {}
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la llamada a herramienta a diccionario"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Crea una llamada a herramienta desde un diccionario"""
        # Manejar conversión de timestamp
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            try:
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                data["timestamp"] = datetime.now()
        else:
            data["timestamp"] = datetime.now()

        # Valores por defecto
        if "parameters" not in data or data["parameters"] is None:
            data["parameters"] = {}
        if "metadata" not in data or data["metadata"] is None:
            data["metadata"] = {}

        return cls(**data)


@dataclass
class ToolResult:
    """Modelo para el resultado de una herramienta"""

    call_id: str
    result: Any
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Inicialización posterior"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        """Crea un resultado desde un diccionario"""
        # Manejar conversión de timestamp
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            try:
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                data["timestamp"] = datetime.now()
        else:
            data["timestamp"] = datetime.now()

        # Valores por defecto
        if "error_message" not in data:
            data["error_message"] = None
        if "execution_time" not in data:
            data["execution_time"] = 0.0
        if "metadata" not in data or data["metadata"] is None:
            data["metadata"] = {}

        return cls(**data)

    @classmethod
    def create_success(
        cls, call_id: str, result: Any, execution_time: float = 0.0
    ) -> "ToolResult":
        """Crea un resultado exitoso"""
        return cls(
            call_id=call_id, result=result, success=True, execution_time=execution_time
        )

    @classmethod
    def create_error(
        cls, call_id: str, error_message: str, execution_time: float = 0.0
    ) -> "ToolResult":
        """Crea un resultado de error"""
        return cls(
            call_id=call_id,
            result=None,
            success=False,
            error_message=error_message,
            execution_time=execution_time,
        )
