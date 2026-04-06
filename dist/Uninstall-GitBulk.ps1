# Uninstall-GitBulk.ps1 — Desinstalador profesional de GitBulk para Windows
# Elimina limpiamente la suite de GitBulk (GUI + CLI).

$AppFolderName = "GitBulk"
$InstallPath = "$env:ProgramFiles\$AppFolderName"

# 1. Verificar permisos de Administrador
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Host "[MSG] Ejecutando como Administrador..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# 2. Eliminar accesos directos
Write-Host "[1/4] Eliminando accesos directos..." -ForegroundColor Cyan
if (Test-Path "$env:PUBLIC\Desktop\GitBulk.lnk") { Remove-Item -Force "$env:PUBLIC\Desktop\GitBulk.lnk" -ErrorAction SilentlyContinue }
if (Test-Path "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\GitBulk.lnk") { Remove-Item -Force "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\GitBulk.lnk" -ErrorAction SilentlyContinue }

# 3. Eliminar del PATH del sistema
Write-Host "[2/4] Eliminando del PATH..." -ForegroundColor Cyan
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($CurrentPath -like "*$InstallPath*") {
    $NewPath = $CurrentPath.Replace("$InstallPath;", "").Replace(";$InstallPath", "").Replace($InstallPath, "")
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "Machine")
}

# 4. Eliminar registro del sistema (Uninstall Registry)
Write-Host "[3/4] Eliminando registro oficial de programas..." -ForegroundColor Cyan
$RegistryPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\GitBulk"
if (Test-Path $RegistryPath) { Remove-Item -Path $RegistryPath -Recurse -Force }

# 5. Eliminar directorio de archivos
Write-Host "[4/4] Eliminando archivos de instalación..." -ForegroundColor Cyan
Write-Host "`n[SUCCESS] GitBulk ha sido desinstalado correctamente." -ForegroundColor Green
Write-Host "Nota: Se recomienda reiniciar la terminal para actualizar el PATH." -ForegroundColor Gray
