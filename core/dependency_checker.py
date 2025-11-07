#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import requests
from typing import Dict, List, Optional, Tuple

from utils.logger import get_logger

class DependencyError(Exception):
    """Excepción para dependencias faltantes"""
    pass

class DependencyChecker:
    """Verificador de dependencias del sistema"""

    def __init__(self):
        self.logger = get_logger("DependencyChecker")
        self.required_tools = {
            'whisper-cli': 'whisper-cli',
            'piper-tts': 'piper-tts',
            'aplay': 'aplay',
            'rec (sox)': 'rec',
            'ollama': 'ollama',
            'ddgr': 'ddgr',
            'kdialog': 'kdialog'
        }

        # Ejecutables encontrados
        self.found_executables = {}

        self.logger.info("DependencyChecker inicializado")

    def check_all_dependencies(self) -> bool:
        """
        Verifica todas las dependencias requeridas

        Returns:
            True si todas las dependencias están disponibles

        Raises:
            DependencyError: Si faltan dependencias
        """
        self.logger.info("Verificando dependencias del sistema...")

        missing_dependencies = []

        for name, command in self.required_tools.items():
            try:
                if name == 'ollama':
                    # Verificación especial para Ollama (servicio)
                    if not self._check_ollama_service():
                        missing_dependencies.append(name)
                        continue
                else:
                    # Verificación de comandos normales
                    executable_path = self._find_executable(command)
                    if not executable_path:
                        missing_dependencies.append(name)
                        continue

                    # Guardar ruta encontrada
                    self.found_executables[command] = executable_path

                    # Verificación adicional para herramientas críticas
                    if command in ['piper-tts', 'whisper-cli']:
                        self._verify_tool_version(command, executable_path)

            except Exception as e:
                self.logger.error(f"Error verificando {name}: {e}")
                missing_dependencies.append(name)

        # Verificar kdesu/alternativas
        kdesu_available = self._check_kdesu_alternatives()
        if not kdesu_available:
            self.logger.warning("kdesu y alternativas no disponibles - comandos sudo no funcionarán")

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
            self._find_in_common_paths
        ]

        for method in methods:
            try:
                path = method(command)
                if path:
                    self.logger.info(f"'{command}' encontrado via {method.__name__}: {path}")
                    return path
            except Exception as e:
                self.logger.debug(f"Error en {method.__name__} para {command}: {e}")

        self.logger.warning(f"Ejecutable no encontrado: {command}")
        return None

    def _find_with_which(self, command: str) -> Optional[str]:
        """Busca usando el comando which"""
        try:
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except Exception as e:
            self.logger.debug(f"Error usando 'which' para {command}: {e}")
        return None

    def _find_with_whereis(self, command: str) -> Optional[str]:
        """Busca usando el comando whereis"""
        try:
            result = subprocess.run(
                ['whereis', '-b', command],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if ':' in output:
                    paths = output.split(':', 1)[1].strip()
                    if paths:
                        for path in paths.split():
                            if os.path.exists(path) and os.access(path, os.X_OK):
                                return path
        except Exception as e:
            self.logger.debug(f"Error usando 'whereis' para {command}: {e}")
        return None

    def _find_in_common_paths(self, command: str) -> Optional[str]:
        """Busca en rutas comunes del sistema"""
        common_paths = [
            '/usr/bin', '/usr/local/bin', '/bin', '/usr/sbin',
            '/usr/libexec', '/opt/bin', '/snap/bin'
        ]

        for base_path in common_paths:
            potential_path = os.path.join(base_path, command)
            if os.path.exists(potential_path) and os.access(potential_path, os.X_OK):
                return potential_path

        return None

    def _check_ollama_service(self) -> bool:
        """Verifica que el servicio Ollama esté ejecutándose"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Ollama no responde: {e}")
            return False

    def _check_kdesu_alternatives(self) -> bool:
        """Verifica la disponibilidad de kdesu o alternativas"""
        alternatives = ['kdesu', 'pkexec', 'gksudo', 'kdesudo', 'beesu']

        for alt in alternatives:
            try:
                result = subprocess.run(['which', alt], capture_output=True, timeout=5, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    self.logger.info(f"Alternativa de elevación encontrada: {alt}")
                    return True
            except Exception:
                continue

        return False

    def _verify_tool_version(self, command: str, executable_path: str):
        """Verifica la versión de una herramienta"""
        try:
            if command == 'piper-tts':
                result = subprocess.run(
                    [executable_path, '--version'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if result.returncode == 0:
                    self.logger.info(f"Piper TTS version: {result.stdout.strip()}")

            elif command == 'whisper-cli':
                result = subprocess.run(
                    [executable_path, '--help'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if result.returncode == 0:
                    self.logger.info("Whisper CLI está disponible")

        except Exception as e:
            self.logger.warning(f"No se pudo verificar versión de {command}: {e}")

    def get_executable_path(self, command: str) -> Optional[str]:
        """Retorna la ruta de un ejecutable encontrado"""
        return self.found_executables.get(command)

    def get_dependency_report(self) -> Dict[str, Dict]:
        """Genera un reporte de dependencias"""
        report = {
            'required_tools': {},
            'found_executables': self.found_executables.copy(),
            'ollama_available': self._check_ollama_service(),
            'kdesu_available': self._check_kdesu_alternatives()
        }

        for name, command in self.required_tools.items():
            status = "OK" if command in self.found_executables or (
                name == 'ollama' and report['ollama_available']
            ) else "MISSING"

            report['required_tools'][name] = {
                'command': command,
                'status': status,
                'path': self.found_executables.get(command, 'Not found')
            }

        return report
