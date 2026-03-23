import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

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
    show_auth_success,
    console
)
from model import find_git_repos, run_git_operation, setup_global_git_credentials, get_repo_metadata, clone_repo, get_all_branches
from view import show_branches_compact

def main():
  os.system("")
  os.system("cls" if os.name == "nt" else "clear")
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

    if args.operation == "export":
        repos = find_git_repos(target_dir)
        if not repos:
           show_no_repos_found(target_dir)
           if log_file: log_file.write("No se encontraron repositorios.\n")
           sys.exit(0)
           
        show_start_processing(len(repos), args.operation)
        snapshot = []
        counts = {"OK": 0}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
           task = progress.add_task(f"[bold cyan]Analizando repos...", total=len(repos))
           with ThreadPoolExecutor(max_workers=args.workers) as executor:
               future_to_repo = {
                   executor.submit(get_repo_metadata, repo): repo for repo in repos
               }
               for future in as_completed(future_to_repo):
                   repo_path = future_to_repo[future]
                   metadata = future.result()
                   rel_path = os.path.relpath(repo_path, target_dir)
                   
                   snapshot.append({
                       "path": rel_path,
                       "url": metadata["url"],
                       "branch": metadata["branch"]
                   })
                   counts["OK"] += 1
                   progress.advance(task, 1)

        with open(args.file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=4)
            
        console.print(f"\n[bold green]OK[/bold green] Exportacion completada. {len(snapshot)} repositorios guardados en [cyan]{args.file}[/cyan].\n")
        show_summary(counts)
        sys.exit(0)

    counts = {}

    def handle_result(status_code: str, detail: str, path: str, result_output: str):
       counts[status_code] = counts.get(status_code, 0) + 1
       show_result(status_code, detail, path, result_output)
       if log_file:
         detail_str = f" {detail}" if detail else ""
         log_file.write(f"[{status_code}{detail_str}] {os.path.basename(path)}\n")
         if result_output and status_code not in ("AUTH", "CLEAN"):
             indented = result_output.replace("\n", "\n    ")
             log_file.write(f"    {indented}\n")

    if args.operation == "restore":
        if not os.path.exists(args.file):
            console.print(f"[bold red]El archivo {args.file} no existe.[/bold red]")
            sys.exit(1)
            
        with open(args.file, "r", encoding="utf-8") as f:
            try:
                snapshot = json.load(f)
            except json.JSONDecodeError:
                console.print(f"[bold red]El archivo {args.file} no es un JSON valido.[/bold red]")
                sys.exit(1)
                
        repos_to_clone = []
        for repo in snapshot:
            repo_abs_path = os.path.normpath(os.path.join(target_dir, repo["path"]))
            if not os.path.exists(os.path.join(repo_abs_path, ".git")):
                repos_to_clone.append((repo_abs_path, repo))
                
        if not repos_to_clone:
            console.print(f"\n[bold green]Todo esta sincronizado. Ningun repositorio faltante en la ruta especificada.[/bold green]")
            sys.exit(0)
            
        show_start_processing(len(repos_to_clone), args.operation)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
          task = progress.add_task(f"[bold cyan]Ejecutando {args.operation.upper()}...", total=len(repos_to_clone))
          with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_repo = {
               executor.submit(clone_repo, path, info): path
               for path, info in repos_to_clone
            }
            for future in as_completed(future_to_repo):
                status, detail, repo_path, output = future.result()
                handle_result(status, detail, repo_path, output)
                progress.advance(task, 1)
                
        show_summary(counts)
        sys.exit(0)

    if args.operation == "current-branch":
        repos = find_git_repos(target_dir)
        if not repos:
           show_no_repos_found(target_dir)
           if log_file: log_file.write("No se encontraron repositorios.\n")
           sys.exit(0)
           
        show_start_processing(len(repos), "Analisis de ramas")
        
        results_queue = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
           task = progress.add_task(f"[bold cyan]Analizando ramas...", total=len(repos))
           with ThreadPoolExecutor(max_workers=args.workers) as executor:
               future_to_repo = {
                   executor.submit(get_all_branches, repo): repo for repo in repos
               }
               for future in as_completed(future_to_repo):
                   repo_path = future_to_repo[future]
                   branches_data = future.result()
                   repo_name = os.path.basename(repo_path)
                   results_queue.append((repo_name, branches_data))
                   progress.advance(task, 1)

        console.print("\n")
        results_queue.sort(key=lambda x: x[0].lower())
        show_branches_compact(results_queue)
        
        sys.exit(0)

    repos = find_git_repos(target_dir)

    if not repos:
      show_no_repos_found(target_dir)
      if log_file: log_file.write("No se encontraron repositorios.\n")
      sys.exit(0)
    
    show_start_processing(len(repos), args.operation)

    repos_needing_auth = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:
      task = progress.add_task(f"[bold cyan]Ejecutando {args.operation.upper()}...", total=len(repos))
      with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_repo = {
          executor.submit(run_git_operation, repo, args.operation, False, getattr(args, 'autostash', False)): repo 
          for repo in repos
        }
      
        for future in as_completed(future_to_repo):
          status, detail, repo_path, output = future.result()

          if status == "AUTH":
            repos_needing_auth.append(repo_path)
            # We don't log the AUTH attempt, we log the final outcome later
            progress.advance(task, 1)
            continue

          handle_result(status, detail, repo_path, output)
          progress.advance(task, 1)
    
    if repos_needing_auth:
      show_auth_fallback(len(repos_needing_auth))
      for repo_path in repos_needing_auth:
        show_auth_fallback_start(repo_path)
        # Ejecucion secuencial permitiendo prompts interactivos
        status, detail, _, output = run_git_operation(repo_path, args.operation, allow_prompt=True)
        handle_result(status, detail, repo_path, output)

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