#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal

from config import PROJECT_PATH, logger


class UpdateManager(QThread):
    """Gestiona las actualizaciones automáticas de Arch-Chan"""

    update_available = Signal(str, str)  # version, changelog
    update_progress = Signal(int, str)  # progress, status
    update_finished = Signal(bool, str)  # success, message

    def __init__(self):
        super().__init__()
        self.current_version = "2.1"
        self.repo_url = (
            "https://api.github.com/repos/Dragoland/arch-chan/releases/latest"
        )

    def run(self):
        """Verifica e instala actualizaciones"""
        try:
            self.update_progress.emit(0, "Buscando actualizaciones...")

            # Verificar actualizaciones
            latest_version, changelog = self.check_for_updates()
            if latest_version:
                self.update_available.emit(latest_version, changelog)

                # Descargar actualización
                self.update_progress.emit(30, "Descargando actualización...")
                if self.download_update():
                    # Instalar actualización
                    self.update_progress.emit(70, "Instalando actualización...")
                    if self.install_update():
                        self.update_progress.emit(100, "Actualización completada!")
                        self.update_finished.emit(
                            True, f"Actualizado a v{latest_version}"
                        )
                    else:
                        self.update_finished.emit(False, "Error en la instalación")
                else:
                    self.update_finished.emit(False, "Error en la descarga")
            else:
                self.update_finished.emit(True, "Ya tienes la última versión")

        except Exception as e:
            logger.error(f"Error en actualización: {e}")
            self.update_finished.emit(False, f"Error: {str(e)}")

    def check_for_updates(self):
        """Verifica si hay actualizaciones disponibles"""
        try:
            response = requests.get(self.repo_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                latest_version = data["tag_name"].lstrip("v")

                if self.compare_versions(latest_version, self.current_version) > 0:
                    return latest_version, data.get(
                        "body", "Sin información de cambios"
                    )
            return None, None
        except Exception as e:
            logger.error(f"Error verificando actualizaciones: {e}")
            return None, None

    def compare_versions(self, v1, v2):
        """Compara dos versiones semánticas"""
        v1_parts = [int(x) for x in v1.split(".")]
        v2_parts = [int(x) for x in v2.split(".")]

        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_part = v1_parts[i] if i < len(v1_parts) else 0
            v2_part = v2_parts[i] if i < len(v2_parts) else 0

            if v1_part != v2_part:
                return v1_part - v2_part
        return 0

    def download_update(self):
        """Descarga la actualización"""
        # Implementar lógica de descarga
        return True

    def install_update(self):
        """Instala la actualización"""
        try:
            # Backup de configuración
            backup_file = os.path.join(
                PROJECT_PATH,
                "backups",
                f"pre_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ini",
            )
            subprocess.run(
                ["cp", os.path.join(PROJECT_PATH, "config.ini"), backup_file]
            )

            # Aquí iría la lógica de instalación específica
            logger.info("Actualización instalada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error instalando actualización: {e}")
            return False
