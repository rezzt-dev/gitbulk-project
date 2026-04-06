# Plan de Implementación de GUI para GitBulk

Este documento define la hoja de ruta y los requerimientos arquitectónicos para implementar una interfaz gráfica (GUI) en GitBulk. El objetivo principal es construir una herramienta de aspecto profesional, similar a GitKraken, GitHub Desktop o Linear, **manteniendo intacta la versión y experiencia CLI actual**.

---

## 1. Visión y UX/UI

La meta es un entorno visual premium que fomente la productividad:
*   **Tema Oscuro Profesional por Defecto:** Interfaz en tonos grises oscuros profundos (ej. `rgb(20, 20, 20)` base, `rgb(30, 30, 30)` para componentes elevados), contrastando con colores vibrantes para indicaciones de estado (Verde para *Clean*, Naranja/Amarillo para *Ahead/Behind*, Rojo para *Errores*).
*   **Tipografía y Microinteracciones:** Uso de tipografías modernas sans-serif en lugar de la del sistema cuando sea posible (ej. tipografías estilo Inter o Roboto). Hover effects fluidos, esquinas sutilmente redondeadas (bordes de 4 a 6px).
*   **Aprovechar lo Visual:** Trasladar la carga mental de leer texto en consola a un golpe de vista. Iconos vectoriales sencillos y una barra de estado o progreso consolidada.

## 2. Estrategia "CLI Dual" (Modo Híbrido)

El núcleo del producto no cambia. GitBulk seguirá siendo un binario CLI primario.
*   Al ejecutar `gitbulk [comando]`, el flujo se dirige a `view/cli.py` (Rich).
*   Al ejecutar `gitbulk --gui`, la aplicación lanza el entorno PySide6.
*   **Ventaja:** Ningún pipeline CI/CD existente se rompe; los _power users_ pueden mantener su flujo en terminal, y la GUI se convierte en un _plus_ de productividad sin coste de refactor destructivo.

---

## 3. Arquitectura y Estructura de Archivos

La lógica en `model/` (operaciones de Git) y `persistence/` (JSON de configuración) es 100% agnóstica de la interfaz, por lo que **no sufrirá cambios estructurales**.

Se añadirá el ecosistema GUI en un nuevo paquete `src/gui/`:

```text
src/
├── main.py                <-- Se actualiza para rutear --gui hacia app.py
├── gui/                   <-- NUEVO PAQUETE GUI
│   ├── __init__.py
│   ├── app.py             <-- Inicialización de QApplication y control general
│   ├── theme.qss          <-- Hoja de estilos (QSS) con temática premium
│   ├── main_window.py     <-- QMainWindow: Coordina el layout general (3 paneles)
│   ├── workers.py         <-- QThread y QRunnable: Manejo asíncrono para no bloquear UI
│   ├── components/        <-- Widgets encapsulados y estilizables
│   │   ├── repo_list.py   <-- Panel Izquierdo: QListView/QTreeView
│   │   ├── action_bar.py  <-- Toolbar Superior/Central: Botones (Fetch, Pull...)
│   │   ├── log_view.py    <-- Panel Derecho: QTextEdit de sólo lectura
│   │   └── progress.py    <-- QProgressBar elegante
│   └── assets/            <-- Iconos SVG (ej. Lucide icons o genéricos) y fuentes
├── model/                 <-- Sin cambios
├── view/cli.py            <-- Sin cambios
└── persistence/           <-- Sin cambios
```

---

## 4. Roadmap de Desarrollo

### Fase 1: Arquitectura Base e Intercepción CLI (Semana 1)
*   **Objetivo:** Instalar PySide6 y conectar el flag `--gui`.
*   **Tareas:**
    *   Añadir `PySide6` a `requirements.txt`.
    *   Modificar `main.py` para soportar el flag `--gui`. Si está presente, importar `src/gui/app.py` y lanzarlo en lugar de continuar con argparse.
    *   Crear una `QMainWindow` vacía pero funcional para verificar la ejecución aislada.

### Fase 2: Diseño Estructural y Theming (Semana 2)
*   **Objetivo:** Construir la cáscara premium inspirada en Linear/GitKraken.
*   **Tareas:**
    *   Crear los 3 paneles principales usando un layout divisor (`QSplitter` o `QHBoxLayout`).
        *   Panel izquierdo: Árbol o Lista de repositorios.
        *   Panel central/superior: Barra de acciones y progreso general.
        *   Panel central/derecho: Logs asíncronos y propiedades de rama actual.
    *   Diseñar el archivo `theme.qss` con paletas de color, *padding*, bordes redondeados y remoción de estilos nativos de Windows que se ven antiguos.

### Fase 3: Integración Asíncrona - Model Read (Semana 3)
*   **Objetivo:** Mostrar datos reales sin que la UI se congele.
*   **Tareas:**
    *   Implementar `workers.py`. Toda llamada a `model.git_ops` u otros modelos pesados deberá realizarse en hilos secundarios (QThread).
    *   Poblar `repo_list.py` con los repositorios guardados en memoria/persistencia.
    *   Asignar iconos en base al estado de repositorios devuelto por los workers (verificando la presencia de iconos SVG estáticos).
    *   Panel de detalles: Al seleccionar un repositorio en la lista, mostrar última fecha de actualización, rama actual, y status.

### Fase 4: Operaciones y Control de Flujo (Semana 4)
*   **Objetivo:** Conectar el *Action Bar* (Fetch, Pull, Export, etc.) al modelo.
*   **Tareas:**
    *   Implementar emisión dinámica de progreso general vía **QSignals** hacia la barra de carga en `progress.py`.
    *   Volcar la salida de procesos y operaciones a la consola interactiva en tiempo real dentro del `log_view.py`.
    *   Mapear la totalidad de las 10 operaciones de CLI a botones o un panel de comandos visualmente claro.

### Fase 5: Pulido, Componentes Críticos y Empaquetado (Semana 5)
*   **Objetivo:** Finalizar interacciones menores y optimizar binario release.
*   **Tareas:**
    *   Implementar de forma atractiva el **Diálogo de Autenticación** (`auth` token de GitLab/GitHub).
    *   Diálogo *Warning Modal*: Diálogo visual fuerte antes de limpiar repos (`clean`).
    *   Incorporar selector de directorios (`QFileDialog.getExistingDirectory()`) al pulsar "Añadir workspace".
    *   Modificar el entorno PyInstaller (`.spec`) y los scripts PowerShell/Bash para asegurar que empaquetan y detectan correctamente las binarias dinámicas (DLLs) de Qt que requiere PySide6.
    *   Probar de extremo a extremo ejecutable para Windows y empaquetado para Linux.

---

## 5. Criterios de Éxito
1.  **Cero interferencia:** El flujo del CLI actual no registra variaciones sintácticas.
2.  **No bloqueante:** En ninguna operación (Pull sobre 20 repos, por ej.) un _frezze_ de la UI es aceptable.
3.  **Refinamiento Visual:** La herramienta de escritorio debe tener apariencia de "native feeling modern app", distanciada de ventanas clásicas "Tkinter-like". Todos los modales, bordes y botones deben verse limpios y cohesionados.
