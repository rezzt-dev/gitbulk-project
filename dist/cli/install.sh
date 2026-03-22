#!/bin/bash

echo "instalando gitbulk cli..."

 # detectar el sistema operativo
os=$(uname -s)
if [ "$os" = "Linux" ]; then
  binary_name="gitbulk-linux"
elif [ "$os" = "Darwin" ]; then
  binary_name="gitbulk-macos"
else
  echo "error: sistema operativo no soportado."
  exit 1
fi

 # definir rutas y url de tu release
url="https://github.com/rezzt-dev/gitbulk-project/releases/download/v1.0/$binary_name"
install_dir="$HOME/.local/bin"
exe_path="$install_dir/gitbulk"

 # crear la carpeta oculta para binarios del usuario si no existe
mkdir -p "$install_dir"

 # descargar el binario correspondiente
echo "descargando la version para $os desde github..."
curl -fsSL "$url" -o "$exe_path"

if [ $? -ne 0 ]; then
  echo "error al descargar el archivo. verifica que el release exita."
  exit 1
fi

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
