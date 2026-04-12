# GitBulk — Guía de Distribución Profesional
==========================================

Bienvenido al paquete oficial de GitBulk. Esta distribución está organizada cuidadosamente para usuarios de Windows y Linux, incluyendo binarios y sus respectivos instaladores tanto para la versión de escritorio gráfica (GUI) como para la línea de comandos (CLI).

## Organización de la Carpeta

```text
dist/
├── windows/
│   ├── GitBulk-GUI.exe         <- Ejecutable Gráfico para Windows
│   ├── gitbulk-cli.exe         <- Ejecutable CLI para Windows
│   ├── install_gui.ps1         <- Instalador PowerShell para la GUI 
│   └── install_cli.ps1         <- Instalador PowerShell para la CLI
├── linux/
│   ├── GitBulk-GUI             <- Ejecutable Gráfico para Linux
│   ├── gitbulk-cli             <- Ejecutable CLI para Linux
│   ├── install_gui.sh          <- Instalador Bash para la GUI
│   └── install_cli.sh          <- Instalador Bash para la CLI
└── README-Dist.md              <- Este archivo
```

---

## Cómo Empezar (Windows)

### Opción A: Instalación Automática (Recomendado)
Puedes instalar la GUI completa en Windows abriendo una PowerShell como administrador y ejecutando:
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/windows/install_gui.ps1" | iex
```
Para la CLI:
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/windows/install_cli.ps1" | iex
```

### Opción B: Uso Portable (Sin Instalación)
Si deseas evitar instalar nada, simplemente entra en la carpeta `windows/` y ejecuta el archivo `GitBulk-GUI.exe` u opera directamente usando la línea de comandos en `gitbulk-cli.exe`.

---

## Cómo Empezar (Linux)

### Instalación de interfaz gráfica
Asegúrate de darle permisos de ejecución al script y lanzarlo:
```bash
cd linux/
chmod +x install_gui.sh
./install_gui.sh
```

### Instalación de interfaz de comandos (CLI)
```bash
cd linux/
chmod +x install_cli.sh
./install_cli.sh
```

### Uso Portable
Si prefieres usarlo de modo portable, simplemente haz `chmod +x` a `GitBulk-GUI` o `gitbulk-cli` de la carpeta `linux/` y ejecútalos.

---
Desarrollado por rezzt-dev — v1.3.0
