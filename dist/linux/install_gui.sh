#!/bin/bash

# GitBulk linux installer - gui edition
# ---------------------------------------------------------
# copyright (c) rezzt-dev. all rights reserved.

set -e

GREEN='\033[0;32m'
INFO='\033[0;37m'
YELLOW='\033[0;33m'
ERROR='\033[0;31m'
NC='\033[0m'

VERSION="v1.4.0"
BINARY_NAME="gitbulk-gui-linux"
INSTALL_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"
APP_DIR="$HOME/.local/share/applications"
DOWNLOAD_URL="https://github.com/rezzt-dev/gitbulk-project/releases/download/${VERSION}/${BINARY_NAME}"
ICON_URL="https://github.com/rezzt-dev/gitbulk-project/raw/main/src/gui/icons/gitbulk_icon.png"

echo ""
echo -e "${GREEN}  =====================================${NC}"
echo -e "${GREEN}         GitBulk ${VERSION}             ${NC}"
echo -e "${INFO}         linux installer - gui          ${NC}"
echo -e "${GREEN}  =====================================${NC}"
echo ""

# 1. crear directorios necesarios
mkdir -p "$INSTALL_DIR"
mkdir -p "$ICON_DIR"
mkdir -p "$APP_DIR"

# 2. descargar binario desde github releases
echo -e "${INFO}[info] descargando GitBulk gui ${VERSION}...${NC}"
if ! curl -fsSL -o "$INSTALL_DIR/$BINARY_NAME" "$DOWNLOAD_URL"; then
    echo -e "${ERROR}[error] fallo al descargar el binario. verifica tu conexion.${NC}"
    echo -e "${INFO}        url: $DOWNLOAD_URL${NC}"
    exit 1
fi
chmod +x "$INSTALL_DIR/$BINARY_NAME"
echo -e "${GREEN}[ok]   binario instalado en $INSTALL_DIR/$BINARY_NAME${NC}"

# 3. crear enlace simbolico de acceso rapido
ln -sf "$INSTALL_DIR/$BINARY_NAME" "$INSTALL_DIR/gitbulk-gui" 2>/dev/null || true
echo -e "${GREEN}[ok]   alias 'gitbulk-gui' creado.${NC}"

# 4. descargar icono de la aplicacion
echo -e "${INFO}[info] descargando icono...${NC}"
if curl -fsSL -o "$ICON_DIR/gitbulk.png" "$ICON_URL" 2>/dev/null; then
    echo -e "${GREEN}[ok]   icono instalado correctamente.${NC}"
else
    echo -e "${YELLOW}[warning] no se pudo descargar el icono. continuando sin el.${NC}"
fi

# 5. crear entrada de escritorio (.desktop)
echo -e "${INFO}[info] creando entrada de escritorio...${NC}"
cat > "$APP_DIR/gitbulk.desktop" <<EOF
[Desktop Entry]
Name=GitBulk
Comment=manage your git repositories concurrently
Exec=$INSTALL_DIR/$BINARY_NAME
Icon=$ICON_DIR/gitbulk.png
Terminal=false
Type=Application
Categories=Development;Utility;
Keywords=git;bulk;repository;
EOF
chmod +x "$APP_DIR/gitbulk.desktop"
echo -e "${GREEN}[ok]   acceso directo en el menu de aplicaciones creado.${NC}"

# 6. configurar path si es necesario
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

# 7. resumen final
echo ""
echo -e "${GREEN}  =====================================${NC}"
echo -e "${GREEN}     GitBulk instalado correctamente!  ${NC}"
echo -e "${GREEN}  =====================================${NC}"
echo -e "${INFO}  - directorio : $INSTALL_DIR${NC}"
echo -e "${INFO}  - version    : $VERSION${NC}"
echo -e "${INFO}  - menu apps  : creado${NC}"
echo ""
echo -e "${INFO}  nota: reinicia el terminal o ejecuta:${NC}"
echo -e "${INFO}        source ~/.bashrc (o ~/.zshrc)${NC}"
echo ""
read -p "presiona enter para finalizar..."
