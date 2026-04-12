# build_gui.ps1 — Emisor de build profesional de GitBulk (Modo Producción)
# Este script genera la versión One-File FINAL y LIMPIA (sin consola).

# 1. Limpiar carpetas anteriores
$ProjectRoot = "$PSScriptRoot\.."
if (Test-Path "$ProjectRoot\build") { Remove-Item -Recurse -Force "$ProjectRoot\build" }
if (Test-Path "$ProjectRoot\dist\windows\GitBulk-GUI.exe") { Remove-Item -Force "$ProjectRoot\dist\windows\GitBulk-GUI.exe" }

# 2. Ejecutar PyInstaller (Versión Final: Sin consola)
python -m PyInstaller --noconsole --onefile --name "GitBulk-GUI" `
    --distpath "$ProjectRoot\dist\windows" `
    --icon "$ProjectRoot\assets\gitbulk.ico" `
    --add-data "$ProjectRoot\assets;assets" `
    --add-data "$ProjectRoot\src\gui\icons;gui/icons" `
    --add-data "$ProjectRoot\src\gui\theme.qss;gui" `
    --add-data "$ProjectRoot\vendor\git;vendor/git" `
    --hidden-import "gui.translations" `
    --hidden-import "gui.icon_manager" `
    --hidden-import "PySide6.QtSvg" `
    --hidden-import "PySide6.QtSvgWidgets" `
    --hidden-import "PySide6.QtXml" `
    --paths "$ProjectRoot\src" `
    "$ProjectRoot\src\main.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Build de producción completado con éxito." -ForegroundColor Green
    Write-Host "Ubicación: dist/windows/GitBulk-GUI.exe" -ForegroundColor Gray
} else {
    Write-Host "`n[ERROR] El build ha fallado." -ForegroundColor Red
}
