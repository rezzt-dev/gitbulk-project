import os
import subprocess
import sys
from typing import Tuple, Dict, List, Optional
from .error_handler import parse_git_error

# --- LOW-LEVEL ENGINE (Performance optimized) ---

def _resolve_git_executable() -> str:
    """
    Resolves the path to the git executable, prioritizing bundled versions.
    Priority:
    1. PyInstaller bundled path (sys._MEIPASS).
    2. Local path (relative to executable).
    3. System PATH.
    """
    # 1. Check for PyInstaller bundled Git
    if hasattr(sys, '_MEIPASS'):
        bin_folder = os.path.join(sys._MEIPASS, "vendor", "git", "cmd")
        bundled_git = os.path.join(bin_folder, "git.exe" if sys.platform == "win32" else "git")
        if os.path.exists(bundled_git):
            return bundled_git

    # 2. Check for local 'bin' folder (non-onefile bundle or local dev)
    local_bin = os.path.join(os.path.dirname(sys.executable), "vendor", "git", "cmd")
    local_git = os.path.join(local_bin, "git.exe" if sys.platform == "win32" else "git")
    if os.path.exists(local_git):
        return local_git

    # 3. Fallback to system path
    return "git"

def _run_git_command(args: List[str], cwd: str, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    """
    Executes a git command via subprocess with controlled environment.
    Returns (returncode, stdout, stderr).
    """
    git_path = _resolve_git_executable()
    
    # Disable terminal prompts to avoid hanging on SSH/Auth
    base_env = os.environ.copy()
    base_env["GIT_TERMINAL_PROMPT"] = "0"
    
    # If using bundled git, we might need to add its bin folder to PATH so it finds helpers
    if git_path != "git":
        git_dir = os.path.dirname(git_path)
        base_env["PATH"] = git_dir + os.pathsep + base_env.get("PATH", "")

    if env:
        base_env.update(env)
        
    try:
        # ── Windows specific: Suppress console windows for silent GUI
        creationflags = 0
        if sys.platform == "win32":
            creationflags = 0x08000000 # subprocess.CREATE_NO_WINDOW

        process = subprocess.run(
            [git_path] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=base_env,
            check=False,
            creationflags=creationflags
        )
        return process.returncode, process.stdout, process.stderr
    except FileNotFoundError:
        return -1, "", f"Git executable not found at: {git_path}"
    except Exception as e:
        return -1, "", str(e)

def _parse_porcelain_v2(output: str) -> Dict[str, str]:
    """
    Parses git status --porcelain=v2 --branch output.
    Returns a normalized dictionary of state.
    """
    state = {
        "branch": "HEAD",
        "ahead": 0,
        "behind": 0,
        "is_dirty": False,
        "conflict": False,
        "modified_count": 0
    }
    
    lines = output.strip().split('\n')
    for line in lines:
        if not line: continue
        
        # Headers
        if line.startswith("# branch.head "):
            state["branch"] = line[14:].strip()
        elif line.startswith("# branch.ab "):
            parts = line[12:].split()
            if len(parts) >= 2:
                state["ahead"] = int(parts[0].replace("+", ""))
                state["behind"] = int(parts[1].replace("-", ""))
        
        # Files (Tracked/Untracked/Unmerged)
        elif line.startswith(("1 ", "2 ", "? ", "u ")):
            state["is_dirty"] = True
            state["modified_count"] += 1
            if line.startswith("u "):
                state["conflict"] = True
                
    return state

# --- HIGH-LEVEL OPERATIONS ---

def run_git_operation(repo_path: str, operation: str, allow_prompt: bool = False, autostash: bool = False, target_branch: str = None, dry_run: bool = False, **kwargs) -> Tuple[str, str, str, str]:
    try:
        if not os.path.exists(os.path.join(repo_path, ".git")):
            return "ERROR", "Not a Git directory", repo_path, ""

        if operation == "status":
            code, stdout, stderr = _run_git_command(["status", "--porcelain=v2", "--branch"], repo_path)
            if code != 0: return "ERROR", "Status failed", repo_path, parse_git_error(stderr)
            
            state = _parse_porcelain_v2(stdout)
            if state["is_dirty"]:
                return "MODIFIED", str(state["modified_count"]), repo_path, ""
            
            if state["ahead"] > 0:
                return "AHEAD", str(state["ahead"]), repo_path, state["branch"]
            elif state["behind"] > 0:
                return "BEHIND", str(state["behind"]), repo_path, state["branch"]
                
            return "CLEAN", "", repo_path, ""

        if operation in ["fetch", "sync"]:
            # Native fetch
            code, stdout, stderr = _run_git_command(["fetch", "--prune"], repo_path)
            # Fetch often prints to stderr even on success (progress)
            output = stdout + stderr

            # Post-fetch status
            code, stdout, stderr = _run_git_command(["status", "--porcelain=v2", "--branch"], repo_path)
            state = _parse_porcelain_v2(stdout)
            
            if state["is_dirty"]:
                return "MODIFIED", f"{state['modified_count']} files", repo_path, output
            
            if state["ahead"] > 0 and state["behind"] > 0:
                return "DIVERGENT", f"↑{state['ahead']} ↓{state['behind']}", repo_path, output
            elif state["ahead"] > 0:
                return "AHEAD", f"{state['ahead']} commits", repo_path, output
            elif state["behind"] > 0:
                return "BEHIND", f"{state['behind']} commits", repo_path, output
                
            return "OK", "Up to date", repo_path, output

        if operation == "clean":
            args = ["clean", "-xfd"]
            if dry_run: args.append("-n")
            
            # Prune first
            _run_git_command(["fetch", "--prune"], repo_path)
            code, stdout, stderr = _run_git_command(args, repo_path)
            
            status = "SIMULATED" if dry_run else "CLEANED"
            detail = "[dry-run] clean" if dry_run else "Aggressive cleanup complete"
            return status, detail, repo_path, stdout

        if operation == "pull":
            # Check dirty
            code, stdout, stderr = _run_git_command(["status", "--porcelain=v2"], repo_path)
            state = _parse_porcelain_v2(stdout)
            
            if state["is_dirty"] and not autostash:
                return "CONFLICT", "Local changes prevent update", repo_path, "Commit changes or use --autostash"
                
            cmd = ["pull", "--ff-only"]
            if autostash: cmd.append("--autostash")
            
            code, stdout, stderr = _run_git_command(cmd, repo_path)
            if code == 0:
                status = "STASH_RESTORED" if autostash and state["is_dirty"] else "OK"
                return status, "Synced", repo_path, stdout
            else:
                return "ERROR", "Pull failed", repo_path, parse_git_error(stderr)

        if operation == "checkout":
            if not target_branch:
                return "ERROR", "Missing branch", repo_path, ""
            
            # 1. Is it local?
            code, stdout, stderr = _run_git_command(["checkout", target_branch], repo_path)
            if code == 0:
                return "CHECKOUT", "Switched", repo_path, stdout
            
            # 2. Try remote
            code, stdout, stderr = _run_git_command(["checkout", "-t", f"origin/{target_branch}"], repo_path)
            if code == 0:
                return "CHECKOUT", "Tracking remote", repo_path, stdout
                
            return "IGNORED", "Branch not found", repo_path, parse_git_error(stderr)

        if operation == "commit":
            # 1. Check if dirty
            code, stdout, stderr = _run_git_command(["status", "--porcelain=v2"], repo_path)
            state = _parse_porcelain_v2(stdout)
            
            if not state["is_dirty"]:
                return "OK", "Nothing to commit", repo_path, "Working tree clean"
            
            # 2. Add all changes
            _run_git_command(["add", "."], repo_path)
            
            # 3. Commit
            msg = kwargs.get("message", "GitBulk: Bulk update")
            body = kwargs.get("body", "")
            cmd = ["commit", "-m", msg]
            if body:
                cmd.extend(["-m", body])
            
            code, stdout, stderr = _run_git_command(cmd, repo_path)
            if code == 0:
                return "COMMITTED", "Changes saved", repo_path, stdout
            else:
                return "ERROR", "Commit failed", repo_path, parse_git_error(stderr)

        if operation == "push":
            # 1. Check if ahead (to avoid unnecessary network calls)
            code, stdout, stderr = _run_git_command(["status", "--porcelain=v2", "--branch"], repo_path)
            state = _parse_porcelain_v2(stdout)
            
            if state["ahead"] == 0:
                return "OK", "Already synced", repo_path, "Local branch is NOT ahead of origin"
            
            # 2. Push current HEAD to origin
            code, stdout, stderr = _run_git_command(["push", "origin", "HEAD"], repo_path)
            if code == 0:
                return "PUSHED", "Uploaded to origin", repo_path, stdout
            else:
                return "ERROR", "Push failed", repo_path, parse_git_error(stderr)

        return "ERROR", "Unknown op", repo_path, ""

    except Exception as e:
        return "ERROR", "Engine Exception", repo_path, str(e)

def get_repo_metadata(repo_path: str) -> dict:
    metadata = {"url": "", "branch": "", "error": ""}
    try:
        # Get URL
        code, stdout, stderr = _run_git_command(["remote", "get-url", "origin"], repo_path)
        if code == 0: metadata["url"] = stdout.strip()
        
        # Get Branch
        code, stdout, stderr = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
        if code == 0: metadata["branch"] = stdout.strip()
        
    except Exception as e:
        metadata["error"] = str(e)
    return metadata

def clone_repo(target_dir: str, repo_info: dict) -> Tuple[str, str, str, str]:
    url = repo_info.get("url")
    branch = repo_info.get("branch")
    
    if not url: return "ERROR", "Missing URL", target_dir, ""
    
    try:
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        args = ["clone", url, target_dir]
        if branch: args += ["-b", branch]
        
        code, stdout, stderr = _run_git_command(args, os.getcwd())
        if code == 0:
            return "OK", branch or "main", target_dir, "Cloned"
        else:
            err = parse_git_error(stderr)
            if "already exists" in err or "existe" in err: return "CLEAN", "Exists", target_dir, ""
            return "ERROR", "Clone failed", target_dir, err
    except Exception as e:
        return "ERROR", "Critical", target_dir, str(e)

def get_all_branches(repo_path: str) -> dict:
    data = {"current": "", "local": [], "remote_only": [], "error": ""}
    try:
        # Current
        code, stdout, stderr = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
        data["current"] = stdout.strip()
        
        # Local
        code, stdout, stderr = _run_git_command(["branch", "--format=%(refname:short)"], repo_path)
        data["local"] = [l.strip() for l in stdout.split('\n') if l.strip()]
        
        # Remote
        code, stdout, stderr = _run_git_command(["branch", "-r", "--format=%(refname:short)"], repo_path)
        remote_branches = [l.strip() for l in stdout.split('\n') if l.strip()]
        # Filter out origin/HEAD and already local ones
        for rb in remote_branches:
            if "/HEAD" in rb: continue
            short_name = rb.split('/', 1)[-1]
            if short_name not in data["local"]:
                data["remote_only"].append(rb)
                
    except Exception as e:
        data["error"] = str(e)
    return data