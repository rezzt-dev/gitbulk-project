# GUIA DE RELEASES

> como preparar el titulo, la descripcion, el tag y los binarios de una release
> de github. se aplica cuando la pr de version ya esta fusionada en `main`. lee
> antes `agent-rules.md`: la release no lleva ningun rastro de ia.

---

## 1. REQUISITOS PREVIOS

1. `CHANGELOG.md` tiene la version cerrada como `## [x.y.z] — aaaa-mm-dd` (ver `changelog-guide.md`).
2. la pr de version hacia `main` esta fusionada con "create a merge commit".
3. no hay version en un fichero de proyecto (no existe `pyproject.toml` ni `setup.py`): el numero vive repetido y se sube a mano en `src/gui/translations.py` (`footer_version`, en los cinco idiomas), `dist/linux/install_cli.sh` y `dist/linux/install_gui.sh` (`VERSION`), `dist/windows/install_cli.ps1` y `dist/windows/install_gui.ps1` (`$version`) y la insignia de `README.md`.
4. los cuatro binarios de pyinstaller estan compilados desde el commit que se va a etiquetar (ver seccion 5) y existe su `SHA256SUMS`.
5. no hay ci en el repositorio: hasta que exista, se ejecuta `python -m pytest tests/ -v` en local y se arrancan la cli (`gitbulk status -d <carpeta>`) y la gui de cada binario antes de publicar. cuando exista ci, debe estar en verde sobre el commit que se etiqueta.

---

## 2. TAG

- siempre `v<x.y.z>`, mismo numero que la cabecera del changelog, sin sufijos extra (ejemplo: `v1.5.0`). el tag historico `v1.0` no sigue este formato y no se toca.
- se crea sobre el commit de merge en `main`, nunca sobre una rama de trabajo.
- no se mueve ni se borra un tag ya publicado; si hay un error, se publica una version nueva.
- los instaladores de `dist/` descargan `releases/download/<VERSION>/<binario>`: el tag y sus binarios deben existir en cuanto `main` lleve el nuevo `VERSION`, o las instalaciones de una linea fallan.

```
git tag -a v<x.y.z> -m "v<x.y.z>"
git push origin v<x.y.z>
```

---

## 3. TITULO

```
v<x.y.z> — <resumen corto en ingles>
```

- en ingles, minusculas y sin acentos; resume las 2-3 entradas mas relevantes.
- ejemplo: `v1.5.0 — self-update command, per-folder config & wider dry-run`.
- las releases antiguas (`GitBulk - Version 1.4` y anteriores) no siguen este formato y no se editan sin orden expresa.

---

## 4. DESCRIPCION

- **solo en ingles**: la release es la cara publica del proyecto.
- reutiliza el bloque `### ENGLISH` de la version cerrada, con sus encabezados `####` en mayusculas, pero en version corta: de 3 a 6 items por categoria, agrupando cambios relacionados (misma regla de sintesis que `pr-merge-guide.md`, seccion 2).
- se omite la categoria sin items; no se reordenan las categorias.
- cierra con una seccion de instalacion y verificacion:

```
#### INSTALL & VERIFY

- install with the one-line installers in `README.md` or download the binary for your system from the assets
- check the download with `sha256sum -c SHA256SUMS --ignore-missing`
```

- sin lineas de atribucion ni enlaces a herramientas de ia.

---

## 5. ACTIVOS

- exactamente estos cuatro binarios, con estos nombres, porque los instaladores de `dist/` los descargan por nombre:

| activo | sale de | instalador que lo usa |
|---|---|---|
| `gitbulk-windows.exe` | `gitbulk-windows.spec` (cli) | `dist/windows/install_cli.ps1` |
| `gitbulk-gui-windows.exe` | `scripts/build_gui_windows.ps1` (gui; genera `dist/windows/gitbulk-gui.exe`, se renombra) | `dist/windows/install_gui.ps1` |
| `gitbulk-linux` | `gitbulk-linux.spec` (cli) | `dist/linux/install_cli.sh` |
| `gitbulk-gui-linux` | `gitbulk-gui-linux.spec` (gui; `scripts/build_gui_linux.sh` genera `GitBulk-GUI`, se renombra) | `dist/linux/install_gui.sh` |

- mas `SHA256SUMS` con el `sha256sum` de los cuatro; nada mas (sin `build/`, sin `.spec`, sin configuraciones locales ni `snapshot.json`).
- los binarios de windows llevan dentro mingit (`vendor/git/`, gplv2): su licencia viaja con el binario.
- no hay firma de codigo de los ejecutables; si se anade, se documenta aqui.

---

## 6. COMANDO

```
gh release create v<x.y.z> gitbulk-windows.exe gitbulk-gui-windows.exe gitbulk-linux gitbulk-gui-linux SHA256SUMS --title "<titulo>" --notes-file <fichero>
```

se entrega el comando sin ejecutar; publicar una release es visible para todos y exige confirmacion (ver `agent-rules.md`).

---

## 7. LISTA DE COMPROBACION

- [ ] el tag coincide con la cabecera del changelog y con `VERSION` / `$version` de los cuatro instaladores.
- [ ] titulo y descripcion estan en ingles.
- [ ] los items salen del bloque `### ENGLISH` del changelog.
- [ ] los cuatro binarios y `SHA256SUMS` corresponden a la misma compilacion y al commit etiquetado.
- [ ] no hay atribucion de ia ni datos sensibles.
