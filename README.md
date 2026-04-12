# GitBulk Project

Una herramienta profesional de línea de comandos (CLI) e interfaz gráfica (GUI) nativa escrita en Python para gestionar y actualizar múltiples repositorios Git de forma masiva y concurrente.

> **Documentación del Proyecto:** Consulta guías de instalación, arquitecturas y uso avanzado en el manual oficial: [Español (ES)](project-doc/es-project-doc.md) | [English (EN)](project-doc/en-project-doc.md).

En lugar de procesar directorios de forma secuencial, **GitBulk** localiza recursivamente todos los repositorios en una ruta específica y ejecuta operaciones de forma concurrente en paralelo (ej. `fetch`, `pull`, `checkout`), reduciendo drásticamente los tiempos de ejecución en entornos con gran volumen de proyectos.

---

## Instalación del Proyecto

GitBulk puede instalarse directamente desde la terminal utilizando los siguientes comandos oficiales:

### GitBulk Desktop (GUI + CLI) - Recomendado

Versión completa con interfaz gráfica, accesos directos e integración total en el sistema operativo.

**Windows (PowerShell):**
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/windows/install_gui.ps1" | iex
```

**Linux (Bash):**
```bash
curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/linux/install_gui.sh" | bash
```

### GitBulk CLI (Terminal Only)

Distribución ligera optimizada exclusivamente para entornos de terminal.

**Windows (PowerShell):**
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/windows/install_cli.ps1" | iex
```

**Linux / macOS (Bash):**
```bash
curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/linux/install_cli.sh" | bash
```

---

## Características Principales

- **Interfaz Gráfica Nativa:** Aplicación de escritorio con diseño moderno, soporte para modo oscuro y retroalimentación visual en tiempo real.
- **Ejecución Concurrente:** Utiliza un motor de hilos optimizado (`ThreadPoolExecutor`) para procesar múltiples repositorios simultáneamente.
- **Persistencia de Sesión:** Sistema de gestión de configuración que preserva el estado del espacio de trabajo y las preferencias del usuario.
- **Interfaz Visual Técnica:** Salida por consola formateada mediante la librería `rich`, proporcionando informes de estado precisos y códigos de color normalizados.
- **Arquitectura Modular:** Basado en patrones de diseño que separan la lógica de negocio (Model) de la interacción con el usuario (View) y la persistencia de datos.

---

## Requisitos de Sistema

- **Git:** Debe estar instalado y accesible globalmente a través de la variable de entorno PATH.
- **Windows (GUI/Desktop):** Distribución autónoma "One-File" (no requiere instalación previa de Python).
- **Linux/macOS:** Requiere **Python 3.7+** para la ejecución de la versión CLI.

---

## Guía de Uso (CLI)

Ejecute la herramienta desde la terminal especificando la operación y los parámetros requeridos.

### Operaciones Disponibles

| Operación | Descripción |
| :--- | :--- |
| `fetch` | Descarga metadatos del historial remoto sin integrar cambios locales. |
| `pull` | Actualiza la rama activa aplicando una estrategia de integración `fast-forward only`. |
| `status` | Analiza el estado del árbol de trabajo (archivos modificados, divergencia de commits). |
| `current-branch` | Genera una topología compacta de las ramas locales frente a las referencias remotas. |
| `checkout` | Realiza una transición masiva de HEAD hacia una rama objetivo (`-b branch`). |
| `clean` | **[Operación Destructiva]** Prunea ramas remotas e inactiva y elimina archivos no rastreados. |
| `ci-status` | Consulta el estado de ejecución de pipelines en GitHub Actions mediante tokens PAT. |
| `export` | Genera un snapshot en formato JSON de la estructura de repositorios y orígenes. |
| `restore` | Clona y reconstruye espacios de trabajo basándose en un archivo de snapshot JSON. |
| `auth` | Gestiona de forma segura las credenciales y Personal Access Tokens (PAT) de GitHub. |

### Argumentos y Banderas

| Flag | Alias | Descripción | Valor por Defecto |
| :--- | :--- | :--- | :--- |
| `--dir <Path>` | `-d` | Directorio raíz para el escaneo recursivo de repositorios. | *(Última ruta utilizada)* |
| `--workers <N>` | `-w` | Número de hilos simultáneos (Límite superior: 50). | `5` |
| `--autostash` | — | Automatiza el `stash` preventivo durante operaciones de actualización. | `False` |
| `--branch <Name>` | `-b` | Especifica la rama objetivo (Requerido para la operación `checkout`). | — |
| `--file <Path>` | `-f` | Archivo JSON de referencia para `export` y `restore`. | `snapshot.json` |
| `--dry-run` | — | Simula la ejecución sin aplicar cambios reales en el sistema de archivos. | `False` |
| `--gui` | — | Fuerza el arranque de la interfaz gráfica de usuario. | — |
| `--log <Path>` | `-l` | Redirige el flujo de salida de la terminal a un archivo log persistente. | — |

---

## Interfaz Gráfica de Usuario (GUI)

En instalaciones **Desktop**, la interfaz gráfica puede lanzarse directamente desde el menú de aplicaciones del sistema. Para ejecuciones manuales desde terminal, utilice la bandera de control:

```bash
gitbulk --gui
```

La GUI proporciona un entorno centralizado para la supervisión de proyectos, facilitando la ejecución de comandos complejos mediante una interacción visual simplificada.

---

## Arquitectura y Persistencia

En su primera ejecución, GitBulk inicializa un esquema de configuración persistente en el directorio personal del usuario (ej. `~/.git_manager_pro.json`). Este archivo centraliza la gestión de estados, rutas de trabajo y tokens de acceso, garantizando una experiencia de usuario coherente entre sesiones.

---

**GitBulk** es un proyecto de código abierto. Puede contribuir al desarrollo o reportar incidencias a través del repositorio oficial.

*Desarrollado por rezzt-dev.*
