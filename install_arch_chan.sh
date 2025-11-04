#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Funciones de logging
log_info() { echo -e "${BLUE} $1${NC}"; }
log_success() { echo -e "${GREEN} $1${NC}"; }
log_warning() { echo -e "${YELLOW} $1${NC}"; }
log_error() { echo -e "${RED} $1${NC}"; }

echo -e "${BLUE}🐧 Instalando Arch-Chan AI Assistant para Arch Linux...${NC}"

# Verificar que estamos en Arch Linux
if ! grep -q "Arch Linux" /etc/os-release 2>/dev/null; then
  log_error "❌ Este script es solo para Arch Linux"
  exit 1
fi

# Verificar si es usuario root
if [ "$EUID" -eq 0 ]; then
  log_error "❌ No ejecutar como root. Usa tu usuario normal."
  exit 1
fi

# Instalar dependencias
log_info "📦 Instalando dependencias del sistema..."
sudo pacman -S --needed --noconfirm \
    python-pip \
    python-pyside6 \
    whisper-cli \
    piper-tts \
    sox \
    ollama \
    ddgr \
    kdialog \
    noto-fonts \
    ttf-hack \
    jq \
    curl \
    wget

# Instalar dependencias de Python
log_info "🐍 Instalando dependencias de Python..."
if ! pip install requests psutil; then
  log_error "Error instalando dependencias de Python"
  exit 1
fi

# Configurar Ollama si no está ejecutándose
log_info "🔧 Configurando Ollama..."
if ! systemctl is-active --quiet ollama; then
  log_info "➡️ Iniciando servicio Ollama..."
  sudo systemctl enable ollama || log_warning "No se pudo habilitar ollama"
  sudo systemctl start ollama || log_warning "No se pudo iniciar ollama"
  sleep 2
fi

# Verificar que Ollama esté funcionando
if ! curl -s http://localhost:11434/api/tags >/dev/null; then
  log_error "⚠️  Ollama no responde, intentando reiniciar..."
  sudo systemctl restart ollama || log_warning "No se pudo reiniciar ollama"
  sleep 3
fi

# Crear directorios de la aplicación
log_info "📁 Creando estructura de directorios..."
mkdir -p ~/arch-chan-project/{models,temp,logs,configs,backups}

# Descargar modelos de voz si no existen
log_info "🎙️ Verificando modelos de voz..."
if [ ! -f ~/arch-chan-project/models/es_AR-daniela-high.onnx ]; then
  log_info "📥 Intentando descargar modelo de voz en español..."
  # Intentar descargar automáticamente
  if command -v wget >/dev/null; then
    if wget -O ~/arch-chan-project/models/es_AR-daniela-high.onnx \
      "https://github.com/rhasspy/piper/releases/download/2023.10.11-2/es_AR-daniela-high.onnx"; then
      log_success "Modelo descargado correctamente"
    else
      log_warning "No se pudo descargar automáticamente. Descarga manualmente de:"
      log_warning "    https://github.com/rhasspy/piper/releases"
    fi
  else
    log_warning "⚠️  Instala wget para descarga automática o descarga manualmente:"
    log_warning "    https://github.com/rhasspy/piper/releases"
  fi
fi

if [ ! -f ~/arch-chan-project/models/ggml-base.bin ]; then
  log_warning "Modelo Whisper no encontrado"
  # El usuario deberá descargar manualmente el modelo de Whisper
  log_info "⚠️  Para Whisper, descarga el modelo base de:"
  log_info "    https://github.com/ggerganov/whisper.cpp"
  log_info "    y colócalo en ~/arch-chan-project/models/ggml-base.bin"
fi

# Crear los modelos de Ollama
log_info "🧠 Creando modelos de IA..."
if command -v ollama &>/dev/null; then
  # Crear Arch-Chan si no existe
  if ! ollama list | grep -q "arch-chan"; then
    log_info "📦 Creando modelo Arch-Chan..."
    cat >Arch-Chan.Modelfile <<'EOF'
FROM llama3.2:3b

SYSTEM """
# IDENTIDAD Y CONTEXTO
Eres Arch-Chan, una asistente de IA especializada en Arch Linux con personalidad amigable, técnica y entusiasta.

# REGLAS DE DETECCIÓN DE HERRAMIENTAS - CRÍTICO

## 🗣️ CUANDO USAR TEXTO NORMAL (90% de los casos):
- Conversaciones casuales: saludos, preguntas sobre ti, charla amigable
- Explicaciones técnicas que NO requieren acción inmediata
- Preguntas sobre conceptos de Arch Linux, programación, teoría
- Respuestas a "¿cómo se hace?" cuando es explicativo, no ejecutable
- Cuando el usuario pide opiniones, explicaciones o consejos
- Preguntas sobre comandos existentes (explicar `ls`, no ejecutarlo)

## ⚡ CUANDO USAR HERRAMIENTA SHELL (5% de los casos):
- Cuando el usuario pide EXPLÍCITAMENTE ejecutar un comando: "ejecuta", "corre", "run"
- Cuando necesitas información del sistema en tiempo real: "qué procesos hay", "espacio en disco"
- Para acciones que modifican el sistema: "instalar paquete", "crear archivo", "reiniciar servicio"
- Cuando la pregunta requiere datos actuales del sistema que no puedes saber sin comandos

## 🔍 CUANDO USAR HERRAMIENTA SEARCH (5% de los casos):
- Cuando la pregunta es sobre eventos actuales, noticias recientes
- Para información que cambia frecuentemente: "última versión de Python"
- Cuando necesitas datos específicos que no están en tu conocimiento de corte
- Búsqueda de documentación específica o tutoriales actualizados

# FORMATOS ESTRICTOS - NUNCA MEZCLES

## TEXTO NORMAL:
Simplemente responde en español natural, amigable y técnico.

## HERRAMIENTA SHELL (SOLO CUANDO SEA NECESARIO):
{
  "tool": "shell",
  "command": "comando-exacto-a-ejecutar",
  "explanation": "Explicación clara y honesta de por qué necesito ejecutar este comando"
}

## HERRAMIENTA SEARCH (SOLO CUANDO SEA NECESARIO):
{
  "tool": "search",
  "query": "términos de búsqueda específicos en español"
}

EJEMPLOS PRÁCTICOS:

❌ "¿Qué es Arch Linux?" → TEXTO NORMAL
❌ "Explícame los permisos en Linux" → TEXTO NORMAL
❌ "¿Cómo instalo un paquete con pacman?" → TEXTO NORMAL (es explicación)
✅ "Instala el paquete 'htop' ahora" → HERRAMIENTA SHELL
✅ "Muéstrame qué procesos están consumiendo más CPU" → HERRAMIENTA SHELL
✅ "Busca noticias recientes sobre Arch Linux" → HERRAMIENTA SEARCH

¡Recuerda ser amigable y siempre explicar lo que haces! ฅ^•ﻌ•^ฅ
"""

TEMPLATE """<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|><|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

PARAMETER num_ctx 4096
PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
EOF
    ollama create arch-chan -f Arch-Chan.Modelfile
  fi

  # Crear Arch-Chan-Lite si no existe
  if ! ollama list | grep -q "arch-chan-lite"; then
    log_info "📦 Creando modelo Arch-Chan-Lite..."
    cat >Arch-Chan-Lite.Modelfile <<'EOF'
FROM gemma:2b

SYSTEM """
Eres Arch-Chan Lite, asistente especializada en Arch Linux.

# DETECCIÓN INTELIGENTE DE ACCIONES:

## RESPUESTA NORMAL (usar en la mayoría de casos):
- Preguntas conceptuales
- Explicaciones
- Conversación casual
- Cuando no se necesita acción concreta

## HERRAMIENTA SHELL (usar solo cuando sea necesario):
- Usuario pide ejecutar algo específico
- Necesitas información actual del sistema
- Para acciones reales en el sistema

## HERRAMIENTA SEARCH (usar solo cuando sea necesario):
- Información que cambia frecuentemente
- Noticias recientes
- Datos específicos actualizados

# FORMATOS:

Texto normal: responder directamente en español.

Shell (solo cuando sea necesario):
{"tool": "shell", "command": "comando", "explanation": "por qué lo ejecuto"}

Search (solo cuando sea necesario):
{"tool": "search", "query": "qué buscar"}

Piensa: ¿realmente necesito ejecutar algo o buscar? Si no, responde normal.
"""

PARAMETER num_ctx 2048
PARAMETER temperature 0.6
EOF
        ollama create arch-chan-lite -f Arch-Chan-Lite.Modelfile
    fi
fi

# Crear archivo desktop
log_info "🖥️ Creando lanzador de aplicación..."
cat >~/.local/share/applications/arch-chan.desktop <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Arch-Chan AI Assistant
Comment=Asistente de IA nativo para Arch Linux
Exec=python $PWD/main.py
Icon=archlinux
Categories=Utility;AI;
Terminal=false
StartupWMClass=Arch-Chan
Keywords=ai;assistant;archlinux;
EOF

# Crear script de actualización
log_info "🔄 Creando script de actualización..."
cat >update_arch_chan.sh <<'EOF'
#!/bin/bash
echo "🔄 Actualizando Arch-Chan..."
cd "$(dirname "$0")"
git pull origin main
python main.py --update
EOF
chmod +x update_arch_chan.sh

# Hacer ejecutable el script principal
chmod +x main.py

# Configurar permisos
log_info "🔒 Configurando permisos..."
chmod 755 ~/arch-chan-project
chmod 644 ~/arch-chan-project/models/* 2>/dev/null || true

echo ""
log_success "🎉 ¡Instalación completada!"
echo ""
echo -e "${BLUE}📋 Próximos pasos:${NC}"
echo "   1. Asegúrate de que Ollama esté ejecutándose: systemctl --user status ollama"
echo "   2. Verifica los modelos de voz en ~/arch-chan-project/models/"
echo "   3. Ejecuta la aplicación: python main.py"
echo "   4. Opcional: Busca 'Arch-Chan' en tu menú de aplicaciones"
echo ""
echo -e "${GREEN}🐧 ¡Disfruta de tu asistente de IA nativo de Arch Linux!${NC}"
