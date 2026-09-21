import os, shutil
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word")
TPL_DIR = BASE_DIR / "webapp_v2" / "templates"

def sync_all():
    print("=== SYNCING ALL 19 KITS TO ROOT MẪU DIRECTORIES ===")
    synced_kits = 0
    total_files = 0

    for kit_dir in sorted(TPL_DIR.iterdir()):
        if not kit_dir.is_dir():
            continue

        clean_name = kit_dir.name
        # Find matching root folder
        target_dir = BASE_DIR / f"Mẫu {clean_name}"
        if not target_dir.exists():
            # Check for slight naming differences
            for item in BASE_DIR.iterdir():
                if item.is_dir() and item.name.startswith("Mẫu ") and clean_name.lower().replace(" ", "") in item.name.lower().replace(" ", ""):
                    target_dir = item
                    break

        if target_dir.exists():
            count = 0
            for f in kit_dir.glob("*.docx"):
                if f.name.startswith(("~$", "_")):
                    continue
                shutil.copy2(f, target_dir / f.name)
                count += 1
                total_files += 1
            synced_kits += 1
            print(f"✅ Synced {kit_dir.name} ({count} files) -> {target_dir.name}")
        else:
            print(f"⚠️ Target root dir not found for: {clean_name}")

    print(f"\nCompleted syncing {synced_kits} kits ({total_files} docx files)!")

if __name__ == "__main__":
    sync_all()
