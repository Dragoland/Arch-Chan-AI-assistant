import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ollama_client import OllamaClient


def debug_ollama_connection():
    print("=== DIAGNÓSTICO DE OLLAMA ===")

    client = OllamaClient()

    # 1. Verificar salud
    print("1. Verificando salud de Ollama...")
    health = client.check_health()
    print(f"   Salud: {health}")

    if not health:
        print("   ❌ Ollama no está disponible")
        return False

    # 2. Listar modelos
    print("2. Listando modelos...")
    models = client.list_models()
    if models:
        print(f"   ✅ Modelos encontrados: {len(models)}")
        for model in models[:5]:  # Mostrar solo los primeros 5
            name = model.get("name", "Unknown")
            print(f"   - {name}")
    else:
        print("   ❌ No se encontraron modelos")
        return False

    # 3. Probar un prompt simple
    print("3. Probando prompt simple...")
    try:
        test_messages = [
            {"role": "user", "content": "Responde con 'OK' si estás funcionando."}
        ]
        response = client.chat(model="llama2", messages=test_messages, stream=False)

        if response and "message" in response:
            content = response["message"].get("content", "No content")
            print(f"   ✅ Respuesta recibida: {content}")
        else:
            print("   ❌ No se recibió respuesta válida")
            return False

    except Exception as e:
        print(f"   ❌ Error en prueba: {e}")
        return False

    print("✅ Ollama está funcionando correctamente")
    return True


if __name__ == "__main__":
    debug_ollama_connection()
