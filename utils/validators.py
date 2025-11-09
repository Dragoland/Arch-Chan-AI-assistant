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

        # Patrones peligrosos - CORREGIDO Y EXPANDIDO
        self.dangerous_patterns = [
            r"rm\s+-rf",
            r"rm\s+-r\s+-f",
            r"dd\s+if=",
            r"mkfs\.?\w*",
            r":\(\)\{:\|:\&\};\:",  # fork bomb
            r">\s*/dev/(sd|hd|nvme|mmcblk|loop)",
            r"chmod\s+[0-7][0-7][0-7]\s+.*/etc/",
            r"chown\s+root:root\s+.*/etc/",
            r"passwd\s+root",
            r"visudo",
            r"wget.*\|\s*(sh|bash)",
            r"curl.*\|\s*(sh|bash)",
            r"bash\s+<",
            r"systemctl\s+(poweroff|reboot|shutdown|halt)",
            r"shutdown\s+-h\s+now",
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
            r">\s*/etc/passwd",
            r">\s*/etc/shadow",
            r">\s*/etc/sudoers",
            r"echo.*>\s*/etc/",
            r"cat.*>\s*/etc/",
            r"mkinitcpio",
            r"pacman\s+-R\s+(linux|systemd)",
            r"pacman\s+-U\s+.*\.pkg\.tar",
            r"rm\s+-rf\s+/\s*$",
            r"rm\s+-rf\s+/\.\.",
            r"rm\s+-rf\s+/boot",
            r"rm\s+-rf\s+/etc",
            r"rm\s+-rf\s+/usr",
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
            "/var/lib",
            "/opt",
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
            "usermod",
            "groupmod",
        ]

        # Comandos permitidos (whitelist)
        self.allowed_commands = [
            "ls",
            "ps",
            "df",
            "du",
            "find",
            "grep",
            "cat",
            "head",
            "tail",
            "wc",
            "date",
            "whoami",
            "pwd",
            "echo",
            "uname",
            "uptime",
            "free",
            "top",
            "htop",
            "neofetch",
            "pacman",
            "yay",
            "paru",
            "git",
            "curl",
            "wget",
            "ping",
            "ss",
            "netstat",
            "journalctl",
            "systemctl",
            "ip",
            "ifconfig",
        ]

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Valida un comando para asegurar que es seguro

        Args:
            command: Comando a validar

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        if not command or not command.strip():
            return False, "Comando vacío"

        command_lower = command.lower().strip()

        # Verificar si es un comando permitido (whitelist approach)
        if self._is_whitelisted_command(command_lower):
            return True, None

        # Verificar patrones peligrosos
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command_lower):
                return False, f"Comando peligroso detectado: {pattern}"

        # Verificar acceso a directorios sensibles con redirección
        for directory in self.sensitive_dirs:
            dir_pattern = re.escape(directory)
            if re.search(dir_pattern, command) and any(
                redirect in command for redirect in [">", ">>", "|", "&>"]
            ):
                return False, f"Redirección a directorio sensible: {directory}"

        # Verificar comandos sudo peligrosos
        if "sudo" in command_lower:
            for dangerous_cmd in self.dangerous_sudo_commands:
                if dangerous_cmd in command_lower:
                    return False, f"Comando sudo peligroso: {dangerous_cmd}"

        # Verificar redirección peligrosa
        if self._has_dangerous_redirect(command):
            return False, "Redirección peligrosa detectada"

        return True, None

    def _is_whitelisted_command(self, command: str) -> bool:
        """
        Verifica si el comando está en la lista blanca

        Args:
            command: Comando a verificar

        Returns:
            True si está permitido
        """
        # Extraer el primer comando (antes de pipes, redirecciones, etc.)
        first_cmd = command.split()[0] if command.split() else ""

        # Verificar comando base
        for allowed in self.allowed_commands:
            if first_cmd == allowed or first_cmd.endswith(f"/{allowed}"):
                return True

        return False

    def _has_dangerous_redirect(self, command: str) -> bool:
        """
        Verifica redirecciones peligrosas

        Args:
            command: Comando a verificar

        Returns:
            True si tiene redirección peligrosa
        """
        dangerous_targets = [
            r"/dev/sd[a-z]",
            r"/dev/hd[a-z]",
            r"/dev/nvme[0-9]+",
            r"/dev/mmcblk[0-9]+",
            r"/etc/passwd",
            r"/etc/shadow",
            r"/etc/sudoers",
            r"/boot/",
            r"/sys/",
            r"/proc/",
        ]

        for target in dangerous_targets:
            if re.search(rf">\s*{target}", command):
                return True
        return False

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
            if ".." in file_path or "../" in file_path or "/.." in file_path:
                return False, "Path traversal detectado"

            # Verificar que no salga de directorios permitidos
            if allowed_dirs:
                allowed = False
                for allowed_dir in allowed_dirs:
                    allowed_dir_abs = os.path.abspath(os.path.expanduser(allowed_dir))
                    if abs_path.startswith(allowed_dir_abs):
                        allowed = True
                        break
                if not allowed:
                    return False, f"Ruta fuera de directorios permitidos: {file_path}"

            # Verificar que no es un directorio sensible
            for sensitive_dir in self.sensitive_dirs:
                if abs_path.startswith(sensitive_dir):
                    return False, f"Acceso a directorio sensible: {sensitive_dir}"

            return True, None

        except Exception as e:
            return False, f"Error validando ruta: {str(e)}"

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
            if result.scheme not in ["http", "https", "ftp", "ftps"]:
                return False, f"Esquema de URL no permitido: {result.scheme}"

            # Verificar que no sea localhost (para prevenir SSRF)
            localhost_patterns = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
            if result.hostname in localhost_patterns:
                return False, "Acceso a localhost no permitido"

            # Verificar IPs privadas
            if result.hostname:
                ip_patterns = [
                    r"^10\.",
                    r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
                    r"^192\.168\.",
                    r"^169\.254\.",
                    r"^fe80:",
                ]
                for pattern in ip_patterns:
                    if re.match(pattern, result.hostname):
                        return False, "Acceso a IP privada no permitido"

            # Verificar caracteres peligrosos
            if "|" in url or "`" in url or "$" in url:
                return False, "URL contiene caracteres peligrosos"

            return True, None

        except Exception as e:
            return False, f"URL inválida: {str(e)}"

    def validate_model_name(self, model_name: str) -> Tuple[bool, Optional[str]]:
        """
        Valida un nombre de modelo

        Args:
            model_name: Nombre del modelo

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        if not model_name or not model_name.strip():
            return False, "Nombre de modelo vacío"

        # Solo permitir caracteres alfanuméricos, guiones, puntos y dos puntos
        if not re.match(r"^[a-zA-Z0-9_\-\.:]+$", model_name):
            return False, "Nombre de modelo contiene caracteres inválidos"

        # Prevenir path traversal en nombres de modelo
        if ".." in model_name or "/" in model_name or "\\" in model_name:
            return False, "Nombre de modelo contiene caracteres de path traversal"

        return True, None


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
        if not email or not email.strip():
            return False, "Email vacío"

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
        if not value or not value.strip():
            return False, "Valor vacío"

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
    def validate_integer(
        value: str, min_val: int = None, max_val: int = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida un número entero

        Args:
            value: Valor a validar
            min_val: Valor mínimo (opcional)
            max_val: Valor máximo (opcional)

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        if not value or not value.strip():
            return False, "Valor vacío"

        try:
            num = int(value)

            if min_val is not None and num < min_val:
                return False, f"El valor debe ser mayor o igual a {min_val}"

            if max_val is not None and num > max_val:
                return False, f"El valor debe ser menor o igual a {max_val}"

            return True, None

        except ValueError:
            return False, "El valor debe ser un número entero válido"

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
        if text is None:
            text = ""

        length = len(text)

        if length < min_length:
            return False, f"El texto debe tener al menos {min_length} caracteres"

        if max_length is not None and length > max_length:
            return False, f"El texto debe tener como máximo {max_length} caracteres"

        return True, None

    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """
        Sanitiza una entrada de texto

        Args:
            text: Texto a sanitizar
            max_length: Longitud máxima permitida

        Returns:
            Texto sanitizado
        """
        if text is None:
            return ""

        # Eliminar caracteres de control excepto tab, newline, carriage return
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Limitar longitud máxima
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
        """
        Valida un nombre de archivo

        Args:
            filename: Nombre de archivo a validar

        Returns:
            Tuple (es_válido, mensaje_de_error)
        """
        if not filename or not filename.strip():
            return False, "Nombre de archivo vacío"

        # Caracteres prohibidos en nombres de archivo
        forbidden_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in forbidden_chars:
            if char in filename:
                return False, f"Nombre de archivo contiene caracter inválido: {char}"

        # Prevenir nombres reservados
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]
        if filename.upper() in reserved_names:
            return False, "Nombre de archivo reservado del sistema"

        return True, None
