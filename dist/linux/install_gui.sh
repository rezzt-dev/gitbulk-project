#!/bin/bash

# --- Color Definitions ---
GREEN='\033[0;32m'
INFO='\033[0;37m'
ERROR='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}   GitBulk Linux Native Installer    ${NC}"
echo -e "${GREEN}=====================================${NC}"

VERSION="v1.3.0"
BINARY_NAME="GitBulk-GUI"
INSTALL_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"
APP_DIR="$HOME/.local/share/applications"
REPO_URL="https://github.com/rezzt-dev/gitbulk-project"
BINARY_URL="${REPO_URL}/releases/download/${VERSION}/${BINARY_NAME}"
ICON_URL="${REPO_URL}/raw/main/src/gui/icons/gitbulk_icon.svg" # Assuming SVG for now

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$ICON_DIR"
mkdir -p "$APP_DIR"

echo -e "${INFO}[INFO] Downloading $BINARY_NAME ${VERSION}...${NC}"
if ! curl -L -o "$INSTALL_DIR/$BINARY_NAME" "$BINARY_URL"; then
    echo -e "${ERROR}[ERROR] Failed to download binary. Please check your connection or version.${NC}"
    read -p "Press Enter to exit..."
    exit 1
fi
chmod +x "$INSTALL_DIR/$BINARY_NAME"

echo -e "${INFO}[INFO] Downloading icon...${NC}"
# User requested gitbulk.png, but we have SVG. We'll try to find it on release or use SVG.
if ! curl -L -o "$ICON_DIR/gitbulk.svg" "$ICON_URL"; then
    echo -e "${ERROR}[ERROR] Failed to download icon.${NC}"
fi

echo -e "${INFO}[INFO] Creating desktop entry...${NC}"
cat <<EOF > "$APP_DIR/gitbulk.desktop"
[Desktop Entry]
Name=GitBulk
Comment=Mass manage your Git repositories with ease.
Exec=$INSTALL_DIR/$BINARY_NAME
Icon=gitbulk
Terminal=false
Type=Application
Categories=Development;Utility;
Keywords=git;bulk;repository;
EOF

# Ensure the icon is recognized (some environments prefer PNG, but SVG is widely supported)
# Link gitbulk.svg to gitbulk if needed, or just hope the desktop entry finds it.
# We'll also try to download a PNG if the user specifically asked for it.
ICON_PNG_URL="${REPO_URL}/raw/main/assets/gitbulk.png"
if curl -L -o "$ICON_DIR/gitbulk.png" "$ICON_PNG_URL" &> /dev/null; then
    echo -e "${INFO}[INFO] PNG icon installed successfully.${NC}"
else
    echo -e "${INFO}[INFO] PNG icon not found, using SVG.${NC}"
    cp "$ICON_DIR/gitbulk.svg" "$ICON_DIR/gitbulk.png" 2>/dev/null || true
fi

echo -e "${INFO}[INFO] Checking PATH...${NC}"
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${INFO}[INFO] Adding $INSTALL_DIR to PATH...${NC}"
    SHELL_RC=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if [ -f "$SHELL_RC" ]; then
        if ! grep -q "$INSTALL_DIR" "$SHELL_RC"; then
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_RC"
            echo -e "${GREEN}[OK] Added to $SHELL_RC. Restart your terminal or run 'source $SHELL_RC'.${NC}"
        fi
    fi
fi

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}[SUCCESS] GitBulk installed!${NC}"
echo -e "${INFO}You can now launch it from your application menu.${NC}"
echo -e "${GREEN}=====================================${NC}"

read -p "Press Enter to finish..."
