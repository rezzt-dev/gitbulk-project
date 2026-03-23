import subprocess
import os
import re
from typing import Tuple

def run_git_operation(repo_path: str, operation: str, allow_prompt: bool = False, autostash: bool = False) -> Tuple[str, str, str, str]:
  cmd = ["git", operation]

  if operation == "pull":
    cmd = ["git", "pull", "--ff-only"]
    if autostash:
      cmd.append("--autostash")
  elif operation == "status":
    cmd = ["git", "status", "--short", "--branch"]

  env = os.environ.copy()
  if not allow_prompt:
    # deshabilitar prompts interactivos de git para evitar bloqueos
    env["GIT_TERMINAL_PROMPT"] = "0"

  try:
    result = subprocess.run(
      cmd,
      cwd = repo_path,
      env = env,
      text = True,
      capture_output = True,
      check = True
    )
    
    output = result.stdout.strip()
    
    if operation == "status":
      lines = output.split("\n") if output else []
      if len(lines) > 1:
          # Hay archivos modificados o untracked
          modified_count = len([line for line in lines[1:] if line.strip()])
          return "MODIFIED", str(modified_count), repo_path, ""
      else:
          branch_info = lines[0] if lines else ""
          ahead, behind = 0, 0
          
          match = re.search(r'\[(.*?)\]', branch_info)
          if match:
              details = match.group(1)
              m_ahead = re.search(r'ahead (\d+)', details)
              if m_ahead: ahead = int(m_ahead.group(1))
              m_behind = re.search(r'behind (\d+)', details)
              if m_behind: behind = int(m_behind.group(1))

          if ahead > 0:
              return "AHEAD", str(ahead), repo_path, branch_info
          elif behind > 0:
              return "BEHIND", str(behind), repo_path, branch_info
          else:
              return "CLEAN", "", repo_path, ""
              
    if operation == "fetch":
        status_res = subprocess.run(["git", "status", "--short", "--branch"], cwd=repo_path, env=env, capture_output=True, text=True)
        if status_res.returncode == 0:
            lines = status_res.stdout.strip().split("\n")
            branch_info = lines[0] if lines else ""
            
            match = re.search(r'\[(.*?)\]', branch_info)
            if match:
                details = match.group(1)
                m_behind = re.search(r'behind (\d+)', details)
                if m_behind:
                    behind = int(m_behind.group(1))
                    return "FETCH_UPDATE", f"{behind} commits por bajar", repo_path, output
        return "OK", "Al día", repo_path, output
              
    return "OK", "", repo_path, output

  except subprocess.CalledProcessError as e:
    error_msg = e.stderr.strip() if e.stderr else str(e)
    # Check if the error is due to disabled terminal prompts
    if not allow_prompt and ("could not read Username" in error_msg or "terminal prompts disabled" in error_msg or "Authentication failed" in error_msg):
        return "AUTH", "", repo_path, error_msg

    if operation == "pull":
        if "overwritten by merge" in error_msg or "Please commit your changes or stash them" in error_msg:
            return "CONFLICT", "Cambios locales", repo_path, error_msg
        if "Not possible to fast-forward" in error_msg or "divergent branches" in error_msg or "Need to specify how to reconcile" in error_msg:
            return "DIVERGENT", "Requiere merge manual", repo_path, error_msg

    return "ERROR", "", repo_path, error_msg

def get_repo_metadata(repo_path: str) -> dict:
  """Extrae la URL remota y la rama actual de un repositorio."""
  metadata = {"url": "", "branch": ""}
  
  try:
    url_res = subprocess.run(["git", "remote", "get-url", "origin"], cwd=repo_path, capture_output=True, text=True, check=True)
    metadata["url"] = url_res.stdout.strip()
  except subprocess.CalledProcessError:
    pass

  try:
    branch_res = subprocess.run(["git", "branch", "--show-current"], cwd=repo_path, capture_output=True, text=True, check=True)
    metadata["branch"] = branch_res.stdout.strip()
  except subprocess.CalledProcessError:
    pass
    
  return metadata

def clone_repo(target_dir: str, repo_info: dict) -> Tuple[str, str, str, str]:
  """Clona un repositorio en target_dir y hace checkout a la rama especificada."""
  url = repo_info.get("url")
  branch = repo_info.get("branch")
  
  if not url:
    return "ERROR", "Falta URL remota", target_dir, ""
    
  try:
    parent_dir = os.path.dirname(target_dir)
    if not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except OSError:
            pass # fallback to letting git clone fail natively

    clone_res = subprocess.run(["git", "clone", url, target_dir], capture_output=True, text=True, check=True)
    
    if branch:
      subprocess.run(["git", "checkout", branch], cwd=target_dir, capture_output=True, text=True, check=True)
      
    return "OK", branch, target_dir, clone_res.stdout.strip()
  except subprocess.CalledProcessError as e:
    error_msg = e.stderr.strip() if e.stderr else str(e)
    if "already exists" in error_msg:
        return "CLEAN", "Ya existe", target_dir, ""
    return "ERROR", "", target_dir, error_msg

def get_all_branches(repo_path: str) -> dict:
  """
  Retorna todas las ramas de un repositorio separadas en activa, locales y solo remotas.
  """
  data = {
    "current": "",
    "local": [],
    "remote_only": []
  }
  
  try:
    res = subprocess.run(["git", "branch", "-a"], cwd=repo_path, capture_output=True, text=True, check=True)
    lines = res.stdout.strip().split("\n")
    
    local_branches = set()
    remote_branches = set()
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith("* "):
            branch_name = line[2:].strip()
            if branch_name.startswith("(HEAD detached at"):
                branch_name = branch_name.replace("(HEAD detached at ", "").rstrip(")")
            data["current"] = branch_name
            local_branches.add(branch_name)
        elif line.startswith("remotes/"):
            if "->" in line: continue
            branch_name = line.replace("remotes/", "", 1).strip()
            remote_branches.add(branch_name)
        else:
            branch_name = line.strip()
            local_branches.add(branch_name)
            data["local"].append(branch_name)
            
    for rb in remote_branches:
        short_name = rb.split("/", 1)[-1] if "/" in rb else rb
        if short_name not in local_branches:
            data["remote_only"].append(rb)

  except subprocess.CalledProcessError:
    pass
    
  return data