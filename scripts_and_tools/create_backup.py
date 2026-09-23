import shutil
from pathlib import Path

src_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
backup_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\backup_pre_rollout")

if backup_dir.exists():
    shutil.rmtree(backup_dir)

backup_dir.mkdir(parents=True, exist_ok=True)

# Copy static, routes, services
for sub in ["static", "routes", "services", "main.py", "start_server.py"]:
    src = src_dir / sub
    dst = backup_dir / sub
    if src.is_dir():
        shutil.copytree(src, dst)
    elif src.is_file():
        shutil.copy2(src, dst)

print("Backup created successfully at:", backup_dir)