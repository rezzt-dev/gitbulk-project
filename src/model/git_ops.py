import subprocess
import os
from typing import Tuple

def run_git_operation(repo_path: str, operation: str, allow_prompt: bool = False) -> Tuple[str, str, str]:
  cmd = ["git", operation]

  if operation == "pull":
    cmd = ["git", "pull", "--ff-only"]

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
    return "OK", repo_path, result.stdout.strip()

  except subprocess.CalledProcessError as e:
    error_msg = e.stderr.strip() if e.stderr else str(e)
    # Check if the error is due to disabled terminal prompts
    if not allow_prompt and ("could not read Username" in error_msg or "terminal prompts disabled" in error_msg or "Authentication failed" in error_msg):
        return "AUTH", repo_path, error_msg

    return "ERROR", repo_path, error_msg