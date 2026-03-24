 $host.ui.rawui.windowtitle = "instalador de gitbulk"
write-host "compilando e instalando gitbulk cli localmente..." -foregroundcolor cyan

 # definir rutas ->
$targetfolder = "$env:userprofile\.gitbulk"
$exe_path = "$targetfolder\gitbulk.exe"


 # crear carpeta oculta en el perfil del usuario si no existe
if (-not (test-path -path $targetfolder)) {
  new-item -itemtype directory -path $targetfolder | out-null
}

 # compilar el ejecutable localmente
write-host "iniciando proceso de compilacion con build.bat..."
& "..\build\build.bat"

if (-not (test-path "..\..\dist\gitbulk-windows\gitbulk-windows.exe")) {
    write-host "error: falló la compilación local." -foregroundcolor red
    exit
}

write-host "copiando el ejecutable generado..."
copy-item -Path "..\..\dist\gitbulk-windows\gitbulk-windows.exe" -Destination $exe_path -Force
write-host "ok: archivo instalado exitosamente." -foregroundcolor green

 # agregar la carpeta al path de windows
write-host "configurando variables de entorno..."
$userpath = [environment]::getenvironmentvariable("path", "user")

if ($userpath -notmatch [regex]::escape($targetfolder)) {
  $newpath = if ($userpath) { "$userpath;$targetfolder" } else { $targetfolder }
  [environment]::setenvironmentvariable("path", $newpath, "user")
  write-host "ok: gitbulk anadido al path correctamente." -foregroundcolor green
} else {
  write-host "ok: gitbulk ya estaba configurado en el path." -foregroundcolor yellow
}


 # mensaje de instalacion completada/existosa
write-host "`n=========================================" -foregroundcolor cyan
write-host "  ¡instalacion completada con exito!     " -foregroundcolor green
write-host "=========================================" -foregroundcolor cyan
write-host "por favor, cierra esta terminal y abre una nueva."
write-host "luego simplemente escribe: gitbulk --help"