# GitBulk windows installer - gui version
# ---------------------------------------------------------
# copyright (c) rezzt-dev. all rights reserved.

$ErrorActionPreference = "Stop"

$version     = "v1.3.0"
$binary_name = "gitbulk-gui-windows.exe"
$install_dir = Join-Path $env:LOCALAPPDATA "GitBulk"
$target_path = Join-Path $install_dir $binary_name
$download_url = "https://github.com/rezzt-dev/gitbulk-project/releases/download/$version/$binary_name"
$shortcut_path = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\GitBulk.lnk"

Write-Host ""
Write-Host "  ==============================" -ForegroundColor Cyan
Write-Host "         GitBulk installer      " -ForegroundColor White
Write-Host "         gui edition - windows  " -ForegroundColor DarkGray
Write-Host "  ==============================" -ForegroundColor Cyan
Write-Host ""

# 1. crear directorio de instalacion
if (-not (Test-Path $install_dir)) {
    Write-Host "[info] creando directorio $install_dir" -ForegroundColor DarkGray
    New-Item -Path $install_dir -ItemType Directory | Out-Null
}

# 2. descargar binario
Write-Host "[info] descargando GitBulk gui $version..." -ForegroundColor DarkGray
try {
    Invoke-WebRequest -Uri $download_url -OutFile $target_path -UseBasicParsing
    Write-Host "[ok]   binario descargado correctamente." -ForegroundColor Green
} catch {
    Write-Host "[error] fallo al descargar. verifica tu conexion a internet." -ForegroundColor Red
    Write-Host "       url: $download_url" -ForegroundColor DarkGray
    Read-Host "presiona enter para salir..."
    exit 1
}

# 3. añadir al path del usuario (sin privilegios de administrador)
Write-Host "[info] configurando path del usuario..." -ForegroundColor DarkGray
$current_path = [Environment]::GetEnvironmentVariable("Path", "User")
if ($current_path -notlike "*$install_dir*") {
    [Environment]::SetEnvironmentVariable("Path", "$current_path;$install_dir", "User")
    Write-Host "[ok]   $install_dir añadido al path." -ForegroundColor Green
} else {
    Write-Host "[info] la ruta ya existe en el path del usuario." -ForegroundColor DarkGray
}

# 4. crear acceso directo en el menu inicio
Write-Host "[info] creando acceso directo en el menu inicio..." -ForegroundColor DarkGray
try {
    $shell    = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcut_path)
    $shortcut.TargetPath      = $target_path
    $shortcut.WorkingDirectory = $install_dir
    $shortcut.Description     = "GitBulk: manage your git repositories concurrently"
    $shortcut.Save()
    Write-Host "[ok]   acceso directo creado en el menu inicio." -ForegroundColor Green
} catch {
    Write-Host "[warning] no se pudo crear el acceso directo. continua de forma manual." -ForegroundColor Yellow
}

# 5. resumen final
Write-Host ""
Write-Host "  ==============================" -ForegroundColor Green
Write-Host "    GitBulk instalado con exito " -ForegroundColor White
Write-Host "  ==============================" -ForegroundColor Green
Write-Host "  - directorio : $install_dir" -ForegroundColor DarkGray
Write-Host "  - ejecutable : $binary_name" -ForegroundColor DarkGray
Write-Host "  - menu inicio: creado" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  reinicia el terminal para que el path surta efecto." -ForegroundColor DarkGray
Write-Host ""
Read-Host "presiona enter para finalizar..."
