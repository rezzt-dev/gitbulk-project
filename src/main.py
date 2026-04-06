import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Workaround for PyInstaller to explicitly pack dependencies (without try/except)
def _pyinstaller_hooks():
    import rich
    import rich.console
    import rich.progress
    import rich.theme
    import git
    import git.exc
    import persistence
    import view
    import model

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
    show_clean_warning,
    show_summary,
    prompt_for_credentials,
    show_auth_success,
    console,
    show_branches_compact,
    show_ci_compact
)
from model import find_git_repos, run_git_operation, setup_global_git_credentials, get_repo_metadata, clone_repo, get_all_branches, get_github_token, get_ci_status

def main():
  # Auto-launch GUI if frozen (PyInstaller) and no arguments
  is_frozen = getattr(sys, 'frozen', False)
  is_gui_mode = "--gui" in sys.argv or (is_frozen and len(sys.argv) == 1)

  if is_gui_mode:
    try:
      import PySide6
    except ImportError:
      if is_frozen:
        print("\n[FATAL ERROR] PySide6 core is missing in bundle.")
      else:
        print("\n[ERROR] PySide6 is not installed. Please run 'pip install PySide6'")
      sys.exit(1)
    
    if "--gui" in sys.argv:
        sys.argv.remove("--gui")
    
    try:
        from gui.app import run_gui
    except ImportError:
        # Fallback for some bundle configurations
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'gui')))
        from app import run_gui
    
    sys.exit(run_gui())

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
      console.print(f"\n[ERROR] Failed to save credentials.")
    sys.exit(0)

  target_dir = os.path.abspath(args.dir)
  config["last_directory"] = target_dir
  save_config(config)

  MAX_WORKERS = 50
  if getattr(args, 'workers', 5) <= 0:
      console.print("\n[bold red]Error: The number of concurrent threads (-w) must be greater than 0.[/bold red]")
      sys.exit(1)
  if getattr(args, 'workers', 5) > MAX_WORKERS:
      console.print(f"\n[bold red]Error: The number of concurrent threads (-w) cannot exceed {MAX_WORKERS}. Received: {args.workers}.[/bold red]")
      sys.exit(1)

  if args.operation == "checkout" and not getattr(args, 'branch', None):
      console.print("\n[bold red]Error: The 'checkout' operation requires a target branch via the -b / --branch flag.[/bold red]")
      sys.exit(1)

  if getattr(args, 'autostash', False) and args.operation != "pull":
      console.print(f"\n[bold yellow]Warning: --autostash has no effect on '{args.operation}'. It only applies to 'pull'.[/bold yellow]")

  if args.operation == "clean":
      if getattr(args, 'dry_run', False):
          console.print("[bold yellow][DRY-RUN][/bold yellow] Previewing 'clean' — no files will be deleted.\n")
      else:
          show_clean_warning()

  log_file = None
  if args.log:
    try:
        log_file = open(args.log, "w", encoding="utf-8")
        log_file.write(f"--- GitBulk Log: Operation {args.operation.upper()} on {target_dir} ---\n\n")
    except OSError as e:
        console.print(f"\n[bold red]Fatal Error: Could not create or open the log file at the specified path:[/bold red]\n{e}")
        sys.exit(1)

  try:
    show_welcome(target_dir, args.operation)

    if args.operation == "export":
        repos = find_git_repos(target_dir)
        if not repos:
           show_no_repos_found(target_dir)
           if log_file: log_file.write("No repositories found.\n")
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

        try:
            with open(args.file, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=4)
        except OSError as e:
            console.print(f"\n[bold red]Fatal Error: Cannot write snapshot to the specified export path:[/bold red]\n{e}")
            sys.exit(1)

        console.print(f"\n[bold green]OK[/bold green] Export complete. {len(snapshot)} repositories saved to [cyan]{args.file}[/cyan].\n")
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
            console.print(f"[bold red]File {args.file} does not exist.[/bold red]")
            sys.exit(1)

        with open(args.file, "r", encoding="utf-8") as f:
            try:
                snapshot = json.load(f)
            except json.JSONDecodeError:
                console.print(f"[bold red]File {args.file} is not valid JSON or is corrupted.[/bold red]")
                sys.exit(1)
            except OSError as e:
                console.print(f"[bold red]OS error reading JSON:[/bold red] {e}")
                sys.exit(1)
                
        repos_to_clone = []
        for repo in snapshot:
            repo_abs_path = os.path.normpath(os.path.join(target_dir, repo["path"]))
            if not os.path.exists(os.path.join(repo_abs_path, ".git")):
                repos_to_clone.append((repo_abs_path, repo))
                
        if not repos_to_clone:
            console.print(f"\n[bold green]All repositories are in sync. No missing repositories found.[/bold green]")
            sys.exit(0)

        if getattr(args, 'dry_run', False):
            console.print(f"[bold yellow][DRY-RUN][/bold yellow] The following {len(repos_to_clone)} repositories would be cloned:\n")
            for path, info in repos_to_clone:
                console.print(f"  [cyan]{info.get('path', path)}[/cyan]  [dim]{info.get('url', '')}[/dim]")
            console.print("\n[dim]No changes have been made.[/dim]")
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

    if args.operation == "ci-status":
        token = get_github_token()
        if not token:
            console.print("\n[bold red]Error: No GitHub token found.[/bold red]")
            console.print("[yellow]Please run 'gitbulk auth' first to save your global credentials (PAT).[/yellow]\n")
            sys.exit(1)
            
        repos = find_git_repos(target_dir)
        if not repos:
           show_no_repos_found(target_dir)
           if log_file: log_file.write("No repositorios.\n")
           sys.exit(0)
           
        show_start_processing(len(repos), "Consulta de Github Actions")
        
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
           task = progress.add_task(f"[bold cyan]Analizando pipelines...", total=len(repos))
           with ThreadPoolExecutor(max_workers=args.workers) as executor:
               future_to_repo = {
                   executor.submit(get_ci_status, repo, token): repo for repo in repos
               }
               for future in as_completed(future_to_repo):
                   repo_path = future_to_repo[future]
                   ci_data = future.result()
                   repo_name = os.path.basename(repo_path)
                   results_queue.append((repo_name, ci_data))
                   progress.advance(task, 1)

        console.print("\n")
        results_queue.sort(key=lambda x: x[0].lower())
        show_ci_compact(results_queue)
        
        sys.exit(0)


    repos = find_git_repos(target_dir)

    if not repos:
      show_no_repos_found(target_dir)
      if log_file: log_file.write("No repositories found.\n")
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
          executor.submit(
              run_git_operation,
              repo,
              args.operation,
              False,
              getattr(args, 'autostash', False),
              getattr(args, 'branch', None),
              getattr(args, 'dry_run', False)
          ): repo 
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
        log_file.write(f"\n--- Final Summary ---\n")
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
    console.print("\n\nOperation cancelled by user.")
    sys.exit(0)
  except Exception as e:
    import traceback
    # Si falla en modo GUI, podemos imprimir pero sin esperar input (el usuario no tiene consola)
    traceback.print_exc()
    sys.exit(1)