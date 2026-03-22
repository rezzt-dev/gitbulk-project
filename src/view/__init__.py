"""
capa de vista (view).
maneja la interaccion con el usuario: argumentos CLI y visualizacion en terminal.
"""

from .cli import (
  parse_arguments,
  show_welcome,
  show_no_repos_found,
  show_start_processing,
  show_result,
  show_summary
)

__all__ = [
  "parse_arguments",
  "show_welcome",
  "show_no_repos_found",
  "show_start_processing",
  "show_result",
  "show_summary"
]