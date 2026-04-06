# GitBulk Technical Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Key Features](#key-features)
3. [Installation and Deployment](#installation-and-deployment)
4. [Authentication Management](#authentication-management)
5. [Operation Catalog](#operation-catalog)
6. [Global Flags and Parameters](#global-flags-and-parameters)
7. [Advanced Usage Scenarios](#advanced-usage-scenarios)

---

## Introduction

GitBulk is a high-performance, integrated solution (CLI and GUI) built in Python for large-scale Git repository orchestration. Designed for microservice architectures and multi-repository environments, the tool mitigates operational latency through concurrent processing, enabling complete development lifecycles to be executed across hundreds of projects simultaneously and securely.

---

## Key Features

- **Concurrent Execution**: Engine based on `ThreadPoolExecutor` that eliminates bottlenecks in network and disk operations.
- **Native Desktop Interface**: High-fidelity application for Windows and Linux environments, featuring dark mode support and real-time monitoring.
- **Operational Resilience**: Built-in protection mechanisms with interactive prompts to prevent accidental data loss during destructive commands.
- **High-Density Technical Reporting**: Visualization using the `rich` library, providing compact matrices, color-coded statuses, and progress telemetry.
- **CI / GitHub Actions Integration**: Native status querying for pipelines directly from the terminal or the desktop interface.

---

## Installation and Deployment

### Recommended Installation (Web Installer)

GitBulk provides optimized one-step installers that automatically configure binaries, shortcuts, and environment variables.

**Windows (PowerShell):**
```powershell
iwr -useb "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install.ps1" | iex
```

**Linux (Bash):**
```bash
curl -fsSL "https://raw.githubusercontent.com/rezzt-dev/gitbulk-project/main/dist/gui/install_linux.sh" | bash
```

### Setup from Source (Development)

For development or customization environments, clone the repository and install the dependency tree:

```bash
git clone https://github.com/rezzt-dev/gitbulk-project.git
cd gitbulk-project
pip install -r requirements.txt
```

---

## Authentication Management

Certain operations (such as `fetch` on private repositories or `ci-status` queries) require valid credentials. GitBulk centralizes this management by requesting a Personal Access Token (PAT) once and storing it securely within the operating system's credentials.

To configure the access environment:
```bash
gitbulk auth
```
This command configures the global Git helper, allowing subsequent operations to execute silently without credential prompt interruptions.

---

## Operation Catalog

### `status`
Analyzes the working tree state and reports divergence relative to tracked remote branches.
**States**: `[CLEAN]`, `[MODIFIED]`, `[AHEAD]`, `[BEHIND]`.

### `fetch`
Downloads remote history metadata without integrating changes into local branches.
**States**: `[OK]`, `[UPDATES]`.

### `pull`
Updates the active branch using a `fast-forward only` integration strategy.
**Suggested Flags**: `--autostash`.

### `checkout`
Performs a bulk transition of `HEAD` towards the specified branch.
**Required Parameter**: `-b <branch_name>`.

### `current-branch`
Generates an ultra-compact topographic map showing the active branch and local/remote references.

### `clean`
**Destructive Operation**: Executes `git fetch --prune` and `git clean -xfd`. Removes dead remote references and untracked files. Requires interactive confirmation.

### `ci-status`
Asynchronous query to the GitHub API to report the status of continuous integration pipelines.
**States**: `[PASS]`, `[FAIL]`, `[PEND]`, `[NONE]`.

### `export` / `restore`
Enables persistence and reconstruction of large-scale workspaces using JSON snapshot files. Useful for instant onboarding processes.

---

## Global Flags and Parameters

- `-d, --dir <path>`: Root directory for recursive scanning. Preserves the persistence of the last used path.
- `-w, --workers <n>`: Number of concurrent threads (Limit: 50). Default: `5`.
- `-l, --log <path>`: Redirection of technical output to a persistent log file.
- `-b, --branch <name>`: Target branch for transition operations (`checkout`).
- `--autostash`: Automates the safeguarding of local changes prior to an update.
- `--dry-run`: Preview changes without real application (Supported in `clean` and `restore`).
- `--gui`: Forces the launch of the graphical user interface.

---

## Advanced Usage Scenarios

### Synchronization with AutoStash
To avoid blocks caused by uncommitted local changes during a bulk pull, the `--autostash` instruction allows for automatic stashing, updating, and re-applying of the work patch.
```bash
gitbulk pull --autostash
```

### Execution in CI Environments (Piped Execution)
GitBulk has been designed following POSIX process standards. Interactive operations like `clean` automatically detect the absence of a terminal (`tty`) or null `stdin` injections, aborting execution safely to prevent catastrophic failures in automated pipelines.
