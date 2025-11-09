#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shlex
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import psutil
from PySide6.QtCore import QObject, Signal

from utils.logger import get_logger
from utils.validators import SecurityValidator


class CommandExecutor(QObject):
    """Ejecutor seguro de comandos del sistema"""

    # Señales
    command_started = Signal(str)  # Comando iniciado
    command_finished = Signal(str, int)  # Comando finalizado (comando, returncode)
    output_received = Signal(str, str)  # Salida recibida (tipo, contenido)
    error_occurred = Signal(str)  # Error en la ejecución

    def __init__(self):
        super().__init__()
        self.logger = get_logger("CommandExecutor")
        self.security_validator = SecurityValidator()

        # Proceso actual
        self.current_process: Optional[subprocess.Popen] = None

        self.logger.info("CommandExecutor inicializado")

    def execute_command(
        self, command: str, timeout: int = 120, shell: bool = False
    ) -> Tuple[Optional[str], Optional[str], int]:
        """
        Ejecuta un comando de forma segura

        Args:
            command: Comando a ejecutar
            timeout: Tiempo máximo de ejecución
            shell: Usar shell para ejecución (False por defecto por seguridad)

        Returns:
            Tuple (stdout, stderr, returncode)
        """
        # Validar comando
        is_safe, error_msg = self.security_validator.validate_command(command)
        if not is_safe:
            self.logger.error(f"Comando no permitido: {error_msg}")
            self.error_occurred.emit(f"Comando no permitido: {error_msg}")
            return None, error_msg, -1

        try:
            self.command_started.emit(command)
            self.logger.info(f"Ejecutando comando: {command}")

            # Ejecutar comando
            if shell:
                self.current_process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    start_new_session=True,  # Permite mejor control del proceso
                )
            else:
                # Dividir comando en partes para mayor seguridad
                command_parts = shlex.split(command)
                self.current_process = subprocess.Popen(
                    command_parts,
                    shell=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    start_new_session=True,
                )

            # Esperar a que termine con timeout
            stdout, stderr = self.current_process.communicate(timeout=timeout)
            returncode = self.current_process.returncode

            # Emitir resultados
            if stdout:
                self.output_received.emit("stdout", stdout)
            if stderr:
                self.output_received.emit("stderr", stderr)

            self.command_finished.emit(command, returncode)
            self.logger.info(f"Comando ejecutado - Código: {returncode}")

            return stdout, stderr, returncode

        except subprocess.TimeoutExpired:
            error_msg = f"Comando excedió el tiempo límite de {timeout} segundos"
            self.logger.error(error_msg)

            if self.current_process:
                # Terminar proceso y todos sus hijos
                self._terminate_process_tree(self.current_process.pid)

            self.error_occurred.emit(error_msg)
            return None, error_msg, -1

        except Exception as e:
            error_msg = f"Error ejecutando comando: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None, error_msg, -1

    def _terminate_process_tree(self, pid: int):
        """Termina un proceso y todos sus hijos"""
        try:
            # Obtener todos los procesos hijos
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            # Terminar hijos primero
            for child in children:
                try:
                    child.terminate()
                except:
                    pass

            # Esperar a que los hijos terminen
            gone, alive = psutil.wait_procs(children, timeout=5)

            # Forzar terminación de los que siguen vivos
            for child in alive:
                try:
                    child.kill()
                except:
                    pass

            # Terminar proceso padre
            try:
                parent.terminate()
                parent.wait(5)
            except:
                try:
                    parent.kill()
                except:
                    pass

        except Exception as e:
            self.logger.warning(f"Error terminando árbol de procesos: {str(e)}")

    def execute_command_with_sudo(
        self, command: str, sudo_tool: str = "pkexec", timeout: int = 120
    ) -> Tuple[Optional[str], Optional[str], int]:
        """
        Ejecuta un comando con elevación de privilegios

        Args:
            command: Comando a ejecutar
            sudo_tool: Herramienta para elevación (pkexec, kdesu, etc.)
            timeout: Tiempo máximo de ejecución

        Returns:
            Tuple (stdout, stderr, returncode)
        """

        # Verificar que el comando no tenga sudo incluido
        if command.strip().startswith("sudo "):
            command = command.replace("sudo ", "", 1)

        # Validar comando antes de elevación
        is_safe, error_msg = self.security_validator.validate_command(command)
        if not is_safe:
            self.logger.error(f"Comando no permitido para elevación: {error_msg}")
            return None, error_msg, -1

        # Construir comando como LISTA para shell=False
        try:
            command_parts = shlex.split(command)

            if sudo_tool == "pkexec":
                sudo_command_parts = ["pkexec"] + command_parts
            elif sudo_tool == "kdesu":
                # kdesu -c espera un solo string
                sudo_command_parts = ["kdesu", "-c", command]
            else:
                sudo_command_parts = [sudo_tool] + command_parts

            self.logger.info(f"Ejecutando con elevación: {sudo_command_parts}")
            self.command_started.emit(" ".join(sudo_command_parts))

            # Ejecutar directamente con subprocess.Popen y shell=False
            self.current_process = subprocess.Popen(
                sudo_command_parts,
                shell=False,  # ¡CRÍTICO!
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                start_new_session=True,
            )

            stdout, stderr = self.current_process.communicate(timeout=timeout)
            returncode = self.current_process.returncode

            self.command_finished.emit(command, returncode)
            return stdout, stderr, returncode

        except Exception as e:
            error_msg = f"Error ejecutando comando sudo: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None, error_msg, -1

    def execute_script(
        self, script_path: str, timeout: int = 300
    ) -> Tuple[Optional[str], Optional[str], int]:
        """
        Ejecuta un script de forma segura

        Args:
            script_path: Ruta al script
            timeout: Tiempo máximo de ejecución

        Returns:
            Tuple (stdout, stderr, returncode)
        """
        if not os.path.exists(script_path):
            error_msg = f"Script no encontrado: {script_path}"
            self.logger.error(error_msg)
            return None, error_msg, -1

        # Validar que el script no sea peligroso
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                script_content = f.read()

            # Verificar contenido peligroso
            dangerous_patterns = [r"rm -rf", r"chmod 777", r"> /dev/sd", r"dd if="]
            for pattern in dangerous_patterns:
                if re.search(pattern, script_content, re.IGNORECASE):
                    error_msg = f"Script contiene operaciones peligrosas: {pattern}"
                    self.logger.error(error_msg)
                    return None, error_msg, -1

        except Exception as e:
            self.logger.warning(f"No se pudo verificar script: {str(e)}")

        # Verificar que el script sea ejecutable
        if not os.access(script_path, os.X_OK):
            try:
                os.chmod(script_path, 0o755)
            except Exception as e:
                error_msg = f"No se pudo hacer ejecutable el script: {str(e)}"
                self.logger.error(error_msg)
                return None, error_msg, -1

        return self.execute_command(f"'{script_path}'", timeout, shell=True)

    def stop_current_command(self):
        """Detiene el comando actual en ejecución"""
        if self.current_process and self.current_process.poll() is None:
            self.logger.info("Deteniendo comando actual...")
            try:
                self._terminate_process_tree(self.current_process.pid)
                self.logger.info("Comando detenido")
            except Exception as e:
                self.logger.error(f"Error deteniendo comando: {str(e)}")

    def get_command_info(self, command: str) -> Dict[str, Any]:
        """
        Obtiene información sobre un comando

        Args:
            command: Comando a analizar

        Returns:
            Diccionario con información del comando
        """
        is_safe, error_msg = self.security_validator.validate_command(command)
        info = {
            "command": command,
            "safe": is_safe,
            "requires_sudo": self._requires_sudo(command),
            "risk_level": self._assess_risk(command),
            "description": self._get_command_description(command),
        }

        if not is_safe:
            info["security_message"] = error_msg

        return info

    def _requires_sudo(self, command: str) -> bool:
        """Verifica si el comando requiere sudo"""
        sudo_commands = [
            "pacman -S",
            "systemctl",
            "useradd",
            "userdel",
            "groupadd",
            "groupdel",
            "chsh",
            "chfn",
            "visudo",
            "passwd",
            "mount",
            "umount",
            "fdisk",
            "parted",
        ]

        command_lower = command.lower()
        return any(sudo_cmd in command_lower for sudo_cmd in sudo_commands)

    def _assess_risk(self, command: str) -> str:
        """Evalúa el nivel de riesgo del comando"""
        low_risk = ["ls", "pwd", "cat", "echo", "date", "whoami", "uname"]
        medium_risk = ["rm", "mv", "cp", "chmod", "chown", "find", "grep"]
        high_risk = ["dd", "mkfs", "fdisk", "shutdown", "reboot", "wipefs"]

        command_lower = command.lower()

        if any(cmd in command_lower for cmd in low_risk):
            return "low"
        elif any(cmd in command_lower for cmd in medium_risk):
            return "medium"
        elif any(cmd in command_lower for cmd in high_risk):
            return "high"
        else:
            return "unknown"

    def _get_command_description(self, command: str) -> str:
        """Obtiene una descripción del comando"""
        # Comandos comunes de Arch Linux
        common_commands = {
            "pacman": "Gestor de paquetes de Arch Linux",
            "yay": "Gestor de paquetes AUR",
            "paru": "Gestor de paquetes AUR",
            "systemctl": "Administrador de servicios systemd",
            "journalctl": "Visor de logs del sistema",
            "ls": "Listar archivos y directorios",
            "cd": "Cambiar directorio",
            "pwd": "Mostrar directorio actual",
            "cat": "Mostrar contenido de archivos",
            "grep": "Buscar patrones en texto",
            "find": "Buscar archivos y directorios",
            "chmod": "Cambiar permisos de archivos",
            "chown": "Cambiar propietario de archivos",
            "ps": "Mostrar procesos",
            "top": "Monitor de procesos en tiempo real",
            "htop": "Monitor de procesos interactivo",
            "df": "Mostrar espacio en disco",
            "du": "Mostrar uso de espacio de archivos",
            "uname": "Mostrar información del sistema",
            "neofetch": "Mostrar información del sistema con estilo",
        }

        # Extraer el comando base (primera palabra)
        base_command = command.split()[0] if command else ""

        return common_commands.get(base_command, "Comando del sistema")

    def is_command_available(self, command: str) -> bool:
        """
        Verifica si un comando está disponible en el sistema

        Args:
            command: Comando a verificar

        Returns:
            True si el comando está disponible
        """
        try:
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"Error verificando comando {command}: {str(e)}")
            return False
