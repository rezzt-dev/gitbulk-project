# GitBulk CLI - Instalador Web Oficial para Windows 
# ======================================================
# Versión: 1.3.0
# Comando: iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/cli/install.ps1" | iex

$AppName = "GitBulk-CLI"
$ExecutableBaseName = "gitbulk"
$Version = "v1.3.0"
$ExeName = "GitBulk-CLI-Windows.exe"
$InstallFolder = "$env:USERPROFILE\.gitbulk"
$ReleaseUrl = "https://github.com/rezzt-dev/gitbulk-project/releases/download/$Version/$ExeName"

# 1. Elevación de Privilegios (Robust Web-Installer Support)
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[!] Solicitando permisos de administrador..." -ForegroundColor Yellow
    
    $ScriptPath = ""
    if ($PSCommandPath) {
        $ScriptPath = $PSCommandPath
    } else {
        $ScriptPath = Join-Path $env:TEMP "GitBulk_CLI_Installer.ps1"
        $RemoteUrl = "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/cli/install.ps1"
        Invoke-WebRequest -Uri $RemoteUrl -OutFile $ScriptPath -ErrorAction SilentlyContinue
    }

    if (Test-Path $ScriptPath) {
        Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -Verb RunAs
    } else {
        Write-Host "[ERROR] No se pudo localizar el instalador para elevar privilegios." -ForegroundColor Red
        Read-Host "Presiona Enter para cerrar..."
    }
    exit
}

try {
    Write-Host "`n--- Instalando GitBulk CLI ($Version) ---" -ForegroundColor Cyan

    # 2. Preparar Carpeta
    if (-not (Test-Path $InstallFolder)) {
        New-Item -ItemType Directory -Path $InstallFolder | Out-Null
    }

    # 3. Descarga / Localización de Binario
    $SourceExe = ""
    $LocalSource = Join-Path $PSScriptRoot "$ExeName"
    
    if (Test-Path "$LocalSource") {
        Write-Host "[INFO] Detectado binario local: $LocalSource" -ForegroundColor Gray
        $SourceExe = $LocalSource
    } else {
        Write-Host "[1/3] Descargando binario desde GitHub..." -ForegroundColor Gray
        $TempExe = Join-Path $env:TEMP $ExeName
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $ReleaseUrl -OutFile $TempExe -ErrorAction Stop
        $SourceExe = $TempExe
    }

    # 4. Instalación
    Write-Host "[2/3] Instalando en carpeta de usuario..." -ForegroundColor Gray
    Copy-Item -Path "$SourceExe" -Destination "$InstallFolder\$ExecutableBaseName.exe" -Force

    # 5. Configuración de PATH
    Write-Host "[3/3] Configurando variables de entorno (PATH)..." -ForegroundColor Gray
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notmatch [regex]::Escape($InstallFolder)) {
        $newPath = if ($userPath) { "$userPath;$InstallFolder" } else { $InstallFolder }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    }

    Write-Host "`n=========================================" -ForegroundColor Cyan
    Write-Host "  ¡Instalación CLI completada con éxito! " -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Cierra esta terminal y abre una nueva para empezar."
} catch {
    Write-Host "`n[FATAL ERROR] La instalación de la CLI ha fallado." -ForegroundColor Red
    Write-Host "Detalles: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Read-Host "`nPresiona Enter para finalizar..."
}