import os
from PySide6.QtCore import QThread, Signal
from concurrent.futures import ThreadPoolExecutor, as_completed

# Inject backend models
try:
    from model.scanner import find_git_repos
    from model.git_ops import run_git_operation
    from model.ci_ops import get_ci_status
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from model.scanner import find_git_repos
    from model.git_ops import run_git_operation
    from model.ci_ops import get_ci_status

class ScannerWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, root_path, parent=None):
        super().__init__(parent)
        self.root_path = root_path

    def run(self):
        try:
            repos = find_git_repos(self.root_path)
            self.finished.emit(repos)
        except Exception as e:
            self.error.emit(str(e))

class OperationWorker(QThread):
    """
    Executes a git operation asynchonously over multiple repositories
    using ThreadPoolExecutor, emitting results safely to the main GUI thread.
    """
    # (status, detail, repo_path, output)
    log_ready = Signal(str, str, str, str)
    # (processed_count)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, repos, operation, max_workers=10, kwargs=None, parent=None):
        super().__init__(parent)
        self.repos = repos
        self.operation = operation
        self.max_workers = max_workers
        self.kwargs = kwargs if kwargs is not None else {}

    def run(self):
        if not self.repos:
            self.finished.emit(0)
            return
            
        try:
            processed = 0
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for repo in self.repos:
                    if self.operation == "ci":
                        token = self.kwargs.get("token", "")
                        futures[executor.submit(get_ci_status, repo, token)] = repo
                    else:
                        futures[executor.submit(
                            run_git_operation,
                            repo,
                            self.operation,
                            False, 
                            self.kwargs.get('autostash', False),
                            self.kwargs.get('target_branch', None),
                            self.kwargs.get('dry_run', False)
                        )] = repo
                
                for future in as_completed(futures):
                    repo_path = futures[future]
                    
                    if self.operation == "ci":
                        # CI returns a dict: {"state": ..., "branch": ..., "reason": ...}
                        ci_data = future.result()
                        state = str(ci_data.get("state", "UNKNOWN")).upper()
                        reason = ci_data.get("reason", "")
                        branch = ci_data.get("branch", "")
                        # Map to expected signals: status, detail, repo_path, output
                        self.log_ready.emit(state, f"Branch: {branch}", repo_path, reason)
                    else:
                        status, detail, repo_path_res, output = future.result()
                        self.log_ready.emit(status, detail, repo_path_res, output)
                    processed += 1
                    
            self.finished.emit(processed)
        except Exception as e:
            self.error.emit(str(e))
