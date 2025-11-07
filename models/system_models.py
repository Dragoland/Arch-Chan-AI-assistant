#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class SystemInfo:
    """Información del sistema en un momento dado"""

    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_kbps: float
    network_recv_kbps: float
    cpu_temp: Optional[float]
    ollama_running: bool
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información a diccionario"""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_gb": self.memory_used_gb,
            "memory_total_gb": self.memory_total_gb,
            "disk_percent": self.disk_percent,
            "disk_used_gb": self.disk_used_gb,
            "disk_total_gb": self.disk_total_gb,
            "network_sent_kbps": self.network_sent_kbps,
            "network_recv_kbps": self.network_recv_kbps,
            "cpu_temp": self.cpu_temp,
            "ollama_running": self.ollama_running,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemInfo":
        """Crea la información del sistema desde un diccionario"""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class ProcessInfo:
    """Información de un proceso"""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    created: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información a diccionario"""
        return {
            "pid": self.pid,
            "name": self.name,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "status": self.status,
            "created": self.created.isoformat(),
        }


@dataclass
class OllamaModel:
    """Información de un modelo de Ollama"""

    name: str
    size: int  # en bytes
    modified_at: datetime
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información a diccionario"""
        return {
            "name": self.name,
            "size": self.size,
            "modified_at": self.modified_at.isoformat(),
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OllamaModel":
        """Crea la información del modelo desde un diccionario"""
        data["modified_at"] = datetime.fromisoformat(data["modified_at"])
        return cls(**data)


@dataclass
class SystemHealth:
    """Estado de salud del sistema"""

    cpu_health: str  # 'good', 'warning', 'critical'
    memory_health: str
    disk_health: str
    temperature_health: str
    ollama_health: str
    overall_health: str

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado de salud a diccionario"""
        return asdict(self)
