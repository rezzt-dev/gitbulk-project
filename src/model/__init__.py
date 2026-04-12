"""
capa de modelo (model)
contiene toda la logica de negocio pura: busca de directorios y ejecucion 
de comandos Git, sin interactuar con la terminal ni el usuario.
"""

from .scanner import find_git_repos, get_groups_topology
from .git_ops import run_git_operation, get_repo_metadata, clone_repo, get_all_branches
from .auth import setup_global_git_credentials, get_github_token, ensure_ssh_agent, test_ssh_connectivity
from .ci_ops import get_ci_status
from .concurrency import calculate_optimal_workers
from .archiver import archive_repository
from .interactive import open_external_editor

__all__ = [
    "find_git_repos",
    "get_groups_topology",
    "run_git_operation",
    "setup_global_git_credentials",
    "get_repo_metadata",
    "clone_repo",
    "get_all_branches",
    "get_github_token",
    "get_ci_status",
    "calculate_optimal_workers",
    "ensure_ssh_agent",
    "test_ssh_connectivity",
    "archive_repository",
    "open_external_editor"
]