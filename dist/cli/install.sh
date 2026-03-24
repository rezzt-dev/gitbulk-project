#!/bin/bash

echo "compilando e instalando gitbulk cli localmente..."

 # definir rutas
install_dir="$HOME/.local/bin"
exe_path="$install_dir/gitbulk"

 # crear la carpeta oculta para binarios del usuario si no existe
mkdir -p "$install_dir"

 # compilar el binario localmente
echo "iniciando proceso de compilacion local con build.sh..."
chmod +x ../build/build.sh
(cd ../build && ./build.sh)

 # buscar el ejecutable generado
local_bin=""
if [ -f "../../dist/gitbulk-linux/gitbulk-linux" ]; then
    local_bin="../../dist/gitbulk-linux/gitbulk-linux"
elif [ -f "../../dist/gitbulk/gitbulk" ]; then
    local_bin="../../dist/gitbulk/gitbulk"
fi

if [ -z "$local_bin" ]; then
  echo "error: la compilacion local fallo."
  exit 1
fi

echo "instalando el ejecutable generado..."
cp "$local_bin" "$exe_path"
echo "ok: archivo copiado exitosamente."


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
