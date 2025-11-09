#!/usr/bin/env python3

import os
import sys
from pathlib import Path

from setuptools import find_packages, setup

# Verificar versión de Python
if sys.version_info < (3, 8):
    sys.exit("Python 3.8 o superior es requerido para Arch-Chan AI Assistant")


def read_file(filename):
    """Lee el contenido de un archivo"""
    try:
        with open(filename, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""


def get_requirements():
    """Obtiene la lista de dependencias"""
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        with open(requirements_file, "r", encoding="utf-8") as fh:
            return [
                line.strip() for line in fh if line.strip() and not line.startswith("#")
            ]
    return []


# Metadatos del proyecto
NAME = "arch-chan-ai-assistant"
VERSION = "2.1.0"
AUTHOR = "Dragoland"
AUTHOR_EMAIL = "dragoland@protonmail.com"
DESCRIPTION = (
    "Una asistente de IA nativa para Arch Linux con interfaz gráfica integrada"
)
LONG_DESCRIPTION = read_file("README.md")
URL = "https://github.com/Dragoland/Arch-Chan-AI-assistant"
REQUIREMENTS = get_requirements()

# Encontrar todos los paquetes
PACKAGES = find_packages(
    include=["*", "core.*", "ui.*", "services.*", "utils.*", "workers.*"]
)

# Archivos de datos a incluir
DATA_FILES = [
    ("share/applications", ["arch-chan.desktop"]),
    ("share/icons/hicolor/256x256/apps", ["assets/arch-chan.png"]),
    ("share/arch-chan", ["README.md", "CHANGELOG.md", "LICENSE"]),
]

# Scripts de consola
CONSOLE_SCRIPTS = [
    "arch-chan=main:main",
]

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=URL,
    packages=PACKAGES,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Desktop Environment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
    python_requires=">=3.8",
    install_requires=REQUIREMENTS,
    entry_points={
        "console_scripts": CONSOLE_SCRIPTS,
    },
    include_package_data=True,
    package_data={
        "": [
            "*.md",
            "*.txt",
            "*.desktop",
            "*.sh",
            "*.Modelfile",
            "*.ini",
            "assets/*.png",
            "assets/*.ico",
            "themes/*.qss",
            "models/*.*",
        ],
    },
    data_files=DATA_FILES,
    keywords="ai assistant arch-linux ollama voice speech qt pyside6",
    project_urls={
        "Bug Reports": f"{URL}/issues",
        "Source": URL,
        "Documentation": f"{URL}#readme",
        "Releases": f"{URL}/releases",
    },
    options={
        "build_exe": {
            "includes": [
                "PySide6.QtCore",
                "PySide6.QtGui",
                "PySide6.QtWidgets",
                "requests",
                "psutil",
            ],
            "excludes": ["tkinter"],
        }
    },
)
