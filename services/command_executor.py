#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shlex
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, Signal

from utils.logger import get_logger


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

        # Proceso actual
        self.current_process: Optional[subprocess.Popen] = None

        # Patrones peligrosos
        self.dangerous_patterns = [
            r"rm -rf",
            r"dd if=",
            r"mkfs",
            r":(){:|:&};:",
            r"fork bomb",
            r"> /dev/sd",
            r"mkfs",
            r"fdisk",
            r"parted",
            r"sfdisk",
            r"chmod 777",
            r"chown root",
            r"passwd",
            r"visudo",
            r"wget",
            r"curl \| sh",
            r"bash <\(",
            r"wget -O-",
            r"systemctl poweroff",
            r"systemctl reboot",
            r"shutdown",
            r"halt",
            r"poweroff",
            r"reboot",
            r"init 0",
            r"init 6",
            r"cryptsetup",
            r"lvcreate",
            r"pvcreate",
            r"vgcreate",
            r"wipefs",
            r"sgdisk",
            r"partprobe",
        ]

        self.sensitive_dirs = [
            "/boot",
            "/etc",
            "/root",
            "/sys",
            "/proc",
            "/dev",
            "/mnt",
            "/media",
            "/usr",
            "/bin",
            "/sbin",
            "/lib",
            "/lib64",
        ]

        self.logger.info("CommandExecutor inicializado")

    def execute_command(
        self, command: str, timeout: int = 120, shell: bool = True
    ) -> Tuple[Optional[str], Optional[str], int]:
        """
        Ejecuta un comando de forma segura

        Args:
            command: Comando a ejecutar
            timeout: Tiempo máximo de ejecución
            shell: Usar shell para ejecución

        Returns:
            Tuple (stdout, stderr, returncode)
        """
        # Validar comando
        if not self._is_safe(command):
            error_msg = f"Comando no permitido por razones de seguridad: {command}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None, error_msg, -1

        try:
            self.command_started.emit(command)
            self.logger.info(f"Ejecutando comando: {command}")

            # Ejecutar comando
            self.current_process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
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
                self.current_process.kill()
                stdout, stderr = self.current_process.communicate()

            self.error_occurred.emit(error_msg)
            return None, error_msg, -1

        except Exception as e:
            error_msg = f"Error ejecutando comando: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None, error_msg, -1

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

        # Construir comando con la herramienta de elevación
        if sudo_tool == "pkexec":
            sudo_command = f"pkexec {command}"
        elif sudo_tool == "kdesu":
            sudo_command = f"kdesu -c '{command}'"
        else:
            sudo_command = f"{sudo_tool} {command}"

        self.logger.info(f"Ejecutando comando con {sudo_tool}: {command}")

        return self.execute_command(sudo_command, timeout)

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

        # Verificar que el script sea ejecutable
        if not os.access(script_path, os.X_OK):
            try:
                os.chmod(script_path, 0o755)
            except Exception as e:
                error_msg = f"No se pudo hacer ejecutable el script: {e}"
                self.logger.error(error_msg)
                return None, error_msg, -1

        return self.execute_command(f"'{script_path}'", timeout)

    def _is_safe(self, command: str) -> bool:
        """
        Verifica si un comando es seguro para ejecutar

        Args:
            command: Comando a verificar

        Returns:
            True si el comando es seguro
        """
        command_lower = command.lower()

        # Verificar patrones peligrosos
        for pattern in self.dangerous_patterns:
            if pattern in command_lower:
                self.logger.warning(f"Comando peligroso detectado: {pattern}")
                return False

        # Verificar acceso a directorios sensibles
        for directory in self.sensitive_dirs:
            if directory in command and any(
                cmd in command_lower for cmd in [" > ", " >> ", " | ", "&>"]
            ):
                self.logger.warning(
                    f"Redirección a directorio sensible bloqueada: {directory}"
                )
                return False

        # Verificar redirección a dispositivos de bloque
        if re.search(r">\s*/dev/(sd|hd|nvme|loop)", command):
            self.logger.warning("Redirección a dispositivos de bloqueo bloqueada")
            return False

        # Verificar intentos de modificación de sistema crítico
        critical_paths = ["/etc/passwd", "/etc/shadow", "/etc/sudoers"]
        for critical_path in critical_paths:
            if critical_path in command and any(
                cmd in command_lower for cmd in [" > ", " >> ", "echo"]
            ):
                self.logger.warning(
                    f"Modificación de archivo crítico bloqueada: {critical_path}"
                )
                return False

        return True

    def stop_current_command(self):
        """Detiene el comando actual en ejecución"""
        if self.current_process and self.current_process.poll() is None:
            self.logger.info("Deteniendo comando actual...")
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
            self.logger.info("Comando detenido")

    def get_command_info(self, command: str) -> Dict[str, Any]:
        """
        Obtiene información sobre un comando

        Args:
            command: Comando a analizar

        Returns:
            Diccionario con información del comando
        """
        info = {
            "command": command,
            "safe": self._is_safe(command),
            "requires_sudo": self._requires_sudo(command),
            "risk_level": self._assess_risk(command),
            "description": self._get_command_description(command),
        }

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
        ]

        return any(sudo_cmd in command for sudo_cmd in sudo_commands)

    def _assess_risk(self, command: str) -> str:
        """Evalúa el nivel de riesgo del comando"""
        low_risk = ["ls", "pwd", "cat", "echo", "date", "whoami"]
        medium_risk = ["rm", "mv", "cp", "chmod", "chown"]
        high_risk = ["dd", "mkfs", "fdisk", "shutdown", "reboot"]

        if any(cmd in command for cmd in low_risk):
            return "low"
        elif any(cmd in command for cmd in medium_risk):
            return "medium"
        elif any(cmd in command for cmd in high_risk):
            return "high"
        else:
            return "unknown"

    def _get_command_description(self, command: str) -> str:
        """Obtiene una descripción del comando"""
        # Comandos comunes de Arch Linux
        common_commands = {
            "pacman": "Gestor de paquetes de Arch Linux",
            "yay": "Gestor de paquetes AUR",
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
                ["which", command], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False
