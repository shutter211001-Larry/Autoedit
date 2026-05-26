import os

base_dir = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Davines"
if os.path.exists(base_dir):
    print(f"Directory exists: {base_dir}")
    try:
        items = os.listdir(base_dir)
        for item in sorted(items):
            path = os.path.join(base_dir, item)
            is_dir = os.path.isdir(path)
            print(f" - {'📁' if is_dir else '📄'} {item}")
            if is_dir:
                try:
                    subitems = os.listdir(path)
                    for sub in sorted(subitems):
                        print(f"     - {sub}")
                except Exception:
                    pass
    except Exception as e:
        print(f"Error listing: {e}")
else:
    print(f"❌ Directory does not exist: {base_dir}")
