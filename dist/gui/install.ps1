# GitBulk GUI - Instalador Web Oficial para Windows 10/11
# ======================================================
# Versión: 1.3.0
# Comando: iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install.ps1" | iex

$AppName = "GitBulk"
$AppFullName = "GitBulk GUI"
$Version = "v1.3.0"
$ExeName = "GitBulk-GUI-Windows.exe"
$InstallFolder = "$env:ProgramFiles\$AppName"
$ReleaseUrl = "https://github.com/rezzt-dev/gitbulk-project/releases/download/$Version/$ExeName"

# 1. Elevación de Privilegios (Robust Web-Installer Support)
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[!] Solicitando permisos de administrador..." -ForegroundColor Yellow
    
    $ScriptPath = ""
    if ($PSCommandPath) {
        $ScriptPath = $PSCommandPath
    } else {
        # IEX mode: We must download to a temp file to allow Start-Process -File
        $ScriptPath = Join-Path $env:TEMP "GitBulk_GUI_Installer.ps1"
        $RemoteUrl = "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install.ps1"
        Invoke-WebRequest -Uri $RemoteUrl -OutFile $ScriptPath -ErrorAction SilentlyContinue
    }

    if (Test-Path $ScriptPath) {
        # Pasamos la ruta del script para que el proceso elevado no pierda el contexto si es local
        Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -Verb RunAs
    } else {
        Write-Host "[ERROR] No se pudo localizar el archivo de instalación para elevar privilegios." -ForegroundColor Red
        Write-Host "Por favor, ejecuta PowerShell como administrador e intenta de nuevo." -ForegroundColor White
        Read-Host "Presiona Enter para cerrar..."
    }
    exit
}

try {
    Write-Host "`n--- Instalando $AppFullName ($Version) ---" -ForegroundColor Cyan

    # 2. Detección de Archivos Locales vs Web
    $SourceExe = ""
    # Intentamos detectar si estamos en el repo local (relativo a este script)
    $LocalSource = Join-Path $PSScriptRoot "..\App_GUI\$ExeName"
    
    if (Test-Path "$LocalSource") {
        Write-Host "[INFO] Detectada instalación desde archivos locales: $LocalSource" -ForegroundColor Gray
        $SourceExe = $LocalSource
    } else {
        Write-Host "[INFO] Binario local no encontrado. Descargando desde GitHub..." -ForegroundColor Gray
        $TempFolder = Join-Path $env:TEMP "GitBulk_Installer"
        if (-not (Test-Path $TempFolder)) { New-Item -ItemType Directory -Path $TempFolder | Out-Null }
        $SourceExe = Join-Path $TempFolder $ExeName
        
        Write-Host "      Descargando: $ReleaseUrl" -ForegroundColor DarkGray
        # Re-intentar descarga con TLS 1.2 explícito por si acaso (Windows 10 viejo)
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $ReleaseUrl -OutFile $SourceExe -ErrorAction Stop
    }

    # 3. Despliegue en Program Files
    Write-Host "[1/5] Preparando carpeta de sistema..." -ForegroundColor Gray
    if (Test-Path "$InstallFolder") {
        Write-Host "      Actualizando rastro anterior..." -ForegroundColor DarkGray
        Remove-Item -Path "$InstallFolder" -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Path "$InstallFolder" -Force | Out-Null

    Write-Host "[2/5] Instalando ejecutable principal..." -ForegroundColor Gray
    # IMPORTANTE: Usamos Copy-Item en lugar de Move-Item para no "robar" archivos si es local
    Copy-Item -Path "$SourceExe" -Destination "$InstallFolder\$ExeName" -Force

    # 4. Accesos Directos (Searchable Menu & Desktop)
    Write-Host "[3/5] Creando accesos directos..." -ForegroundColor Gray
    $WshShell = New-Object -ComObject WScript.Shell

    # Menú Inicio
    $StartMenuPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\$AppName.lnk"
    $Shortcut = $WshShell.CreateShortcut($StartMenuPath)
    $Shortcut.TargetPath = "$InstallFolder\$ExeName"
    $Shortcut.WorkingDirectory = "$InstallFolder"
    $Shortcut.Description = "Gestiona tus repositorios Git de forma masiva (GUI)."
    $Shortcut.Save()

    # Escritorio
    $DesktopPath = "$env:Public\Desktop\$AppName.lnk"
    $Shortcut = $WshShell.CreateShortcut($DesktopPath)
    $Shortcut.TargetPath = "$InstallFolder\$ExeName"
    $Shortcut.WorkingDirectory = "$InstallFolder"
    $Shortcut.Save()

    # 5. Integración con el PATH (CLI Ready)
    Write-Host "[4/5] Configurando terminal (PATH)..." -ForegroundColor Gray
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$InstallFolder*") {
        $newPath = if ($currentPath) { "$currentPath;$InstallFolder" } else { $InstallFolder }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
    }

    # 6. Registro de Desinstalación
    Write-Host "[5/5] Registrando software en el sistema..." -ForegroundColor Gray
    $RegistryPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
    if (-not (Test-Path $RegistryPath)) { New-Item -Path $RegistryPath -Force | Out-Null }
    Set-ItemProperty -Path $RegistryPath -Name "DisplayName" -Value "$AppFullName"
    Set-ItemProperty -Path $RegistryPath -Name "DisplayVersion" -Value "$Version"
    Set-ItemProperty -Path $RegistryPath -Name "Publisher" -Value "rezzt-dev"
    Set-ItemProperty -Path $RegistryPath -Name "DisplayIcon" -Value "$InstallFolder\$ExeName"
    Set-ItemProperty -Path $RegistryPath -Name "InstallLocation" -Value "$InstallFolder"
    
    # Uninstaller string robusto
    $UninstallCmd = "powershell.exe -ExecutionPolicy Bypass -Command `"Remove-Item -Path '$InstallFolder' -Recurse -Force; Remove-Item -Path '$StartMenuPath' -Force; Remove-Item -Path '$RegistryPath' -Force`""
    Set-ItemProperty -Path $RegistryPath -Name "UninstallString" -Value $UninstallCmd

    Write-Host "`n[OK] $AppFullName se ha instalado con éxito." -ForegroundColor Green
    Write-Host "      Busca 'GitBulk' en el menú de inicio para comenzar." -ForegroundColor White
} catch {
    Write-Host "`n[FATAL ERROR] La instalación ha fallado." -ForegroundColor Red
    Write-Host "Error detallado: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Por favor, reporta este error si persiste." -ForegroundColor Gray
} finally {
    Read-Host "`nPresiona Enter para finalizar..."
}
