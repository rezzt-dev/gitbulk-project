# Documentación Técnica de GitBulk

## Índice
1. [Introducción](#introducción)
2. [Características Principales](#características-principales)
3. [Instalación y Despliegue](#instalación-y-despliegue)
4. [Gestión de Autenticación](#gestión-de-autenticación)
5. [Catálogo de Operaciones](#catálogo-de-operaciones)
6. [Banderas y Parámetros Globales](#banderas-y-parámetros-globales)
7. [Escenarios de Uso Avanzado](#escenarios-de-uso-avanzado)

---

## Introducción

GitBulk es una solución integral (CLI y GUI) de alto rendimiento construida en Python para la orquestación masiva de repositorios Git. Diseñada para arquitecturas de microservicios y entornos multi-repositorio, la herramienta mitiga la latencia operativa mediante el procesamiento concurrente, permitiendo ejecutar ciclos de vida de desarrollo completos sobre cientos de proyectos de forma simultánea y segura.

---

## Características Principales

- **Procesamiento Concurrente**: Motor basado en `ThreadPoolExecutor` que elimina cuellos de botella en operaciones de red y disco.
- **Interfaz Gráfica Nativa (Desktop)**: Aplicación de alta fidelidad para entornos Windows y Linux con soporte para modo oscuro y monitorización en tiempo real.
- **Resiliencia Operativa**: Mecanismos de protección integrados con prompts interactivos para prevenir la pérdida accidental de datos en comandos destructivos.
- **Reporte Técnico de Alta Densidad**: Visualización mediante la librería `rich` que proporciona matrices compactas, estados codificados por color y telemetría de progreso.
- **Integración de CI / GitHub Actions**: Consulta nativa del estado de los pipelines directamente desde la terminal o la interfaz de escritorio.

---

## Instalación y Despliegue

### Instalación Recomendada (Web Installer)

GitBulk proporciona instaladores optimizados de un solo paso que configuran automáticamente los binarios, los accesos directos y las variables de entorno.

**Windows (PowerShell):**
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install.ps1" | iex
```

**Linux (Bash):**
```bash
curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install_linux.sh" | bash
```

### Configuración desde Código Fuente (Desarrollo)

Para entornos de desarrollo o personalización, clone el repositorio e instale el árbol de dependencias:

```bash
git clone https://github.com/rezzt-dev/gitbulk-project.git
cd gitbulk-project
pip install -r requirements.txt
```

---

## Gestión de Autenticación

Ciertas operaciones (como `fetch` en repositorios privados o consultas de `ci-status`) requieren credenciales válidas. GitBulk centraliza esta gestión solicitando un Personal Access Token (PAT) una sola vez y almacenándolo de forma segura en las credenciales del sistema operativo.

Para configurar el entorno de acceso:
```bash
gitbulk auth
```
Este comando configura el helper global de Git, permitiendo que las operaciones posteriores se ejecuten de forma silenciosa sin interrupciones por solicitud de credenciales.

---

## Catálogo de Operaciones

### `status`
Analiza el estado del árbol de trabajo y reporta la divergencia respecto a las ramas remotas.
**Estados**: `[CLEAN]`, `[MODIFIED]`, `[AHEAD]`, `[BEHIND]`.

### `fetch`
Descarga metadatos del historial remoto sin integrar cambios en las ramas locales.
**Estados**: `[OK]`, `[UPDATES]`.

### `pull`
Actualiza la rama activa mediante una estrategia de integración `fast-forward only`.
**Banderas sugeridas**: `--autostash`.

### `checkout`
Realiza una transición masiva de `HEAD` hacia la rama especificada.
**Parámetro requerido**: `-b <branch_name>`.

### `current-branch`
Genera un mapa topográfico ultra-compacto que muestra la rama activa y las referencias locales/remotas.

### `clean`
**Operación Destructiva**: Ejecuta `git fetch --prune` y `git clean -xfd`. Elimina referencias remotas muertas y archivos no rastreados. Requiere confirmación interactiva.

### `ci-status`
Consulta asíncrona a la API de GitHub para reportar el estado de los pipelines de integración continua.
**Estados**: `[PASS]`, `[FAIL]`, `[PEND]`, `[NONE]`.

### `export` / `restore`
Permiten la persistencia y reconstrucción de espacios de trabajo masivos mediante archivos de snapshot JSON. Útil para procesos de onboarding instantáneo.

---

## Banderas y Parámetros Globales

- `-d, --dir <ruta>`: Directorio raíz para el escaneo recursivo. Conserva la persistencia de la última ruta utilizada.
- `-w, --workers <n>`: Número de hilos concurrentes (Límite: 50). Defecto: `5`.
- `-l, --log <ruta>`: Redirección del volcado técnico a un archivo log persistente.
- `-b, --branch <nombre>`: Rama objetivo para operaciones de transición (`checkout`).
- `--autostash`: Automatiza el resguardo de cambios locales previo a una actualización.
- `--dry-run`: Previsualización de cambios sin aplicación real (Soportado en `clean` y `restore`).
- `--gui`: Fuerza el lanzamiento de la interfaz gráfica de usuario.

---

## Escenarios de Uso Avanzado

### Sincronización con AutoStash
Para evitar bloqueos por cambios locales no finalizados durante un pull masivo, la instrucción `--autostash` permite alojar, actualizar y recomponer automáticamente el parche de trabajo.
```bash
gitbulk pull --autostash
```

### Ejecución en Entornos de CI (Piped Execution)
GitBulk ha sido diseñado respetando los estándares de procesos POSIX. Operaciones interactivas como `clean` detectan automáticamente la ausencia de un terminal (`tty`) o inyecciones de `stdin` nulo, abortando la ejecución de forma segura para evitar fallos catastróficos en pipelines automatizados.
