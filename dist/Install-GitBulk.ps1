# Install-GitBulk.ps1 — En instalador profesional de GitBulk para Windows
# Se encarga de la instalación completa de la suite (GUI + CLI).

$AppFolderName = "GitBulk"
$InstallPath = "$env:ProgramFiles\$AppFolderName"
# La ubicación de origen es relativa a la carpeta 'dist/' donde reside este script
$SourcePath = "$PSScriptRoot\App_GUI\GitBulk"
$StartupPath = "$InstallPath\GitBulk.exe"
$IconPath = "$InstallPath\assets\gitbulk.ico"

# 1. Verificar permisos de Administrador
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Host "[MSG] Ejecutando como Administrador..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# 2. Verificar existencia de los archivos de build (o clonar desde GitHub si es Web-Installer)
if (-not (Test-Path $SourcePath)) {
    Write-Host "[MSG] No se detectan archivos locales. Iniciando descarga desde GitHub..." -ForegroundColor Yellow
    $TempDownload = Join-Path $env:TEMP "gitbulk_webinstall_$(Get-Random)"
    git clone https://github.com/rezzt-dev/gitbulk-project.git $TempDownload
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] No se pudo clonar el repositorio. Verifica tu conexión y 'git'." -ForegroundColor Red
        exit
    }
    # Redefinimos SourcePath hacia la descarga temporal
    $SourcePath = "$TempDownload\dist\App_GUI\GitBulk"
    if (-not (Test-Path $SourcePath)) {
        Write-Host "[ERROR] El repositorio no contiene los binarios en la ruta esperada." -ForegroundColor Red
        Remove-Item -Recurse -Force $TempDownload
        exit
    }
}

# 3. Crear directorio de instalación y desplegar
Write-Host "[1/5] Registrando aplicación en $InstallPath..." -ForegroundColor Cyan
if (Test-Path $InstallPath) { Remove-Item -Recurse -Force $InstallPath }
New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
Copy-Item -Path "$SourcePath\*" -Destination $InstallPath -Recurse -Force

# 4. Accesos Directos
Write-Host "[2/5] Creando accesos directos..." -ForegroundColor Cyan
$WshShell = New-Object -ComObject WScript.Shell
$DesktopLnk = "$env:PUBLIC\Desktop\GitBulk.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopLnk)
$Shortcut.TargetPath = $StartupPath
$Shortcut.IconLocation = "$IconPath,0"
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.Save()

$StartMenuLnk = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\GitBulk.lnk"
$Shortcut = $WshShell.CreateShortcut($StartMenuLnk)
$Shortcut.TargetPath = $StartupPath
$Shortcut.IconLocation = "$IconPath,0"
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.Save()

# 5. Integración con el PATH del sistema
Write-Host "[3/5] Configurando terminal (PATH)..." -ForegroundColor Cyan
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($CurrentPath -notlike "*$InstallPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$InstallPath", "Machine")
}

# 6. Registro oficial en Windows
Write-Host "[4/5] Registrando desinstalador oficial de Windows..." -ForegroundColor Cyan
$RegistryPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\GitBulk"
if (-not (Test-Path $RegistryPath)) { New-Item -Path $RegistryPath -Force | Out-Null }
Set-ItemProperty -Path $RegistryPath -Name "DisplayName" -Value "GitBulk (GUI & CLI)"
Set-ItemProperty -Path $RegistryPath -Name "DisplayIcon" -Value $IconPath
Set-ItemProperty -Path $RegistryPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$InstallPath\Uninstall-GitBulk.ps1`""
Set-ItemProperty -Path $RegistryPath -Name "Publisher" -Value "rezzt-dev"
Set-ItemProperty -Path $RegistryPath -Name "InstallLocation" -Value $InstallPath

# 7. Copiar el desinstalador a la carpeta final
Copy-Item -Path "$PSScriptRoot\Uninstall-GitBulk.ps1" -Destination $InstallPath -Force

Write-Host "`n[SUCCESS] GitBulk ha sido instalado con éxito!" -ForegroundColor Green
Write-Host "Comando CLI habilitado: 'gitbulk'" -ForegroundColor Gray
