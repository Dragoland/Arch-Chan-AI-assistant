#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import traceback
from pathlib import Path

# Agregar el directorio actual al path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def setup_environment():
    """Configura el entorno de la aplicación"""
    # Establecer directorio de trabajo
    os.chdir(current_dir)

    # Configurar variables de entorno para Qt
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

    # Mejorar compatibilidad Wayland/X11
    if "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland"
    else:
        os.environ["QT_QPA_PLATFORM"] = "xcb"


def verify_imports():
    """Verifica que todos los imports críticos funcionen"""
    print("📦 Verificando imports críticos...")

    imports_to_check = [
        ("PySide6.QtWidgets", "QApplication, QMessageBox"),
        ("PySide6.QtCore", "QTimer, QObject, QThread"),
        ("utils.logger", "get_logger, setup_logging"),
        ("utils.constants", "PROJECT_DIR, LOGS_DIR, TEMP_DIR, MODELS_DIR"),
        ("utils.file_utils", "FileUtils"),
        ("core.config_manager", "ConfigManager"),
        ("core.dependency_checker", "DependencyChecker"),
        ("core.application", "ArchChanApplication"),
        ("core.state_manager", "AppStateManager"),
        ("services.ollama_client", "OllamaClient"),
        ("services.system_monitor", "SystemMonitor"),
        ("psutil", "psutil"),
    ]

    for module, imports in imports_to_check:
        try:
            __import__(module)
            print(f"✅ {module} importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando {module}: {e}")
            return False

    print("✅ Todos los imports críticos funcionan correctamente")
    return True


def main():
    """Punto de entrada principal de la aplicación"""
    try:
        print("🚀 Iniciando Arch-Chan AI Assistant v2.1.0...")

        # Configurar entorno
        setup_environment()
        print("✅ Entorno configurado correctamente")

        # Verificar imports
        if not verify_imports():
            return 1

        # Configurar logging (usando constantes)
        # Asegurar que los directorios de constantes existen
        from utils.constants import LOGS_DIR, MODELS_DIR, PROJECT_DIR, TEMP_DIR
        from utils.file_utils import FileUtils
        from utils.logger import get_logger, setup_logging

        # CORRECCIÓN: Convertir a string si son Path objects
        FileUtils.ensure_directory(str(PROJECT_DIR))
        FileUtils.ensure_directory(str(LOGS_DIR))
        FileUtils.ensure_directory(str(TEMP_DIR))
        FileUtils.ensure_directory(str(MODELS_DIR))

        logger = setup_logging(log_dir=str(LOGS_DIR))
        logger.info("Logger configurado correctamente")

        # Crear aplicación Qt
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication, QMessageBox

        logger.info("Creando aplicación Qt...")
        app = QApplication(sys.argv)
        app.setApplicationName("Arch-Chan AI Assistant")
        app.setApplicationVersion("2.1.0")
        app.setOrganizationName("Arch-Chan")
        app.setOrganizationDomain("arch-chan.org")

        # Establecer estilo de aplicación
        app.setStyle("Fusion")

        # Crear y mostrar aplicación principal
        logger.info("Creando aplicación principal...")
        try:
            from core.application import ArchChanApplication

            application = ArchChanApplication()

            # Conectar señal de shutdown
            application.app_shutdown.connect(app.quit)

            # Iniciar aplicación con timer para asegurar que el event loop esté corriendo
            QTimer.singleShot(0, application.start)

            logger.info("Aplicación Arch-Chan v2.1.0 iniciada correctamente")

        except Exception as e:
            logger.error(f"Error iniciando aplicación: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Error Inicial",
                f"No se pudo iniciar la aplicación:\n\n{str(e)}\n\n"
                "Revisa la consola para más detalles.",
            )
            return 1

        # Configurar manejo de excepciones no capturadas
        def handle_exception(exc_type, exc_value, exc_traceback):
            """Maneja excepciones no capturadas"""
            if issubclass(exc_type, KeyboardInterrupt):
                # Ignorar KeyboardInterrupt para permitir cierre normal
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            logger.critical(
                "Excepción no capturada:", exc_info=(exc_type, exc_value, exc_traceback)
            )

            # Mostrar diálogo de error
            error_msg = f"{exc_type.__name__}: {exc_value}"
            QMessageBox.critical(
                None,
                "Error Crítico",
                f"Se produjo un error crítico:\n\n{error_msg}\n\n"
                "La aplicación se cerrará.",
            )
            # Intentar apagar la aplicación de forma ordenada
            if "application" in locals() and hasattr(application, "shutdown"):
                application.shutdown()

        sys.excepthook = handle_exception

        # Ejecutar loop principal
        logger.info("Ejecutando loop principal de Qt...")
        return_code = app.exec()

        logger.info(f"Aplicación finalizada con código: {return_code}")
        return return_code

    except Exception as e:
        print(f"❌ Error crítico en main(): {e}")
        traceback.print_exc()

        # Intentar mostrar diálogo de error si Qt está disponible
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox

            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Error Crítico",
                f"Error inicializando la aplicación:\n\n{str(e)}\n\n"
                "Revisa la consola para más detalles.\n\n"
                "Posibles soluciones:\n"
                "1. Verifica que todas las dependencias estén instaladas\n"
                "2. Ejecuta 'python -m pip install -r requirements.txt'\n"
                "3. Verifica que Ollama esté instalado y ejecutándose",
            )
            return 1
        except:
            print("No se pudo mostrar diálogo de error")
            return 1


if __name__ == "__main__":
    print("🎯 Iniciando Arch-Chan AI Assistant...")
    print(f"📁 Directorio: {Path(__file__).parent}")
    print(f"🐍 Python: {sys.version}")

    exit_code = main()
    print(f"🔚 Saliendo con código: {exit_code}")
    sys.exit(exit_code)
