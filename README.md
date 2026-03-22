## GitBulk Project

una herramienta profesional de linea de comandos (CLI) escrita en Python para gestionar y actualizar multiples repositorios Git de forma masiva y concurrente.

en lugar de ir carpeta por carpeta ejecutando comandos, **GitBulk** busca recursivamente todos los repositorios en una ruta especifica y ejecuta operaciones (`fetch` o `pull`) en paralelo, reduciendo drasticamente el tiempo de espera.

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
abre tu terminal, situate en la carpeta raiz del proyecto (`gitbulk`) y ejecuta el programa como un modulo de Python.

#### Uso Basico
ejecutar un `fetch` en el directorio actual (o en el utlimo que usaste):
```bash
python -m src.main fetch
```

ejecuta un `pull` (con `ff-only`) en una ruta especifica:
```bash
python -m src.main pull --dir "C:\Mis\Repositorios"
```

#### Argumentos Disponibles
| Argumento   | Atajo | Descripcion                                                       | Valor por Defecto                     |
| ----------- | ----- | ----------------------------------------------------------------- | ------------------------------------- |
| `operation` | -     | **requerido**. la operacion de Git a ejecutar (`fetch` o `pull`). | -                                     |
| `--dir`     | `-d`  | ruta raiz donde buscar repositorios.                              | ultima ruta usada / Directorio actual |
| `--workers` | `-w`  | numero de hilos simultáneos para la descarga de red.              | `5`                                   |

#### Argumentos Disponibles
hacer `pull` en una ruta concreta usando 10 hilos simultaneamente para mayor velocidad:
```bash
python -m src.main pull -d "/home/usuario/proyectos" -w 10
```

---
### Como Funciona la Persistencia
la primera vez que ejecutas el programa, se crea un archivo de configuracion oculto en tu carpeta de usuario (ej. `C:\Users\Usuario\.git_manager_pro.json` o `~/.git_manager_pro.json`). este archivo almacena tus preferencias, como la ultima ruta sobre lo que operaste, mejorando la comodidad en usos futuros.

con esto, tu proyecto no solo tiene un codigo de primera categoria, sino tambien una documentacion que lo respalda. cualquier desarrollador que vea tu repositorio de GitHub (o donde decidas guardarlo) entendera al instante como esta construido y como usarlo.

para ponerle la guinda al pastel, ¿quieres que te enseñe como empaquetar todo este proyecto en un **único archivo `.exe`** (usando `PyInstaller`) para que puedas usarlo como un comando nativo de tu sistema sin tener que invocar a Python?