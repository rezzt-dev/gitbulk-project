import os
import sys
import subprocess
import tempfile

def open_external_editor(initial_text="", repo_context=None):
    """
    Opens the system's default text editor with a temporary file.
    Returns the edited text or None if the editor was closed without saving/empty.
    """
    # 1. Determine the editor command
    # Priority: Env Var EDITOR > Env Var VISUAL > Platform Specific Default
    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')
    if not editor:
        if os.name == 'nt': # Windows
            editor = 'notepad.exe'
        else: # Linux / macOS
            # Common defaults
            for cmd in ['nano', 'vim', 'vi', 'gedit']:
                if subprocess.call(['which', cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    editor = cmd
                    break
            editor = editor or 'vi'

    # 2. Prepare instructions header (commented out)
    header = ""
    if repo_context:
        header = (
            f"# Editing commit message for: {os.path.basename(repo_context)}\n"
            "# Lines starting with '#' will be ignored.\n"
            "# Please enter your message, save and exit.\n"
            "# --------------------------------------------------\n"
        )
    
    full_initial_content = header + initial_text

    # 3. Create temp file
    # We use .gitbulk_commit_msg.txt for better identification
    fd, path = tempfile.mkstemp(suffix=".gitbulk_commit.txt", text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
            tmp.write(full_initial_content)
        
        # 4. Launch editor
        # subprocess.call is blocking, which is what we want
        try:
            subprocess.call([editor, path])
        except Exception as e:
            # Fallback for Windows if notepad.exe was not in path (rare)
            if os.name == 'nt' and editor == 'notepad.exe':
                 subprocess.call(['notepad', path])
            else:
                raise e
        
        # 5. Read back text
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Clean lines starting with '#'
        cleaned_lines = [l for l in lines if not l.strip().startswith('#')]
        final_text = "".join(cleaned_lines).strip()
        
        return final_text if final_text else None

    finally:
        # 6. Cleanup
        if os.path.exists(path):
            os.remove(path)

def get_cli_input(prompt, options=None):
    """Simple wrapper for cross-py2/3 compatibility if needed (not here) and centralizing prompts."""
    if options:
        prompt = f"{prompt} ({'/'.join(options)}) "
    
    val = input(prompt).lower().strip()
    return val if val else (options[0] if options else "")
