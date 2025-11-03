#!/usr/bin/env python3
import subprocess
import requests
import time

def create_arch_chan_model():
    """Crea el modelo Arch-Chan corregido"""
    modelfile = """
FROM llama3.2:3b

SYSTEM \"\"\"
Eres Arch-Chan, una asistente de IA especializada en Arch Linux.

REGlas:
1. Para conversación normal: responde con texto en español
2. Para acciones: usa EXCLUSIVAMENTE JSON válido

Formatos permitidos:
- Comando: {"tool": "shell", "command": "comando", "explanation": "explicación"}
- Búsqueda: {"tool": "search", "query": "términos"}

Prohibiciones:
❌ NUNCA uses markdown para JSON
❌ NUNCA mezcles JSON con texto
❌ SOLO "shell" o "search" en el campo tool
\"\"\"

TEMPLATE \"\"\"<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|><|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

\"\"\"

PARAMETER num_ctx 4096
PARAMETER temperature 0.7
"""

    with open('Arch-Chan.Modelfile', 'w', encoding='utf-8') as f:
        f.write(modelfile)

    print("Creando modelo Arch-Chan...")
    result = subprocess.run(['ollama', 'create', 'arch-chan', '-f', 'Arch-Chan.Modelfile'],
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Error:", result.stderr)

def create_arch_chan_lite_model():
    """Crea el modelo Arch-Chan Lite corregido"""
    modelfile = """
FROM gemma:2b

SYSTEM \"\"\"
Eres Arch-Chan Lite, versión optimizada para Arch Linux.

Instrucciones:
1. Conversación normal: texto en español
2. Acciones: SOLO JSON válido

Formatos:
{"tool": "shell", "command": "comando", "explanation": "razón"}
{"tool": "search", "query": "qué buscar"}

Restricciones:
- SOLO "shell" o "search" en tool
- JSON válido sin texto extra
\"\"\"

PARAMETER num_ctx 2048
PARAMETER temperature 0.6
"""

    with open('Arch-Chan-Lite.Modelfile', 'w', encoding='utf-8') as f:
        f.write(modelfile)

    print("Creando modelo Arch-Chan-Lite...")
    result = subprocess.run(['ollama', 'create', 'arch-chan-lite', '-f', 'Arch-Chan-Lite.Modelfile'],
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Error:", result.stderr)

def verify_models():
    """Verifica que los modelos se crearon correctamente"""
    time.sleep(2)
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        models = response.json()
        print("\n=== MODELOS DISPONIBLES ===")
        for model in models['models']:
            print(f"✓ {model['name']}")
    except Exception as e:
        print(f"Error verificando modelos: {e}")

if __name__ == "__main__":
    create_arch_chan_model()
    create_arch_chan_lite_model()
    verify_models()
