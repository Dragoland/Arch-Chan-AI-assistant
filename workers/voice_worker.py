#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import Any, Dict, Optional

from PySide6.QtCore import Signal

from services.speech_service import SpeechService
from utils.logger import get_logger
from workers.base_worker import BaseWorker


class VoiceWorker(BaseWorker):
    """Worker para procesamiento de voz"""

    # Señales específicas
    recording_started = Signal()  # Grabación iniciada
    recording_finished = Signal()  # Grabación finalizada
    transcription_ready = Signal(str)  # Transcripción lista
    audio_level = Signal(int)  # Nivel de audio (0-100)
    processing_step = Signal(str)

    def __init__(
        self, speech_service: SpeechService, config: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        self.logger = get_logger("VoiceWorker")

        self.speech_service = speech_service
        self.config = config or {}

        # Conectar señales del servicio de voz
        self.speech_service.transcription_ready.connect(self.transcription_ready)
        self.speech_service.error_occurred.connect(self.error_occurred)

    def _execute(self) -> Dict[str, Any]:
        """
        Ejecuta el procesamiento de voz completo

        Returns:
            Resultado del procesamiento
        """
        try:
            # 1. Grabar audio
            self.processing_step.emit("Iniciando grabación...")
            self.recording_started.emit()

            audio_file = self.config.get("audio_file", "/tmp/arch_chan_input.wav")
            record_duration = self.config.get("record_duration", 10)
            silence_threshold = self.config.get("silence_threshold", "5%")

            success = self.speech_service.record_audio(
                output_file=audio_file,
                duration=record_duration,
                silence_threshold=silence_threshold,
            )

            if self.check_stopped():
                return {"status": "cancelled"}

            if not success:
                return {
                    "status": "error",
                    "error": "No se pudo grabar audio",
                    "type": "recording",
                }

            self.recording_finished.emit()

            # 2. Transcribir audio
            self.processing_step.emit("Transcribiendo audio...")

            transcribed_text = self.speech_service.speech_to_text(audio_file)

            if self.check_stopped():
                return {"status": "cancelled"}

            if not transcribed_text:
                return {
                    "status": "error",
                    "error": "No se pudo transcribir audio",
                    "type": "transcription",
                }

            # 3. Limpiar archivo temporal
            if self.config.get("cleanup_temp_files", True):
                try:
                    os.remove(audio_file)
                    text_file = audio_file + ".txt"
                    if os.path.exists(text_file):
                        os.remove(text_file)
                except Exception as e:
                    self.logger.warning(f"No se pudo limpiar archivos temporales: {e}")

            return {
                "status": "success",
                "type": "transcription",
                "text": transcribed_text,
                "audio_file": audio_file,
            }

        except Exception as e:
            self.logger.error(f"Error en procesamiento de voz: {e}")
            return {"status": "error", "error": str(e), "type": "voice_processing"}

    def text_to_speech(self, text: str) -> bool:
        """
        Convierte texto a voz (ejecución síncrona)

        Args:
            text: Texto a convertir

        Returns:
            True si la conversión fue exitosa
        """
        try:
            self.processing_step.emit("Sintetizando voz...")
            return self.speech_service.text_to_speech(text)
        except Exception as e:
            self.logger.error(f"Error en síntesis de voz: {e}")
            return False

    def get_transcription(self) -> Optional[str]:
        """
        Retorna la transcripción resultante

        Returns:
            Texto transcribido o None
        """
        result = self._result or {}
        return result.get("text") if result.get("status") == "success" else None

    def get_audio_file(self) -> Optional[str]:
        """
        Retorna el archivo de audio grabado

        Returns:
            Ruta del archivo de audio o None
        """
        result = self._result or {}
        return result.get("audio_file")
