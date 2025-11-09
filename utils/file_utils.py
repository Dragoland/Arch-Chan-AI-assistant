#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

_logger = get_logger("FileUtils")


class FileUtils:
    """Utilidades para manejo de archivos y directorios"""

    def __init__(self):
        self.logger = _logger

    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """
        Asegura que un directorio existe

        Args:
            directory: Ruta del directorio

        Returns:
            True si el directorio existe o fue creado
        """
        try:
            directory = os.path.expanduser(directory)
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            _logger.error(f"Error creando directorio {directory}: {str(e)}")
            return False

    @staticmethod
    def safe_delete(file_path: str) -> bool:
        """
        Elimina un archivo de forma segura

        Args:
            file_path: Ruta del archivo

        Returns:
            True si fue eliminado o no existía
        """
        try:
            file_path = os.path.expanduser(file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            _logger.error(f"Error eliminando archivo {file_path}: {str(e)}")
            return False

    @staticmethod
    def safe_write(file_path: str, content: str, backup: bool = True) -> bool:
        """
        Escribe contenido en un archivo de forma segura

        Args:
            file_path: Ruta del archivo
            content: Contenido a escribir
            backup: Hacer backup del archivo existente

        Returns:
            True si la escritura fue exitosa
        """
        temp_path = None
        try:
            file_path = os.path.expanduser(file_path)
            # Crear directorio si no existe
            directory = os.path.dirname(file_path)
            FileUtils.ensure_directory(directory)

            # Hacer backup si existe
            if backup and os.path.exists(file_path):
                backup_path = (
                    f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                shutil.copy2(file_path, backup_path)

            # Escribir archivo temporal
            temp_path = f"{file_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Reemplazar archivo original
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_path, file_path)

            return True

        except Exception as e:
            _logger.error(f"Error escribiendo archivo {file_path}: {str(e)}")
            # Limpiar archivo temporal si existe
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False

    @staticmethod
    def safe_read(file_path: str) -> Optional[str]:
        """
        Lee un archivo de forma segura

        Args:
            file_path: Ruta del archivo

        Returns:
            Contenido del archivo o None en caso de error
        """
        try:
            file_path = os.path.expanduser(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            _logger.error(f"Error leyendo archivo {file_path}: {str(e)}")
            return None

    @staticmethod
    def read_json(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Lee un archivo JSON

        Args:
            file_path: Ruta del archivo

        Returns:
            Diccionario con los datos o None en caso de error
        """
        try:
            content = FileUtils.safe_read(file_path)
            if content is None:
                return None
            return json.loads(content)
        except json.JSONDecodeError as e:
            _logger.error(f"Error decodificando JSON {file_path}: {str(e)}")
            return None
        except Exception as e:
            _logger.error(f"Error leyendo JSON {file_path}: {str(e)}")
            return None

    @staticmethod
    def write_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
        """
        Escribe datos en un archivo JSON

        Args:
            file_path: Ruta del archivo
            data: Datos a escribir
            indent: Indentación del JSON

        Returns:
            True si la escritura fue exitosa
        """
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return FileUtils.safe_write(file_path, content)
        except Exception as e:
            _logger.error(f"Error escribiendo JSON {file_path}: {str(e)}")
            return False

    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
        """
        Calcula el hash de un archivo

        Args:
            file_path: Ruta del archivo
            algorithm: Algoritmo de hash (sha256, md5, etc.)

        Returns:
            Hash del archivo o None en caso de error
        """
        try:
            file_path = os.path.expanduser(file_path)
            hash_func = hashlib.new(algorithm)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            _logger.error(f"Error calculando hash de {file_path}: {str(e)}")
            return None

    @staticmethod
    def find_files(directory: str, pattern: str = "*") -> List[str]:
        """
        Encuentra archivos que coincidan con un patrón

        Args:
            directory: Directorio donde buscar
            pattern: Patrón de búsqueda (ej: "*.py")

        Returns:
            Lista de rutas de archivos encontrados
        """
        try:
            directory = os.path.expanduser(directory)
            directory_path = Path(directory)
            return [str(p) for p in directory_path.rglob(pattern)]
        except Exception as e:
            _logger.error(f"Error buscando archivos en {directory}: {str(e)}")
            return []

    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        Obtiene el tamaño de un archivo en bytes

        Args:
            file_path: Ruta del archivo

        Returns:
            Tamaño en bytes o None en caso de error
        """
        try:
            file_path = os.path.expanduser(file_path)
            return os.path.getsize(file_path)
        except Exception as e:
            _logger.error(f"Error obteniendo tamaño de {file_path}: {str(e)}")
            return None

    @staticmethod
    def cleanup_old_files(directory: str, pattern: str, max_age_days: int) -> int:
        """
        Limpia archivos antiguos en un directorio

        Args:
            directory: Directorio a limpiar
            pattern: Patrón de archivos a limpiar (ej: "*.tmp")
            max_age_days: Edad máxima en días

        Returns:
            Número de archivos eliminados
        """
        try:
            directory = os.path.expanduser(directory)
            deleted_count = 0
            now = datetime.now()
            max_age_seconds = max_age_days * 24 * 60 * 60

            for file_path in FileUtils.find_files(directory, pattern):
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    file_age = (now - file_time).total_seconds()

                    if file_age > max_age_seconds:
                        if FileUtils.safe_delete(file_path):
                            deleted_count += 1
                except Exception as e:
                    _logger.warning(f"Error procesando archivo {file_path}: {str(e)}")
                    continue

            return deleted_count

        except Exception as e:
            _logger.error(f"Error limpiando archivos en {directory}: {str(e)}")
            return 0

    @staticmethod
    def copy_file_safe(source: str, destination: str) -> bool:
        """
        Copia un archivo de forma segura

        Args:
            source: Ruta de origen
            destination: Ruta de destino

        Returns:
            True si la copia fue exitosa
        """
        try:
            source = os.path.expanduser(source)
            destination = os.path.expanduser(destination)

            # Crear directorio de destino si no existe
            FileUtils.ensure_directory(os.path.dirname(destination))

            # Copiar archivo
            shutil.copy2(source, destination)
            return True

        except Exception as e:
            _logger.error(f"Error copiando {source} a {destination}: {str(e)}")
            return False
