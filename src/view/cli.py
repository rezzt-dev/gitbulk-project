"""
src/view/cli.py

View layer: argument parsing and all terminal output using the rich library.
"""

import argparse
import os
import getpass
from typing import Tuple
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.tree import Tree

console = Console()

def parse_arguments(default_dir: str) -> argparse.Namespace:
  """
  Configures and parses command-line arguments.

  Args:
    default_dir (str): The default directory retrieved from persistent storage.

  Returns:
    argparse.Namespace: Object containing all parsed arguments.
  """

  parser = argparse.ArgumentParser(
    description = (
        "GitBulk: Run bulk Git commands across multiple repositories concurrently.\n\n"
        "Available commands:\n"
        "  fetch          : Download remote history without merging (git fetch).\n"
        "  pull           : Update the current branch from remote (git pull --ff-only).\n"
        "  auth           : Configure your global GitHub credentials (PAT).\n"
        "  status         : Show working tree state (modified, ahead/behind).\n"
        "  export         : Export repository list and origins to a JSON file.\n"
        "  restore        : Bulk-clone missing repositories from an export JSON file.\n"
        "  current-branch : Display an ultra-compact topology of local and remote branches.\n"
        "  clean          : [Destructive] Remove dead remote branches and untracked files.\n"
        "  checkout       : Iteratively move HEAD to a target branch (-b target_branch).\n"
        "  ci-status      : Query GitHub Actions pipeline status using your configured PAT."
    ),
    formatter_class=argparse.RawTextHelpFormatter
  )

  parser.add_argument(
    "operation",
    choices = ["fetch", "pull", "auth", "status", "export", "restore", "current-branch", "clean", "checkout", "ci-status"],
    help = "The primary Git operation to iterate across the active workspace."
  )

  parser.add_argument(
    "-d", "--dir",
    default=default_dir,
    help = f"root directory to scan (default: {default_dir if default_dir else 'current directory'})"
  )

  parser.add_argument(
    "-w", "--workers",
    type = int,
    default = 5,
    help = "number of concurrent threads for increased speed (default: 5)."
  )

  parser.add_argument(
    "-l", "--log",
    type = str,
    help = "optional file path to save execution results."
  )

  parser.add_argument(
    "--autostash",
    action = "store_true",
    help = "use git stash pre/post pull to avoid conflicts from locally modified files."
  )

  parser.add_argument(
    "-f", "--file",
    type = str,
    default = "snapshot.json",
    help = "JSON file to save/load the repository list."
  )

  parser.add_argument(
    "-b", "--branch",
    type = str,
    help = "target branch name (REQUIRED for the 'checkout' operation)."
  )

  parser.add_argument(
    "--dry-run",
    action = "store_true",
    dest = "dry_run",
    help = (
        "preview the actions that would be taken without applying any changes.\n"
        "Supported operations: 'clean' (shows what would be deleted), 'restore' (shows what would be cloned)."
    )
  )

  return parser.parse_args()

def prompt_for_credentials() -> Tuple[str, str]:
  """Securely prompts the user for their GitHub credentials."""
  console.print(f"\n[bold cyan]--- GitHub Credentials Setup ---[/bold cyan]")
  console.print(f"[bold yellow]Note: Using a Personal Access Token (PAT) is strongly recommended over a password.[/bold yellow]")
  username = input("GitHub username: ")
  token = getpass.getpass("Password or Token: ")
  return username, token

def show_auth_success(username: str) -> None:
  console.print(f"\n[bold green]OK[/bold green] Credentials for [cyan]{username}[/cyan] saved globally.")

def show_welcome(root_dir: str, operation: str) -> None:
  """Displays the startup banner."""
  welcome_msg = f"[bold cyan]Root directory:[/bold cyan] {root_dir}\n[bold cyan]Operation:[/bold cyan] [bold white]{operation.upper()}[/bold white]"
  console.print(Panel(welcome_msg, title="[bold cyan]GitBulk[/bold cyan]", border_style="blue", expand=False))

def show_no_repos_found(root_dir: str) -> None:
  """Displays a message when no Git repositories are found."""
  console.print(f"[bold red]No Git repositories found in {root_dir}[/bold red]")

def show_start_processing(count: int, operation: str) -> None:
  """Displays how many repositories will be processed."""
  console.print(f"\n[dim]Found [bold yellow]{count}[/bold yellow] Git repositories. Running '{operation}' in parallel...[/dim]\n")

def show_result(status: str, detail: str, repo_path: str, output: str) -> None:
  """Displays the individual result for a single repository."""
  repo_name = os.path.basename(repo_path)
  detail_str = f" [dim]({detail})[/dim]" if detail else ""

  if status == "OK":
    console.print(f"[bold green][OK][/bold green] [cyan]{repo_name}[/cyan]")
  elif status == "CLEAN":
    console.print(f"[bold green][CLEAN][/bold green] [cyan]{repo_name}[/cyan]")
  elif status == "MODIFIED":
    console.print(f"[bold yellow][MODIFIED][/bold yellow]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "AHEAD":
    console.print(f"[bold green][AHEAD][/bold green]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "BEHIND":
    console.print(f"[bold yellow][BEHIND][/bold yellow]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "CONFLICT":
    console.print(f"[bold yellow][CONFLICT][/bold yellow]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "DIVERGENT":
    console.print(f"[bold red][DIVERGENT][/bold red]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "FETCH_UPDATE":
    console.print(f"[bold blue][UPDATES][/bold blue]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "STASH_RESTORED":
    console.print(f"[bold blue][SYNC+STASH][/bold blue]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "STASH_CONFLICT":
    console.print(f"[bold yellow][STASH CONFLICT][/bold yellow]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "CLEANED":
    console.print(f"[bold magenta][CLEANED][/bold magenta]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "SIMULATED":
    console.print(f"[bold green][DRY-RUN][/bold green]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "CHECKOUT":
    console.print(f"[bold cyan][CHECKOUT][/bold cyan]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "IGNORED":
    console.print(f"[dim white][IGNORED][/dim white]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "AUTH":
    console.print(f"[bold yellow][AUTH][/bold yellow] [cyan]{repo_name}[/cyan] [dim](Credentials required)[/dim]")
  else:
    console.print(f"[bold red][ERROR][/bold red] [cyan]{repo_name}[/cyan]")

  if output and status not in ("AUTH", "CLEAN"):
    indented_output = output.replace("\n", "\n    ")
    console.print(f"    [dim]{indented_output}[/dim]")

def show_auth_fallback(count: int) -> None:
  """Informs the user that some repositories require credentials and will be processed sequentially."""
  console.print(f"\n[bold yellow]{count}[/bold yellow] repositories require credentials.")
  console.print("[dim]Processing sequentially to allow manual credential input...[/dim]\n")

def show_auth_fallback_start(repo_path: str) -> None:
  repo_name = os.path.basename(repo_path)
  console.print(f"[bold cyan]Authenticating {repo_name} ...[/bold cyan]")

def show_clean_warning() -> bool:
  """
  Displays the destructive operation warning panel and asks for interactive confirmation.

  Returns:
    True if the user explicitly confirms, False if they decline.
    Exits the process (sys.exit(0)) on KeyboardInterrupt or EOFError (non-interactive environments).
  """
  import sys
  console.print(Panel(
      "[bold]ALL[/bold] dead remote branch references and untracked local files "
      "will be [bold]PERMANENTLY DELETED[/bold].\n"
      "This operation runs 'git fetch --prune' and 'git clean -xfd'.\n"
      "Make sure you have no unsaved local configurations or .env files.",
      title="[bold red]SECURITY WARNING[/bold red]",
      border_style="red"
  ))
  try:
      confirmed = Confirm.ask(
          "[bold yellow]Are you ABSOLUTELY sure you want to proceed on ALL repositories?[/bold yellow]"
      )
      if not confirmed:
          console.print("[dim]Bulk 'clean' operation cancelled. Everything is safe.[/dim]")
          sys.exit(0)
      return True
  except (KeyboardInterrupt, EOFError):
      console.print("\n[dim]Security prompt abruptly cancelled.[/dim]")
      sys.exit(0)

def show_summary(counts: dict) -> None:
  """Displays the final execution summary table."""
  table = Table(title="[bold magenta]Execution Summary[/bold magenta]", show_header=True, header_style="bold magenta")
  table.add_column("Status", style="dim")
  table.add_column("Count", justify="right")

  if counts.get('OK', 0) > 0:            table.add_row("[bold green]Success[/bold green]",             str(counts['OK']))
  if counts.get('CLEAN', 0) > 0:         table.add_row("[bold green]Up to date[/bold green]",          str(counts['CLEAN']))
  if counts.get('MODIFIED', 0) > 0:      table.add_row("[bold yellow]Modified[/bold yellow]",           str(counts['MODIFIED']))
  if counts.get('AHEAD', 0) > 0:         table.add_row("[bold green]Ahead[/bold green]",                str(counts['AHEAD']))
  if counts.get('BEHIND', 0) > 0:        table.add_row("[bold yellow]Behind[/bold yellow]",             str(counts['BEHIND']))
  if counts.get('FETCH_UPDATE', 0) > 0:  table.add_row("[bold blue]Pending Pull[/bold blue]",           str(counts['FETCH_UPDATE']))
  if counts.get('STASH_RESTORED', 0) > 0:table.add_row("[bold blue]Synced (Autostash)[/bold blue]",    str(counts['STASH_RESTORED']))
  if counts.get('CLEANED', 0) > 0:       table.add_row("[bold magenta]Cleaned / Pruned[/bold magenta]", str(counts['CLEANED']))
  if counts.get('CHECKOUT', 0) > 0:      table.add_row("[bold cyan]Checked Out[/bold cyan]",            str(counts['CHECKOUT']))
  if counts.get('IGNORED', 0) > 0:       table.add_row("[dim white]Ignored[/dim white]",                str(counts['IGNORED']))
  if counts.get('CONFLICT', 0) > 0:      table.add_row("[bold yellow]Local Conflicts[/bold yellow]",    str(counts['CONFLICT']))
  if counts.get('STASH_CONFLICT', 0) > 0:table.add_row("[bold yellow]Autostash Conflicts[/bold yellow]",str(counts['STASH_CONFLICT']))
  if counts.get('DIVERGENT', 0) > 0:     table.add_row("[bold red]Require Merge[/bold red]",            str(counts['DIVERGENT']))
  if counts.get('ERROR', 0) > 0:         table.add_row("[bold red]Errors[/bold red]",                   str(counts['ERROR']))

  console.print("\n")
  console.print(table)

def show_branches_compact(results: list) -> None:
  """Displays an ultra-compact one-line-per-repository branch topology view."""
  console.print("\n[bold magenta]Branch Topology[/bold magenta]")

  if not results: return

  max_len = max(len(repo_name) for repo_name, _ in results)

  for repo_name, branches_data in results:
      error = branches_data.get("error", "")
      if error:
          console.print(f"[bold red][ERROR][/bold red] [cyan]{repo_name}[/cyan]   [dim]{error}[/dim]")
          continue

      active = branches_data.get("current") or "N/A"
      local = branches_data.get("local", [])
      remote = branches_data.get("remote_only", [])

      line = f"[bold cyan]{repo_name.ljust(max_len)}[/bold cyan]   [bold green]({active})[/bold green]"

      extras = []
      if local:
          extras.append(f"[cyan]L: {', '.join(local)}[/cyan]")
      if remote:
          extras.append(f"[dim yellow]R: {', '.join(remote)}[/dim yellow]")

      if extras:
          line += "   " + "   ".join(extras)

      console.print(line)

def show_ci_compact(results: list) -> None:
  """Displays a compact view of CI pipeline statuses."""
  console.print("\n[bold magenta]Continuous Integration Status (GitHub Actions)[/bold magenta]")
  if not results: return

  table = Table(show_header=True, header_style="bold magenta", box=None)
  table.add_column("Status", justify="center")
  table.add_column("Repository", style="cyan")
  table.add_column("Active Branch", style="dim")
  table.add_column("Detail", style="dim red")

  for repo_name, ci_data in results:
      state = ci_data.get("state", "none")
      branch = ci_data.get("branch", "N/A")

      if state == "success":   st_text = "[bold green][PASS][/bold green]"
      elif state == "failure": st_text = "[bold red][FAIL][/bold red]"
      elif state == "pending": st_text = "[bold yellow][PEND][/bold yellow]"
      elif state == "none":    st_text = "[dim white][NONE][/dim white]"
      elif state == "error":
          reason = ci_data.get("reason", "Unknown error.")
          st_text = "[bold red][ERR][/bold red]"
          table.add_row(st_text, repo_name, branch, reason)
          continue
      else: st_text = "[dim red]! ERR[/dim red]"

      table.add_row(st_text, repo_name, branch, "")

  console.print(table)