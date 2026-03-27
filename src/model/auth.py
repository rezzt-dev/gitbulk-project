import subprocess
import os
import sys
import urllib.parse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def _restrict_file_permissions(filepath: Path) -> None:
    """
    Restringe los permisos del fichero al propietario exclusivamente.
    En POSIX (Linux/macOS) usa chmod 0o600.
    En Windows usa icacls para eliminar el acceso heredado y conceder permisos solo al usuario actual.
    """
    if sys.platform == "win32":
        try:
            username = os.environ.get("USERNAME", "")
            subprocess.run(
                ["icacls", str(filepath), "/inheritance:r", "/grant:r", f"{username}:F"],
                check=True, capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    else:
        os.chmod(filepath, 0o600)

def setup_global_git_credentials(username: str, token: str) -> bool:
  """
  Configures Git to globally store credentials for https://github.com.
  Returns True if successful, False otherwise.
  """
  try:
    # Set the credential helper globally
    subprocess.run(
      ["git", "config", "--global", "credential.helper", "store"],
       check=True,
       capture_output=True,
       text=True
    )
    
  except subprocess.CalledProcessError as e:
    console.print(f"[bold red]Error configuring the credential helper:[/bold red] {e.stderr}")
    return False

  # Create or append to the ~/.git-credentials file
  credentials_file = Path.home() / ".git-credentials"
  credential_string = f"https://{username}:{token}@github.com"
  
  try:
    # Read existing credentials
    existing_creds = []
    if credentials_file.exists():
        with open(credentials_file, 'r', encoding='utf-8') as f:
            existing_creds = [line.strip() for line in f.readlines() if line.strip()]

    # Add new credential if it doesn't already exist (or replace old github one)
    updated_creds = []
    for cred in existing_creds:
        if "@github.com" not in cred:
             updated_creds.append(cred)
    
    updated_creds.append(credential_string)
    
    # Write back
    with open(credentials_file, 'w', encoding='utf-8') as f:
        for cred in updated_creds:
            f.write(f"{cred}\n")
            
    # Restringir permisos del fichero (multiplataforma)
    _restrict_file_permissions(credentials_file)

    console.print()
    console.print(Panel(
        f"[bold yellow]Credentials saved in plaintext at:[/bold yellow] [cyan]{credentials_file}[/cyan]\n"
        "[dim]Ensure only you have read access to this file.[/dim]\n"
        "[dim]Consider revoking the token on GitHub if this is a shared machine.[/dim]",
        title="[bold red]Security Warning[/bold red]",
        border_style="yellow",
        expand=False
    ))
    console.print()
    return True
  except Exception as e:
    console.print(f"[bold red]Error saving credentials to ~/.git-credentials:[/bold red] {str(e)}")
    return False

def get_github_token() -> str:
    """Silently extracts the stored PAT from global Git credentials."""
    credentials_file = Path.home() / ".git-credentials"
    if not credentials_file.exists(): 
        return None
        
    try:
        with open(credentials_file, 'r', encoding='utf-8') as f:
            for line in f:
                if "@github.com" in line:
                    parsed = urllib.parse.urlparse(line.strip())
                    return parsed.password
    except Exception:
        pass
    return None
