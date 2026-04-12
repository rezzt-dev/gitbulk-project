"""
Safe archiving module for GitBulk.
Handles moving repositories to a hidden archive folder instead of deletion.
"""

import os
import shutil
import json
from datetime import datetime

def archive_repository(repo_path: str, root_dir: str) -> tuple[bool, str]:
    """
    Moves a repository to the .gitbulk_archive folder.
    
    Args:
        repo_path: Absolute path to the repository to archive.
        root_dir: The root directory of the workspace.
        
    Returns:
        A tuple of (success: bool, detail: str)
    """
    try:
        archive_root = os.path.join(root_dir, ".gitbulk_archive")
        if not os.path.exists(archive_root):
            os.makedirs(archive_root, exist_ok=True)
            
        repo_name = os.path.basename(repo_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{repo_name}_{timestamp}"
        target_path = os.path.join(archive_root, archive_name)
        
        # Metadata for recovery
        meta = {
            "original_path": repo_path,
            "archived_at": datetime.now().isoformat(),
            "repo_name": repo_name
        }
        
        # 1. Move the repository
        shutil.move(repo_path, target_path)
        
        # 2. Add metadata file inside the archived folder
        with open(os.path.join(target_path, ".gitbulk_archive_info.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)
            
        return True, f"Archived as {archive_name}"
        
    except Exception as e:
        return False, str(e)
