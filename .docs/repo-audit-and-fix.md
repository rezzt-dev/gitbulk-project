# GitBulk — auditoría y corrección completa del repositorio

> fichero de trabajo para un agente de ia (claude code) que opera en el clon local de la herramienta
> de escritorio (`gitbulk-project/`: cli + gui en python, empaquetada con pyinstaller). contiene todo
> lo necesario para auditar y corregir documentación, aspectos legales, higiene del repositorio y
> release en una sola pasada. vive en `.docs/`, que se versiona en este repositorio.
>
> cómo usarlo: abre claude code en la raíz de este repositorio y escribe
> `lee .docs/repo-audit-and-fix.md y ejecútalo de principio a fin`.

---

## 0. PROMPT DE LANZAMIENTO

```text
Eres el agente responsable de dejar el repositorio GitBulk (herramienta de escritorio cli + gui
para operaciones git masivas) profesional, completo y consistente con la release pública v1.4.0,
en inglés y castellano. Sigue este documento fase por fase, en orden. No es asesoría legal: todo
texto legal que redactes se marca para revisión de un abogado.

Reglas de ejecución:
1. Fase 1 es de solo lectura. Al terminarla, haz TODAS las preguntas de la sección 3 en una sola
   interacción (AskUserQuestion, agrupadas) y espera. No preguntes nada más después, salvo bloqueo real.
   Lo que no se responda se resuelve con el valor "por defecto" de la sección 3 y se anota como
   TODO(owner) en el informe final.
2. Lee antes `CLAUDE.md`, `AGENTS.md`, `.docs/manager.md` y las guías de `.docs/-github-guides/`.
   Son la fuente de verdad: si contradicen este documento, gana el repositorio y lo indicas en el informe.
3. Nunca ejecutes sin confirmación expresa: push (menos aún forzado), reescritura de historial,
   mover o borrar tags, crear/editar/publicar releases o subir binarios, cambiar ajustes del repo en
   GitHub, cambiar la rama por defecto. Prepara el comando exacto y lístalo en el informe final.
4. Verifica toda afirmación contra el código y contra GitHub (`gh`). No inventes datos legales,
   técnicos, cifras ni capturas. Si falta un dato: `TODO(owner): <qué falta>`.
5. Trabaja en una rama nueva `changes/repo-audit-and-fix` creada desde `main`.
   Commits pequeños y temáticos según la sección 6. Sin push ni PR hasta que yo lo apruebe.
6. Todo documento nuevo o modificado debe existir en inglés y en castellano con paridad exacta.
7. No toques `vendor/git/` (MinGit de terceros) ni rompas las URLs `raw.githubusercontent.com/.../main/dist/...`
   que usan el README y la web `gitbulk.rezzt.dev`.
8. Termina con el informe de la sección 8.
```

---

## 1. CONTEXTO VERIFICADO (a 2026-11-06)

hechos comprobados con `git` y `gh`. el agente debe **re-verificarlos**, no darlos por buenos.

| tema | hallazgo |
|---|---|
| repositorio | `https://github.com/rezzt-dev/gitbulk-project` (público). rama por defecto `main`; es la única rama (local y remota). |
| descripción y homepage | descripción en castellano, solo habla de "CLI" y tiene erratas ("recurvisa", doble espacio); homepage `https://gitbulk.rezzt.dev`. sin topics. |
| historial | casi todo commiteado directo en `main`; un solo merge (`cad1950`, `merge \| GitBulk v1.4 - production release`). títulos irregulares: `update` a secas, `fixed`, `Fix error messages…`. |
| tags / releases | tags `v1.0` (sin parche), `v1.1.0`, `v1.2.0`, `v1.3.0`, `v1.4.0`; releases "GitBulk - Version 1.0…1.4", cuerpo narrativo en castellano, sin categorías. `v1.4.0` (Latest) tiene 4 activos: `gitbulk-windows.exe`, `gitbulk-gui-windows.exe`, `gitbulk-linux`, `gitbulk-gui-linux` (GitHub publica su sha256). `v1.3.0` usaba otros nombres (`GitBulk-CLI-Linux`, `GitBulk-GUI-Windows.exe`…). sin `SHA256SUMS`. |
| `main` por delante del tag | `v1.4.0` apunta a `2254497`; `main` tiene 3 commits más: instaladores reescritos (`e6ffe66`), arreglo de persistencia en `auth.py` / `git_ops.py` (`9caff5b`) y un commit `update` que reescribe casi todo el árbol (cambio de finales de línea; `git diff -w` lo reduce a 11 ficheros). nada de eso está en el changelog ni publicado. |
| versión | no hay `pyproject.toml` ni `setup.py`. `v1.4.0` está repetida a mano en `src/gui/translations.py` (`footer_version`, 5 idiomas), `dist/linux/install_{cli,gui}.sh` (`VERSION`), `dist/windows/install_{cli,gui}.ps1` (`$version`) y la insignia de `README.md`. coincide con la última release. |
| changelog | `CHANGELOG.md` (keep a changelog, solo inglés). tiene `## [Unreleased]` con trabajo ya publicado (licencia, pruebas, `--dry-run`…) y `## [0.1.0] — 2026-01-01`; no registra `v1.0`…`v1.4.0`. este cambio añade encima `## SIN PUBLICAR / UNRELEASED` bilingüe. |
| licencia | `LICENSE` MIT, "Copyright (c) 2026 rezzt-dev"; GitHub la detecta (`mit`). el README también dice MIT. ojo: la web (`gitbulk-web-project`) usa otra licencia (no comercial, Juan García Cazallas). |
| terceros redistribuidos | `vendor/git/` versiona MinGit 2.44.0 para windows (339 ficheros, ~108 MB, GPLv2 con `vendor/git/LICENSE.txt`) y se empaqueta en los binarios. los binarios gui llevan PySide6 (LGPLv3) y todos el bootloader de pyinstaller. no hay `NOTICE` ni inventario de licencias de terceros. |
| ficheros de comunidad | solo `README.md` y `LICENSE` (health 42 %). sin `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, plantillas ni `.github/`. |
| ci | no hay `.github/workflows/`. sin dependabot ni renovate. |
| pruebas | `tests/` con 30 pruebas; según `AGENTS.md`, 20 fallan desde la migración de GitPython a `subprocess` (no re-verificado: `pytest` no estaba instalado en la máquina de la auditoría). |
| artefactos versionados | 35 `__pycache__/*.pyc` versionados pese al `.gitignore` (y con la ruta local de la máquina del propietario embebida); `dist/` versiona instaladores y `README-Dist.md`; `build/` y los binarios de `dist/linux/` están ignorados (existen en local). |
| datos personales | `snapshot.json` (versionado) lista rutas y urls de repositorios del propietario; `sync_test.json` es un fixture. sin `.env`, claves ni tokens versionados (`vendor/git/mingw64/etc/ssl/cert.pem` es el almacén público de ca de git). |
| credenciales | `gitbulk auth` guarda el pat en claro en `~/.git-credentials` y fija `credential.helper store` en la config **global** de git del usuario. |
| instaladores | `dist/linux/install_gui.sh` descarga el icono `src/gui/icons/gitbulk_icon.png`, que no está versionado (solo `.svg`). los scripts de build generan `gitbulk-gui.exe` / `GitBulk-GUI`, no los nombres que esperan los instaladores: hay que renombrar a mano. `dist/README-Dist.md` describe nombres antiguos (`GitBulk-GUI.exe`, `gitbulk-cli.exe`). |
| enlaces externos | `README.md`, `dist/README-Dist.md` y la web `gitbulk.rezzt.dev` (`gitbulk-web-project/src/main.ts`) usan `https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/{windows,linux}/install_{cli,gui}.{ps1,sh}` y `https://github.com/rezzt-dev/gitbulk-project`. los instaladores descargan `releases/download/<VERSION>/<binario>`. **no romper esas rutas ni esos nombres** sin avisar. la web muestra "1.4.0" en su badge en castellano pero "1.3.0" en inglés y en el pie; `important-docs/` de la web cita rutas que ya no existen (`dist/cli/install.ps1`). |
| documentación | `project-doc/{en,es}-project-doc.md`; `agents-docs/` y `.docs/` con análisis internos; `README.md` solo en castellano. |

---

## 2. FASES

### Fase 1 — auditoría (solo lectura)

1. `git fetch --all --tags`; compara `main` con `v1.4.0` (`git log --oneline v1.4.0..main`, `git diff -w --stat v1.4.0 main`) y decide qué hay sin publicar.
2. Descarga los 4 activos de `v1.4.0` a un directorio nuevo y vacío fuera del repo; trátalos como no confiables. Calcula `sha256sum` y compáralo con el digest de `gh release view v1.4.0 --json assets`. Si puedes, lista su contenido con `pyi-archive_viewer` para ver de qué código salieron.
3. Inventario real: dependencias de `requirements.txt` (versiones y licencias: `rich`, `PySide6`, `pyinstaller`, `pytest`), MinGit en `vendor/git/` y sus componentes, fuente JetBrains Mono (se pide por nombre, no se embebe), iconos svg de `src/gui/icons/` (origen y licencia), datos que guarda (`~/.git_manager_pro.json`, `~/.git-credentials`, `.gitbulk_archive/`) y llamadas de red (`api.github.com`, `ssh -T git@github.com`).
4. Estado de `README.md`, `dist/README-Dist.md` y `project-doc/{en,es}`: paridad, enlaces rotos y qué falta frente al código (sección 4, fase 5).
5. Busca secretos y datos personales: `git grep -nIE` de tokens, correos y rutas locales; revisa `snapshot.json`, los `.pyc` versionados y la historia (`git log --all -p -- '*.json'`).
6. Ejecuta las pruebas (sección 5) y apunta cuántas fallan y por qué.
7. Entrega el informe de hallazgos (confirmados / refutados / nuevos) y pasa a la sección 3.

### Fase 2 — higiene del repositorio

- `.gitignore`: ya ignora `build/`, `__pycache__/`, `*.pyc` y `*.exe`; quitar del índice lo que se coló (`git rm -r --cached` de los `__pycache__/`), revisar la línea suelta `.exe` y confirmar que `vendor/git/**/*.exe` se versiona a propósito.
- `snapshot.json`: decidir si se sustituye por un ejemplo anónimo (`examples/snapshot.example.json`) y se deja de versionar.
- `vendor/git/` (~108 MB): **proponer** (sin ejecutar) alternativas — descargarlo en el build con `scripts/prepare_portable_git.ps1` en vez de versionarlo, o git lfs — con su impacto. no purgar historial sin orden expresa.
- `.docs/` y `agents-docs/` se versionan: no se proponen dejar de versionar; revisar solo que no contengan datos personales.
- Añadir `.gitattributes` con la política de finales de línea si se confirma que el commit `5b46f1f` fue una conversión crlf/lf.
- Asegurar que `CLAUDE.md` y `AGENTS.md` duplican las guidelines para agentes que no abran `.docs/`.

### Fase 3 — documentos legales (EN + ES, cada uno con paridad)

formato bilingüe: un único fichero con inglés primero y castellano después, separados por encabezados, o `X.md` + `X.es.md` enlazados entre sí. elige uno, justifícalo en una línea y aplícalo a todos.

| fichero | contenido mínimo |
|---|---|
| `LICENSE` | se mantiene MIT (texto en inglés, es el canónico). confirmar titular: "rezzt-dev" frente a "Juan García Cazallas (rezzt-dev)". |
| `NOTICE` y `THIRD_PARTY_LICENSES.md` | MinGit / Git for Windows (GPLv2: oferta de código fuente o enlace a la versión exacta), PySide6 / Qt (LGPLv3: cómo sustituir la librería en un binario onefile), `rich` (MIT), bootloader de pyinstaller (GPL con excepción), iconos. **verifica la licencia de cada uno**. |
| `PRIVACY.md` | qué guarda la herramienta en el equipo (configuración, pat en claro, archivo de repos), qué envía (api de github con el pat del usuario, ssh a github), sin telemetría (verificar), cómo borrar los datos, contacto `contacto@rezzt.dev`. |
| `SECURITY.md` | versiones soportadas (tabla real), canal privado de informe (preguntar), plazos, divulgación coordinada, alcance (almacenamiento del pat, `clean`, ejecución de subprocesos). sin recompensas. |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1 con contacto de cumplimiento. |
| `CONTRIBUTING.md` | setup (`pip install -r requirements.txt`), ejecución, pruebas, build con pyinstaller, convención de commits, changelog bilingüe, reglas no negociables (no versionar binarios, no romper las urls de `dist/`). |
| `.github/` | plantillas de issue y PR bilingües, `CODEOWNERS`, `SUPPORT.md`; workflow de ci si se acuerda (pruebas en linux y windows). |

### Fase 4 — readme y changelog

- `README.md` EN + ES: badges reales (versión, python, licencia MIT, ci si existe), características verificadas, instalación con los instaladores de una línea y descarga manual, verificación del sha256, ejecución desde fuente, estructura, enlaces a `project-doc/`, seguridad (pat en claro) y licencia. Sin superlativos ("senior-level", "alto rendimiento") que no se puedan medir.
- Corregir `dist/README-Dist.md` (nombres reales de los binarios).
- `CHANGELOG.md`: decidir qué hacer con `## [Unreleased]` antiguo (sección 3) y, con la versión acordada, cerrar `## SIN PUBLICAR / UNRELEASED` como `## [x.y.z] — aaaa-mm-dd` (commit con prefijo `changelog`). Comprobar que cada ítem existe en el código.

### Fase 5 — documentación técnica y de usuario (EN + ES)

auditar `project-doc/en-project-doc.md` y `project-doc/es-project-doc.md` contra el código y completar lo que falte, con paridad exacta de secciones, datos y enlaces:

- los 14 comandos reales de `src/view/cli.py` (`fetch`, `pull`, `auth`, `status`, `export`, `restore`, `current-branch`, `clean`, `checkout`, `ci-status`, `workspace`, `groups`, `commit`, `push`) y sus opciones (`-d`, `-w`, `-l`, `--autostash`, `-f`, `-b`, `--dry-run`, `--group`, `-i`, `-m`, `-D`, `--action`, `-n`, `--gui`)
- workspaces (`save`, `load`, `list`, `delete`, `sync`) y archivado en `.gitbulk_archive/`
- grupos con `.gitbulk.repo.json`
- auto-ajuste de hilos (`-w 0`, máximo 50)
- gui: idiomas (`es_ES`, `en_US`, `en_UK`, `de_DE`, `fr_FR`), operaciones destructivas y confirmaciones
- almacenamiento del pat y riesgos
- capturas: solo si puedes generarlas; si no, `TODO(owner): screenshot <pantalla>`

### Fase 6 — versión y release (solo preparar)

preparar, sin ejecutar:

1. número de la siguiente versión para lo que hay en `main` desde `v1.4.0` (sección 3) y el commit `changes` que lo sube en los cinco sitios donde se repite.
2. texto de release en inglés: título `v<x.y.z> — <summary en minúsculas, sin acentos>`, cuerpo = bloque `### ENGLISH` del changelog con categorías `ADDED / CHANGED / FIXED / REMOVED / SECURITY` y la sección `INSTALL & VERIFY`.
3. compilación de los 4 binarios con sus nombres exactos (`.docs/-github-guides/release-guide.md`, sección 5) y `SHA256SUMS`.
4. orden de publicación para no romper los instaladores de `main`: release y binarios publicados en el mismo momento en que `main` recibe el nuevo `VERSION`.
5. impacto en la web: textos de versión de `gitbulk-web-project/src/main.ts` (`heroBadge`, `footSub`) que hay que alinear.
6. comandos `gh` exactos listos para pegar (release, edit, upload), sin ejecutarlos.

### Fase 7 — metadatos de GitHub (lista para que los aplique el propietario)

descripción en inglés (cli + gui), homepage `https://gitbulk.rezzt.dev`, topics (`git`, `cli`, `pyside6`, `python`, `developer-tools`…), social preview, private vulnerability reporting, protección de `main` (pr obligatoria, sin force push), comandos `gh api` exactos.

---

## 3. DECISIONES A PREGUNTAR (una sola vez, tras la fase 1)

| # | pregunta | por defecto si no hay respuesta |
|---|---|---|
| 1 | qué hacer con el `## [Unreleased]` antiguo del changelog | dejarlo intacto con una nota "histórico, publicado entre v1.0 y v1.4.0"; no inventar versiones pasadas |
| 2 | número de la siguiente versión para lo que hay en `main` tras `v1.4.0` | `1.4.1` si solo son arreglos; `1.5.0` si hay funcionalidad |
| 3 | idioma y formato de los docs raíz | `X.md` bilingüe (EN primero, ES después) |
| 4 | titular de la licencia MIT | "rezzt-dev" tal como está; anotar `TODO(owner)` si quiere nombre legal |
| 5 | `vendor/git/` versionado (108 MB) | mantenerlo y documentar la licencia; no purgar historial |
| 6 | `snapshot.json` con datos del propietario | sustituir por un ejemplo anónimo y dejar de versionar el real |
| 7 | correo de contacto para seguridad y conducta | `contacto@rezzt.dev`; sugerir además GitHub private vulnerability reporting |
| 8 | añadir ci (pruebas en linux y windows) | sí, solo pruebas; sin publicar binarios desde ci |
| 9 | firma de código de los ejecutables | no; documentar el sha256 como verificación |
| 10 | titulares y descripción de las releases antiguas | no se editan |

---

## 4. REGLAS DE ESTILO

- commits, changelog, PR y release: `.docs/-github-guides/`. changelog en minúsculas y sin acentos; fechas `aaaa-mm-dd`.
- documentación y readme: castellano e inglés con acentos normales; mismo orden, mismos títulos traducidos, mismas tablas y cifras.
- nombres de ficheros, rutas, comandos e identificadores entre backticks.
- sin emojis decorativos, sin superlativos de marketing, sin afirmaciones de "seguro" o "infalible".
- `clean` y `workspace sync` son operaciones destructivas o que mueven datos: documentarlas con su aviso.

---

## 5. COMPROBACIONES (ejecutar y pegar resultados en el informe)

```bash
# enlaces relativos de todos los markdown (fuera de vendor/)
git ls-files '*.md' ':!vendor' | while read f; do grep -oE '\]\((\./|\.\./)?[^)#h][^)]*\)' "$f" \
  | sed -E 's/^\]\(|\)$//' | while read l; do
    [ -e "$(dirname "$f")/$l" ] || echo "ROTO: $f -> $l"; done; done

# paridad en/es de la documentación
diff <(grep -c '^#' project-doc/en-project-doc.md) <(grep -c '^#' project-doc/es-project-doc.md)

# acentos en items del changelog nuevo (debe salir vacío en las listas)
grep -nP '^- .*[áéíóúñÁÉÍÓÚ]' CHANGELOG.md

# versión repetida: todas deben coincidir
grep -n 'footer_version' src/gui/translations.py; grep -n '^VERSION=\|^\$version' dist/*/install_*

# artefactos versionados que no deberían estarlo
git ls-files | grep -E '__pycache__|\.pyc$|^build/'

# pruebas (sin escribir .pyc en el árbol)
python -m pip install -r requirements.txt
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/ -v -p no:cacheprovider

# arranque desde fuente
python src/main.py status -d .
python src/main.py --gui

# binarios publicados
gh release download v1.4.0 -D <dir-vacio> && (cd <dir-vacio> && sha256sum *)
gh release view v1.4.0 --json assets --jq '.assets[] | .name + " " + .digest'
```

---

## 6. PLAN DE COMMITS (rama `changes/repo-audit-and-fix`)

orden sugerido; ajusta al estado real del repo.

1. `changes | dejar de versionar los pyc y reforzar el .gitignore`
2. `changes | sustituir snapshot.json por un ejemplo anonimo`
3. `update | anadir NOTICE y THIRD_PARTY_LICENSES con mingit y pyside6`
4. `update | anadir la politica de privacidad y security bilingues`
5. `update | anadir code of conduct y contributing en ingles y castellano`
6. `update | anadir plantillas de issue y pr bilingues y SUPPORT`
7. `update | completar la documentacion tecnica de project-doc en ingles y castellano`
8. `update | rehacer el readme bilingue con datos verificados`
9. `changes | anadir la ci de pruebas` (solo si se acordó)
10. `changes | subir la version a <x.y.z> en la gui y los instaladores` (solo si se acordó)
11. `changelog | cerrar la seccion de changelog para la version <x.y.z>`

cada cuerpo: lista `-` de una línea por ítem, qué y por qué, sin ninguna línea de atribución.

---

## 7. DEFINICIÓN DE HECHO

- [ ] ningún hallazgo de la sección 1 queda sin resolver, propuesto o anotado como `TODO(owner)`
- [ ] `LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES.md`, `PRIVACY.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` y `README.md` existen en EN y ES con paridad (la licencia MIT, en su texto canónico)
- [ ] la redistribución de MinGit y PySide6 está documentada con su licencia
- [ ] `project-doc/{en,es}` cubre los 14 comandos, workspaces, grupos, auto-ajuste y gui
- [ ] las comprobaciones de la sección 5 pasan o sus fallos están explicados
- [ ] no hay `.pyc` ni datos personales versionados
- [ ] `CHANGELOG.md` con `## SIN PUBLICAR / UNRELEASED` bilingüe, cerrado con versión y fecha si se acordó
- [ ] propuesta de release en inglés con los 4 binarios, `SHA256SUMS` y orden de publicación listos
- [ ] ninguna acción prohibida de la sección 0 se ha ejecutado sin confirmación
- [ ] las urls de `dist/` que usan el README y la web siguen funcionando o el cambio está documentado

---

## 8. INFORME FINAL (formato de entrega)

1. **resumen**: qué se hizo, en cinco líneas como máximo.
2. **hallazgos**: tabla confirmado / refutado / nuevo, con evidencia (comando o ruta).
3. **ficheros**: creados, modificados y eliminados del índice.
4. **decisiones aplicadas**: las respondidas y las resueltas por defecto.
5. **`TODO(owner)`**: lista numerada de datos que faltan.
6. **para revisión legal**: puntos concretos que debe revisar un abogado (gplv2 de mingit, lgpl de pyside6 en binarios onefile).
7. **acciones pendientes de mi confirmación**: comandos exactos (push, PR, tag, release, ajustes de GitHub).
8. **título y descripción de la PR** en el formato del repositorio, en bloques de código separados.
9. **cambios necesarios en `gitbulk-web-project`**: ficheros y valores concretos (versiones de `src/main.ts`, rutas antiguas de `important-docs/`).
