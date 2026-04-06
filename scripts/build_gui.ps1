# build_gui.ps1 — En empaquetador oficial de GitBulk para Windows
# Estructura profesional (dist/App_GUI/GitBulk)

# 1. Limpiar carpetas anteriores
$ProjectRoot = "$PSScriptRoot\.."
if (Test-Path "$ProjectRoot\build") { Remove-Item -Recurse -Force "$ProjectRoot\build" }
if (Test-Path "$ProjectRoot\dist\App_GUI") { Remove-Item -Recurse -Force "$ProjectRoot\dist\App_GUI" }

# 2. Ejecutar PyInstaller con todas las dependencias visuales
python -m PyInstaller --noconsole --onedir --name "GitBulk" `
    --distpath "$ProjectRoot\dist\App_GUI" `
    --icon "$ProjectRoot\assets\gitbulk.ico" `
    --add-data "$ProjectRoot\assets;assets" `
    --add-data "$ProjectRoot\src\gui\icons;gui/icons" `
    --add-data "$ProjectRoot\src\gui\theme.qss;gui" `
    --hidden-import "PySide6.QtSvg" `
    --hidden-import "PySide6.QtSvgWidgets" `
    --paths "$ProjectRoot\src" `
    "$ProjectRoot\src\main.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Build completado con éxito." -ForegroundColor Green
    Write-Host "Ubicación: dist/App_GUI/GitBulk/GitBulk.exe" -ForegroundColor Gray
} else {
    Write-Host "`n[ERROR] El build ha fallado." -ForegroundColor Red
}
