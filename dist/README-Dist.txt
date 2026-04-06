# GitBulk — Guía de Distribución Profesional
==========================================

Bienvenido al paquete oficial de GitBulk. Esta carpeta está organizada para ofrecerte la mejor experiencia tanto si prefieres una interfaz gráfica (GUI) como si eres un usuario avanzado de terminal (CLI).

## Estructura de esta carpeta

1.  **`Install-GitBulk.ps1`**: [RECOMENDADO] Instalador maestro. Registra GitBulk en Windows, crea accesos directos y habilita el comando `gitbulk` en tu terminal.
2.  **`Uninstall-GitBulk.ps1`**: Desinstalador oficial para eliminar rastro del programa de forma segura.
3.  **`App_GUI/`**: Contiene los binarios internos de la versión de escritorio. No es necesario entrar aquí si usas el instalador.
4.  **`Portable_CLI/`**: Contiene binarios independientes (un solo archivo) para Windows y Linux. Ideal para llevar en un USB o usar rápidamente sin instalar nada.

---

## Cómo empezar

### Opción A: Experiencia Completa (Instalación)
Si quieres tener GitBulk integrado en tu menú inicio y escritorio:
1.  Haz clic derecho sobre `Install-GitBulk.ps1`.
2.  Selecciona **"Ejecutar con PowerShell"**.
3.  Sigue las instrucciones en pantalla (requiere permisos de Administrador).

### Opción B: Uso Rápido (Portable)
Si solo necesitas la terminal:
1.  Entra en la carpeta `Portable_CLI/`.
2.  Ejecuta `gitbulk-windows.exe` directamente.

---

## Notas Técnicas
- **Comando de Terminal**: Tras la instalación, puedes abrir la GUI escribiendo `gitbulk --gui`.
- **Desinstalación**: Puedes usar `Uninstall-GitBulk.ps1` o ir a "Configuración > Aplicaciones" en Windows.

---
Desarrollado por rezzt-dev
