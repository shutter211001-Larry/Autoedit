import os
import sys

srt_path = r"c:\TEST\scratch\Subtitle_1.srt"

if not os.path.exists(srt_path):
    print("❌ Subtitle_1.srt does not exist!")
    sys.exit(1)

with open(srt_path, "r", encoding="utf-8") as f:
    content = f.read()

print(f"Read {len(content)} characters.")

search_terms = ["新羅貓", "暹羅貓", "搭配", "我們會", "特分立", "髮色"]
for term in search_terms:
    count = content.count(term)
    print(f"Term '{term}': {count} occurrences")
    if count > 0:
        # Find all lines containing this term
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if term in line:
                print(f"  Line {idx+1}: {line.strip()}")
