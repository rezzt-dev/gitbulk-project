#!/bin/bash

# Exit on error
set -e

echo -e "\e[1;32m[INFO] Starting GitBulk GUI Build for Linux...\e[0m"

# Ensure we are in the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo -e "\e[1;31m[ERROR] PyInstaller not found. Please install it with: pip install pyinstaller\e[0m"
    exit 1
fi

echo -e "\e[1;34m[INFO] Cleaning previous builds...\e[0m"
rm -rf build/ dist/GitBulk-GUI-Linux

echo -e "\e[1;34m[INFO] Running PyInstaller...\e[0m"

pyinstaller --noconfirm --onefile --windowed \
    --name "GitBulk-GUI-Linux" \
    --paths "src" \
    --add-data "assets:assets" \
    --add-data "src/gui/icons:src/gui/icons" \
    --add-data "src/gui/theme.qss:src/gui/theme.qss" \
    --hidden-import "PySide6.QtSvg" \
    --hidden-import "PySide6.QtSvgWidgets" \
    --hidden-import "PySide6.QtXml" \
    --hidden-import "gui.translations" \
    --hidden-import "gui.icon_manager" \
    "src/main.py"

echo -e "\e[1;32m[SUCCESS] Build complete! Binary available at: dist/GitBulk-GUI-Linux\e[0m"
