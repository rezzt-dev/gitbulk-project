# GitBulk technical documentation

## table of contents
1. [introduction](#introduction)
2. [key features](#key-features)
3. [engine architecture](#engine-architecture)
4. [installation and deployment](#installation-and-deployment)
5. [authentication management](#authentication-management)
6. [workspace system](#workspace-system)
7. [group organization](#group-organization)
8. [operation catalog](#operation-catalog)
9. [global flags and parameters](#global-flags-and-parameters)

---

## introduction

GitBulk is a high-performance integrated solution (cli and gui) for massive git repository orchestration. designed for microservice architectures, the tool eliminates operational latency through concurrent processing and an optimized native engine.

---

## key features

- **intelligent concurrency**: hardware-aware auto-tuning to maximize disk and network throughput.
- **workspaces**: persistence of entire environments with logical state synchronization.
- **corporate branding**: minimalist interface with modern typography and strict lowercase compliance.
- **native multi-language support**: full translation into spanish, english (us/uk), german, and french.
- **visual conflict management**: dedicated hubs for error resolution and bulk commits.

---

## engine architecture

the GitBulk engine has been reprogrammed to utilize native subprocess calls, bypassing external library limitations. it includes:
- **ui throttling**: batched updates (250ms) for extreme responsiveness.
- **icon cache**: i/o optimization via static visual asset persistence.
- **ssh diagnostics**: automatic detection and configuration of ssh agents for secure tunneling.

---

## installation and deployment

### web installers

**windows (powershell):**
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install.ps1" | iex
```

**linux (bash):**
```bash
curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install_linux.sh" | bash
```

---

## authentication management

GitBulk utilizes personal access tokens (pat) stored securely within the system credentials.
```bash
gitbulk auth
```

---

## workspace system

workspaces allow for saving and restoring full states of root directories.
- **save**: freezes the current topology.
- **load**: automatically clones missing repositories.
- **sync**: reconciles disk state with a reference definition, archiving unwanted repositories.

---

## group organization

via the group inspector, GitBulk detects tags in `.gitbulk.repo.json` to logically group repositories (e.g., backend, frontend, microservices).

---

## operation catalog

### `status`
visually analyzes divergences and local states.

### `commit` / `push`
bulk write operations with support for custom messages and interactive dialogs.

### `workspace`
commands: `save`, `load`, `list`, `delete`, `sync`.

### `groups`
inspection of the logical topology of the workspace.

### `fetch` / `pull`
remote synchronization with `--autostash` support.

### `ci-status`
real-time monitoring of github actions pipelines.

---

## global flags and parameters

- `-d, --dir`: root directory (persists across sessions).
- `-w, --workers`: concurrent threads. use `0` for automatic hardware tuning.
- `--gui`: launches the native graphical interface.
- `--dry-run`: preview of destructive operations.
