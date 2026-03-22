"""
capa de persistencia (persistence).
maneja la lectura y escritura de la configuracion del usuario (JSON).
"""

from .config_repo import load_config, save_config

__all__ = [
  "load_config",
  "save_config"
]