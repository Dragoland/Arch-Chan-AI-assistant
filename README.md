# Arch-Chan AI Assistant

![Version](https://img.shields.io/badge/version-2.1-blue)
![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=flat&logo=arch-linux&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-0%20-00B588?style=flat)
![License](https://img.shields.io/badge/license-MIT-green)

Una asistente de IA nativa para Arch Linux con interfaz gráfica integrada, desarrollada en Python y PySide6. Utiliza Ollama para modelos de lenguaje local, Whisper para transcripción de voz y Piper para síntesis de voz.

# ACLARACION!!!

El programa todavia se encuentra en fase de desarrollo, todavia no existe en el repo AUR ni tampoco funciona al 100%, no existe ninguna release, toda copia existente que haya del software no es oficial, guiese por la informacion oficial.

## 🚀 Características Principales

### 🎨 Interfaz Nativa de Arch Linux
- Diseño visual auténtico con colores oficiales (#1793D1)
- Panel lateral con información del sistema en tiempo real
- Burbujas de chat modernas con estilo nativo
- Integración perfecta con el ecosistema Arch

### 🧠 Inteligencia Artificial Local
- **Modelos Optimizados**: `arch-chan` (llama3.2:3b) y `arch-chan-lite` (gemma:2b)
- **Detección Inteligente**: Analiza automáticamente cuándo usar comandos, búsquedas o conversación
- **Memoria Contextual**: Mantiene historial de conversación para respuestas coherentes
- **Tool-Use Avanzado**: Ejecución segura de comandos shell y búsquedas web

### 🗣️ Sistema de Voz Completo
- **Voz a Texto**: Transcripción en tiempo real con Whisper
- **Texto a Voz**: Síntesis de voz natural con Piper (voz en español)
- **Grabación Inteligente**: Detección automática de silencio
- **Audio en Tiempo Real**: Reproducción inmediata de respuestas

### ⚡ Funcionalidades Avanzadas
- **Ejecución Segura de Comandos**: Validación y confirmación para operaciones riesgosas
- **Búsquedas Web**: Integración con ddgr para información actualizada
- **Gestión de Privilegios**: Confirmación gráfica para comandos sudo
- **Notificaciones del Sistema**: Integración con KDE mediante kdialog

## 📦 Instalación

### Método 1: AUR (Recomendado para Arch Linux)

```bash
# Usando yay (o tu ayudante AUR favorito)
yay -S arch-chan-ai-assistant
```

### Método 2: PIP

```bash

# Instalar desde PyPI
pip install arch-chan-ai-assistant

# Ejecutar
arch-chan
```

### Método 3: Instalación Semi-automatica

```bash
# Clonar el repositorio
git clone https://github.com/Dragoland/Arch-Chan-AI-assistant.git
cd Arch-Chan-AI-assistant

# Ejecutar instalador nativo
chmod +x install_arch_chan.sh
./install_arch_chan.sh
```

### Método 4: Instalacion Manual
```bash

# Clonar el repositorio
git clone https://github.com/Dragoland/Arch-Chan-AI-assistant.git
cd Arch-Chan-AI-assistant

# 1. Instalar dependencias del sistema
sudo pacman -S --needed python-pip python-pyside6 whisper.cpp piper-tts sox ollama ddgr kdialog

# 2. Instalar dependencias de Python
pip install requests

# 3. Configurar Ollama
sudo systemctl enable ollama
sudo systemctl start ollama

# 4. Crear modelos de IA
ollama create arch-chan -f Arch-Chan.Modelfile
ollama create arch-chan-lite -f Arch-Chan-Lite.Modelfile

# 5. Crear directorios de la aplicación
mkdir -p ~/arch-chan-project/{models,temp,logs}

# 6. Ejecutar la aplicación
python main.py
```


## 📋 Requisitos del Sistema

### Sistema Operativo
- **Arch Linux** (recomendado) o distribución compatible
- **Escritorio KDE Plasma** (óptimo) o otro entorno de escritorio

### Dependencias Principales

```bash
# Desde repositorios de Arch Linux
sudo pacman -S --needed \
    python-pip \
    whisper.cpp \
    piper-tts \
    sox \
    ollama \
    ddgr \
    kdialog \
    noto-fonts \
    ttf-hack
 ```

## Modelos de IA Requeridos
- **Ollama**: Servicio ejecutándose en `localhost:11434`
- **Modelos Creados**: `arch-chan` y `arch-chan-lite`

## Hardware Recomendado
- **RAM**: 8GB mínimo, 16GB recomendado
- **Almacenamiento**: 2GB para modelos base
- **Micrófono**: Para funcionalidad de voz
- **Altavoces**: Para respuestas de audio

## 🎯 Uso

### Inicio Rápido
1. **Ejecutar la aplicación**: `arch-chan` o buscar "Arch-Chan" en el menú de aplicaciones
2. **Seleccionar modelo**: Elegir entre `arch-chan` (completo) o `arch-chan-lite` (ligero)
3. **Interactuar**: Usar voz (botón 🎤) o texto (campo de entrada)

### Ejemplos de Interacción

#### 💬 Conversación Normal
1. **Usuario**: ¿Qué es Arch Linux?
2. **Arch-Chan**: Arch Linux es una distribución Linux rolling release...

#### ⚡ Comandos Shell

1. **Usuario**: Muestra qué procesos consumen más CPU
2. **Arch-Chan**: 
```json
{"tool": "shell", 
"command": "ps aux --sort=-%cpu | head -10", 
"explanation": "Voy a mostrar los 10 procesos que más CPU consumen"}
```

#### 🔍 Búsquedas Web

1. **Usuario**: Busca noticias recientes sobre Arch Linux
2. **Arch-Chan**: 
```json
{"tool": "search", 
"query": "noticias Arch Linux actualizaciones recientes"}
```

### Controles Principales
- **🎤 Voz**: Grabar audio para transcripción
- **📤 Enviar**: Enviar mensaje de texto
- **⏹ Detener**: Cancelar operación en curso
- **🗑️ Limpiar Chat**: Reiniciar la conversación
- **⚙️ Configuración**: Ajustes de la aplicación

## 🏗️ Estructura del Proyecto

```
arch-chan-project/
├── main.py                      # Punto de entrada
├── core/                        # Lógica principal
│   ├── application.py           # Clase principal de la aplicación
│   ├── config_manager.py        # Gestión de configuración
│   └── state_manager.py         # Gestión de estados
├── ui/                          # Componentes de interfaz
│   ├── main_window.py           # Ventana principal
│   ├── components/              # Componentes UI reutilizables
│   ├── dialogs/                 # Diálogos especializados
│   └── themes/                  # Sistema de temas
├── services/                    # Servicios externos
│   ├── ollama_client.py         # Cliente de Ollama
│   ├── speech_service.py        # Servicio de voz
│   └── command_executor.py      # Ejecutor de comandos
├── workers/                     # Hilos de trabajo
│   ├── base_worker.py           # Worker base
│   ├── chat_worker.py           # Worker de chat
│   └── voice_worker.py          # Worker de voz
├── models/                      # Modelos de datos
│   ├── chat_models.py           # Modelos de chat
│   ├── config_models.py         # Modelos de configuración
│   └── system_models.py         # Modelos del sistema
└── utils/                       # Utilidades
    ├── logger.py                # Sistema de logging
    ├── validators.py            # Validadores de seguridad
    └── file_utils.py            # Utilidades de archivos
```

## 🔧 Configuración

### Archivo de Configuración
La aplicación crea automáticamente `~/arch-chan-project/config.ini`:

```ini
[General]
model = arch-chan
auto_cleanup = true
max_history = 20
notifications = true
voice_enabled = true

[Paths]
project_path = ~/arch-chan-project
models_path = ~/arch-chan-project/models
temp_path = ~/arch-chan-project/temp

[Audio]
sample_rate = 22050
silence_threshold = 5%
voice_volume = 80

[UI]
theme = arch-dark
font_size = 11
sidebar_visible = true
```
### Personalización
- **Modelos**: Cambiar entre `arch-chan` y `arch-chan-lite` en tiempo real
- **Historial**: Ajustar el número máximo de mensajes conservados
- **Audio**: Configurar sensibilidad de grabación y volumen de voz
- **Interfaz**: Modificar tema y tamaño de fuente

## 🐛 Solución de Problemas

### Problemas Comunes

#### Ollama No Responde
```bash
# Verificar servicio
sudo systemctl status ollama

# Reiniciar servicio
sudo systemctl restart ollama

# Probar conexión
curl http://localhost:11434/api/tags
```

#### Error de Dependencias
```bash
# Reinstalar dependencias faltantes
sudo pacman -S whisper.cpp piper-tts sox

# Verificar instalación
which whisper.cpp piper-tts rec
```

#### Problemas de Audio
```bash
# Verificar dispositivos de audio
arecord -l
aplay -l

# Probar grabación
rec test.wav
# Reproducir prueba
aplay test.wav
```

### Registros y Depuración
- Los logs se guardan en `~/arch-chan-project/logs/`
- Nivel de detalle configurable en el código
- Incluye timestamps y información de errores

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Areas donde puedes ayudar:

### Mejoras Planeadas
- [ ] Soporte para más modelos de lenguaje
- [ ] Sistema de plugins modular
- [ ] Integración con AUR
- [ ] Temas visuales adicionales
- [ ] Soporte para más idiomas

### Cómo Contribuir
1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte y Comunidad

Únete a nuestra comunidad de Telegram para soporte y discusiones:

[**t.me/diario_del_informatico**](https://t.me/diario_del_informatico)

---

<div align="center">

**¡Disfruta de tu asistente de IA nativo de Arch Linux! 🐧**

*Desarrollado con ❤️ para la comunidad Arch Linux*

[Reportar Bug](issues/) · [Solicitar Feature](issues/)

</div>
