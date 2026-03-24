#!/bin/bash

echo "compilando e instalando gitbulk cli localmente..."

 # definir rutas
install_dir="$HOME/.local/bin"
exe_path="$install_dir/gitbulk"
temp_dir="/tmp/gitbulk_src_$$"

 # crear la carpeta oculta para binarios del usuario si no existe
mkdir -p "$install_dir"

echo "clonando la ultima version desde internet..."
git clone https://github.com/rezzt-dev/gitbulk-project.git "$temp_dir" || { echo "error: no se pudo clonar el repositorio."; exit 1; }

echo "iniciando compilacion de dependencias..."
cd "$temp_dir"
pip3 install -r requirements.txt || pip install -r requirements.txt

echo "empaquetando ejectuable..."
pyinstaller gitbulk-linux.spec --clean

 # buscar el ejecutable generado
local_bin=""
if [ -f "dist/gitbulk-linux/gitbulk-linux" ]; then
    local_bin="dist/gitbulk-linux/gitbulk-linux"
elif [ -f "dist/gitbulk/gitbulk" ]; then
    local_bin="dist/gitbulk/gitbulk"
fi

if [ -z "$local_bin" ]; then
  echo "error: la compilacion local fallo."
  cd "$HOME"
  rm -rf "$temp_dir"
  exit 1
fi

echo "instalando el ejecutable generado..."
cp "$local_bin" "$exe_path"
chmod +x "$exe_path"
echo "limpiando rastros temporales..."
cd "$HOME"
rm -rf "$temp_dir"
echo "ok: archivo copiado e instalado exitosamente."


chmod +x "$exe_path"

if ! echo "$PATH" | grep -q "$install_dir"; then
  echo "configurando variables de entorno..."

   # detectar si usa bash o zsh (el por defecto en macos) y añadir el path
  if [ -f "$HOME/.zshrc" ]; then
    echo '\nexport PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
  elif [ -f "$HOME/.bashrc" ]; then
    echo '\nexport PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
  fi
  echo "ok: gitbulk añadido al path."
else
  echo "ok: gitbulk ya estaba configurado en tu path."
fi

echo "========================================="
echo "  ¡instalacion completada con exito!     "
echo "========================================="
echo "por favor, cierra esta terminal y abre una nueva,"
echo "o ejecuta: source ~/.bashrc (o ~/.zshrc)"
echo "luego simplemente escribe: gitbulk --help"
