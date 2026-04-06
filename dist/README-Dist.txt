# GitBulk — Guía de Distribución Profesional
==========================================

Bienvenido al paquete oficial de GitBulk. Esta distribución está diseñada tanto para usuarios finales que buscan una experiencia de escritorio (GUI) como para desarrolladores que prefieren la terminal (CLI).

## 📂 Estructura de Distribución

1.  **`gui/install.ps1`**: [RECOMENDADO] Instalador web y local para la interfaz gráfica. Gestiona permisos, crea accesos directos y registra la App en Windows.
2.  **`cli/install.ps1`**: Instalador para la versión de terminal en Windows.
3.  **`cli/install.sh`**: Instalador para la versión de terminal en Linux/macOS.
4.  **`App_GUI/`**: Contiene el ejecutable compilado (`GitBulk-GUI-Windows.exe`) listo para instalar o usar.
5.  **`Portable_CLI/`**: Binarios independientes (One-File) para ejecución rápida sin instalación.

---

## 🚀 Cómo empezar

### Opción A: Instalación Automática (Recomendado)
Puedes instalar la GUI completa ejecutando este comando en una PowerShell con permisos de administrador:
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install.ps1" | iex
```

### Opción B: Instalación Manual
1. Entra en la carpeta `gui/`.
2. Haz clic derecho sobre `install.ps1` y selecciona "Ejecutar con PowerShell".
3. Sigue las instrucciones para registrar GitBulk en tu sistema.

### Opción C: Uso Portable
Si no deseas instalar nada, simplemente ejecuta los archivos dentro de `App_GUI/` o `Portable_CLI/`.

---

## 🔍 Notas Técnicas
- **Comando global**: Tras la instalación, puedes abrir la App desde cualquier terminal escribiendo `gitbulk --gui` o simplemente `gitbulk` para la CLI.
- **Búsqueda en Windows**: El programa aparecerá en tu Menú Inicio tras la instalación.
- **Desinstalación**: Puedes eliminar el rastro del programa desde "Configuración > Aplicaciones" en Windows.

---
Desarrollado por rezzt-dev — v1.3.0
