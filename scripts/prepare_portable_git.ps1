# prepare_portable_git.ps1
# Este script descarga MinGit (minimal Git for Windows) para empaquetarlo con GitBulk.

$GitVersion = "2.44.0"
$Url = "https://github.com/git-for-windows/git/releases/download/v$GitVersion.windows.1/MinGit-$GitVersion-64-bit.zip"
$ProjectRoot = "$PSScriptRoot\.."
$VendorPath = "$ProjectRoot\vendor\git"
$ZipPath = "$ProjectRoot\vendor\mingit.zip"

if (-not (Test-Path $VendorPath)) {
    New-Item -ItemType Directory -Path $VendorPath -Force
}

Write-Host "[INFO] Descargando MinGit v$GitVersion..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $Url -OutFile $ZipPath

Write-Host "[INFO] Extrayendo archivos..." -ForegroundColor Cyan
Expand-Archive -Path $ZipPath -DestinationPath $VendorPath -Force

Write-Host "[INFO] Limpiando..." -ForegroundColor Cyan
Remove-Item $ZipPath

Write-Host "[SUCCESS] MinGit está listo en: vendor/git" -ForegroundColor Green
Write-Host "Este contenido será incluido automáticamente en el próximo build." -ForegroundColor Gray
