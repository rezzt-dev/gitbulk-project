# GUIA DE RAMAS

> ramas del repositorio, flujo de versiones y que rama es la base de cada pull
> request. sirve para decidir el destino de una pr sin tener que preguntarlo.

---

## 1. RAMAS PERMANENTES

| rama | funcion |
|---|---|
| `main` | unica rama permanente y rama por defecto: codigo publicado y base de todas las pr; de aqui salen los tags `v<x.y.z>`. los instaladores de una linea se descargan de `main` (`raw.githubusercontent.com/.../main/dist/...`) |

no hay ramas de desarrollo ni de version. el historial lo confirma: casi todo se ha commiteado directo en `main` y solo hay un merge (`cad1950`, `merge | GitBulk v1.4 - production release`), de una rama de trabajo ya borrada. a partir de ahora el trabajo entra por ramas de trabajo y pr.

---

## 2. RAMAS DE TRABAJO

nombre en minusculas, con barra y guiones:

| prefijo | uso | ejemplo |
|---|---|---|
| `feature/` | funcionalidad nueva | `feature/self-update` |
| `fix/` | correccion de error | `fix/branch-count-no-remote` |
| `changes/` | estructura, tooling, build, documentacion | `changes/repo-management-guides` |
| `hotfix/` | urgencia sobre una version publicada (binarios o instaladores) | `hotfix/linux-gui-installer-url` |

- se crean siempre desde `main` actualizado (`git checkout main && git pull --ff-only`).
- una rama, un tema; si el tema crece, se divide.
- una rama de trabajo se borra (local y remota) en cuanto su pr esta fusionada.

---

## 3. FLUJO DE UNA VERSION

```
feature/* , fix/* , changes/* , hotfix/*   →   main   →   tag v<x.y.z> + release
```

| paso | origen | destino | tipo de pr | titulo |
|---|---|---|---|---|
| 1 | `feature/*`, `fix/*`, `changes/*`, `hotfix/*` | `main` | trabajo normal | `<prefijo> \| <resumen>` |
| 2 | rama con el commit `changelog` que cierra la version (por ejemplo `changes/release-1.5.0`) | `main` | version | `release version <x.y.z> - <resumen>` |
| 3 | `main` | — | release de github | `v<x.y.z> — <resumen en ingles>` |

- todos los pasos se fusionan con "create a merge commit".
- antes de abrir una pr se comprueba que el destino no tiene commits que la rama no tenga: `git log <origen>..main`. si los tiene, se actualiza la rama primero (`git merge main`, sin rebase de ramas ya subidas).
- como `main` es la que sirven los instaladores, nada que deje `dist/` roto o apuntando a una release inexistente se fusiona en `main`.

---

## 4. CI

- no hay ci: no existe `.github/workflows/`.
- hasta que exista, antes de fusionar se ejecuta en local `python -m pytest tests/ -v` y se prueba el comando afectado. la suite tiene fallos conocidos desde la migracion a `subprocess` (ver `AGENTS.md`, *Testing*): una pr no puede anadir fallos nuevos.
- cuando exista ci, no se fusiona una pr con la ci en rojo.

---

## 5. LIMPIEZA

tras fusionar una pr de trabajo:

```
git checkout main
git pull --ff-only
git branch -d <rama>
git push origin --delete <rama>
```

`main` nunca se borra.
