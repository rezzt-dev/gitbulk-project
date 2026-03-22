import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

 # importamos nuestras capas limpiamente a traves de __init__.py
from persistence import load_config, save_config
from view import (
    parse_arguments,
    show_welcome,
    show_no_repos_found,
    show_start_processing,
    show_result,
    show_auth_fallback,
    show_auth_fallback_start,
    show_summary
)
from model import find_git_repos, run_git_operation

def main():
  os.system("")
  config = load_config()
  default_dir = config.get("last_directory", os.getcwd())

  args = parse_arguments(default_dir)
  target_dir = os.path.abspath(args.dir)
  config["last_directory"] = target_dir
  save_config(config)
  show_welcome(target_dir, args.operation)
  repos = find_git_repos(target_dir)

  if not repos:
    show_no_repos_found(target_dir)
    sys.exit(0)
  
  show_start_processing(len(repos), args.operation)

  successes = 0
  errors = 0
  repos_needing_auth = []

  with ThreadPoolExecutor(max_workers=args.workers) as executor:
    future_to_repo = {
      executor.submit(run_git_operation, repo, args.operation, False): repo 
      for repo in repos
    }
  
    for future in as_completed(future_to_repo):
      status, repo_path, output = future.result()

      if status == "OK":
        successes += 1
      elif status == "AUTH":
        repos_needing_auth.append(repo_path)
      else:
        errors += 1
      
      show_result(status, repo_path, output)
  
  if repos_needing_auth:
    show_auth_fallback(len(repos_needing_auth))
    for repo_path in repos_needing_auth:
      show_auth_fallback_start(repo_path)
      # Ejecucion secuencial permitiendo prompts interactivos
      status, _, output = run_git_operation(repo_path, args.operation, allow_prompt=True)
      if status == "OK":
        successes += 1
      else:
        errors += 1
      show_result(status, repo_path, output)

  show_summary(successes, errors)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\n\n operacion cancelada por el usuario.")
    sys.exit(1)