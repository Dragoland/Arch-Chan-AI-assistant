#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Panel de chat completamente reescrito para Arch-Chan v2.1
Con interfaz moderna, animaciones y mejoras de usabilidad
"""

from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services import ollama_client
from ui.themes.arch_theme import ArchLinuxTheme
from utils.logger import get_logger


class ChatPanel(QWidget):
    """Panel principal de chat con interfaz moderna y mejoras de UX"""

    # Señales
    voice_flow_started = Signal()
    text_flow_started = Signal(str)
    worker_stop_requested = Signal()
    model_changed = Signal(str)
    theme_change_requested = Signal(str)
    performance_metrics_updated = Signal(dict)

    def __init__(self, config_manager, state_manager):
        super().__init__()
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger = get_logger("ChatPanel")

        self.chat_history = []
        self.current_theme = self.config_manager.get("UI", "theme", "arch-dark")
        self.processing = False
        self.voice_recording = False
        self.typing_indicator_active = False

        self._create_ui()
        self._setup_animations()
        self._connect_signals()
        self._show_welcome_message()

        self.logger.info("ChatPanel inicializado")

    def _create_ui(self):
        """Crea la interfaz del panel de chat"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header del chat
        self._create_chat_header(layout)

        # Área de chat
        self._create_chat_area(layout)

        # Barra de progreso
        self._create_progress_bar(layout)

        # Panel de estado
        self._create_status_panel(layout)

        # Controles de entrada
        self._create_input_controls(layout)

    def _create_chat_header(self, parent_layout):
        """Crea el header del chat"""
        header_frame = QFrame()
        header_frame.setObjectName("chat_header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 10, 16, 10)

        # Título del chat con icono
        chat_title_layout = QHBoxLayout()
        chat_icon = QLabel("💬")
        chat_icon.setStyleSheet("font-size: 16px;")
        chat_title = QLabel("Asistente de IA - Arch Linux")
        chat_title.setObjectName("chat_title")

        chat_title_layout.addWidget(chat_icon)
        chat_title_layout.addWidget(chat_title)
        chat_title_layout.addStretch()

        # Selector de modelo
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Modelo:"))

        self.model_selector = QComboBox()
        self.model_selector.setObjectName("model_selector")
        self.model_selector.setFixedWidth(150)
        self._load_available_models()

        saved_model = self.config_manager.get("General", "model", "arch-chan")
        index = self.model_selector.findText(saved_model)
        if index >= 0:
            self.model_selector.setCurrentIndex(index)

        model_layout.addWidget(self.model_selector)

        header_layout.addLayout(chat_title_layout)
        header_layout.addStretch()
        header_layout.addLayout(model_layout)

        parent_layout.addWidget(header_frame)

    def _create_chat_area(self, parent_layout):
        """Crea el área de chat con scroll mejorado"""
        self.chat_area = QTextEdit()
        self.chat_area.setObjectName("chat_area")
        self.chat_area.setReadOnly(True)
        self.chat_area.document().setDocumentMargin(12)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Configurar fuente para mejor legibilidad
        font = QFont("Noto Sans", 10)
        self.chat_area.setFont(font)

        parent_layout.addWidget(self.chat_area)

        # Configurar fuente para mejor legibilidad
        font = QFont("Noto Sans", 10)
        self.chat_area.setFont(font)

        parent_layout.addWidget(self.chat_area)

    def _create_progress_bar(self, parent_layout):
        """Crea la barra de progreso animada"""
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        parent_layout.addWidget(self.progress_bar)

    def _create_status_panel(self, parent_layout):
        """Crea el panel de estado con indicadores"""
        status_frame = QFrame()
        status_frame.setObjectName("status_frame")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 8, 12, 8)

        self.status_label = QLabel("🟢 Sistema listo - Conectado a Ollama")
        self.status_label.setObjectName("status_label")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        # Indicadores de estado
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(12)

        self.voice_indicator = QLabel("🎤 Voz: Activa")
        self.voice_indicator.setObjectName("voice_indicator")

        self.connection_indicator = QLabel("🌐 Conectado")
        self.connection_indicator.setObjectName("connection_indicator")

        indicators_layout.addWidget(self.voice_indicator)
        indicators_layout.addWidget(self.connection_indicator)

        status_layout.addLayout(indicators_layout)

        parent_layout.addWidget(status_frame)

    def _create_input_controls(self, parent_layout):
        """Crea los controles de entrada mejorados"""
        input_frame = QFrame()
        input_frame.setObjectName("input_frame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        # Botón de voz
        self.voice_button = QPushButton("🎤 Voz")
        self.voice_button.setObjectName("voice_button")
        self.voice_button.setFixedWidth(80)
        self.voice_button.setToolTip("Iniciar grabación de voz (Ctrl+V)")

        # Campo de entrada
        self.text_input = QLineEdit()
        self.text_input.setObjectName("text_input")
        self.text_input.setPlaceholderText(
            "Escribe tu mensaje o presiona el botón de voz..."
        )
        self.text_input.setClearButtonEnabled(True)

        # Botón de enviar
        self.send_button = QPushButton("📤 Enviar")
        self.send_button.setObjectName("send_button")
        self.send_button.setFixedWidth(80)
        self.send_button.setToolTip("Enviar mensaje (Enter)")
        self.send_button.setEnabled(False)

        # Botón de detener
        self.stop_button = QPushButton("⏹ Detener")
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setFixedWidth(80)
        self.stop_button.setEnabled(False)
        self.stop_button.setToolTip("Detener operación actual (Esc)")

        input_layout.addWidget(self.voice_button)
        input_layout.addWidget(self.text_input)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.stop_button)

        parent_layout.addWidget(input_frame)

    def _setup_animations(self):
        """Configura las animaciones y timers"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_animation)
        self.status_animation_state = 0

        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress_animation)
        self.progress_value = 0

        self.typing_indicator_timer = QTimer()
        self.typing_indicator_timer.timeout.connect(self._update_typing_indicator)

    def _connect_signals(self):
        """Conecta todas las señales internas"""
        self.voice_button.clicked.connect(self.start_voice_flow)
        self.send_button.clicked.connect(self.start_text_flow)
        self.text_input.returnPressed.connect(self.start_text_flow)
        self.text_input.textChanged.connect(self._on_text_changed)
        self.stop_button.clicked.connect(self.stop_generation)
        self.model_selector.currentTextChanged.connect(self.model_changed.emit)

    def _load_available_models(self):
        """Carga los modelos disponibles desde Ollama"""
        try:
            # Limpiar selector primero
            self.model_selector.clear()

            # Intentar cargar modelos de Ollama si está disponible
            if hasattr(self, "ollama_client") and self.ollama_client:
                models = self.ollama_client.list_models()
                if models:
                    model_names = []
                    for model in models:
                        name = model.get("name", "")
                        if name:
                            model_names.append(name)

                    if model_names:
                        self.model_selector.addItems(model_names)
                        self.logger.info(
                            f"Modelos cargados desde Ollama: {len(model_names)}"
                        )
                        return

            # Fallback a modelos por defecto
            default_models = [
                "arch-chan-lite",
                "arch-chan",
                "llama3.2:3b",
                "gemma:2b",
            ]
            self.model_selector.addItems(default_models)
            self.logger.info("Usando modelos por defecto")

        except Exception as e:
            self.logger.error(f"Error cargando modelos: {e}")
            # Fallback mínimo
            self.model_selector.addItems(["arch-chan"])

    def _show_welcome_message(self):
        """Muestra el mensaje de bienvenida"""
        theme = ArchLinuxTheme.get_theme(self.current_theme)

        welcome_msg = f"""
        <div style='text-align: center; margin: 40px 20px; padding: 30px; 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {theme['surface_light']}, stop:1 {theme['surface']});
                    border-radius: 12px; border: 1px solid {theme['border_light']};'>
            <h3 style='color: {theme['primary']}; margin-bottom: 15px; 
                       font-size: 18px; font-weight: bold;'>
                🐧 ¡Bienvenido a Arch-Chan v2.1.0!
            </h3>
            <p style='color: {theme['text_secondary']}; line-height: 1.6; 
                      font-size: 12px; margin-bottom: 20px;'>
                Tu asistente de IA nativo de Arch Linux<br>
                Usa voz o texto para interactuar conmigo
            </p>
            <div style='color: {theme['text_muted']}; font-size: 11px; 
                       background: {theme['background']}; padding: 10px; 
                       border-radius: 6px; border: 1px solid {theme['border']};'>
                💡 <b>Consejos rápidos:</b><br>
                • Presiona <b>Ctrl+V</b> para activar el modo voz<br>
                • Presiona <b>Enter</b> para enviar mensajes<br>
                • Usa <b>Esc</b> para cancelar operaciones
            </div>
        </div>
        """

        self.chat_area.setHtml(welcome_msg)

    def add_chat_message(self, sender, message, is_tool=False):
        """Añade un mensaje al chat con formato mejorado"""
        timestamp = datetime.now()
        self.chat_history.append(
            {
                "sender": sender,
                "message": message,
                "timestamp": timestamp,
                "is_tool": is_tool,
            }
        )

        theme = ArchLinuxTheme.get_theme(self.current_theme)

        if is_tool:
            # Formato para logs de herramientas
            html = f"""
            <div style='margin: 12px 0; padding: 12px; 
                        background-color: {theme['surface']}; 
                        border: 1px solid {theme['border_light']}; 
                        border-radius: 8px; border-left: 4px solid {theme['accent']};'>
                <div style='color: {theme['primary']}; font-weight: bold; font-size: 10px; 
                           margin-bottom: 6px; display: flex; align-items: center;'>
                    <span style='margin-right: 6px;'>🔧</span> {sender}
                    <span style='margin-left: auto; color: {theme['text_muted']}; 
                                font-size: 9px;'>
                        {timestamp.strftime("%H:%M:%S")}
                    </span>
                </div>
                <pre style='color: {theme['text_primary']}; font-size: 10px; margin: 0; 
                           white-space: pre-wrap; font-family: monospace;
                           background-color: {theme['background']}; padding: 10px; 
                           border-radius: 4px; border: 1px solid {theme['border']};'>{message}</pre>
            </div>
            """
        else:
            is_user = sender == "Usuario"
            alignment = "right" if is_user else "left"
            bg_color = theme["primary"] if is_user else theme["surface_light"]
            text_color = "white" if is_user else theme["text_primary"]
            icon = "👤" if is_user else "🤖"

            html = f"""
            <div style='margin: 16px 0; text-align: {alignment};'>
                <div style='display: inline-block; max-width: 80%; text-align: left;'>
                    <div style='background-color: {bg_color}; color: {text_color}; 
                               padding: 12px 16px; border-radius: 14px; 
                               font-size: 11px; line-height: 1.5;
                               border-bottom-{alignment}-radius: 4px;'>
                        {message.replace(chr(10), '<br>')}
                    </div>
                    <div style='color: {theme['text_muted']}; font-size: 9px; 
                               padding: 4px 8px 2px 8px; display: flex; align-items: center;'>
                        <span style='margin-right: 6px;'>{icon}</span>
                        {sender} • {timestamp.strftime("%H:%M")}
                    </div>
                </div>
            </div>
            """

        # Mantener el cursor al final
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_area.setTextCursor(cursor)

        self.chat_area.append(html)

        # Auto-scroll al final
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_ollama_client(self, ollama_client):
        self.ollama_client = ollama_client

    def start_voice_flow(self):
        """Inicia el flujo de voz"""
        if self.processing:
            return

        self.voice_flow_started.emit()
        self._set_processing_state(True)
        self.voice_recording = True
        self.voice_button.setText("🔴 Grabando...")
        self.voice_button.setProperty("class", "recording")
        self.status_label.setText("🎤 Grabando audio... Habla ahora")
        self.voice_indicator.setText("🎤 Grabando...")
        self._start_status_animation()

    def start_text_flow(self):
        """Inicia el flujo de texto"""
        if self.processing:
            return

        user_prompt = self.text_input.text().strip()
        if not user_prompt:
            return

        current_model = self.model_selector.currentText()
        self.logger.info(f"Iniciando flujo de texto con modelo: {current_model}")
        self.text_flow_started.emit(user_prompt)
        self._set_processing_state(True)
        self.text_input.clear()
        self.add_chat_message("Usuario", user_prompt)
        self._start_status_animation()

    def _on_text_changed(self, text):
        """Maneja cambios en el texto de entrada"""
        # Habilitar/deshabilitar botón de enviar
        self.send_button.setEnabled(bool(text.strip()))

    def stop_generation(self):
        """Detiene la generación actual - MÉTODO NUEVO"""
        try:
            self.logger.info("Solicitando detención de generación...")
            self.worker_stop_requested.emit()
            self._set_processing_state(False)
            self.status_label.setText("🟢 Generación detenida")

            # Mostrar mensaje en el chat
            self.add_chat_message(
                "Sistema", "Generación detenida por el usuario", is_tool=True
            )

        except Exception as e:
            self.logger.error(f"Error deteniendo generación: {e}")

    def _set_processing_state(self, processing=True):
        """Establece el estado de procesamiento"""
        self.processing = processing
        self.voice_button.setEnabled(not processing)
        self.send_button.setEnabled(
            not processing and bool(self.text_input.text().strip())
        )
        self.text_input.setEnabled(not processing)
        self.model_selector.setEnabled(not processing)
        self.stop_button.setEnabled(
            processing
        )  # Solo habilitado cuando está procesando

        self.progress_bar.setVisible(processing)
        if processing:
            self._start_progress_animation()
            self.status_label.setText("🤖 Procesando...")
        else:
            self._stop_progress_animation()
            self.voice_recording = False
            self.voice_button.setText("🎤 Voz")
            self.voice_button.setProperty("class", "")
            self.voice_indicator.setText("🎤 Voz: Activa")
            self.status_label.setText("🟢 Sistema listo")

    def _start_status_animation(self):
        """Inicia la animación de estado"""
        self.status_animation_state = 0
        self.status_timer.start(500)

    def _update_status_animation(self):
        """Actualiza la animación de estado"""
        animations = [
            "⏳ Procesando",
            "⏳ Procesando.",
            "⏳ Procesando..",
            "⏳ Procesando...",
        ]
        self.status_animation_state = (self.status_animation_state + 1) % len(
            animations
        )
        self.status_label.setText(animations[self.status_animation_state])

    def _start_progress_animation(self):
        """Inicia animación de barra de progreso indeterminada"""
        self.progress_value = 0
        self.progress_timer.start(50)
        self.progress_bar.setRange(0, 100)

    def _update_progress_animation(self):
        """Actualiza animación de barra de progreso"""
        self.progress_value = (self.progress_value + 2) % 100
        self.progress_bar.setValue(self.progress_value)

    def _stop_progress_animation(self):
        """Detiene animación de barra de progreso"""
        self.progress_timer.stop()
        self.progress_bar.setValue(0)

    def _update_typing_indicator(self):
        """Actualiza el indicador de escritura"""
        if self.typing_indicator_active:
            current_text = self.status_label.text()
            if "escribiendo" in current_text.lower():
                dots = (current_text.count(".") + 1) % 4
                self.status_label.setText(f"🤖 Arch-Chan está escribiendo{'.' * dots}")

    def on_worker_finished(self):
        """Maneja la finalización del worker"""
        self._set_processing_state(False)
        self.status_label.setText("🟢 Sistema listo")
        self._stop_status_animation()

    def _stop_status_animation(self):
        """Detiene la animación de estado"""
        self.status_timer.stop()
        self.progress_bar.setVisible(False)

    def update_connection_status(self, connected=True):
        """Actualiza el estado de conexión"""
        if connected:
            self.connection_indicator.setText("🌐 Conectado")
            self.status_label.setText("🟢 Sistema listo - Conectado a Ollama")
            self.connection_indicator.setStyleSheet(
                "color: #33D17A; font-weight: bold;"
            )
        else:
            self.connection_indicator.setText("🔴 Desconectado")
            self.status_label.setText("🔴 Sistema desconectado")
            self.connection_indicator.setStyleSheet(
                "color: #F04A50; font-weight: bold;"
            )

    def verify_ollama_connection(self):
        """Verifica la conexión con Ollama y actualiza la UI"""
        try:
            if hasattr(self, "ollama_client") and self.ollama_client:
                is_healthy = self.ollama_client.check_health()
                self.update_connection_status(is_healthy)

                if is_healthy:
                    # Recargar modelos si está conectado
                    self._load_available_models()
                return is_healthy
            return False
        except Exception as e:
            self.logger.error(f"Error verificando conexión Ollama: {e}")
            self.update_connection_status(False)
            return False

    def clear_chat(self):
        """Limpia el historial del chat"""
        self.chat_area.clear()
        self.chat_history.clear()
        self._show_welcome_message()
        self.logger.info("Chat limpiado por el usuario")

    def on_config_changed(self):
        """Maneja cambios en la configuración"""
        self.current_theme = self.config_manager.get("UI", "theme", "arch-dark")
        self._apply_component_styles()

    def on_theme_changed(self, theme_name):
        """Maneja cambios de tema"""
        self.current_theme = theme_name
        self._apply_component_styles()

    def on_model_changed(self, model_name):
        """Maneja cambios de modelo"""
        self.model_selector.setCurrentText(model_name)

    def _apply_component_styles(self):
        """Aplica estilos específicos a los componentes"""
        # Los estilos principales se aplican via QSS
        # Este método puede usarse para ajustes específicos
        pass

    def set_voice_recording_state(self, recording=True):
        """Establece el estado de grabación de voz"""
        self.voice_recording = recording
        if recording:
            self.voice_button.setProperty("class", "recording")
        else:
            self.voice_button.setProperty("class", "")
        self.voice_button.style().unpolish(self.voice_button)
        self.voice_button.style().polish(self.voice_button)

    def set_connection_state(self, connected=True):
        """Establece el estado de conexión con estilo"""
        self.connection_indicator.setProperty(
            "connected", "true" if connected else "false"
        )
        self.connection_indicator.style().unpolish(self.connection_indicator)
        self.connection_indicator.style().polish(self.connection_indicator)
        self.update_connection_status(connected)

    def set_processing_state(self, processing=True):
        """Establece el estado de procesamiento con estilo"""
        self.status_label.setProperty("processing", "true" if processing else "false")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self._set_processing_state(processing)

    def show_typing_indicator(self, show=True):
        """Muestra u oculta el indicador de escritura"""
        self.typing_indicator_active = show
        if show:
            self.typing_indicator_timer.start(500)
            self.status_label.setText("🤖 Arch-Chan está escribiendo")
        else:
            self.typing_indicator_timer.stop()
            self.status_label.setText("🟢 Sistema listo")
