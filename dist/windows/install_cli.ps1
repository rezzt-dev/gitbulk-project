# GitBulk windows installer - cli edition
# ---------------------------------------------------------
# copyright (c) rezzt-dev. all rights reserved.

$ErrorActionPreference = "Stop"

$version      = "v1.4.0"
$binary_name  = "gitbulk-windows.exe"
$install_dir  = Join-Path $env:LOCALAPPDATA "GitBulk"
$target_path  = Join-Path $install_dir $binary_name
$alias_path   = Join-Path $install_dir "gitbulk.exe"
$download_url = "https://github.com/rezzt-dev/gitbulk-project/releases/download/$version/$binary_name"

Write-Host ""
Write-Host "  ======================================" -ForegroundColor Cyan
Write-Host "         GitBulk $version              " -ForegroundColor White
Write-Host "         windows installer - cli         " -ForegroundColor DarkGray
Write-Host "  ======================================" -ForegroundColor Cyan
Write-Host ""

# 1. crear directorio de instalacion
if (-not (Test-Path $install_dir)) {
    Write-Host "[info] creando directorio de instalacion en $install_dir" -ForegroundColor DarkGray
    New-Item -Path $install_dir -ItemType Directory | Out-Null
}

# 2. descargar binario desde github releases
Write-Host "[info] descargando GitBulk cli $version..." -ForegroundColor DarkGray
try {
    $client = [System.Net.WebClient]::new()
    $client.DownloadFile($download_url, $target_path)
    Write-Host "[ok]   binario descargado en $target_path" -ForegroundColor Green
} catch {
    Write-Host "[error] fallo al descargar. verifica tu conexion a internet." -ForegroundColor Red
    Write-Host "        url: $download_url" -ForegroundColor DarkGray
    Read-Host "presiona enter para salir..."
    exit 1
}

# 3. copiar con alias corto (gitbulk.exe) para invocacion directa desde terminal
Write-Host "[info] configurando alias 'gitbulk' en el directorio de instalacion..." -ForegroundColor DarkGray
try {
    Copy-Item -Path $target_path -Destination $alias_path -Force
    Write-Host "[ok]   alias 'gitbulk.exe' creado." -ForegroundColor Green
} catch {
    Write-Host "[warning] no se pudo crear el alias." -ForegroundColor Yellow
}

# 4. añadir al path del usuario (sin privilegios de administrador)
Write-Host "[info] configurando variables de entorno (path)..." -ForegroundColor DarkGray
$current_path = [Environment]::GetEnvironmentVariable("Path", "User")
if ($current_path -notlike "*$install_dir*") {
    [Environment]::SetEnvironmentVariable("Path", "$current_path;$install_dir", "User")
    Write-Host "[ok]   $install_dir añadido al path del usuario." -ForegroundColor Green
} else {
    Write-Host "[info] la ruta ya existe en el path." -ForegroundColor DarkGray
}

# 5. resumen final
Write-Host ""
Write-Host "  ======================================" -ForegroundColor Green
Write-Host "     GitBulk cli instalado!            " -ForegroundColor White
Write-Host "  ======================================" -ForegroundColor Green
Write-Host "  - directorio : $install_dir" -ForegroundColor DarkGray
Write-Host "  - version    : $version" -ForegroundColor DarkGray
Write-Host "  - comando    : gitbulk --help" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  nota: reinicia el terminal para que el path surta efecto." -ForegroundColor DarkGray
Write-Host "        luego ejecuta: gitbulk --help" -ForegroundColor DarkGray
Write-Host ""
Read-Host "presiona enter para finalizar..."
