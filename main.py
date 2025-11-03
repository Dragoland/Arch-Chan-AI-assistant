#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import requests
import json
import psutil
import platform
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QTextEdit, QLabel, QLineEdit, QComboBox,
                               QMessageBox, QProgressBar, QFrame, QSplitter, QSystemTrayIcon,
                               QMenu, QInputDialog, QDialog, QTabWidget, QCheckBox, 
                               QSlider, QSpinBox, QGroupBox, QScrollArea, QFormLayout,
                               QDialogButtonBox, QToolBar, QStatusBar, QMainWindow,
                               QToolButton, QSizePolicy, QStackedWidget)
from PySide6.QtCore import (Qt, Slot, QTimer, QPropertyAnimation, QEasingCurve, 
                           QPoint, QSize, QThread, Signal, QSettings, QMargins)
from PySide6.QtGui import (QFont, QFontDatabase, QTextCursor, QPalette, QColor,
                          QIcon, QPixmap, QPainter, QAction, QGuiApplication, 
                          QLinearGradient, QPen, QPainterPath)

# Importar desde nuestros módulos
from config import (
    logger,
    PROJECT_PATH, TEMP_PATH, MODELS_PATH, LOGS_PATH,
    DEFAULT_MODELS,
    ConfigManager, AppState, DependencyError,
    KDESU_AVAILABLE
)
from worker import WorkerThread

# Variables globales que serán pobladas por check_dependencies
import config

# --- Verificación de Dependencias Mejorada ---
def find_dependency(cmd):
    """Busca la dependencia usando múltiples métodos"""
    try:
        result = subprocess.run(['which', cmd], capture_output=True, timeout=5, text=True)
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip().split('\n')[0]
            logger.info(f"'{cmd}' encontrado via 'which': {path}")
            return path
    except Exception as e:
        logger.warning(f"Error usando 'which' para {cmd}: {e}")

    try:
        logger.info(f"Búsqueda profunda para '{cmd}' con 'whereis'...")
        result = subprocess.run(['whereis', '-b', cmd], capture_output=True, timeout=5, text=True)
        if result.returncode == 0:
            output = result.stdout.strip()
            if ':' in output:
                paths = output.split(':', 1)[1].strip()
                if paths:
                    for path in paths.split():
                        if os.path.exists(path) and os.access(path, os.X_OK):
                            logger.info(f"'{cmd}' encontrado via 'whereis': {path}")
                            return path
    except Exception as e:
        logger.warning(f"Error usando 'whereis' para {cmd}: {e}")

    common_paths = [
        '/usr/bin', '/usr/local/bin', '/bin', '/usr/sbin',
        '/usr/libexec', '/opt/bin', '/snap/bin'
    ]

    for base_path in common_paths:
        potential_path = os.path.join(base_path, cmd)
        if os.path.exists(potential_path) and os.access(potential_path, os.X_OK):
            logger.info(f"'{cmd}' encontrado en ruta común: {potential_path}")
            return potential_path

    raise FileNotFoundError(f"No se encontró el ejecutable: {cmd}")

def handle_kdesu_special_case():
    """Manejo especial para kdesu - con alternativas robustas"""
    try:
        result = subprocess.run(['kdesu', '--version'], capture_output=True, timeout=5, text=True)
        if result.returncode == 0 or result.returncode == 1:
            logger.info("kdesu funciona como comando de shell")
            config.KDESU_AVAILABLE = 'kdesu'
            return 'kdesu'
    except Exception as e:
        logger.warning(f"kdesu no funciona como comando directo: {e}")

    try:
        kdesu_path = find_dependency('kdesu')
        logger.info(f"kdesu encontrado via find_dependency: {kdesu_path}")
        config.KDESU_AVAILABLE = kdesu_path
        return kdesu_path
    except FileNotFoundError:
        logger.warning("kdesu no encontrado con find_dependency")

    alternatives = ['pkexec', 'gksudo', 'kdesudo', 'beesu']
    for alt in alternatives:
        try:
            result = subprocess.run(['which', alt], capture_output=True, timeout=5, text=True)
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                logger.info(f"Alternativa a kdesu encontrada: {alt} en {path}")
                config.KDESU_AVAILABLE = alt
                return alt
        except Exception:
            continue

    try:
        result = subprocess.run(['kde-cli-tools', '--version'], capture_output=True, timeout=5, text=True)
        if result.returncode != 127:
            logger.info("kde-cli-tools está disponible")
            config.KDESU_AVAILABLE = 'kdesu'
            return 'kdesu'
    except Exception:
        pass

    logger.warning("kdesu y alternativas no disponibles")
    config.KDESU_AVAILABLE = None
    return None

def check_dependencies():
    """Verifica que todas las dependencias necesarias estén disponibles"""
    required_tools = {
        'whisper-cli': 'whisper-cli',
        'piper-tts': 'piper-tts',
        'aplay': 'aplay',
        'rec (sox)': 'rec',
        'ollama': 'ollama',
        'ddgr': 'ddgr',
        'kdialog': 'kdialog'
    }

    missing = []

    for name, cmd in required_tools.items():
        try:
            if name == 'ollama':
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                response.raise_for_status()
            else:
                actual_cmd = find_dependency(cmd)

                if name == 'piper-tts':
                    config.PIPER_EXE = actual_cmd
                elif name == 'whisper-cli':
                    config.WHISPER_EXE = actual_cmd

                if cmd not in ['aplay', 'ddgr', 'rec']:
                    subprocess.run(
                        [actual_cmd, '--version'] if cmd != 'kdialog' else [actual_cmd, '--help'],
                        capture_output=True, timeout=5, check=True
                    )

        except Exception as e:
            logger.error(f"Fallo de dependencia en '{name}': {e}")
            missing.append(name)

    kdesu_result = handle_kdesu_special_case()
    if not kdesu_result:
        logger.warning("kdesu no disponible - los comandos sudo no funcionarán")

    if missing:
        raise DependencyError(f"Herramientas faltantes: {', '.join(missing)}")

    logger.info("Todas las dependencias verificadas correctamente")

# --- Sistema de Temas Mejorado ---
class ArchLinuxTheme:
    """Sistema de temas mejorado para Arch Linux"""
    
    THEMES = {
        'arch-dark': {
            'primary': '#1793D1',
            'primary_dark': '#0E6B9E',
            'primary_light': '#4BB4F0',
            'background': '#2F343F',
            'surface': '#383C4A',
            'surface_light': '#404552',
            'text_primary': '#D3DAE3',
            'text_secondary': '#7C818C',
            'text_muted': '#545A66',
            'accent': '#48B9C7',
            'warning': '#F27835',
            'error': '#F04A50',
            'success': '#33D17A',
            'border': '#1A1E26',
            'border_light': '#4B5162',
            'shadow': 'rgba(0, 0, 0, 0.3)',
            'hover': 'rgba(255, 255, 255, 0.05)',
            'selection': 'rgba(23, 147, 209, 0.3)'
        },
        'arch-light': {
            'primary': '#1793D1',
            'primary_dark': '#0E6B9E',
            'primary_light': '#4BB4F0',
            'background': '#F8F9FA',
            'surface': '#FFFFFF',
            'surface_light': '#F1F3F5',
            'text_primary': '#2F343F',
            'text_secondary': '#7C818C',
            'text_muted': '#A0A6B1',
            'accent': '#48B9C7',
            'warning': '#F27835',
            'error': '#F04A50',
            'success': '#33D17A',
            'border': '#E1E5EB',
            'border_light': '#D1D6DE',
            'shadow': 'rgba(0, 0, 0, 0.1)',
            'hover': 'rgba(0, 0, 0, 0.03)',
            'selection': 'rgba(23, 147, 209, 0.1)'
        },
        'blue-matrix': {
            'primary': '#00FF41',
            'primary_dark': '#008F11',
            'primary_light': '#00FF41',
            'background': '#0D0208',
            'surface': '#0D0208',
            'surface_light': '#003B00',
            'text_primary': '#00FF41',
            'text_secondary': '#008F11',
            'text_muted': '#007700',
            'accent': '#00FF41',
            'warning': '#FF6B00',
            'error': '#FF003C',
            'success': '#00FF41',
            'border': '#008F11',
            'border_light': '#00FF41',
            'shadow': 'rgba(0, 255, 65, 0.2)',
            'hover': 'rgba(0, 255, 65, 0.1)',
            'selection': 'rgba(0, 255, 65, 0.2)'
        }
    }
    
    FONTS = {
        'primary': 'Noto Sans, DejaVu Sans, sans-serif',
        'monospace': 'Hack, Fira Code, DejaVu Sans Mono, monospace',
        'title': 'Noto Sans, Cantarell, sans-serif'
    }
    
    @classmethod
    def get_theme(cls, theme_name='arch-dark'):
        """Obtiene un tema por nombre"""
        return cls.THEMES.get(theme_name, cls.THEMES['arch-dark'])
    
    @classmethod
    def get_stylesheet(cls, theme_name='arch-dark'):
        """Genera la hoja de estilo completa para el tema especificado"""
        theme = cls.get_theme(theme_name)
        
        return f"""
            /* === ESTILOS ARCH LINUX - {theme_name.upper()} === */
            
            /* Ventana principal */
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
            
            /* Diálogos de mensaje */
            QMessageBox {{
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 8px;
            }}
            
            QMessageBox QLabel {{
                color: {theme['text_primary']};
            }}
            
            QMessageBox QPushButton {{
                min-width: 80px;
            }}
            
            /* Group boxes */
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme['text_primary']};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {theme['primary']};
            }}
            
            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {theme['border_light']};
                border-radius: 6px;
                background-color: {theme['surface']};
            }}
            
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            
            QTabBar::tab {{
                background-color: {theme['surface_light']};
                color: {theme['text_secondary']};
                padding: 8px 16px;
                margin: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {theme['primary']};
                color: white;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {theme['hover']};
                color: {theme['text_primary']};
            }}
            
            /* Checkboxes */
            QCheckBox {{
                color: {theme['text_primary']};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {theme['border_light']};
                border-radius: 3px;
                background-color: {theme['surface']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {theme['primary']};
                border: 1px solid {theme['primary_dark']};
            }}
            
            QCheckBox::indicator:hover {{
                border: 1px solid {theme['primary_light']};
            }}
            
            /* Sliders */
            QSlider::groove:horizontal {{
                border: 1px solid {theme['border_light']};
                height: 4px;
                background: {theme['surface_light']};
                border-radius: 2px;
            }}
            
            QSlider::handle:horizontal {{
                background: {theme['primary']};
                border: 1px solid {theme['primary_dark']};
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background: {theme['primary_light']};
            }}
            
            /* Spin boxes */
            QSpinBox {{
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border_light']};
                border-radius: 4px;
                padding: 4px;
                min-width: 60px;
            }}
            
            QSpinBox:hover {{
                border: 1px solid {theme['primary_light']};
            }}
            
            QSpinBox:focus {{
                border: 1px solid {theme['primary']};
            }}
            
            /* Separadores */
            QFrame[frameShape="4"] /* HLine */ {{
                color: {theme['border_light']};
            }}
            
            QFrame[frameShape="5"] /* VLine */ {{
                color: {theme['border_light']};
            }}
        """

# --- Sistema de Monitoreo Mejorado ---
class SystemMonitorThread(QThread):
    """Hilo para monitoreo del sistema en tiempo real mejorado"""
    
    system_update = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.previous_net_io = psutil.net_io_counters()
        
    def run(self):
        while self.running:
            try:
                # Monitorear CPU con promedio
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Monitorear memoria
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used_gb = memory.used / (1024**3)
                memory_total_gb = memory.total / (1024**3)
                
                # Monitorear disco
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                disk_used_gb = disk.used / (1024**3)
                disk_total_gb = disk.total / (1024**3)
                
                # Monitorear red
                net_io = psutil.net_io_counters()
                net_sent = (net_io.bytes_sent - self.previous_net_io.bytes_sent) / 1024  # KB/s
                net_recv = (net_io.bytes_recv - self.previous_net_io.bytes_recv) / 1024  # KB/s
                self.previous_net_io = net_io
                
                # Monitorear temperatura (si está disponible)
                try:
                    temps = psutil.sensors_temperatures()
                    cpu_temp = temps.get('coretemp', [{}])[0].current if 'coretemp' in temps else None
                except:
                    cpu_temp = None
                
                # Monitorear Ollama
                ollama_running = self.check_ollama_status()
                
                # Información del sistema
                system_info = {
                    'cpu': cpu_percent,
                    'memory_percent': memory_percent,
                    'memory_used': memory_used_gb,
                    'memory_total': memory_total_gb,
                    'disk_percent': disk_percent,
                    'disk_used': disk_used_gb,
                    'disk_total': disk_total_gb,
                    'network_sent': net_sent,
                    'network_recv': net_recv,
                    'cpu_temp': cpu_temp,
                    'ollama_running': ollama_running,
                    'timestamp': datetime.now()
                }
                
                self.system_update.emit(system_info)
                
            except Exception as e:
                logger.error(f"Error en monitoreo del sistema: {e}")
            
            self.msleep(2000)  # Actualizar cada 2 segundos
    
    def check_ollama_status(self):
        """Verifica si Ollama está ejecutándose"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.running = False

# --- Diálogo de Configuración Mejorado ---
class ConfigDialog(QDialog):
    """Diálogo de configuración mejorado con pestañas"""
    
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = config_manager.config
        self.setup_ui()
        self.load_current_config()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        self.setWindowTitle("Configuración - Arch-Chan v2.1")
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Pestañas
        self.tabs = QTabWidget()
        
        # Pestaña General
        self.general_tab = self.create_general_tab()
        self.tabs.addTab(self.general_tab, "General")
        
        # Pestaña Audio
        self.audio_tab = self.create_audio_tab()
        self.tabs.addTab(self.audio_tab, "Audio")
        
        # Pestaña Interfaz
        self.ui_tab = self.create_ui_tab()
        self.tabs.addTab(self.ui_tab, "Interfaz")
        
        # Pestaña Avanzado
        self.advanced_tab = self.create_advanced_tab()
        self.tabs.addTab(self.advanced_tab, "Avanzado")
        
        layout.addWidget(self.tabs)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Guardar")
        self.save_button.clicked.connect(self.save_config)
        
        self.cancel_button = QPushButton("❌ Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        self.apply_button = QPushButton("⚡ Aplicar")
        self.apply_button.clicked.connect(self.apply_config)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def create_general_tab(self):
        """Crea la pestaña de configuración general"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de modelo
        model_group = QGroupBox("Modelo de IA")
        model_layout = QFormLayout(model_group)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(['arch-chan', 'arch-chan-lite', 'llama3.2:3b', 'gemma:2b'])
        model_layout.addRow("Modelo principal:", self.model_combo)
        
        self.auto_update_check = QCheckBox("Buscar actualizaciones automáticamente")
        model_layout.addRow(self.auto_update_check)
        
        layout.addWidget(model_group)
        
        # Grupo de comportamiento
        behavior_group = QGroupBox("Comportamiento")
        behavior_layout = QFormLayout(behavior_group)
        
        self.auto_cleanup_check = QCheckBox("Limpieza automática de archivos temporales")
        behavior_layout.addRow(self.auto_cleanup_check)
        
        self.notifications_check = QCheckBox("Mostrar notificaciones del sistema")
        behavior_layout.addRow(self.notifications_check)
        
        self.backup_check = QCheckBox("Crear backups automáticos de configuración")
        behavior_layout.addRow(self.backup_check)
        
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(5, 100)
        self.max_history_spin.setSuffix(" mensajes")
        behavior_layout.addRow("Máximo historial:", self.max_history_spin)
        
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        return tab
        
    def create_audio_tab(self):
        """Crea la pestaña de configuración de audio"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de voz
        voice_group = QGroupBox("Síntesis de Voz")
        voice_layout = QFormLayout(voice_group)
        
        self.voice_enabled_check = QCheckBox("Habilitar síntesis de voz")
        voice_layout.addRow(self.voice_enabled_check)
        
        self.voice_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.voice_volume_slider.setRange(0, 100)
        self.voice_volume_label = QLabel("80%")
        voice_layout.addRow("Volumen de voz:", self.voice_volume_slider)
        voice_layout.addRow("", self.voice_volume_label)
        
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["16000", "22050", "44100"])
        voice_layout.addRow("Frecuencia de muestreo:", self.sample_rate_combo)
        
        self.noise_reduction_check = QCheckBox("Reducción de ruido en audio")
        voice_layout.addRow(self.noise_reduction_check)
        
        layout.addWidget(voice_group)
        
        # Grupo de calidad
        quality_group = QGroupBox("Calidad de Audio")
        quality_layout = QFormLayout(quality_group)
        
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["Baja", "Media", "Alta"])
        quality_layout.addRow("Calidad de audio:", self.audio_quality_combo)
        
        self.silence_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.silence_threshold_slider.setRange(1, 20)
        self.silence_threshold_label = QLabel("5%")
        quality_layout.addRow("Umbral de silencio:", self.silence_threshold_slider)
        quality_layout.addRow("", self.silence_threshold_label)
        
        layout.addWidget(quality_group)
        
        layout.addStretch()
        return tab
        
    def create_ui_tab(self):
        """Crea la pestaña de configuración de interfaz"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de tema
        theme_group = QGroupBox("Apariencia")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Arch Dark", "Arch Light", "Blue Matrix"])
        theme_layout.addRow("Tema:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        self.font_size_spin.setSuffix(" px")
        theme_layout.addRow("Tamaño de fuente:", self.font_size_spin)
        
        self.animations_check = QCheckBox("Habilitar animaciones")
        theme_layout.addRow(self.animations_check)
        
        self.compact_mode_check = QCheckBox("Modo compacto")
        theme_layout.addRow(self.compact_mode_check)
        
        layout.addWidget(theme_group)
        
        # Grupo de ventana
        window_group = QGroupBox("Ventana")
        window_layout = QFormLayout(window_group)
        
        self.sidebar_check = QCheckBox("Mostrar panel lateral")
        window_layout.addRow(self.sidebar_check)
        
        self.tray_check = QCheckBox("Minimizar a bandeja del sistema")
        window_layout.addRow(self.tray_check)
        
        layout.addWidget(window_group)
        
        layout.addStretch()
        return tab
        
    def create_advanced_tab(self):
        """Crea la pestaña de configuración avanzada"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de rendimiento
        performance_group = QGroupBox("Rendimiento")
        performance_layout = QFormLayout(performance_group)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(30, 300)
        self.timeout_spin.setSuffix(" segundos")
        performance_layout.addRow("Timeout de comandos:", self.timeout_spin)
        
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setSuffix(" intentos")
        performance_layout.addRow("Reintentos:", self.retry_spin)
        
        self.cache_check = QCheckBox("Cachear respuestas")
        performance_layout.addRow(self.cache_check)
        
        layout.addWidget(performance_group)
        
        # Grupo de seguridad
        security_group = QGroupBox("Seguridad")
        security_layout = QFormLayout(security_group)
        
        self.sudo_confirm_check = QCheckBox("Confirmar comandos sudo")
        security_layout.addRow(self.sudo_confirm_check)
        
        self.danger_check = QCheckBox("Bloquear comandos peligrosos")
        security_layout.addRow(self.danger_check)
        
        layout.addWidget(security_group)
        
        # Grupo de logs
        log_group = QGroupBox("Registro y Logs")
        log_layout = QFormLayout(log_group)
        
        self.debug_check = QCheckBox("Modo debug (logs detallados)")
        log_layout.addRow(self.debug_check)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        return tab
        
    def load_current_config(self):
        """Carga la configuración actual en los controles"""
        # General
        self.model_combo.setCurrentText(self.config.get('General', 'model', fallback='arch-chan'))
        self.auto_update_check.setChecked(self.config.getboolean('General', 'auto_update', fallback=False))
        self.auto_cleanup_check.setChecked(self.config.getboolean('General', 'auto_cleanup', fallback=True))
        self.notifications_check.setChecked(self.config.getboolean('General', 'notifications', fallback=True))
        self.backup_check.setChecked(self.config.getboolean('General', 'backup_enabled', fallback=True))
        self.max_history_spin.setValue(self.config.getint('General', 'max_history', fallback=20))
        
        # Audio
        self.voice_enabled_check.setChecked(self.config.getboolean('General', 'voice_enabled', fallback=True))
        self.voice_volume_slider.setValue(self.config.getint('Audio', 'voice_volume', fallback=80))
        self.sample_rate_combo.setCurrentText(self.config.get('Audio', 'sample_rate', fallback='22050'))
        self.noise_reduction_check.setChecked(self.config.getboolean('Audio', 'noise_reduction', fallback=True))
        
        audio_quality = self.config.get('Audio', 'audio_quality', fallback='high')
        quality_map = {'low': 'Baja', 'medium': 'Media', 'high': 'Alta'}
        self.audio_quality_combo.setCurrentText(quality_map.get(audio_quality, 'Alta'))
        
        silence_threshold = self.config.get('Audio', 'silence_threshold', fallback='5%').rstrip('%')
        self.silence_threshold_slider.setValue(int(silence_threshold))
        
        # UI
        theme = self.config.get('UI', 'theme', fallback='arch-dark')
        theme_map = {'arch-dark': 'Arch Dark', 'arch-light': 'Arch Light', 'blue-matrix': 'Blue Matrix'}
        self.theme_combo.setCurrentText(theme_map.get(theme, 'Arch Dark'))
        
        self.font_size_spin.setValue(self.config.getint('UI', 'font_size', fallback=11))
        self.animations_check.setChecked(self.config.getboolean('UI', 'animations', fallback=True))
        self.compact_mode_check.setChecked(self.config.getboolean('UI', 'compact_mode', fallback=False))
        self.sidebar_check.setChecked(self.config.getboolean('UI', 'sidebar_visible', fallback=True))
        self.tray_check.setChecked(self.config.getboolean('UI', 'tray_enabled', fallback=True))
        
        # Avanzado
        self.timeout_spin.setValue(self.config.getint('Advanced', 'timeout_duration', fallback=120))
        self.retry_spin.setValue(self.config.getint('Advanced', 'retry_attempts', fallback=3))
        self.cache_check.setChecked(self.config.getboolean('Advanced', 'cache_responses', fallback=True))
        self.sudo_confirm_check.setChecked(self.config.getboolean('Advanced', 'sudo_confirm', fallback=True))
        self.danger_check.setChecked(self.config.getboolean('Advanced', 'block_dangerous', fallback=True))
        self.debug_check.setChecked(self.config.getboolean('Advanced', 'debug_mode', fallback=False))
        
        # Conectar señales para actualizaciones en tiempo real
        self.voice_volume_slider.valueChanged.connect(
            lambda v: self.voice_volume_label.setText(f"{v}%")
        )
        self.silence_threshold_slider.valueChanged.connect(
            lambda v: self.silence_threshold_label.setText(f"{v}%")
        )
        
    def save_config(self):
        """Guarda la configuración y cierra el diálogo"""
        if self.apply_config():
            self.accept()
        
    def apply_config(self):
        """Aplica la configuración sin cerrar el diálogo"""
        try:
            # General
            self.config.set('General', 'model', self.model_combo.currentText())
            self.config.set('General', 'auto_update', str(self.auto_update_check.isChecked()))
            self.config.set('General', 'auto_cleanup', str(self.auto_cleanup_check.isChecked()))
            self.config.set('General', 'notifications', str(self.notifications_check.isChecked()))
            self.config.set('General', 'backup_enabled', str(self.backup_check.isChecked()))
            self.config.set('General', 'max_history', str(self.max_history_spin.value()))
            self.config.set('General', 'voice_enabled', str(self.voice_enabled_check.isChecked()))
            
            # Audio
            self.config.set('Audio', 'voice_volume', str(self.voice_volume_slider.value()))
            self.config.set('Audio', 'sample_rate', self.sample_rate_combo.currentText())
            self.config.set('Audio', 'noise_reduction', str(self.noise_reduction_check.isChecked()))
            
            audio_quality_map = {'Baja': 'low', 'Media': 'medium', 'Alta': 'high'}
            self.config.set('Audio', 'audio_quality', audio_quality_map[self.audio_quality_combo.currentText()])
            self.config.set('Audio', 'silence_threshold', f"{self.silence_threshold_slider.value()}%")
            
            # UI
            theme_map = {'Arch Dark': 'arch-dark', 'Arch Light': 'arch-light', 'Blue Matrix': 'blue-matrix'}
            self.config.set('UI', 'theme', theme_map[self.theme_combo.currentText()])
            self.config.set('UI', 'font_size', str(self.font_size_spin.value()))
            self.config.set('UI', 'animations', str(self.animations_check.isChecked()))
            self.config.set('UI', 'compact_mode', str(self.compact_mode_check.isChecked()))
            self.config.set('UI', 'sidebar_visible', str(self.sidebar_check.isChecked()))
            self.config.set('UI', 'tray_enabled', str(self.tray_check.isChecked()))
            
            # Avanzado
            self.config.set('Advanced', 'timeout_duration', str(self.timeout_spin.value()))
            self.config.set('Advanced', 'retry_attempts', str(self.retry_spin.value()))
            self.config.set('Advanced', 'cache_responses', str(self.cache_check.isChecked()))
            self.config.set('Advanced', 'sudo_confirm', str(self.sudo_confirm_check.isChecked()))
            self.config.set('Advanced', 'block_dangerous', str(self.danger_check.isChecked()))
            self.config.set('Advanced', 'debug_mode', str(self.debug_check.isChecked()))
            
            self.config_manager.save_config()
            
            # Emitir señal para que la aplicación principal se actualice
            if hasattr(self.parent(), 'config_applied'):
                self.parent().config_applied.emit()
                
            QMessageBox.information(self, "Configuración", "✅ Configuración aplicada correctamente")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Error al guardar configuración: {str(e)}")
            return False

# --- Ventana Principal Mejorada ---
class ArchChanApp(QMainWindow):
    """Ventana principal mejorada con interfaz nativa de Arch Linux"""

    # Señales
    config_applied = Signal()

    def __init__(self):
        super().__init__()
        self.chat_history = []
        self.worker_thread = None
        self.current_state = AppState.IDLE
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # Componentes del sistema
        self.system_monitor = SystemMonitorThread()
        self.tray_icon = None
        
        # Configuración inicial
        self.current_theme = self.config.get('UI', 'theme', fallback='arch-dark')
        
        self.setup_ui()
        self.setup_system_monitor()
        self.setup_tray_icon()
        self.apply_theme(self.current_theme)
        
        logger.info("Aplicación Arch-Chan v2.1 con interfaz mejorada inicializada")

    def setup_ui(self):
        """Configura la interfaz de usuario mejorada"""
        self.setWindowTitle("Arch-Chan AI Assistant v2.1")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Panel lateral (colapsable)
        self.side_panel = self.create_side_panel()
        main_layout.addWidget(self.side_panel, 1)  # 25% del ancho

        # Panel principal de chat
        self.chat_panel = self.create_chat_panel()
        main_layout.addWidget(self.chat_panel, 3)  # 75% del ancho

        # Barra de herramientas
        self.setup_toolbar()

        # Barra de estado
        self.setup_statusbar()

        # Conexiones de señales
        self.setup_connections()

        # Mensaje de bienvenida
        self.show_welcome_message()

    def setup_toolbar(self):
        """Configura la barra de herramientas"""
        toolbar = QToolBar("Herramientas Principales")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        # Acciones de la barra de herramientas
        voice_action = QAction("🎤 Voz", self)
        voice_action.setStatusTip("Iniciar grabación de voz")
        voice_action.triggered.connect(self.start_voice_flow)
        toolbar.addAction(voice_action)

        toolbar.addSeparator()

        clear_action = QAction("🗑️ Limpiar", self)
        clear_action.setStatusTip("Limpiar historial del chat")
        clear_action.triggered.connect(self.clear_chat)
        toolbar.addAction(clear_action)

        config_action = QAction("⚙️ Configurar", self)
        config_action.setStatusTip("Abrir configuración")
        config_action.triggered.connect(self.show_config_dialog)
        toolbar.addAction(config_action)

        stop_action = QAction("⏹️ Detener", self)
        stop_action.setStatusTip("Detener operación actual")
        stop_action.triggered.connect(self.stop_worker)
        toolbar.addAction(stop_action)

    def setup_statusbar(self):
        """Configura la barra de estado"""
        statusbar = self.statusBar()
        
        # Estado principal
        self.status_label = QLabel("🟢 Sistema listo - Conectado a Ollama")
        statusbar.addWidget(self.status_label)
        
        # Separador
        statusbar.addPermanentWidget(QLabel("|"))
        
        # Información de modelo
        self.model_status = QLabel("Modelo: arch-chan")
        statusbar.addPermanentWidget(self.model_status)
        
        statusbar.addPermanentWidget(QLabel("|"))
        
        # Estado de voz
        self.voice_status = QLabel("🎤 Voz: Activa")
        statusbar.addPermanentWidget(self.voice_status)

    def create_side_panel(self):
        """Crea el panel lateral mejorado con información del sistema"""
        side_frame = QFrame()
        side_frame.setObjectName("system_info_frame")
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(12, 12, 12, 12)
        side_layout.setSpacing(12)

        # Header del panel lateral
        header_layout = QHBoxLayout()
        
        # Logo y título con mejor diseño
        logo_label = QLabel("🐧")
        logo_label.setObjectName("arch_logo")
        logo_label.setFixedSize(32, 32)
        
        title_label = QLabel("Arch-Chan v2.1")
        title_label.setObjectName("title_label")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Botón para colapsar panel
        self.collapse_button = QToolButton()
        self.collapse_button.setText("◀")
        self.collapse_button.setToolTip("Colapsar panel lateral")
        self.collapse_button.setFixedSize(24, 24)
        self.collapse_button.clicked.connect(self.toggle_side_panel)
        header_layout.addWidget(self.collapse_button)
        
        side_layout.addLayout(header_layout)

        # Separador
        separator = self.create_separator()
        side_layout.addWidget(separator)

        # Información del sistema en tiempo real
        sys_info_label = QLabel("MONITOR DEL SISTEMA")
        sys_info_label.setStyleSheet("color: #1793D1; font-weight: bold; font-size: 10px; letter-spacing: 1px;")
        side_layout.addWidget(sys_info_label)

        # CPU
        cpu_group = self.create_metric_group("CPU", "0%", "info_value")
        side_layout.addWidget(cpu_group)

        # Memoria
        memory_group = self.create_metric_group("Memoria", "0.0/0.0 GB", "info_value")
        side_layout.addWidget(memory_group)

        # Disco
        disk_group = self.create_metric_group("Disco", "0.0/0.0 GB", "info_value")
        side_layout.addWidget(disk_group)

        # Red
        network_group = self.create_metric_group("Red", "↑0.0 ↓0.0 KB/s", "info_value")
        side_layout.addWidget(network_group)

        # Temperatura (si está disponible)
        temp_group = self.create_metric_group("Temperatura", "N/A", "info_value")
        side_layout.addWidget(temp_group)

        # Estado de Ollama
        ollama_group = self.create_metric_group("Ollama", "Verificando...", "info_value")
        side_layout.addWidget(ollama_group)

        # Separador
        side_layout.addWidget(separator)

        # Información de la sesión
        session_label = QLabel("INFORMACIÓN DE SESIÓN")
        session_label.setStyleSheet("color: #1793D1; font-weight: bold; font-size: 10px; letter-spacing: 1px;")
        side_layout.addWidget(session_label)

        # Modelo actual
        model_group = self.create_metric_group("Modelo", "arch-chan", "info_value")
        side_layout.addWidget(model_group)

        # Mensajes en chat
        messages_group = self.create_metric_group("Mensajes", "0", "info_value")
        side_layout.addWidget(messages_group)

        # Tiempo de actividad
        uptime_group = self.create_metric_group("Activo desde", self.get_current_time(), "info_value")
        side_layout.addWidget(uptime_group)

        # Separador
        side_layout.addWidget(separator)

        # Controles rápidos
        controls_label = QLabel("CONTROLES RÁPIDOS")
        controls_label.setStyleSheet("color: #1793D1; font-weight: bold; font-size: 10px; letter-spacing: 1px;")
        side_layout.addWidget(controls_label)

        # Botones de control
        control_layout = QVBoxLayout()
        control_layout.setSpacing(6)

        voice_btn = QPushButton("🎤 Iniciar Voz")
        voice_btn.clicked.connect(self.start_voice_flow)
        control_layout.addWidget(voice_btn)

        clear_btn = QPushButton("🗑️ Limpiar Chat")
        clear_btn.clicked.connect(self.clear_chat)
        control_layout.addWidget(clear_btn)

        config_btn = QPushButton("⚙️ Configuración")
        config_btn.clicked.connect(self.show_config_dialog)
        control_layout.addWidget(config_btn)

        stop_btn = QPushButton("⏹️ Detener Todo")
        stop_btn.clicked.connect(self.stop_worker)
        control_layout.addWidget(stop_btn)

        side_layout.addLayout(control_layout)

        # Espacio flexible
        side_layout.addStretch()

        # Información de versión
        version_layout = QHBoxLayout()
        version_label = QLabel("v2.1 - Arch Linux Native")
        version_label.setStyleSheet("color: #7C818C; font-size: 9px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_layout.addWidget(version_label)
        side_layout.addLayout(version_layout)

        side_frame.setLayout(side_layout)
        return side_frame

    def create_metric_group(self, label, value, value_class="info_value"):
        """Crea un grupo de métrica para el panel lateral"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 2, 6, 2)
        
        label_widget = QLabel(f"{label}:")
        label_widget.setProperty("class", "info_label")
        label_widget.setFixedWidth(80)
        
        value_widget = QLabel(value)
        value_widget.setProperty("class", value_class)
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)
        
        # Guardar referencia para actualizaciones
        setattr(self, f"{label.lower()}_value", value_widget)
        
        return widget

    def create_separator(self):
        """Crea un separador estilizado"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #4B5162; margin: 4px 0px;")
        separator.setFixedHeight(1)
        return separator

    def create_chat_panel(self):
        """Crea el panel principal de chat mejorado"""
        chat_frame = QFrame()
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(8)

        # Header del chat
        header_frame = QFrame()
        header_frame.setObjectName("header_frame")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 10, 16, 10)

        # Título del chat con icono
        chat_title_layout = QHBoxLayout()
        chat_icon = QLabel("💬")
        chat_icon.setStyleSheet("font-size: 16px;")
        chat_title = QLabel("Asistente de IA - Arch Linux")
        chat_title.setObjectName("title_label")
        chat_title.setStyleSheet("font-size: 14px;")
        
        chat_title_layout.addWidget(chat_icon)
        chat_title_layout.addWidget(chat_title)
        chat_title_layout.addStretch()

        # Selector de modelo en header
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Modelo:"))
        
        self.model_selector = QComboBox()
        self.model_selector.setObjectName("model_selector")
        self.model_selector.setFixedWidth(150)
        self.load_available_models()
        
        saved_model = self.config.get('General', 'model', fallback='arch-chan')
        index = self.model_selector.findText(saved_model)
        if index >= 0:
            self.model_selector.setCurrentIndex(index)
        
        self.model_selector.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_selector)

        header_layout.addLayout(chat_title_layout)
        header_layout.addStretch()
        header_layout.addLayout(model_layout)

        header_frame.setLayout(header_layout)
        chat_layout.addWidget(header_frame)

        # Área de chat con scroll mejorado
        self.chat_area = QTextEdit()
        self.chat_area.setObjectName("chat_area")
        self.chat_area.setReadOnly(True)
        self.chat_area.document().setDocumentMargin(8)
        chat_layout.addWidget(self.chat_area)

        # Barra de progreso con animación
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        chat_layout.addWidget(self.progress_bar)

        # Panel de estado mejorado
        status_frame = QFrame()
        status_frame.setObjectName("status_frame")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(12, 8, 12, 8)

        self.status_label = QLabel("🟢 Sistema listo - Conectado a Ollama")
        self.status_label.setObjectName("status_label")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        # Indicadores de estado
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(12)

        self.voice_indicator = QLabel("🎤 Voz: Activa")
        self.voice_indicator.setStyleSheet("color: #33D17A; font-size: 10px;")
        indicators_layout.addWidget(self.voice_indicator)

        self.connection_indicator = QLabel("🌐 Conectado")
        self.connection_indicator.setStyleSheet("color: #33D17A; font-size: 10px;")
        indicators_layout.addWidget(self.connection_indicator)

        status_layout.addLayout(indicators_layout)

        status_frame.setLayout(status_layout)
        chat_layout.addWidget(status_frame)

        # Panel de controles de entrada mejorado
        input_frame = QFrame()
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        # Botón de voz con estado
        self.voice_button = QPushButton("🎤 Voz")
        self.voice_button.setObjectName("voice_button")
        self.voice_button.setFixedWidth(80)
        self.voice_button.setToolTip("Iniciar grabación de voz (Ctrl+V)")

        # Campo de entrada mejorado
        self.text_input = QLineEdit()
        self.text_input.setObjectName("text_input")
        self.text_input.setPlaceholderText("Escribe tu mensaje o presiona el botón de voz...")
        self.text_input.setToolTip("Presiona Enter para enviar o Ctrl+V para voz")

        # Botón de enviar
        self.send_button = QPushButton("📤 Enviar")
        self.send_button.setObjectName("send_button")
        self.send_button.setFixedWidth(80)
        self.send_button.setToolTip("Enviar mensaje (Enter)")

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

        input_frame.setLayout(input_layout)
        chat_layout.addWidget(input_frame)

        chat_frame.setLayout(chat_layout)
        return chat_frame

    def setup_connections(self):
        """Configura las conexiones de señales y slots"""
        # Conexiones de botones
        self.voice_button.clicked.connect(self.start_voice_flow)
        self.send_button.clicked.connect(self.start_text_flow)
        self.text_input.returnPressed.connect(self.start_text_flow)
        self.stop_button.clicked.connect(self.stop_worker)

        # Atajos de teclado
        self.text_input.returnPressed.connect(self.start_text_flow)
        
        # Timer para animaciones
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_animation)
        self.status_animation_state = 0

        # Timer para actualizar hora
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(60000)  # Actualizar cada minuto

        # Señal de configuración aplicada
        self.config_applied.connect(self.on_config_applied)

    def setup_system_monitor(self):
        """Configura el monitoreo del sistema"""
        self.system_monitor.system_update.connect(self.update_system_info)
        self.system_monitor.start()

    def setup_tray_icon(self):
        """Configura el icono de system tray"""
        if QSystemTrayIcon.isSystemTrayAvailable() and self.config.getboolean('UI', 'tray_enabled', fallback=True):
            self.tray_icon = QSystemTrayIcon(self)
            
            # Crear icono
            pixmap = self.create_tray_icon()
            self.tray_icon.setIcon(QIcon(pixmap))
            
            # Crear menú de tray
            tray_menu = QMenu()
            
            show_action = QAction("Mostrar", self)
            show_action.triggered.connect(self.show_normal)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Ocultar", self)  
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Salir", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            self.tray_icon.show()
            
            self.tray_icon.setToolTip("Arch-Chan AI Assistant v2.1")

    def create_tray_icon(self):
        """Crea un icono para la bandeja del sistema"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar logo de Arch Linux
        painter.setBrush(QColor(23, 147, 209))  # Azul Arch
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        
        # Dibujar 'A' de Arch
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        
        painter.end()
        return pixmap

    def tray_icon_activated(self, reason):
        """Maneja clicks en el icono del tray"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show_normal()

    def show_normal(self):
        """Muestra la ventana normal"""
        self.show()
        self.raise_()
        self.activateWindow()

    @Slot(dict)
    def update_system_info(self, system_info):
        """Actualiza la información del sistema en la UI"""
        # CPU
        cpu_text = f"{system_info['cpu']:.1f}%"
        cpu_class = "info_value_warning" if system_info['cpu'] > 80 else "info_value"
        if hasattr(self, 'cpu_value'):
            self.cpu_value.setText(cpu_text)
            self.cpu_value.setProperty("class", cpu_class)
            self.cpu_value.style().unpolish(self.cpu_value)
            self.cpu_value.style().polish(self.cpu_value)
        
        # Memoria
        memory_text = f"{system_info['memory_used']:.1f}/{system_info['memory_total']:.1f} GB"
        memory_class = "info_value_warning" if system_info['memory_percent'] > 80 else "info_value"
        if hasattr(self, 'memoria_value'):
            self.memoria_value.setText(memory_text)
            self.memoria_value.setProperty("class", memory_class)
            self.memoria_value.style().unpolish(self.memoria_value)
            self.memoria_value.style().polish(self.memoria_value)
        
        # Disco
        disk_text = f"{system_info['disk_used']:.1f}/{system_info['disk_total']:.1f} GB"
        disk_class = "info_value_warning" if system_info['disk_percent'] > 90 else "info_value"
        if hasattr(self, 'disco_value'):
            self.disco_value.setText(disk_text)
            self.disco_value.setProperty("class", disk_class)
            self.disco_value.style().unpolish(self.disco_value)
            self.disco_value.style().polish(self.disco_value)
        
        # Red
        net_text = f"↑{system_info['network_sent']:.1f} ↓{system_info['network_recv']:.1f} KB/s"
        if hasattr(self, 'red_value'):
            self.red_value.setText(net_text)
        
        # Temperatura
        temp_text = f"{system_info['cpu_temp']:.1f}°C" if system_info['cpu_temp'] else "N/A"
        temp_class = "info_value_error" if system_info['cpu_temp'] and system_info['cpu_temp'] > 80 else "info_value"
        if hasattr(self, 'temperatura_value'):
            self.temperatura_value.setText(temp_text)
            self.temperatura_value.setProperty("class", temp_class)
            self.temperatura_value.style().unpolish(self.temperatura_value)
            self.temperatura_value.style().polish(self.temperatura_value)
        
        # Ollama
        ollama_text = "🟢 Conectado" if system_info['ollama_running'] else "🔴 Desconectado"
        ollama_class = "info_value_success" if system_info['ollama_running'] else "info_value_error"
        if hasattr(self, 'ollama_value'):
            self.ollama_value.setText(ollama_text)
            self.ollama_value.setProperty("class", ollama_class)
            self.ollama_value.style().unpolish(self.ollama_value)
            self.ollama_value.style().polish(self.ollama_value)
            
        # Actualizar indicadores en barra de estado
        self.connection_indicator.setText("🌐 Conectado" if system_info['ollama_running'] else "🌐 Desconectado")
        self.connection_indicator.setStyleSheet(
            "color: #33D17A;" if system_info['ollama_running'] else "color: #F04A50;"
        )

    def load_available_models(self):
        """Carga los modelos disponibles desde Ollama"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                preferred_models = ['arch-chan', 'arch-chan-lite', 'llama3.2:3b', 'gemma:2b']
                for model in preferred_models:
                    if any(model in avail for avail in available_models):
                        self.model_selector.addItem(model)
                
                # Actualizar información lateral
                if self.model_selector.count() > 0:
                    if hasattr(self, 'modelo_value'):
                        self.modelo_value.setText(self.model_selector.currentText())
                    
                    self.model_status.setText(f"Modelo: {self.model_selector.currentText()}")
                
                logger.info(f"Modelos cargados: {[self.model_selector.itemText(i) for i in range(self.model_selector.count())]}")
            else:
                self.model_selector.addItems(DEFAULT_MODELS)
                if hasattr(self, 'modelo_value'):
                    self.modelo_value.setText(self.model_selector.currentText())
                logger.warning("No se pudieron cargar modelos de Ollama, usando lista por defecto")
        except Exception as e:
            logger.error(f"Error cargando modelos: {e}")
            self.model_selector.addItems(DEFAULT_MODELS)
            if hasattr(self, 'modelo_value'):
                self.modelo_value.setText(self.model_selector.currentText())

    def on_model_changed(self, model_name):
        """Maneja el cambio de modelo"""
        if hasattr(self, 'modelo_value'):
            self.modelo_value.setText(model_name)
        self.model_status.setText(f"Modelo: {model_name}")
        self.save_model_preference(model_name)
        logger.info(f"Modelo cambiado a: {model_name}")

    def add_chat_message(self, sender, message, is_tool=False):
        """Añade un mensaje al chat con formato mejorado"""
        theme = ArchLinuxTheme.get_theme(self.current_theme)
        
        if is_tool:
            # Formato para logs de herramientas
            html = f"""
            <div style='margin: 12px 0; padding: 10px; background-color: {theme['surface']}; 
                        border: 1px solid {theme['border_light']}; border-radius: 6px; 
                        box-shadow: 0 1px 3px {theme['shadow']};'>
                <div style='color: {theme['primary']}; font-weight: bold; font-size: 10px; 
                           margin-bottom: 6px;'>🔧 {sender}</div>
                <pre style='color: {theme['text_primary']}; font-family: {ArchLinuxTheme.FONTS['monospace']}; 
                           font-size: 10px; margin: 0; white-space: pre-wrap; 
                           background-color: {theme['background']}; padding: 8px; 
                           border-radius: 4px; border: 1px solid {theme['border']};'>{message}</pre>
            </div>
            """
        else:
            is_user = sender == "Usuario"
            alignment = "right" if is_user else "left"
            bg_color = theme['primary'] if is_user else theme['surface_light']
            text_color = "white" if is_user else theme['text_primary']
            bubble_style = "border-top-right-radius: 2px;" if is_user else "border-top-left-radius: 2px;"
            
            html = f"""
            <div style='margin: 12px 0; text-align: {alignment};'>
                <div style='display: inline-block; max-width: 75%; text-align: left;'>
                    <div style='background-color: {bg_color}; color: {text_color}; 
                               padding: 10px 14px; border-radius: 12px; {bubble_style}
                               font-size: 11px; line-height: 1.4; 
                               box-shadow: 0 1px 2px {theme['shadow']};'>
                        {message.replace(chr(10), '<br>')}
                    </div>
                    <div style='color: {theme['text_muted']}; font-size: 9px; 
                               padding: 4px 8px 2px 8px;'>
                        {datetime.now().strftime("%H:%M")} • {sender}
                    </div>
                </div>
            </div>
            """
        
        # Mantener el cursor al final
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_area.setTextCursor(cursor)
        
        self.chat_area.append(html)
        
        # Auto-scroll al final
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Actualizar contador de mensajes
        if not is_tool and message.strip():
            self.add_to_chat_history('user' if sender == 'Usuario' else 'assistant', message)
            if hasattr(self, 'mensajes_value'):
                self.mensajes_value.setText(str(len(self.chat_history)))

    def add_to_chat_history(self, role, content):
        """Añade un mensaje al historial manteniendo límites"""
        self.chat_history.append({'role': role, 'content': content})

        max_history = self.config.getint('General', 'max_history', fallback=20)
        if len(self.chat_history) > max_history:
            self.chat_history = self.chat_history[-max_history:]

    def show_welcome_message(self):
        """Muestra el mensaje de bienvenida"""
        welcome_msg = """
        <div style='text-align: center; margin: 20px 0;'>
            <h3 style='color: #1793D1; margin-bottom: 10px;'>¡Bienvenido a Arch-Chan v2.1! 🐧</h3>
            <p style='color: #7C818C; line-height: 1.5;'>
                Tu asistente de IA nativo de Arch Linux<br>
                <strong>Características mejoradas:</strong>
            </p>
            <div style='text-align: left; display: inline-block; margin: 10px 0;'>
                <div style='margin: 4px 0;'>• 💬 <strong>Conversación inteligente</strong> en español</div>
                <div style='margin: 4px 0;'>• ⚡ <strong>Ejecución segura</strong> de comandos shell</div>
                <div style='margin: 4px 0;'>• 🔍 <strong>Búsquedas web</strong> en tiempo real</div>
                <div style='margin: 4px 0;'>• 🎤 <strong>Entrada por voz</strong> mejorada</div>
                <div style='margin: 4px 0;'>• 🔒 <strong>Confirmación para comandos sudo</strong></div>
                <div style='margin: 4px 0;'>• 📊 <strong>Monitoreo del sistema</strong> en tiempo real</div>
                <div style='margin: 4px 0;'>• 🎨 <strong>Múltiples temas</strong> personalizables</div>
            </div>
            <p style='color: #7C818C; font-style: italic; margin-top: 15px;'>
                ¡Estoy listo para ayudarte con Arch Linux! Escribe un mensaje o usa el botón de voz.
            </p>
        </div>
        """
        
        self.chat_area.setHtml(welcome_msg)
        logger.info("Mensaje de bienvenida mostrado")

    @Slot()
    def start_voice_flow(self):
        """Inicia el flujo de conversación por voz"""
        if self.current_state != AppState.IDLE:
            self.show_warning("Espera", "Ya hay una operación en curso. Espera a que termine.")
            return

        self.set_state(AppState.LISTENING)
        self.disable_controls(True)
        self.voice_button.setText("🔴 Grabando...")
        self.set_status("🎤 Grabando audio... Habla ahora")
        self.voice_indicator.setText("🎤 Grabando...")
        self.voice_indicator.setStyleSheet("color: #F27835;")

        selected_model = self.model_selector.currentText()
        self.save_model_preference(selected_model)

        self.worker_thread = WorkerThread(
            chat_history=self.chat_history,
            model_name=selected_model,
            config=self.config
        )
        self.connect_worker_signals()
        self.worker_thread.start()

        self.start_status_animation()

    @Slot()
    def start_text_flow(self):
        """Inicia el flujo de conversación por texto"""
        if self.current_state != AppState.IDLE:
            self.show_warning("Espera", "Ya hay una operación en curso. Espera a que termine.")
            return

        user_prompt = self.text_input.text().strip()
        if not user_prompt:
            self.show_warning("Entrada vacía", "Por favor, escribe un mensaje antes de enviar.")
            return

        self.set_state(AppState.PROCESSING)
        self.disable_controls(True)
        self.text_input.clear()
        self.add_chat_message("Usuario", user_prompt)

        selected_model = self.model_selector.currentText()
        self.save_model_preference(selected_model)

        self.worker_thread = WorkerThread(
            chat_history=self.chat_history,
            text_prompt=user_prompt,
            model_name=selected_model,
            config=self.config
        )
        self.connect_worker_signals()
        self.worker_thread.start()

        self.start_status_animation()

    def save_model_preference(self, model_name):
        """Guarda la preferencia de modelo"""
        self.config.set('General', 'model', model_name)
        self.config_manager.save_config()

    def disable_controls(self, disabled=True):
        """Habilita o deshabilita los controles de la UI"""
        self.voice_button.setEnabled(not disabled)
        self.send_button.setEnabled(not disabled)
        self.text_input.setEnabled(not disabled)
        self.model_selector.setEnabled(not disabled)
        self.stop_button.setEnabled(disabled)

        if disabled:
            self.voice_button.setStyleSheet("background-color: #7C818C;")
            self.send_button.setStyleSheet("background-color: #7C818C;")
        else:
            # Restaurar estilos normales
            self.apply_theme(self.current_theme)

    def start_status_animation(self):
        """Inicia la animación de estado"""
        self.status_animation_state = 0
        self.status_timer.start(500)
        self.progress_bar.setVisible(True)

    def stop_status_animation(self):
        """Detiene la animación de estado"""
        self.status_timer.stop()
        self.progress_bar.setVisible(False)

    @Slot()
    def update_status_animation(self):
        """Actualiza la animación de estado"""
        animations = ['⏳ Procesando', '⏳ Procesando.', '⏳ Procesando..', '⏳ Procesando...']
        self.status_animation_state = (self.status_animation_state + 1) % len(animations)
        self.set_status(animations[self.status_animation_state])

    @Slot()
    def update_clock(self):
        """Actualiza la hora en el panel lateral"""
        if hasattr(self, 'activo_desde_value'):
            self.activo_desde_value.setText(self.get_current_time())

    def get_current_time(self):
        """Obtiene la hora actual formateada"""
        return datetime.now().strftime("%H:%M")

    @Slot(str)
    def set_status(self, status):
        """Actualiza el texto de estado"""
        self.status_label.setText(status)

    @Slot(int)
    def update_progress(self, value):
        """Actualiza la barra de progreso"""
        if value < 0:
            self.progress_bar.setVisible(False)
        else:
            self.stop_status_animation()
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(value)

    def connect_worker_signals(self):
        """Conecta las señales del worker thread"""
        if not self.worker_thread:
            return
            
        self.worker_thread.update_status.connect(self.set_status)
        self.worker_thread.add_conversation_log.connect(self.add_chat_message)
        self.worker_thread.flow_finished.connect(self.on_worker_finished)
        self.worker_thread.sudo_confirmation_required.connect(self.show_sudo_confirmation)
        self.worker_thread.add_tool_log.connect(self.on_add_tool_log)
        self.worker_thread.error_occurred.connect(self.on_error_occurred)
        self.worker_thread.progress_update.connect(self.update_progress)

    def disconnect_worker_signals(self):
        """Desconecta todas las señales del worker thread"""
        if not self.worker_thread:
            return
            
        try:
            self.worker_thread.update_status.disconnect(self.set_status)
            self.worker_thread.add_conversation_log.disconnect(self.add_chat_message)
            self.worker_thread.flow_finished.disconnect(self.on_worker_finished)
            self.worker_thread.sudo_confirmation_required.disconnect(self.show_sudo_confirmation)
            self.worker_thread.add_tool_log.disconnect(self.on_add_tool_log)
            self.worker_thread.error_occurred.disconnect(self.on_error_occurred)
            try:
                self.worker_thread.progress_update.disconnect(self.update_progress)
            except TypeError:
                pass
        except TypeError as e:
            logger.warning(f"Error al desconectar señales: {e}")

    @Slot(str, str)
    def on_add_tool_log(self, command, raw_output):
        """Muestra el log de herramientas ejecutadas"""
        tool_message = f"Comando: {command}\n\nSalida:\n{raw_output}"
        self.add_chat_message("Herramienta Ejecutada", tool_message, is_tool=True)

    @Slot(str, str)
    def on_worker_finished(self, user_prompt, final_response_content):
        """Maneja la finalización del worker thread"""
        self.set_state(AppState.IDLE)
        self.disable_controls(False)
        self.voice_button.setText("🎤 Voz")
        self.set_status("🟢 Sistema listo")
        self.voice_indicator.setText("🎤 Voz: Activa")
        self.voice_indicator.setStyleSheet("color: #33D17A;")
        self.stop_status_animation()

        self.disconnect_worker_signals()

        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None

        if user_prompt and self.config.getboolean('General', 'notifications', fallback=True):
            self.send_notification(
                "Arch-Chan - Tarea completada",
                f"Procesado: {user_prompt[:30]}..."
            )

        logger.info("Flujo de trabajo completado")

    @Slot(str)
    def on_error_occurred(self, error_msg):
        """Maneja errores del worker thread"""
        self.add_chat_message("Sistema", f"❌ Error: {error_msg}")
        self.voice_indicator.setText("🎤 Voz: Error")
        self.voice_indicator.setStyleSheet("color: #F04A50;")
        logger.error(f"Error en worker thread: {error_msg}")

    def send_notification(self, title, message):
        """Envía una notificación del sistema"""
        try:
            kdialog_path = find_dependency('kdialog')
            subprocess.Popen([kdialog_path, '--title', title, '--passivepopup', message, '3'])
        except Exception as e:
            logger.warning(f"No se pudo enviar notificación: {e}")

    @Slot(str)
    def show_sudo_confirmation(self, command):
        """Muestra diálogo de confirmación para comandos sudo"""
        self.activateWindow()
        self.raise_()

        if KDESU_AVAILABLE is None:
            QMessageBox.warning(
                self,
                '⚠️ Comandos Sudo No Disponibles',
                f"Se requiere sudo pero no hay herramienta gráfica disponible.\n\n"
                f"Comando: <b>{command}</b>\n\n"
                f"Para habilitar comandos sudo, instala 'kde-cli-tools' o 'polkit'.",
                QMessageBox.StandardButton.Ok
            )
            if self.worker_thread:
                self.worker_thread.on_sudo_response(False)
            return

        tool_name = os.path.basename(KDESU_AVAILABLE)
        reply = QMessageBox.question(
            self,
            '🔐 Confirmación de Sudo',
            f"¿Permitir que Arch-Chan ejecute este comando?\n\n"
            f"<b>Comando:</b>\n<code>{command}</code>\n\n"
            f"Usando: <b>{tool_name}</b>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if self.worker_thread:
            self.worker_thread.on_sudo_response(reply == QMessageBox.StandardButton.Yes)

    @Slot()
    def stop_worker(self):
        """Detiene el worker thread actual"""
        self.set_status("🛑 Deteniendo...")
        self.stop_status_animation()

        if self.worker_thread:
            self.worker_thread.stop_all()

        logger.info("Worker thread detenido por el usuario")

    def set_state(self, new_state):
        """Actualiza el estado de la aplicación"""
        old_state = self.current_state
        self.current_state = new_state
        logger.info(f"Cambio de estado: {old_state} -> {new_state}")

    def clear_chat(self):
        """Limpia el historial del chat"""
        reply = QMessageBox.question(
            self,
            'Limpiar Chat',
            '¿Estás seguro de que quieres limpiar el historial del chat?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_area.clear()
            self.chat_history.clear()
            if hasattr(self, 'mensajes_value'):
                self.mensajes_value.setText("0")
            self.show_welcome_message()
            logger.info("Chat limpiado por el usuario")

    def show_config_dialog(self):
        """Muestra el diálogo de configuración mejorado"""
        dialog = ConfigDialog(self, self.config_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Recargar configuración
            self.config = self.config_manager.load_config()
            self.apply_theme(self.config.get('UI', 'theme', fallback='arch-dark'))

    @Slot()
    def on_config_applied(self):
        """Maneja la aplicación de nueva configuración"""
        self.config = self.config_manager.load_config()
        self.apply_theme(self.config.get('UI', 'theme', fallback='arch-dark'))

    def apply_theme(self, theme_name):
        """Aplica un tema a la aplicación"""
        self.current_theme = theme_name
        stylesheet = ArchLinuxTheme.get_stylesheet(theme_name)
        self.setStyleSheet(stylesheet)
        
        # Actualizar también los widgets hijos si es necesario
        for child in self.findChildren(QWidget):
            child.setStyleSheet(stylesheet)

    def toggle_side_panel(self):
        """Alterna la visibilidad del panel lateral"""
        if self.side_panel.isVisible():
            self.side_panel.hide()
            self.collapse_button.setText("▶")
            self.collapse_button.setToolTip("Expandir panel lateral")
        else:
            self.side_panel.show()
            self.collapse_button.setText("◀")
            self.collapse_button.setToolTip("Colapsar panel lateral")

    def show_warning(self, title, message):
        """Muestra un mensaje de advertencia"""
        QMessageBox.warning(self, title, message)

    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        logger.info("Cerrando aplicación Arch-Chan v2.1...")
        
        # Detener monitoreo del sistema
        if self.system_monitor.isRunning():
            self.system_monitor.stop_monitoring()
            self.system_monitor.wait(2000)
        
        # Detener worker thread si está ejecutándose
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop_all()
            self.worker_thread.wait(2000)

        # Guardar configuración
        self.config_manager.save_config()
        
        # Ocultar tray icon
        if self.tray_icon:
            self.tray_icon.hide()
            
        event.accept()

    def keyPressEvent(self, event):
        """Maneja eventos de teclado"""
        if event.key() == Qt.Key.Key_Escape and self.worker_thread:
            self.stop_worker()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
            self.start_voice_flow()
        elif event.key() == Qt.Key.Key_Return and self.text_input.hasFocus():
            self.start_text_flow()
        else:
            super().keyPressEvent(event)

# --- Punto de Entrada Principal ---
def main():
    """Función principal de la aplicación"""
    app = QApplication(sys.argv)
    app.setApplicationName("Arch-Chan AI Assistant")
    app.setApplicationVersion("2.1")
    app.setOrganizationName("Arch-Chan")

    try:
        # Crear directorios necesarios
        for path in [PROJECT_PATH, TEMP_PATH, MODELS_PATH, LOGS_PATH]:
            Path(path).mkdir(parents=True, exist_ok=True)

        logger.info("Directorios de la aplicación verificados/creados")

        # Verificar dependencias
        logger.info("Verificando dependencias...")
        check_dependencies()

        # Configurar aplicación
        app.setStyle("Fusion")
        
        # Configurar fuente por defecto
        font = QFont("Noto Sans", 10)
        app.setFont(font)

        # Crear y mostrar ventana principal
        window = ArchChanApp()
        window.show()

        logger.info("Aplicación Arch-Chan v2.1 con interfaz mejorada iniciada correctamente")

        # Ejecutar loop principal
        return app.exec()

    except DependencyError as e:
        logger.error(f"Error de dependencias: {e}")
        missing_tools_str = str(e).split(': ')[1]

        QMessageBox.critical(
            None,
            "❌ Error de Dependencias - Arch-Chan",
            f"<b>Herramientas faltantes:</b> {missing_tools_str}<br><br>"
            f"Por favor, instala las herramientas faltantes y reinicia la aplicación.<br>"
            f"<code>sudo pacman -S whisper-cli piper-tts sox ollama ddgr kdialog</code>",
            QMessageBox.StandardButton.Ok
        )
        return 1
    except Exception as e:
        logger.error(f"Error inicializando la aplicación: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "❌ Error Inicial - Arch-Chan",
            f"<b>Error inesperado:</b><br>{str(e)}<br><br>Revisa los logs para más detalles.",
            QMessageBox.StandardButton.Ok
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())