# Maintainer: Dragoland <dragoland@protonmail.com>
pkgname=arch-chan-ai-assistant
pkgver=2.1.0
pkgrel=1
pkgdesc="Una asistente de IA nativa para Arch Linux con interfaz gráfica integrada"
arch=('x86_64')
url="https://github.com/Dragoland/Arch-Chan-AI-assistant"
license=('MIT')
depends=(
    'python-requests'
    'python-psutil'
    'whisper.cpp'
    'piper-tts'
    'sox'
    'ollama'
    'ddgr'
    'kdialog'
    'noto-fonts'
    'ttf-hack'
    'git'
    'base-devel'
)
makedepends=('python-setuptools')
source=("$pkgname-$pkgver.tar.gz::https://github.com/Dragoland/Arch-Chan-AI-assistant/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')  # Actualizar con el hash real al crear el release

prepare() {
    cd "$srcdir/Arch-Chan-AI-assistant-$pkgver"
    # Asegurar que los scripts tengan permisos de ejecución
    chmod +x install_arch_chan.sh
    chmod +x update_arch_chan.sh
    chmod +x setup_models.py
}

package() {
    cd "$srcdir/Arch-Chan-AI-assistant-$pkgver"
    
    # Crear directorios necesarios
    install -d "$pkgdir/usr/bin"
    install -d "$pkgdir/usr/share/applications"
    install -d "$pkgdir/usr/share/arch-chan"
    install -d "$pkgdir/usr/share/licenses/$pkgname"
    
    # Copiar toda la aplicación
    cp -r . "$pkgdir/usr/share/arch-chan/"
    
    # Crear script de lanzamiento
    cat > "$pkgdir/usr/bin/arch-chan" << 'EOF'
#!/bin/bash
cd /usr/share/arch-chan
python main.py "$@"
EOF
    chmod +x "$pkgdir/usr/bin/arch-chan"
    
    # Crear script de instalación de modelos
    cat > "$pkgdir/usr/bin/arch-chan-setup-models" << 'EOF'
#!/bin/bash
cd /usr/share/arch-chan
python setup_models.py
EOF
    chmod +x "$pkgdir/usr/bin/arch-chan-setup-models"
    
    # Instalar archivo .desktop
    install -Dm644 "arch-chan.desktop" "$pkgdir/usr/share/applications/arch-chan.desktop"
    
    # Instalar licencia
    install -Dm644 "LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    
    # Limpiar archivos innecesarios del paquete
    rm -f "$pkgdir/usr/share/arch-chan/.gitignore"
    rm -rf "$pkgdir/usr/share/arch-chan/.git"
}

post_install() {
    echo "🎉 Arch-Chan AI Assistant instalado correctamente"
    echo "📋 Próximos pasos:"
    echo "   1. Configurar Ollama: sudo systemctl enable --now ollama"
    echo "   2. Configurar modelos: arch-chan-setup-models"
    echo "   3. Ejecutar: arch-chan"
    echo "   4. Buscar 'Arch-Chan' en el menú de aplicaciones"
}

post_upgrade() {
    echo "🔄 Arch-Chan AI Assistant actualizado a v$pkgver"
    echo "💡 Ejecuta 'arch-chan-setup-models' si necesitas actualizar los modelos"
}