import argparse
import os
import getpass
from typing import Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()

def parse_arguments(default_dir: str) -> argparse.Namespace:
  """
  configura y lee los argumentos pasados por la linea de comandos.

  args:
    default_dir (str): el directorio por defecto (obtenido de la persistencia).

  returns:
    argparse.Namespace: objeto con los argumentos parseados.
  """

  parser = argparse.ArgumentParser(
    description = (
        "GitBulk: Ejecuta comandos masivos en múltiples repositorios Git concurrentemente.\n\n"
        "Comandos disponibles:\n"
        "  fetch          : Descarga el historial remoto sin fusionar (git fetch).\n"
        "  pull           : Actualiza la rama actual con el remoto (git pull --ff-only).\n"
        "  auth           : Configura tus credenciales globales (PAT) de GitHub.\n"
        "  status         : Muestra el estado del árbol de trabajo (modificados, ahead/behind).\n"
        "  export         : Exporta la lista de repositorios y su origen a un archivo JSON.\n"
        "  restore        : Clona masivamente repositorios faltantes leyendo un JSON de exportación.\n"
        "  current-branch : Muestra una topografía ultracompacta de ramas locales y remotas.\n"
        "  clean          : [Destructivo] Elimina ramas remotas muertas y archivos no versionados.\n"
        "  checkout       : Cambia el puntero HEAD iterativamente (-b rama_destino).\n"
        "  ci-status      : Consulta a GitHub el estado de pruebas (Pipelines) mediante tu PAT configurado."
    ),
    formatter_class=argparse.RawTextHelpFormatter
  )

  parser.add_argument(
    "operation",
    choices = ["fetch", "pull", "auth", "status", "export", "restore", "current-branch", "clean", "checkout", "ci-status"],
    help = "La operación principal de Git a iterar en el espacio de trabajo activo."
  )

  parser.add_argument(
    "-d", "--dir",
    default=default_dir,
    help = f"directorio raiz (por defecto: {default_dir if default_dir else 'directorio actual'})"
  )

  parser.add_argument(
    "-w", "--workers",
    type = int,
    default = 5,
    help = "numero de hilos concurrentes para mayor velocidad (por defecto: 5)."
  )

  parser.add_argument(
    "-l", "--log",
    type = str,
    help = "archivo opcional para guardar los resultados de la ejecucion."
  )

  parser.add_argument(
    "--autostash",
    action = "store_true",
    help = "usa git stash pre y post pull para evitar conflictos por archivos modificados locales."
  )

  parser.add_argument(
    "-f", "--file",
    type = str,
    default = "snapshot.json",
    help = "archivo json para guardar/cargar la lista de repositorios."
  )

  parser.add_argument(
    "-b", "--branch",
    type = str,
    help = "rama de destino (OBLIGATORIA para la operación 'checkout')."
  )

  return parser.parse_args()

def prompt_for_credentials() -> Tuple[str, str]:
  """Pide al usuario sus credenciales de GitHub de forma segura."""
  console.print(f"\n[bold cyan]--- Configuración de Credenciales de GitHub ---[/bold cyan]")
  console.print(f"[bold yellow]Nota: Se recomienda usar un Personal Access Token (PAT) en lugar de la contraseña.[/bold yellow]")
  username = input("Usuario de GitHub: ")
  token = getpass.getpass("Contraseña o Token: ")
  return username, token

def show_auth_success(username: str) -> None:
  console.print(f"\n[bold green]OK[/bold green] Credenciales para [cyan]{username}[/cyan] guardadas globalmente con éxito.")

def show_welcome(root_dir: str, operation: str) -> None:
  """muestra el mensaje de inicio del programa."""
  welcome_msg = f"[bold cyan]Directorio raíz:[/bold cyan] {root_dir}\n[bold cyan]Operación:[/bold cyan] [bold white]{operation.upper()}[/bold white]"
  console.print(Panel(welcome_msg, title="[bold cyan]GitBulk Manager[/bold cyan]", border_style="blue", expand=False))

def show_no_repos_found(root_dir: str) -> None:
  """muestra un mensaje cuando no se encuentran repositorios."""
  console.print(f"[bold red]No se encontro ningun repositorio Git en {root_dir}[/bold red]")

def show_start_processing(count: int, operation: str) -> None:
  """muestra cuantos repositorios se van a procesar."""
  console.print(f"\n[dim]Encontrados [bold yellow]{count}[/bold yellow] repositorios Git. Ejecutando '{operation}' en paralelo...[/dim]\n")

def show_result(status: str, detail: str, repo_path: str, output: str) -> None:
  """muestra el resultado individual de un respositorio."""
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
  elif status == "CHECKOUT":
    console.print(f"[bold cyan][CHECKOUT][/bold cyan]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "IGNORED":
    console.print(f"[dim white][IGNORED][/dim white]{detail_str} [cyan]{repo_name}[/cyan]")
  elif status == "AUTH":
    console.print(f"[bold yellow][AUTH][/bold yellow] [cyan]{repo_name}[/cyan] [dim](Requiere credenciales)[/dim]")
  else:
    console.print(f"[bold red][ERROR][/bold red] [cyan]{repo_name}[/cyan]")
  
  if output and status not in ("AUTH", "CLEAN"):
     # indentamos la salida para que sea mas facil de leer.
    indented_output = output.replace("\n", "\n    ")
    console.print(f"    [dim]{indented_output}[/dim]")

def show_auth_fallback(count: int) -> None:
  """informa al usuario que hay repositorios que requieren credenciales y se procesaran secuencialmente."""
  console.print(f"\n[bold yellow]{count}[/bold yellow] repositorios requieren credenciales.")
  console.print("[dim]Procesando secuencialmente para permitir la entrada manual...[/dim]\n")

def show_auth_fallback_start(repo_path: str) -> None:
  repo_name = os.path.basename(repo_path)
  console.print(f"[bold cyan]Autenticando {repo_name} ...[/bold cyan]")

def show_summary(counts: dict) -> None:
  """muestra el resumen final de la ejecuccion."""
  table = Table(title="[bold magenta]Resumen Final de Ejecución[/bold magenta]", show_header=True, header_style="bold magenta")
  table.add_column("Estado", style="dim")
  table.add_column("Cantidad", justify="right")

  if counts.get('OK', 0) > 0: table.add_row("[bold green]Éxitos[/bold green]", str(counts['OK']))
  if counts.get('CLEAN', 0) > 0: table.add_row("[bold green]Al día[/bold green]", str(counts['CLEAN']))
  if counts.get('MODIFIED', 0) > 0: table.add_row("[bold yellow]Modificados[/bold yellow]", str(counts['MODIFIED']))
  if counts.get('AHEAD', 0) > 0: table.add_row("[bold green]Adelantados[/bold green]", str(counts['AHEAD']))
  if counts.get('BEHIND', 0) > 0: table.add_row("[bold yellow]Atrasados[/bold yellow]", str(counts['BEHIND']))
  if counts.get('FETCH_UPDATE', 0) > 0: table.add_row("[bold blue]Pendientes de Pull[/bold blue]", str(counts['FETCH_UPDATE']))
  if counts.get('STASH_RESTORED', 0) > 0: table.add_row("[bold blue]Sincronizados (Autostash)[/bold blue]", str(counts['STASH_RESTORED']))
  if counts.get('CLEANED', 0) > 0: table.add_row("[bold magenta]Limpiados / Pruned[/bold magenta]", str(counts['CLEANED']))
  if counts.get('CHECKOUT', 0) > 0: table.add_row("[bold cyan]Cambiados (Checkout)[/bold cyan]", str(counts['CHECKOUT']))
  if counts.get('IGNORED', 0) > 0: table.add_row("[dim white]Ignorados[/dim white]", str(counts['IGNORED']))
  if counts.get('CONFLICT', 0) > 0: table.add_row("[bold yellow]Conflictos Locales[/bold yellow]", str(counts['CONFLICT']))
  if counts.get('STASH_CONFLICT', 0) > 0: table.add_row("[bold yellow]Conflictos Autostash[/bold yellow]", str(counts['STASH_CONFLICT']))
  if counts.get('DIVERGENT', 0) > 0: table.add_row("[bold red]Requieren Merge[/bold red]", str(counts['DIVERGENT']))
  if counts.get('ERROR', 0) > 0: table.add_row("[bold red]Errores[/bold red]", str(counts['ERROR']))

  console.print("\n")
  console.print(table)

def show_branches_compact(results: list) -> None:
  """muestra una vista ultracompacta de exactamente 1 linea por repositorio."""
  console.print("\n[bold magenta]Topografía de Ramas[/bold magenta]")
  
  if not results: return
  
  max_len = max(len(repo_name) for repo_name, _ in results)
  
  for repo_name, branches_data in results:
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
  """muestra una vista compacta de los status del CI."""
  console.print("\n[bold magenta]Estado de Integración Continua (GitHub Actions)[/bold magenta]")
  if not results: return
  
  table = Table(show_header=True, header_style="bold magenta", box=None)
  table.add_column("Estado", justify="center")
  table.add_column("Repositorio", style="cyan")
  table.add_column("Rama Activa", style="dim")
  
  for repo_name, ci_data in results:
      state = ci_data.get("state", "none")
      branch = ci_data.get("branch", "N/A")
      
      if state == "success": st_text = "[bold green][PASS][/bold green]"
      elif state == "failure": st_text = "[bold red][FAIL][/bold red]"
      elif state == "pending": st_text = "[bold yellow][PEND][/bold yellow]"
      elif state == "none": st_text = "[dim white][NONE][/dim white]"
      else: st_text = "[dim red]! ERR[/dim red]"
          
      table.add_row(st_text, repo_name, branch)
      
  console.print(table)