# GitBulk — Agent Guide

> **Audience**: AI coding agents with no prior context about this project.  
> **Scope**: Covers architecture, build/test workflow, code conventions, security, and known caveats for the GitBulk desktop project.

---

## Project Overview

GitBulk is a cross-platform desktop tool (CLI + GUI) for orchestrating bulk Git operations across hundreds of repositories concurrently. It is developed by **rezzt-dev** and branded as a senior-level workspace manager.

- **Current version**: `1.4.0` (see `CHANGELOG.md`).
- **Language**: Python 3.10+.
- **License**: MIT (`LICENSE`).
- **Distribution model**: PyInstaller-based standalone executables for Windows and Linux, plus direct Python execution from source.
- **Repository layout**:
  - `src/` — application source.
  - `tests/` — automated test suite.
  - `scripts/` — build and preparation scripts.
  - `dist/` — release installers and pre-built binaries.
  - `vendor/git/` — optional bundled MinGit for Windows builds.
  - `assets/` — application icon.
  - `project-doc/` — human-readable technical docs (English and Spanish).
  - `.docs/` — internal planning and build notes.

### What GitBulk Does

- Scans a root directory recursively for Git repositories.
- Runs operations in parallel using `ThreadPoolExecutor`.
- Supports: `status`, `fetch`, `pull`, `push`, `commit`, `checkout`, `clean`, `export`, `restore`, `current-branch`, `ci-status`, `auth`, `workspace`, `groups`.
- Persists last directory, saved workspaces, and UI language in `~/.git_manager_pro.json`.
- Optional PySide6 GUI with dark theme, multi-language support, workspace tree, group inspector, commit hub, and sync preview.

---

## Technology Stack

| Component | Library / Tool | Purpose |
|-----------|---------------|---------|
| Runtime | Python 3.10+ | Core language. |
| CLI rendering | `rich==14.3.3` | Colored tables, panels, progress bars, prompts. |
| GUI framework | `PySide6>=6.5.0` | Native Qt6 desktop interface. |
| Git execution | `subprocess` (native Git binary) | Replaced GitPython; runs `git` commands directly for speed and reduced dependencies. |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` | Parallel repo operations. |
| Bundling | `pyinstaller==6.19.0` | One-file `.exe` / binary distribution. |
| Testing | `pytest>=8.0.0` | Unit tests. |
| Portable Git (Windows) | MinGit 2.44.0 | Bundled Git for machines without a system install. |

### Entry Point

- `src/main.py` is the single entry point for both CLI and GUI.
- If the binary is frozen (PyInstaller) and launched with no arguments, the GUI starts automatically.
- Explicitly launch the GUI with `python -m src.main --gui` or `gitbulk --gui`.

---

## Architecture

GitBulk follows a layered architecture with a clear separation between business logic and presentation.

```text
src/
├── main.py              # Entry point, operation dispatch, progress orchestration.
├── view/
│   ├── __init__.py      # Re-exports the public CLI view API.
│   └── cli.py           # Argument parsing (argparse) and terminal output (rich).
├── model/
│   ├── __init__.py      # Re-exports pure business-logic functions.
│   ├── scanner.py       # Recursive Git repo discovery and group topology.
│   ├── git_ops.py       # Subprocess-based Git operations (status, pull, etc.).
│   ├── auth.py          # Git credential setup, PAT extraction, SSH agent helpers.
│   ├── ci_ops.py        # GitHub Actions Check Runs API polling.
│   ├── concurrency.py   # Hardware-aware worker auto-tuning.
│   ├── archiver.py      # Safe repo archiving to `.gitbulk_archive/`.
│   ├── interactive.py   # External editor launch and CLI prompts.
│   └── error_handler.py # Normalizes raw Git stderr into user messages.
├── persistence/
│   └── config_repo.py   # JSON config read/write (`~/.git_manager_pro.json`).
└── gui/
    ├── app.py           # QApplication setup, DPI, fonts, theme, language load.
    ├── main_window.py   # Main Qt window, tree, sidebar, operations.
    ├── workers.py       # QThread workers for scanning and operations.
    ├── translations.py  # Translation dictionaries and lowercase brand enforcer.
    ├── icon_manager.py  # SVG icon colorizer and cache.
    ├── theme.qss        # Dark QSS stylesheet.
    └── icons/           # SVG icon assets.
```

### Key Design Decisions

1. **Native subprocess engine**: `model/git_ops.py` runs Git via `subprocess.run` instead of GitPython. It resolves the Git executable from (1) PyInstaller bundle, (2) local `vendor/git`, or (3) system `PATH`.
2. **Auto-tuning concurrency**: `model/concurrency.py` benchmarks disk I/O and caps workers at 50. `-w 0` enables hardware-based tuning.
3. **Single config file**: `~/.git_manager_pro.json` stores `last_directory`, `workspaces`, and `language`.
4. **Group topology**: Repositories declare groups via a `.gitbulk.repo.json` file in the repo root (`{ "groups": ["backend", "fintech"] }`).
5. **Workspace snapshots**: JSON lists of `{ path, url, branch }` used by `export`, `restore`, `workspace save/load/sync`.
6. **Safe sync**: `workspace sync` archives repos missing from the reference into `.gitbulk_archive/<repo>_<timestamp>/` rather than deleting them.

---

## Build and Distribution

### Prerequisites

```bash
pip install -r requirements.txt
```

On Windows, for fully portable builds you also need MinGit in `vendor/git`:

```powershell
.\scripts\prepare_portable_git.ps1
```

### Running from Source

```bash
# CLI
python src/main.py status -d /path/to/workspace

# GUI
python src/main.py --gui
```

### Building Executables

#### Windows GUI

```powershell
.\scripts\build_gui_windows.ps1
# or
.\scripts\build_gui.ps1
```

Produces `dist/windows/gitbulk-gui-windows.exe`.

#### Windows CLI

The CLI build uses the `gitbulk-windows.spec` file:

```bash
python -m PyInstaller gitbulk-windows.spec
```

Produces `dist/windows/gitbulk-windows.exe`.

#### Linux GUI

```bash
chmod +x scripts/build_gui_linux.sh
./scripts/build_gui_linux.sh
```

Produces `dist/linux/GitBulk-GUI`.

#### Linux CLI

```bash
python -m PyInstaller gitbulk-linux.spec
```

Produces `dist/linux/gitbulk-linux`.

### Distribution Installers

- `dist/windows/install_gui.ps1` and `dist/windows/install_cli.ps1` download binaries from GitHub Releases, add them to the user `PATH`, and (GUI) create a Start Menu shortcut.
- `dist/linux/install_gui.sh` and `dist/linux/install_cli.sh` do the equivalent for Linux/macOS-style shells.

### PyInstaller Notes

- `.spec` files are the canonical build definitions and include `--add-data` entries for assets, GUI resources, and portable Git.
- The CLI specs explicitly `exclude=['PySide6', 'PySide2']` to keep CLI binaries smaller.
- The GUI specs include hidden imports for `PySide6.QtSvg`, `PySide6.QtSvgWidgets`, `PySide6.QtXml`, `gui.translations`, and `gui.icon_manager`.

---

## Testing

### Running Tests

```bash
python -m pytest tests/ -v
```

### Current Test State (Important)

The project has **30 tests** covering `scanner.py`, `auth.py`, `git_ops.py`, and `error_handler.py`.  
**As of the latest source state, only 10 pass and 20 fail.**

The failures are caused by a recent migration from **GitPython to native `subprocess`**:

- `tests/test_git_ops.py` mocks `model.git_ops.Repo`, but `git_ops.py` no longer imports or uses `Repo`.
- `tests/test_error_handler.py` passes `GitCommandError` / `MagicMock` objects to `parse_git_error`, but the function now expects a plain string.
- `tests/test_scanner.py` expects `find_git_repos` to return a list of path strings; it now returns a list of dicts (`{ "path": ..., "metadata": ... }`).

`tests/test_auth.py` passes because the credential file logic in `model/auth.py` remained compatible with the test mocks.

### Agent Guidance on Tests

- Before modifying `model/git_ops.py`, `model/error_handler.py`, or `model/scanner.py`, update the corresponding tests to reflect the current subprocess-based API.
- Do not reintroduce GitPython as a runtime dependency just to satisfy existing tests; update the tests instead.
- Prefer mocking `model.git_ops._run_git_command` for Git operation tests rather than `Repo`.
- For `parse_git_error`, pass raw stderr strings.
- For `find_git_repos`, assert against the dict structure `{ "path": str, "metadata": { "groups": [...] } }`.

---

## Code Style Guidelines

### Language and Strings

- **User-facing strings are in English** (unified in v1.4; see `CHANGELOG.md`).
- Internal comments may be Spanish or English; do not rewrite them unless you are editing the surrounding logic.
- **Brand enforcement**: The word "gitbulk" must appear lowercase in user-facing text, except for the product name "GitBulk". The GUI translation helper enforces this in `gui/translations.py` (`TR` function).

### Formatting

- Indentation is **2 spaces** in `main.py` and `view/cli.py`; other files use **4 spaces**. Follow the style of the file you are editing.
- Use `rich.console.Console` for all CLI output; avoid bare `print()`.
- Keep lines reasonably short for readability inside Rich markup.

### Imports and Module Structure

- Use explicit relative imports inside packages where the package already does so.
- `model/__init__.py` and `view/__init__.py` re-export public functions; import through those packages in `main.py`.
- `gui/` modules use defensive try/except import blocks to handle both PyInstaller and dev execution.

### Git Operations

- Add new operations to `model/git_ops.py` inside `run_git_operation`.
- Return the standard tuple `(status_code: str, detail: str, repo_path: str, output: str)`.
- Surface errors through `parse_git_error(stderr)`.
- Set `GIT_TERMINAL_PROMPT=0` in the subprocess environment to avoid hangs.
- On Windows, pass `creationflags=0x08000000` (`CREATE_NO_WINDOW`) to subprocess calls.

### GUI Conventions

- All heavy work must run in `QThread` workers (`gui/workers.py`); never block the main thread.
- UI log updates are batched via a 250 ms timer in `main_window.py`.
- Drag-and-drop reordering is intentionally disabled; use context-menu "Move to group" actions.
- The GUI uses JetBrains Mono as the master font and a custom dark QSS theme.

---

## Security Considerations

### Credential Storage

- `gitbulk auth` stores the GitHub PAT in plaintext in `~/.git-credentials` using Git's `credential.helper store`.
- `auth.py` hardens file permissions:
  - POSIX: `chmod 0o600`.
  - Windows: `icacls /inheritance:r /grant:r <USERNAME>:F`.
- A visible security warning panel is shown after credentials are saved.
- **Never log or expose tokens** in output, logs, or error messages.

### Destructive Operations

- `clean` runs `git fetch --prune` and `git clean -xfd`. It requires interactive confirmation in the CLI and should be gated by a strong warning modal in the GUI.
- `workspace sync` archives (moves) repositories to `.gitbulk_archive/`; it does not permanently delete, but users must still confirm.
- `--dry-run` is supported for `clean` and `restore` to preview actions without side effects.

### Subprocess and Shell Injection

- Git commands are constructed as argument lists, not shell strings.
- User-provided paths and branch names are passed directly to `subprocess.run` arguments, but review any new concatenation carefully.

### Network

- `ci_ops.py` calls the GitHub Check Runs API with the stored PAT over HTTPS.
- `auth.py` includes SSH agent detection and a basic GitHub SSH connectivity test.

---

## Configuration Files

- **No `pyproject.toml`, `setup.py`, or `package.json` exists.** The project is driven by `requirements.txt` and PyInstaller `.spec` files.
- `.gitignore` excludes build artifacts, virtual environments, Python cache, and compiled binaries.
- `requirements.txt` is the source of truth for runtime, build, and test dependencies.

---

## Useful Commands Summary

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python src/main.py status -d .

# Run GUI
python src/main.py --gui

# Run tests
python -m pytest tests/ -v

# Build Windows CLI
python -m PyInstaller gitbulk-windows.spec

# Build Windows GUI
.\scripts\build_gui_windows.ps1

# Build Linux GUI
chmod +x scripts/build_gui_linux.sh
./scripts/build_gui_linux.sh

# Prepare portable Git (Windows only)
.\scripts\prepare_portable_git.ps1
```

---

## Notes for Future Agents

- The CLI and GUI share the same `model/` and `persistence/` layers. Prefer adding logic there rather than duplicating it in `view/cli.py` or `gui/main_window.py`.
- The `CHANGELOG.md` is actively maintained; add entries for user-visible changes and security fixes.
- If you add a new CLI flag, update `view/cli.py::parse_arguments`, `main.py`, and the relevant tests.
- If you add a new GUI feature, ensure it is translatable and update `gui/translations.py` for all five supported languages (`es_ES`, `en_US`, `en_UK`, `de_DE`, `fr_FR`).
- Be aware that the current test suite is out of sync with the subprocess migration; fixing it is a high-value maintenance task.
