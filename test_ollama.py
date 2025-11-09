#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ollama_client import OllamaClient


def main():
    print("=== Diagnóstico de Ollama ===")

    client = OllamaClient()

    print("1. Verificando salud de Ollama...")
    health = client.check_health()
    print(f"   Salud: {health}")

    if health:
        print("2. Listando modelos...")
        models = client.list_models()
        if models:
            print(f"   Modelos encontrados: {len(models)}")
            for model in models:
                name = model.get("name", "Unknown")
                print(f"   - {name}")
        else:
            print("   No se encontraron modelos")
    else:
        print("   Ollama no está disponible")

    print("3. Probando conexión completa...")
    diag = client.diagnostic_check()
    print(f"   Diagnóstico: {diag}")


if __name__ == "__main__":
    main()
