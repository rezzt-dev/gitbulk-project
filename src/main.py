import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Workaround for PyInstaller to explicitly pack dependencies
def _pyinstaller_hooks():
    import rich
    import rich.console
    import rich.progress
    import rich.theme
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
    show_ci_compact,
    show_sync_preview,
    show_interactive_prompt,
    show_git_diff
)
from model import find_git_repos, run_git_operation, setup_global_git_credentials, get_repo_metadata, clone_repo, get_all_branches, get_github_token, get_ci_status, calculate_optimal_workers, ensure_ssh_agent, test_ssh_connectivity, get_groups_topology, archive_repository, open_external_editor

def main():
  # Auto-launch GUI if frozen (PyInstaller) and no arguments
  is_frozen = getattr(sys, 'frozen', False)
  is_gui_mode = "--gui" in sys.argv or (is_frozen and len(sys.argv) == 1)

  if is_gui_mode:
    try:
      import PySide6
    except ImportError:
      if is_frozen:
        print("\n[fatal error] PySide6 core is missing in bundle.")
      else:
        print("\n[error] PySide6 is not installed. please run 'pip install PySide6'")
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

  # ── CLI Mode Only ──────────────────────────────────────────────────────
  # Force ANSI support on Windows and clear terminal
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
      console.print(f"\n[error] failed to save credentials.")
    sys.exit(0)

  target_dir = os.path.abspath(args.dir)
  config["last_directory"] = target_dir
  save_config(config)

  MAX_WORKERS = 50
  requested_workers = getattr(args, 'workers', 0)
  if requested_workers < 0:
      console.print("\n[bold red]error: the number of concurrent threads (-w) must be 0 or greater.[/bold red]")
      sys.exit(1)
  if requested_workers > MAX_WORKERS:
      console.print(f"\n[bold red]error: the number of concurrent threads (-w) cannot exceed {MAX_WORKERS}. received: {requested_workers}.[/bold red]")
      sys.exit(1)

  # Calculate optimal workers based on hardware profiling if requested_workers is 0
  optimal_workers = calculate_optimal_workers(target_dir, requested_workers)
  
  if requested_workers == 0:
      console.print(f"[dim][info] auto-tuning: detected optimal concurrency for this hardware: [bold yellow]{optimal_workers}[/bold yellow] threads.[/dim]")

  # SSH Agent Auto-start
  ssh_success, ssh_msg = ensure_ssh_agent()
  if not ssh_success:
      console.print(f"\n[bold yellow][!] ssh agent advisory:[/bold yellow]\n[dim]{ssh_msg}[/dim]\n")
  elif "started" in ssh_msg:
      console.print(f"[dim][info] {ssh_msg}[/dim]")

  if args.operation == "checkout" and not getattr(args, 'branch', None):
      console.print("\n[bold red]error: the 'checkout' operation requires a target branch via the -b / --branch flag.[/bold red]")
      sys.exit(1)

  if getattr(args, 'autostash', False) and args.operation != "pull":
      console.print(f"\n[bold yellow]warning: --autostash has no effect on '{args.operation}'. it only applies to 'pull'.[/bold yellow]")

  if args.operation == "clean":
      if getattr(args, 'dry_run', False):
          console.print("[bold yellow][dry-run][/bold yellow] previewing 'clean' — no files will be deleted.\n")
      else:
          show_clean_warning()

  log_file = None
  if args.log:
    try:
        log_file = open(args.log, "w", encoding="utf-8")
        log_file.write(f"--- GitBulk log: operation {args.operation} on {target_dir} ---\n\n")
    except OSError as e:
        console.print(f"\n[bold red]fatal error: could not create or open the log file at the specified path:[/bold red]\n{e}")
        sys.exit(1)

  try:
    show_welcome(target_dir, args.operation)

    if args.operation == "workspace":
        if not getattr(args, "action", None):
            console.print("\n[bold red]error: the 'workspace' operation requires an --action (save, load, list, delete).[/bold red]")
            sys.exit(1)

        workspaces = config.get("workspaces", {})

        if args.action == "list":
            if not workspaces:
                console.print("\n[dim]no workspaces saved yet.[/dim]")
            else:
                console.print("\n[bold magenta]saved workspaces:[/bold magenta]")
                for name in workspaces:
                    count = len(workspaces[name])
                    console.print(f"  • [cyan]{name}[/cyan] ({count} repos)")
            sys.exit(0)

        if args.action == "save":
            if not args.name:
                console.print("\n[bold red]error: 'save' action requires a --name.[/bold red]")
                sys.exit(1)
            
            # Scan and possibly filter by group
            raw_repos = find_git_repos(target_dir)
            if not raw_repos:
                show_no_repos_found(target_dir)
                sys.exit(0)

            # Filtering logic
            if getattr(args, "group", None):
                repos = [r["path"] for r in raw_repos if args.group in r["metadata"].get("groups", [])]
                if not repos:
                    console.print(f"\n[bold yellow]no repositories found belonging to group: '{args.group}'[/bold yellow]")
                    sys.exit(0)
            else:
                repos = [r["path"] for r in raw_repos]

            show_start_processing(len(repos), "saving workspace")
            snapshot = []
            
            with Progress(
                SpinnerColumn("dots"),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=False
            ) as progress:
                task = progress.add_task(f"[bold cyan]analizando repos...", total=len(repos))
                with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
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
                        progress.advance(task, 1)
            
            workspaces[args.name] = snapshot
            config["workspaces"] = workspaces
            save_config(config)
            console.print(f"\n[bold green]workspace '{args.name}' saved successfully![/bold green] ({len(snapshot)} repositories)")
            sys.exit(0)

        if args.action == "delete":
            if not args.name:
                console.print("\n[bold red]error: 'delete' action requires a --name.[/bold red]")
                sys.exit(1)
            if args.name in workspaces:
                del workspaces[args.name]
                config["workspaces"] = workspaces
                save_config(config)
                console.print(f"\n[bold green]workspace '{args.name}' deleted.[/bold green]")
            else:
                console.print(f"\n[bold red]workspace '{args.name}' not found.[/bold red]")
            sys.exit(0)

        if args.action == "load":
            if not args.name:
                console.print("\n[bold red]error: 'load' action requires a --name.[/bold red]")
                sys.exit(1)
            if args.name not in workspaces:
                console.print(f"\n[bold red]workspace '{args.name}' not found.[/bold red]")
                sys.exit(1)
            
            snapshot = workspaces[args.name]
            console.print(f"\n[bold cyan]loading workspace:[/bold cyan] {args.name} ({len(snapshot)} repos)\n")
            
            repos_to_clone = []
            for repo in snapshot:
                repo_abs_path = os.path.normpath(os.path.join(target_dir, repo["path"]))
                if not os.path.exists(os.path.join(repo_abs_path, ".git")):
                    repos_to_clone.append((repo_abs_path, repo))
                    
            if not repos_to_clone:
                console.print(f"\n[bold green]all repositories are in sync. no missing repositories found.[/bold green]")
                sys.exit(0)

            show_start_processing(len(repos_to_clone), "loading")
            
            with Progress(
                SpinnerColumn("dots"),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=False
            ) as progress:
              task = progress.add_task(f"[bold cyan]restoring {args.name}...", total=len(repos_to_clone))
              with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
                future_to_repo = {
                   executor.submit(clone_repo, path, info): path
                   for path, info in repos_to_clone
                }
                counts = {'OK': 0, 'CLEAN': 0, 'ERROR': 0}
                for future in as_completed(future_to_repo):
                    status, detail, repo_path, output = future.result()
                    counts[status] = counts.get(status, 0) + 1
                    show_result(status, detail, repo_path, output)
                    progress.advance(task, 1)

            show_summary(counts)
            sys.exit(0)

        if args.action == "sync":
            # 1. Determine local state
            raw_repos = find_git_repos(target_dir)
            
            # 2. Determine target state (from file or workspace name)
            snapshot = []
            if args.name and args.name in workspaces:
                snapshot = workspaces[args.name]
            elif args.file and os.path.exists(args.file):
                with open(args.file, "r", encoding="utf-8") as f:
                    snapshot = json.load(f)
            else:
                console.print(f"\n[bold red]error: 'sync' action requires a valid snapshot file (-f) or workspace name (-n).[/bold red]")
                sys.exit(1)
                
            # Maps for comparison (relative path -> info)
            expected_map = {os.path.normpath(r["path"]): r for r in snapshot}
            local_map = {os.path.normpath(os.path.relpath(r["path"], target_dir)): r["path"] for r in raw_repos}
            
            to_clone = []
            for rel_path, info in expected_map.items():
                if rel_path not in local_map:
                    abs_path = os.path.normpath(os.path.join(target_dir, rel_path))
                    to_clone.append((abs_path, info))
                    
            to_archive = []
            for rel_path, abs_path in local_map.items():
                if rel_path not in expected_map:
                    to_archive.append(abs_path)
                    
            # 3. Preview
            if not show_sync_preview(to_clone, to_archive):
                sys.exit(0)
                
            # 4. Execute Archive
            if to_archive:
                console.print(f"\n[bold yellow]archiving {len(to_archive)} repositories...[/bold yellow]")
                for path in to_archive:
                    ok, detail = archive_repository(path, target_dir)
                    if ok:
                        console.print(f"  [green]Moved[/green] {os.path.basename(path)} -> {detail}")
                    else:
                        console.print(f"  [red]Failed[/red] {os.path.basename(path)}: {detail}")

            # 5. Execute Clone
            if to_clone:
                show_start_processing(len(to_clone), "loading (sync)")
                with Progress(
                    SpinnerColumn("dots"),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=console,
                    transient=False
                ) as progress:
                  task = progress.add_task(f"[bold cyan]restoring missing...", total=len(to_clone))
                  with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
                    futures = {
                       executor.submit(clone_repo, path, info): path
                       for path, info in to_clone
                    }
                    counts = {'OK': 0, 'CLEAN': 0, 'ERROR': 0}
                    for future in as_completed(futures):
                        status, detail, repo_path, output = future.result()
                        counts[status] = counts.get(status, 0) + 1
                        show_result(status, detail, repo_path, output)
                        progress.advance(task, 1)
                show_summary(counts)
                
            console.print("\n[bold green]sync operation complete.[/bold green]")
            sys.exit(0)

    if args.operation == "export":
        raw_repos = find_git_repos(target_dir)
        if not raw_repos:
           show_no_repos_found(target_dir)
           if log_file: log_file.write("No repositories found.\n")
           sys.exit(0)

        # Filtering logic
        if getattr(args, "group", None):
            repos = [r["path"] for r in raw_repos if args.group in r["metadata"].get("groups", [])]
            if not repos:
                console.print(f"\n[bold yellow]No repositories found belonging to group: '{args.group}'[/bold yellow]")
                sys.exit(0)
        else:
            repos = [r["path"] for r in raw_repos]

        show_start_processing(len(repos), args.operation)
        snapshot = []
        counts = {"OK": 0}
        
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
           task = progress.add_task(f"[bold cyan]Analizando repos...", total=len(repos))
           with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
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

        console.print(f"\n[bold green]ok[/bold green] export complete. {len(snapshot)} repositories saved to [cyan]{args.file}[/cyan].\n")
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
            console.print(f"\n[bold green]all repositories are in sync. no missing repositories found.[/bold green]")
            sys.exit(0)

        if getattr(args, 'dry_run', False):
            console.print(f"[bold yellow][dry-run][/bold yellow] the following {len(repos_to_clone)} repositories would be cloned:\n")
            for path, info in repos_to_clone:
                console.print(f"  [cyan]{info.get('path', path)}[/cyan]  [dim]{info.get('url', '')}[/dim]")
            console.print("\n[dim]no changes have been made.[/dim]")
            sys.exit(0)
            
        show_start_processing(len(repos_to_clone), args.operation)
        
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
          task = progress.add_task(f"[bold cyan]Ejecutando {args.operation.upper()}...", total=len(repos_to_clone))
          with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
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
        raw_repos = find_git_repos(target_dir)
        if not raw_repos:
           show_no_repos_found(target_dir)
           if log_file: log_file.write("No se encontraron repositorios.\n")
           sys.exit(0)

        # Filtering logic
        if getattr(args, "group", None):
            repos = [r["path"] for r in raw_repos if args.group in r["metadata"].get("groups", [])]
            if not repos:
                console.print(f"\n[bold yellow]No se encontraron repositorios en el grupo: '{args.group}'[/bold yellow]")
                sys.exit(0)
        else:
            repos = [r["path"] for r in raw_repos]
           
        show_start_processing(len(repos), "Analisis de ramas")
        
        results_queue = []
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
           task = progress.add_task(f"[bold cyan]analizando ramas...", total=len(repos))
           with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
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
            console.print("\n[bold red]error: no GitHub token found.[/bold red]")
            console.print("[yellow]please run 'gitbulk auth' first to save your global credentials (pat).[/yellow]\n")
            sys.exit(1)
            
        raw_repos = find_git_repos(target_dir)
        if not raw_repos:
           show_no_repos_found(target_dir)
           if log_file: log_file.write("No repositorios.\n")
           sys.exit(0)

        # Filtering logic
        if getattr(args, "group", None):
            repos = [r["path"] for r in raw_repos if args.group in r["metadata"].get("groups", [])]
            if not repos:
                console.print(f"\n[bold yellow]No se encontraron repositorios en el grupo: '{args.group}'[/bold yellow]")
                sys.exit(0)
        else:
            repos = [r["path"] for r in raw_repos]
           
        show_start_processing(len(repos), "Consulta de Github Actions")
        
        results_queue = []
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
           task = progress.add_task(f"[bold cyan]analizando pipelines...", total=len(repos))
           kwargs = {
            "autostash": getattr(args, "autostash", False),
            "target_branch": getattr(args, "branch", None),
            "dry_run": getattr(args, "dry_run", False),
            "message": getattr(args, "message", None),
            "body": getattr(args, "body", None)
           }
           with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
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


    if args.operation == "groups":
        show_welcome(target_dir, "Groups Inspector")
        topology = get_groups_topology(target_dir)
        from view import show_groups_summary
        show_groups_summary(topology)
        sys.exit(0)

    # Default operations (fetch, pull, status, clean, checkout)
    raw_repos = find_git_repos(target_dir)
    if not raw_repos:
        show_no_repos_found(target_dir)
        if log_file: log_file.write("No se encontraron repositorios.\n")
        sys.exit(0)

    # Filtering logic
    if getattr(args, "group", None):
        repos = [r["path"] for r in raw_repos if args.group in r["metadata"].get("groups", [])]
        if not repos:
            console.print(f"\n[bold yellow]No se encontraron repositorios en el grupo: '{args.group}'[/bold yellow]")
            sys.exit(0)
    else:
        repos = [r["path"] for r in raw_repos]
    
    show_start_processing(len(repos), args.operation)

    repos_needing_auth = []

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:
      # --- SPECIAL CASE: INTERACTIVE COMMIT ---
      if args.operation == "commit" and getattr(args, "interactive", False):
          progress.stop() # Suspend progress bar for interaction
          for repo_path in repos:
              # 1. Check status first (to skip clean repos)
              status, detail, _, output = run_git_operation(repo_path, "status")
              if status == "OK" and "CLEAN" in detail:
                  continue
              
              action = show_interactive_prompt(repo_path, detail)
              
              if action == 'q':
                  sys.exit(0)
              elif action == 's':
                  break
              elif action == 'n':
                  continue
              elif action == 'd':
                  show_git_diff(repo_path)
                  # Re-prompt after diff
                  action = show_interactive_prompt(repo_path, detail)
                  if action in ['q', 's', 'n']: continue # Handle transition
              
              # Execute commit (either 'y' or 'e')
              msg = getattr(args, 'message', "")
              body = getattr(args, 'body', "")
              
              if action == 'e':
                  content = open_external_editor(f"{msg}\n\n{body}" if msg else "", repo_path)
                  if not content:
                      console.print("[yellow]empty message, skipping commit.[/yellow]")
                      continue
                  # Split first line as title
                  parts = content.split('\n', 1)
                  msg = parts[0].strip()
                  body = parts[1].strip() if len(parts) > 1 else ""
                  
              res_status, res_detail, _, res_output = run_git_operation(
                  repo_path, "commit", message=msg, body=body
              )
              handle_result(res_status, res_detail, repo_path, res_output)
          
          show_summary(counts)
          sys.exit(0)

      # --- DEFAULT PARALLEL LOOP ---
      task = progress.add_task(f"[bold cyan]Ejecutando {args.operation.upper()}...", total=len(repos))
      with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
        future_to_repo = {
          executor.submit(
              run_git_operation,
              repo,
              args.operation,
              False,
              getattr(args, 'autostash', False),
              getattr(args, 'branch', None),
              getattr(args, 'dry_run', False),
              message=getattr(args, 'message', None),
              body=getattr(args, 'body', None)
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
        status, detail, _, output = run_git_operation(
            repo_path, 
            args.operation, 
            allow_prompt=True,
            autostash=getattr(args, 'autostash', False),
            target_branch=getattr(args, 'branch', None),
            dry_run=getattr(args, 'dry_run', False),
            message=getattr(args, 'message', None),
            body=getattr(args, 'body', None)
        )
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
    console.print("\n\noperation cancelled by user.")
    sys.exit(0)
  except Exception as e:
    import traceback
    # Si falla en modo GUI, podemos imprimir pero sin esperar input (el usuario no tiene consola)
    traceback.print_exc()
    sys.exit(1)