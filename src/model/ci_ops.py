import urllib.request
import json
import re
from .git_ops import get_repo_metadata

def get_ci_status(repo_path: str, token: str) -> dict:
    """Consulte el estado asíncrono de los pipelines CI del head actual a la API de Github"""
    meta = get_repo_metadata(repo_path)
    url = meta.get("url", "")
    branch = meta.get("branch", "")
    
    if not url or not branch or "github.com" not in url:
        return {"state": "none", "branch": branch}
        
    # Extraemos recursivamente el nombre y proyecto limpiando el host SSH/HTTPS
    m = re.search(r'github\.com[:/](.+?)/(.+?)(\.git)?$', url)
    if not m:
        return {"state": "none", "branch": branch}
        
    owner, repo = m.groups()[:2]
    repo = repo.replace(".git", "")
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}/check-runs"
    req = urllib.request.Request(api_url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            if data.get("total_count", 0) == 0:
                return {"state": "none", "branch": branch}
            
            # Analizamos todos los tests de Integration corriendo simultáneamente
            runs = data.get("check_runs", [])
            conclusions = [r.get("conclusion") for r in runs if r.get("conclusion")]
            statuses = [r.get("status") for r in runs]
            
            if "in_progress" in statuses or "queued" in statuses:
                return {"state": "pending", "branch": branch}

            if "failure" in conclusions or "timed_out" in conclusions or "action_required" in conclusions or "cancelled" in conclusions:
                return {"state": "failure", "branch": branch}

            if len(conclusions) > 0 and all(c == "success" for c in conclusions):
                return {"state": "success", "branch": branch}
                
            return {"state": "none", "branch": branch}
            
    except Exception:
        return {"state": "error", "branch": branch}
