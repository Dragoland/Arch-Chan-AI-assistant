#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import requests

from utils.logger import get_logger


class DependencyError(Exception):
    """Excepción para dependencias faltantes"""

    pass


class DependencyChecker:
    """Verificador de dependencias del sistema"""

    def __init__(self):
        self.logger = get_logger("DependencyChecker")

        # Herramientas requeridas y sus comandos de verificación
        self.required_tools = {
            "whisper.cpp": "whisper-cli",
            "piper-tts": "piper-tts",
            "aplay": "aplay",
            "rec (sox)": "rec",
            "ollama": "ollama",
            "ddgr": "ddgr",
            "kdialog": "kdialog",
        }

        # Dependencias de Python
        self.required_python_packages = {
            "PySide6": "PySide6",
            "requests": "requests",
            "psutil": "psutil",
        }

        # Ejecutables encontrados
        self.found_executables = {}
        self.found_python_packages = {}

        self.logger.info("DependencyChecker inicializado")

    def check_all_dependencies(self) -> bool:
        """
        Verifica todas las dependencias requeridas

        Returns:
            True si todas las dependencias están disponibles

        Raises:
            DependencyError: Si faltan dependencias críticas
        """
        self.logger.info("Verificando dependencias del sistema...")

        missing_dependencies = []
        warning_dependencies = []

        # Verificar herramientas del sistema
        for name, command in self.required_tools.items():
            try:
                if name == "ollama":
                    # Verificación especial para Ollama (servicio)
                    if not self._check_ollama_service():
                        missing_dependencies.append(name)
                        continue
                else:
                    # Verificación de comandos normales
                    executable_path = self._find_executable(command)
                    if not executable_path:
                        if name in ["kdialog"]:  # Dependencias opcionales
                            warning_dependencies.append(name)
                        else:
                            missing_dependencies.append(name)
                        continue

                    # Guardar ruta encontrada
                    self.found_executables[command] = executable_path

                    # Verificación adicional para herramientas críticas
                    if command in ["piper-tts", "whisper-cli"]:
                        self._verify_tool_version(command, executable_path)

            except Exception as e:
                self.logger.error(f"Error verificando {name}: {str(e)}")
                if name not in ["kdialog"]:
                    missing_dependencies.append(name)

        # Verificar paquetes de Python
        python_missing = self._check_python_packages()
        missing_dependencies.extend(python_missing)

        # Verificar kdesu/alternativas
        kdesu_available = self._check_kdesu_alternatives()
        if not kdesu_available:
            warning_dependencies.append("kdesu/pkexec")

        # Reportar resultados
        if warning_dependencies:
            self.logger.warning(
                f"Dependencias con advertencias: {', '.join(warning_dependencies)}"
            )

        if missing_dependencies:
            missing_str = ", ".join(missing_dependencies)
            self.logger.error(f"Dependencias faltantes: {missing_str}")
            raise DependencyError(f"Herramientas faltantes: {missing_str}")

        self.logger.info("Todas las dependencias verificadas correctamente")
        return True

    def _find_executable(self, command: str) -> Optional[str]:
        """
        Busca un ejecutable en el sistema

        Args:
            command: Comando a buscar

        Returns:
            Ruta del ejecutable o None si no se encuentra
        """
        methods = [
            self._find_with_which,
            self._find_with_whereis,
            self._find_in_common_paths,
        ]

        for method in methods:
            try:
                path = method(command)
                if path:
                    self.logger.info(
                        f"'{command}' encontrado via {method.__name__}: {path}"
                    )
                    return path
            except Exception as e:
                self.logger.debug(
                    f"Error en {method.__name__} para {command}: {str(e)}"
                )

        self.logger.warning(f"Ejecutable no encontrado: {command}")
        return None

    def _find_with_which(self, command: str) -> Optional[str]:
        """Busca usando el comando which"""
        try:
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                timeout=5,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]
        except Exception as e:
            self.logger.debug(f"Error usando 'which' para {command}: {str(e)}")
        return None

    def _find_with_whereis(self, command: str) -> Optional[str]:
        """Busca usando el comando whereis"""
        try:
            result = subprocess.run(
                ["whereis", "-b", command],
                capture_output=True,
                timeout=5,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if ":" in output:
                    paths = output.split(":", 1)[1].strip()
                    if paths:
                        for path in paths.split():
                            if os.path.exists(path) and os.access(path, os.X_OK):
                                return path
        except Exception as e:
            self.logger.debug(f"Error usando 'whereis' para {command}: {str(e)}")
        return None

    def _find_in_common_paths(self, command: str) -> Optional[str]:
        """Busca en rutas comunes del sistema"""
        common_paths = [
            "/usr/bin",
            "/usr/local/bin",
            "/bin",
            "/usr/sbin",
            "/usr/libexec",
            "/opt/bin",
            "/snap/bin",
            "/usr/games",
            "/usr/local/sbin",
        ]

        # También verificar en PATH
        path_dirs = os.environ.get("PATH", "").split(":")
        common_paths.extend(path_dirs)

        for base_path in common_paths:
            if not base_path:
                continue
            potential_path = os.path.join(base_path, command)
            if os.path.exists(potential_path) and os.access(potential_path, os.X_OK):
                return potential_path

        return None

    def _check_ollama_service(self) -> bool:
        """Verifica que el servicio Ollama esté ejecutándose"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("Ollama service is running")
                return True
            else:
                self.logger.warning(
                    f"Ollama responded with status {response.status_code}"
                )
                return False
        except Exception as e:
            self.logger.debug(f"Ollama no responde: {str(e)}")
            return False

    def _check_python_packages(self) -> List[str]:
        """Verifica paquetes de Python requeridos"""
        missing_packages = []

        for name, package in self.required_python_packages.items():
            try:
                __import__(package)
                self.found_python_packages[package] = True
                self.logger.info(f"Paquete Python '{name}' encontrado")
            except ImportError as e:
                self.logger.error(f"Paquete Python faltante: {name} ({package})")
                missing_packages.append(name)
            except Exception as e:
                self.logger.error(f"Error verificando paquete {name}: {str(e)}")
                missing_packages.append(name)

        return missing_packages

    def _check_kdesu_alternatives(self) -> bool:
        """Verifica la disponibilidad de kdesu o alternativas"""
        alternatives = ["kdesu", "pkexec", "gksudo", "kdesudo", "beesu"]

        for alt in alternatives:
            try:
                result = subprocess.run(
                    ["which", alt],
                    capture_output=True,
                    timeout=5,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    self.logger.info(f"Alternativa de elevación encontrada: {alt}")
                    return True
            except Exception as e:
                self.logger.debug(f"Error verificando {alt}: {str(e)}")
                continue

        self.logger.warning(
            "No se encontraron alternativas de elevación de privilegios"
        )
        return False

    def _verify_tool_version(self, command: str, executable_path: str):
        """Verifica la versión de una herramienta"""
        try:
            if command == "piper-tts":
                result = subprocess.run(
                    [executable_path, "--version"],
                    capture_output=True,
                    timeout=5,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    self.logger.info(f"Piper TTS version: {result.stdout.strip()}")

            elif command == "whisper-cli":
                result = subprocess.run(
                    [executable_path, "--help"],
                    capture_output=True,
                    timeout=5,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    self.logger.info("Whisper CLI está disponible")

        except Exception as e:
            self.logger.warning(f"No se pudo verificar versión de {command}: {str(e)}")

    def get_executable_path(self, command: str) -> Optional[str]:
        """Retorna la ruta de un ejecutable encontrado"""
        return self.found_executables.get(command)

    def get_dependency_report(self) -> Dict:
        """Genera un reporte completo de dependencias"""
        report = {
            "system_tools": {},
            "python_packages": {},
            "system_info": {
                "ollama_available": self._check_ollama_service(),
                "kdesu_available": self._check_kdesu_alternatives(),
                "python_version": sys.version,
                "platform": sys.platform,
            },
        }

        # Reportar herramientas del sistema
        for name, command in self.required_tools.items():
            status = (
                "OK"
                if command in self.found_executables
                or (name == "ollama" and report["system_info"]["ollama_available"])
                else "MISSING"
            )

            report["system_tools"][name] = {
                "command": command,
                "status": status,
                "path": self.found_executables.get(command, "Not found"),
                "optional": name in ["kdialog"],
            }

        # Reportar paquetes Python
        for name, package in self.required_python_packages.items():
            status = (
                "OK" if self.found_python_packages.get(package, False) else "MISSING"
            )
            report["python_packages"][name] = {"package": package, "status": status}

        return report

    def check_system_requirements(self) -> Dict[str, bool]:
        """Verifica requisitos mínimos del sistema"""
        requirements = {
            "min_python_version": sys.version_info >= (3, 8),
            "linux_platform": sys.platform.startswith("linux"),
            "enough_memory": self._check_memory(),
            "enough_disk_space": self._check_disk_space(),
        }

        return requirements

    def _check_memory(self, min_gb: int = 4) -> bool:
        """Verifica memoria RAM mínima"""
        try:
            import psutil

            memory_gb = psutil.virtual_memory().total / (1024**3)
            return memory_gb >= min_gb
        except:
            return True  # Si no se puede verificar, asumir que es suficiente

    def _check_disk_space(self, min_gb: int = 2) -> bool:
        """Verifica espacio en disco mínimo"""
        try:
            import psutil

            disk_gb = psutil.disk_usage("/").free / (1024**3)
            return disk_gb >= min_gb
        except:
            return True  # Si no se puede verificar, asumir que es suficiente
