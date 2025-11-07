#!/bin/bash
echo "🔄 Actualizando Arch-Chan..."
cd "$(dirname "$0")"
git pull origin main
python main.py --update
