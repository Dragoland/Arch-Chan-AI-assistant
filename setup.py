#!/usr/bin/env python3

import os

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="arch-chan-ai-assistant",
    version="2.1.0",
    author="Dragoland",
    author_email="dragoland@protonmail.com",
    description="Una asistente de IA nativa para Arch Linux con interfaz gráfica integrada",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Dragoland/Arch-Chan-AI-assistant",
    packages=find_packages(),
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
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "arch-chan=main:main",
            "arch-chan-setup-models=setup_models:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "*.md",
            "*.txt",
            "*.desktop",
            "*.sh",
            "*.Modelfile",
        ],
    },
    keywords="ai assistant arch-linux ollama voice speech",
    project_urls={
        "Bug Reports": "https://github.com/Dragoland/Arch-Chan-AI-assistant/issues",
        "Source": "https://github.com/Dragoland/Arch-Chan-AI-assistant",
        "Documentation": "https://github.com/Dragoland/Arch-Chan-AI-assistant#readme",
    },
)
