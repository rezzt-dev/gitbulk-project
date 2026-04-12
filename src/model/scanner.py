import os
import json
from typing import List, Dict

def find_git_repos(root_path: str) -> List[Dict]:
    """
    Busca de forma recursiva directorios que contengan una carpeta '.git'.
    Retorna una lista de diccionarios con la ruta y metadatos del repositorio.
    Prioriza el rendimiento usando os.scandir de forma iterativa.
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
                            # Encontrado un repositorio Git.
                            # Ahora buscamos el archivo opcional de metadatos locales.
                            metadata = {"groups": []}
                            meta_file = os.path.join(current_dir, ".gitbulk.repo.json")
                            if os.path.exists(meta_file):
                                try:
                                    with open(meta_file, "r", encoding="utf-8") as f:
                                        raw_meta = json.load(f)
                                        if isinstance(raw_meta, dict):
                                            # Extraemos solo los campos conocidos para evitar basura
                                            metadata["groups"] = raw_meta.get("groups", [])
                                            # Podríamos añadir name_override u otros en el futuro
                                except Exception:
                                    # Si el JSON está mal, simplemente ignoramos los metadatos
                                    pass
                            
                            repos.append({
                                "path": current_dir,
                                "metadata": metadata
                            })
                            is_repo = True
                            break
                        elif entry.name == ".gitbulk_archive":
                            continue # Skip the archive folder
                        else:
                            subdirs.append(entry.path)
                
                # Si no es un repo, seguimos buscando en subdirectorios
                if not is_repo:
                    stack.extend(reversed(subdirs))
                    
        except (PermissionError, OSError):
            continue

    return repos

def get_groups_topology(root_path: str) -> Dict[str, List[Dict]]:
    """
    Scans the directory and returns a mapping of group names to 
    lists of repository information dictionaries.
    """
    raw_repos = find_git_repos(root_path)
    topology = {}
    
    for repo in raw_repos:
        groups = repo["metadata"].get("groups", [])
        if not groups:
            if "Uncategorized" not in topology:
                topology["Uncategorized"] = []
            topology["Uncategorized"].append(repo)
        else:
            for g in groups:
                if g not in topology:
                    topology[g] = []
                topology[g].append(repo)
                
    return topology