import subprocess
from typing import Tuple

def run_git_operation(repo_path: str, operation: str) -> Tuple[bool, str, str]:
  cmd = ["git", operation]

  if operation == "pull":
    cmd = ["git", "pull", "--ff-only"]

  try:
    result = subprocess.run(
      cmd,
      cwd = repo_path,
      text = True,
      capture_output = True,
      check = True
    )
    return True, repo_path, result.stdout.strip()

  except subprocess.CalledProcessError as e:
    error_msg = e.stderr.strip() if e.stderr else str(e)
    return False, repo_path, error_msg