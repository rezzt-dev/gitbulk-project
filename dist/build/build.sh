#!/bin/bash
cd ../../

echo "====== Compilador automatizado de GitBulk (Linux/macOS) ======"
echo ""
echo "[1/2] Instalando dependencias de instalacion y ejecucion..."
pip3 install -r requirements.txt || pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Fallo al instalar dependencias con pip. Comprueba el entorno."
    exit 1
fi

echo ""
echo "[2/2] Construyendo el binario usando PyInstaller protegido..."
pyinstaller gitbulk-linux.spec --clean
if [ $? -ne 0 ]; then
    echo "[ERROR] PyInstaller fallo durante la construccion."
    exit 1
fi

echo ""
echo "========================================================="
if [ -f "dist/gitbulk-linux/gitbulk-linux" ] || [ -f "dist/gitbulk/gitbulk" ]; then
    echo "[EXITO] Compilacion exitosa."
    echo "Revisa la carpeta dist/ para obtener tu ejecutable (gitbulk-linux o gitbulk)."
else
    echo "[ERROR] No se encontro el ejecutable compilado en dist/."
fi
echo "========================================================="
