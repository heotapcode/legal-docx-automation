import subprocess
import time

def stop_server(port=8002):
    try:
        output = subprocess.check_output("netstat -ano", shell=True).decode()
        killed = False
        for line in output.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                print(f"Đã dừng máy chủ cổng {port} (PID {pid}).")
                killed = True
        if not killed:
            print(f"Không có máy chủ nào đang chạy trên cổng {port}.")
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    stop_server(8002)
