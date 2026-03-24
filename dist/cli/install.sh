#!/bin/bash
echo "Iniciando instalación de gitbulk CLI..."

# 1. Comprobar dependencias mínimas (git y python)
if ! command -v git &> /dev/null; then
    echo "error: No se ha encontrado 'git'. Por favor, instálalo antes de continuar."
    exit 1
}

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "error: No se ha encontrado 'python' o 'python3'. Por favor, instálalo antes de continuar."
    exit 1
fi

# 2. Configurar variables de directorios
TARGET_FOLDER="$HOME/.local/bin"
EXE_PATH="$TARGET_FOLDER/gitbulk"
SPEC_FILE="gitbulk.spec"
TEMP_DIR="/tmp/gitbulk_src_$$"

# Crear carpeta de destino si no existe
mkdir -p "$TARGET_FOLDER"

echo "Descargando todo el código fuente..."
git clone https://github.com/rezzt-dev/gitbulk-project.git "$TEMP_DIR"
if [ $? -ne 0 ]; then
    echo "error: Falló la clonación del repositorio remoto."
    exit 1
fi

cd "$TEMP_DIR" || exit 1

echo "Creando entorno virtual (venv)..."
$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    echo "error: No se pudo crear el entorno virtual. Es posible que te falte el paquete python3-venv en tu sistema (ej. sudo apt install python3-venv)."
    cd "$HOME" || exit 1
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Instalando dependencias en el entorno virtual..."
./venv/bin/pip install -r requirements.txt pyinstaller
if [ $? -ne 0 ]; then
    echo "error: Falló la instalación de dependencias."
    cd "$HOME" || exit 1
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Compilando el ejecutable localmente..."
./venv/bin/pyinstaller "$SPEC_FILE" --clean

DIST_PATH="dist/gitbulk"
if [ ! -f "$DIST_PATH" ]; then
    echo "error: Falló la compilación local. No se encontró $DIST_PATH."
    cd "$HOME" || exit 1
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Moviendo el ejecutable a la ruta final..."
cp "$DIST_PATH" "$EXE_PATH"
chmod +x "$EXE_PATH"

echo "Ok: Limpieza terminada e instalación exitosa."
cd "$HOME" || exit 1
rm -rf "$TEMP_DIR"

# Configurar variables de entorno
echo "Configurando variables de entorno..."

if ! echo "$PATH" | grep -q "$TARGET_FOLDER"; then
    if [ -f "$HOME/.zshrc" ]; then
        echo -e '\nexport PATH="'$TARGET_FOLDER':$PATH"' >> "$HOME/.zshrc"
        echo "Ok: gitbulk añadido a ~/.zshrc."
    elif [ -f "$HOME/.bashrc" ]; then
        echo -e '\nexport PATH="'$TARGET_FOLDER':$PATH"' >> "$HOME/.bashrc"
        echo "Ok: gitbulk añadido a ~/.bashrc."
    fi
else
    echo "Ok: gitbulk ya estaba configurado en tu PATH."
fi

echo "========================================="
echo "  ¡Instalación completada con éxito!     "
echo "========================================="
echo "Por favor, cierra esta terminal y abre una nueva,"
echo "o ejecuta: source ~/.bashrc (o ~/.zshrc)"
echo "Luego simplemente escribe: gitbulk --help"
