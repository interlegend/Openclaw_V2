import os
import subprocess

def read_file(filepath):
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return None, "File not found."
    
    try:
        with open(filepath, "r") as f:
            content = f.read(3000)
            if len(content) >= 3000:
                content += "\n... [truncated]"
            return content, None
    except Exception as e:
        return None, str(e)

def write_file(filepath, content):
    filepath = os.path.expanduser(filepath)
    try:
        with open(filepath, "w") as f:
            f.write(content)
        byte_count = os.path.getsize(filepath)
        return f"Successfully wrote {byte_count} bytes to {filepath}", None
    except Exception as e:
        return None, str(e)

def find_files(pattern):
    try:
        # find ~ -name "<pattern>" 2>/dev/null
        command = f"find ~ -name '{pattern}' 2>/dev/null | head -n 20"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip() or "No results found.", None
    except Exception as e:
        return None, str(e)

def list_dir(path="~"):
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return None, "Path not found."
    
    try:
        items = os.listdir(path)
        summary = f"📁 **Contents of {path}:**\n\n"
        for item in items:
            item_path = os.path.join(path, item)
            item_type = "DIR" if os.path.isdir(item_path) else "FILE"
            item_size = os.path.getsize(item_path) if item_type == "FILE" else "-"
            summary += f"- [{item_type}] {item} ({item_size} bytes)\n"
        return summary, None
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
