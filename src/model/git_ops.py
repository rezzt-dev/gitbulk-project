import os
from typing import Tuple
from git import Repo, exc
from .error_handler import parse_git_error

def run_git_operation(repo_path: str, operation: str, allow_prompt: bool = False, autostash: bool = False, target_branch: str = None, dry_run: bool = False) -> Tuple[str, str, str, str]:
    try:
        if not os.path.exists(os.path.join(repo_path, ".git")):
            return "ERROR", "Not a Git directory", repo_path, ""
            
        repo = Repo(repo_path)
        
        if operation == "status":
            is_dirty = repo.is_dirty(untracked_files=True)
            if is_dirty:
                modified_count = len(repo.untracked_files) + len([diff for diff in repo.index.diff(None)]) + len([diff for diff in repo.index.diff('HEAD')])
                return "MODIFIED", str(modified_count), repo_path, ""
            else:
                try:
                    active_branch = repo.active_branch
                    tracking_branch = active_branch.tracking_branch()
                    if tracking_branch:
                        commits_behind = list(repo.iter_commits(f'{active_branch.name}..{tracking_branch.name}'))
                        commits_ahead = list(repo.iter_commits(f'{tracking_branch.name}..{active_branch.name}'))
                        if commits_ahead:
                            return "AHEAD", str(len(commits_ahead)), repo_path, active_branch.name
                        elif commits_behind:
                            return "BEHIND", str(len(commits_behind)), repo_path, active_branch.name
                    return "CLEAN", "", repo_path, ""
                except TypeError:
                    return "CLEAN", "Detached HEAD", repo_path, ""
                except ValueError:
                    return "CLEAN", "No commits yet", repo_path, ""

        if operation in ["fetch", "sync"]:
            output = repo.git.fetch()
            
            # Use shared status logic for detailed reporting
            is_dirty = repo.is_dirty(untracked_files=True)
            if is_dirty:
                modified_count = len(repo.untracked_files) + len([diff for diff in repo.index.diff(None)]) + len([diff for diff in repo.index.diff('HEAD')])
                return "MODIFIED", f"{modified_count} files", repo_path, output
            
            try:
                active_branch = repo.active_branch
                tracking_branch = active_branch.tracking_branch()
                if tracking_branch:
                    commits_behind = list(repo.iter_commits(f'{active_branch.name}..{tracking_branch.name}'))
                    commits_ahead = list(repo.iter_commits(f'{tracking_branch.name}..{active_branch.name}'))
                    
                    if commits_ahead and commits_behind:
                        return "DIVERGENT", f"↑{len(commits_ahead)} ↓{len(commits_behind)}", repo_path, output
                    elif commits_ahead:
                        return "AHEAD", f"{len(commits_ahead)} commits", repo_path, output
                    elif commits_behind:
                        return "BEHIND", f"{len(commits_behind)} commits", repo_path, output
                return "OK", "Up to date", repo_path, output
            except Exception:
                return "OK", "Up to date", repo_path, output

        if operation == "clean":
            if dry_run:
                output_prune = repo.git.fetch("--prune", "--dry-run")
                output_clean = repo.git.clean("-xfd", "-n")
                preview = f"{output_prune}\n{output_clean}".strip()
                return "SIMULATED", "[dry-run] clean", repo_path, preview if preview else "Nothing to remove."
            output_prune = repo.git.fetch("--prune")
            output_clean = repo.git.clean("-xfd")
            return "CLEANED", "Aggressive cleanup complete", repo_path, f"{output_prune}\n{output_clean}".strip()

        if operation == "pull":
            is_dirty = repo.is_dirty(untracked_files=True)
            
            if is_dirty and not autostash:
                return "CONFLICT", "Local changes prevent update", repo_path, "Commit your changes or enable --autostash"
                
            args = ["--ff-only"]
            if autostash:
                args.append("--autostash")
            output = repo.git.pull(*args)
            
            if is_dirty and autostash:
                return "STASH_RESTORED", "Changes synced and auto-stashed", repo_path, output

            return "OK", "", repo_path, output

        if operation == "checkout":
            if not target_branch:
                return "ERROR", "Operation failed", repo_path, "Missing target branch name. Use the -b flag."
            
            try:
                if not repo.head.is_detached and repo.active_branch.name == target_branch:
                    return "CLEAN", "Already on target branch", repo_path, ""
            except TypeError:
                pass
            
            if target_branch in [h.name for h in repo.heads]:
                repo.heads[target_branch].checkout()
                return "CHECKOUT", "Switched to local branch", repo_path, ""
            
            if "origin" in repo.remotes:
                origin = repo.remotes.origin
                remote_ref = f"{origin.name}/{target_branch}"
                refs = [r.name for r in origin.refs]
                if remote_ref in refs:
                    repo.create_head(target_branch, origin.refs[target_branch]).set_tracking_branch(origin.refs[target_branch]).checkout()
                    return "CHECKOUT", "Tracking remote branch", repo_path, ""
                    
            return "IGNORED", "Branch not found", repo_path, "Skipping repository"

        return "ERROR", "Unsupported operation", repo_path, ""

    except exc.GitCommandError as e:
        error_msg = parse_git_error(e)
        if not allow_prompt and ("Error de Autenticación" in error_msg):
            return "AUTH", "", repo_path, "Requiere configuración."

        if operation == "pull":
            if "Autostash conflict" in error_msg or "Conflicto de Autostash" in error_msg:
                return "STASH_CONFLICT", "Conflict restoring stash", repo_path, error_msg
            if "Pull conflict" in error_msg or "Conflicto de pull" in error_msg:
                return "CONFLICT", "Local changes prevent update", repo_path, error_msg
            if "Divergent branches" in error_msg or "Ramas divergentes" in error_msg:
                return "DIVERGENT", "Manual merge required", repo_path, error_msg

        return "ERROR", "Operation failed", repo_path, error_msg
    except Exception as e:
        return "ERROR", "Unexpected engine error", repo_path, str(e)


def get_repo_metadata(repo_path: str) -> dict:
    metadata = {"url": "", "branch": "", "error": ""}
    try:
        repo = Repo(repo_path)
        if repo.remotes:
            metadata["url"] = list(repo.remotes[0].urls)[0]
        if not repo.head.is_detached:
            metadata["branch"] = repo.active_branch.name
    except exc.InvalidGitRepositoryError:
        metadata["error"] = "Invalid or corrupted Git repository."
    except PermissionError:
        metadata["error"] = "Insufficient read permissions on the repository."
    except Exception as e:
        metadata["error"] = str(e)
    return metadata

def clone_repo(target_dir: str, repo_info: dict) -> Tuple[str, str, str, str]:
    url = repo_info.get("url")
    branch = repo_info.get("branch")
    
    if not url:
        return "ERROR", "Missing remote URL", target_dir, ""
        
    try:
        parent_dir = os.path.dirname(target_dir)
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except OSError:
                pass
                
        repo = Repo.clone_from(url, target_dir)
        if branch:
            repo.git.checkout(branch)
            
        return "OK", branch if branch else "default", target_dir, "Successfully cloned"
        
    except exc.GitCommandError as e:
        error_msg = parse_git_error(e)
        if "System conflict" in error_msg or "Conflicto de sistema" in error_msg:
            return "CLEAN", "Already exists", target_dir, ""
        return "ERROR", "", target_dir, error_msg
    except Exception as e:
        return "ERROR", "Critical exception during clone", target_dir, str(e)

def get_all_branches(repo_path: str) -> dict:
    data = {"current": "", "local": [], "remote_only": [], "error": ""}
    try:
        repo = Repo(repo_path)
        if not repo.head.is_detached:
            data["current"] = repo.active_branch.name
        data["local"] = [h.name for h in repo.heads]
        if repo.remotes:
            for r in repo.remotes:
                for ref in r.refs:
                    if ref.remote_head != 'HEAD':
                        if ref.remote_head not in data["local"]:
                            data["remote_only"].append(f"{r.name}/{ref.remote_head}")
    except exc.InvalidGitRepositoryError:
        data["error"] = "Invalid or corrupted Git repository."
    except PermissionError:
        data["error"] = "Insufficient read permissions on the repository."
    except Exception as e:
        data["error"] = str(e)
    return data