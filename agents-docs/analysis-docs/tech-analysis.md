# GitBulk — Análisis Técnico Maestro

**Documento de referencia técnica interna para mantenimiento, evolución y reescritura sobre .NET, C#, Avalonia y arquitectura moderna.**

---

## Metadatos del documento

| Campo | Valor |
|-------|-------|
| Producto | GitBulk |
| Versión auditada | 1.4.0 |
| Repositorio | `d:\repositorios\desktop-projects\gitbulk-project` |
| Rama / commit | `main` / `9caff5b` |
| Tecnología actual | Python 3.10+, Rich, PySide6, PyInstaller |
| Tecnología objetivo | .NET, C#, Avalonia UI |
| Autoría del análisis | Auditoría técnica interna basada en inspección de código fuente |
| Fecha de elaboración | 2026-06-20 |

---

## 1. Introducción técnica

### 1.1 Propósito del documento

El presente documento constituye una referencia técnica maestra del sistema GitBulk en su versión 1.4.0. Su objetivo es triple:

1. Servir como fuente de verdad técnica para el equipo de ingeniería responsable del mantenimiento de la aplicación actual.
2. Establecer una base analítica sólida para la reescritura del producto sobre una pila tecnológica moderna (.NET, C#, Avalonia).
3. Documentar decisiones de diseño, deuda técnica, riesgos de seguridad y oportunidades de mejora con el nivel de detalle requerido por un arquitecto de software senior.

El análisis prioriza la arquitectura, la calidad del código, la seguridad y la mantenibilidad sobre la descripción funcional superficial.

### 1.2 Alcance del análisis

Este documento cubre exclusivamente la parte técnica del sistema:

- Código fuente de la aplicación (`src/`).
- Infraestructura de build y distribución (`*.spec`, `scripts/`, `requirements.txt`).
- Suite de pruebas (`tests/`).
- Configuración y persistencia (`persistence/`).
- Recursos gráficos y de estilo (`assets/`, `src/gui/icons/`, `src/gui/theme.qss`).

No se analizan procesos de negocio externos, ni se profundiza en la estrategia de marketing o comercialización del producto.

### 1.3 Público objetivo

- Arquitectos de software.
- Ingenieros senior / staff encargados de la migración a .NET y Avalonia.
- Líderes técnicos responsables de mantenimiento y evolución.
- Auditores de calidad y seguridad.

### 1.4 Supuestos y limitaciones

- El análisis se ha realizado sobre el código fuente disponible en el directorio de trabajo indicado.
- No se ha ejecutado la aplicación en modo interactivo; las conclusiones sobre GUI se derivan de inspección estática de `src/gui/`.
- Algunos aspectos de comportamiento en tiempo de ejecución (rendimiento real, latencia de red, consumo de memoria) son inferidos a partir del diseño del código y no han sido medidos empíricamente.
- Se asume que la versión 1.4.0 es el punto de partida para la migración; cualquier cambio posterior deberá ser reevaluado.

### 1.5 Fuentes de información consideradas

- `AGENTS.md`: guía de proyecto para agentes de codificación; describe arquitectura, convenciones y estado de los tests.
- `src/main.py`: punto de entrada único y orquestador de operaciones.
- `src/view/cli.py`: parsing de argumentos y renderizado de terminal.
- `src/model/`: lógica de negocio (scanner, git_ops, auth, ci_ops, concurrency, archiver, interactive, error_handler).
- `src/persistence/config_repo.py`: persistencia de configuración.
- `src/gui/`: aplicación PySide6, ventana principal, workers, traducciones, iconos y tema.
- `requirements.txt`: dependencias declaradas.
- `gitbulk-gui-windows.spec` y `gitbulk-windows.spec`: configuración de build con PyInstaller.
- `CHANGELOG.md` y `README.md`: contexto funcional y evolutivo.
- `tests/`: suite de pruebas automatizadas.

### 1.6 Validación y revisión adicional

| Aspecto | Estado de validación | Observación |
|---------|---------------------|-------------|
| Estructura de carpetas y archivos | Validada | Inspección directa con `Glob`, `ReadFile` y agentes de exploración. |
| Flujo de ejecución CLI | Validada | Lectura directa de `src/main.py` y `src/view/cli.py`. |
| Comandos y flags soportados | Validada | Confirmada mediante `argparse` en `cli.py`. |
| Motor Git (subprocess) | Validada | Inspección directa de `src/model/git_ops.py`. |
| Resolución de ejecutable Git | Validada | Prioridad bundle → local → PATH confirmada. |
| Concurrencia y auto-tuning | Validada | `src/model/concurrency.py` y uso en `main.py`. |
| Estado de tests | Validada | Ejecución real de `pytest`: 10 pasan, 20 fallan. |
| Estructura GUI | Validada | Lectura directa de `src/gui/app.py`, `main_window.py`, `workers.py`. |
| Bugs detectados en GUI | Parcialmente validada | Detectados por inspección estática; requieren ejecución para confirmación absoluta. |
| Rendimiento real | No validada | Requiere benchmarking en hardware representativo. |
| Uso de memoria | No validado | Requiere profiling. |
| Experiencia de usuario final | Parcialmente validada | Basada en análisis estático de la interfaz y flujo de eventos. |

---

## 2. Visión general del sistema

### 2.1 Qué resuelve la aplicación

GitBulk es una herramienta de escritorio multiplataforma que permite ejecutar operaciones Git de forma masiva y concurrente sobre grandes colecciones de repositorios. Está orientada a arquitecturas de microservicios, monorepos lógicos distribuidos en disco o entornos donde un desarrollador necesita mantener sincronizados cientos de repositorios sin intervención manual repetitiva.

### 2.2 Objetivo funcional del proyecto

Proporcionar una interfaz unificada (CLI y GUI) para:

- Descubrir repositorios Git de forma recursiva dentro de un directorio raíz.
- Ejecutar operaciones de lectura y escritura en paralelo: `status`, `fetch`, `pull`, `push`, `commit`, `checkout`, `clean`.
- Gestionar workspaces persistentes con capacidad de exportar, restaurar y sincronizar estados.
- Organizar repositorios en grupos lógicos mediante metadatos locales.
- Consultar el estado de pipelines CI/CD de GitHub Actions.
- Empaquetar la aplicación como ejecutable independiente mediante PyInstaller.

### 2.3 Flujo general de uso

1. El usuario selecciona un directorio raíz (`-d/--dir` o mediante GUI).
2. El sistema escanea recursivamente buscando carpetas `.git`.
3. Opcionalmente filtra por grupo lógico definido en `.gitbulk.repo.json`.
4. Calcula el grado de concurrencia óptimo o lo toma del parámetro `-w/--workers`.
5. Ejecuta la operación solicitada en paralelo usando `ThreadPoolExecutor`.
6. Presenta resultados agregados con códigos de estado normalizados.
7. Persiste el directorio usado y otros datos de sesión en `~/.git_manager_pro.json`.

### 2.4 Relación entre CLI y GUI

Ambas interfaces comparten la misma base de código:

- **CLI**: se activa cuando el binario no está congelado y se reciben argumentos, o cuando no se indica `--gui`.
- **GUI**: se activa con `--gui` o automáticamente si el binario está congelado por PyInstaller y no hay argumentos.

La lógica de negocio (`model/`) y la persistencia (`persistence/`) son comunes. La CLI renderiza con `rich`; la GUI con `PySide6`.

### 2.5 Dependencias entre componentes

```
main.py
├── view/cli.py (argparse + rich)
├── persistence/config_repo.py (JSON)
├── model/
│   ├── scanner.py
│   ├── git_ops.py
│   ├── auth.py
│   ├── ci_ops.py
│   ├── concurrency.py
│   ├── archiver.py
│   ├── interactive.py
│   └── error_handler.py
└── gui/ (solo si --gui o binario congelado)
    ├── app.py
    ├── main_window.py
    ├── workers.py
    ├── translations.py
    ├── icon_manager.py
    └── theme.qss
```

### 2.6 Rol de cada parte dentro del sistema global

| Componente | Rol |
|------------|-----|
| `src/main.py` | Orquestador, punto de entrada, despacho de operaciones, manejo de progreso. |
| `src/view/cli.py` | Vista de terminal: argumentos, tablas, prompts, banners. |
| `src/model/scanner.py` | Descubrimiento de repositorios y topología de grupos. |
| `src/model/git_ops.py` | Motor de ejecución Git vía subprocess. |
| `src/model/auth.py` | Gestión de credenciales globales y SSH. |
| `src/model/ci_ops.py` | Consulta a GitHub Check Runs API. |
| `src/model/concurrency.py` | Auto-tuning de workers según disco y CPU. |
| `src/model/archiver.py` | Archivado seguro para `workspace sync`. |
| `src/model/interactive.py` | Editor externo y prompts CLI. |
| `src/model/error_handler.py` | Normalización de errores Git. |
| `src/persistence/config_repo.py` | Lectura/escritura de `~/.git_manager_pro.json`. |
| `src/gui/app.py` | Bootstrap de la aplicación Qt. |
| `src/gui/main_window.py` | Ventana principal, árbol, sidebar, diálogos, estado. |
| `src/gui/workers.py` | Hilos de trabajo para escaneo y operaciones. |
| `src/gui/translations.py` | Internacionalización propia (5 idiomas). |
| `src/gui/icon_manager.py` | Gestión de iconos SVG. |
| `src/gui/theme.qss` | Tema oscuro en QSS. |

---

## 3. Análisis de la parte CLI

### 3.1 Estructura y organización

#### 3.1.1 Estructura de carpetas

```
src/
├── main.py              # Punto de entrada y orquestador
├── view/
│   ├── __init__.py      # Re-exporta API pública CLI
│   └── cli.py           # Argumentos y salida de terminal
├── model/
│   ├── __init__.py      # Re-exporta lógica de negocio
│   ├── scanner.py
│   ├── git_ops.py
│   ├── auth.py
│   ├── ci_ops.py
│   ├── concurrency.py
│   ├── archiver.py
│   ├── interactive.py
│   └── error_handler.py
└── persistence/
    ├── __init__.py
    └── config_repo.py
```

#### 3.1.2 Organización de módulos

La organización intenta seguir una arquitectura por capas:

- **Vista (`view/`)**: todo lo relativo a la interfaz de terminal.
- **Modelo (`model/`)**: lógica pura, sin dependencias de UI.
- **Persistencia (`persistence/`)**: lectura/escritura de configuración.

No obstante, como se detalla más adelante, la separación no es estricta.

#### 3.1.3 Entrada principal del programa

`src/main.py` es el único punto de entrada. Contiene la función `main()`, que:

1. Detecta si debe lanzar la GUI (`sys.frozen` + sin argumentos, o `--gui`).
2. En modo CLI, carga configuración, parsea argumentos, valida workers, inicia SSH agent y despacha la operación.

#### 3.1.4 Separación entre lógica, utilidades y presentación

La separación es nominal pero no estricta:

- `view/cli.py` contiene parseo de argumentos y funciones de renderizado (`show_*`).
- `model/` contiene la lógica de negocio.
- Sin embargo, `main.py` acumula lógica de orquestación, filtrado y manejo de progreso que podría pertenecer a una capa de controlador o servicio intermedio.
- `auth.py` y `config_repo.py` mezclan renderizado (`console.print`) con lógica.
- `view/cli.py` importa `model.interactive.get_cli_input`, creando una dependencia inversa vista → modelo.

### 3.2 Lógica técnica

#### 3.2.1 Cómo se ejecuta

El programa se ejecuta como script Python:

```bash
python src/main.py <operation> [flags]
```

O como ejecutable empaquetado por PyInstaller. En modo congelado sin argumentos se lanza la GUI automáticamente.

#### 3.2.2 Flujo de comandos

```
main()
├── Detección GUI/CLI
├── load_config()
├── parse_arguments()
├── Validaciones preliminares
├── calculate_optimal_workers()
├── ensure_ssh_agent()
├── Despacho por operación
│   ├── auth
│   ├── workspace
│   ├── export / restore
│   ├── current-branch / ci-status / groups
│   └── fetch / pull / push / commit / clean / checkout / status
└── show_summary() / persistencia
```

#### 3.2.3 Manejo de argumentos

`src/view/cli.py::parse_arguments` utiliza `argparse.ArgumentParser` con `RawTextHelpFormatter`.

Comandos soportados (`choices`):

```
fetch, pull, auth, status, export, restore, current-branch,
clean, checkout, ci-status, workspace, groups, commit, push
```

Flags principales:

| Flag | Tipo | Operación | Descripción |
|------|------|-----------|-------------|
| `-m/--message` | str | commit | Mensaje de commit. |
| `-D/--body` | str | commit | Cuerpo del mensaje. |
| `--action` | choice | workspace | save, load, list, delete, sync. |
| `-n/--name` | str | workspace | Nombre del workspace. |
| `-d/--dir` | str | global | Directorio raíz. |
| `-w/--workers` | int | global | Concurrencia; 0 = auto. |
| `-l/--log` | str | global | Archivo de log. |
| `--autostash` | bool | pull | Aplica stash automático. |
| `-f/--file` | str | export/restore | Archivo JSON. |
| `-b/--branch` | str | checkout | Rama destino. |
| `--dry-run` | bool | clean/restore | Simulación. |
| `--group` | str | global | Filtro por grupo. |
| `-i/--interactive` | bool | commit | Commit interactivo. |

#### 3.2.4 Validaciones

Validaciones implementadas:

- Workers en rango `[0, 50]`.
- `checkout` requiere `--branch`.
- `--autostash` solo afecta a `pull` (advertencia si no).
- `workspace` requiere `--action`.
- `workspace save/load/delete/sync` requiere `--name`.
- Existencia del archivo JSON para `restore` y `workspace sync`.
- Confirmación interactiva para `clean` destructivo.

Validaciones ausentes o débiles:

- No se valida que `--dir` sea un directorio existente antes de escanear.
- No se valida que `--group` corresponda a un grupo definido.
- No se valida formato ni longitud del token GitHub.
- No se sanitiza `--message`/`--body` antes de pasarlos a `git commit`.

#### 3.2.5 Gestión de errores

- `model/error_handler.py::parse_git_error(stderr: str)` normaliza errores comunes (red, autenticación, conflictos, clones, divergencia).
- `run_git_operation` captura excepciones generales y devuelve `("ERROR", "Engine Exception", repo_path, str(e))`.
- `main.py` registra resultados en un diccionario de conteos y muestra un resumen final.

#### 3.2.6 Casos límite

- Directorio sin `.git`: `find_git_repos` devuelve lista vacía; `run_git_operation` devuelve error controlado.
- Ejecutable Git no encontrado: retorna código `-1`.
- `fetch`/`sync` concatenan `stderr` a `stdout` porque Git suele escribir progreso en `stderr`.
- `clean` no verifica el código de retorno del `fetch --prune`; continúa aunque falle.
- `clone_repo` detecta "already exists" o "existe" en el error; frágil ante distintos locales de Git.
- `checkout` devuelve `IGNORED` cuando no encuentra la rama, lo cual es semánticamente confuso.

### 3.3 Calidad de implementación

#### 3.3.1 Legibilidad

- El código de `main.py` (726 líneas) es difícil de seguir debido a múltiples bloques `if/elif` anidados y lógica repetida.
- `cli.py` es más legible gracias a funciones pequeñas y enfocadas.
- Mezcla de idiomas: mensajes de UI en inglés, pero comentarios y algunas cadenas en español ("analizando repos...").
- Indentación inconsistente: `main.py` y `view/cli.py` usan 2 espacios; el resto del proyecto usa 4 espacios.

#### 3.3.2 Mantenibilidad

- La lógica de orquestación está acoplada a `main.py`, dificultando la extensión con nuevas operaciones.
- La duplicación de bloques `Progress` y de filtrado por grupo incrementa el riesgo de inconsistencias.
- La ausencia de tests de integración para `main.py` dificulta refactorizaciones seguras.

#### 3.3.3 Reutilización

- Las funciones de `model/` son reutilizables por CLI y GUI.
- La interfaz `(status, detail, repo_path, output)` es consistente y aprovechable.
- La vista CLI está demasiado ligada a `rich` como para reutilizarse fuera del entorno terminal.

#### 3.3.4 Acoplamiento

- `main.py` importa `console` directamente desde `view`, acoplando la capa de control a la vista.
- `view/cli.py` depende de `model.interactive.get_cli_input`.
- `auth.py` y `config_repo.py` dependen de `rich.console.Console`.

#### 3.3.5 Cohesión

- `model/` tiene buena cohesión: cada módulo trata un aspecto bien definido.
- `main.py` tiene baja cohesión: mezcla parseo, validación, orquestación, progreso y salida.
- `view/cli.py` tiene buena cohesión en su mayoría.

#### 3.3.6 Duplicación de código

- Bloques `Progress(...)` repetidos aproximadamente 6 veces en `main.py`.
- Lógica de filtrado por grupo repetida en `workspace save`, `export`, `current-branch`, `ci-status` y operaciones masivas.
- Funciones `resource_path` y `_resolve_resource` duplicadas en `gui/app.py` e `icon_manager.py`.

#### 3.3.7 Posibles problemas de diseño

- `main.py` actúa como controlador monolítico. Carece de una capa de servicios o casos de uso.
- No existe patrón de comando ni factoría de operaciones; cada operación se maneja con bloques condicionales.
- No hay inyección de dependencias; todo se importa directamente.
- El mecanismo de logging es manual y limitado: solo escribe a archivo si se indica `--log`.

### 3.4 Seguridad y robustez

#### 3.4.1 Riesgos técnicos

| Riesgo | Severidad | Descripción |
|--------|-----------|-------------|
| Credenciales en texto plano | Alta | PAT almacenado en `~/.git-credentials`. |
| Validación de entrada limitada | Media | `--branch`, `--message`, `--body` no se sanitizan. |
| `clean` destructivo sin rastro | Media | `git clean -xfd` puede eliminar archivos no rastreados de valor. |
| Dependencia de `EDITOR`/`VISUAL` | Baja | `interactive.py` usa el valor del entorno sin validación. |
| `icacls` depende de `USERNAME` | Baja | En entornos atípicos puede fallar silenciosamente. |

#### 3.4.2 Validación de entradas

- Los argumentos se parsean correctamente con tipos.
- Faltan validaciones semánticas: existencia de directorios, grupos, formato de token, longitud de mensajes.
- No se detectan caracteres nulos, escapes ni comandos incrustados en rutas o ramas.

#### 3.4.3 Manejo de rutas

- Uso generalizado de `os.path.abspath` para normalizar rutas.
- `os.path.relpath` para guardar workspaces de forma portable.
- Posible problema: rutas con espacios se pasan correctamente como argumentos de lista, por lo que no hay shell injection.

#### 3.4.4 Manejo de archivos

- `config_repo.py` escribe en el directorio home del usuario.
- `auth.py` restringe permisos del archivo de credenciales.
- El archivo de log no tiene rotación ni límite de tamaño.

#### 3.4.5 Posibles vectores de fallo o abuso

- Un mensaje de commit extremadamente largo podría saturar la línea de comandos o el buffer de Git.
- Un archivo `.gitbulk.repo.json` malicioso con contenido muy grande podría ralentizar el escaneo, aunque solo se lee el campo `groups`.
- Ejecutar `clean` sin confirmación en entornos no interactivos (si se omite el prompt) sería destructivo.

#### 3.4.6 Estrategias de mitigación

- Mantener la construcción de comandos Git como listas de argumentos (ya implementado).
- Añadir validaciones semánticas y sanitización de entradas.
- Considerar almacenamiento de credenciales mediante keyring o DPAPI en lugar de texto plano.
- Implementar `--dry-run` para más operaciones de escritura.
- Añadir logging estructurado con niveles y rotación.

### 3.5 Dependencias y librerías

#### 3.5.1 Librerías utilizadas

| Librería | Versión | Propósito |
|----------|---------|-----------|
| `rich` | `==14.3.3` | Renderizado de tablas, paneles, barras de progreso y prompts en terminal. |
| `PySide6` | `>=6.5.0` | Framework Qt6 para la GUI. |
| `pyinstaller` | `==6.19.0` | Generación de ejecutables standalone. |
| `pytest` | `>=8.0.0` | Ejecución de tests. |

#### 3.5.2 Motivo de uso

- `rich` simplifica la salida terminal y la experiencia visual CLI.
- `PySide6` proporciona widgets nativos multiplataforma para la GUI.
- `pyinstaller` permite distribuir sin requerir Python instalado.
- `pytest` es el estándar de facto para testing en Python.

#### 3.5.3 Riesgos asociados

- `PySide6` es una dependencia pesada para la CLI; el build CLI la excluye explícitamente.
- `rich` está muy ligada a la salida terminal; no es portable a una UI gráfica.
- `pyinstaller` puede generar falsos positivos en antivirus y dificulta la firma de código.

#### 3.5.4 Dependencias innecesarias o prescindibles

- Desde el punto de vista de la CLI, `PySide6` no es necesaria. La separación actual mediante exclusión en `gitbulk-windows.spec` es correcta.
- Para la nueva base .NET, ni `rich` ni `PySide6` son reutilizables directamente.

---

## 4. Análisis de la parte GUI

### 4.1 Estructura y organización

#### 4.1.1 Estructura de la interfaz

```
src/gui/
├── app.py               # Bootstrap QApplication
├── main_window.py       # Ventana principal (~2366 líneas)
├── workers.py           # QThread workers
├── translations.py      # Diccionario de 5 idiomas
├── icon_manager.py      # Gestión de SVG
├── theme.qss            # Estilos dark
├── icons/               # 18 iconos SVG
└── download_actions.py  # Vacío
```

#### 4.1.2 Organización de ventanas, vistas y recursos

- `MainWindow` es una única ventana sin marco (`FramelessWindowHint`) de aproximadamente 2366 líneas.
- Contiene la barra de título custom (`TitleBar`), sidebar, árbol de workspace, status bar y diálogos embebidos.
- Los diálogos (`MoveToDialog`, `CommitHubDialog`, `ConflictHubDialog`, `GroupSummaryDialog`, `SyncPreviewDialog`) están definidos dentro de `main_window.py`.
- Los recursos visuales (iconos SVG, tema QSS) se cargan dinámicamente desde el sistema de archivos o desde el bundle de PyInstaller.

#### 4.1.3 Separación entre UI y lógica

- La lógica de negocio reside en `model/` y es compartida con la CLI.
- Los `workers.py` encapsulan el trabajo pesado en `QThread`.
- Sin embargo, `MainWindow` asume responsabilidades de controlador y gestor de estado, acoplando vista y lógica.
- `main_window.py` importa directamente funciones de `model/`, rompiendo la barrera vista → modelo.

### 4.2 Arquitectura de interfaz

#### 4.2.1 Patrón de diseño usado o sugerido

El código actual no sigue estrictamente MVC ni MVVM. Es un híbrido donde:

- `MainWindow` actúa como vista + controlador + estado.
- `model/` representa el modelo de datos/negocio.
- `workers.py` actúa como capa de servicios asíncronos.

Para la migración a Avalonia se recomienda adoptar **MVVM** de forma explícita.

#### 4.2.2 Relación entre vista, modelo y lógica

```
Vista (MainWindow + widgets Qt)
├── Controlador embebido (eventos, estado)
├── Workers (QThread + ThreadPoolExecutor)
│   └── invocan funciones de model/
└── Persistencia (config_repo.py, ~/.gitbulk_virtual_groups.json)
```

#### 4.2.3 Flujo de interacción con el usuario

1. `app.py` inicia `QApplication`, carga fuentes, icono, tema e idioma.
2. Crea `MainWindow` y restaura la última sesión (`last_directory`).
3. El usuario selecciona un directorio o workspace.
4. `ScannerWorker` escanea repositorios en segundo plano.
5. `MainWindow` reconstruye el árbol (`_rebuild_tree`).
6. El usuario dispara una operación desde la sidebar.
7. `OperationWorker` ejecuta la operación en paralelo y emite señales.
8. La UI actualiza el árbol y el log mediante un timer de 250 ms.

#### 4.2.4 Gestión de estado

Variables clave en `MainWindow`:

- `target_dir`: directorio raíz activo.
- `found_repos`: lista de rutas descubiertas.
- `raw_scan_results`: resultados crudos del scanner (`{path, metadata}`).
- `workspace_data`: fuente única de la jerarquía virtual (grupos/repos).
- `_pending_import_layout`: flag para aplicar layout importado tras escaneo.
- `_found_repo_nodes`: caché de items Qt por ruta.
- `_current_conflicts`: conflictos detectados.

El estado se persiste en:

- `~/.git_manager_pro.json`: directorio, workspaces, idioma.
- `~/.gitbulk_virtual_groups.json`: layout virtual de grupos.

#### 4.2.5 Manejo de eventos

- Señales Qt conectan workers con slots de `MainWindow`.
- Eventos del árbol: click, menú contextual, expansión/colapso.
- Timer de 250 ms para procesar la cola de logs y evitar reflows masivos.
- Drag-and-drop deshabilitado intencionalmente; reorganización mediante diálogos.

### 4.3 Calidad de implementación

#### 4.3.1 Legibilidad

- `main_window.py` es excesivamente grande (2366 líneas) y difícil de navegar.
- Los imports defensivos `try/except ImportError` se repiten en cada módulo GUI, generando ruido.
- Algunos métodos son largos y mezclan construcción de UI, lógica de negocio y persistencia.

#### 4.3.2 Mantenibilidad

- El monolito de `main_window.py` dificulta el mantenimiento y la revisión de código.
- Los diálogos embebidos deberían extraerse a módulos independientes.
- La duplicación de helpers (`resource_path`, `_get_mapped_paths`) incrementa la deuda técnica.

#### 4.3.3 Escalabilidad

- El renderizado del árbol recorre toda la jerarquía en `_rebuild_tree()`. Con cientos de repositorios es aceptable; con miles podría convertirse en cuello de botella.
- La carga de metadatos (`get_repo_metadata`) se ejecuta en el hilo GUI (`_create_repo_row` → `_safe_get_metadata`), lo que congela la interfaz con muchos repositorios o red lenta.

#### 4.3.4 Reutilización

- Los widgets custom (`TrafficLightGroup`, `TitleBar`) podrían reutilizarse si se extraen.
- La lógica de negocio en `model/` es reutilizable por CLI y GUI.
- La traducción y el icon manager están acoplados a Qt; no son directamente portables.

#### 4.3.5 Acoplamiento entre UI y lógica

- Alto acoplamiento: `MainWindow` invoca directamente funciones de `model/`.
- No existe una capa de ViewModel o servicio de aplicación que medie entre UI y modelo.
- Los workers dependen de `model/` directamente.

#### 4.3.6 Problemas de diseño detectables

- Código muerto: `download_actions.py` vacío, `_apply_imported_layout` no se invoca, `_on_item_expanded` y `_on_item_collapsed` vacíos.
- Bug funcional: `focus_on_group` referencia `self.repo_view`, atributo inexistente (el árbol es `self.tree`).
- Bug funcional: `OperationWorker` no pasa `message`/`body` a `run_git_operation`; el commit GUI siempre usa el mensaje por defecto.
- Bug funcional: CI en GUI lee `config.get("github_token")`, pero `config_repo.py` no persiste ese campo.
- Manejo de excepciones silencioso: múltiples bloques `except Exception: pass` ocultan errores.

### 4.4 Usabilidad y experiencia de usuario

#### 4.4.1 Claridad de la interfaz

- Ventana moderna frameless con barra de título estilo macOS.
- Sidebar organizada por secciones: Acciones, Jerarquía, Workspaces, Avanzado, Zona de peligro.
- Árbol con 4 columnas: nombre, rama, estado, detalles.
- Estados visuales con colores semánticos.

#### 4.4.2 Flujo de navegación

- Selección de directorio → escaneo → árbol → operación → resultados.
- Workspaces accesibles desde la sidebar.
- Commit Hub y Conflict Hub como diálogos modales.

#### 4.4.3 Consistencia visual

- Tema oscuro unificado en QSS.
- Fuente JetBrains Mono global.
- Iconos SVG con recolorización, aunque no todos son homogéneos (`fill="currentColor"` vs `fill="#BBBBBB"` fijo).

#### 4.4.4 Manejo de estados vacíos, errores y carga

- Estados vacíos comunicados: "ningún directorio seleccionado", "sin espacios guardados".
- Indicador de progreso de 2 px en la barra inferior.
- Cola de logs con throttling de 250 ms.
- Sin embargo, la operación `clean` en GUI no muestra confirmación previa (a diferencia de la CLI), lo cual es un riesgo de usabilidad y seguridad.

#### 4.4.5 Oportunidades de mejora desde una perspectiva profesional

- Extraer diálogos a archivos propios.
- Implementar MVVM con ViewModels por pantalla.
- Mover la carga de metadatos a un worker.
- Añadir confirmación previa a `clean`.
- Mejorar la retroalimentación de errores (evitar `except Exception: pass`).
- Completar la internacionalización (todas las cadenas deben pasar por `TR()`).
- Implementar cancelación de operaciones largas.

### 4.5 Seguridad y robustez

#### 4.5.1 Riesgos derivados de la interfaz

- `clean` en GUI ejecuta `git clean -xfd` sin confirmación previa.
- No hay flujo de autenticación propio en GUI; CI no funciona por falta de token.
- Carga de metadatos síncrona en hilo principal puede congelar la UI y generar frustración.

#### 4.5.2 Validación visual y funcional

- `SyncPreviewDialog` muestra adiciones y archivados y requiere confirmación.
- `MoveToDialog` previene mover un grupo dentro de sí mismo.
- Falta validación visual de entradas críticas (ramas, mensajes de commit).

#### 4.5.3 Manejo seguro de datos

- El token no se loguea en salidas ni en logs.
- No se almacena `github_token` en el JSON de configuración (lo cual, aunque impide CI, evita filtraciones accidentales).

#### 4.5.4 Resistencia ante errores de usuario

- Operaciones destructivas (`clean`) no están suficientemente protegidas.
- La falta de cancelación dificulta corregir operaciones masivas iniciadas por error.
- Estados de error se muestran en el árbol, pero el manejo silencioso de excepciones puede ocultar fallos importantes.

---

## 5. Arquitectura general

### 5.1 Estilo arquitectónico actual

La aplicación sigue un estilo **por capas con orquestador central**. No adopta formalmente MVC, MVVM, Clean Architecture ni arquitectura hexagonal. La capa de presentación CLI y GUI comparten el mismo modelo de dominio, pero `main.py` y `MainWindow` actúan como controladores monolíticos.

### 5.2 Capas del sistema

```
┌─────────────────────────────────────┐
│  Presentación                       │
│  ├── CLI (view/cli.py + main.py)   │
│  └── GUI (gui/ + PySide6)           │
├─────────────────────────────────────┤
│  Orquestación / Control             │
│  ├── main.py (CLI)                  │
│  └── MainWindow (GUI)               │
├─────────────────────────────────────┤
│  Lógica de negocio                  │
│  └── model/                         │
├─────────────────────────────────────┤
│  Persistencia                       │
│  └── persistence/config_repo.py     │
├─────────────────────────────────────┤
│  Infraestructura externa            │
│  └── Git, GitHub API, sistema       │
└─────────────────────────────────────┘
```

### 5.3 Dependencias entre capas

- `view/` depende de `model/` (inversión parcial debida a `get_cli_input`).
- `persistence/` es independiente, aunque usa `rich` para advertencias.
- `gui/` depende de `model/` y `persistence/`.
- `model/` no depende de `view/` ni de `gui/`.

### 5.4 Separación de responsabilidades

| Responsabilidad | Ubicación actual | Evaluación |
|-----------------|------------------|------------|
| Parseo de argumentos | `view/cli.py` | Correcta. |
| Renderizado terminal | `view/cli.py` | Correcta. |
| Orquestación CLI | `main.py` | Sobrecargada. |
| Ejecución Git | `model/git_ops.py` | Correcta. |
| Escaneo | `model/scanner.py` | Correcta. |
| Concurrencia | `model/concurrency.py` | Correcta. |
| Autenticación | `model/auth.py` | Mezcla renderizado. |
| Configuración | `persistence/config_repo.py` | Mezcla renderizado. |
| Bootstrap GUI | `gui/app.py` | Correcta. |
| Ventana principal | `gui/main_window.py` | Sobrecargada. |
| Workers | `gui/workers.py` | Correcta. |
| Traducciones | `gui/translations.py` | Correcta, pero mejorable. |

### 5.5 Puntos débiles estructurales

1. **Monolitos de control**: `main.py` y `main_window.py` concentran demasiadas responsabilidades.
2. **Falta de capa de aplicación/servicios**: no hay casos de uso explícitos.
3. **Alto acoplamiento GUI**: `MainWindow` depende directamente de `model/`.
4. **Persistencia de layout virtual separada**: dos archivos JSON diferentes con responsabilidades solapadas.
5. **Dependencia global `console`**: usada desde múltiples capas.

### 5.6 Riesgos de evolución futura

- Añadir nuevas operaciones requiere modificar `main.py`, `workers.py`, `translations.py` y `theme.qss`.
- La duplicación de lógica de filtrado por grupo aumenta el riesgo de inconsistencias.
- La falta de tests de integración y GUI dificulta refactorizaciones.
- La migración a .NET requerirá reescribir casi toda la capa de presentación.

---

## 6. Evaluación técnica

### 6.1 Calidad de código

| Aspecto | Puntuación | Justificación |
|---------|------------|---------------|
| Legibilidad | 5/10 | Monolitos en `main.py` y `main_window.py`; mezcla de idiomas; indentación inconsistente. |
| Mantenibilidad | 5/10 | Lógica repetida, acoplamiento, falta de tests de integración. |
| Reutilización | 7/10 | `model/` es reutilizable; vista no tanto. |
| Cohesión | 6/10 | Buena en `model/`; baja en controladores. |
| Acoplamiento | 5/10 | Dependencias directas entre capas. |

### 6.2 Coherencia arquitectónica

- Existe una intención clara de separación por capas.
- No se respeta de forma estricta: controladores mezclan responsabilidades.
- Faltan abstracciones clave (servicios, repositorios, casos de uso).

### 6.3 Mantenibilidad

- La lógica de negocio en `model/` es razonablemente mantenible.
- `main.py` y `main_window.py` requieren refactorización urgente.
- La deuda técnica principal reside en los tests obsoletos y en la duplicación de código.

### 6.4 Testabilidad

- Actualmente **baja** para `main.py` y `MainWindow`.
- `model/` es testable si se mockea `_run_git_command`.
- Los tests existentes están desactualizados: 20 de 30 fallan.
- No hay tests de integración ni de GUI.

### 6.5 Escalabilidad

- El motor concurrente escala bien hasta cientos de repositorios.
- La GUI puede degradarse con miles de repositorios debido a `_rebuild_tree()` y carga síncrona de metadatos.
- El tope de 50 workers es razonable para I/O de red y disco.

### 6.6 Seguridad

- **Subprocess seguro**: comandos Git como listas de argumentos.
- **Prevención de bloqueos**: `GIT_TERMINAL_PROMPT=0`, `CREATE_NO_WINDOW`.
- **Credenciales**: almacenamiento en texto plano; permisos restringidos.
- **Validación de entradas**: insuficiente.
- **Operaciones destructivas**: `clean` en GUI sin confirmación.

### 6.7 Deuda técnica

| Ítem | Impacto | Prioridad |
|------|---------|-----------|
| Tests obsoletos (20/30 fallan) | Alto | Crítica |
| Monolito `main.py` | Alto | Alta |
| Monolito `main_window.py` | Alto | Alta |
| Carga síncrona de metadatos en GUI | Alto | Alta |
| `clean` sin confirmación en GUI | Medio | Alta |
| Duplicación de lógica de filtrado | Medio | Media |
| Mezcla de idiomas / indentación | Bajo | Media |
| Docstring obsoleto en `error_handler.py` | Bajo | Baja |

### 6.8 Facilidad de refactorización

- `model/` puede refactorizarse de forma aislada.
- `main.py` requiere extraer servicios/casos de uso primero.
- `main_window.py` requiere extraer diálogos, ViewModels y servicios.
- La migración a .NET implica reescribir presentación y orquestación; `model/` puede servir como especificación funcional.

### 6.9 Preparación para una base nueva

El proyecto está **parcialmente preparado** para una reescritura:

- **A favor**: la lógica de negocio está relativamente bien separada; las operaciones Git tienen interfaz clara; el dominio es comprensible.
- **En contra**: la falta de tests, la mezcla de responsabilidades y la deuda técnica en GUI obligan a una reescritura significativa más que a una migración mecánica.

---

## 7. Dependencias y tecnologías

### 7.1 Lenguajes usados

| Lenguaje | Uso |
|----------|-----|
| Python 3.10+ | Lógica de aplicación, CLI, GUI, build. |
| QSS (Qt Style Sheets) | Estilos de la GUI. |
| SVG | Iconos de la GUI. |
| Markdown | Documentación. |

### 7.2 Frameworks

| Framework | Versión | Uso |
|-----------|---------|-----|
| PySide6 | >=6.5.0 | GUI nativa con Qt6. |
| Rich | 14.3.3 | Renderizado terminal. |

### 7.3 Librerías

| Librería | Uso |
|----------|-----|
| `argparse` | Parseo de argumentos CLI. |
| `concurrent.futures` | Concurrencia. |
| `subprocess` | Ejecución de Git. |
| `json` | Persistencia y snapshots. |
| `urllib.parse` | Extracción de token de credenciales. |
| `os`, `sys`, `pathlib` | Utilidades del sistema. |

### 7.4 Herramientas de build

| Herramienta | Versión | Uso |
|-------------|---------|-----|
| PyInstaller | 6.19.0 | Empaquetado de ejecutables standalone. |
| PowerShell / Bash | - | Scripts de build e instalación. |

### 7.5 Herramientas de desarrollo

| Herramienta | Uso |
|-------------|-----|
| pytest | Ejecución de tests unitarios. |
| Git | Control de versiones. |

### 7.6 Posibles incompatibilidades con la nueva base

| Tecnología actual | Equivalente .NET/Avalonia | Observación |
|-------------------|---------------------------|-------------|
| PySide6 | Avalonia UI | Reescritura completa de GUI. |
| Rich | Spectre.Console o Terminal.Gui | Reescritura de CLI. |
| QSS | Avalonia styles / themes | Migración de tema visual. |
| PyInstaller | dotnet publish / single-file | Cambio total de pipeline. |
| subprocess | System.Diagnostics.Process o LibGit2Sharp | Posible migración a LibGit2Sharp para mejor rendimiento. |
| ThreadPoolExecutor | Task.Parallel / async/await | Modelo de concurrencia nativo de C#. |
| JSON manual | System.Text.Json | Serialización más eficiente y tipada. |

### 7.7 Recomendaciones para estandarizar la nueva solución

- Usar **.NET 8/9** como runtime objetivo.
- Adoptar **Avalonia UI** para la GUI multiplataforma.
- Usar **Spectre.Console** para la CLI rica en terminal.
- Preferir **LibGit2Sharp** sobre invocaciones a `git` si se busca rendimiento y control, manteniendo fallback a CLI de Git para operaciones avanzadas.
- Usar **System.Text.Json** para serialización.
- Implementar **Microsoft.Extensions.DependencyInjection** para inyección de dependencias.
- Usar **Microsoft.Extensions.Logging** con Serilog o NLog para logging estructurado.
- Adoptar **xUnit / NUnit** con Moq o NSubstitute para tests.
- Estructurar la solución en proyectos separados por capas.

---

## 8. Problemas, riesgos y deuda técnica

### 8.1 Problemas estructurales

1. **Controladores monolíticos**: `main.py` y `main_window.py` asumen demasiadas responsabilidades.
2. **Falta de capa de aplicación**: no existen servicios o casos de uso que aíslen la UI del dominio.
3. **Persistencia dual**: configuración general y layout virtual en archivos separados sin esquema claro.
4. **Dependencia global `console`**: usada desde `view`, `main`, `auth` y `config_repo`.

### 8.2 Problemas de diseño

1. **Duplicación de lógica de filtrado por grupo** en múltiples operaciones.
2. **Duplicación de barras de progreso** en `main.py`.
3. **Duplicación de helpers** (`resource_path`, `_get_mapped_paths`).
4. **No hay patrón de comando** ni factoría de operaciones.
5. **Código muerto** (`download_actions.py`, métodos vacíos en `main_window.py`).

### 8.3 Problemas de calidad

1. **Tests desactualizados**: 20 de 30 fallan.
2. **Mezcla de idiomas** en comentarios y cadenas.
3. **Indentación inconsistente** (2 vs 4 espacios).
4. **Docstrings obsoletos** (`error_handler.py` menciona `GitCommandError` de GitPython).
5. **Manejo silencioso de excepciones** (`except Exception: pass`).
6. **Uso de `os.system("cls")`** no portable ni idempotente.

### 8.4 Riesgos de seguridad

1. **Credenciales en texto plano** en `~/.git-credentials`.
2. **`clean` destructivo sin confirmación en GUI**.
3. **Validación insuficiente** de entradas de usuario.
4. **Dependencia de variables de entorno** (`EDITOR`, `USERNAME`, `SSH_AUTH_SOCK`).
5. **Sin firma ni checksum** de binarios distribuidos.

### 8.5 Riesgos de mantenimiento

1. Dificultad para añadir nuevas operaciones sin tocar múltiples archivos.
2. Falta de tests de integración y GUI.
3. Acoplamiento entre presentación y lógica.
4. Documentación obsoleta en algunos puntos.

### 8.6 Riesgos de migración

1. Reescritura casi total de la capa de presentación.
2. Reescritura de la orquestación en `main.py`.
3. Adaptación del modelo de concurrencia a `async/await` y TPL.
4. Reemplazo de PyInstaller por `dotnet publish`.
5. Migración del tema visual y recursos gráficos.
6. Riesgo de pérdida de comportamientos no documentados si se migra mecánicamente.

### 8.7 Deuda técnica priorizada por impacto

| Prioridad | Ítem | Impacto | Esfuerzo estimado |
|-----------|------|---------|-------------------|
| 1 | Actualizar tests a la API subprocess | Alto | Medio |
| 2 | Refactorizar `main.py` en servicios/casos de uso | Alto | Alto |
| 3 | Refactorizar `main_window.py` (MVVM, diálogos separados) | Alto | Alto |
| 4 | Mover carga de metadatos a worker en GUI | Alto | Medio |
| 5 | Añadir confirmación a `clean` en GUI | Medio | Bajo |
| 6 | Unificar helpers duplicados | Medio | Bajo |
| 7 | Eliminar código muerto | Bajo | Bajo |
| 8 | Normalizar idioma e indentación | Bajo | Medio |

---

## 9. Reutilización para la nueva versión

### 9.1 Qué se puede conservar

1. **Especificación funcional**: catálogo de operaciones, flags, estados de resultado.
2. **Formato de snapshots**: `{path, url, branch}` para export/restore.
3. **Esquema de metadatos de grupo**: `.gitbulk.repo.json` con `{ "groups": [...] }`.
4. **Lógica de resolución de ejecutable Git**: prioridad bundle → local → PATH.
5. **Estrategia de concurrencia**: auto-tuning basado en I/O con tope de 50 workers.
6. **Esquema de configuración**: `last_directory`, `workspaces`, `language`.
7. **Paleta visual y recursos**: tema oscuro, iconos SVG, fuente JetBrains Mono.
8. **Flujo de autenticación**: aunque debería mejorarse el almacenamiento.

### 9.2 Qué se puede adaptar

1. **Parser de `git status --porcelain=v2`**: la lógica de extracción de estado es portable a C#.
2. **Normalizador de errores Git**: `parse_git_error` puede traducirse a un servicio de mensajes.
3. **Topología de grupos**: algoritmo de agrupación portable.
4. **Archivado seguro**: estrategia de mover a `.gitbulk_archive/<repo>_<timestamp>/`.
5. **Workers asíncronos**: concepto de `ScannerWorker` y `OperationWorker`.
6. **Sistema de traducciones**: reemplazar por `.resx` o similar en .NET.

### 9.3 Qué conviene aislar

1. **Motor Git**: encapsular detrás de una interfaz `IGitEngine` para permitir `LibGit2Sharp` o `git` CLI.
2. **Servicio de configuración**: abstraer lectura/escritura de JSON.
3. **Servicio de autenticación**: abstraer obtención y almacenamiento de credenciales.
4. **Servicio de escaneo**: abstraer descubrimiento de repositorios.
5. **Servicio de concurrencia**: abstraer cálculo de workers y ejecución paralela.

### 9.4 Qué conviene reescribir

1. **Capa de presentación CLI**: reemplazar Rich por Spectre.Console.
2. **Capa de presentación GUI**: reescribir en Avalonia con MVVM.
3. **Orquestación**: reemplazar `main.py` por casos de uso y servicios de aplicación.
4. **Manejo de estado en GUI**: reemplazar variables sueltas por ViewModels con INotifyPropertyChanged.
5. **Tests**: reescribir completamente con xUnit/NUnit y mocks modernos.
6. **Build y distribución**: reemplazar PyInstaller por `dotnet publish`.

### 9.5 Qué patrones deberían mantenerse

1. **Separación por capas**: presentación, aplicación, dominio, infraestructura.
2. **Comandos Git como lista de argumentos**: evitar shell injection.
3. **Desactivación de prompts interactivos**: `GIT_TERMINAL_PROMPT=0` o equivalente.
4. **Throttling de actualizaciones UI**: procesar logs/eventos en lotes.
5. **Archivado en lugar de borrado** para `sync`.
6. **Confirmación explícita para operaciones destructivas**.

### 9.6 Qué componentes no deberían migrarse tal cual

1. **`main.py` como orquestador**: debe dividirse en casos de uso.
2. **`MainWindow` monolítico**: debe dividirse en vistas, ViewModels y servicios.
3. **Sistema de traducciones propietario**: reemplazar por mecanismos de .NET.
4. **`icon_manager` basado en Qt**: reemplazar por manejo de recursos de Avalonia.
5. **Persistencia manual de JSON**: reemplazar por serialización tipada con validación de esquema.
6. **`console` global**: reemplazar por logging estructurado e inyección de servicios.

---

## 10. Plan de migración a .NET, C# y Avalonia

### 10.1 Estrategia recomendada

Se recomienda una **reescritura controlada con enfoque de strangler fig tree**:

1. Definir la arquitectura objetivo en .NET.
2. Implementar primero el **núcleo de dominio** (escaneo, operaciones Git, concurrencia, autenticación) como biblioteca .NET.
3. Construir una **CLI mínima funcional** sobre el núcleo.
4. Construir la **GUI en Avalonia** sobre el mismo núcleo.
5. Ir migrando operaciones una a una, validando paridad funcional.
6. Mantener la versión Python operativa hasta que la nueva base alcance paridad.

### 10.2 Arquitectura objetivo

```
GitBulk.sln
├── GitBulk.Core                    # Dominio puro (interfaces, entidades)
├── GitBulk.Application             # Casos de uso y servicios de aplicación
├── GitBulk.Infrastructure          # Git, filesystem, GitHub API, config
├── GitBulk.CLI                     # Aplicación de consola (Spectre.Console)
└── GitBulk.Desktop                 # Aplicación Avalonia (MVVM)
```

### 10.3 Estructura inicial de solución

```
src/
├── GitBulk.Core/
│   ├── Models/
│   │   ├── Repository.cs
│   │   ├── RepositoryGroup.cs
│   │   ├── Workspace.cs
│   │   └── OperationResult.cs
│   ├── Enums/
│   │   └── OperationStatus.cs
│   ├── Interfaces/
│   │   ├── IGitEngine.cs
│   │   ├── IRepositoryScanner.cs
│   │   ├── IConfigurationService.cs
│   │   ├── IAuthService.cs
│   │   └── IWorkerPool.cs
│   └── Exceptions/
├── GitBulk.Application/
│   ├── Services/
│   │   ├── BulkOperationService.cs
│   │   ├── WorkspaceService.cs
│   │   └── AuthService.cs
│   └── UseCases/
│       ├── FetchRepositories.cs
│       ├── PullRepositories.cs
│       ├── CommitRepositories.cs
│       └── SyncWorkspace.cs
├── GitBulk.Infrastructure/
│   ├── Git/
│   │   ├── CliGitEngine.cs
│   │   └── LibGit2SharpEngine.cs
│   ├── Scanning/
│   │   └── FileSystemRepositoryScanner.cs
│   ├── Configuration/
│   │   └── JsonConfigurationService.cs
│   └── Security/
│       └── CredentialManager.cs
├── GitBulk.CLI/
│   ├── Program.cs
│   └── Commands/
├── GitBulk.Desktop/
│   ├── Views/
│   ├── ViewModels/
│   ├── Models/
│   └── Services/
└── tests/
    ├── GitBulk.Core.Tests
    ├── GitBulk.Application.Tests
    ├── GitBulk.Infrastructure.Tests
    └── GitBulk.Desktop.Tests
```

### 10.4 Capas y responsabilidades

| Proyecto | Responsabilidad |
|----------|-----------------|
| `GitBulk.Core` | Entidades, interfaces, reglas de negocio puras. Sin dependencias externas. |
| `GitBulk.Application` | Orquestación de casos de uso, coordinación de servicios. Depende de `Core`. |
| `GitBulk.Infrastructure` | Implementaciones concretas de Git, filesystem, API, configuración. Depende de `Core`. |
| `GitBulk.CLI` | Adaptador de consola. Depende de `Application` e `Infrastructure`. |
| `GitBulk.Desktop` | Adaptador gráfico Avalonia. Depende de `Application` e `Infrastructure`. |

### 10.5 Recomendación de patrón UI

Se recomienda **MVVM (Model-View-ViewModel)** para la aplicación Avalonia:

- **Model**: entidades del dominio (`Repository`, `Workspace`).
- **View**: vistas XAML (`MainView`, `RepositoryTreeView`, `CommitHubView`).
- **ViewModel**: `MainViewModel`, `RepositoryNodeViewModel`, `OperationViewModel`.
- Uso de `CommunityToolkit.Mvvm` para reducir boilerplate (`ObservableObject`, `[ObservableProperty]`, `[RelayCommand]`).
- Navegación mediante un `NavigationService` inyectado.

### 10.6 Priorización de módulos

| Fase | Módulo | Justificación |
|------|--------|---------------|
| 1 | Core + Scanner + GitEngine | Base de todo el sistema. |
| 2 | Configuración + AuthService | Requerido para sesiones y CI. |
| 3 | CLI básica (status, fetch, pull) | Permite validar el núcleo. |
| 4 | Operaciones de escritura (commit, push, clean) | Añaden complejidad; requieren tests sólidos. |
| 5 | Workspaces (export/restore/sync) | Requiere escaneo y GitEngine estables. |
| 6 | CI Status | Depende de autenticación y GitHub API. |
| 7 | GUI Avalonia | Se construye sobre el núcleo ya validado. |

### 10.7 Orden de reconstrucción

1. Crear solución y proyectos base.
2. Definir interfaces de dominio (`IGitEngine`, `IRepositoryScanner`, etc.).
3. Implementar `FileSystemRepositoryScanner` y modelo de grupos.
4. Implementar `CliGitEngine` con parseo de `status --porcelain=v2`.
5. Implementar `BulkOperationService` con `Parallel.ForEachAsync` o `Task.WhenAll`.
6. Implementar `JsonConfigurationService` con `System.Text.Json`.
7. Implementar `AuthService` con CredentialManager / DPAPI / keyring.
8. Construir CLI con Spectre.Console.
9. Construir GUI Avalonia con MVVM.
10. Escribir tests unitarios e integración.
11. Configurar CI/CD y `dotnet publish` para distribución.

### 10.8 Riesgos de migración

| Riesgo | Mitigación |
|--------|------------|
| Pérdida de comportamientos no documentados | Realizar auditoría funcional previa y pruebas de regresión. |
| Diferencias en concurrencia TPL vs ThreadPoolExecutor | Prototipar y medir con cargas reales. |
| Incompatibilidades de LibGit2Sharp | Mantener `CliGitEngine` como alternativa. |
| Paridad visual de la GUI | Definir design system previo en Avalonia. |
| Distribución cross-platform | Validar `dotnet publish` para Windows, Linux y macOS. |
| Curva de aprendizaje del equipo | Capacitación en Avalonia + MVVM. |

### 10.9 Criterios para considerar la nueva base lista

1. Paridad funcional con la versión Python 1.4.0 en CLI.
2. GUI con todas las operaciones principales disponibles.
3. Suite de tests con cobertura mínima del 70% en Core y Application.
4. Tests de integración para operaciones Git críticas.
5. Pipeline de build y release automatizado.
6. Documentación técnica actualizada.
7. Revisión de seguridad aprobada (credenciales, validación de entradas, operaciones destructivas).
8. Validación en Windows, Linux y macOS.
9. Migración de workspaces y configuración de usuarios documentada.
10. Cero tests fallidos en la suite principal.

---

## 11. Recomendación profesional final

### 11.1 Qué haría para llevar el proyecto a nivel empresarial

1. **Reescribir la base sobre .NET y Avalonia** siguiendo los principios de Clean Architecture y MVVM.
2. **Eliminar los monolitos de control** (`main.py`, `main_window.py`) en favor de servicios y casos de uso.
3. **Implementar una suite de tests robusta** desde el día cero: unitarios, integración y, eventualmente, UI.
4. **Adoptar logging estructurado** con niveles, correlación de operaciones y rotación.
5. **Mejorar la seguridad de credenciales** usando Credential Manager (Windows), Keychain (macOS) o Secret Service (Linux).
6. **Añadir telemetría y diagnósticos** opcionales para detectar fallos en producción.
7. **Establecer un pipeline CI/CD** con build, test, análisis estático y firma de binarios.
8. **Documentar APIs internas** y decisiones de arquitectura en ADRs (Architecture Decision Records).

### 11.2 Qué decisiones de ingeniería tomaría

1. **Usar `LibGit2Sharp` como motor principal**, con fallback a CLI de Git para operaciones no soportadas.
2. **Modelar operaciones como comandos inmutables** con un handler por operación.
3. **Aplicar inyección de dependencias** desde el punto de entrada.
4. **Usar `System.Text.Json` con source generators** para mejor rendimiento.
5. **Adoptar `async/await` y `Channel<T>`** para comunicación entre workers y UI.
6. **Diseñar el tema visual como resource dictionary de Avalonia**, no como QSS.
7. **Mantener la marca y la estética** (dark theme, JetBrains Mono, iconos SVG).

### 11.3 Qué estándares aplicaría

1. **C# Coding Conventions** de Microsoft.
2. **Principios SOLID** y **GRASP**.
3. **Clean Architecture** o **Hexagonal Architecture**.
4. **Conventional Commits** para historial de cambios.
5. **Semantic Versioning** para versionado.
6. **OWASP ASVS** para revisión de seguridad.
7. **ISO 25010** para evaluación de calidad.

### 11.4 Qué prácticas de mantenimiento, calidad y documentación impondría

1. **Code review obligatorio** para todo cambio en `main`.
2. **Análisis estático** con SonarQube, Roslyn analyzers y editorconfig.
3. **Cobertura de tests mínima** por proyecto (Core > 80%, Application > 70%).
4. **Tests de integración** que ejecuten operaciones Git reales en repositorios temporales.
5. **Documentación técnica viva**: README, ADRs, comentarios de API y diagramas de arquitectura.
6. **Changelog mantenido** y releases con notas detalladas.
7. **Gestión de deuda técnica** mediante backlog visible y priorizado.
8. **Revisiones de seguridad trimestrales**.

### 11.5 Qué faltaría para considerarlo un proyecto robusto y escalable

| Área | Estado actual | Requerido |
|------|---------------|-----------|
| Arquitectura limpia | Parcial | Completa separación de capas. |
| Tests | 20/30 fallan | Suite verde y completa. |
| Logging | Manual | Estructurado y configurable. |
| Seguridad de credenciales | Texto plano | Almacenamiento seguro del SO. |
| CI/CD | No presente | Pipeline automatizado. |
| Documentación técnica | Básica | Completa y actualizada. |
| Build moderno | PyInstaller | `dotnet publish` + single-file. |
| Escalabilidad GUI | Limitada | Virtualización y async completo. |
| Cancelación de operaciones | No existe | Implementar en workers. |
| Telemetría/diagnósticos | No existe | Opcional y respetuosa con privacidad. |

---

## Apéndice A — Estado de la suite de tests

```
collected 30 items
20 failed, 10 passed
```

### Tests que pasan (10)

- Todos los tests de `tests/test_auth.py` (7).
- `test_directorio_sin_git_devuelve_error` en `tests/test_git_ops.py` (1).
- `test_ruta_inexistente_devuelve_lista_vacia` y `test_directorio_vacio_devuelve_lista_vacia` en `tests/test_scanner.py` (2).

### Tests que fallan (20)

- `tests/test_error_handler.py` (6): `parse_git_error` ahora espera `str`; los tests pasan `MagicMock` / `GitCommandError`.
- `tests/test_git_ops.py` (10): mockean `model.git_ops.Repo` (GitPython), pero el módulo ya no usa `Repo`.
- `tests/test_scanner.py` (4): `find_git_repos` devuelve diccionarios; los tests esperaban lista de strings.

### Recomendación

Antes de cualquier migración, estabilizar la suite actual actualizando los mocks a la API subprocess, o bien descartarla y diseñar una nueva suite sobre la base .NET.

---

## Apéndice B — Hallazgos de seguridad priorizados

| Prioridad | Hallazgo | Acción recomendada |
|-----------|----------|-------------------|
| Crítica | Almacenamiento de PAT en texto plano | Migrar a Credential Manager / DPAPI / keyring. |
| Alta | `clean` sin confirmación en GUI | Añadir diálogo de confirmación. |
| Media | Validación insuficiente de entradas | Implementar validadores semánticos. |
| Media | Dependencia de variables de entorno críticas | Normalizar y validar valores por defecto. |
| Baja | Logging manual sin rotación | Implementar logging estructurado. |

---

## Apéndice C — Glosario técnico

| Término | Definición |
|---------|------------|
| **PAT** | Personal Access Token; token de acceso personal de GitHub. |
| **Porcelain v2** | Formato estable y parseable de `git status`. |
| **MinGit** | Distribución portable mínima de Git para Windows. |
| **PyInstaller** | Herramienta para empaquetar aplicaciones Python como ejecutables. |
| **Avalonia** | Framework UI multiplataforma para .NET. |
| **MVVM** | Model-View-ViewModel; patrón de presentación. |
| **TPL** | Task Parallel Library; biblioteca de concurrencia de .NET. |
| **LibGit2Sharp** | Binding .NET para la librería nativa libgit2. |

---

**Fin del documento.**
