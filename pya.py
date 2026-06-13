import os
import sys
from pathlib import Path

EXCLUDED_DIRS = {
    '__pycache__', '.git', '.env', 'venv', 'env', '.venv', '.idea', '.vscode',
    'node_modules', 'dist', 'build', 'logs', 'temp', 'tmp', '.pytest_cache'
}
BINARY_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.pyc', '.pyo', '.class', '.jar',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.jpg', '.jpeg', '.png', '.gif',
    '.bmp', '.ico', '.mp3', '.mp4', '.avi', '.mov', '.pdf', '.doc', '.docx',
    '.xls', '.xlsx', '.ppt', '.pptx', '.bin', '.dat', '.db', '.sqlite'
}

def is_text_file(file_path):
    """Return True if file is likely text (not binary)."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return False
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return False
        return True
    except:
        return False

def should_skip(path):
    """Check if path should be excluded (directory or file)."""
    parts = Path(path).parts
    for part in parts:
        if part in EXCLUDED_DIRS:
            return True
    return False

def generate_tree_and_content(root_dir, output_file=None):
    """Walk root_dir, print tree and then each file's content."""
    root_dir = os.path.abspath(root_dir)
    if output_file is None:
        output_file = os.path.join(root_dir, 'folder_report.txt')

    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(f"# Report for: {root_dir}\n\n")
        out.write("## Folder Structure\n```\n")
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
            if should_skip(dirpath):
                continue
            level = dirpath.replace(root_dir, '').count(os.sep)
            indent = '│   ' * level
            out.write(f"{indent}├── {os.path.basename(dirpath)}/\n")
            subindent = '│   ' * (level + 1)
            for f in sorted(filenames):
                full_path = os.path.join(dirpath, f)
                if should_skip(full_path) or not is_text_file(full_path):
                    continue
                out.write(f"{subindent}├── {f}\n")
        out.write("```\n\n")

        out.write("## File Contents\n\n")
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
            if should_skip(dirpath):
                continue
            for f in sorted(filenames):
                full_path = os.path.join(dirpath, f)
                if should_skip(full_path) or not is_text_file(full_path):
                    continue
                rel_path = os.path.relpath(full_path, root_dir)
                out.write(f"\n[file name]: {rel_path}\n")
                out.write("[file content begin]\n")
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as fc:
                        content = fc.read()
                    out.write(content)
                    if not content.endswith('\n'):
                        out.write('\n')
                except Exception as e:
                    out.write(f"[ERROR reading file: {e}]\n")
                out.write("[file content end]\n")

    print(f"Report saved to: {output_file}")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    generate_tree_and_content(target)