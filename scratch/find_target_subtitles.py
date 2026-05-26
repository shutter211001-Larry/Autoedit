import os
import sys
import glob

search_text = "我們會搭配"
search_text_alt = "搭配"
search_text_alt2 = "暹羅貓的髮色"

directories = [
    r"c:\TEST",
    r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Davines\260327_Mars"
]

print(f"🔍 Searching for '{search_text}' or '{search_text_alt2}'...")

found = False

for base_dir in directories:
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        continue
    print(f"Scanning directory: {base_dir}...")
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith((".srt", ".txt", ".json", ".py", ".md")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines):
                        if search_text in line or search_text_alt2 in line:
                            print(f"✨ Match found in {file_path} (Line {idx+1}):")
                            print(f"  👉 {line.strip()}")
                            found = True
                except Exception as e:
                    pass

if not found:
    print("❌ No matching text found in any files.")
