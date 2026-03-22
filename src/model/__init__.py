"""
capa de modelo (model)
contiene toda la logica de negocio pura: busca de directorios y ejecucion 
de comandos Git, sin interactuar con la terminal ni el usuario.
"""

from .scanner import find_git_repos
from .git_ops import run_git_operation

__all__ = [
  "find_git_repos",
  "run_git_operation"
]