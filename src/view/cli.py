import argparse
import os
import getpass
from typing import Tuple

 # codigo ANSI para colores basicos en la terminal
C_RESET = "\033[0m"
C_GREEN = "\033[1;32m"
C_RED = "\033[1;31m"
C_CYAN = "\033[1;36m"
C_YELLOW = "\033[1;33m"

def parse_arguments(default_dir: str) -> argparse.Namespace:
  """
  configura y lee los argumentos pasados por la linea de comandos.

  args:
    default_dir (str): el directorio por defecto (obtenido de la persistencia).

  returns:
    argparse.Namespace: objeto con los argumentos parseados.
  """

  parser = argparse.ArgumentParser(
    description = "GitBulk: ejecuta comandos masivos en multiples repositorios."
  )

  parser.add_argument(
    "operation",
    choices = ["fetch", "pull", "auth", "status"],
    help = "la operacion de Git a ejecutar, 'auth' para credenciales, o 'status' para verificar estado."
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

  return parser.parse_args()

def prompt_for_credentials() -> Tuple[str, str]:
  """Pide al usuario sus credenciales de GitHub de forma segura."""
  print(f"\n{C_CYAN}--- Configuración de Credenciales de GitHub ---{C_RESET}")
  print(f"{C_YELLOW}Nota: Se recomienda usar un Personal Access Token (PAT) en lugar de la contraseña.{C_RESET}")
  username = input(f"Usuario de GitHub: ")
  token = getpass.getpass(f"Contraseña o Token: ")
  return username, token

def show_auth_success(username: str) -> None:
  print(f"\n[{C_GREEN}OK{C_RESET}] Credenciales para {C_CYAN}{username}{C_RESET} guardadas globalmente con éxito.")

def show_welcome(root_dir: str, operation: str) -> None:
  """muestra el mensaje de inicio del programa."""
  print(f"\n{C_CYAN}buscando repositorios en:{C_RESET} {root_dir}")
  print(f"{C_CYAN}operacion seleccionada:{C_RESET} {operation.upper()}\n")

def show_no_repos_found(root_dir: str) -> None:
  """muestra un mensaje cuando no se encuentran repositorios."""
  print(f"{C_RED}no se encontro ningun repositorio Git en {root_dir}{C_RESET}")

def show_start_processing(count: int, operation: str) -> None:
  """muestra cuantos repositorios se van a procesar."""
  print(f"encontrados {C_YELLOW}{count}{C_RESET} repositorios Git. ejecutando '{operation}' en paralelo...\n")

def show_result(status: str, repo_path: str, output: str) -> None:
  """muestra el resultado individual de un respositorio."""
  repo_name = os.path.basename(repo_path)

  if status == "OK":
    print(f"[{C_GREEN}OK{C_RESET}] {C_CYAN}{repo_name}{C_RESET}")
  elif status == "CLEAN":
    print(f"[{C_GREEN}CLEAN{C_RESET}] {C_CYAN}{repo_name}{C_RESET}")
  elif status == "MODIFIED":
    print(f"[{C_YELLOW}MODIFIED{C_RESET}] {C_CYAN}{repo_name}{C_RESET}")
  elif status == "AHEAD":
    print(f"[{C_GREEN}AHEAD{C_RESET}] {C_CYAN}{repo_name}{C_RESET}")
  elif status == "BEHIND":
    print(f"[{C_YELLOW}BEHIND{C_RESET}] {C_CYAN}{repo_name}{C_RESET}")
  elif status == "AUTH":
    print(f"[{C_YELLOW}AUTH{C_RESET}] {C_CYAN}{repo_name}{C_RESET} (Requiere credenciales)")
  else:
    print(f"[{C_RED}ERROR{C_RESET}] {C_CYAN}{repo_name}{C_RESET}")
  
  if output and status != "AUTH" and status != "CLEAN":
     # indentamos la salida para que sea mas facil de leer.
    indented_output = output.replace("\n", "\n    ")
    print(f"    {indented_output}")

def show_auth_fallback(count: int) -> None:
  """informa al usuario que hay repositorios que requieren credenciales y se procesaran secuencialmente."""
  print(f"\n{C_YELLOW}{count}{C_RESET} repositorios requieren credenciales.")
  print(f"procesando secuencialmente para permitir la entrada manual...\n")

def show_auth_fallback_start(repo_path: str) -> None:
  repo_name = os.path.basename(repo_path)
  print(f"{C_CYAN}--- Autenticando {repo_name} ---{C_RESET}")

def show_summary(counts: dict) -> None:
  """muestra el resumen final de la ejecuccion."""
  print("-" * 40)
  print(f"proceso finalizado.")
  if counts.get('OK', 0) > 0: print(f"   exitos: {C_GREEN}{counts['OK']}{C_RESET}")
  if counts.get('CLEAN', 0) > 0: print(f"   al dia: {C_GREEN}{counts['CLEAN']}{C_RESET}")
  if counts.get('MODIFIED', 0) > 0: print(f"   con cambios locales: {C_YELLOW}{counts['MODIFIED']}{C_RESET}")
  if counts.get('AHEAD', 0) > 0: print(f"   adelante del remoto: {C_GREEN}{counts['AHEAD']}{C_RESET}")
  if counts.get('BEHIND', 0) > 0: print(f"   atrasado del remoto: {C_YELLOW}{counts['BEHIND']}{C_RESET}")
  if counts.get('ERROR', 0) > 0: print(f"   errores: {C_RED}{counts['ERROR']}{C_RESET}")