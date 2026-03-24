# GitBulk Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Authentication](#authentication)
5. [Core Commands](#core-commands)
6. [Global Flags](#global-flags)
7. [Advanced Usage](#advanced-usage)

## Introduction
GitBulk is a robust, concurrent Command Line Interface (CLI) utility built in Python. It is designed to orchestrate and execute Git operations across multiple isolated repositories simultaneously. Utilizing `GitPython` as its underlying engine and `ThreadPoolExecutor` for parallel processing, GitBulk mitigates the latency and repetitive strain of managing large-scale microservice architectures or multi-repository environments.

## Features
- **Concurrent Execution**: Processes multiple directories simultaneously without thread-blocking.
- **Cross-Platform Compatibility**: Fully functional on Linux, Windows, and macOS environments.
- **Interactive Safeguards**: Prevents accidental data loss through interactive prompts on destructive actions.
- **Detailed CLI Reporting**: Utilizes `rich` to render compact, color-coded matrices and progress bars.
- **Authentication Handling**: Capable of reading global Git credentials seamlessly to interact with remote origins without interrupting process flows.
- **CI / Actions Monitoring**: Connects natively to the GitHub API to check live pipeline status.

## Installation

### Prerequisites
- Python 3.10 or higher.
- Git installed and accessible in the system PATH.

### Setup from Source
Clone the repository and install the required dependencies:

```bash
git clone https://github.com/rezzt-dev/gitbulk-project.git
cd gitbulk-project
pip install -r requirements.txt
```

### Building the Binary
To compile GitBulk into a standalone executable that does not require a Python runtime environment, use PyInstaller:

```bash
pip install pyinstaller
pyinstaller --name gitbulk --onefile src/main.py
```
The resulting binary will be located in the `dist/` directory. You can move this binary to your system's binaries folder (e.g., `/usr/local/bin/` on Linux) for global access.

## Authentication
Certain network-reliant operations (like fetching remote branches or querying CI statuses) require valid GitHub credentials. GitBulk simplifies this by requesting a Personal Access Token (PAT) once and storing it securely.

To configure your credentials:
```bash
python main.py auth
```
This command stores the credential string sequentially in `~/.git-credentials`, configuring your global Git helper to use it. Subsequent operations will extract this token silently.

## Core Commands

### `status`
Scans the working tree of all repositories to report their divergence relative to the tracked upstream branches.
**Output States**: `[CLEAN]`, `[MODIFIED]`, `[AHEAD]`, `[BEHIND]`.

### `fetch`
Downloads the remote history without integrating it into the local working tree.
**Output States**: `[OK]`, `[UPDATES]` (indicates commits pending to be pulled).

### `pull`
Updates the active branch with the latest remote commits exclusively via fast-forward.
**Output States**: `[OK]`, `[CONFLICT]`, `[DIVERGENT]`.
**Related Flag**: `--autostash`

### `checkout`
Shifts the `HEAD` pointer of all repositories to a specified branch. If the branch exists locally, it checks it out. If it exists tracking on the remote but not locally, it creates the link and downloads it. Repositories lacking the branch are safely ignored.
**Required Flag**: `-b <branch_name>`

### `current-branch`
Renders an ultra-compact topographic map showing the active branch, existing local branches, and remote-only branches for each repository.

### `clean`
A strict, destructive operation that executes `git fetch --prune` and `git clean -xfd`. It permanently removes deleted remote references and untracked files/directories (like `node_modules` or `build`).
**Warning**: Requires interactive confirmation.

### `ci-status`
Connects asynchronously to the GitHub API to query the integration pipelines (GitHub Actions) of the current `HEAD` commit.
**Output States**: `[PASS]`, `[FAIL]`, `[PEND]`, `[NONE]`

### `export`
Serializes the state, URLs, and active branch metadata of all discovered repositories into a JSON snapshot.
**Related Flag**: `-f <file_path>`

### `restore`
Reads a previously generated JSON snapshot and clones any missing repositories into the active working directory, positioning them on the identical branch captured during the export.
**Related Flag**: `-f <file_path>`

## Global Flags

- `-d, --dir <path>`: Specifies the root directory to scan recursively. Defaults to the current or last used directory.
- `-w, --workers <int>`: Defines the number of concurrent thread workers. Default: 5.
- `-l, --log <path>`: Instructs the system to dump a raw text log of the operation outputs into the specified file.
- `-b, --branch <name>`: Target branch parameter. Mandatory for the `checkout` operation.
- `-f, --file <path>`: The target JSON file path for the `export` and `restore` operations. Default: `snapshot.json`.
- `--autostash`: Safely stashes uncommitted local modifications prior to a `pull` operation, reapplying them automatically after the remote history is integrated.

## Advanced Usage

### Safe Pulling with AutoStash
When developers leave uncommitted work, a standard pull will fail. Use autostash to bypass blocks while preserving code:
```bash
python main.py pull --autostash
```
State returns `[SYNC+STASH]` if modifications were restored successfully, or `[STASH CONFLICT]` if manual merge intervention is necessary.

### Piped Execution
GitBulk is designed to be compatible with automated CI runners. Interactive commands like `clean` will safely intercept broken pipes or empty standard inputs (such as `< /dev/null`), aborting operation execution cleanly without crashing the pipeline.
