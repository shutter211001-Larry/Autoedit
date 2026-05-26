import os
import sys

target_dir = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Davines\260327_Mars"
if os.path.exists(target_dir):
    print(f"Directory exists: {target_dir}")
    try:
        files = os.listdir(target_dir)
        print(f"Total files in directory: {len(files)}")
        for f in sorted(files):
            print(f" - {f}")
    except Exception as e:
        print(f"Error listing files: {e}")
else:
    print(f"❌ Directory does not exist: {target_dir}")
