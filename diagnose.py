#!/usr/bin/env python3

import importlib
import os
import sys
import traceback
from pathlib import Path


def check_file_exists(file_path):
    """Verifica si un archivo existe"""
    exists = os.path.exists(file_path)
    status = "✅" if exists else "❌"
    print(f"{status} {file_path}")
    return exists


def check_module_import(module_path, class_name=None):
    """Verifica si un módulo puede ser importado"""
    try:
        module = importlib.import_module(module_path)
        if class_name:
            getattr(module, class_name)
            print(f"✅ {module_path}.{class_name}")
        else:
            print(f"✅ {module_path}")
        return True
    except Exception as e:
        print(f"❌ {module_path}{f'.{class_name}' if class_name else ''}: {e}")
        return False


def main():
    print("🔍 DIAGNÓSTICO DE ARCH-CHAN AI ASSISTANT")
    print("=" * 50)

    current_dir = Path(__file__).parent
    print(f"📁 Directorio actual: {current_dir}")
    print()

    # Verificar archivos esenciales
    print("📄 VERIFICANDO ARCHIVOS ESENCIALES:")
    essential_files = [
        "main.py",
        "core/__init__.py",
        "core/config_manager.py",
        "core/state_manager.py",
        "core/application.py",
        "ui/__init__.py",
        "ui/main_window.py",
        "ui/components/__init__.py",
        "ui/components/chat_panel.py",
        "ui/components/side_panel.py",
        "ui/components/toolbar.py",
        "ui/components/status_bar.py",
        "utils/__init__.py",
        "utils/logger.py",
    ]

    all_files_exist = True
    for file in essential_files:
        if not check_file_exists(current_dir / file):
            all_files_exist = False

    print()

    # Verificar imports básicos
    print("📦 VERIFICANDO IMPORTS BÁSICOS:")
    basic_imports = [
        ("PySide6.QtWidgets", "QApplication"),
        ("PySide6.QtCore", "QObject"),
        ("utils.logger", "setup_logging"),
        ("core.config_manager", "ConfigManager"),
        ("core.state_manager", "AppStateManager"),
        ("core.application", "ArchChanApplication"),
        ("ui.main_window", "MainWindow"),
    ]

    all_imports_work = True
    for module, class_name in basic_imports:
        if not check_module_import(module, class_name):
            all_imports_work = False

    print()

    # Verificar estructura de directorios
    print("📁 VERIFICANDO ESTRUCTURA:")
    directories = ["core", "ui", "ui/components", "utils"]
    for dir_name in directories:
        dir_path = current_dir / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        status = "✅" if exists else "❌"
        print(f"{status} {dir_name}/")

    print()

    # Resumen
    if all_files_exist and all_imports_work:
        print("🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("🚀 Ejecuta: python main.py")
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print()
        print("💡 SOLUCIONES SUGERIDAS:")
        if not all_files_exist:
            print(
                "  • Asegúrate de que todos los archivos .py estén en sus directorios"
            )
            print("  • Verifica que los nombres de archivo sean correctos")
        if not all_imports_work:
            print("  • Instala dependencias faltantes: pip install PySide6")
            print("  • Revisa errores de sintaxis en los archivos Python")
            print("  • Verifica que los imports en los archivos sean correctos")

    return 0 if (all_files_exist and all_imports_work) else 1


if __name__ == "__main__":
    sys.exit(main())
