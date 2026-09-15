import os
import shutil
import zipfile
from pathlib import Path

def build_plugins():
    source_dir = Path("plugins")
    dest_dir = Path("core/dev_data/plugins")

    if not source_dir.exists():
        print("Source directory 'plugins' not found.")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)

    for plugin_path in source_dir.iterdir():
        if plugin_path.is_dir() and (plugin_path / "manifest.json").exists():
            plugin_name = plugin_path.name
            zip_filename = dest_dir / f"{plugin_name}.hm"

            print(f"Packaging {plugin_name} into {zip_filename}...")

            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(plugin_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(plugin_path)
                        zipf.write(file_path, arcname)

if __name__ == "__main__":
    build_plugins()
