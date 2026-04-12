# build_gui_windows.ps1 — Standard Production Build for GitBulk GUI
# Based on the branding and configuration standards of rezzt-dev.

$ProjectRoot = "$PSScriptRoot\.."
Set-Location $ProjectRoot

# 1. Ensure dependencies are ready
if (-not (Test-Path "vendor/git")) {
    Write-Host "[INFO] Preparando Git portátil..." -ForegroundColor Cyan
    powershell -File scripts/prepare_portable_git.ps1
}

# 2. Cleanup previous artifacts
Write-Host "[INFO] Limpiando carpetas de construcción..." -ForegroundColor Gray
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist/windows/gitbulk-gui.exe") { Remove-Item -Force "dist/windows/gitbulk-gui.exe" }

# 3. Execute PyInstaller
Write-Host "[INFO] Generando ejecutable standalone (One-File)..." -ForegroundColor Cyan
python -m PyInstaller --noconsole --onefile --name "gitbulk-gui" `
    --distpath "dist/windows" `
    --icon "assets/gitbulk.ico" `
    --add-data "assets;assets" `
    --add-data "src/gui/icons;src/gui/icons" `
    --add-data "src/gui/theme.qss;src/gui" `
    --add-data "vendor/git;vendor/git" `
    --hidden-import "gui.translations" `
    --hidden-import "gui.icon_manager" `
    --hidden-import "PySide6.QtSvg" `
    --hidden-import "PySide6.QtSvgWidgets" `
    --hidden-import "PySide6.QtXml" `
    --paths "src" `
    "src/main.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Build de gitbulk-gui completado." -ForegroundColor Green
    Write-Host "Ubicación: dist/windows/gitbulk-gui.exe" -ForegroundColor Gray
} else {
    Write-Host "`n[ERROR] El build ha fallado." -ForegroundColor Red
    exit $LASTEXITCODE
}
