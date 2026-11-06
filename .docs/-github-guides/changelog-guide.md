# GUIA DEL CHANGELOG

> como se escribe y se cierra `CHANGELOG.md` (raiz del repositorio). es la
> fuente de verdad de commits, pull requests, merges y releases: nada se
> redacta en paralelo, todo se extrae de aqui.

---

## 1. ESTRUCTURA

```
# Changelog

<cabecera existente: keep a changelog + semver, no se toca>

---

## SIN PUBLICAR / UNRELEASED

## [x.y.z] — aaaa-mm-dd

### CASTELLANO

#### ANADIDO
- <cambio>

### ENGLISH

#### ADDED
- <change>
```

- la seccion `## SIN PUBLICAR / UNRELEASED` esta siempre arriba, justo debajo de la cabecera, y recoge lo que aun no se ha publicado.
- las versiones cerradas van de la mas reciente a la mas antigua.
- cada version nueva lleva `### CASTELLANO` y `### ENGLISH` con paridad exacta de items.
- las secciones antiguas `## [Unreleased]` y `## [0.1.0] — 2026-01-01` usan el formato anterior (solo ingles, categorias `Added` / `Changed` / `Fixed` / `Planned`) y no se reescriben. `## [Unreleased]` describe trabajo ya publicado entre `v1.0` y `v1.4.0`; reconciliarla es una decision del propietario (ver `.docs/repo-audit-and-fix.md`).

---

## 2. CATEGORIAS (CERRADAS Y EN ESTE ORDEN)

| castellano | english | que va |
|---|---|---|
| `ANADIDO` | `ADDED` | funcionalidades, comandos, ficheros o documentos nuevos |
| `CAMBIADO` | `CHANGED` | cambios en comportamiento, estructura, build o documentacion existente |
| `CORREGIDO` | `FIXED` | errores corregidos |
| `ELIMINADO` | `REMOVED` | codigo, ficheros o funciones retirados |
| `SEGURIDAD` | `SECURITY` | correcciones o endurecimiento con impacto de seguridad (credenciales, permisos de ficheros, subprocesos) |

se omite la categoria que no tenga items. no se crean otras (las ideas futuras no van al changelog).

---

## 3. REGLAS DE ESTILO

- minusculas y sin acentos en el contenido; titulos y encabezados en mayusculas.
- un item por linea, en imperativo ("anadir", "corregir", "mover"), empezando por `-`.
- ficheros, rutas, comandos e identificadores entre backticks.
- explica el efecto visible o el motivo, no el detalle de implementacion linea a linea.
- sin menciones a herramientas de ia ni a quien escribio el item.

---

## 4. CUANDO SE ACTUALIZA

1. **en cada commit** con cambios visibles: se anaden los items a `## SIN PUBLICAR / UNRELEASED`, en los dos idiomas, en el mismo commit.
2. **al preparar una pr o un merge**: se comprueba que el changelog cubre todo el diff; si falta algo, se anade antes de abrirla.
3. **al cerrar una version**: ver seccion 5.

---

## 5. CERRAR UNA VERSION

1. comprobar que `## SIN PUBLICAR / UNRELEASED` esta completo y con paridad entre idiomas.
2. renombrarlo a `## [x.y.z] — aaaa-mm-dd` (fecha de cierre, mismo guion largo que las versiones existentes) y dejar encima una seccion `## SIN PUBLICAR / UNRELEASED` vacia.
3. subir la version a mano donde se repite (commit `changes`): `src/gui/translations.py` (`footer_version`, cinco idiomas), `VERSION` en `dist/linux/install_cli.sh` y `dist/linux/install_gui.sh`, `$version` en `dist/windows/install_cli.ps1` y `dist/windows/install_gui.ps1`, y la insignia de `README.md`.
4. commit con prefijo `changelog`:

```
changelog | cerrar la seccion de changelog para la version <x.y.z>
```

5. abrir la pr de version (ver `pr-merge-guide.md`) y, al fusionar en `main`, crear la release (ver `release-guide.md`) sin dejar `main` con un `VERSION` cuya release aun no existe.

---

## 6. NUMERACION

- esquema `x.y.z` (semver, como declara la cabecera del changelog); la ultima release publicada es `v1.4.0`.
- `x` cambia con rupturas grandes (comandos o formato de configuracion incompatibles); `y` con funcionalidades nuevas; `z` con correcciones.
- un numero publicado no se reutiliza.

---

## 7. LISTA DE COMPROBACION

- [ ] los dos idiomas tienen los mismos items.
- [ ] solo hay categorias de la lista cerrada.
- [ ] ningun item queda sin backticks en identificadores.
- [ ] la fecha de la version cerrada usa `aaaa-mm-dd`.
- [ ] no hay atribucion de ia.
