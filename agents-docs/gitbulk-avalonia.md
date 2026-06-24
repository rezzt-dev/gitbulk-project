# GitBulk Avalonia — Hoja de información general

> **Producto:** GitBulk  
> **Versión de referencia:** 1.4.0 (Python)  
> **Versión objetivo:** Reescritura en .NET + Avalonia  
> **Autoría:** Análisis técnico interno  
> **Fecha:** 2026-06-20  
> **Fuentes:** `general-analysis.md`, `tech-analysis.md`, `project-resume.md`

---

## Introducción

Esta hoja resume la propuesta de reescritura de GitBulk sobre .NET, C# y Avalonia UI. El proyecto actual (v1.4.0) está implementado en Python con una interfaz Qt6/PySide6 y una CLI basada en `rich`. Los análisis disponibles concluyen que la base Python es funcional pero acumula deuda técnica significativa, por lo que la estrategia recomendada no es un port mecánico, sino una **reescritura controlada** que conserve la semántica de negocio, los flujos de usuario y los activos visuales, reconstruyendo la arquitectura, la presentación y la infraestructura con estándares enterprise.

---

## 1. Información General

Esta sección describe qué es GitBulk Avalonia, cuál es su propósito, el contexto del proyecto actual y las decisiones estratégicas que justifican la migración a .NET y Avalonia. Aquí se recogen los aspectos de negocio, el alcance funcional y los criterios generales de éxito, antes de entrar en detalles técnicos.

### 1.1. Qué es GitBulk

GitBulk es una herramienta de escritorio multiplataforma (CLI + GUI) diseñada para orquestar operaciones Git masivas sobre cientos de repositorios de forma concurrente. Está orientada a equipos que trabajan con arquitecturas de microservicios, monorepos lógicos distribuidos en disco o entornos donde es necesario mantener sincronizados muchos repositorios sin intervención manual repetitiva.

### 1.2. Propósito de la versión Avalonia

La versión Avalonia tiene como objetivo transformar GitBulk en un producto profesional, mantenible y escalable, aprovechando el ecosistema .NET para:

- Ofrecer una experiencia de escritorio moderna y multiplataforma (Windows, Linux, macOS).
- Mejorar la arquitectura mediante MVVM, inyección de dependencias y separación de capas.
- Resolver los problemas de seguridad, calidad y mantenibilidad detectados en la base Python.
- Facilitar la distribución mediante `dotnet publish` en lugar de PyInstaller.
- Sentar las bases para funcionalidades enterprise: multi-forja, SSO, telemetría opt-in y auditoría.

### 1.3. Contexto del proyecto actual (v1.4.0)

La versión actual resuelve un problema real y cuenta con funcionalidades valiosas, pero presenta limitaciones importantes:

- **Stack:** Python 3.10+, `rich` (CLI), `PySide6` (GUI), `subprocess` (Git), PyInstaller.
- **Arquitectura:** separación conceptual en capas, pero con controladores monolíticos (`main.py`, `main_window.py`).
- **Tests:** 30 tests, de los cuales 20 fallan tras la migración de GitPython a `subprocess`.
- **Seguridad:** credenciales almacenadas en texto plano, binarios no firmados, validación de entradas limitada.
- **GUI:** ventana principal de ~2.366 líneas con bloqueos de UI por operaciones síncronas y falta de cancelación.

### 1.4. Estrategia de migración recomendada

La estrategia no es un port línea a línea, sino una **reescritura controlada** con enfoque de *strangler fig tree*:

1. Conservar conceptos, flujos de usuario, semántica de operaciones y activos visuales.
2. Reescribir el orquestador CLI, la GUI completa, el motor de credenciales, la persistencia y la infraestructura de build/tests.
3. Invertir primero en arquitectura, seguridad y tests; luego en funcionalidad y distribución.
4. Mantener la versión Python operativa hasta que la nueva base alcance paridad funcional.

### 1.5. Criterios de éxito

La versión Avalonia se considerará lista cuando se cumplan, como mínimo, los siguientes criterios:

- Paridad funcional con la versión Python 1.4.0 en CLI.
- GUI Avalonia con todas las operaciones principales disponibles.
- Suite de tests con cobertura mínima del 70 % en Core y Application.
- Tests de integración para operaciones Git críticas.
- Pipeline de build y release automatizado.
- Documentación técnica actualizada.
- Revisión de seguridad aprobada.
- Validación en Windows, Linux y macOS.
- Cero tests fallidos en la suite principal.

---

## 2. Información Técnica

Esta sección profundiza en el stack tecnológico, la arquitectura objetivo, la estructura de la solución, los patrones de diseño, el plan de migración y los riesgos técnicos. Es la referencia principal para arquitectos, desarrolladores senior y responsables de la migración.

### 2.1. Stack tecnológico objetivo

| Componente | Tecnología | Propósito |
|------------|-----------|-----------|
| Runtime | .NET 8/9 | Plataforma de ejecución multiplataforma. |
| GUI | Avalonia UI 11.x | Interfaz gráfica multiplataforma. |
| CLI | Spectre.Console | Renderizado profesional en terminal. |
| Git | LibGit2Sharp + fallback a CLI | Motor de operaciones Git. |
| Serialización | System.Text.Json | Persistencia y snapshots. |
| DI / Logging | Microsoft.Extensions.* | Inyección de dependencias y logging estructurado. |
| Tests | xUnit / NUnit + NSubstitute / Moq | Tests unitarios e integración. |
| Build | `dotnet publish` | Distribución single-file self-contained. |
| CI/CD | GitHub Actions / Azure DevOps | Build, test, análisis estático y release. |

### 2.2. Arquitectura objetivo

Se propone una arquitectura limpia basada en capas y patrones modernos:

```text
GitBulk.sln
├── GitBulk.Core              # Dominio puro: entidades, interfaces, reglas
├── GitBulk.Application       # Casos de uso y servicios de aplicación
├── GitBulk.Infrastructure    # Git, filesystem, API GitHub, configuración
├── GitBulk.CLI               # Aplicación de consola
└── GitBulk.Desktop           # Aplicación Avalonia
```

Cada proyecto tiene una responsabilidad clara:

- `GitBulk.Core`: entidades (`Repository`, `Workspace`), interfaces (`IGitEngine`, `IRepositoryScanner`), enums y excepciones. Sin dependencias externas.
- `GitBulk.Application`: orquestación de casos de uso (`FetchRepositories`, `SyncWorkspace`, etc.). Depende de `Core`.
- `GitBulk.Infrastructure`: implementaciones concretas (`CliGitEngine`, `LibGit2SharpEngine`, `JsonConfigurationService`, `CredentialManager`). Depende de `Core`.
- `GitBulk.CLI`: adaptador de consola con Spectre.Console. Depende de `Application` e `Infrastructure`.
- `GitBulk.Desktop`: adaptador gráfico Avalonia con MVVM. Depende de `Application` e `Infrastructure`.

### 2.3. Patrones de diseño

| Patrón | Uso |
|--------|-----|
| MVVM | Separación View / ViewModel / Model en la GUI Avalonia. |
| Clean Architecture / Vertical Slices | Aislar casos de uso y capas. |
| Dependency Injection | `Microsoft.Extensions.DependencyInjection`. |
| Repository / Provider | Abstraer Git, CI, configuración y persistencia. |
| Command | Operaciones deshacibles y auditables. |
| Options | Configuración tipada y validada. |
| Plugin / Provider | Soporte multi-forja (GitHub, GitLab, Azure DevOps, etc.). |

### 2.4. Estructura inicial de la solución

```text
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
└── GitBulk.Desktop/
    ├── Views/
    ├── ViewModels/
    ├── Models/
    └── Services/

tests/
├── GitBulk.Core.Tests/
├── GitBulk.Application.Tests/
├── GitBulk.Infrastructure.Tests/
└── GitBulk.Desktop.Tests/
```

### 2.5. Componentes principales

#### Motor Git (`IGitEngine`)

- Se recomienda `LibGit2Sharp` como motor principal, con fallback a `System.Diagnostics.Process` para operaciones avanzadas.
- Comandos construidos como listas de argumentos (no strings shell) para evitar inyección.
- Desactivación de prompts interactivos (`GIT_TERMINAL_PROMPT=0` o equivalente).
- Soporte de `CancellationToken` e `IProgress<T>`.

#### Escaneo (`IRepositoryScanner`)

- Recorrido recursivo del directorio raíz buscando carpetas `.git`.
- Lectura de metadatos `.gitbulk.repo.json` para topología de grupos.
- Retorno de modelo tipado en lugar de diccionarios sueltos.

#### Concurrencia (`IWorkerPool`)

- Reemplazo de `ThreadPoolExecutor` por `async/await`, `Task.Parallel` o `Parallel.ForEachAsync`.
- Auto-tuning basado en I/O del disco, con tope de 50 workers.
- Cancelación mediante `CancellationToken`.

#### Autenticación (`IAuthService`)

- Almacenamiento seguro mediante Credential Manager (Windows), Keychain (macOS) o Secret Service (Linux).
- OAuth device flow o PAT seguro.
- Nunca modificar la configuración global de Git del usuario.

#### Configuración (`IConfigurationService`)

- `Microsoft.Extensions.Configuration` + validación de esquema.
- Serialización con `System.Text.Json`.
- Cifrado de valores sensibles en reposo cuando sea necesario.

### 2.6. Plan de migración por fases

| Fase | Semanas | Objetivo |
|------|---------|----------|
| 0 — Fundamentos | 1-2 | Requisitos, stack definitivo, repositorio limpio, ADRs iniciales. |
| 1 — Núcleo Git y configuración | 3-5 | `GitBulk.Core`, `IGitService`, `IRepoScanner`, configuración, tests. |
| 2 — CLI profesional | 6-7 | Spectre.Console, un comando por operación, tests de CLI. |
| 3 — GUI Avalonia | 8-12 | Esqueleto MVVM, escaneo, operaciones, diálogos, localización, tests. |
| 4 — Seguridad y credenciales | 13-14 | Credential store, validación, hardening. |
| 5 — Build, distribución y CI/CD | 15-16 | `dotnet publish`, GitHub Actions, firma, installers. |
| 6 — Funcionalidad enterprise | 17-20+ | Multi-forja, SSH avanzado, `.gitbulk.toml`, telemetría opt-in. |

### 2.7. Deuda técnica heredada

Los análisis identifican los siguientes problemas críticos que la versión Avalonia debe resolver:

| Deuda | Severidad | Acción en Avalonia |
|-------|-----------|-------------------|
| Tests obsoletos (20/30 fallan) | Alta | Nueva suite sobre xUnit/NUnit desde el inicio. |
| `main.py` monolítico (726 líneas) | Alta | Dividir en servicios y casos de uso. |
| `main_window.py` monolítico (~2.366 líneas) | Alta | Reescribir en Avalonia con MVVM. |
| Credenciales en texto plano | Alta | Usar credential store del SO. |
| Binarios no firmados | Alta | Firma de código en CI/CD. |
| Bloqueos de UI / sin cancelación | Media | `async/await` + `CancellationToken`. |
| `clean` sin confirmación en GUI | Media | Diálogo de confirmación obligatorio. |
| Mezcla de idiomas e indentaciones | Baja | `.editorconfig`, StyleCop, Roslyn analyzers. |

### 2.8. Riesgos de migración

| Riesgo | Mitigación |
|--------|------------|
| Pérdida de comportamientos no documentados | Auditoría funcional previa y pruebas de regresión. |
| Diferencias TPL vs ThreadPoolExecutor | Prototipar y medir con cargas reales. |
| Incompatibilidades de LibGit2Sharp | Mantener `CliGitEngine` como alternativa. |
| Paridad visual de la GUI | Definir design system previo en Avalonia. |
| Distribución cross-platform | Validar `dotnet publish` en Windows, Linux y macOS. |
| Curva de aprendizaje del equipo | Capacitación en Avalonia + MVVM. |

---

## 3. Información Funcional

Esta sección resume las capacidades funcionales que la versión Avalonia debe conservar, mejorar o añadir, tomando como base la experiencia de usuario y los flujos de la versión Python 1.4.0.

### 3.1. Operaciones principales

La versión Avalonia debe soportar, como mínimo, el mismo catálogo de operaciones:

`status`, `fetch`, `pull`, `push`, `commit`, `checkout`, `clean`, `export`, `restore`, `current-branch`, `ci-status`, `auth`, `workspace`, `groups`.

Además, se recomienda planificar operaciones avanzadas: `rebase`, `stash`, `merge`, `cherry-pick`, `reset`, `bisect`.

### 3.2. Workspaces y snapshots

- Formato JSON `{ path, url, branch }` para exportar, restaurar y sincronizar estados.
- Sincronización segura: archivar repos que ya no estén en el workspace de referencia en lugar de eliminarlos.
- Soporte a migración de workspaces de la versión Python.

### 3.3. Grupos y metadatos

- Cada repositorio puede declarar grupos mediante `.gitbulk.repo.json` (`{ "groups": ["backend", "fintech"] }`).
- La GUI debe permitir organizar repositorios en una jerarquía virtual de grupos.
- Persistencia del layout virtual de grupos.

### 3.4. Mejoras funcionales propuestas

- Preview de operaciones destructivas con diff/impacto visible.
- Resolución de conflictos y rollback en sincronización de workspaces.
- Soporte multi-forja: GitHub, GitLab, Azure DevOps, Forgejo, Bitbucket.
- SSH avanzado: múltiples claves, ssh-agent, Pageant, 1Password SSH agent.
- Telemetría opt-in y logs de auditoría.

---

## 4. Seguridad y Cumplimiento

Esta sección recoge los aspectos de seguridad que deben abordarse de forma explícita en la versión Avalonia, derivados de los hallazgos críticos detectados en el análisis de la base Python.

### 4.1. Credenciales

- Nunca almacenar tokens en texto plano.
- Usar el credential store nativo del sistema operativo.
- No modificar la configuración global de Git del usuario.
- Implementar OAuth device flow o PAT seguro.

### 4.2. Validación y sanitización

- Validar rutas (anti path traversal), URLs (esquema y host), ramas (caracteres permitidos) y número de workers.
- Construir comandos Git como listas de argumentos.
- No exponer tokens en logs, errores ni salidas de consola.

### 4.3. Operaciones destructivas

- `clean` debe requerir confirmación explícita en CLI y GUI.
- `--dry-run` debe ser realmente inocuo (no ejecutar `fetch --prune`).
- Archivar en lugar de borrar en `workspace sync`.

### 4.4. Distribución

- Firmar binarios con certificado de código.
- Publicar checksums y notas de release firmadas.
- Evaluar licenciamiento de Git / LibGit2Sharp para evitar problemas GPL.

---

## 5. Calidad y Mantenibilidad

Esta sección define los estándares y prácticas de ingeniería que deben regir el desarrollo de la versión Avalonia para evitar reproducir la deuda técnica acumulada en la base Python.

### 5.1. Estándares de código

- C# Coding Conventions de Microsoft.
- `.editorconfig` y analizadores Roslyn / StyleCop.
- Principios SOLID y GRASP.
- Funciones y clases pequeñas (preferiblemente < 150 líneas).

### 5.2. Tests

- Cobertura mínima: Core > 80 %, Application > 70 %.
- Tests unitarios, de integración con repositorios Git temporales y, eventualmente, UI headless con Avalonia.Headless.
- Cero tests fallidos en la suite principal antes de release.

### 5.3. Logging y observabilidad

- Logging estructurado con `Microsoft.Extensions.Logging` + Serilog / NLog.
- Nunca registrar tokens ni rutas sensibles.
- Telemetría opt-in para diagnóstico en producción.

### 5.4. Documentación

- README, ADRs, diagramas de arquitectura.
- Changelog mantenido y releases con notas detalladas.
- Documentación de migración de workspaces y configuración de usuarios.

---

## 6. Recursos y Referencias

Esta sección enumera los documentos y análisis que sirven de fuente para esta hoja de información general.

- `agents-docs/analysis-docs/general-analysis.md` — Análisis de viabilidad de migración a C# y Avalonia.
- `agents-docs/analysis-docs/tech-analysis.md` — Análisis técnico maestro del sistema.
- `agents-docs/project-resume.md` — Guía de proyecto para agentes.
- `AGENTS.md` — Guía de arquitectura, convenciones y estado de tests del proyecto Python.
- `CHANGELOG.md` — Historial de cambios del proyecto.

---

*Fin de la hoja de información general.*
