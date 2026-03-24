$host.ui.rawui.windowtitle = "instalador de gitbulk"
write-host "instalando gitbulk cli..." -foregroundcolor cyan

 # definir rutas ->
$targetfolder = "$env:userprofile\.gitbulk"
$exe_url = "https://github.com/rezzt-dev/gitbulk-project/releases/download/v1.2.0/gitbulk-windows.exe"
$exe_path = "$targetfolder\gitbulk.exe"


 # crear carpeta oculta en el perfil del usuario si no existe
if (-not (test-path -path $targetfolder)) {
  new-item -itemtype directory -path $targetfolder | out-null
}


 # descargar el ejecutable desde github releases
write-host "descargando gitbulk.exe desde github..."
try {
  invoke-webrequest -uri $exe_url -outfile $exe_path -usebasicparsing
  write-host "ok: archivo descargado exitosamente." -foregroundcolor green
} catch {
  write-host "error: no se pudo descargar el archivo. verifica la url del release." -foregroundcolor red
  exit
}


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