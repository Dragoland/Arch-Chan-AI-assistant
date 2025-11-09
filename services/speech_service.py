#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile
import time
from typing import Optional, Tuple

from PySide6.QtCore import QObject, QProcess, Signal

from utils.constants import AUDIO_INPUT_FILE, TTS_MODEL_ONNX, WHISPER_MODEL
from utils.logger import get_logger


class SpeechService(QObject):
    """Servicio de voz para síntesis y reconocimiento de voz"""

    # Señales
    transcription_ready = Signal(str)  # Texto transcribido desde audio
    synthesis_started = Signal()  # Inicio de síntesis de voz
    synthesis_finished = Signal()  # Fin de síntesis de voz
    error_occurred = Signal(str)  # Error en el servicio de voz
    recording_started = Signal()  # Inicio de grabación
    recording_finished = Signal()  # Fin de grabación
    audio_level_update = Signal(int)  # Nivel de audio en tiempo real

    def __init__(
        self,
        piper_path: str = "piper-tts",
        whisper_path: str = "whisper-cli",
        aplay_path: str = "aplay",
        rec_path: str = "rec",
    ):
        super().__init__()
        self.logger = get_logger("SpeechService")

        # Rutas de ejecutables
        self.piper_path = piper_path
        self.whisper_path = whisper_path
        self.aplay_path = aplay_path
        self.rec_path = rec_path

        # Estado
        self.current_process: Optional[QProcess] = None
        self.is_speaking = False
        self.is_recording = False

        # Directorio temporal
        self.temp_dir = tempfile.gettempdir()

        self.logger.info("SpeechService inicializado")

    def text_to_speech(
        self,
        text: str,
        model_path: str = TTS_MODEL_ONNX,
        sample_rate: int = 22050,
        volume: float = 0.8,
    ) -> bool:
        """
        Convierte texto a voz y lo reproduce

        Args:
            text: Texto a convertir
            model_path: Ruta al modelo de TTS
            sample_rate: Tasa de muestreo de audio
            volume: Volumen de salida (0.0 a 1.0)

        Returns:
            True si la conversión fue exitosa
        """
        if not text or not text.strip():
            self.logger.warning("Texto vacío para TTS")
            return False

        try:
            self.synthesis_started.emit()
            self.is_speaking = True

            # Limitar longitud del texto para TTS
            if len(text) > 1000:
                text = text[:1000] + "..."
                self.logger.warning("Texto truncado para TTS")

            # Usar archivo temporal para el audio
            temp_audio = os.path.join(self.temp_dir, "tts_output.wav")

            # Comando de Piper para sintetizar audio a archivo
            piper_command = [
                self.piper_path,
                "--model",
                model_path,
                "--output_file",
                temp_audio,
            ]

            self.logger.info(f"Iniciando síntesis de voz: {text[:50]}...")

            # Ejecutar Piper para generar archivo de audio
            piper_process = subprocess.run(
                piper_command,
                input=text.encode("utf-8"),
                capture_output=True,
                text=False,  # Usar bytes para stdin
                timeout=30,  # Timeout de 30 segundos
            )

            if piper_process.returncode != 0:
                error_msg = f"Piper falló: {piper_process.stderr.decode('utf-8', errors='ignore')}"
                self.logger.error(error_msg)
                raise Exception(error_msg)

            # Verificar que el archivo se creó
            if not os.path.exists(temp_audio):
                raise Exception("Piper no generó archivo de audio")

            # Reproducir archivo con aplay
            aplay_command = [self.aplay_path, "-q", temp_audio]  # Modo silencioso

            aplay_process = subprocess.run(
                aplay_command, capture_output=True, timeout=30
            )

            # Limpiar archivo temporal
            try:
                os.remove(temp_audio)
            except:
                pass

            if aplay_process.returncode != 0:
                error_msg = f"Error reproduciendo audio: {aplay_process.stderr.decode('utf-8', errors='ignore')}"
                self.logger.error(error_msg)
                raise Exception(error_msg)

            self.synthesis_finished.emit()
            self.is_speaking = False
            self.logger.info("Síntesis de voz completada")

            return True

        except subprocess.TimeoutExpired:
            error_msg = "Síntesis de voz excedió el tiempo límite"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.is_speaking = False
            return False

        except Exception as e:
            error_msg = f"Error en síntesis de voz: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.is_speaking = False
            return False

    def speech_to_text(
        self,
        audio_file: str = AUDIO_INPUT_FILE,
        model_path: str = WHISPER_MODEL,
        language: str = "es",
        timeout: int = 30,
    ) -> Optional[str]:
        """
        Transcribe audio a texto usando Whisper

        Args:
            audio_file: Ruta al archivo de audio
            model_path: Ruta al modelo de Whisper
            language: Idioma del audio
            timeout: Tiempo máximo de espera

        Returns:
            Texto transcribido o None en caso de error
        """
        if not os.path.exists(audio_file):
            self.logger.error(f"Archivo de audio no encontrado: {audio_file}")
            return None

        try:
            self.logger.info(f"Iniciando transcripción de audio: {audio_file}")

            # Usar archivo temporal para la salida
            base_name = os.path.splitext(audio_file)[0]
            output_file = os.path.join(
                self.temp_dir, f"transcription_{os.path.basename(base_name)}"
            )

            whisper_command = [
                self.whisper_path,
                "-m",
                model_path,
                "-f",
                audio_file,
                "-l",
                language,
                "-otxt",
                "-of",
                output_file,
                "--timeout",
                str(timeout * 1000),  # Whisper espera en milisegundos
            ]

            result = subprocess.run(
                whisper_command, capture_output=True, text=True, timeout=timeout
            )

            if result.returncode != 0:
                self.logger.error(f"Whisper retornó error: {result.stderr}")
                return None

            # Leer el archivo de texto generado
            text_file = output_file + ".txt"
            if not os.path.exists(text_file):
                self.logger.error(f"Archivo de transcripción no generado: {text_file}")
                return None

            with open(text_file, "r", encoding="utf-8") as f:
                transcribed_text = f.read().strip()

            # Limpiar archivo temporal
            try:
                os.remove(text_file)
            except:
                pass

            self.logger.info(f"Transcripción completada: {transcribed_text[:50]}...")
            self.transcription_ready.emit(transcribed_text)

            return transcribed_text

        except subprocess.TimeoutExpired:
            error_msg = f"Transcripción excedió el tiempo límite de {timeout} segundos"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

        except Exception as e:
            error_msg = f"Error en transcripción de voz: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def record_audio(
        self,
        output_file: str = AUDIO_INPUT_FILE,
        duration: int = 10,
        sample_rate: int = 16000,
        silence_threshold: str = "5%",
    ) -> bool:
        """
        Graba audio desde el micrófono

        Args:
            output_file: Ruta donde guardar el audio
            duration: Duración máxima en segundos
            sample_rate: Tasa de muestreo
            silence_threshold: Umbral de silencio para detección

        Returns:
            True si la grabación fue exitosa
        """
        try:
            self.recording_started.emit()
            self.is_recording = True

            self.logger.info("Iniciando grabación de audio...")

            # Usar sox (rec) para grabación con detección de silencio
            record_command = [
                self.rec_path,
                "-r",
                str(sample_rate),
                "-c",
                "1",
                "-b",
                "16",
                output_file,
                "silence",
                "1",
                "0.1",
                silence_threshold,
                "1",
                "1.0",
                silence_threshold,
            ]

            # Ejecutar grabación con timeout
            result = subprocess.run(
                record_command,
                timeout=duration + 2,  # Margen adicional
                capture_output=True,
                text=True,
            )

            self.is_recording = False
            self.recording_finished.emit()

            if result.returncode != 0:
                self.logger.error(f"Error en grabación: {result.stderr}")
                return False

            # Verificar que se creó el archivo y tiene contenido
            if not os.path.exists(output_file):
                self.logger.error("Archivo de grabación no creado")
                return False

            file_size = os.path.getsize(output_file)
            if file_size == 0:
                self.logger.error("Archivo de grabación vacío")
                return False

            self.logger.info(f"Grabación completada: {output_file} ({file_size} bytes)")
            return True

        except subprocess.TimeoutExpired:
            self.logger.info("Grabación finalizada por tiempo")
            self.is_recording = False
            self.recording_finished.emit()
            return os.path.exists(output_file) and os.path.getsize(output_file) > 0

        except Exception as e:
            error_msg = f"Error en grabación de audio: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.is_recording = False
            self.recording_finished.emit()
            return False

    def stop_speech(self):
        """Detiene cualquier operación de voz en curso"""
        if (
            self.current_process
            and self.current_process.state() == QProcess.ProcessState.Running
        ):
            self.current_process.terminate()
            if not self.current_process.wait(2000):  # Esperar 2 segundos
                self.current_process.kill()

        self.is_speaking = False
        self.is_recording = False
        self.logger.info("Operaciones de voz detenidas")

    def is_available(self) -> bool:
        """Verifica si el servicio de voz está disponible"""
        tools = {
            "Piper": [self.piper_path, "--version"],
            "Whisper": [self.whisper_path, "--help"],
            "rec (sox)": [self.rec_path, "--version"],
            "aplay": [self.aplay_path, "--version"],
        }

        for tool_name, command in tools.items():
            try:
                result = subprocess.run(
                    command, capture_output=True, timeout=5, check=False
                )
                if result.returncode != 0:
                    self.logger.warning(f"{tool_name} no disponible")
                    return False
            except Exception as e:
                self.logger.warning(f"Error verificando {tool_name}: {str(e)}")
                return False

        self.logger.info("Todos los componentes de voz están disponibles")
        return True

    def get_audio_devices(self) -> Tuple[list, list]:
        """
        Obtiene la lista de dispositivos de audio disponibles

        Returns:
            Tuple (dispositivos_de_entrada, dispositivos_de_salida)
        """
        input_devices = []
        output_devices = []

        try:
            # Obtener dispositivos de entrada
            result = subprocess.run(
                ["arecord", "-l"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "card" in line and "device" in line:
                        input_devices.append(line.strip())

            # Obtener dispositivos de salida
            result = subprocess.run(
                ["aplay", "-l"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "card" in line and "device" in line:
                        output_devices.append(line.strip())

        except Exception as e:
            self.logger.warning(f"Error obteniendo dispositivos de audio: {str(e)}")

        return input_devices, output_devices
