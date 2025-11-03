#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import requests
import json
import re
import time
import psutil
from datetime import datetime
from PySide6.QtCore import (QThread, Signal, QMutex, QWaitCondition, Slot, QTimer)

from config import (
    WHISPER_MODEL,
    logger,
    PIPER_EXE,
    WHISPER_EXE,
    TTS_MODEL_ONNX,
    OLLAMA_API_URL,
    KDESU_AVAILABLE,
    AUDIO_INPUT_FILE,
    TEMP_PATH,
    ConfigManager,
    SecurityError,
    CommandTimeoutError
)

class WorkerThread(QThread):
    """Hilo principal mejorado que maneja toda la lógica de procesamiento"""

    # Señales
    update_status = Signal(str)
    add_conversation_log = Signal(str, str)
    add_tool_log = Signal(str, str)
    flow_finished = Signal(str, str)
    sudo_confirmation_required = Signal(str)
    progress_update = Signal(int)
    error_occurred = Signal(str)
    performance_metrics = Signal(dict)
    audio_level = Signal(int)  # Nuevo: para mostrar nivel de audio en tiempo real

    def __init__(self, chat_history: list, text_prompt=None, model_name='arch-chan', config=None):
        super().__init__()
        self.text_prompt = text_prompt
        self.model_name = model_name
        self.chat_history = chat_history.copy()
        self.config = config or ConfigManager().load_config()

        # Synchronization
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.sudo_approved = False
        self._is_stopped = False

        # Process handles
        self.current_process = None
        self.piper_process = None
        self.aplay_process = None
        self.rec_process = None

        # Audio configuration
        self.voice_sample_rate = self.config.get('Audio', 'sample_rate', fallback='22050')
        
        # Nuevas variables para mejoras
        self.retry_attempts = self.config.getint('Advanced', 'retry_attempts', fallback=3)
        self.timeout_duration = self.config.getint('Advanced', 'timeout_duration', fallback=120)
        self.start_time = None
        self.metrics = {
            'transcription_time': 0,
            'processing_time': 0,
            'tts_time': 0,
            'total_time': 0,
            'audio_duration': 0
        }
        
        # Cache para respuestas
        self.response_cache = {}
        self.cache_enabled = self.config.getboolean('Advanced', 'cache_responses', fallback=True)
        
        # Timer para monitoreo de audio
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self.check_audio_level)

        logger.info(f"WorkerThread v2.1 inicializado con modelo: {model_name}")

    def analyze_intent(self, user_input):
        """Analiza la intención del usuario con detección mejorada"""
        input_lower = user_input.lower().strip()
        
        # Patrones que indican necesidad de SHELL (expandido)
        shell_patterns = [
            r'ejecuta', r'corre', r'run', r'ejecutar', r'correr',
            r'instala', r'install', r'instalar', r'remueve', r'remove', r'desinstalar',
            r'muestra', r'muéstrame', r'show me', r'display', r'listar', r'lista',
            r'qué procesos', r'qué espacio', r'cuánto espacio', r'uso de memoria',
            r'reinicia', r'restart', r'reiniciar', r'detén', r'stop',
            r'crea', r'create', r'crear', r'make', r'nuevo',
            r'elimina', r'delete', r'eliminar', r'remove', r'borrar',
            r'cambia', r'change', r'cambiar', r'modify', r'edita',
            r'configura', r'configure', r'configurar', r'setup', r'ajusta',
            r'actualiza', r'update', r'actualizar', r'upgrade',
            r'copia', r'copy', r'mueve', r'move', r'renombra',
            r'permisos', r'permissions', r'chmod', r'chown',
            r'servicio', r'service', r'systemctl', r'daemon',
            r'paquete', r'package', r'pacman', r'yay', r'paru',
            r'proceso', r'process', r'ps', r'kill', r'matar',
            r'disco', r'disk', r'espacio', r'df', r'du',
            r'red', r'network', r'ping', r'wget', r'curl',
            r'usuario', r'user', r'grupo', r'group'
        ]
        
        # Patrones que indican necesidad de SEARCH (expandido)
        search_patterns = [
            r'noticias', r'news', r'últimas', r'recientes',
            r'busca', r'search', r'búscame', r'find', r'buscar',
            r'qué hay de nuevo', r'novedades', r'tendencias',
            r'información actual', r'actualidad', r'hoy',
            r'última versión', r'latest version', r'cambios',
            r'tutoriales recientes', r'recent tutorials', r'guías',
            r'cómo se hace', r'how to', r'tutorial', r'guía',
            r'documentación', r'documentation', r'manual',
            r'foro', r'forum', r'comunidad', r'ayuda',
            r'error', r'problema', r'solución', r'fix'
        ]
        
        # Patrones de emergencia/comandos peligrosos (expandido)
        danger_patterns = [
            r'rm -rf', r'formatear', r'format', r'fdisk', r'parted',
            r'dd if=', r'mkfs', r'wipefs', r'sgdisk',
            r'chmod 777', r'chown root', r'passwd', r'visudo',
            r'wget', r'curl | sh', r'bash <(', r'wget -O-',
            r'systemctl poweroff', r'systemctl reboot', r'shutdown',
            r'halt', r'poweroff', r'reboot', r'init',
            r'> /dev/sd', r'> /dev/nvme', r'dd of=',
            r'mount /dev/sd', r'umount /dev/sd',
            r'cryptsetup', r'lvm', r'pvcreate',
            r'eliminar todo', r'delete all', r'formatear todo',
            r'reiniciar sistema', r'shutdown now', r'apagar'
        ]
        
        # Verificar patrones peligrosos primero
        if self.config.getboolean('Advanced', 'block_dangerous', fallback=True):
            for pattern in danger_patterns:
                if re.search(pattern, input_lower):
                    logger.warning(f"Intención peligrosa detectada: {pattern}")
                    return "danger"
        
        # Verificar shell patterns
        for pattern in shell_patterns:
            if re.search(pattern, input_lower):
                logger.info(f"Intención detectada: SHELL (patrón: {pattern})")
                return "shell"
        
        # Verificar search patterns
        for pattern in search_patterns:
            if re.search(pattern, input_lower):
                logger.info(f"Intención detectada: SEARCH (patrón: {pattern})")
                return "search"
        
        # Si no coincide con ningún patrón de acción, es conversación normal
        logger.info("Intención detectada: CONVERSACIÓN NORMAL")
        return "conversation"

    def validate_command(self, command_str):
        """Valida comandos shell con seguridad mejorada"""
        dangerous_patterns = [
            'rm -rf', 'dd if=', 'mkfs', ':(){:|:&};:', 'fork bomb',
            '> /dev/sd', 'mkfs', 'fdisk', 'parted', 'sfdisk',
            'chmod 777', 'chown root', 'passwd', 'visudo',
            'wget', 'curl | sh', 'bash <(', 'wget -O-',
            'systemctl poweroff', 'systemctl reboot', 'shutdown',
            'halt', 'poweroff', 'reboot', 'init 0', 'init 6',
            'cryptsetup', 'lvcreate', 'pvcreate', 'vgcreate',
            'wipefs', 'sgdisk', 'partprobe'
        ]

        sensitive_dirs = [
            '/boot', '/etc', '/root', '/sys', '/proc',
            '/dev', '/mnt', '/media', '/usr', '/bin',
            '/sbin', '/lib', '/lib64'
        ]

        dangerous_sudo_commands = [
            'visudo', 'passwd', 'useradd', 'userdel',
            'groupadd', 'groupdel', 'chsh', 'chfn'
        ]

        command_lower = command_str.lower()
        
        # Verificar patrones peligrosos
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                raise SecurityError(f"Comando peligroso detectado y bloqueado: {pattern}")

        # Verificar acceso a directorios sensibles
        for directory in sensitive_dirs:
            if directory in command_str and any(cmd in command_lower for cmd in [' > ', ' >> ', ' | ', '&>']):
                raise SecurityError(f"Redirección a directorio sensible bloqueada: {directory}")

        # Verificar comandos sudo peligrosos
        if 'sudo' in command_lower:
            for dangerous_cmd in dangerous_sudo_commands:
                if dangerous_cmd in command_lower:
                    raise SecurityError(f"Comando sudo peligroso bloqueado: {dangerous_cmd}")

        # Verificar redirección a dispositivos de bloque
        if re.search(r'>\s*/dev/(sd|hd|nvme|loop)', command_str):
            raise SecurityError("Redirección a dispositivos de bloqueo bloqueada")

        # Verificar intentos de modificación de sistema crítico
        critical_paths = ['/etc/passwd', '/etc/shadow', '/etc/sudoers']
        for critical_path in critical_paths:
            if critical_path in command_str and any(cmd in command_lower for cmd in [' > ', ' >> ', 'echo']):
                raise SecurityError(f"Modificación de archivo crítico bloqueada: {critical_path}")

        logger.info(f"Comando validado: {command_str}")

    def record_audio(self):
        """Graba audio con monitoreo en tiempo real"""
        if self._is_stopped:
            return False

        try:
            silence_threshold = self.config.get('Audio', 'silence_threshold', fallback='5%')
            rec_cmd = [
                'rec', AUDIO_INPUT_FILE, 'rate', '16k', 
                'silence', '1', '0.1', silence_threshold, 
                '1', '1.0', silence_threshold,
                'norm', '−3'  # Normalizar audio
            ]
            
            # Configurar calidad de audio
            audio_quality = self.config.get('Audio', 'audio_quality', fallback='high')
            if audio_quality == 'high':
                rec_cmd.extend(['-b', '16', '-c', '1'])
            elif audio_quality == 'medium':
                rec_cmd.extend(['-b', '8', '-c', '1'])
            else:  # low
                rec_cmd.extend(['-b', '8', '-c', '1', 'rate', '8k'])

            logger.info(f"Iniciando grabación con comando: {' '.join(rec_cmd)}")
            
            self.rec_process = subprocess.Popen(
                rec_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )

            # Iniciar monitoreo de nivel de audio
            self.audio_timer.start(100)  # Actualizar cada 100ms

            # Esperar a que termine la grabación
            self.rec_process.wait(timeout=30)  # Timeout de 30 segundos
            self.audio_timer.stop()
            
            return True

        except subprocess.TimeoutExpired:
            logger.warning("Grabación excedió el tiempo límite")
            if self.rec_process:
                self.rec_process.terminate()
            return False
        except Exception as e:
            logger.error(f"Error en grabación de audio: {e}")
            return False
        finally:
            self.audio_timer.stop()

    def check_audio_level(self):
        """Verifica el nivel de audio en tiempo real (simulado)"""
        # En una implementación real, esto leería del proceso de grabación
        # Por ahora, simulamos un nivel aleatorio para demostración
        import random
        level = random.randint(0, 100)
        self.audio_level.emit(level)

    def speak_text(self, text):
        """Sintetiza y reproduce texto usando Piper TTS - Versión mejorada"""
        if self._is_stopped or not text.strip():
            return

        self.update_status.emit("🔊 Reproduciendo audio...")
        logger.info(f"Reproduciendo texto: {text[:50]}...")

        try:
            # Limitar longitud del texto para TTS
            max_length = self.config.getint('Advanced', 'max_response_length', fallback=1000)
            if len(text) > max_length:
                text = text[:max_length] + "..."
                logger.warning(f"Texto truncado para TTS a {max_length} caracteres")

            tts_start = time.time()

            # Configurar calidad de audio según configuración
            audio_quality = self.config.get('Audio', 'audio_quality', fallback='high')
            quality_args = []
            if audio_quality == 'high':
                quality_args = ['--quality', 'high']
            elif audio_quality == 'medium':
                quality_args = ['--quality', 'medium']

            # Configurar volumen
            volume = self.config.getint('Audio', 'voice_volume', fallback=80)
            volume_factor = volume / 100.0

            self.aplay_process = subprocess.Popen(
                ['aplay', '-r', self.voice_sample_rate, '-f', 'S16_LE', '-t', 'raw', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            piper_command = [PIPER_EXE, '--model', TTS_MODEL_ONNX, '--output-file', '-'] + quality_args
            
            # Aplicar reducción de ruido si está habilitada
            if self.config.getboolean('Audio', 'noise_reduction', fallback=True):
                piper_command.extend(['--noise-scale', '0.667', '--noise-w', '0.8'])

            self.piper_process = subprocess.Popen(
                piper_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,  # Cambiado para poder procesar la salida
                stderr=subprocess.DEVNULL
            )

            # Enviar texto a Piper
            self.piper_process.stdin.write(text.encode('utf-8'))
            self.piper_process.stdin.close()

            # Leer salida de Piper y enviar a aplay
            try:
                while True:
                    if self._is_stopped:
                        break
                    data = self.piper_process.stdout.read(1024)
                    if not data:
                        break
                    self.aplay_process.stdin.write(data)
            except BrokenPipeError:
                pass  # Proceso terminado

            self.piper_process.wait(timeout=30)
            self.aplay_process.stdin.close()
            self.aplay_process.wait(timeout=10)

            self.metrics['tts_time'] = time.time() - tts_start

        except subprocess.TimeoutExpired:
            logger.warning("TTS timeout, limpiando procesos...")
            self.cleanup_processes()
        except Exception as e:
            if not self._is_stopped:
                error_msg = f"Error en síntesis de voz: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
        finally:
            self.cleanup_processes()

    def cleanup_processes(self):
        """Limpia todos los procesos en ejecución de forma robusta"""
        processes = [
            (self.piper_process, "Piper TTS"),
            (self.aplay_process, "aplay"),
            (self.rec_process, "rec"),
            (self.current_process, "Comando actual")
        ]

        for process, name in processes:
            if process and process.poll() is None:
                try:
                    logger.info(f"Terminando proceso: {name}")
                    process.terminate()
                    process.wait(timeout=2)
                except (subprocess.TimeoutExpired, Exception) as e:
                    try:
                        logger.warning(f"Forzando terminación de: {name}")
                        process.kill()
                        process.wait(timeout=1)
                    except Exception:
                        pass
                finally:
                    if process == self.piper_process:
                        self.piper_process = None
                    elif process == self.aplay_process:
                        self.aplay_process = None
                    elif process == self.rec_process:
                        self.rec_process = None
                    elif process == self.current_process:
                        self.current_process = None

    def call_ollama_chat(self, messages: list, is_tool_call=False):
        """Realiza una llamada a la API de Ollama con manejo mejorado de errores"""
        if self._is_stopped:
            return None

        # Verificar cache si está habilitado
        if self.cache_enabled and not is_tool_call:
            cache_key = str(messages[-1] if messages else "")
            if cache_key in self.response_cache:
                logger.info("Respuesta obtenida desde cache")
                return self.response_cache[cache_key]

        api_payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_k": 40,
                "top_p": 0.9,
                "num_ctx": 4096
            }
        }

        if is_tool_call:
            api_payload["format"] = "json"

        try:
            logger.info(f"Llamando a Ollama con {len(messages)} mensajes")
            self.update_status.emit("🤖 Consultando modelo IA...")
            
            response = requests.post(
                OLLAMA_API_URL, 
                json=api_payload, 
                timeout=self.timeout_duration,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            result = response.json()['message']
            
            # Guardar en cache si está habilitado
            if self.cache_enabled and not is_tool_call:
                cache_key = str(messages[-1] if messages else "")
                self.response_cache[cache_key] = result
                
            return result
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout llamando a Ollama después de {self.timeout_duration} segundos"
            logger.error(error_msg)
            return {'role': 'assistant', 'content': 'Error: Timeout en la consulta al modelo.'}
        except requests.exceptions.ConnectionError:
            error_msg = "No se pudo conectar con Ollama. Verifica que el servicio esté ejecutándose."
            logger.error(error_msg)
            return {'role': 'assistant', 'content': 'Error: No se puede conectar con Ollama.'}
        except requests.exceptions.RequestException as e:
            error_msg = f"Error en la llamada a Ollama: {e}"
            logger.error(error_msg)
            return {'role': 'assistant', 'content': f'Error de API: {str(e)}'}

    @Slot(bool)
    def on_sudo_response(self, approved: bool):
        """Maneja la respuesta de confirmación de sudo"""
        self.mutex.lock()
        self.sudo_approved = approved
        self.wait_condition.wakeAll()
        self.mutex.unlock()
        logger.info(f"Respuesta sudo: {'aprobado' if approved else 'denegado'}")

    def stop_all(self):
        """Detiene todos los procesos en ejecución de forma completa"""
        self._is_stopped = True
        logger.info("Deteniendo todos los procesos del worker...")
        self.cleanup_processes()
        self.audio_timer.stop()
        self.on_sudo_response(False)

    def run_command(self, command_list, shell=False, timeout=None):
        """Ejecuta un comando shell de forma segura con mejoras"""
        if timeout is None:
            timeout = self.timeout_duration

        command_str = ' '.join(command_list) if isinstance(command_list, list) else command_list

        self.validate_command(command_str)
        logger.info(f"Ejecutando comando: {command_str}")

        self.current_process = subprocess.Popen(
            command_list,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            encoding='utf-8',
            errors='ignore'
        )

        try:
            stdout, stderr = self.current_process.communicate(timeout=timeout)
            return_code = self.current_process.returncode
        except subprocess.TimeoutExpired:
            self.current_process.kill()
            stdout, stderr = self.current_process.communicate()
            raise CommandTimeoutError(f"El comando excedió el tiempo límite de {timeout} segundos")
        finally:
            self.current_process = None

        if self._is_stopped:
            raise Exception("Proceso detenido por el usuario")

        logger.info(f"Comando ejecutado - Código: {return_code}, Salida: {len(stdout)} chars, Errores: {len(stderr)} chars")
        
        return stdout, stderr, return_code

    def fallback_to_normal_response(self, content):
        """Fallback cuando no se puede procesar como herramienta"""
        logger.info("Usando fallback a respuesta normal")
        return content

    def process_tool_call(self, tool_data, current_messages, ai_response_msg):
        """Procesa una llamada a herramienta con manejo de errores robusto"""
        
        # Limpieza y validación robusta del JSON
        if not isinstance(tool_data, dict):
            logger.warning(f"tool_data no es un diccionario: {type(tool_data)}")
            return self.fallback_to_normal_response(ai_response_msg.get('content', ''))

        # Limpiar y normalizar el tipo de herramienta
        tool_type = str(tool_data.get("tool", "")).strip().lower()
        
        # Validar tool_type permitido
        allowed_tools = ['shell', 'search']
        if tool_type not in allowed_tools:
            logger.warning(f"Tipo de herramienta no permitida: '{tool_type}'")
            return self.fallback_to_normal_response(ai_response_msg.get('content', ''))
        
        # Validar campos requeridos según el tipo
        if tool_type == "shell":
            if "command" not in tool_data:
                logger.warning("Herramienta shell sin campo 'command'")
                return self.fallback_to_normal_response(ai_response_msg.get('content', ''))
            # Validar que el comando no esté vacío
            if not tool_data["command"].strip():
                logger.warning("Herramienta shell con comando vacío")
                return self.fallback_to_normal_response(ai_response_msg.get('content', ''))
        
        if tool_type == "search":
            if "query" not in tool_data:
                logger.warning("Herramienta search sin campo 'query'")  
                return self.fallback_to_normal_response(ai_response_msg.get('content', ''))
            # Validar que la consulta no esté vacía
            if not tool_data["query"].strip():
                logger.warning("Herramienta search con query vacío")
                return self.fallback_to_normal_response(ai_response_msg.get('content', ''))
        
        logger.info(f"Procesando herramienta válida: {tool_type}")
        
        # Ejecutar la herramienta correspondiente
        if tool_type == "shell":
            return self.process_shell_tool(tool_data, current_messages, ai_response_msg)
        elif tool_type == "search":
            return self.process_search_tool(tool_data, current_messages, ai_response_msg)

    def process_shell_tool(self, tool_data, current_messages, ai_response_msg):
        """Procesa una herramienta de shell con mejoras"""
        command_str = tool_data.get("command", "")
        explanation = tool_data.get("explanation", "Voy a ejecutar un comando.")

        # Verificar si el comando requiere sudo pero kdesu no está disponible
        if "sudo" in command_str.lower() and KDESU_AVAILABLE is None:
            error_msg = "No puedo ejecutar comandos con sudo porque no hay herramienta gráfica de elevación de privilegios disponible."
            logger.error(error_msg)
            self.add_conversation_log.emit("Arch-Chan", error_msg)
            self.speak_text(error_msg)
            return error_msg

        self.add_conversation_log.emit("Arch-Chan", explanation)
        self.speak_text(explanation)

        if self._is_stopped:
            return None

        # Manejar comandos sudo
        sudo_used = False
        if "sudo" in command_str.lower() and self.config.getboolean('Advanced', 'sudo_confirm', fallback=True):
            self.update_status.emit("⚠️ ¡Requiere 'sudo'!")
            self.mutex.lock()
            self.sudo_confirmation_required.emit(command_str)
            self.wait_condition.wait(self.mutex)
            self.mutex.unlock()

            if not self.sudo_approved:
                self.update_status.emit("❌ 'sudo' denegado.")
                return "¡Entendido! No ejecutaré el comando 'sudo'."

            # Reemplazar 'sudo ' con la herramienta disponible
            if KDESU_AVAILABLE == 'pkexec':
                command_str = command_str.replace("sudo ", "pkexec ", 1)
            else:
                command_str = command_str.replace("sudo ", f"{KDESU_AVAILABLE} -c ", 1)

            self.update_status.emit(f"✅ 'sudo' aprobado. Usando '{KDESU_AVAILABLE}'.")
            sudo_used = True

        # Ejecutar comando
        self.update_status.emit(f"⚡ Ejecutando: {command_str}")
        try:
            stdout, stderr, return_code = self.run_command(command_str, shell=True)
            
            # Formatear salida
            command_output = f"Código de salida: {return_code}\n\n"
            command_output += f"Salida:\n{stdout}\n"
            if stderr.strip():
                command_output += f"Errores:\n{stderr}\n"
                
            if sudo_used:
                command_output += f"\n[Comando ejecutado con: {KDESU_AVAILABLE}]"

            self.add_tool_log.emit(command_str, command_output)

            if self._is_stopped:
                return None

            # Resumir resultados
            self.update_status.emit("🧠 Resumiendo resultado...")
            summary_messages = (
                current_messages + [ai_response_msg] +
                [{'role': 'user', 'content': f"El comando se ejecutó con código de salida {return_code}. La salida fue:\n{stdout}\n\nErrores:\n{stderr}\n\nPor favor, resume esta información para el usuario de forma amigable y concisa."}]
            )

            final_summary_msg = self.call_ollama_chat(summary_messages, is_tool_call=False)
            return final_summary_msg.get('content', 'No pude procesar el resultado.')

        except CommandTimeoutError as e:
            error_msg = f"El comando tardó demasiado tiempo: {str(e)}"
            logger.error(error_msg)
            return f"El comando excedió el tiempo límite y fue cancelado: {str(e)}"
        except Exception as e:
            error_msg = f"Error ejecutando comando: {str(e)}"
            logger.error(error_msg)
            return f"Error ejecutando el comando: {str(e)}"

    def process_search_tool(self, tool_data, current_messages, ai_response_msg):
        """Procesa una herramienta de búsqueda con mejoras"""
        query = tool_data.get("query", "")
        explanation = f"¡Buena pregunta! Voy a buscar en internet sobre '{query}'."

        self.add_conversation_log.emit("Arch-Chan", explanation)
        self.speak_text(explanation)

        if self._is_stopped:
            return None

        # Realizar búsqueda
        self.update_status.emit(f"🌎 Buscando: {query}")
        try:
            search_cmd = ['ddgr', '--json', '-n', '5', '--unsafe', query]
            stdout, stderr, return_code = self.run_command(search_cmd, timeout=30)

            # Procesar resultados
            try:
                search_results = json.loads(stdout)
                snippets = []
                for i, result in enumerate(search_results[:3], 1):
                    title = result.get('title', 'Sin título')
                    abstract = result.get('abstract', 'Sin descripción')
                    url = result.get('url', 'Sin URL')
                    snippets.append(f"{i}. {title}\n   {abstract}\n   {url}")
                
                results_context = "\n\n".join(snippets) if snippets else "No se encontraron resultados relevantes."
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error procesando resultados de búsqueda: {e}")
                results_context = f"No pude procesar los resultados de búsqueda. Error: {e}"

            self.add_tool_log.emit(f"ddgr --json -n 5 \"{query}\"", results_context)

            if self._is_stopped:
                return None

            # Resumir búsqueda
            self.update_status.emit("🧠 Resumiendo búsqueda...")
            summary_messages = (
                current_messages + [ai_response_msg] +
                [{'role': 'user', 'content': f"Busqué '{query}'. Los resultados son:\n{results_context}\n\nPor favor, responde la pregunta original del usuario usando esta información. Sé conciso y útil."}]
            )

            final_summary_msg = self.call_ollama_chat(summary_messages, is_tool_call=False)
            return final_summary_msg.get('content', 'No pude procesar la búsqueda.')

        except CommandTimeoutError:
            error_msg = "La búsqueda tardó demasiado tiempo."
            logger.error(error_msg)
            return "La búsqueda excedió el tiempo límite. Por favor, intenta con términos más específicos."
        except Exception as e:
            error_msg = f"Error en búsqueda: {str(e)}"
            logger.error(error_msg)
            return f"Error realizando la búsqueda: {str(e)}"

    def transcribe_audio(self):
        """Transcribe audio a texto con manejo mejorado de errores"""
        if self._is_stopped:
            return None

        transcription_start = time.time()
        self.update_status.emit("🧠 Transcribiendo audio...")
        logger.info("Transcribiendo audio con Whisper...")

        for attempt in range(self.retry_attempts):
            try:
                whisper_cmd = [
                    WHISPER_EXE, '-m', WHISPER_MODEL, '-f', AUDIO_INPUT_FILE,
                    '-l', 'es', '-otxt', '-od', TEMP_PATH, '--timeout', '30000'
                ]
                
                # Añadir opciones de calidad
                audio_quality = self.config.get('Audio', 'audio_quality', fallback='high')
                if audio_quality == 'high':
                    whisper_cmd.extend(['--threads', str(os.cpu_count())])
                elif audio_quality == 'medium':
                    whisper_cmd.extend(['--threads', str(max(1, os.cpu_count() // 2))])
                
                stdout, stderr, return_code = self.run_command(whisper_cmd, timeout=60)
                
                if return_code == 0:
                    break
                else:
                    logger.warning(f"Whisper retornó código {return_code}, reintentando...")
                    
            except CommandTimeoutError:
                if attempt == self.retry_attempts - 1:
                    raise
                logger.warning(f"Timeout en transcripción, reintentando... ({attempt + 1}/{self.retry_attempts})")
                continue
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise
                logger.warning(f"Error en transcripción, reintentando... ({attempt + 1}/{self.retry_attempts}): {e}")
                continue

        self.metrics['transcription_time'] = time.time() - transcription_start

        # Leer transcripción
        text_file_path = f"{AUDIO_INPUT_FILE}.txt"
        if not os.path.exists(text_file_path):
            raise FileNotFoundError(f"No se pudo encontrar el archivo de transcripción: {text_file_path}")

        with open(text_file_path, 'r', encoding='utf-8') as f:
            transcribed_text = f.read().strip()

        if not transcribed_text:
            raise ValueError("La transcripción está vacía")

        return transcribed_text

    def run(self):
        """Método principal del hilo de trabajo - Versión mejorada"""
        user_prompt = ""
        final_response_content = ""
        self.start_time = time.time()

        try:
            # Obtener input del usuario (audio o texto)
            if self.text_prompt:
                user_prompt = self.text_prompt
                logger.info(f"Procesando prompt de texto: {user_prompt[:50]}...")
                self.metrics['audio_duration'] = 0
            else:
                if self._is_stopped:
                    return

                self.update_status.emit("🎤 Grabando audio...")
                logger.info("Iniciando grabación de audio...")

                # Grabar audio
                record_start = time.time()
                if not self.record_audio():
                    if not self._is_stopped:
                        self.update_status.emit("❌ Error en grabación")
                    self.flow_finished.emit("", "")
                    return

                self.metrics['audio_duration'] = time.time() - record_start

                if self._is_stopped:
                    return

                # Transcribir audio
                try:
                    user_prompt = self.transcribe_audio()
                except Exception as e:
                    if not self._is_stopped:
                        self.update_status.emit("❌ Error en transcripción")
                    logger.error(f"Error en transcripción: {e}")
                    self.flow_finished.emit("", f"Error en transcripción: {str(e)}")
                    return

                if not user_prompt:
                    if not self._is_stopped:
                        self.update_status.emit("🤫 No se detectó audio claro.")
                    self.flow_finished.emit("", "")
                    return

                logger.info(f"Audio transcribido: {user_prompt[:50]}...")
                self.add_conversation_log.emit("Usuario", user_prompt)

            # Analizar intención del usuario
            intent = self.analyze_intent(user_prompt)
            logger.info(f"Intención detectada: {intent}")
            
            # Manejar intenciones peligrosas
            if intent == "danger":
                warning_msg = "⚠️ He detectado un comando que podría ser peligroso para el sistema. Por razones de seguridad, no puedo ejecutarlo."
                self.add_conversation_log.emit("Arch-Chan", warning_msg)
                self.speak_text(warning_msg)
                self.flow_finished.emit(user_prompt, warning_msg)
                return

            # Procesar con Ollama
            if self._is_stopped:
                return

            processing_start = time.time()
            self.update_status.emit("🤖 Procesando con IA...")
            current_messages = self.chat_history + [{'role': 'user', 'content': user_prompt}]

            # Llamar a Ollama con manejo de reintentos
            ai_response_msg = None
            for attempt in range(self.retry_attempts):
                try:
                    ai_response_msg = self.call_ollama_chat(current_messages, is_tool_call=True)
                    if ai_response_msg is not None and ai_response_msg.get('content'):
                        break
                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        raise
                    logger.warning(f"Reintentando llamada a Ollama... ({attempt + 1}/{self.retry_attempts}): {e}")
                    time.sleep(1)  # Esperar antes de reintentar

            if ai_response_msg is None:
                error_msg = "No se pudo obtener respuesta del modelo después de varios intentos."
                self.error_occurred.emit(error_msg)
                return

            self.metrics['processing_time'] = time.time() - processing_start

            ai_response_content = ai_response_msg.get('content', '')
            logger.info(f"Respuesta cruda recibida: {ai_response_content[:200]}...")

            # Procesar respuesta (puede ser JSON de herramienta o texto normal)
            try:
                # Intentar parsear como JSON
                tool_data = json.loads(ai_response_content)
                logger.info(f"JSON parseado correctamente: {list(tool_data.keys())}")

                # Procesar la herramienta
                final_response_content = self.process_tool_call(tool_data, current_messages, ai_response_msg)

                if final_response_content and not self._is_stopped:
                    self.add_conversation_log.emit("Arch-Chan", final_response_content)
                    self.speak_text(final_response_content)

            except json.JSONDecodeError:
                # No es JSON válido, tratar como texto normal
                logger.info("Respuesta no es JSON, tratando como texto normal")
                final_response_content = ai_response_content
                if final_response_content and not self._is_stopped:
                    self.add_conversation_log.emit("Arch-Chan", final_response_content)
                    self.speak_text(final_response_content)

            except Exception as e:
                # Error inesperado al procesar herramienta
                logger.error(f"Error procesando respuesta: {e}")
                error_msg = f"Lo siento, tuve un problema procesando tu solicitud: {str(e)}"
                if not self._is_stopped:
                    self.add_conversation_log.emit("Arch-Chan", error_msg)
                    self.speak_text(error_msg)

            # Calcular métricas finales
            self.metrics['total_time'] = time.time() - self.start_time
            logger.info(f"Métricas de performance: {self.metrics}")
            self.performance_metrics.emit(self.metrics)

            # Limpieza final
            if not self._is_stopped:
                self.update_status.emit("✅ Proceso completado")

            # Limpiar archivos temporales de audio
            if not self.text_prompt and self.config.getboolean('General', 'auto_cleanup', fallback=True):
                self.cleanup_temp_files()

        except SecurityError as e:
            error_msg = f"Error de seguridad: {str(e)}"
            logger.error(error_msg)
            if not self._is_stopped:
                self.error_occurred.emit(error_msg)
                final_response_content = f"Por razones de seguridad, no puedo ejecutar ese comando: {e}"
        except CommandTimeoutError as e:
            error_msg = f"Timeout: {str(e)}"
            logger.error(error_msg)
            if not self._is_stopped:
                self.error_occurred.emit(error_msg)
                final_response_content = "La operación tardó demasiado tiempo y fue cancelada."
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if not self._is_stopped:
                self.error_occurred.emit(error_msg)
                final_response_content = f"Ocurrió un error inesperado: {e}"

        self.flow_finished.emit(user_prompt, final_response_content)

    def cleanup_temp_files(self):
        """Limpia archivos temporales de forma segura"""
        temp_files = [
            AUDIO_INPUT_FILE,
            f"{AUDIO_INPUT_FILE}.txt",
            f"{AUDIO_INPUT_FILE}.wav",
        ]
        
        # También buscar en el directorio temporal
        temp_patterns = [
            os.path.join(TEMP_PATH, "*.txt"),
            os.path.join(TEMP_PATH, "*.wav"),
            os.path.join(TEMP_PATH, "*.json")
        ]
        
        all_files = temp_files + temp_patterns
        
        for file_pattern in all_files:
            try:
                if '*' in file_pattern:
                    # Usar glob para patrones con wildcard
                    import glob
                    for file_path in glob.glob(file_pattern):
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.debug(f"Archivo temporal eliminado: {file_path}")
                else:
                    if os.path.exists(file_pattern):
                        os.remove(file_pattern)
                        logger.debug(f"Archivo temporal eliminado: {file_pattern}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar {file_pattern}: {e}")