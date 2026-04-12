# GitBulk: orquestador de alto rendimiento para flujos masivos de git

<p align="center">
  <img src="https://img.shields.io/badge/versión-1.4.0-blue?style=for-the-badge" alt="versión">
  <img src="https://img.shields.io/badge/motor-python_3.10-green?style=for-the-badge" alt="tecnología">
  <img src="https://img.shields.io/badge/licencia-mit-orange?style=for-the-badge" alt="licencia">
</p>

GitBulk es una herramienta integral (cli y gui) diseñada para la gestión concurrente de cientos de repositorios git de forma simultánea. optimizada para arquitecturas de microservicios y despliegues a gran escala, permite centralizar operaciones críticas sin latencia manual.

> [!NOTE]
> **identidad de marca**: el proyecto sigue una línea estética senior con cumplimiento estricto de minúsculas en todas sus interfaces y documentación técnica, una marca personal de desarrollo de **rezzt-dev**.

---

## 🚀 instalación rápida (producción)

puedes desplegar el entorno completo con un solo comando en tu terminal:

### GitBulk desktop (gui + cli)
**windows (powershell):**
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install.ps1" | iex
```

**linux (bash):**
```bash
curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install_linux.sh" | bash
```

---

## evolución v1.4: características avanzadas

### 1. gestión de workspaces (espacios de trabajo)
gestione múltiples entornos raíz y sincronice estados lógicos. guarde una snapshot de su árbol de directorios y restáurela instantáneamente en cualquier máquina, automatizando clonaciones y archivado de repositorios no deseados.

### 2. motor de concurrencia optimizado
olvídese de configurar hilos manualmente. el motor de GitBulk incluye **auto-tuning** basado en hardware (`-w 0`). la herramienta perfila su cpu e io para asignar el paralelismo óptimo sin saturar el sistema.

### 3. group inspector & logical topology
organice sus proyectos mediante etiquetas lógicas (ej: `fintech`, `backend`, `frontend`). filtre cualquier operación masiva para que afecte solo a un grupo específico de la topología.

---

## catálogo de operaciones cli

GitBulk proporciona una suite completa de comandos para el ciclo de vida de desarrollo:

| comando | descripción técnica |
| :--- | :--- |
| `status` | análisis visual del árbol de trabajo y divergencia remota. |
| `fetch` / `pull` | sincronización remota asíncrona con soporte `--autostash`. |
| `push` / `commit` | operaciones de escritura masiva con diálogos interactivos. |
| `workspace` | gestión de perfiles: `save`, `load`, `list`, `delete`, `sync`. |
| `groups` | inspección de la topología lógica y descriptores de proyecto. |
| `checkout` | transición Head masiva hacia ramas objetivo (`-b branch`). |
| `ci-status` | monitorización de pipelines de github actions en tiempo real. |
| `clean` | **[destructivo]** eliminación de ramas muertas y archivos no rastreados. |

---

## ecosistema y arquitectura

- **motor nativo**: migración completa a procesos `subprocess` para máxima velocidad y mínima dependencia.
- **gui de alta fidelidad**: interfaz dinámica multi-lenguaje (es, us, uk, de, fr) con soporte para modo oscuro nativo.
- **hubs de gestión**: diálogos avanzados para resolución de conflictos (`conflicthub`) y previsualización de sincronización.
- **diagnóstico inteligente**: detección automática de agentes ssh y validación de conectividad.

---

## documentación completa

para una inmersión profunda en la arquitectura y escenarios de uso avanzado, consulta los manuales técnicos:

📕 [documentación en castellano](project-doc/es-project-doc.md)  
📘 [english technical documentation](project-doc/en-project-doc.md)

---

desarrollado con ❤️ por **rezzt-dev**.  
*GitBulk: senior-level workspace management.*
