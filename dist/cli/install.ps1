 $host.ui.rawui.windowtitle = "instalador de gitbulk"
write-host "compilando e instalando gitbulk cli localmente..." -foregroundcolor cyan

 # definir rutas ->
$targetfolder = "$env:userprofile\.gitbulk"
$exe_path = "$targetfolder\gitbulk.exe"
$temp_dir = "$env:temp\gitbulk_src_$(Get-Random)"


 # crear carpeta oculta en el perfil del usuario si no existe
if (-not (test-path -path $targetfolder)) {
  new-item -itemtype directory -path $targetfolder | out-null
}

write-host "descargando todo el codigo fuente..."
git clone https://github.com/rezzt-dev/gitbulk-project.git $temp_dir
if ($LASTEXITCODE -ne 0) {
    write-host "error: falló la clonación del repositorio remoto." -foregroundcolor red
    exit
}

Push-Location $temp_dir

write-host "instalando entorno y dependencias..."
pip install -r requirements.txt

write-host "compilando el ejecutable localmente..."
pyinstaller gitbulk-windows.spec --clean

if (-not (test-path "dist\gitbulk-windows\gitbulk-windows.exe")) {
    write-host "error: falló la compilación local." -foregroundcolor red
    Pop-Location
    Remove-Item -Recurse -Force $temp_dir
    exit
}

write-host "moviendo el ejecutable a la ruta final..."
copy-item -Path "dist\gitbulk-windows\gitbulk-windows.exe" -Destination $exe_path -Force
write-host "ok: limpieza terminada e instalacion exitosa." -foregroundcolor green

Pop-Location
Remove-Item -Recurse -Force $temp_dir

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