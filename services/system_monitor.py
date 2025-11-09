#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import platform
from datetime import datetime
from typing import Dict, Optional

import psutil
import requests
from PySide6.QtCore import QThread, Signal

from utils.logger import get_logger


class SystemMonitor(QThread):
    """Servicio de monitoreo del sistema en tiempo real"""

    # Señales
    system_updated = Signal(dict)
    ollama_status_changed = Signal(bool)
    high_usage_warning = Signal(str, float)  # resource_type, usage_percent
    health_status_changed = Signal(str)  # Estado de salud general

    def __init__(self, update_interval: int = 2000):
        super().__init__()
        self.logger = get_logger("SystemMonitor")
        self.update_interval = update_interval
        self.running = False

        # Estado inicial
        self.previous_net_io = None
        self.ollama_available = False
        self.health_status = "unknown"

        # Umbrales de advertencia
        self.warning_thresholds = {
            "cpu": 80.0,
            "memory": 85.0,
            "disk": 90.0,
            "temperature": 80.0,
        }

        # Historial para cálculos de red
        self.network_history = []

        # Cliente Ollama
        self.ollama_client = None

        self.logger.info(f"SystemMonitor inicializado (intervalo: {update_interval}ms)")

    def run(self):
        """Bucle principal del monitor"""
        self.running = True
        self.logger.info("Iniciando monitoreo del sistema...")

        # Inicializar datos de red
        self.previous_net_io = psutil.net_io_counters()

        while self.running:
            try:
                system_info = self._collect_system_data()
                if system_info:
                    self.system_updated.emit(system_info)

                    # Verificar advertencias
                    self._check_warnings(system_info)

                    # Verificar estado de Ollama
                    self._check_ollama_status(system_info)

                    # Verificar estado de salud
                    self._update_health_status(system_info)

            except Exception as e:
                self.logger.error(f"Error en monitoreo del sistema: {str(e)}")

            self.msleep(self.update_interval)

    def _collect_system_data(self) -> Optional[Dict]:
        """Recolecta datos del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)

            # Swap
            swap = psutil.swap_memory()
            swap_percent = swap.percent if swap.total > 0 else 0
            swap_used_gb = swap.used / (1024**3)
            swap_total_gb = swap.total / (1024**3)

            # Disco
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)

            # Red
            current_net_io = psutil.net_io_counters()
            net_sent_kbps, net_recv_kbps = self._calculate_network_speed(current_net_io)
            self.previous_net_io = current_net_io

            # Temperatura
            cpu_temp = self._get_cpu_temperature()

            # Carga del sistema
            load_avg = self._get_load_average()

            # Ollama
            ollama_running = self._check_ollama_connection()

            # Información del sistema
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used_gb": round(memory_used_gb, 2),
                "memory_total_gb": round(memory_total_gb, 2),
                "swap_percent": swap_percent,
                "swap_used_gb": round(swap_used_gb, 2),
                "swap_total_gb": round(swap_total_gb, 2),
                "disk_percent": disk_percent,
                "disk_used_gb": round(disk_used_gb, 2),
                "disk_total_gb": round(disk_total_gb, 2),
                "network_sent": round(net_sent_kbps, 2),
                "network_recv": round(net_recv_kbps, 2),
                "cpu_temp": cpu_temp,
                "load_avg": load_avg,
                "ollama_running": ollama_running,
                "uptime": str(uptime).split(".")[0],  # Remover microsegundos
                "boot_time": boot_time,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error recolectando datos del sistema: {str(e)}")
            return None

    def _calculate_network_speed(self, current_net_io) -> tuple:
        """Calcula la velocidad de red en KB/s"""
        if not self.previous_net_io:
            return 0.0, 0.0

        try:
            # Calcular diferencia en bytes
            time_elapsed = self.update_interval / 1000.0  # segundos
            bytes_sent = current_net_io.bytes_sent - self.previous_net_io.bytes_sent
            bytes_recv = current_net_io.bytes_recv - self.previous_net_io.bytes_recv

            # Convertir a KB/s
            sent_kbps = (bytes_sent / 1024) / time_elapsed
            recv_kbps = (bytes_recv / 1024) / time_elapsed

            return sent_kbps, recv_kbps
        except Exception as e:
            self.logger.debug(f"Error calculando velocidad de red: {str(e)}")
            return 0.0, 0.0

    def _get_cpu_temperature(self) -> Optional[float]:
        """Obtiene la temperatura de la CPU"""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None

            # Buscar en sensores comunes
            for sensor_name in ["coretemp", "k10temp", "cpu_thermal"]:
                if sensor_name in temps and temps[sensor_name]:
                    return temps[sensor_name][0].current

            # Tomar el primer sensor disponible
            for sensor_values in temps.values():
                if sensor_values:
                    return sensor_values[0].current

            return None
        except Exception as e:
            self.logger.debug(f"No se pudo obtener temperatura: {str(e)}")
            return None

    def _get_load_average(self) -> list:
        """Obtiene la carga promedio del sistema"""
        try:
            if hasattr(os, "getloadavg"):
                return list(os.getloadavg())
            return [0.0, 0.0, 0.0]
        except Exception:
            return [0.0, 0.0, 0.0]

    def set_ollama_client(self, ollama_client):
        """Establece el cliente de Ollama para verificación consistente"""
        self.ollama_client = ollama_client

    def _check_ollama_connection(self) -> bool:
        """Verifica la conexión con Ollama de forma más robusta"""

        try:
            # Intentar múltiples endpoints
            endpoints = [
                "http://127.0.0.1:11434/api/tags",
                "http://localhost:11434/api/tags",
            ]

            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=2)
                    if response.status_code == 200:
                        self.logger.debug(f"Ollama disponible en {endpoint}")
                        return True
                except:
                    continue

            # Si todos los endpoints fallan, verificar proceso
            return self._check_ollama_process()

        except Exception as e:
            self.logger.debug(f"Ollama no disponible: {str(e)}")
            return False

    def _check_ollama_process(self) -> bool:
        """Verifica si el proceso de Ollama está ejecutándose"""
        try:
            for proc in psutil.process_iter(["name", "cmdline"]):
                try:
                    proc_name = proc.info["name"].lower() if proc.info["name"] else ""
                    cmdline = " ".join(proc.info["cmdline"] or []).lower()

                    if "ollama" in proc_name or "ollama" in cmdline:
                        self.logger.debug("Proceso de Ollama encontrado")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            self.logger.debug(f"Error verificando proceso Ollama: {str(e)}")
            return False

    def _check_ollama_status(self, system_info: Dict):
        """Verifica cambios en el estado de Ollama"""
        current_status = system_info.get("ollama_running", False)
        if current_status != self.ollama_available:
            self.ollama_available = current_status
            self.ollama_status_changed.emit(current_status)

    def _check_warnings(self, system_info: Dict):
        """Verifica condiciones de advertencia"""
        # CPU
        cpu_usage = system_info.get("cpu_percent", 0)
        if cpu_usage > self.warning_thresholds["cpu"]:
            self.high_usage_warning.emit("CPU", cpu_usage)

        # Memoria
        memory_usage = system_info.get("memory_percent", 0)
        if memory_usage > self.warning_thresholds["memory"]:
            self.high_usage_warning.emit("Memoria", memory_usage)

        # Disco
        disk_usage = system_info.get("disk_percent", 0)
        if disk_usage > self.warning_thresholds["disk"]:
            self.high_usage_warning.emit("Disco", disk_usage)

        # Temperatura
        cpu_temp = system_info.get("cpu_temp")
        if cpu_temp and cpu_temp > self.warning_thresholds["temperature"]:
            self.high_usage_warning.emit("Temperatura", cpu_temp)

    def _update_health_status(self, system_info: Dict):
        """Actualiza el estado de salud del sistema"""
        status = "healthy"

        # Verificar condiciones críticas
        if system_info.get("cpu_percent", 0) > 95:
            status = "critical"
        elif system_info.get("memory_percent", 0) > 95:
            status = "critical"
        elif system_info.get("disk_percent", 0) > 98:
            status = "critical"
        elif system_info.get("cpu_temp", 0) and system_info["cpu_temp"] > 90:
            status = "critical"
        elif not system_info.get("ollama_running", False):
            status = "warning"

        if status != self.health_status:
            self.health_status = status
            self.health_status_changed.emit(status)

    def set_warning_thresholds(self, thresholds: Dict):
        """Establece nuevos umbrales de advertencia"""
        self.warning_thresholds.update(thresholds)
        self.logger.info(f"Umbrales de advertencia actualizados: {thresholds}")

    def get_system_summary(self) -> Dict:
        """Retorna un resumen del sistema"""
        try:
            # Información básica del sistema
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            system_info = {
                "platform": f"{platform.system()} {platform.release()}",
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "boot_time": boot_time,
                "uptime": str(uptime).split(".")[0],
                "cpu_count": psutil.cpu_count(),
                "cpu_physical_cores": psutil.cpu_count(logical=False),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
                "python_version": platform.python_version(),
            }
            return system_info
        except Exception as e:
            self.logger.error(f"Error obteniendo resumen del sistema: {str(e)}")
            return {}

    def stop(self):
        """Detiene el monitoreo - MEJORADO"""
        self.logger.info("Deteniendo monitoreo del sistema...")
        self.running = False

        # Esperar de forma más segura
        if self.isRunning():
            self.wait(5000)  # Esperar hasta 5 segundos
            if self.isRunning():
                self.logger.warning("El hilo no terminó correctamente, terminando...")
                self.terminate()
                self.wait(1000)

    def safe_delete(self):
        """Eliminación segura del monitor"""
        try:
            self.stop()
            self.disconnect()
        except Exception as e:
            self.logger.debug(f"Error en safe_delete: {str(e)}")

    def is_running(self) -> bool:
        """Verifica si el monitor está ejecutándose"""
        return self.running and self.isRunning()

    def get_health_status(self) -> str:
        """Retorna el estado de salud actual"""
        return self.health_status
