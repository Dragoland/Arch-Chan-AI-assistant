# CHANGELOG - Arch-Chan AI Assistant

Registro de actualizaciones y cambios importantes del proyecto.

---

## Versión 2.1 (Fecha) - Arquitectura Modular y Mejoras de Empaquetado

### 🏗️ Arquitectura y Código
- **Refactorización Modular**: Separación del código en módulos especializados (core, ui, services, workers, models, utils)
- **Mejora de Mantenibilidad**: Código más limpio y fácil de extender
- **Patrón de Diseño**: Implementación de señales Qt para comunicación entre componentes

### 🚀 Nuevas Características
- **Sistema de Temas**: Múltiples temas incluidos (Arch Dark, Arch Light, Blue Matrix, Green Terminal, Purple Haze)
- **Monitoreo del Sistema**: Panel lateral con información en tiempo real del sistema
- **Gestión de Estado**: State manager centralizado para controlar el estado de la aplicación

### 🛠️ Mejoras Técnicas
- **Servicios Modulares**: Clientes para Ollama, voz, comandos y monitoreo del sistema
- **Workers Especializados**: Procesamiento en hilos para chat y voz
- **Validadores de Seguridad**: Validación robusta de comandos y entradas
- **Utilidades de Archivo**: Manejo seguro de archivos y directorios

### 📦 Empaquetado
- **Soporte AUR**: PKGBUILD para distribución en Arch User Repository
- **Soporte PIP**: setup.py para instalación via pip
- **Script de Instalación Mejorado**: install_arch_chan.sh actualizado

### 🐛 Correcciones
- **Manejo de Errores**: Mejor manejo de excepciones en todos los módulos
- **Rendimiento**: Optimización del uso de memoria y CPU
- **Estabilidad**: Corrección de condiciones de carrera en hilos

---

## Versión 1.0 (2 de Noviembre de 2025) - Optimización y Pulido Final

### 🚀 Rendimiento y Optimización
- **Gestión Inteligente de Memoria:** Limpieza automática del historial después de 20 intercambios
- **Cache de Modelos:** Modelos mantenidos en memoria durante periodos de inactividad

### 🛡️ Seguridad Mejorada
- **Sandbox de Comandos:** Entorno restringido para comandos shell (Aun por implementar)
- **Whitelist de Comandos Seguros:** Lista de comandos permitidos para operaciones comunes (Aun por implementar)
- **Auditoría de Seguridad:** Registro con marca de tiempo de cada comando ejecutado (Aun por implemenetar)

### 🎨 Experiencia de Usuario
- **Indicadores Visuales Mejorados:** Barra de progreso animada
- **Modo Oscuro/Claro:** Sistema de temas intercambiables (Aun por implementar)

---

## Versión 0.9 (25 de octubre de 2025) - Lanzamiento Estabilizado

### 🐛 Correcciones Críticas de Entorno
- **Solución de PATH de Binarios:** Función `find_dependency` para buscar binarios KDE
- **Flujo de Inicio Corregido:** Inicialización de `QApplication` al inicio de `main()`
- **Variables Globales de Ejecutables:** Rutas completas para `PIPER_EXE` y `WHISPER_EXE`

### 🛡️ Seguridad y Robustez
- **Validación de Comandos Shell:** Bloqueo de comandos destructivos
- **Manejo de Excepciones Detallado:** `SecurityError`, `CommandTimeoutError`, `DependencyError`
- **Verificación de Dependencias:** Confirmación de `ollama` activo y herramientas instaladas
- **Manejo Robusto de Hilos:** Desconexión explícita de señales
- **Gestión de Configuración Persistente:** Uso de `config.ini`
- **Sistema de Logging Avanzado:** Registro detallado en carpeta `logs/`

### 🎨 Mejoras en la Interfaz
- **Animación de Estado:** Icono `⏳` durante procesamiento
- **Logs de Herramientas Mejorados:** Salida en bloques de código
- **Tooltips:** Información contextual en controles principales

---

## Versión 0.8.5 - Pre-lanzamiento Estilizado y Ligero

### 🚀 Rendimiento
- **Modelo Lite:** `arch-chan-lite` basado en `gemma:2b`
- **Personalidad Optimizada:** `Arch-Chan-Lite.Modelfile` con prompt `SYSTEM` optimizado
- **Selector de Modelos:** `QComboBox` para cambiar modelo en tiempo real

### 🎨 Diseño y Usabilidad
- **Diseño de Conversación Moderna:** Burbujas de chat con CSS
- **Estilos Detallados:** Efectos `hover` y `focus` en botones y campos

---

## Versión 0.8 - Control y Estabilidad

### ⚙️ Control de Procesos
- **Botón de Stop:** Implementación de "⏹️ Detener" y función `stop_all`
- **Gestión de Procesos:** Lógica mejorada para `piper-tts`, `aplay`, comandos externos

### 🛡️ Permisos
- **Manejo de Sudo:** Detección de comandos `sudo` en JSON de IA
- **Confirmación con GUI:** Integración de `kdesu` y `QMessageBox`
- **Notificaciones de Sistema:** Uso de `kdialog` para notificaciones KDE

---

## Versión 0.7 - Arquitectura de Herramientas Completa

### 🧠 Lógica de IA
- **Tool-Use Completo:** Ejecución de herramienta `search` con `ddgr`
- **Resumen de Búsqueda:** Salida de `ddgr` capturada y resumida por Ollama
- **Memoria (Historial de Chat):** Historial completo enviado a Ollama para contexto
- **Creacion de Arch Chan:** Se creo el modelo `arch-chan` basado en `llama3.2:3b` 

---

## Versión 0.6 - Procesamiento y Threading

### ⚙️ Core Funcionalidad
- **WorkerThread:** Lógica pesada aislada en `QThread`
- **Grabación de Voz:** Uso de `rec` (Sox) con detección de silencio
- **Transmisión de Señales:** Configuración de `Signals` y `Slots` PySide6

---

## Versión 0.5 - Base de Arquitectura y Ollama

### 💻 Backend
- **API Ollama:** Comunicación con API de Ollama
- **Lógica de Herramienta Shell:** Ejecución de comandos con `subprocess.Popen`
- **Respuesta Estructurada:** Capacidad de responder con JSON para Tool-Use

---

## Versión 0.4 - Integración de Voz y Texto

### 🗣️ Sistema de Voz
- **Configuración de Piper TTS:** Texto-a-voz con `piper-tts`
- **Configuración de Whisper CLI:** Voz-a-texto con `whisper-cli`
- **Pipeline de Audio:** Flujo grabación → transcripción → síntesis

---

## Versión 0.3 - Arquitectura GUI Base

### 🖼️ Interfaz Gráfica
- **Ventana Principal PySide6:** Estructura básica de GUI
- **Controles Esenciales:** Botones, área de texto, etiquetas de estado
- **Manejo de Eventos Básico:** Señales y slots iniciales

---

## Versión 0.2 - Configuración de Entorno

### 🏗️ Infraestructura
- **Estructura de Carpetas:** `src/`, `models/`, `config/`
- **Gestión de Dependencias:** Script de instalación y verificación
- **Configuración Inicial:** Variables de entorno y paths

---

## Versión 0.1 - Prototipo Conceptual

### 💡 Concepto Inicial
- **Ideación del Proyecto:** Visión de Arch-Chan como asistente de voz local
- **Selección de Tecnologías:** PySide6, Ollama, Whisper, Piper
- **Prototipo de Prueba:** Primer script funcional de concepto

---

*Este changelog se mantiene actualizado con cada commit significativo al proyecto.*