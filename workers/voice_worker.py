#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import Any, Dict, Optional

from PySide6.QtCore import QEventLoop, Signal

from services.speech_service import SpeechService
from utils.constants import AUDIO_INPUT_FILE, TTS_MODEL_ONNX, WHISPER_MODEL
from utils.logger import get_logger
from workers.base_worker import BaseWorker


class VoiceWorker(BaseWorker):
    """Worker para procesamiento de voz (Patrón moveToThread)"""

    # Señales específicas
    recording_started = Signal()
    recording_finished = Signal()
    transcription_ready = Signal(str)
    audio_level = Signal(int)
    processing_step = Signal(str)

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.logger = get_logger("VoiceWorker")
        self.config = config or {}

        # El servicio de voz se creará en el hilo del worker
        self.speech_service: Optional[SpeechService] = None

    def _initialize_speech_service(self):
        """Inicializa el servicio de voz si no está proporcionado -"""
        if self.speech_service is None:
            self.speech_service = SpeechService()
            # Configurar para eliminación segura
            self.speech_service.setParent(self)
            # Conectar señales del servicio de voz
            self.speech_service.transcription_ready.connect(self.transcription_ready)
            self.speech_service.error_occurred.connect(self.error_occurred)
            self.speech_service.recording_started.connect(self.recording_started)
            self.speech_service.recording_finished.connect(self.recording_finished)

    def safe_delete(self):
        """Eliminación segura del worker y sus servicios"""
        try:
            if self.speech_service:
                self.speech_service.stop_speech()
                self.speech_service = None

            super().safe_delete()
        except Exception as e:
            self.logger.debug(f"Error en safe_delete: {str(e)}")

    def _execute(self) -> Dict[str, Any]:
        """
        Ejecuta el procesamiento de voz completo (grabación y transcripción)
        """
        try:
            self._initialize_speech_service()

            if not self.speech_service:
                return {"status": "error", "error": "Servicio de voz no disponible"}

            # 1. Grabar audio
            self.processing_step.emit("Iniciando grabación...")

            audio_file = self.config.get("audio_file", AUDIO_INPUT_FILE)
            record_duration = self.config.get("record_duration", 10)
            silence_threshold = self.config.get("silence_threshold", "5%")

            # Usar QEventLoop para esperar a que la grabación (asíncrona) termine
            record_loop = QEventLoop()
            record_success = False

            def on_record_finish(success: bool):
                nonlocal record_success
                record_success = success
                record_loop.quit()

            self.speech_service.recording_finished.connect(on_record_finish)

            # Iniciar la grabación no bloqueante
            self.speech_service.record_audio(
                output_file=audio_file,
                duration=record_duration,
                silence_threshold=silence_threshold,
            )

            record_loop.exec()  # Esperar
            self.speech_service.recording_finished.disconnect(on_record_finish)

            if self.check_stopped():
                self.speech_service.stop_speech()
                return {"status": "cancelled"}

            if not record_success:
                return {"status": "error", "error": "No se pudo grabar audio"}

            # 2. Transcribir audio
            self.processing_step.emit("Transcribiendo audio...")

            # La transcripción sigue siendo bloqueante (rápida) dentro del worker
            transcribed_text = self.speech_service.speech_to_text(
                audio_file, model_path=WHISPER_MODEL
            )

            if self.check_stopped():
                return {"status": "cancelled"}

            if (
                transcribed_text is None
            ):  # Comprobar None, no Falsy (texto vacío es válido)
                return {"status": "error", "error": "No se pudo transcribir audio"}

            # 3. Limpiar archivo temporal
            if self.config.get("cleanup_temp_files", True):
                try:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                except Exception as e:
                    self.logger.warning(
                        f"No se pudo limpiar archivo temporal: {str(e)}"
                    )

            return {
                "status": "success",
                "type": "transcription",
                "text": transcribed_text,
                "audio_file": audio_file,
            }

        except Exception as e:
            self.logger.error(f"Error en procesamiento de voz: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e), "type": "voice_processing"}

    def get_transcription(self) -> Optional[str]:
        result = self._result or {}
        return result.get("text") if result.get("status") == "success" else None
