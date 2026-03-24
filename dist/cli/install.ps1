$Host.UI.RawUI.WindowTitle = "Instalador de gitbulk"
Write-Host "Iniciando instalacion de gitbulk CLI..." -ForegroundColor Cyan

# 1. Comprobar dependencias (git y python)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Error: No se ha encontrado 'git'. Por favor, instálalo antes de continuar." -ForegroundColor Red
    exit 1
}

$pythonCmd = ""
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py" # Utilidad de entorno de windows py launcher
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} else {
    Write-Host "Error: No se ha encontrado 'python' o 'py'. Por favor, instálalo antes de continuar." -ForegroundColor Red
    exit 1
}

# 2. Configurar variables para Windows
$targetFolder = "$env:USERPROFILE\.gitbulk"
$exePath = "$targetFolder\gitbulk.exe"
$specFile = "gitbulk-windows.spec"
$distPath = "dist\gitbulk-windows\gitbulk-windows.exe"
$venvPython = "venv\Scripts\python.exe"
$venvPip = "venv\Scripts\pip.exe"
$venvPyinstaller = "venv\Scripts\pyinstaller.exe"

# Crear carpeta de destino si no existe
if (-not (Test-Path -Path $targetFolder)) {
    New-Item -ItemType Directory -Path $targetFolder | Out-Null
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) "gitbulk_src_$(Get-Random)"

Write-Host "Descargando todo el codigo fuente..." -ForegroundColor Yellow
git clone https://github.com/rezzt-dev/gitbulk-project.git $tempDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Falló la clonación del repositorio remoto." -ForegroundColor Red
    exit 1
}

Push-Location $tempDir

Write-Host "Creando entorno virtual (venv)..." -ForegroundColor Yellow
& $pythonCmd -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: No se pudo crear el entorno virtual. Verifica tu instalación de Python." -ForegroundColor Red
    Pop-Location
    Remove-Item -Recurse -Force $tempDir
    exit 1
}

Write-Host "Instalando dependencias en el entorno virtual..." -ForegroundColor Yellow
& $venvPip install -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Falló la instalación de dependencias." -ForegroundColor Red
    Pop-Location
    Remove-Item -Recurse -Force $tempDir
    exit 1
}

Write-Host "Compilando el ejecutable localmente..." -ForegroundColor Yellow
& $venvPyinstaller $specFile --clean

if (-not (Test-Path $distPath)) {
    Write-Host "Error: Falló la compilación local." -ForegroundColor Red
    Pop-Location
    Remove-Item -Recurse -Force $tempDir
    exit 1
}

Write-Host "Moviendo el ejecutable a la ruta final..." -ForegroundColor Yellow
Copy-Item -Path $distPath -Destination $exePath -Force

Write-Host "Ok: Limpieza terminada e instalacion exitosa." -ForegroundColor Green

Pop-Location
Remove-Item -Recurse -Force $tempDir

# Configurar variables de entorno
Write-Host "Configurando variables de entorno..." -ForegroundColor Yellow

# Modificar el PATH del usuario de Windows
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notmatch [regex]::Escape($targetFolder)) {
    $newPath = if ($userPath) { "$userPath;$targetFolder" } else { $targetFolder }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Ok: gitbulk añadido al PATH correctamente." -ForegroundColor Green
} else {
    Write-Host "Ok: gitbulk ya estaba configurado en el PATH." -ForegroundColor DarkGreen
}

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  ¡Instalacion completada con exito!     " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Por favor, cierra esta terminal y abre una nueva."
Write-Host "Luego simplemente escribe: gitbulk --help"