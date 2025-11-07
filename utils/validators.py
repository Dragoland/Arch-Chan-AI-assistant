#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shlex
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from utils.logger import get_logger


class SecurityValidator:
    """Validador de seguridad para entradas y comandos"""

    def __init__(self):
        self.logger = get_logger("SecurityValidator")

        # Patrones peligrosos - CORREGIDO: eliminar duplicados
        self.dangerous_patterns = [
            r"rm -rf",
            r"rm\s+-rf",
            r"dd if=",
            r"mkfs",
            r":\(\)\{:\|:\&\};\:",  # fork bomb
            r">\s+/dev/sd",
            r"chmod\s+777",
            r"chown\s+root",
            r"passwd",
            r"visudo",
            r"wget.*\|",
            r"curl.*\|.*sh",
            r"bash\s+<",
            r"wget\s+-O-",
            r"systemctl\s+(poweroff|reboot|shutdown)",
            r"shutdown",
            r"halt",
            r"poweroff",
            r"reboot",
            r"init\s+[06]",
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

        self.dangerous_sudo_commands = [
            "visudo",
            "passwd",
            "useradd",
            "userdel",
            "groupadd",
            "groupdel",
            "chsh",
            "chfn",
        ]

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Valida un comando para asegurar que es seguro

        Args:
            command: Comando a validar

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        command_lower = command.lower().strip()

        # Verificar comandos vacíos
        if not command_lower:
            return False, "Comando vacío"

        # Verificar patrones peligrosos
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command_lower):
                return False, f"Comando peligroso detectado: {pattern}"

        # Verificar acceso a directorios sensibles
        for directory in self.sensitive_dirs:
            if directory in command and any(
                cmd in command_lower for cmd in [" > ", " >> ", " | ", "&>", ">>"]
            ):
                return (
                    False,
                    f"Redirección a directorio sensible bloqueada: {directory}",
                )

        # Verificar comandos sudo peligrosos
        if "sudo" in command_lower:
            for dangerous_cmd in self.dangerous_sudo_commands:
                if dangerous_cmd in command_lower:
                    return False, f"Comando sudo peligroso bloqueado: {dangerous_cmd}"

        # Verificar redirección a dispositivos de bloque
        if re.search(r">\s*/dev/(sd|hd|nvme|loop|mmcblk)", command):
            return False, "Redirección a dispositivos de bloqueo bloqueada"

        # Verificar intentos de modificación de sistema crítico
        critical_paths = ["/etc/passwd", "/etc/shadow", "/etc/sudoers"]
        for critical_path in critical_paths:
            if critical_path in command and any(
                cmd in command_lower for cmd in [" > ", " >> ", "echo", "cat >"]
            ):
                return (
                    False,
                    f"Modificación de archivo crítico bloqueada: {critical_path}",
                )

        return True, None

    def validate_file_path(
        self, file_path: str, allowed_dirs: List[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida una ruta de archivo

        Args:
            file_path: Ruta a validar
            allowed_dirs: Directorios permitidos (None para cualquier directorio)

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        try:
            # Resolver ruta absoluta
            abs_path = os.path.abspath(os.path.expanduser(file_path))

            # Verificar path traversal
            if "../" in file_path or "/.." in file_path:
                return False, "Path traversal detectado en la ruta"

            # Verificar que no salga de directorios permitidos
            if allowed_dirs:
                allowed = False
                for allowed_dir in allowed_dirs:
                    allowed_dir_abs = os.path.abspath(allowed_dir)
                    if abs_path.startswith(allowed_dir_abs):
                        allowed = True
                        break
                if not allowed:
                    return False, f"Ruta fuera de directorios permitidos: {file_path}"

            # Verificar que no es un directorio sensible
            for sensitive_dir in self.sensitive_dirs:
                if abs_path.startswith(sensitive_dir):
                    return (
                        False,
                        f"Acceso a directorio sensible bloqueado: {sensitive_dir}",
                    )

            return True, None

        except Exception as e:
            return False, f"Error validando ruta: {e}"

    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Valida una URL

        Args:
            url: URL a validar

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        try:
            result = urlparse(url)

            # Verificar esquema
            if result.scheme not in ["http", "https", "ftp"]:
                return False, f"Esquema de URL no permitido: {result.scheme}"

            # Verificar que no sea localhost (para prevenir SSRF)
            if result.hostname in ["localhost", "127.0.0.1", "::1", "0.0.0.0"]:
                return False, "Acceso a localhost no permitido"

            # Verificar IPs privadas
            if result.hostname:
                ip_pattern = r"^(10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.)"
                if re.match(ip_pattern, result.hostname):
                    return False, "Acceso a IP privada no permitido"

            return True, None

        except Exception as e:
            return False, f"URL inválida: {e}"


class InputValidator:
    """Validador para entradas de usuario"""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Valida una dirección de email

        Args:
            email: Email a validar

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if re.match(pattern, email):
            return True, None
        return False, "Formato de email inválido"

    @staticmethod
    def validate_number(
        value: str, min_val: float = None, max_val: float = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida un número

        Args:
            value: Valor a validar
            min_val: Valor mínimo (opcional)
            max_val: Valor máximo (opcional)

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        try:
            num = float(value)

            if min_val is not None and num < min_val:
                return False, f"El valor debe ser mayor o igual a {min_val}"

            if max_val is not None and num > max_val:
                return False, f"El valor debe ser menor o igual a {max_val}"

            return True, None

        except ValueError:
            return False, "El valor debe ser un número válido"

    @staticmethod
    def validate_text_length(
        text: str, min_length: int = 0, max_length: int = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida la longitud de un texto

        Args:
            text: Texto a validar
            min_length: Longitud mínima
            max_length: Longitud máxima

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        length = len(text)

        if length < min_length:
            return False, f"El texto debe tener al menos {min_length} caracteres"

        if max_length is not None and length > max_length:
            return False, f"El texto debe tener como máximo {max_length} caracteres"

        return True, None

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitiza una entrada de texto

        Args:
            text: Texto a sanitizar

        Returns:
            Texto sanitizado
        """
        # Eliminar caracteres de control excepto tab, newline, carriage return
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Limitar longitud máxima (prevención de ataques de desbordamiento)
        max_length = 10000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized
