import os
from typing import List

def find_git_repos(root_path: str) -> List[str]:
  """
  busca de forma recursiva directorios que contengan una carpeta '.git'.

  args:
    root_path (str): la ruta raiz desde donde empezar a buscar.
  
  returns:
    List[str]: una lista con las rutas absolutas de los repositorios encontrados.
  """

  repos = []

  if not os.path.exists(root_path):
    return repos
  
  for root_dir, dirs, files in os.walk(root_path):
    git_dir = os.path.join(root_dir, ".git")

    if os.path.isdir(git_dir):
      repos.append(root_dir)
      dirs[:] = []
  
  return repos