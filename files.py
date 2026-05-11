import os
import shutil
from pathlib import Path

# Project Root Resolution
PROJECT_ROOT = Path(__file__).parent.resolve()

def resolve_path(filepath):
    """Utility to resolve paths relative to project root if they are not absolute."""
    path = Path(os.path.expanduser(filepath))
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path

def read_file(filepath):
    """Read file content with cross-platform path handling."""
    path = resolve_path(filepath)
    if not path.exists():
        return None, f"File not found: {path}"
    
    try:
        with path.open("r", encoding="utf-8") as f:
            content = f.read(3000)
            if len(content) >= 3000:
                content += "\n... [truncated]"
            return content, None
    except Exception as e:
        return None, str(e)

def write_file(filepath, content):
    """Write file content with cross-platform path handling."""
    path = resolve_path(filepath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {path.stat().st_size} bytes to {path}", None
    except Exception as e:
        return None, str(e)

def find_files(pattern, start_path="."):
    """Cross-platform recursive file search (defaults to project root)."""
    try:
        root = resolve_path(start_path)
        matches = []
        for p in root.rglob(pattern):
            matches.append(str(p))
            if len(matches) >= 20:
                break
        
        if not matches:
            return "No results found.", None
        return "\n".join(matches), None
    except Exception as e:
        return None, str(e)

def list_dir(path="."):
    """Cross-platform directory listing (defaults to project root)."""
    target_path = resolve_path(path)
    if not target_path.exists():
        return None, f"Path not found: {target_path}"
    
    try:
        summary = f"📁 **Contents of {target_path}:**\n\n"
        for item in target_path.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            item_size = item.stat().st_size if item.is_file() else "-"
            summary += f"- [{item_type}] {item.name} ({item_size} bytes)\n"
        return summary, None
    except Exception as e:
        return None, str(e)

def copy_file(src, dst):
    """Cross-platform file copy."""
    try:
        shutil.copy2(resolve_path(src), resolve_path(dst))
        return f"Copied {src} to {dst}", None
    except Exception as e:
        return None, str(e)

def move_file(src, dst):
    """Cross-platform file move/rename."""
    try:
        shutil.move(resolve_path(src), resolve_path(dst))
        return f"Moved {src} to {dst}", None
    except Exception as e:
        return None, str(e)

def remove_file(filepath):
    """Cross-platform file removal."""
    try:
        path = resolve_path(filepath)
        if path.is_dir():
            shutil.rmtree(path)
            return f"Removed directory {filepath}", None
        else:
            path.unlink()
            return f"Removed file {filepath}", None
    except Exception as e:
        return None, str(e)

# === ALIASES FOR AI.PY ===
def read_file_content(path: str) -> str:
    content, error = read_file(path)
    if error:
        return f"Error: {error}"
    return content

def write_file_content(path: str, content: str) -> str:
    result, error = write_file(path, content)
    if error:
        return f"Error: {error}"
    return result
