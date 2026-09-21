import subprocess
import time
import urllib.request
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PY_EXE = r"C:\Users\Pc\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe"

if not os.path.exists(PY_EXE):
    PY_EXE = r"C:\Users\Pc\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"

def is_server_running(port=8002):
    try:
        req = urllib.request.urlopen(f"http://localhost:{port}/api/templates", timeout=1.5)
        return req.status == 200
    except Exception:
        return False

def kill_existing_on_port(port=8002):
    try:
        output = subprocess.check_output("netstat -ano", shell=True).decode()
        for line in output.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                time.sleep(1)
    except Exception:
        pass

def open_browser():
    try:
        # Open default browser without console window
        subprocess.Popen(["explorer.exe", "http://localhost:8002"])
    except Exception:
        pass

def start_daemon():
    if is_server_running(8002):
        open_browser()
        return True

    kill_existing_on_port(8002)

    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200

    log_path = str(BASE_DIR / "server_run.log")
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND)

    proc = subprocess.Popen(
        [PY_EXE, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"],
        cwd=str(BASE_DIR),
        stdout=fd,
        stderr=fd,
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True
    )

    for attempt in range(12):
        time.sleep(1)
        if is_server_running(8002):
            open_browser()
            return True

    return False

if __name__ == "__main__":
    start_daemon()
