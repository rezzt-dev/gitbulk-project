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
    show_summary,
    prompt_for_credentials,
    show_auth_success
)
from model import find_git_repos, run_git_operation, setup_global_git_credentials

def main():
  os.system("")
  config = load_config()
  default_dir = config.get("last_directory", os.getcwd())

  args = parse_arguments(default_dir)

  if args.operation == "auth":
    username, token = prompt_for_credentials()
    if setup_global_git_credentials(username, token):
      show_auth_success(username)
    else:
      print(f"\n[ERROR] No se pudieron guardar las credenciales.")
    sys.exit(0)

  target_dir = os.path.abspath(args.dir)
  config["last_directory"] = target_dir
  save_config(config)

  log_file = None
  if args.log:
    log_file = open(args.log, "w", encoding="utf-8")
    log_file.write(f"--- GitBulk Log: Operacion {args.operation.upper()} en {target_dir} ---\n\n")

  try:
    show_welcome(target_dir, args.operation)
    repos = find_git_repos(target_dir)

    if not repos:
      show_no_repos_found(target_dir)
      if log_file: log_file.write("No se encontraron repositorios.\n")
      sys.exit(0)
    
    show_start_processing(len(repos), args.operation)

    counts = {}
    repos_needing_auth = []

    def handle_result(status_code: str, path: str, result_output: str):
       counts[status_code] = counts.get(status_code, 0) + 1
       show_result(status_code, path, result_output)
       if log_file:
         log_file.write(f"[{status_code}] {os.path.basename(path)}\n")
         if result_output and status_code not in ("AUTH", "CLEAN"):
             indented = result_output.replace("\n", "\n    ")
             log_file.write(f"    {indented}\n")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
      future_to_repo = {
        executor.submit(run_git_operation, repo, args.operation, False): repo 
        for repo in repos
      }
    
      for future in as_completed(future_to_repo):
        status, repo_path, output = future.result()

        if status == "AUTH":
          repos_needing_auth.append(repo_path)
          # We don't log the AUTH attempt, we log the final outcome later
          continue

        handle_result(status, repo_path, output)
    
    if repos_needing_auth:
      show_auth_fallback(len(repos_needing_auth))
      for repo_path in repos_needing_auth:
        show_auth_fallback_start(repo_path)
        # Ejecucion secuencial permitiendo prompts interactivos
        status, _, output = run_git_operation(repo_path, args.operation, allow_prompt=True)
        handle_result(status, repo_path, output)

    show_summary(counts)
    if log_file:
        log_file.write(f"\n--- Resumen Final ---\n")
        for key, val in counts.items():
           if val > 0:
              log_file.write(f"{key}: {val}\n")

  finally:
    if log_file:
      log_file.close()


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\n\n operacion cancelada por el usuario.")
    sys.exit(1)