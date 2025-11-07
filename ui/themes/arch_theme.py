#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sistema de temas mejorado para Arch-Chan
"""


class ArchLinuxTheme:
    """Sistema de temas mejorado para Arch Linux"""

    THEMES = {
        "arch-dark": {
            "primary": "#1793D1",
            "primary_dark": "#0E6B9E",
            "primary_light": "#4BB4F0",
            "background": "#2F343F",
            "surface": "#383C4A",
            "surface_light": "#404552",
            "text_primary": "#D3DAE3",
            "text_secondary": "#7C818C",
            "text_muted": "#545A66",
            "accent": "#48B9C7",
            "warning": "#F27835",
            "error": "#F04A50",
            "success": "#33D17A",
            "border": "#1A1E26",
            "border_light": "#4B5162",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "hover": "rgba(255, 255, 255, 0.05)",
            "selection": "rgba(23, 147, 209, 0.3)",
        },
        "arch-light": {
            "primary": "#1793D1",
            "primary_dark": "#0E6B9E",
            "primary_light": "#4BB4F0",
            "background": "#F8F9FA",
            "surface": "#FFFFFF",
            "surface_light": "#F1F3F5",
            "text_primary": "#2F343F",
            "text_secondary": "#7C818C",
            "text_muted": "#A0A6B1",
            "accent": "#48B9C7",
            "warning": "#F27835",
            "error": "#F04A50",
            "success": "#33D17A",
            "border": "#E1E5EB",
            "border_light": "#D1D6DE",
            "shadow": "rgba(0, 0, 0, 0.1)",
            "hover": "rgba(0, 0, 0, 0.03)",
            "selection": "rgba(23, 147, 209, 0.1)",
        },
        "blue-matrix": {
            "primary": "#00FF41",
            "primary_dark": "#008F11",
            "primary_light": "#00FF41",
            "background": "#0D0208",
            "surface": "#0D0208",
            "surface_light": "#003B00",
            "text_primary": "#00FF41",
            "text_secondary": "#008F11",
            "text_muted": "#007700",
            "accent": "#00FF41",
            "warning": "#FF6B00",
            "error": "#FF003C",
            "success": "#00FF41",
            "border": "#008F11",
            "border_light": "#00FF41",
            "shadow": "rgba(0, 255, 65, 0.2)",
            "hover": "rgba(0, 255, 65, 0.1)",
            "selection": "rgba(0, 255, 65, 0.2)",
        },
        "green-terminal": {
            "primary": "#00CC00",
            "primary_dark": "#009900",
            "primary_light": "#00FF00",
            "background": "#001100",
            "surface": "#002200",
            "surface_light": "#003300",
            "text_primary": "#00FF00",
            "text_secondary": "#00CC00",
            "text_muted": "#009900",
            "accent": "#00FF88",
            "warning": "#FFAA00",
            "error": "#FF4444",
            "success": "#00FF00",
            "border": "#004400",
            "border_light": "#00AA00",
            "shadow": "rgba(0, 255, 0, 0.2)",
            "hover": "rgba(0, 255, 0, 0.1)",
            "selection": "rgba(0, 255, 0, 0.2)",
        },
        "purple-haze": {
            "primary": "#9D4EDD",
            "primary_dark": "#7B2CBF",
            "primary_light": "#C77DFF",
            "background": "#1A1423",
            "surface": "#24152F",
            "surface_light": "#2D1B3B",
            "text_primary": "#E0AAFF",
            "text_secondary": "#C77DFF",
            "text_muted": "#9D4EDD",
            "accent": "#FF6B6B",
            "warning": "#FF9E64",
            "error": "#FF4757",
            "success": "#51CF66",
            "border": "#3C2A4D",
            "border_light": "#5A3D7A",
            "shadow": "rgba(157, 78, 221, 0.3)",
            "hover": "rgba(157, 78, 221, 0.1)",
            "selection": "rgba(157, 78, 221, 0.3)",
        },
    }

    FONTS = {
        "primary": "Noto Sans, DejaVu Sans, sans-serif",
        "monospace": "Hack, Fira Code, DejaVu Sans Mono, monospace",
        "title": "Noto Sans, Cantarell, sans-serif",
    }

    @classmethod
    def get_theme(cls, theme_name="arch-dark"):
        """Obtiene un tema por nombre"""
        return cls.THEMES.get(theme_name, cls.THEMES["arch-dark"])

    @classmethod
    def get_available_themes(cls):
        """Retorna la lista de temas disponibles"""
        return list(cls.THEMES.keys())

    @classmethod
    def get_stylesheet(cls, theme_name="arch-dark"):
        """Genera la hoja de estilo completa para el tema especificado"""
        theme = cls.get_theme(theme_name)

        return f"""
            /* === ESTILOS ARCH LINUX - {theme_name.upper()} === */

            QMainWindow, QWidget {{
                background-color: {theme['background']};
                color: {theme['text_primary']};
                font-family: {cls.FONTS['primary']};
                font-size: 11px;
                border: none;
            }}

            /* Frame de aplicación */
            ArchChanApp {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['surface']},
                    stop: 1 {theme['background']});
                border: 1px solid {theme['border']};
                border-radius: 8px;
            }}

            /* Header de la aplicación */
            #header_frame {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['primary_dark']},
                    stop: 1 {theme['primary']});
                border-bottom: 1px solid {theme['border']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 4px;
            }}

            /* Título de la aplicación */
            #title_label {{
                color: white;
                font-size: 14px;
                font-weight: bold;
                font-family: {cls.FONTS['title']};
                background: transparent;
                padding: 4px 8px;
            }}

            /* Logo de Arch */
            #arch_logo {{
                color: white;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }}

            /* Selector de modelo */
            #model_selector {{
                background-color: {theme['surface_light']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 140px;
                font-size: 10px;
                selection-background-color: {theme['selection']};
            }}

            #model_selector:hover {{
                border: 1px solid {theme['primary_light']};
                background-color: {theme['hover']};
            }}

            #model_selector::drop-down {{
                border: none;
                width: 20px;
            }}

            #model_selector::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {theme['text_secondary']};
                width: 0px;
                height: 0px;
            }}

            #model_selector QAbstractItemView {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border_light']};
                color: {theme['text_primary']};
                selection-background-color: {theme['primary']};
                selection-color: white;
                outline: none;
                border-radius: 4px;
            }}

            /* Área de chat */
            #chat_area {{
                background-color: {theme['background']};
                border: none;
                border-radius: 0px;
                font-family: {cls.FONTS['primary']};
                font-size: 11px;
                color: {theme['text_primary']};
                padding: 12px;
                selection-background-color: {theme['selection']};
                line-height: 1.4;
            }}

            /* Barra de estado */
            #status_frame {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                padding: 8px 12px;
                margin: 4px;
            }}

            #status_label {{
                color: {theme['text_secondary']};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }}

            /* Barra de progreso */
            #progress_bar {{
                border: 1px solid {theme['border_light']};
                border-radius: 4px;
                background-color: {theme['surface']};
                text-align: center;
                height: 6px;
            }}

            #progress_bar::chunk {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {theme['primary']},
                    stop: 1 {theme['accent']});
                border-radius: 3px;
            }}

            /* Botones principales */
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['surface_light']},
                    stop: 1 {theme['surface']});
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
                min-height: 24px;
            }}

            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['primary_light']},
                    stop: 1 {theme['primary']});
                color: white;
                border: 1px solid {theme['primary_dark']};
            }}

            QPushButton:pressed {{
                background-color: {theme['primary_dark']};
                color: white;
            }}

            QPushButton:disabled {{
                background-color: {theme['surface']};
                color: {theme['text_muted']};
                border: 1px solid {theme['border']};
            }}

            /* Botón de voz específico */
            #voice_button {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['accent']},
                    stop: 1 {theme['primary']});
                color: white;
                border: 1px solid {theme['primary_dark']};
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
                font-size: 12px;
            }}

            #voice_button:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['success']},
                    stop: 1 {theme['accent']});
            }}

            /* Botón de enviar */
            #send_button {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['success']},
                    stop: 1 {theme['accent']});
                color: white;
                border: 1px solid {theme['primary_dark']};
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
                font-size: 12px;
            }}

            #send_button:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45E685,
                    stop: 1 {theme['success']});
            }}

            /* Botón de detener */
            #stop_button {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['error']},
                    stop: 1 {theme['warning']});
                color: white;
                border: 1px solid {theme['border']};
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}

            #stop_button:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FF6B6B,
                    stop: 1 {theme['error']});
            }}

            /* Campo de texto */
            #text_input {{
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                padding: 8px 12px;
                font-family: {cls.FONTS['primary']};
                font-size: 11px;
                selection-background-color: {theme['selection']};
            }}

            #text_input:focus {{
                border: 1px solid {theme['primary']};
                background-color: {theme['surface_light']};
            }}

            #text_input:placeholder {{
                color: {theme['text_muted']};
                font-style: italic;
            }}

            /* Panel de información del sistema */
            #system_info_frame {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border_light']};
                border-radius: 8px;
                padding: 12px;
            }}

            /* Etiquetas de información */
            .info_label {{
                color: {theme['text_secondary']};
                font-size: 10px;
                background: transparent;
                font-weight: normal;
            }}

            .info_value {{
                color: {theme['text_primary']};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }}

            .info_value_warning {{
                color: {theme['warning']};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }}

            .info_value_error {{
                color: {theme['error']};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }}

            .info_value_success {{
                color: {theme['success']};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }}

            /* Tooltips */
            QToolTip {{
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 10px;
            }}

            /* Barras de scroll */
            QScrollBar:vertical {{
                background-color: {theme['surface']};
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {theme['border_light']};
                border-radius: 6px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {theme['primary_light']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar:horizontal {{
                background-color: {theme['surface']};
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {theme['border_light']};
                border-radius: 6px;
                min-width: 20px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {theme['primary_light']};
            }}
            #chat_header {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme['surface_light']},
                    stop: 1 {theme['surface']});
                border-bottom: 1px solid {theme['border_light']};
                border-radius: 8px 8px 0 0;
            }}

            #chat_title {{
                color: {theme['text_primary']};
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }}

            /* Frame de entrada */
            #input_frame {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border_light']};
                border-radius: 8px;
                padding: 8px;
            }}

            /* Indicadores de estado */
            #voice_indicator, #connection_indicator {{
                color: {theme['text_secondary']};
                font-size: 10px;
                font-weight: normal;
                background: transparent;
            }}

            /* Estado de procesamiento activo */
            #status_label[class="processing"] {{
                color: {theme['primary']};
                font-weight: bold;
            }}

            /* Mejoras de scrollbar para el área de chat */
            #chat_area QScrollBar:vertical {{
                background-color: {theme['surface']};
                width: 14px;
                margin: 0px;
                border-radius: 7px;
            }}

            #chat_area QScrollBar::handle:vertical {{
                background-color: {theme['border_light']};
                border-radius: 7px;
                min-height: 30px;
            }}

            #chat_area QScrollBar::handle:vertical:hover {{
                background-color: {theme['primary_light']};
            }}

            /* Efectos de hover para botones deshabilitados */
            QPushButton:disabled {{
                background-color: {theme['surface']};
                color: {theme['text_muted']};
                border: 1px solid {theme['border']};
                opacity: 0.6;
            }}

            /* Mejoras de focus para inputs */
            #text_input:focus {{
                border: 1px solid {theme['primary']};
                background-color: {theme['surface_light']};
                selection-background-color: {theme['selection']};
            }}

            /* Animaciones sutiles para botones */
            QPushButton {{
                transition: all 0.2s ease;
            }}

            QPushButton:hover {{
                transform: translateY(-1px);
            }}

            QPushButton:pressed {{
                transform: translateY(1px);
            }}

            /* Efectos de sombra para mensajes del chat */
            #chat_area QFrame {{
                border: none;
                background: transparent;
            }}
        """
