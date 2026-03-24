# Documentación de GitBulk

## Índice
1. [Introducción](#introducción)
2. [Características](#características)
3. [Instalación](#instalación)
4. [Autenticación](#autenticación)
5. [Comandos Principales](#comandos-principales)
6. [Banderas Globales](#banderas-globales)
7. [Uso Avanzado](#uso-avanzado)

## Introducción
GitBulk es una interfaz de línea de comandos (CLI) robusta y concurrente construida en Python. Está diseñada para orquestar y ejecutar operaciones Git a través de múltiples repositorios aislados de forma simultánea. Utilizando `GitPython` como motor subyacente y `ThreadPoolExecutor` para el procesamiento en paralelo, GitBulk mitiga la latencia y la fatiga repetitiva de gestionar arquitecturas masivas de microservicios o entornos multi-repositorio.

## Características
- **Ejecución Concurrente**: Procesa múltiples directorios de forma simultánea sin bloqueos de hilos.
- **Compatibilidad Multiplataforma**: Totalmente funcional en sistemas Linux, Windows y macOS.
- **Mecanismos de Seguridad Interactivos**: Previene la pérdida de datos accidental mediante prompts interactivos obligatorios en acciones destructivas.
- **Reporte Detallado en CLI**: Utiliza la librería `rich` para renderizar matrices compactas, codificadas por color y barras de progreso.
- **Gestión de Autenticación**: Capaz de leer credenciales de Git globales fluidamente para interactuar con repositorios remotos sin interrumpir o cancelar los flujos masivos de ejecución.
- **Monitorización de CI / Actions**: Se conecta de forma nativa a la API de GitHub para consultar el estado en vivo de los pipelines de integración continua.

## Instalación

### Requisitos Previos
- Python 3.10 o superior.
- Git instalado y accesible en la variable PATH del sistema.

### Configuración desde Código Fuente
Clona el repositorio e instala las dependencias requeridas (incluido GitPython y Rich):

```bash
git clone https://github.com/rezzt-dev/gitbulk-project.git
cd gitbulk-project
pip install -r requirements.txt
```

### Compilación del Binario (Aplicación Portable)
Para compilar GitBulk en un ejecutable portátil independiente que no requiera un entorno de ejecución de Python activo, utiliza PyInstaller:

```bash
pip install pyinstaller
pyinstaller --name gitbulk --onefile src/main.py
```
El binario resultante se alojará en el directorio `dist/`. Puedes mover este binario a la carpeta de binarios locales de tu sistema (ej., `/usr/local/bin/` en Linux) para obtener acceso global en toda la terminal.

## Autenticación
Ciertas operaciones que dependen de internet (como efectuar `fetch` a ramas remotas privadas o consultar flujos `ci-status`) requieren credenciales válidas de GitHub. GitBulk simplifica esto solicitando un Personal Access Token (PAT) una sola vez y reteniéndolo de forma segura bajo tus propias credenciales de sistema operativo.

Para configurar tu acceso:
```bash
python main.py auth
```
Este comando almacena la clave en el archivo `~/.git-credentials`, configurando tu helper global de Git para emplearlo en el futuro. Las iteraciones subsiguientes extraerán este token silenciosamente sin volver a preguntártelo.

## Comandos Principales

### `status`
Escanea recursivamente el árbol de trabajo local de todos los repositorios para reportar su divergencia e historial en relación con las ramas upstream remotas.
**Estados de Salida**: `[CLEAN]`, `[MODIFIED]`, `[AHEAD]`, `[BEHIND]`.

### `fetch`
Descarga estáticamente el historial remoto sin integrarlo o fusionarlo dentro del código de trabajo local.
**Estados de Salida**: `[OK]`, `[UPDATES]` (indica que existen commits pendientes de ser descargados vía pull).

### `pull`
Actualiza directamente la rama actual combinando los últimos commits del servidor remoto. Se efectúa exclusivamente de forma segura en modalidad de avance rápido (fast-forward).
**Estados de Salida**: `[OK]`, `[CONFLICT]`, `[DIVERGENT]`.
**Bandera Relacionada Sugerida**: `--autostash`

### `checkout`
Mueve o re-alinea iterativamente el puntero `HEAD` de todos los repositorios hacia la rama especificada. Si la rama existe localmente, cambia orgánicamente a ella. Si existe en la red (remote) pero localmente no, crea el vínculo de rastreo automático y la descarga. Los repositorios donde no contengan rastros de este nombre de rama serán ignorados de forma segura devolviendo `[IGNORED]`.
**Bandera Obligatoria**: `-b <nombre_de_rama>`

### `current-branch`
Renderiza un mapa topográfico en formato tabla ultra compacto listando paralelamente la rama activa, todas las ramas locales secundarias existentes y las ramas exclusivas de solo-remoto para cada uno de los repositorios.

### `clean`
Una iteración estricta y destructiva que ejecuta iterativamente `git fetch --prune` sumado a `git clean -xfd`. Elimina permanentemente de la computadora las referencias de ramas remotas abandonadas y destruye todos los archivos y directorios no versionados locales (ej: `node_modules`, `obj`, `bin`, `build`).
**Advertencia**: Altera masivamente los discos duros, por ende, el flujo requerirá confirmación interactiva obligatoria de `(Y/N)`.

### `ci-status`
Abre una conexión asíncrona dedicada hacia la API de GitHub para consultar y consolidar los pipelines de validación (GitHub Actions / Jenkins) relacionados con el commit actualmente montado en tu `HEAD`.
**Estados de Salida (ASCII)**: `[PASS]`, `[FAIL]`, `[PEND]`, `[NONE]`

### `export`
Serializa la ruta, estado, URLs maestras y el árbol de ramas en control de todos los repositorios activos y lo compila creando un Snapshot o foto instantánea persistente en arquitectura JSON.
**Asignación**: Guarda por omisión en `snapshot.json` a menos que se reemplace con `-f`.

### `restore`
Inspecciona tu escritorio activo comparándolo contra un archivo Snapshot capturado previamente por la herramienta. Realizará clonaciones masivas controladas devolviendo a disco cualquier repositorio faltante, posicionándolo inmediatamente en la rama que poseía durante la lectura meta inicial.

## Banderas Globales Múltiples

- `-d, --dir <ruta>`: Exige el directorio raíz absoluto a ser escaneado recursivamente en busca de sub-git-directorios. (Por defecto almacena persistencia en el caché usando tu última ruta abierta).
- `-w, --workers <entero>`: Administra el nivel de presión del CPU definiendo el número de hilos de sistema asíncronos encolados concurrentemente. Mínimo 1. Por defecto: `5`.
- `-l, --log <ruta>`: Imprime silenciosamente una copia textual cruda de todos los STDOUT y STDERR recopilados durante los pipelines en la ruta especificada de archivo.
- `-b, --branch <nombre>`: Criterio de string nombrando la rama destino (ej. `release/v2.0`). Condicional estricta al solicitar `checkout`.
- `-f, --file <ruta>`: Especifica la procedencia/destino del Snapshot JSON para los respaldos masivos usando `export` y `restore`.
- `--autostash`: Instrucción de auto-blindaje en código durante el `pull`. Almacena en Stash tus ediciones en duro que impidan combinar código. Efectuará el pull e instantáneamente aplicará tu parche no finalizado encima del nuevo head.

## Uso Avanzado Operativo

### Pull Asistido y Seguro (AutoStash)
Es habitual que los servidores rechacen un Pull si un repositorio acarrea trabajo sin guardar (untracked/modified files) devolviendo fallos en terminal. Agregando la bandera `--autostash` sorteamos el error mediante paramecio automático: interrumpe, aloja, avanza el puntero de red y recompone las ediciones.
```bash
python main.py pull --autostash
```
El log te informará del salvataje indicando visualmente `[SYNC+STASH]` certificando la integridad, o deteniéndose bajo el error `[STASH CONFLICT]` indicando divergencias severas que ameritan intervención de un Merge Driver local.

### Ejecución Segura en Tuberías CI
Nuestra arquitectura interactiva ha sido elaborada desde la base respetando el ciclo de procesos UNIX. Como tal, es inherentemente robusto contra entornos ciegos o Runners (Jenkins/GitLab CI) que eviten inyecciones de Standard Input (`stdin`). Entregar operaciones como `clean` a través de un shell-pipe corrompido (`< /dev/null`) anula internamente el input sin colapsar el interpretador Python lanzando los catch `KeyboardInterrupt` o `EOFError`.
