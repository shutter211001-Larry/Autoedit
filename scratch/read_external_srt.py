import os
import sys

src_srt = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Davines\260327_Mars\Subtitle 1.srt"
dst_srt = r"c:\TEST\scratch\Subtitle_1.srt"

if os.path.exists(src_srt):
    try:
        with open(src_srt, "r", encoding="utf-8", errors="ignore") as f_in:
            content = f_in.read()
        with open(dst_srt, "w", encoding="utf-8") as f_out:
            f_out.write(content)
        print(f"✅ Successfully copied SRT file to {dst_srt}. Total characters: {len(content)}")
    except Exception as e:
        print(f"Error copying SRT file: {e}")
else:
    print(f"❌ Source SRT file does not exist: {src_srt}")
