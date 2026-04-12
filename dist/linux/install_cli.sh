#!/bin/bash

# GitBulk linux installer - cli edition
# ---------------------------------------------------------
# copyright (c) rezzt-dev. all rights reserved.

set -e

GREEN='\033[0;32m'
INFO='\033[0;37m'
YELLOW='\033[0;33m'
ERROR='\033[0;31m'
NC='\033[0m'

VERSION="v1.4.0"
BINARY_NAME="gitbulk-linux"
INSTALL_DIR="$HOME/.local/bin"
DOWNLOAD_URL="https://github.com/rezzt-dev/gitbulk-project/releases/download/${VERSION}/${BINARY_NAME}"

echo ""
echo -e "${GREEN}  =====================================${NC}"
echo -e "${GREEN}         GitBulk ${VERSION}             ${NC}"
echo -e "${INFO}         linux installer - cli          ${NC}"
echo -e "${GREEN}  =====================================${NC}"
echo ""

# 1. comprobar dependencias minimas
if ! command -v git &> /dev/null; then
    echo -e "${ERROR}[error] 'git' no encontrado. instalalo antes de continuar.${NC}"
    exit 1
fi
echo -e "${GREEN}[ok]   git detectado: $(git --version)${NC}"

# 2. crear directorio de instalacion
mkdir -p "$INSTALL_DIR"
echo -e "${INFO}[info] directorio de instalacion: $INSTALL_DIR${NC}"

# 3. descargar binario desde github releases
echo -e "${INFO}[info] descargando GitBulk cli ${VERSION}...${NC}"
if ! curl -fsSL -o "$INSTALL_DIR/$BINARY_NAME" "$DOWNLOAD_URL"; then
    echo -e "${ERROR}[error] fallo al descargar el binario. verifica tu conexion.${NC}"
    echo -e "${INFO}        url: $DOWNLOAD_URL${NC}"
    exit 1
fi
chmod +x "$INSTALL_DIR/$BINARY_NAME"
echo -e "${GREEN}[ok]   binario instalado en $INSTALL_DIR/$BINARY_NAME${NC}"

# 4. crear alias de acceso rapido (gitbulk)
ln -sf "$INSTALL_DIR/$BINARY_NAME" "$INSTALL_DIR/gitbulk" 2>/dev/null || true
echo -e "${GREEN}[ok]   alias 'gitbulk' creado.${NC}"

# 5. configurar path si es necesario
echo -e "${INFO}[info] verificando configuracion del path...${NC}"
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    SHELL_RC=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.bashrc"
    fi

    if [ -f "$SHELL_RC" ]; then
        if ! grep -q "$INSTALL_DIR" "$SHELL_RC"; then
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_RC"
            echo -e "${GREEN}[ok]   ruta añadida a $SHELL_RC${NC}"
        fi
    fi
else
    echo -e "${INFO}[info] la ruta ya existe en el path.${NC}"
fi

# 6. resumen final
echo ""
echo -e "${GREEN}  =====================================${NC}"
echo -e "${GREEN}     GitBulk cli instalado!            ${NC}"
echo -e "${GREEN}  =====================================${NC}"
echo -e "${INFO}  - directorio : $INSTALL_DIR${NC}"
echo -e "${INFO}  - version    : $VERSION${NC}"
echo -e "${INFO}  - comando    : gitbulk --help${NC}"
echo ""
echo -e "${INFO}  nota: reinicia el terminal o ejecuta:${NC}"
echo -e "${INFO}        source ~/.bashrc (o ~/.zshrc)${NC}"
echo -e "${INFO}        luego: gitbulk --help${NC}"
echo ""
read -p "presiona enter para finalizar..."
