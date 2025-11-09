#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SystemHealthStatus(Enum):
    """Estados de salud del sistema"""

    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ServiceStatus(Enum):
    """Estados de servicios"""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


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
    cpu_temp: Optional[float] = None
    ollama_running: bool = False
    timestamp: datetime = None
    uptime_seconds: float = 0
    load_average: List[float] = None
    swap_used_gb: float = 0
    swap_total_gb: float = 0

    def __post_init__(self):
        """Inicialización posterior"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.load_average is None:
            self.load_average = [0.0, 0.0, 0.0]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información a diccionario"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["load_average"] = self.load_average
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemInfo":
        """Crea la información del sistema desde un diccionario"""
        # Manejar conversión de timestamp
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            try:
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                data["timestamp"] = datetime.now()
        else:
            data["timestamp"] = datetime.now()

        # Manejar load_average
        load_avg = data.get("load_average", [0.0, 0.0, 0.0])
        if load_avg is None:
            load_avg = [0.0, 0.0, 0.0]
        data["load_average"] = load_avg

        return cls(**data)

    def get_cpu_health(self) -> SystemHealthStatus:
        """Obtiene el estado de salud de la CPU"""
        if self.cpu_percent > 90:
            return SystemHealthStatus.CRITICAL
        elif self.cpu_percent > 70:
            return SystemHealthStatus.WARNING
        elif self.cpu_percent > 50:
            return SystemHealthStatus.GOOD
        else:
            return SystemHealthStatus.EXCELLENT

    def get_memory_health(self) -> SystemHealthStatus:
        """Obtiene el estado de salud de la memoria"""
        if self.memory_percent > 90:
            return SystemHealthStatus.CRITICAL
        elif self.memory_percent > 75:
            return SystemHealthStatus.WARNING
        elif self.memory_percent > 50:
            return SystemHealthStatus.GOOD
        else:
            return SystemHealthStatus.EXCELLENT

    def get_disk_health(self) -> SystemHealthStatus:
        """Obtiene el estado de salud del disco"""
        if self.disk_percent > 95:
            return SystemHealthStatus.CRITICAL
        elif self.disk_percent > 85:
            return SystemHealthStatus.WARNING
        elif self.disk_percent > 70:
            return SystemHealthStatus.GOOD
        else:
            return SystemHealthStatus.EXCELLENT

    def get_temperature_health(self) -> SystemHealthStatus:
        """Obtiene el estado de salud de la temperatura"""
        if self.cpu_temp is None:
            return SystemHealthStatus.UNKNOWN
        elif self.cpu_temp > 85:
            return SystemHealthStatus.CRITICAL
        elif self.cpu_temp > 75:
            return SystemHealthStatus.WARNING
        elif self.cpu_temp > 60:
            return SystemHealthStatus.GOOD
        else:
            return SystemHealthStatus.EXCELLENT

    def get_overall_health(self) -> SystemHealthStatus:
        """Obtiene el estado de salud general"""
        statuses = [
            self.get_cpu_health(),
            self.get_memory_health(),
            self.get_disk_health(),
            self.get_temperature_health(),
        ]

        # Filtrar estados desconocidos
        known_statuses = [s for s in statuses if s != SystemHealthStatus.UNKNOWN]

        if not known_statuses:
            return SystemHealthStatus.UNKNOWN

        if any(s == SystemHealthStatus.CRITICAL for s in known_statuses):
            return SystemHealthStatus.CRITICAL
        elif any(s == SystemHealthStatus.WARNING for s in known_statuses):
            return SystemHealthStatus.WARNING
        elif all(s == SystemHealthStatus.EXCELLENT for s in known_statuses):
            return SystemHealthStatus.EXCELLENT
        else:
            return SystemHealthStatus.GOOD


@dataclass
class ProcessInfo:
    """Información de un proceso"""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    created: datetime
    command: Optional[str] = None
    username: Optional[str] = None
    memory_rss: int = 0  # en bytes
    memory_vms: int = 0  # en bytes

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información a diccionario"""
        data = asdict(self)
        data["created"] = self.created.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessInfo":
        """Crea la información del proceso desde un diccionario"""
        # Manejar conversión de created
        created_str = data.get("created")
        if created_str:
            try:
                data["created"] = datetime.fromisoformat(created_str)
            except (ValueError, TypeError):
                data["created"] = datetime.now()
        else:
            data["created"] = datetime.now()

        return cls(**data)


@dataclass
class OllamaModel:
    """Información de un modelo de Ollama"""

    name: str
    size: int  # en bytes
    modified_at: datetime
    digest: str
    details: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    template: Optional[str] = None

    def __post_init__(self):
        """Inicialización posterior"""
        if self.details is None:
            self.details = {}
        if self.parameters is None:
            self.parameters = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información a diccionario"""
        data = asdict(self)
        data["modified_at"] = self.modified_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OllamaModel":
        """Crea la información del modelo desde un diccionario"""
        # Manejar conversión de modified_at
        modified_str = data.get("modified_at")
        if modified_str:
            try:
                data["modified_at"] = datetime.fromisoformat(modified_str)
            except (ValueError, TypeError):
                data["modified_at"] = datetime.now()
        else:
            data["modified_at"] = datetime.now()

        return cls(**data)

    def get_size_gb(self) -> float:
        """Retorna el tamaño en GB"""
        return self.size / (1024**3)

    def get_size_mb(self) -> float:
        """Retorna el tamaño en MB"""
        return self.size / (1024**2)

    def get_formatted_size(self) -> str:
        """Retorna el tamaño formateado"""
        size_gb = self.get_size_gb()
        if size_gb >= 1:
            return f"{size_gb:.2f} GB"
        else:
            return f"{self.get_size_mb():.2f} MB"


@dataclass
class SystemHealth:
    """Estado de salud del sistema"""

    cpu_health: SystemHealthStatus
    memory_health: SystemHealthStatus
    disk_health: SystemHealthStatus
    temperature_health: SystemHealthStatus
    ollama_health: SystemHealthStatus
    overall_health: SystemHealthStatus
    timestamp: datetime = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        """Inicialización posterior"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado de salud a diccionario"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["cpu_health"] = self.cpu_health.value
        data["memory_health"] = self.memory_health.value
        data["disk_health"] = self.disk_health.value
        data["temperature_health"] = self.temperature_health.value
        data["ollama_health"] = self.ollama_health.value
        data["overall_health"] = self.overall_health.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemHealth":
        """Crea el estado de salud desde un diccionario"""
        # Manejar conversión de timestamp
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            try:
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                data["timestamp"] = datetime.now()
        else:
            data["timestamp"] = datetime.now()

        # Convertir enums
        enum_fields = [
            "cpu_health",
            "memory_health",
            "disk_health",
            "temperature_health",
            "ollama_health",
            "overall_health",
        ]
        for field in enum_fields:
            if field in data:
                try:
                    data[field] = SystemHealthStatus(data[field])
                except ValueError:
                    data[field] = SystemHealthStatus.UNKNOWN

        return cls(**data)


@dataclass
class NetworkInfo:
    """Información de red"""

    interface: str
    ip_address: str
    netmask: str
    mac_address: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información a diccionario"""
        return asdict(self)


@dataclass
class ServiceInfo:
    """Información de un servicio"""

    name: str
    status: ServiceStatus
    description: Optional[str] = None
    active: bool = False
    enabled: bool = False
    pid: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información a diccionario"""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceInfo":
        """Crea la información del servicio desde un diccionario"""
        # Convertir status
        if "status" in data:
            try:
                data["status"] = ServiceStatus(data["status"])
            except ValueError:
                data["status"] = ServiceStatus.UNKNOWN

        return cls(**data)
