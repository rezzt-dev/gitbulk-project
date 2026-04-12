import os
from typing import List

def find_git_repos(root_path: str) -> List[str]:
  """
  busca de forma recursiva directorios que contengan una carpeta '.git'.
  Optimizado usando os.scandir (iterativo) para mejor rendimiento y estabilidad.
  """
  repos = []
  if not os.path.exists(root_path):
    return repos

  # Usamos una pila (stack) para busqueda iterativa (evita RecursionError)
  stack = [root_path]
  
  while stack:
    current_dir = stack.pop()
    try:
      with os.scandir(current_dir) as it:
        is_repo = False
        subdirs = []
        for entry in it:
          if entry.is_dir():
            if entry.name == ".git":
              repos.append(current_dir)
              is_repo = True
              break
            else:
              subdirs.append(entry.path)
        
        # Si no es un repo, seguimos buscando en subdirectorios
        if not is_repo:
          # Añadimos en orden inverso para mantener el orden de escaneo (opcional)
          stack.extend(reversed(subdirs))
          
    except (PermissionError, OSError):
      continue

  return repos