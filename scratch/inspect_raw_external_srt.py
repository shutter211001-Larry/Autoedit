import os
import sys

src_srt = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Davines\260327_Mars\Subtitle 1.srt"

if not os.path.exists(src_srt):
    print(f"❌ Original file does not exist: {src_srt}")
    sys.exit(1)

print(f"File exists: {src_srt}")
size = os.path.getsize(src_srt)
print(f"File size: {size} bytes")

# Read with various encodings
for enc in ["utf-16", "utf-16-le", "utf-8", "big5", "gbk"]:
    try:
        with open(src_srt, "r", encoding=enc) as f:
            content = f.read()
        print(f"Successfully read with {enc}! Total characters: {len(content)}")
        lines = content.splitlines()
        print("First 30 lines of the file:")
        for idx, line in enumerate(lines[:30]):
            print(f"  {idx+1}: {line}")
        break
    except Exception as e:
        print(f"Failed with {enc}: {e}")
