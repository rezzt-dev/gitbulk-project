import json
from pathlib import Path
from typing import Dict, Any
from rich.console import Console

console = Console()

 # definimos donde se guardara el archivo de configuracion.
CONFIG_FILE = Path.home() / ".git_manager_pro.json"

 # configuramos por defecto si es la primera vez que se abre el programa.
DEFAULT_CONFIG = {
  "last_directory": "",
  "workspaces": {}
}

def load_config() -> Dict[str, Any]:
  """
  carga la configuracion desde el archivo JSON del usuario.
  si el archivo no existe o esta corrupto, devuelve la configuracion por defecto.
  """

  if not CONFIG_FILE.exists():
    return DEFAULT_CONFIG.copy()
  
  try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
    
  except (json.JSONDecodeError, IOError):
    return DEFAULT_CONFIG.copy()

def save_config(config_data: Dict[str, Any]) -> None:
  """
  Guarda el diccionario de configuracion en el archivo JSON del usuario.
  Si no es posible escribir el fichero, informa al usuario en lugar de fallar silenciosamente.
  """

  try:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
      json.dump(config_data, f, indent=4)
  except IOError as e:
    console.print(f"[bold yellow][Warning][/bold yellow] Could not save configuration to {CONFIG_FILE}: {e}")