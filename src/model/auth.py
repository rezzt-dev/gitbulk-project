import subprocess
import os
from pathlib import Path

def setup_global_git_credentials(username: str, token: str) -> bool:
  """
  Configure git to globally store credentials for https://github.com
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
    print(f"Error configurando el helper de credenciales: {e.stderr}")
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
            
    # Restrict permissions for security
    os.chmod(credentials_file, 0o600)
    
    return True
  except Exception as e:
     print(f"Error guardando credenciales en ~/.git-credentials: {str(e)}")
     return False
