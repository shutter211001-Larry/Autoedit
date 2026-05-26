import os
import sys
import chardet

src_srt = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Davines\260327_Mars\Subtitle 1.srt"

if os.path.exists(src_srt):
    try:
        # Detect encoding using chardet
        with open(src_srt, "rb") as f:
            raw_data = f.read(1000)
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            print(f"Detected Encoding: {encoding} with confidence {result['confidence']}")
        
        # Try reading with common encodings
        encodings_to_try = [encoding, "utf-8", "utf-16", "utf-16-le", "utf-16-be", "big5", "gbk"]
        for enc in encodings_to_try:
            if not enc: continue
            try:
                with open(src_srt, "r", encoding=enc) as f:
                    content = f.read()
                print(f"\nSuccessfully read with encoding '{enc}'! Total characters: {len(content)}")
                # Show first 15 lines of content
                lines = content.splitlines()
                print("First 15 lines:")
                for idx, line in enumerate(lines[:15]):
                    print(f"  {idx+1}: {line}")
                
                # Check if "我們會搭配" or "搭配" is in the content
                if "我們會搭配" in content or "搭配" in content or "暹羅貓" in content:
                    print("✨ MATCH FOUND IN THIS ENCODING!")
                    
                break
            except Exception as e:
                print(f"Failed with encoding '{enc}': {e}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("❌ Source file does not exist")
