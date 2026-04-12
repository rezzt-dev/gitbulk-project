"""
src/model/error_handler.py

Translates raw GitCommandError exceptions from GitPython into
clean, user-friendly English messages for display in the terminal.
"""

import re
def parse_git_error(error_msg: str) -> str:
    """
    Parses and cleans raw errors returned by Git commands,
    translating the most common failures into readable messages.
    Unknown errors are truncated to avoid cluttering the terminal.
    """
    error_msg = error_msg.strip()
    if not error_msg:
        return "Unknown Git error."

    # 1. Network / SSH / Connectivity errors
    if "Could not resolve host" in error_msg or "Connection timed out" in error_msg or "Could not read from remote repository" in error_msg:
        return "Network error: The remote repository is unreachable or the connection failed."

    if "Connection refused" in error_msg:
        return "Network error: Connection refused by the remote server."

    if "Repository not found" in error_msg:
        return "HTTP 404: Repository not found at the remote origin."

    # 2. Authentication errors
    if "Permission denied (publickey)" in error_msg:
        return "SSH Auth Error: Permission denied. Ensure your private key is added to the ssh-agent (ssh-add)."
        
    if "Permission denied" in error_msg or "Authentication failed" in error_msg or "could not read Username" in error_msg:
        return "Authentication error: Invalid or missing SSH/HTTPS credentials."

    # 3. Merge and conflict errors
    if "Applied autostash" in error_msg and "CONFLICT" in error_msg.upper():
        return "Autostash conflict: Downloaded changes clash with local edits. Manual resolution required."

    if "overwritten by merge" in error_msg or "Please commit your changes or stash them" in error_msg:
        return "Pull conflict: Unsaved local changes prevent the network update."

    if "Not possible to fast-forward" in error_msg or "divergent branches" in error_msg or "Need to specify how to reconcile" in error_msg:
        return "Divergent branches: Local and remote histories have advanced in different directions."

    # 4. Clone errors
    if "already exists and is not an empty directory" in error_msg or "already exists" in error_msg:
        return "System conflict: The destination directory already exists or is not empty."

    # 5. Default fallback: truncate excessively long unknown errors
    lines = [line.strip() for line in error_msg.split('\n') if line.strip()]
    if len(lines) > 3:
        return '\n    '.join(lines[:3]) + "\n    [...] Native Git error truncated."

    return '\n    '.join(lines)
