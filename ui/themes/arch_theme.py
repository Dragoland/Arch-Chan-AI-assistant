#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sistema de temas completamente reescrito para Arch-Chan v2.1
Incluye 10 temas diferentes con animaciones CSS3 y efectos visuales
"""

import json
from typing import Any, Dict, List


class ArchLinuxTheme:
    """Sistema de temas avanzado con paletas de colores profesionales"""

    # Diccionario completo de temas disponibles
    THEMES = {
        "arch-dark": {
            "name": "Arch Dark",
            "type": "dark",
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
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1793D1, stop:1 #0E6B9E)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #383C4A, stop:1 #2F343F)",
        },
        "arch-light": {
            "name": "Arch Light",
            "type": "light",
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
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1793D1, stop:1 #0E6B9E)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F8F9FA)",
        },
        "blue-matrix": {
            "name": "Blue Matrix",
            "type": "dark",
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
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00FF41, stop:1 #008F11)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0D0208, stop:1 #003B00)",
        },
        "cyberpunk": {
            "name": "Cyberpunk Neon",
            "type": "dark",
            "primary": "#FF00FF",
            "primary_dark": "#CC00CC",
            "primary_light": "#FF66FF",
            "background": "#0A0A12",
            "surface": "#151520",
            "surface_light": "#1E1E2E",
            "text_primary": "#00FFEE",
            "text_secondary": "#FF00FF",
            "text_muted": "#666699",
            "accent": "#00FFEE",
            "warning": "#FFAA00",
            "error": "#FF0055",
            "success": "#00FF88",
            "border": "#FF00FF",
            "border_light": "#00FFEE",
            "shadow": "rgba(255, 0, 255, 0.4)",
            "hover": "rgba(0, 255, 238, 0.1)",
            "selection": "rgba(255, 0, 255, 0.3)",
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF00FF, stop:1 #CC00CC)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #151520, stop:1 #0A0A12)",
        },
        "sunset-glow": {
            "name": "Sunset Glow",
            "type": "dark",
            "primary": "#FF6B35",
            "primary_dark": "#E55627",
            "primary_light": "#FF8E53",
            "background": "#2D1B2E",
            "surface": "#3A2745",
            "surface_light": "#473354",
            "text_primary": "#FFEEDD",
            "text_secondary": "#FFB399",
            "text_muted": "#CC9988",
            "accent": "#FFE74C",
            "warning": "#FF9F1C",
            "error": "#E71D36",
            "success": "#2EC4B6",
            "border": "#FF6B35",
            "border_light": "#FF8E53",
            "shadow": "rgba(255, 107, 53, 0.3)",
            "hover": "rgba(255, 107, 53, 0.1)",
            "selection": "rgba(255, 107, 53, 0.3)",
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF6B35, stop:1 #E55627)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3A2745, stop:1 #2D1B2E)",
        },
        "midnight-ocean": {
            "name": "Midnight Ocean",
            "type": "dark",
            "primary": "#00A8CC",
            "primary_dark": "#0077A3",
            "primary_light": "#33D6FF",
            "background": "#001233",
            "surface": "#001F4D",
            "surface_light": "#002D66",
            "text_primary": "#E6F7FF",
            "text_secondary": "#99E6FF",
            "text_muted": "#66B3CC",
            "accent": "#FF6B6B",
            "warning": "#FFD166",
            "error": "#EF476F",
            "success": "#06D6A0",
            "border": "#005C99",
            "border_light": "#0088CC",
            "shadow": "rgba(0, 168, 204, 0.3)",
            "hover": "rgba(0, 168, 204, 0.1)",
            "selection": "rgba(0, 168, 204, 0.3)",
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00A8CC, stop:1 #0077A3)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #001F4D, stop:1 #001233)",
        },
        "forest-deep": {
            "name": "Forest Deep",
            "type": "dark",
            "primary": "#27AE60",
            "primary_dark": "#219653",
            "primary_light": "#6FCF97",
            "background": "#0D1B12",
            "surface": "#152619",
            "surface_light": "#1C331F",
            "text_primary": "#E8F5E8",
            "text_secondary": "#A3D9A5",
            "text_muted": "#7AA87C",
            "accent": "#F2C94C",
            "warning": "#F2994A",
            "error": "#EB5757",
            "success": "#27AE60",
            "border": "#1E4620",
            "border_light": "#2D6A31",
            "shadow": "rgba(39, 174, 96, 0.3)",
            "hover": "rgba(39, 174, 96, 0.1)",
            "selection": "rgba(39, 174, 96, 0.3)",
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #27AE60, stop:1 #219653)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #152619, stop:1 #0D1B12)",
        },
        "neon-dreams": {
            "name": "Neon Dreams",
            "type": "dark",
            "primary": "#9C27B0",
            "primary_dark": "#7B1FA2",
            "primary_light": "#E1BEE7",
            "background": "#1A1A2E",
            "surface": "#16213E",
            "surface_light": "#0F3460",
            "text_primary": "#E6E6FA",
            "text_secondary": "#BB86FC",
            "text_muted": "#9580FF",
            "accent": "#03DAC6",
            "warning": "#FFB74D",
            "error": "#CF6679",
            "success": "#4DB6AC",
            "border": "#3700B3",
            "border_light": "#6200EE",
            "shadow": "rgba(156, 39, 176, 0.4)",
            "hover": "rgba(156, 39, 176, 0.2)",
            "selection": "rgba(156, 39, 176, 0.3)",
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9C27B0, stop:1 #7B1FA2)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #16213E, stop:1 #1A1A2E)",
        },
        "purple-haze": {
            "name": "Purple Haze",
            "type": "dark",
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
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9D4EDD, stop:1 #7B2CBF)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #24152F, stop:1 #1A1423)",
        },
        "green-terminal": {
            "name": "Green Terminal",
            "type": "dark",
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
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00CC00, stop:1 #009900)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #002200, stop:1 #001100)",
        },
        "nordic": {
            "name": "Nordic",
            "type": "dark",
            "primary": "#88C0D0",
            "primary_dark": "#81A1C1",
            "primary_light": "#B48EAD",
            "background": "#2E3440",
            "surface": "#3B4252",
            "surface_light": "#434C5E",
            "text_primary": "#ECEFF4",
            "text_secondary": "#D8DEE9",
            "text_muted": "#A3BE8C",
            "accent": "#EBCB8B",
            "warning": "#D08770",
            "error": "#BF616A",
            "success": "#A3BE8C",
            "border": "#3B4252",
            "border_light": "#4C566A",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "hover": "rgba(236, 239, 244, 0.05)",
            "selection": "rgba(129, 161, 193, 0.3)",
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #88C0D0, stop:1 #81A1C1)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B4252, stop:1 #2E3440)",
        },
        "solarized-light": {
            "name": "Solarized Light",
            "type": "light",
            "primary": "#268BD2",
            "primary_dark": "#073642",
            "primary_light": "#2AA198",
            "background": "#FDF6E3",
            "surface": "#EEE8D5",
            "surface_light": "#FDF6E3",
            "text_primary": "#586E75",
            "text_secondary": "#657B83",
            "text_muted": "#93A1A1",
            "accent": "#B58900",
            "warning": "#CB4B16",
            "error": "#DC322F",
            "success": "#859900",
            "border": "#EEE8D5",
            "border_light": "#93A1A1",
            "shadow": "rgba(0, 0, 0, 0.1)",
            "hover": "rgba(0, 0, 0, 0.03)",
            "selection": "rgba(38, 139, 210, 0.2)",
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #268BD2, stop:1 #2AA198)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FDF6E3, stop:1 #EEE8D5)",
        },
        "monokai": {
            "name": "Monokai",
            "type": "dark",
            "primary": "#F92672",
            "primary_dark": "#AE81FF",
            "primary_light": "#FF6188",
            "background": "#272822",
            "surface": "#3E3D32",
            "surface_light": "#49483E",
            "text_primary": "#F8F8F2",
            "text_secondary": "#A6E22E",
            "text_muted": "#75715E",
            "accent": "#E6DB74",
            "warning": "#FD971F",
            "error": "#F92672",
            "success": "#A6E22E",
            "border": "#75715E",
            "border_light": "#F8F8F2",
            "shadow": "rgba(249, 38, 114, 0.3)",
            "hover": "rgba(249, 38, 114, 0.1)",
            "selection": "rgba(249, 38, 114, 0.3)",
            "gradient_primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F92672, stop:1 #AE81FF)",
            "gradient_surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3E3D32, stop:1 #272822)",
        },
    }

    # Configuración de fuentes
    FONTS = {
        "primary": "'Noto Sans', 'DejaVu Sans', sans-serif",
        "monospace": "'Hack', 'Fira Code', 'DejaVu Sans Mono', monospace",
        "title": "'Noto Sans', 'Cantarell', sans-serif",
        "icon": "'Material Icons', 'Segoe MDL2 Assets', sans-serif",
    }

    @classmethod
    def get_theme(cls, theme_name: str) -> Dict[str, Any]:
        """Obtiene un tema completo por nombre"""
        return cls.THEMES.get(theme_name, cls.THEMES["arch-dark"])

    @classmethod
    def get_available_themes(cls) -> List[str]:
        """Retorna la lista de todos los temas disponibles"""
        return list(cls.THEMES.keys())

    @classmethod
    def get_theme_names(cls) -> List[str]:
        """Retorna los nombres display de los temas"""
        return [theme["name"] for theme in cls.THEMES.values()]

    @classmethod
    def get_stylesheet(cls, theme_name: str) -> str:
        """Genera la hoja de estilo completa para el tema especificado"""
        theme = cls.get_theme(theme_name)

        return f"""
            /* === ARCH LINUX THEME - {theme['name'].upper()} === */
            /* Generado automáticamente para Arch-Chan v2.1 */

            /* === ESTILOS BASE === */
            QMainWindow, QWidget {{
                background-color: {theme['background']};
                color: {theme['text_primary']};
                font-family: {cls.FONTS['primary']};
                font-size: 11px;
                border: none;
                outline: none;
            }}

            /* === VENTANA PRINCIPAL === */
            #main_central_widget {{
                background: {theme['gradient_surface']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
            }}

            /* === BARRA DE HERRAMIENTAS === */
            QToolBar {{
                background: {theme['gradient_surface']};
                border-bottom: 1px solid {theme['border_light']};
                spacing: 6px;
                padding: 4px;
            }}

            QToolBar::separator {{
                background: {theme['border_light']};
                width: 1px;
                margin: 4px 2px;
            }}

            /* === BOTONES PRINCIPALES === */
            QPushButton {{
                background: {theme['gradient_primary']};
                color: white;
                border: 1px solid {theme['primary_dark']};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
                min-height: 28px;
            }}

            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['primary_light']}, stop:1 {theme['primary']});
                border: 1px solid {theme['primary_light']};
                transform: translateY(-1px);
            }}

            QPushButton:pressed {{
                background: {theme['primary_dark']};
                transform: translateY(1px);
            }}

            QPushButton:disabled {{
                background: {theme['surface']};
                color: {theme['text_muted']};
                border: 1px solid {theme['border']};
            }}

            /* === BOTÓN DE VOZ === */
            #voice_button {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['accent']}, stop:1 {theme['primary']});
                color: white;
                border: 1px solid {theme['primary_dark']};
                border-radius: 8px;
                font-weight: bold;
                min-width: 80px;
                font-size: 12px;
            }}

            #voice_button:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success']}, stop:1 {theme['accent']});
            }}

            #voice_button.recording {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error']}, stop:1 {theme['warning']});
                animation: pulse 2s infinite;
            }}

            /* === BOTÓN DE ENVIAR === */
            #send_button {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success']}, stop:1 {theme['accent']});
                color: white;
                border: 1px solid {theme['primary_dark']};
                border-radius: 8px;
                font-weight: bold;
                min-width: 80px;
                font-size: 12px;
            }}

            #send_button:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45E685, stop:1 {theme['success']});
            }}

            /* === BOTÓN DE DETENER === */
            #stop_button {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error']}, stop:1 {theme['warning']});
                color: white;
                border: 1px solid {theme['border']};
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }}

            #stop_button:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF6B6B, stop:1 {theme['error']});
            }}

            /* === CAMPO DE TEXTO === */
            #text_input {{
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 8px;
                padding: 10px 14px;
                font-family: {cls.FONTS['primary']};
                font-size: 11px;
                selection-background-color: {theme['selection']};
            }}

            #text_input:focus {{
                border: 2px solid {theme['primary']};
                background-color: {theme['surface_light']};
            }}

            #text_input:placeholder {{
                color: {theme['text_muted']};
                font-style: italic;
            }}

            /* === ÁREA DE CHAT === */
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

            /* === PANEL LATERAL === */
            #system_info_frame {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border_light']};
                border-radius: 12px;
                padding: 16px;
            }}

            /* === BARRA DE ESTADO === */
            QStatusBar {{
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                border-top: 1px solid {theme['border_light']};
                font-size: 10px;
            }}

            /* === SELECTOR DE MODELO === */
            #model_selector {{
                background-color: {theme['surface_light']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 8px;
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
                border-radius: 6px;
            }}

            /* === BARRAS DE PROGRESO === */
            QProgressBar {{
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                background-color: {theme['surface']};
                text-align: center;
                height: 8px;
            }}

            QProgressBar::chunk {{
                background: {theme['gradient_primary']};
                border-radius: 4px;
            }}

            /* === ANIMACIONES CSS === */
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
                100% {{ opacity: 1; }}
            }}

            @keyframes glow {{
                0% {{ box-shadow: 0 0 5px {theme['primary']}; }}
                50% {{ box-shadow: 0 0 20px {theme['primary']}, 0 0 30px {theme['accent']}; }}
                100% {{ box-shadow: 0 0 5px {theme['primary']}; }}
            }}

            @keyframes slideIn {{
                from {{ transform: translateX(-100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}

            /* === ESTADOS ANIMADOS === */
            QPushButton:hover {{
                animation: pulse 1.5s infinite;
            }}

            #voice_button.recording {{
                animation: glow 2s infinite;
            }}

            .processing {{
                animation: pulse 1s infinite;
                color: {theme['accent']};
            }}

            .warning {{
                color: {theme['warning']};
                font-weight: bold;
            }}

            .error {{
                color: {theme['error']};
                font-weight: bold;
                animation: pulse 0.5s infinite;
            }}

            .success {{
                color: {theme['success']};
                font-weight: bold;
            }}

            /* === TOOLTIPS === */
            QToolTip {{
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10px;
                opacity: 240;
            }}

            /* === MENÚS DESPLEGABLES === */
            QMenu {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border_light']};
                border-radius: 8px;
                padding: 4px;
            }}

            QMenu::item {{
                padding: 6px 16px;
                border-radius: 4px;
                background-color: transparent;
            }}

            QMenu::item:selected {{
                background-color: {theme['selection']};
            }}

            QMenu::separator {{
                height: 1px;
                background: {theme['border_light']};
                margin: 4px 8px;
            }}

            /* === CHECKBOXES Y RADIO BUTTONS === */
            QCheckBox, QRadioButton {{
                spacing: 8px;
                color: {theme['text_primary']};
            }}

            QCheckBox::indicator, QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {theme['border_light']};
                border-radius: 3px;
                background: {theme['surface_light']};
            }}

            QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
                background: {theme['primary']};
                border: 1px solid {theme['primary_dark']};
            }}

            QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
                border: 1px solid {theme['primary_light']};
            }}

            /* === GROUP BOXES === */
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme['border_light']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                color: {theme['text_primary']};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: {theme['primary']};
            }}

            /* === SCROLLBARS MEJORADAS === */
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

            /* === HEADERS Y TÍTULOS === */
            #chat_header {{
                background: {theme['gradient_surface']};
                border-bottom: 1px solid {theme['border_light']};
                border-radius: 12px 12px 0 0;
            }}

            #chat_title {{
                color: {theme['text_primary']};
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }}

            /* === ETIQUETAS DE INFORMACIÓN === */
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
                font-weight: bold;
            }}

            .info_value_error {{
                color: {theme['error']};
                font-weight: bold;
            }}

            .info_value_success {{
                color: {theme['success']};
                font-weight: bold;
            }}

            /* === EFECTOS DE TRANSICIÓN === */
            QWidget {{
                transition: all 0.3s ease;
            }}

            /* === ESTILOS PARA DIÁLOGOS === */
            QDialog {{
                background: {theme['gradient_surface']};
                border: 1px solid {theme['border_light']};
                border-radius: 12px;
            }}

            QMessageBox {{
                background: {theme['gradient_surface']};
                border: 1px solid {theme['border_light']};
                border-radius: 12px;
            }}

            /* === MEJORAS DE ACCESIBILIDAD === */
            QWidget:focus {{
                outline: 2px solid {theme['primary']};
                outline-offset: 2px;
            }}

            /* === ESTILOS PARA BOTONES DE CERRAR/MINIMIZAR === */
            #close_button, #minimize_button {{
                background: transparent;
                border: none;
                color: {theme['text_secondary']};
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 4px;
            }}

            #close_button:hover {{
                background: {theme['error']};
                color: white;
            }}

            #minimize_button:hover {{
                background: {theme['warning']};
                color: white;
            }}
        """

    @classmethod
    def get_theme_preview_html(cls, theme_name: str) -> str:
        """Genera HTML de vista previa para el tema"""
        theme = cls.get_theme(theme_name)

        return f"""
        <div style="font-family: 'Noto Sans', sans-serif; padding: 20px; 
                    background: {theme['background']}; color: {theme['text_primary']}; 
                    border-radius: 12px; border: 2px solid {theme['border_light']};">
            <h3 style="color: {theme['primary']}; margin-bottom: 15px;">
                🎨 {theme['name']} Theme
            </h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                <div style="background: {theme['surface']}; padding: 10px; border-radius: 6px; border: 1px solid {theme['border_light']};">
                    Surface
                </div>
                <div style="background: {theme['primary']}; color: white; padding: 10px; border-radius: 6px;">
                    Primary
                </div>
                <div style="background: {theme['accent']}; padding: 10px; border-radius: 6px;">
                    Accent
                </div>
                <div style="background: {theme['success']}; padding: 10px; border-radius: 6px;">
                    Success
                </div>
            </div>
            <div style="font-size: 12px; color: {theme['text_secondary']};">
                Tipo: {theme['type'].title()} • Colores: {len(theme)}
            </div>
        </div>
        """

    @classmethod
    def export_theme(cls, theme_name: str, filepath: str) -> bool:
        """Exporta un tema a archivo JSON"""
        try:
            theme = cls.get_theme(theme_name)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(theme, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    @classmethod
    def import_theme(cls, filepath: str) -> Dict[str, Any]:
        """Importa un tema desde archivo JSON"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
