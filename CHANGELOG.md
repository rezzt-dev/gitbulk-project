# Changelog

All notable changes to this project will be documented in this file.

This format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned

- `gitbulk update` command: self-update the binary by querying the latest GitHub release and replacing the local executable in-place.
- `.gitbulk.toml` workspace configuration file: per-directory defaults for `--workers`, `--file`, and `--branch`, superseding the single-field JSON stored in the user home directory.
- `--dry-run` flag extension to additional write operations beyond `clean` and `restore`.

### Added

- `LICENSE` file (MIT) added to the repository root.
- Full automated test suite (`tests/`) with 30 passing tests covering `scanner.py`, `auth.py`, `git_ops.py`, and `error_handler.py`.
- Upper-bound validation for the `--workers` flag (maximum: 50 threads).
- Warning when `--autostash` is passed with an operation other than `pull`.
- `_restrict_file_permissions()` function in `auth.py`: cross-platform credential file permission hardening using `icacls` on Windows and `chmod 0o600` on POSIX.
- Security warning panel displayed after `auth` credential setup, informing the user of plaintext storage.
- Explicit error feedback in `save_config` when the configuration file cannot be written.
- Typed `error` field in `get_repo_metadata` and `get_all_branches` return dicts to surface repository-level failures.
- Typed `reason` field in `get_ci_status` return dict distinguishing HTTP 401, HTTP 404, network timeout, and unknown API errors.
- `show_clean_warning()` function in the view layer to properly separate the destructive operation prompt from the controller.
- `--dry-run` flag for `clean` (uses `git clean -n` and `git fetch --dry-run`) and `restore` (lists missing repositories without cloning).

### Changed

- All user-facing text unified to English across `cli.py`, `main.py`, `error_handler.py`, `auth.py`, `ci_ops.py`, and `git_ops.py`.
- All bare `print()` calls replaced by `console.print()` from `rich` throughout the entire source tree.
- `ci-status` output table extended with a `Detail` column showing machine-readable error reasons.
- `show_branches_compact()` now renders an `[ERROR]` row for repositories where branch data could not be read.
- Security warning in `auth.py` upgraded to a styled `rich.Panel` instead of plain text output.
- `save_config` error message translated to English and styled with `rich` markup.
- `clean` confirmation prompt moved from `main.py` (controller) to `view/cli.py` (view layer).
- `requirements.txt` dependencies pinned to exact tested versions.

### Fixed

- `os.chmod(0o600)` was a no-op on Windows; replaced with `icacls`-based equivalent.
- Broad `except Exception: pass` blocks in `get_repo_metadata` and `get_all_branches` now surface errors via the `error` dict field.
- `ci_ops.py` silently returned `{"state": "error"}` without any reason; now returns a descriptive `reason` field.
- `save_config` silently swallowed `IOError`; now prints a visible warning.

---

## [0.1.0] — 2026-01-01

### Added

- Initial public release of GitBulk.
- Concurrent bulk Git operations: `fetch`, `pull`, `status`, `checkout`, `clean`, `export`, `restore`, `current-branch`, `ci-status`, `auth`.
- `ThreadPoolExecutor`-based parallel execution with configurable `--workers` flag.
- Session persistence: last-used directory stored in `~/.git_manager_pro.json`.
- Rich terminal UI with color-coded status codes and real-time progress bars.
- GitHub Actions CI status polling via the GitHub Check Runs API.
- Export/restore workflow for bulk repository cloning from a JSON snapshot.
- Cross-platform installation scripts (`install.ps1` for Windows, `install.sh` for Linux/macOS).
- PyInstaller-based standalone binary compilation support.
