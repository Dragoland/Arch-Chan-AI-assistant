#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import traceback
from pathlib import Path

# Agregar el directorio actual al path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"🔍 Directorio actual: {current_dir}")
print(f"🔍 Python path: {sys.path}")


def main():
    """Punto de entrada principal de la aplicación"""
    try:
        print("🚀 Iniciando Arch-Chan AI Assistant v2.1.0...")

        # Verificar que estamos en el directorio correcto
        os.chdir(current_dir)
        print("✅ Directorio de trabajo configurado")

        # Verificar imports críticos uno por uno
        print("📦 Verificando imports...")

        try:
            from PySide6.QtWidgets import QApplication, QMessageBox

            print("✅ PySide6 importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando PySide6: {e}")
            print("💡 Instala PySide6: pip install PySide6")
            return 1

        try:
            from utils.logger import get_logger, setup_logging

            print("✅ Logger importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando logger: {e}")
            return 1

        # Configurar logging
        logger = setup_logging()
        logger.info("Logger configurado correctamente")

        try:
            from core.config_manager import ConfigManager

            print("✅ ConfigManager importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando ConfigManager: {e}")
            logger.error(f"Error importando ConfigManager: {e}")
            return 1

        try:
            from core.dependency_checker import DependencyChecker

            print("✅ DependencyChecker importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando DependencyChecker: {e}")
            logger.error(f"Error importando DependencyChecker: {e}")
            return 1

        try:
            from core.application import ArchChanApplication

            print("✅ ArchChanApplication importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando ArchChanApplication: {e}")
            logger.error(f"Error importando ArchChanApplication: {e}")
            return 1

        print("✅ Todos los imports críticos funcionan correctamente")

        # Crear aplicación Qt
        logger.info("Creando aplicación Qt...")
        app = QApplication(sys.argv)
        app.setApplicationName("Arch-Chan AI Assistant")
        app.setApplicationVersion("2.1.0")
        app.setOrganizationName("Arch-Chan")

        # Crear y mostrar aplicación principal
        logger.info("Creando aplicación principal...")
        try:
            application = ArchChanApplication()
            application.start()
            logger.info("Aplicación Arch-Chan v2.1.0 iniciada correctamente")
        except Exception as e:
            logger.error(f"Error iniciando aplicación: {e}", exc_info=True)
            QMessageBox.critical(
                None, "Error Inicial", f"No se pudo iniciar la aplicación:\n\n{str(e)}"
            )
            return 1

        # Ejecutar loop principal
        logger.info("Ejecutando loop principal...")
        return_code = app.exec()

        logger.info(f"Aplicación finalizada con código: {return_code}")
        return return_code

    except Exception as e:
        print(f"❌ Error crítico en main(): {e}")
        traceback.print_exc()

        # Intentar mostrar diálogo de error si Qt está disponible
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Error Crítico",
                f"Error inicializando la aplicación:\n\n{str(e)}\n\nRevisa la consola para más detalles.",
            )
        except:
            print("No se pudo mostrar diálogo de error")

        return 1


if __name__ == "__main__":
    print("🎯 Iniciando Arch-Chan AI Assistant...")
    exit_code = main()
    print(f"🔚 Saliendo con código: {exit_code}")
    sys.exit(exit_code)
