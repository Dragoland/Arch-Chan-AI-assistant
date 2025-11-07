#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configuración global de logging
_loggers = {}

def setup_logging(
    log_dir: str = "~/arch-chan-project/logs",
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Configura el sistema de logging para la aplicación

    Args:
        log_dir: Directorio donde guardar los logs
        level: Nivel de logging
        console_output: Si mostrar logs en consola

    Returns:
        Logger configurado
    """
    # Expandir directorio de usuario
    log_dir = os.path.expanduser(log_dir)
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Crear archivo de log con timestamp
    log_file = os.path.join(
        log_dir,
        f"arch-chan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configurar handlers
    handlers = []

    # Handler de archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    # Handler de consola (opcional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # Configurar logging root
    logging.basicConfig(
        level=level,
        handlers=handlers
    )

    # Logger principal
    main_logger = logging.getLogger("ArchChan")
    main_logger.info(f"Sistema de logging inicializado: {log_file}")

    return main_logger

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Obtiene o crea un logger con el nombre especificado

    Args:
        name: Nombre del logger
        level: Nivel de logging (opcional)

    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    if level is not None:
        logger.setLevel(level)

    _loggers[name] = logger
    return logger

def set_log_level(level: int):
    """
    Establece el nivel de logging para todos los loggers

    Args:
        level: Nivel de logging
    """
    for logger in _loggers.values():
        logger.setLevel(level)

class LoggingMixin:
    """Mix-in para agregar capacidades de logging a las clases"""

    @property
    def logger(self) -> logging.Logger:
        """Retorna el logger para esta clase"""
        if not hasattr(self, '_logger'):
            class_name = self.__class__.__name__
            self._logger = get_logger(class_name)
        return self._logger

# Utilidades específicas para diferentes componentes
def log_function_call(logger: logging.Logger):
    """
    Decorador para loggear llamadas a funciones

    Args:
        logger: Logger a utilizar
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Llamando {func.__name__} con args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Función {func.__name__} completada exitosamente")
                return result
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator

def log_execution_time(logger: logging.Logger):
    """
    Decorador para medir y loggear tiempo de ejecución

    Args:
        logger: Logger a utilizar
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()

            result = func(*args, **kwargs)

            execution_time = time.time() - start_time
            logger.debug(f"Función {func.__name__} ejecutada en {execution_time:.3f}s")

            return result
        return wrapper
    return decorator
