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
        "GitBulk: run bulk Git commands across multiple repositories concurrently.\n\n"
        "available commands:\n"
        "  fetch          : download remote history without merging (git fetch).\n"
        "  pull           : update current branch from remote (git pull --ff-only).\n"
        "  push           : upload local commits to remote (git push).\n"
        "  commit         : perform a bulk commit across all dirty repositories.\n"
        "  status         : show working tree state (modified, ahead, behind).\n"
        "  workspace      : manage saved workspace configurations (save, load, list).\n"
        "  groups         : inspect the logical topology of repository groups.\n"
        "  checkout       : move HEAD to a target branch across all repositories.\n"
        "  ci-status      : query GitHub Actions pipeline status.\n"
        "  auth           : configure global GitHub credentials (PAT).\n"
        "  clean          : [destructive] remove dead branches and untracked files.\n"
        "  export/restore : manage repository list backup and recovery."
    ),
    formatter_class=argparse.RawTextHelpFormatter,
    epilog="GitBulk v1.4 | multi-language & workspace-aware engine."
  )

  parser.add_argument(
    "operation",
    choices = ["fetch", "pull", "auth", "status", "export", "restore", "current-branch", "clean", "checkout", "ci-status", "workspace", "groups", "commit", "push"],
    help = "the primary Git operation to iterate across the active workspace."
  )

  parser.add_argument(
    "-m", "--message",
    help = "commit message title (used only for 'commit' operation)."
  )

  parser.add_argument(
    "-D", "--body",
    help = "commit message body (used only for 'commit' operation)."
  )

  parser.add_argument(
    "--action",
    choices = ["save", "load", "list", "delete", "sync"],
    help = "the specific action for the 'workspace' operation."
  )

  parser.add_argument(
    "-n", "--name",
    type = str,
    help = "the name of the workspace to save, load, or delete."
  )

  parser.add_argument(
    "-d", "--dir",
    default=default_dir,
    help = f"root directory to scan (default: {default_dir if default_dir else 'current directory'})"
  )

  parser.add_argument(
    "-w", "--workers",
    type = int,
    default = 0,
    help = "number of concurrent threads. set to 0 for automatic hardware-based tuning (default: 0)."
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
    help = "json file to save/load the repository list."
  )

  parser.add_argument(
    "-b", "--branch",
    type = str,
    help = "target branch name (required for the 'checkout' operation)."
  )

  parser.add_argument(
    "--dry-run",
    action = "store_true",
    dest = "dry_run",
    help = (
        "preview the actions that would be taken without applying any changes.\n"
        "supported operations: 'clean' (shows what would be deleted), 'restore' (shows what would be cloned)."
    )
  )

  parser.add_argument(
    "--group",
    type = str,
    help = "filter operations to only include repositories in this specific group (defined in .gitbulk.repo.json or workspace)."
  )

  parser.add_argument(
    "-i", "--interactive",
    action = "store_true",
    help = "enable interactive mode for 'commit' operation (step-by-step review)."
  )

  return parser.parse_args()

def prompt_for_credentials() -> Tuple[str, str]:
  """Securely prompts the user for their GitHub credentials."""
  console.print(f"\n[bold cyan]--- github credentials setup ---[/bold cyan]")
  console.print(f"[bold yellow]note: using a personal access token (pat) is strongly recommended over a password.[/bold yellow]")
  username = input("github username: ")
  token = getpass.getpass("password or token: ")
  return username, token

def show_interactive_prompt(repo_path, status):
    """
    Shows a fancy interactive prompt for a repository.
    """
    repo_name = os.path.basename(repo_path)
    console.print(f"\n[bold cyan]─── {repo_name} ───[/bold cyan]")
    console.print(f"status: [yellow]{status}[/yellow]")
    
    table = Table(box=None, padding=(0, 2))
    table.add_column("option", style="bold green")
    table.add_column("action", style="dim")
    
    table.add_row("(y)es", "Commit with default message")
    table.add_row("(n)o", "Skip this repository")
    table.add_row("(e)dit", "Open system editor for custom message")
    table.add_row("(d)iff", "Show Git diff summary")
    table.add_row("(s)kip all", "Cancel all remaining commits")
    table.add_row("(q)uit", "Exit GitBulk")
    
    console.print(table)
    
    from model.interactive import get_cli_input
    # Use 'y' as default if they just press Enter
    return get_cli_input("Action?", options=['y', 'n', 'e', 'd', 's', 'q'])

def show_git_diff(repo_path):
    """Shows a simplified git diff for the repo."""
    try:
        import subprocess
        # Get diff summary
        diff = subprocess.check_output(['git', 'diff', '--stat'], cwd=repo_path).decode('utf-8', errors='ignore')
        if not diff.strip():
            diff = "No staged/unstaged changes to show (might be untracked files)."
        console.print(Panel(diff, title="git diff summary", border_style="dim"))
    except Exception as e:
        console.print(f"[red]Error showing diff: {e}[/red]")

def show_auth_success(username: str) -> None:
  console.print(f"\n[bold green]ok[/bold green] credentials for [cyan]{username}[/cyan] saved globally.")

def show_welcome(root_dir: str, operation: str) -> None:
  """Displays the startup banner."""
  welcome_msg = f"[bold cyan]root directory:[/bold cyan] {root_dir}\n[bold cyan]operation:[/bold cyan] [bold white]{operation}[/bold white]"
  console.print(Panel(welcome_msg, title="[bold cyan]GitBulk[/bold cyan]", border_style="blue", expand=False))

def show_no_repos_found(root_dir: str) -> None:
  """Displays a message when no Git repositories are found."""
  console.print(f"[bold red]no Git repositories found in {root_dir}[/bold red]")

def show_start_processing(count: int, operation: str) -> None:
  """Displays how many repositories will be processed."""
  console.print(f"\n[dim]found [bold yellow]{count}[/bold yellow] Git repositories. running '{operation}' in parallel...[/dim]\n")

def show_result(status: str, detail: str, repo_path: str, output: str) -> None:
  """Displays the individual result for a single repository."""
  repo_name = os.path.basename(repo_path)
  detail_str = f" [dim]({detail})[/dim]" if detail else ""

  if status == "OK":
    console.print(f"[bold green][ok][/bold green] [cyan]{repo_name}[/cyan]")
  elif status == "CLEAN":
    console.print(f"[bold green][clean][/bold green] [cyan]{repo_name}[/cyan]")
  elif status == "MODIFIED":
    console.print(f"[bold yellow][modified][/bold yellow]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "AHEAD":
    console.print(f"[bold green][ahead][/bold green]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "BEHIND":
    console.print(f"[bold yellow][behind][/bold yellow]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "CONFLICT":
    console.print(f"[bold yellow][conflict][/bold yellow]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "DIVERGENT":
    console.print(f"[bold red][divergent][/bold red]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "FETCH_UPDATE":
    console.print(f"[bold blue][updates][/bold blue]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "STASH_RESTORED":
    console.print(f"[bold blue][sync+stash][/bold blue]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "STASH_CONFLICT":
    console.print(f"[bold yellow][stash conflict][/bold yellow]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "COMMITTED":
    console.print(f"[bold blue][committed][/bold blue]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "PUSHED":
    console.print(f"[bold green][pushed][/bold green]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "CLEANED":
    console.print(f"[bold magenta][cleaned][/bold magenta]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "SIMULATED":
    console.print(f"[bold green][dry-run][/bold green]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "CHECKOUT":
    console.print(f"[bold cyan][checkout][/bold cyan]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "IGNORED":
    console.print(f"[dim white][ignored][/dim white]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "AUTH":
    console.print(f"[bold yellow][auth][/bold yellow] [cyan]{repo_name}[/cyan] [dim](credentials required)[/dim]")
  else:
    console.print(f"[bold red][error][/bold red] [cyan]{repo_name}[/cyan]")

  if output and status not in ("AUTH", "CLEAN"):
    indented_output = output.replace("\n", "\n    ")
    console.print(f"    [dim]{indented_output}[/dim]")

def show_auth_fallback(count: int) -> None:
  """Informs the user that some repositories require credentials and will be processed sequentially."""
  console.print(f"\n[bold yellow]{count}[/bold yellow] repositories require credentials.")
  console.print("[dim]processing sequentially to allow manual credential input...[/dim]\n")

def show_auth_fallback_start(repo_path: str) -> None:
  repo_name = os.path.basename(repo_path)
  console.print(f"[bold cyan]authenticating {repo_name} ...[/bold cyan]")

def show_clean_warning() -> bool:
  """
  Displays the destructive operation warning panel and asks for interactive confirmation.

  Returns:
    True if the user explicitly confirms, False if they decline.
    Exits the process (sys.exit(0)) on KeyboardInterrupt or EOFError (non-interactive environments).
  """
  import sys
  console.print(Panel(
      "[bold]all[/bold] dead remote branch references and untracked local files "
      "will be [bold]permanently deleted[/bold].\n"
      "this operation runs 'git fetch --prune' and 'git clean -xfd'.\n"
      "make sure you have no unsaved local configurations or .env files.",
      title="[bold red]security warning[/bold red]",
      border_style="red"
  ))
  try:
      confirmed = Confirm.ask(
          "[bold yellow]are you absolutely sure you want to proceed on all repositories?[/bold yellow]"
      )
      if not confirmed:
          console.print("[dim]bulk 'clean' operation cancelled. everything is safe.[/dim]")
          sys.exit(0)
      return True
  except (KeyboardInterrupt, EOFError):
      console.print("\n[dim]security prompt abruptly cancelled.[/dim]")
      sys.exit(0)

def show_summary(counts: dict) -> None:
  """Displays the final execution summary table."""
  table = Table(title="[bold magenta]execution summary[/bold magenta]", show_header=True, header_style="bold magenta")
  table.add_column("status", style="dim")
  table.add_column("count", justify="right")

  if counts.get('OK', 0) > 0:            table.add_row("[bold green]success[/bold green]",             str(counts['OK']))
  if counts.get('CLEAN', 0) > 0:         table.add_row("[bold green]up to date[/bold green]",          str(counts['CLEAN']))
  if counts.get('MODIFIED', 0) > 0:      table.add_row("[bold yellow]modified[/bold yellow]",           str(counts['MODIFIED']))
  if counts.get('AHEAD', 0) > 0:         table.add_row("[bold green]ahead[/bold green]",                str(counts['AHEAD']))
  if counts.get('BEHIND', 0) > 0:        table.add_row("[bold yellow]behind[/bold yellow]",             str(counts['BEHIND']))
  if counts.get('FETCH_UPDATE', 0) > 0:  table.add_row("[bold blue]pending pull[/bold blue]",           str(counts['FETCH_UPDATE']))
  if counts.get('STASH_RESTORED', 0) > 0:table.add_row("[bold blue]synced (autostash)[/bold blue]",    str(counts['STASH_RESTORED']))
  if counts.get('CLEANED', 0) > 0:       table.add_row("[bold magenta]cleaned / pruned[/bold magenta]", str(counts['CLEANED']))
  if counts.get('CHECKOUT', 0) > 0:      table.add_row("[bold cyan]checked out[/bold cyan]",            str(counts['CHECKOUT']))
  if counts.get('COMMITTED', 0) > 0:     table.add_row("[bold blue]committed[/bold blue]",              str(counts['COMMITTED']))
  if counts.get('PUSHED', 0) > 0:        table.add_row("[bold green]pushed[/bold green]",               str(counts['PUSHED']))
  if counts.get('IGNORED', 0) > 0:       table.add_row("[dim white]ignored[/dim white]",                str(counts['IGNORED']))
  if counts.get('CONFLICT', 0) > 0:      table.add_row("[bold yellow]local conflicts[/bold yellow]",    str(counts['CONFLICT']))
  if counts.get('STASH_CONFLICT', 0) > 0:table.add_row("[bold yellow]autostash conflicts[/bold yellow]",str(counts['STASH_CONFLICT']))
  if counts.get('DIVERGENT', 0) > 0:     table.add_row("[bold red]require merge[/bold red]",            str(counts['DIVERGENT']))
  if counts.get('ERROR', 0) > 0:         table.add_row("[bold red]errors[/bold red]",                   str(counts['ERROR']))

  console.print("\n")
  console.print(table)

def show_sync_preview(to_clone: list, to_archive: list) -> bool:
  """
  Shows a preview of the sync operation and asks for confirmation.
  """
  from rich.table import Table
  from rich.prompt import Confirm
  
  if not to_clone and not to_archive:
    console.print("\n[bold green]workspace is already perfectly synced with the reference file.[/bold green]\n")
    return False

  table = Table(title="[bold yellow]sync preview[/bold yellow]", show_header=True)
  table.add_column("repository", style="cyan")
  table.add_column("action", justify="center")
  table.add_column("detail", style="dim")

  for path, info in to_clone:
    table.add_row(path, "[bold green]clone[/bold green]", f"from {info.get('url', 'n/a')}")
    
  for path in to_archive:
    table.add_row(path, "[bold red]archive[/bold red]", "move to .gitbulk_archive/")

  console.print(table)
  console.print("\n[bold red]warning:[/bold red] archive moves the above folders to a timestamped backup folder.")
  
  try:
    return Confirm.ask("[bold yellow]do you want to proceed with this sync?[/bold yellow]")
  except (KeyboardInterrupt, EOFError):
    return False


def show_groups_summary(topology: dict) -> None:
  """Displays a structured overview of all discovered groups and their repositories."""
  from rich.tree import Tree
  import os
  
  console.print("\n[bold magenta]group topology inspector[/bold magenta]")
  if not topology:
      console.print("[dim]no organizational data found.[/dim]")
      return

  root_tree = Tree("[bold cyan]workspace groups[/bold cyan]")
  
  # Sort groups alphabetically, but put Uncategorized last
  sorted_groups = sorted(topology.keys(), key=lambda x: (1 if x == "Uncategorized" else 0, x.lower()))
  
  for g_name in sorted_groups:
      group_node = root_tree.add(f"[bold yellow]{g_name}[/bold yellow] [dim]({len(topology[g_name])} repos)[/dim]")
      for repo in topology[g_name]:
          repo_name = os.path.basename(repo["path"])
          group_node.add(f"[cyan]{repo_name}[/cyan] [dim]({repo['path']})[/dim]")
  
  console.print(root_tree)
  console.print("\n")

def show_branches_compact(results: list) -> None:
  """Displays an ultra-compact one-line-per-repository branch topology view."""
  console.print("\n[bold magenta]branch topology[/bold magenta]")

  if not results: return

  max_len = max(len(repo_name) for repo_name, _ in results)

  for repo_name, branches_data in results:
      error = branches_data.get("error", "")
      if error:
          console.print(f"[bold red][error][/bold red] [cyan]{repo_name}[/cyan]   [dim]{error}[/dim]")
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
  console.print("\n[bold magenta]continuous integration status (GitHub Actions)[/bold magenta]")
  if not results: return

  table = Table(show_header=True, header_style="bold magenta", box=None)
  table.add_column("status", justify="center")
  table.add_column("repository", style="cyan")
  table.add_column("active branch", style="dim")
  table.add_column("detail", style="dim red")

  for repo_name, ci_data in results:
      state = ci_data.get("state", "none")
      branch = ci_data.get("branch", "n/a")

      if state == "success":   st_text = "[bold green][pass][/bold green]"
      elif state == "failure": st_text = "[bold red][fail][/bold red]"
      elif state == "pending": st_text = "[bold yellow][pend][/bold yellow]"
      elif state == "none":    st_text = "[dim white][none][/dim white]"
      elif state == "error":
          reason = ci_data.get("reason", "unknown error.")
          st_text = "[bold red][err][/bold red]"
          table.add_row(st_text, repo_name, branch, reason)
          continue
      else: st_text = "[dim red]! err[/dim red]"

      table.add_row(st_text, repo_name, branch, "")

  console.print(table)