# Guía de Compilación y Distribución (Build Guide)

Esta guía explica el proceso para generar los ejecutables "Zero-Dependency" de GitBulk para Windows y Linux.

## Requisitos Previos

- **Python 3.10+** instalado.
- Dependencias de desarrollo instaladas:
  ```bash
  pip install -r requirements.txt
  ```

---

## Paso 1: Preparación de Git Portable (Windows)

Para que el programa funcione en equipos sin Git instalado, debemos descargar la versión "MinGit" e incluirla en el build.

1. Abre una terminal de PowerShell en la raíz del proyecto.
2. Ejecuta el script de preparación:
   ```powershell
   ./scripts/prepare_portable_git.ps1
   ```
   *Esto creará la carpeta `vendor/git` con los binarios necesarios.*

---

## Paso 2: Generación del Ejecutable

GitBulk utiliza **PyInstaller** para empaquetar todo el código, librerías y recursos en un único archivo.

### En Windows (GUI)
Ejecuta el script automatizado:
```powershell
./scripts/build_gui.ps1
```

### En Linux (GUI)
Ejecuta el script de shell:
```bash
chmod +x scripts/build_gui_linux.sh
./scripts/build_gui_linux.sh
```

---

## Explicación del Comando PyInstaller

El comando interno que ejecutan los scripts es similar a este:

```bash
python -m PyInstaller --noconsole --onefile --name "GitBulk-GUI" \
    --icon "assets/gitbulk.ico" \
    --add-data "assets:assets" \
    --add-data "src/gui/icons:gui/icons" \
    --add-data "src/gui/theme.qss:gui" \
    --add-data "vendor/git:vendor/git" \
    --hidden-import "gui.translations" \
    --paths "src" \
    "src/main.py"
```

### Flags Principales:
- `--noconsole`: Oculta la ventana de terminal negra al abrir la aplicación gráfica.
- `--onefile`: Empaqueta todo en un único archivo `.exe` o binario.
- `--add-data`: Incluye archivos no-Python (iconos, estilos, git portable) dentro del ejecutable.
- `--hidden-import`: Asegura que módulos cargados dinámicamente sean incluidos.
- `--paths`: Indica dónde buscar los paquetes del código fuente (`src`).

---

## Resultados

Los archivos generados se ubicarán en:
- **Windows**: `dist/windows/GitBulk-GUI.exe`
- **Linux**: `dist/linux/GitBulk-GUI`

---

## Troubleshooting (Solución de Problemas)

### El antivirus bloquea el build
PyInstaller a veces genera falsos positivos. Se recomienda desactivar temporalmente el escudo de tiempo real o añadir la carpeta `dist` a exclusiones.

### Faltan iconos o estilos
Asegúrate de que las rutas en el comando `--add-data` son correctas y que la función `resource_path` en el código está usando la variable `sys._MEIPASS` de PyInstaller.

### Git no se encuentra en el equipo de destino
Verifica que ejecutaste el Paso 1 y que el archivo generado pesa más de 40MB (lo que indica que Git ha sido incluido correctamente).
