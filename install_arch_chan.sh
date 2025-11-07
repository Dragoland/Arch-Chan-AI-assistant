#!/bin/bash

# Arch-Chan AI Assistant - Instalador Mejorado
# Versión: 2.1.0
# Autor: Dragoland

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # Sin color

# Funciones de logging mejoradas
log_info() { echo -e "${BLUE}📘 [INFO] $1${NC}"; }
log_success() { echo -e "${GREEN}✅ [SUCCESS] $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️ [WARNING] $1${NC}"; }
log_error() { echo -e "${RED}❌ [ERROR] $1${NC}"; }
log_debug() { echo -e "${CYAN}🐛 [DEBUG] $1${NC}"; }
log_step() { echo -e "${MAGENTA}🚀 [STEP] $1${NC}"; }

# Funcion para verificar comandos
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para instalar paquetes con manejo de errores mejorado
install_packages() {
    local packages=("$@")
    log_info "Instalando paquetes: ${packages[*]}"
    
    if ! sudo pacman -S --needed --noconfirm "${packages[@]}"; then
        log_error "Error instalando paquetes: ${packages[*]}"
        return 1
    fi
    return 0
}

# Función para verificar sistema
verify_system() {
    log_step "Verificando sistema..."
    
    # Verificar que estamos en Arch Linux
    if ! grep -q "Arch Linux" /etc/os-release 2>/dev/null; then
        log_error "Este script es solo para Arch Linux"
        log_info "Si estás en otra distribución, considera usar el empaquetado PIP"
        exit 1
    fi

    # Verificar si es usuario root
    if [ "$EUID" -eq 0 ]; then
        log_error "No ejecutar como root. Usa tu usuario normal."
        exit 1
    fi

    # Verificar conexión a internet
    if ! ping -c 1 archlinux.org &> /dev/null; then
        log_error "No hay conexión a internet. Verifica tu conexión."
        exit 1
    fi

    log_success "Sistema verificado correctamente"
}

# Función para instalar dependencias del sistema
install_system_dependencies() {
    log_step "Instalando dependencias del sistema..."
    
    local system_dependencies=(
        python-pip
        whisper.cpp
        piper-tts
        sox
        ollama
        ddgr
        kdialog
        noto-fonts
        ttf-hack
        jq
        curl
        wget
        git
        base-devel
    )

    if ! install_packages "${system_dependencies[@]}"; then
        log_error "Fallo en la instalación de dependencias del sistema"
        exit 1
    fi

    log_success "Dependencias del sistema instaladas correctamente"
}

# Función para configurar Ollama
setup_ollama() {
    log_step "Configurando Ollama..."
    
    # Verificar e iniciar servicio Ollama
    if ! systemctl is-active --quiet ollama; then
        log_info "Iniciando servicio Ollama..."
        sudo systemctl enable ollama || log_warning "No se pudo habilitar ollama"
        sudo systemctl start ollama || log_warning "No se pudo iniciar ollama"
        sleep 3
    fi

    # Verificar que Ollama esté funcionando
    local max_retries=5
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -s http://localhost:11434/api/tags >/dev/null; then
            log_success "Ollama está funcionando correctamente"
            return 0
        else
            log_warning "Ollama no responde, reintentando... ($((retry_count + 1))/$max_retries)"
            sudo systemctl restart ollama || true
            sleep 5
            ((retry_count++))
        fi
    done

    log_error "Ollama no responde después de $max_retries intentos"
    log_info "Puedes intentar configurar Ollama manualmente más tarde"
    return 1
}

# Función para crear estructura de directorios
create_directory_structure() {
    log_step "Creando estructura de directorios..."
    
    local directories=(
        "$APP_DIR"
        "$MODEL_DIR"
        "$CONFIG_DIR"
        "$LOG_DIR"
        "$APP_DIR/temp"
        "$APP_DIR/backups"
        "$APP_DIR/cache"
    )

    for dir in "${directories[@]}"; do
        if mkdir -p "$dir"; then
            log_debug "Directorio creado: $dir"
        else
            log_error "No se pudo crear el directorio: $dir"
            exit 1
        fi
    done

    log_success "Estructura de directorios creada correctamente"
}

# Función para descargar modelos de voz
download_voice_models() {
    log_step "Verificando modelos de voz..."
    
    # Modelo Piper TTS (Español)
    if [ ! -f "$MODEL_DIR/es_AR-daniela-high.onnx" ]; then
        log_info "Descargando modelo de voz en español (Piper TTS)..."
        
        local piper_url="https://github.com/rhasspy/piper/releases/download/2023.10.11-2/es_AR-daniela-high.onnx"
        local piper_json_url="https://github.com/rhasspy/piper/releases/download/2023.10.11-2/es_AR-daniela-high.onnx.json"
        
        if command_exists wget; then
            if wget -O "$MODEL_DIR/es_AR-daniela-high.onnx" "$piper_url" && \
               wget -O "$MODEL_DIR/es_AR-daniela-high.onnx.json" "$piper_json_url"; then
                log_success "Modelo Piper TTS descargado correctamente"
            else
                log_warning "No se pudo descargar el modelo Piper TTS automáticamente"
                log_info "Descarga manualmente desde: https://github.com/rhasspy/piper/releases"
            fi
        else
            log_warning "wget no disponible para descarga automática"
            log_info "Instala wget o descarga manualmente los modelos de voz"
        fi
    else
        log_info "Modelo Piper TTS ya existe"
    fi

    # Modelo Whisper
    if [ ! -f "$MODEL_DIR/ggml-base.bin" ]; then
        log_warning "Modelo Whisper no encontrado"
        log_info "Para Whisper, descarga el modelo base de:"
        log_info "https://github.com/ggerganov/whisper.cpp"
        log_info "Y colócalo en: $MODEL_DIR/ggml-base.bin"
    else
        log_info "Modelo Whisper ya existe"
    fi
}

# Función para crear modelos de Ollama
create_ollama_models() {
    log_step "Creando modelos de IA..."
    
    if ! command_exists ollama; then
        log_error "Ollama no está disponible"
        return 1
    fi

    # Crear Arch-Chan si no existe
    if ! ollama list | grep -q "arch-chan"; then
        log_info "Creando modelo Arch-Chan..."
        
        cat > "$APP_DIR/Arch-Chan.Modelfile" << 'EOF'
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

        if ollama create arch-chan -f "$APP_DIR/Arch-Chan.Modelfile"; then
            log_success "Modelo Arch-Chan creado correctamente"
        else
            log_error "Error creando modelo Arch-Chan"
        fi
    else
        log_info "Modelo Arch-Chan ya existe"
    fi

    # Crear Arch-Chan-Lite si no existe
    if ! ollama list | grep -q "arch-chan-lite"; then
        log_info "Creando modelo Arch-Chan-Lite..."
        
        cat > "$APP_DIR/Arch-Chan-Lite.Modelfile" << 'EOF'
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

        if ollama create arch-chan-lite -f "$APP_DIR/Arch-Chan-Lite.Modelfile"; then
            log_success "Modelo Arch-Chan-Lite creado correctamente"
        else
            log_error "Error creando modelo Arch-Chan-Lite"
        fi
    else
        log_info "Modelo Arch-Chan-Lite ya existe"
    fi
}

# Función para crear lanzador de aplicación
create_desktop_file() {
    log_step "Creando lanzador de aplicación..."
    
    local desktop_dir="$HOME/.local/share/applications"
    mkdir -p "$desktop_dir"
    
    cat > "$desktop_dir/arch-chan.desktop" << EOF
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
X-GNOME-Autostart-enabled=true
EOF

    if [ -f "$desktop_dir/arch-chan.desktop" ]; then
        log_success "Archivo desktop creado correctamente"
    else
        log_error "Error creando archivo desktop"
    fi
}

# Función para crear script de actualización
create_update_script() {
    log_step "Creando script de actualización..."
    
    cat > "$APP_DIR/update_arch_chan.sh" << 'EOF'
#!/bin/bash

# Arch-Chan AI Assistant - Script de Actualización
# Versión: 2.1.0

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 Actualizando Arch-Chan AI Assistant...${NC}"

# Verificar si es un repositorio git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ No es un repositorio git. Actualización manual requerida.${NC}"
    exit 1
fi

# Actualizar código
echo -e "${BLUE}📥 Descargando actualizaciones...${NC}"
if git pull origin main; then
    echo -e "${GREEN}✅ Código actualizado correctamente${NC}"
else
    echo -e "${RED}❌ Error al actualizar el código${NC}"
    exit 1
fi

# Actualizar dependencias de Python
echo -e "${BLUE}📦 Actualizando dependencias de Python...${NC}"
if pip install -r requirements.txt; then
    echo -e "${GREEN}✅ Dependencias actualizadas correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  Advertencia: Error actualizando algunas dependencias${NC}"
fi

# Actualizar modelos si es necesario
echo -e "${BLUE}🧠 Verificando modelos de IA...${NC}"
if command -v ollama >/dev/null 2>&1; then
    echo -e "${BLUE}🔄 Actualizando modelos de Ollama...${NC}"
    python setup_models.py
fi

echo -e "${GREEN}🎉 ¡Actualización completada!${NC}"
echo -e "${BLUE}💡 Ejecuta 'python main.py' para iniciar la aplicación${NC}"
EOF

    chmod +x "$APP_DIR/update_arch_chan.sh"
    log_success "Script de actualización creado correctamente"
}

# Función para configurar permisos
setup_permissions() {
    log_step "Configurando permisos..."
    
    # Dar permisos de ejecución a scripts
    find "$APP_DIR" -type f -name "*.sh" -exec chmod +x {} \;
    chmod +x main.py 2>/dev/null || true
    chmod +x setup_models.py 2>/dev/null || true
    
    # Permisos de directorios
    chmod 755 "$APP_DIR"
    chmod 755 "$MODEL_DIR" 2>/dev/null || true
    chmod 644 "$MODEL_DIR"/* 2>/dev/null || true
    
    log_success "Permisos configurados correctamente"
}

# Función para verificación final
final_verification() {
    log_step "Realizando verificaciones finales..."
    
    local checks_passed=0
    local checks_total=6
    
    # Verificar directorio de la aplicación
    if [ -d "$APP_DIR" ]; then
        ((checks_passed++))
        log_debug "✅ Directorio de aplicación existe"
    else
        log_error "❌ Directorio de aplicación no existe"
    fi
    
    # Verificar archivo desktop
    if [ -f "$HOME/.local/share/applications/arch-chan.desktop" ]; then
        ((checks_passed++))
        log_debug "✅ Archivo desktop existe"
    else
        log_warning "⚠️  Archivo desktop no existe"
    fi
    
    # Verificar Ollama
    if command_exists ollama; then
        ((checks_passed++))
        log_debug "✅ Ollama instalado"
    else
        log_error "❌ Ollama no instalado"
    fi
    
    # Verificar servicio Ollama
    if systemctl is-active --quiet ollama; then
        ((checks_passed++))
        log_debug "✅ Servicio Ollama activo"
    else
        log_warning "⚠️  Servicio Ollama inactivo"
    fi
    
    # Verificar modelos de voz
    if [ -f "$MODEL_DIR/es_AR-daniela-high.onnx" ]; then
        ((checks_passed++))
        log_debug "✅ Modelo de voz existe"
    else
        log_warning "⚠️  Modelo de voz no descargado"
    fi
    
    # Verificar dependencias de Python
    if python -c "import PySide6, requests, psutil" &>/dev/null; then
        ((checks_passed++))
        log_debug "✅ Dependencias de Python instaladas"
    else
        log_error "❌ Dependencias de Python faltantes"
    fi
    
    log_success "Verificaciones completadas ($checks_passed/$checks_total OK)"
    return $((checks_total - checks_passed))
}

# Función para mostrar resumen de instalación
show_installation_summary() {
    echo ""
    echo -e "${GREEN}🎉 ¡Instalación de Arch-Chan AI Assistant completada!${NC}"
    echo ""
    echo -e "${CYAN}📋 Resumen de la instalación:${NC}"
    echo -e "  ${GREEN}✅${NC} Dependencias del sistema instaladas"
    echo -e "  ${GREEN}✅${NC} Estructura de directorios creada"
    echo -e "  ${GREEN}✅${NC} Modelos de IA configurados"
    echo -e "  ${GREEN}✅${NC} Lanzador de aplicación creado"
    echo ""
    echo -e "${BLUE}🚀 Próximos pasos:${NC}"
    echo -e "  1. ${CYAN}Asegúrate de que Ollama esté ejecutándose:${NC} systemctl status ollama"
    echo -e "  2. ${CYAN}Verifica los modelos de voz en:${NC} $MODEL_DIR"
    echo -e "  3. ${CYAN}Ejecuta la aplicación:${NC} python main.py"
    echo -e "  4. ${CYAN}O busca 'Arch-Chan' en tu menú de aplicaciones${NC}"
    echo ""
    echo -e "${MAGENTA}🔧 Comandos útiles:${NC}"
    echo -e "  ${YELLOW}Iniciar aplicación:${NC} python main.py"
    echo -e "  ${YELLOW}Actualizar:${NC} ./update_arch_chan.sh"
    echo -e "  ${YELLOW}Configurar modelos:${NC} python setup_models.py"
    echo ""
    echo -e "${GREEN}🐧 ¡Disfruta de tu asistente de IA nativo de Arch Linux!${NC}"
    echo ""
}

# Configuración
APP_NAME="Arch-Chan AI Assistant"
APP_VERSION="2.1.0"
APP_DIR="$HOME/arch-chan-project"
MODEL_DIR="$APP_DIR/models"
CONFIG_DIR="$APP_DIR/configs"
LOG_DIR="$APP_DIR/logs"

# Banner de inicio
echo -e "${MAGENTA}"
echo "    ___                  _   ____ _                 _   "
echo "   /   |  ____ _   __   / | / ___| |__   __ _ _ __ | |_ "
echo "  / /| | / __/| | / /  /  | | |   | '_ \ / _\` | '_ \| __|"
echo " / ___ |/ /   | |/ /  / /| | | |__| | | | (_| | | | | |_ "
echo "/_/  |_/_/    |___/  /_/ |_| \____|_| |_|\__,_|_| |_|\__|"
echo -e "${NC}"
echo -e "${BLUE}🐧 $APP_NAME v$APP_VERSION - Instalador${NC}"
echo -e "${CYAN}===============================================${NC}"
echo ""

# Ejecutar instalación
main() {
    log_step "Iniciando instalación de $APP_NAME v$APP_VERSION..."
    
    verify_system
    install_system_dependencies
    setup_ollama
    create_directory_structure
    download_voice_models
    create_ollama_models
    create_desktop_file
    create_update_script
    setup_permissions
    
    # Verificación final
    if final_verification; then
        show_installation_summary
    else
        log_warning "Algunas verificaciones fallaron, pero la instalación puede funcionar"
        show_installation_summary
    fi
}

# Manejar señales de interrupción
trap 'log_error "Instalación interrumpida por el usuario"; exit 1' INT TERM

# Ejecutar función principal
main "$@"
