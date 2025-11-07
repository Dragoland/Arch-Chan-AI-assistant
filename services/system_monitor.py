#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import platform
from datetime import datetime

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

    def __init__(self, update_interval=2000):
        super().__init__()
        self.logger = get_logger("SystemMonitor")
        self.update_interval = update_interval
        self.running = False

        # CORREGIDO: Inicializar con valores por defecto
        self.previous_net_io = (
            psutil.net_io_counters() if hasattr(psutil, "net_io_counters") else None
        )
        self.ollama_available = False

        # Umbrales de advertencia
        self.warning_thresholds = {
            "cpu": 80.0,
            "memory": 85.0,
            "disk": 90.0,
            "temperature": 80.0,
        }

        self.logger.info(f"SystemMonitor inicializado (intervalo: {update_interval}ms)")

    def run(self):
        """Bucle principal del monitor"""
        self.running = True
        self.logger.info("Iniciando monitoreo del sistema...")

        while self.running:
            try:
                system_info = self._collect_system_data()
                if system_info:  # CORREGIDO: Solo emitir si hay datos
                    self.system_updated.emit(system_info)

                    # Verificar advertencias
                    self._check_warnings(system_info)

                    # Verificar estado de Ollama
                    self._check_ollama_status(system_info)

            except Exception as e:
                self.logger.error(f"Error en monitoreo del sistema: {e}")

            self.msleep(self.update_interval)

    def _collect_system_data(self):
        """Recolecta datos del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)

            # Disco
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)

            # Red - CORREGIDO: Manejar caso donde no hay datos previos
            net_io = psutil.net_io_counters()
            if self.previous_net_io:
                net_sent = (
                    net_io.bytes_sent - self.previous_net_io.bytes_sent
                ) / 1024  # KB/s
                net_recv = (
                    net_io.bytes_recv - self.previous_net_io.bytes_recv
                ) / 1024  # KB/s
            else:
                net_sent = 0
                net_recv = 0
            self.previous_net_io = net_io

            # Temperatura
            cpu_temp = self._get_cpu_temperature()

            # Ollama
            ollama_running = self._check_ollama_connection()

            return {
                "cpu": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used": memory_used_gb,
                "memory_total": memory_total_gb,
                "disk_percent": disk_percent,
                "disk_used": disk_used_gb,
                "disk_total": disk_total_gb,
                "network_sent": net_sent,
                "network_recv": net_recv,
                "cpu_temp": cpu_temp,
                "ollama_running": ollama_running,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error recolectando datos del sistema: {e}")
            return {}

    def _get_cpu_temperature(self):
        """Obtiene la temperatura de la CPU"""
        try:
            # CORREGIDO: Manejar diferentes formas de obtener temperatura
            temps = psutil.sensors_temperatures()
            if not temps:
                return None

            # Intentar diferentes claves comunes
            for key in ["coretemp", "cpu_thermal", "k10temp"]:
                if key in temps and temps[key]:
                    return temps[key][0].current

            # Si no encuentra, tomar la primera disponible
            for key, values in temps.items():
                if values:
                    return values[0].current

            return None
        except Exception as e:
            self.logger.debug(f"No se pudo obtener temperatura: {e}")
            return None

    def _check_ollama_connection(self):
        """Verifica la conexión con Ollama"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False

    def _check_ollama_status(self, system_info):
        """Verifica cambios en el estado de Ollama"""
        current_status = system_info.get("ollama_running", False)
        if current_status != self.ollama_available:
            self.ollama_available = current_status
            self.ollama_status_changed.emit(current_status)

    def _check_warnings(self, system_info):
        """Verifica condiciones de advertencia"""
        # CPU
        cpu_usage = system_info.get("cpu", 0)
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

    def set_warning_thresholds(self, thresholds):
        """Establece nuevos umbrales de advertencia"""
        self.warning_thresholds.update(thresholds)
        self.logger.info(f"Umbrales de advertencia actualizados: {thresholds}")

    def get_system_summary(self):
        """Retorna un resumen del sistema"""
        try:
            # Información básica del sistema
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            system_info = {
                "boot_time": boot_time,
                "uptime": str(uptime).split(".")[0],  # Remover microsegundos
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage("/").total / (1024**3),
                "platform": f"{platform.system()} {platform.release()}",
            }
            return system_info
        except Exception as e:
            self.logger.error(f"Error obteniendo resumen del sistema: {e}")
            return {}

    def stop(self):
        """Detiene el monitoreo"""
        self.logger.info("Deteniendo monitoreo del sistema...")
        self.running = False
        if self.isRunning():
            self.wait(3000)  # Esperar hasta 3 segundos

    def is_running(self):
        """Verifica si el monitor está ejecutándose"""
        return self.running and self.isRunning()
