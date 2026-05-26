import os
import sys

real_src = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Davines\Mars\Subtitle 1.srt"
dst = r"c:\TEST\scratch\Real_Subtitle_1.srt"

if os.path.exists(real_src):
    try:
        with open(real_src, "r", encoding="utf-8", errors="ignore") as f_in:
            content = f_in.read()
        with open(dst, "w", encoding="utf-8") as f_out:
            f_out.write(content)
        print(f"✅ Successfully copied REAL SRT. Total characters: {len(content)}")
        
        # Print first 20 lines
        lines = content.splitlines()
        print("First 20 lines:")
        for idx, line in enumerate(lines[:20]):
            print(f"  {idx+1}: {line}")
            
    except Exception as e:
        print(f"Error copying real SRT: {e}")
else:
    print(f"❌ Real SRT path does not exist: {real_src}")
