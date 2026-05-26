import os
import sys

src_srt = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Davines\260327_Mars\Subtitle 1.srt"

if os.path.exists(src_srt):
    try:
        with open(src_srt, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.splitlines()
        
        search_terms = ["我們會搭配", "我們會", "搭配", "暹羅貓"]
        
        for term in search_terms:
            print(f"\n🔍 Searching for '{term}'...")
            found_count = 0
            for idx, line in enumerate(lines):
                if term in line:
                    print(f"  👉 Line {idx+1}: {line.strip()}")
                    found_count += 1
            if found_count == 0:
                print("  ❌ No matches")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("❌ Source file does not exist")
