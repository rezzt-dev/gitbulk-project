# documentación técnica de GitBulk

## índice
1. [introducción](#introducción)
2. [características principales](#características-principales)
3. [arquitectura del motor](#arquitectura-del-motor)
4. [instalación y despliegue](#instalación-y-despliegue)
5. [gestión de autenticación](#gestión-de-autenticación)
6. [sistema de workspaces](#sistema-de-workspaces)
7. [organización por grupos](#organización-por-grupos)
8. [catálogo de operaciones](#catálogo-de-operaciones)
9. [banderas y parámetros globales](#banderas-y-parámetros-globales)

---

## introducción

GitBulk es una solución integral (cli y gui) de alto rendimiento para la orquestación masiva de repositorios git. diseñada para arquitecturas de microservicios, la herramienta elimina la latencia operativa mediante procesamiento concurrente y un motor nativo optimizado.

---

## características principales

- **concurrencia inteligente**: auto-tuning basado en hardware para maximizar el througput de disco y red.
- **espacios de trabajo (workspaces)**: persistencia de entornos completos con sincronización de estado lógica.
- **branding corporativo**: interfaz minimalista con tipografía moderna y cumplimiento estricto de minúsculas.
- **soporte multi-idioma nativo**: traducción completa a español, inglés (us/uk), alemán y francés.
- **gestión visual de conflictos**: hubs dedicados para resolución de errores y commits masivos.

---

## arquitectura del motor

el motor de GitBulk ha sido reprogramado para utilizar llamadas nativas a subprocess, evitando las limitaciones de librerías externas. incluye:
- **renderizado throttling**: actualizaciones de ui agrupadas (250ms) para fluidez extrema.
- **caché de iconos**: optimización de i/o mediante persistencia estática de recursos visuales.
- **diagnóstico ssh**: detección automática y configuración de agentes ssh para túneles seguros.

---

## instalación y despliegue

### instaladores web

**windows (powershell):**
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install.ps1" | iex
```

**linux (bash):**
```bash
curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install_linux.sh" | bash
```

---

## gestión de autenticación

GitBulk utiliza tokens de acceso personal (pat) almacenados de forma segura en las credenciales del sistema.
```bash
gitbulk auth
```

---

## sistema de workspaces

los workspaces permiten guardar y restaurar estados completos de directorios raíz.
- **save**: congela la topología actual.
- **load**: clona automáticamente repositorios faltantes.
- **sync**: concilia el estado del disco con una definición de referencia, archivando repositorios no deseados.

---

## organización por grupos

mediante el inspector de grupos, GitBulk detecta etiquetas en `.gitbulk.repo.json` para agrupar repositorios de forma lógica (ej: backend, frontend, microservices).

---

## catálogo de operaciones

### `status`
analiza divergencias y estados locales de forma visual.

### `commit` / `push`
operaciones de escritura masiva con soporte para mensajes personalizados y diálogos interactivos.

### `workspace`
comandos: `save`, `load`, `list`, `delete`, `sync`.

### `groups`
inspección de la topología lógica del espacio de trabajo.

### `fetch` / `pull`
sincronización remota con soporte para `--autostash`.

### `ci-status`
monitorización de pipelines de github actions en tiempo real.

---

## banderas y parámetros globales

- `-d, --dir`: directorio raíz (persiste entre sesiones).
- `-w, --workers`: hilos concurrentes. usa `0` para auto-tuning automático.
- `--gui`: inicia la interfaz gráfica nativa.
- `--dry-run`: previsualización de operaciones destructivas.
