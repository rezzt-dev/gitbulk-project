@echo off
cd ..\..\
echo ====== Compilador automatizado de GitBulk (Windows) ======
echo.
echo [1/2] Instalando dependencias de instalacion y ejecucion...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al instalar las dependencias con pip. Asegurese de tener Python instalado correctamente.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Construyendo el binario usando PyInstaller protegido...
pyinstaller gitbulk-windows.spec --clean
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller fallo durante la construccion.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =========================================================
if exist "dist\gitbulk-windows\gitbulk-windows.exe" (
    echo [EXITO] Compilacion exitosa. 
    echo Ejecutable generado en: dist\gitbulk-windows\gitbulk-windows.exe
) else (
    echo [ERROR] No se pudo encontrar el ejecutable generado en la carpeta dist.
)
echo =========================================================
pause
