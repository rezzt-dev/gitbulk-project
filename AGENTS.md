# GITBULK-PROJECT: REPOSITORY GUIDE

python cli and desktop gui for managing multiple git repositories. this guide covers the repository; nested agent instructions apply within their own folders.

## PROJECT OVERVIEW

| property | verified value |
| --- | --- |
| repository | `rezzt-dev/gitbulk-project` |
| active source | `./` |
| development base for this change | `main` |
| remote default branch | `main` |
| version source | no application version manifest exists |
| continuous integration | no tracked github actions workflows |

## TECHNOLOGY STACK

- python dependencies and package entry points are declared per program; no shared environment is assumed

## PROJECT STRUCTURE

- `CHANGELOG.md`
- `LICENSE`
- `README.md`
- `agents-docs/`
- `assets/`
- `gitbulk-gui-linux.spec`
- `gitbulk-linux.spec`
- `gitbulk-windows.spec`
- `project-doc/`
- `requirements.txt`
- `scripts/`
- `snapshot.json`
- `src/`
- `sync_test.json`
- `tests/`
- `vendor/`

management documentation lives in `.docs/manager.md`, `.docs/-github-guides/` and `.docs/repo-audit-and-fix.md`. keep this file and `CLAUDE.md` consistent.

## BUILD, RUN AND TEST COMMANDS

for application changes, run these checks from `./`:

```bash
python -m pytest
```

## CODE STYLE AND ARCHITECTURAL DECISIONS

use temporary repositories for tests; preserve git credential boundaries and user changes; never exercise bulk push or deletion against real repositories. follow the existing formatter and naming of the changed module. verify manifest versions when dependencies change.

## TESTING STRATEGY

documentation-only changes require `git diff --check`, existing-path checks and a review of the staged file list. run module checks for application changes, with disposable data. report unavailable tooling and failed checks; never claim a check passed without running it.

## SECURITY AND DEPLOYMENT

keep credentials, local configuration, signing material and user data out of commits. do not print secret values while auditing. inspect configuration names and code references instead.

existing legal and community files: `LICENSE`. when changing dependencies, permissions, storage or network services, review those files against the implementation. record missing policies as audit work; do not invent licence terms or ownership decisions.

deployment, signing, store publication, migrations against hosted databases and repository settings require their own explicit request. this documentation task prepares management instructions and pull requests.

## COMMON TASKS

1. read the relevant module and its nearest agent instructions
2. inspect the working tree and choose the smallest change that solves the request
3. update the affected documentation and changelog with evidence from the diff
4. run checks appropriate to the changed module and report their actual results
5. for git operations, follow the manager and the digest below

## EXISTING PROJECT CONVENTIONS

the following project-specific context is retained from the previous guide. paths are relative to the active module when stated. for git operations, the manager and final digest supersede previous workflow examples.

## GITBULK — AGENT GUIDE

> **gitbulk** is a cross-platform desktop tool (cli + pyside6 gui) by **rezzt-dev** that runs bulk git operations (status, fetch, pull, push, commit, checkout, clean, export/restore, ci status, workspaces, groups) across many repositories concurrently. it is written in python, calls the native `git` binary through `subprocess`, and ships as pyinstaller one-file executables for windows and linux.
>
> **audience:** ai coding agents with no prior context about this project.
>
> **git workflow (commits, prs, merges, releases):** when asked for a commit, pr, merge or release title/description, read `.docs/manager.md` first (it is versioned in this repository) and follow the guides it points to; the last section of this file ("commit, pr, merge & release guidelines") is the self-contained digest. never add ai attribution of any kind.

---

## PROJECT OVERVIEW

| property | value |
|----------|-------|
| **repository** | `rezzt-dev/gitbulk-project` (public), single branch `main` |
| **latest release** | `v1.4.0` (2026-04-12). `main` carries 3 unreleased commits after the tag (installers rewrite, persistence fix in `auth.py` / `git_ops.py`, line-ending rewrite) |
| **version in code** | no `pyproject.toml` / `setup.py`; `v1.4.0` is hard-coded in `src/gui/translations.py` (`footer_version`, 5 languages), `dist/linux/install_{cli,gui}.sh` (`VERSION`), `dist/windows/install_{cli,gui}.ps1` (`$version`) and the `README.md` badge |
| **language** | python 3.10+ (readme badge); the versioned `.pyc` files were compiled with 3.13 and 3.14 |
| **license** | mit (`LICENSE`, "copyright (c) 2026 rezzt-dev"); github detects it |
| **homepage** | `https://gitbulk.rezzt.dev` (repo `gitbulk-web-project`) |
| **distribution** | pyinstaller one-file binaries attached to github releases, installed with the one-line scripts in `dist/` |
| **ci** | none (no `.github/`) |

### WHAT GITBULK DOES

- scans a root directory recursively for git repositories (`model/scanner.py`), skipping `.gitbulk_archive/`.
- runs operations in parallel with `ThreadPoolExecutor`; `-w 0` auto-tunes the worker count to the disk latency (hard cap 50).
- cli operations (`src/view/cli.py`): `fetch`, `pull`, `auth`, `status`, `export`, `restore`, `current-branch`, `clean`, `checkout`, `ci-status`, `workspace` (`--action save|load|list|delete|sync`), `groups`, `commit`, `push`.
- cli options: `-d/--dir`, `-w/--workers`, `-l/--log`, `--autostash`, `-f/--file`, `-b/--branch`, `--dry-run`, `--group`, `-i/--interactive`, `-m/--message`, `-D/--body`, `--action`, `-n/--name`; `--gui` is handled in `main.py` before argparse.
- persists last directory, saved workspaces and ui language in `~/.git_manager_pro.json`.
- optional pyside6 gui: dark qss theme, five languages, workspace tree, group inspector, commit hub, sync preview.

---

## TECHNOLOGY STACK

| component | library / tool | purpose |
|-----------|---------------|---------|
| runtime | python 3.10+ | core language |
| cli rendering | `rich==14.3.3` | tables, panels, progress bars, prompts |
| gui framework | `PySide6>=6.5.0` | qt6 desktop interface (lgplv3) |
| git execution | `subprocess` + native `git` | replaced gitpython for speed and fewer dependencies |
| concurrency | `concurrent.futures.ThreadPoolExecutor` | parallel repo operations |
| bundling | `pyinstaller==6.19.0` | one-file `.exe` / elf binaries |
| testing | `pytest>=8.0.0` (tests are written with `unittest`) | unit tests |
| portable git (windows) | mingit 2.44.0 in `vendor/git/` (gplv2) | bundled git for machines without a system install |

`requirements.txt` is the single source of dependencies (runtime, build and test). there is no `pyproject.toml`, `setup.py` or lock file.

### ENTRY POINT

- `src/main.py` is the single entry point for both cli and gui.
- if the binary is frozen (pyinstaller) and launched with no arguments, the gui starts automatically.
- launch the gui explicitly with `python src/main.py --gui` (or `gitbulk --gui` from an installed binary).

---

## PROJECT STRUCTURE

```text
gitbulk-project/
├── src/
│   ├── main.py              # Entry point, operation dispatch, progress orchestration (2-space indent)
│   ├── view/
│   │   ├── __init__.py      # Re-exports the public CLI view API
│   │   └── cli.py           # argparse definition and rich terminal output (2-space indent)
│   ├── model/
│   │   ├── __init__.py      # Re-exports pure business-logic functions
│   │   ├── scanner.py       # Recursive repo discovery, `.gitbulk.repo.json` groups topology
│   │   ├── git_ops.py       # `_resolve_git_executable`, `_run_git_command`, `run_git_operation`
│   │   ├── auth.py          # Credential helper setup, PAT extraction, SSH agent helpers
│   │   ├── ci_ops.py        # GitHub Check Runs API polling
│   │   ├── concurrency.py   # Disk-latency based worker auto-tuning (max 50)
│   │   ├── archiver.py      # Moves repos to `.gitbulk_archive/<repo>_<timestamp>/`
│   │   ├── interactive.py   # External editor launch and CLI prompts
│   │   └── error_handler.py # Normalizes raw git stderr into user messages
│   ├── persistence/
│   │   └── config_repo.py   # `~/.git_manager_pro.json` read/write
│   └── gui/
│       ├── app.py           # QApplication setup, DPI, fonts, theme, language, resource_path()
│       ├── main_window.py   # Main Qt window (~2 400 lines): tree, sidebar, hubs, operations
│       ├── workers.py       # QThread workers for scanning and operations
│       ├── translations.py  # LANGUAGES dict (es_ES, en_US, en_UK, de_DE, fr_FR) + TR() brand enforcer
│       ├── icon_manager.py  # SVG icon colorizer and cache
│       ├── download_actions.py # empty placeholder
│       ├── theme.qss        # Dark stylesheet
│       └── icons/           # SVG icons (gitbulk_icon.svg, …)
├── tests/                   # unittest-style tests run with pytest (test_auth, test_error_handler, test_git_ops, test_scanner)
├── scripts/
│   ├── build_gui_windows.ps1 # PyInstaller GUI build → dist/windows/gitbulk-gui.exe
│   ├── build_gui.ps1        # older GUI build → dist/windows/GitBulk-GUI.exe
│   ├── build_gui_linux.sh   # PyInstaller GUI build → dist/linux/GitBulk-GUI
│   └── prepare_portable_git.ps1 # downloads MinGit 2.44.0 into vendor/git
├── gitbulk-windows.spec     # CLI, Windows → gitbulk-windows (excludes PySide6)
├── gitbulk-linux.spec       # CLI, Linux → gitbulk-linux (excludes PySide6)
├── gitbulk-gui-linux.spec   # GUI, Linux → gitbulk-gui-linux
├── dist/                    # versioned: one-line installers + README-Dist.md; built binaries are ignored
│   ├── windows/install_{cli,gui}.ps1
│   ├── linux/install_{cli,gui}.sh
│   └── README-Dist.md       # Spanish; describes older binary names
├── vendor/git/              # MinGit for Windows (third party, GPLv2) — do not edit
├── assets/gitbulk.ico       # Application icon
├── project-doc/{en,es}-project-doc.md # Human-readable technical docs
├── agents-docs/             # Internal analysis notes (Spanish)
├── .docs/                   # Versioned: git guides (manager.md, -github-guides/), audit work file, planning notes
├── snapshot.json            # Workspace export of the owner's repos (personal data; see Security)
├── sync_test.json           # Small workspace fixture
├── requirements.txt
├── CHANGELOG.md · LICENSE · README.md (Spanish) · AGENTS.md · CLAUDE.md
└── build/                   # PyInstaller work dir, ignored
```

---

## BUILD / RUN / TEST COMMANDS

```bash
# Install dependencies (runtime, build and test)
pip install -r requirements.txt

# Run the CLI from source
python src/main.py status -d /path/to/workspace

# Run the GUI from source
python src/main.py --gui

# Run the tests (do not write .pyc files into the tree: some are versioned)
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/ -v -p no:cacheprovider

# Build the CLI binaries
python -m PyInstaller gitbulk-windows.spec      # on Windows → dist/gitbulk-windows.exe
python -m PyInstaller gitbulk-linux.spec        # on Linux   → dist/gitbulk-linux

# Build the GUI binaries
python -m PyInstaller gitbulk-gui-linux.spec    # on Linux   → dist/gitbulk-gui-linux
./scripts/build_gui_linux.sh                    # on Linux   → dist/linux/GitBulk-GUI (rename for release)
.\scripts\build_gui_windows.ps1                 # on Windows → dist/windows/gitbulk-gui.exe (rename to gitbulk-gui-windows.exe)

# Prepare portable Git (Windows builds)
.\scripts\prepare_portable_git.ps1
```

### PYINSTALLER NOTES

- the `.spec` files are the canonical build definitions; they add `assets/` and `vendor/git/` as data (gui spec also `src/gui/icons` and `theme.qss`).
- the cli specs set `excludes=['PySide6', 'PySide2']` to keep cli binaries small.
- the gui spec adds hidden imports for `PySide6.QtSvg`, `PySide6.QtSvgWidgets`, `PySide6.QtXml`, `gui.translations` and `gui.icon_manager`.
- there is no windows gui `.spec` (`GitBulk-GUI-Windows.spec` was deleted); the windows gui is built with `scripts/build_gui_windows.ps1`.
- build output names do not all match the release asset names the installers download; rename before uploading (see `.docs/-github-guides/release-guide.md`, section 5).

---

## CODE STYLE GUIDELINES

### LANGUAGE AND STRINGS

- **user-facing strings are in english** in the cli and model layers (unified before v1.4; see `CHANGELOG.md`). gui strings live in `gui/translations.py` for five languages.
- internal comments may be spanish or english; do not rewrite them unless you are editing the surrounding logic.
- **brand enforcement:** `TR()` in `gui/translations.py` lowercases every translated string and then restores the product name as `GitBulk`. write new keys with that in mind (the result is always lowercase except `GitBulk`).

### FORMATTING

- indentation is **2 spaces** in `main.py`, `view/cli.py` and `persistence/config_repo.py`; other files use **4 spaces**. follow the style of the file you are editing.
- use `rich.console.Console` for all cli output; avoid bare `print()`.
- no formatter or linter is configured (no `ruff`, `black`, `flake8` config).

### IMPORTS AND MODULE STRUCTURE

- `model/__init__.py` and `view/__init__.py` re-export public functions; `main.py` imports through those packages.
- `src/` is put on the path (pyinstaller `pathex=['src']`), so modules import as `model`, `view`, `persistence`, `gui`.
- `gui/` modules use defensive `try/except ImportError` blocks to work both frozen and from source; resources go through `resource_path()` (`sys._MEIPASS`).

### GIT OPERATIONS

- add new operations to `model/git_ops.py` inside `run_git_operation`.
- return the standard tuple `(status_code: str, detail: str, repo_path: str, output: str)`.
- run git only through `_run_git_command(args, cwd, env)`; it resolves the executable from (1) the pyinstaller bundle, (2) local `vendor/git`, (3) `PATH`.
- surface errors through `parse_git_error(stderr)`.
- `GIT_TERMINAL_PROMPT=0` is set in the subprocess environment to avoid hangs; on windows `creationflags=0x08000000` (`CREATE_NO_WINDOW`).
- build commands as argument lists, never shell strings.

### GUI CONVENTIONS

- all heavy work runs in `QThread` workers (`gui/workers.py`); never block the main thread.
- ui log updates are batched by a 250 ms `QTimer` in `main_window.py`.
- drag-and-drop reordering is intentionally disabled; use the context-menu "move to group" actions.
- jetbrains mono is requested by name (`QFont("JetBrains Mono")`); it is not bundled.
- a new gui feature must be translatable: add its keys to all five languages in `gui/translations.py`.

---

## TESTING STRATEGY

| type | location | runner | libraries |
|------|----------|--------|-----------|
| unit tests | `tests/test_*.py` | `python -m pytest tests/ -v` | `unittest`, `unittest.mock`, `tempfile` |

there are no integration, gui or ci tests.

### CURRENT TEST STATE (IMPORTANT)

the suite has **30 tests** covering `scanner.py`, `auth.py`, `git_ops.py` and `error_handler.py`. according to the previous version of this guide, **only 10 pass and 20 fail** — `TODO(owner): re-run and confirm` (pytest was not installed on the machine that rewrote this file). the failures come from the migration from **gitpython to native `subprocess`**:

- `tests/test_git_ops.py` mocks `model.git_ops.Repo`, but `git_ops.py` no longer imports or uses `Repo`.
- `tests/test_error_handler.py` passes `GitCommandError` / `MagicMock` objects to `parse_git_error`, which now expects a plain string.
- `tests/test_scanner.py` expects `find_git_repos` to return path strings; it now returns dicts (`{ "path": ..., "metadata": ... }`).
- `tests/test_auth.py` passes: the credential file logic stayed compatible with its mocks.

### AGENT GUIDANCE ON TESTS

- before modifying `model/git_ops.py`, `model/error_handler.py` or `model/scanner.py`, update the corresponding tests to the current subprocess-based api.
- do not reintroduce gitpython as a runtime dependency to satisfy old tests; update the tests instead.
- mock `model.git_ops._run_git_command` for git operation tests.
- for `parse_git_error`, pass raw stderr strings.
- for `find_git_repos`, assert against `{ "path": str, "metadata": { "groups": [...] } }`.
- a change must not add new failures; fixing the suite is a high-value maintenance task.

---

## KEY ARCHITECTURAL DECISIONS

1. **native subprocess engine.** `model/git_ops.py` runs git through `subprocess.run` instead of gitpython, with the bundled → vendor → `PATH` resolution order above.
2. **shared layers.** cli and gui share `model/` and `persistence/`; add logic there rather than duplicating it in `view/cli.py` or `gui/main_window.py`.
3. **auto-tuning concurrency.** `model/concurrency.py` measures disk latency and picks the worker count; explicit values are capped at 50.
4. **single config file.** `~/.git_manager_pro.json` stores `last_directory`, `workspaces` and `language`.
5. **group topology.** repositories declare groups in `.gitbulk.repo.json` at their root (`{ "groups": ["backend", "fintech"] }`).
6. **workspace snapshots.** json lists of `{ path, url, branch }` used by `export`, `restore` and `workspace save/load/sync`.
7. **safe sync.** `workspace sync` moves repositories missing from the reference to `.gitbulk_archive/<repo>_<timestamp>/` (with `.gitbulk_archive_info.json`) instead of deleting them.
8. **installers download from releases.** `dist/` scripts download `releases/download/<VERSION>/<binary>` and are themselves served from `main` via `raw.githubusercontent.com`; their paths and the asset names are a public contract (readme and `gitbulk.rezzt.dev` link to them).

---

## SECURITY CONSIDERATIONS

### CREDENTIAL STORAGE

- `gitbulk auth` sets `credential.helper store` in the user's **global** git config and writes the github pat in plaintext to `~/.git-credentials`.
- `_restrict_file_permissions()` in `auth.py` hardens the file: posix `chmod 0o600`; windows `icacls /inheritance:r /grant:r <USERNAME>:F`.
- a security warning panel is shown after credentials are saved.
- **never log or expose tokens** in output, logs or error messages.

### DESTRUCTIVE OPERATIONS

- `clean` runs `git fetch --prune` and `git clean -xfd`; it requires interactive confirmation in the cli (`show_clean_warning()`) and must stay behind a strong warning modal in the gui.
- `workspace sync` archives (moves) repositories; it does not delete, but users must still confirm.
- `--dry-run` is supported for `clean` (`git clean -n`, `git fetch --dry-run`) and `restore` (lists missing repositories).

### SUBPROCESS AND SHELL INJECTION

- git commands are argument lists, not shell strings. user-provided paths and branch names go straight into the argument list; review any new concatenation carefully.

### NETWORK

- `ci_ops.py` calls `https://api.github.com/repos/{owner}/{repo}/commits/{branch}/check-runs` with the stored pat.
- `auth.py` detects the ssh agent and tests `ssh -T git@github.com -o ConnectTimeout=5`.

### REPOSITORY HYGIENE

- no `.env`, keys or tokens are versioned. `vendor/git/mingw64/etc/ssl/cert.pem` is git's public ca bundle.
- `snapshot.json` lists the owner's repository paths and urls: do not copy it into public texts or extend it.
- 35 `__pycache__/*.pyc` files are versioned despite `.gitignore` and embed the owner's local path; do not add more (run python with `PYTHONDONTWRITEBYTECODE=1`) and do not regenerate them in a commit.

---

## COMMON TASKS FOR AGENTS

### ADDING A NEW CLI OPERATION OR FLAG
1. add the choice / argument in `view/cli.py::parse_arguments`.
2. implement the git work in `model/git_ops.py::run_git_operation` (or a new `model/` module re-exported from `model/__init__.py`).
3. dispatch it in `main.py` and render the result through `view/`.
4. add or update tests in `tests/`.
5. document it in `project-doc/en-project-doc.md` and `project-doc/es-project-doc.md`, and add a bilingual `CHANGELOG.md` entry.

### ADDING A NEW GUI FEATURE
1. run the work in a `QThread` worker (`gui/workers.py`).
2. add every new string to the five languages in `gui/translations.py` and read it through `TR()`.
3. load icons through `icon_manager.py` and resources through `resource_path()` so the frozen build finds them; add new data folders to the gui `.spec` and build scripts.

### CHANGING DEPENDENCIES
1. edit `requirements.txt` (runtime pins are exact for `rich` and `pyinstaller`).
2. rebuild the four binaries and smoke-test them.
3. commit with the `changes` prefix, add the changelog entry and review the legal files (see deployment notes).

### BUMPING THE VERSION
- change every occurrence listed in *project overview* in one `changes` commit; see `.docs/-github-guides/changelog-guide.md`, section 5, and never leave `main` with an installer `VERSION` whose release does not exist yet.

---

## DEPLOYMENT NOTES

- releases are github releases tagged `v<x.y.z>` on `main`, with exactly four assets: `gitbulk-windows.exe`, `gitbulk-gui-windows.exe`, `gitbulk-linux`, `gitbulk-gui-linux` (plus `SHA256SUMS`). the installers download them by name.
- one-line install (served from `main`, also linked from `README.md` and `gitbulk.rezzt.dev`):
  - windows: `iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/windows/install_{gui,cli}.ps1" | iex`
  - linux: `curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/linux/install_{gui,cli}.sh" | bash`
- `dist/windows/install_*.ps1` add the binary to the user `PATH` (gui: start menu shortcut); `dist/linux/install_*.sh` install into `~/.local/bin` (gui: `.desktop` entry and icon). `install_gui.sh` fetches `src/gui/icons/gitbulk_icon.png`, which is not versioned — `TODO(owner): add the PNG or point to the SVG`.
- binaries are not code-signed.
- legal files: `LICENSE` (mit) is the only one. a new dependency, a change to `vendor/git/`, to stored data (`~/.git_manager_pro.json`, `~/.git-credentials`, `.gitbulk_archive/`) or to network calls must be reflected in `LICENSE` / `vendor/git/LICENSE.txt` and, once they exist, in `NOTICE`, `THIRD_PARTY_LICENSES.md` and `PRIVACY.md` (proposed in `.docs/repo-audit-and-fix.md`). the windows binaries redistribute mingit (gplv2) and the gui binaries pyside6 (lgplv3).
- documentation layout: `README.md` (spanish), `CHANGELOG.md`, `LICENSE`, `AGENTS.md` and `CLAUDE.md` at the root; `project-doc/` for the technical manual in english and spanish; `dist/README-Dist.md` for the distribution folder.

---

## ADDITIONAL ENTRY-POINT CONVENTIONS

## GitBulk — CLAUDE.md

> This file exists so Claude (and any other AI agent) always has the git
> workflow rules at hand. For the full architecture, tech stack, build commands and
> code style guide, see [`AGENTS.md`](./AGENTS.md) — this file only carries
> the commit / PR / merge / release conventions.
>
> **When the user asks for a commit, PR, merge or release title/description,
> follow the section below first. Never add AI attribution of any kind.**
>
> repository layout: `CHANGELOG.md`, `LICENSE` (MIT), `README.md` and `AGENTS.md` live at the
> root; there is no `.github/` and no community files (`SECURITY.md`, `CONTRIBUTING.md`,
> `CODE_OF_CONDUCT.md`) yet. `.docs/` is versioned and holds the git guides
> (`.docs/manager.md`, `.docs/-github-guides/`), the audit work file
> (`.docs/repo-audit-and-fix.md`) and internal planning notes. `dist/` versions only the
> one-line installers and `README-Dist.md` (the binaries are release assets);
> `vendor/git/` versions MinGit for Windows; `build/` is ignored.

## COMMIT, PR, MERGE & RELEASE GUIDELINES

read `.docs/manager.md` first, then the selected guide in `.docs/-github-guides/`. these files are versioned; this digest also works without opening them.

| request | guide |
| --- | --- |
| commit title, body and changelog | `commit-guide.md`, `changelog-guide.md` |
| pull request or merge | `pr-merge-guide.md`, `branching-guide.md` |
| version and release | `release-guide.md`, `changelog-guide.md` |
| permissions and sensitive data | `agent-rules.md` |

- inspect `git status`, both diffs and recent history before describing changes
- use `<prefix> | <imperative summary>` with `update`, `fix`, `hotfix`, `changes` or `changelog`; keep titles within 72 characters
- write commit bodies as 2 to 6 markdown bullets, one logical change per line, with literal paths in backticks
- never add authorship footers, automated attribution, signatures or generation notices; preserve the configured git identity
- update `CHANGELOG.md` under `## SIN PUBLICAR / UNRELEASED` in matching `### CASTELLANO` and `### ENGLISH` sections
- use the existing changelog category vocabulary and preserve language parity; describe only changes in the actual diff
- summarize pull requests in 1 to 3 bullets per category and language, at most 110 characters per bullet
- documentation and repository-management work targets `main`; the remote default is `main`; do not silently promote development work to the default branch
- the authorization for a requested action remains valid throughout that task; creating a pull request includes pushing its branch, but does not authorize merging or publishing
- use merge commits when a merge is requested; never force-push, rewrite published history or remove branches without an explicit instruction
- releases use the approved version and an immutable tag on the verified release commit, with english notes from the closed changelog; do not create a release for documentation work
- deliver requested titles, bodies and changelog fragments in separate code blocks; report executed actions with their commit hash or pull request link
