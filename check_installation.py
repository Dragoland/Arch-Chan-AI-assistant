#!/usr/bin/env python3

import importlib
import os
import sys


def check_import(module_name, package_name=None):
    """Verifica si un módulo puede ser importado"""
    try:
        if package_name:
            module = importlib.import_module(module_name, package=package_name)
        else:
            module = importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name}: {e}")
        return False


def main():
    print("🔍 Verificando instalación de Arch-Chan AI Assistant...")
    print()

    # Verificar dependencias externas
    print("📦 Verificando dependencias externas:")
    external_deps = [
        "PySide6",
        "requests",
        "psutil",
    ]

    for dep in external_deps:
        check_import(dep)

    print()

    # Verificar módulos internos
    print("🏗️ Verificando módulos internos:")
    internal_modules = [
        ("core.config_manager", "core"),
        ("core.dependency_checker", "core"),
        ("core.state_manager", "core"),
        ("core.application", "core"),
        ("ui.main_window", "ui"),
        ("ui.components.chat_panel", "ui.components"),
        ("ui.components.side_panel", "ui.components"),
        ("ui.components.toolbar", "ui.components"),
        ("ui.components.status_bar", "ui.components"),
        ("ui.themes.arch_theme", "ui.themes"),
        ("services.ollama_client", "services"),
        ("services.speech_service", "services"),
        ("services.command_executor", "services"),
        ("services.system_monitor", "services"),
        ("workers.base_worker", "workers"),
        ("workers.chat_worker", "workers"),
        ("workers.voice_worker", "workers"),
        ("models.chat_models", "models"),
        ("models.config_models", "models"),
        ("models.system_models", "models"),
        ("utils.logger", "utils"),
        ("utils.validators", "utils"),
        ("utils.file_utils", "utils"),
        ("utils.constants", "utils"),
    ]

    all_ok = True
    for module, package in internal_modules:
        if not check_import(module, package):
            all_ok = False

    print()

    if all_ok:
        print(
            "🎉 ¡Todas las verificaciones pasaron! El software debería funcionar correctamente."
        )
        print("🚀 Ejecuta: python main.py")
    else:
        print("❌ Algunas verificaciones fallaron. Revisa los errores arriba.")
        print("💡 Asegúrate de que todos los archivos .py estén en su lugar.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
