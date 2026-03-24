## GitBulk Project

Una herramienta profesional de línea de comandos (CLI) escrita en Python para gestionar y actualizar múltiples repositorios Git de forma masiva y concurrente.

> **Documentación del Proyecto:** Consulta guías de instalación, arquitecturas y uso avanzado en el manual oficial: [Español (ES)](project-doc/es-project-doc.md) | [English (EN)](project-doc/en-project-doc.md).

En lugar de ir carpeta por carpeta ejecutando comandos, **GitBulk** busca recursivamente todos los repositorios en una ruta específica y ejecuta operaciones de forma silenciosa en paralelo (ej. `fetch`, `checkout`, `clean`), reduciendo drásticamente el tiempo de espera.

---
### Instalacion del Proyecto
#### Windows 10/11
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/cli/install.ps1" | iex
```
#### Linux / macOS
```bash
curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/cli/install.sh" | bash
```

---
### Caracteristicas Principales
 - **Ejecuccion Concurrente:** utiliza multiples hilos (`ThreadPoolExecutor`) para procesar varios repositorios al mismo tiempo.
 - **Memoria de Sesion (Persistencia):** recuerda automaticamente el ultimo directorio analizado para que no tengas que escribir la ruta cada vez.
 - **Interfaz Visual Clara:** salida en terminal formateada con colores (exitos en verde, errores en rojo) y resumen final de operaciones.
 - **Arquitectura Limpia:** construido bajo principios de separacion de responsabilidades (modelo, vista, persistencia).

---
### Estructura del Proyecto
el codigo esta organizado de forma modular para facilitar su mantenimiento y escalabilidad:
```text
git_manager_pro/
├── README.md
└── src/
  ├── main.py        # Controlador: Conecta todas las capas.
  ├── model/         # Lógica de negocio (búsqueda de repos, comandos git).
  ├── persistence/   # Gestión de configuración de usuario (JSON).
  └── view/          # Interfaz de usuario (parseo CLI y prints a color).
```

---
### Requisitos
 - **Python 3.7+** (no requiere librerias externas de terceros).
 - **Git** instalado y accesible desde la variable de entorno PATH del sistema.

---
### Uso
Abre tu terminal, sitúate en la carpeta raíz del proyecto y ejecuta el programa como un script.

#### Operaciones Disponibles
GitBulk soporta comandos masivos para simplificar tu flujo de trabajo de cientos de repositorios en 1 clic:
| Comando          | Descripción                                                                                   |
|------------------|-----------------------------------------------------------------------------------------------|
| `fetch`          | Ejecuta rutinas de actualización de origen remoto sin forzar cambios a la historia local.     |
| `pull`           | Descarga de red los cambios sin retraso bajo formato libre de conflictos *fast-forward only*. |
| `status`         | Analiza cuántos commits adelantados, atrasados o archivos modificados hay sin revisar.        |
| `current-branch` | Genera de forma super-compacta una vista topográfica del árbol de ramas locales vs remotas.   |
| `export`         | Compila un diccionario en JSON (Snapshot) extrayendo las rutas remotas exactas locales.       |
| `restore`        | Reconstruye carpetas y clona infraestructura de software masiva analizando su matriz remota.  |
| `auth`           | Automatiza el guardado de PAT tokens (Tokens de Acceso) de forma segura.                      |

#### Argumentos Extendidos
| Flag / Bandera     | Atajo | Descripción                                                        | Predeterminado |
|--------------------|-------|--------------------------------------------------------------------|----------------|
| `--dir <Ruta>`     | `-d`  | Carpeta fundamental que desencadena el escáner del `main.py`.      | *(Última Ruta)*|
| `--workers <N>`    | `-w`  | Define el límite de tareas ejecutadas en paralelo a la vez.        | `5`            |
| `--autostash`      |  —    | Congela ramas momentáneamente antes de un pull con bloqueos extra. | `False`        |
| `--log <Archivo>`  | `-l`  | Fuerza volcado físico de salida terminal (Git Outputs).            | *(Omita Vacio)*|
| `--file <Archivo>` | `-f`  | Inyecta el archivo JSON fuente a comandos de Backup masivo.        | `snapshot.json`|

#### Ejemplos
```bash
# Sincroniza red a 12 hilos congelando temporalmente modificaciones para prevenir rechazo estricto "non-fast-forward"
python -m src.main pull -d "/home/usuario/proyectos" -w 12 --autostash

# Visualiza topográficamente el workspace y todas sus ramas por defecto
python -m src.main current-branch

# Creación veloz y automática de toda la red local en otra computadora (Onboarding Instantáneo)
python -m src.main export -f infraestructura_backend.json
python -m src.main restore -f infraestructura_backend.json -w 20
```

---
### Como Funciona la Persistencia
la primera vez que ejecutas el programa, se crea un archivo de configuracion oculto en tu carpeta de usuario (ej. `C:\Users\Usuario\.git_manager_pro.json` o `~/.git_manager_pro.json`). este archivo almacena tus preferencias, como la ultima ruta sobre lo que operaste, mejorando la comodidad en usos futuros.

con esto, tu proyecto no solo tiene un codigo de primera categoria, sino tambien una documentacion que lo respalda. cualquier desarrollador que vea tu repositorio de GitHub (o donde decidas guardarlo) entendera al instante como esta construido y como usarlo.

para ponerle la guinda al pastel, ¿quieres que te enseñe como empaquetar todo este proyecto en un **único archivo `.exe`** (usando `PyInstaller`) para que puedas usarlo como un comando nativo de tu sistema sin tener que invocar a Python?