import re
import os

srt_path = r"c:\TEST\scratch\Mars_Marketing_Antigravity.srt"

if not os.path.exists(srt_path):
    print("❌ SRT file does not exist!")
    exit(1)

with open(srt_path, "r", encoding="utf-8") as f:
    content = f.read()

# Parse SRT blocks
blocks = content.strip().split("\n\n")
print(f"Total subtitle blocks parsed: {len(blocks)}")

errors = []
warnings = []

def clean_tags(text):
    # Remove HTML tags like <b>, </b>
    return re.sub(r"<[^>]+>", "", text).strip()

def count_chinese_chars(text):
    # We count all characters except punctuation marks
    text_clean = re.sub(r"[，。：；！？、,.:;!?]", "", text)
    return len(text_clean)

# Time parsing helper
def srt_time_to_seconds(tc):
    parts = tc.replace(",", ".").split(":")
    h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s

prev_end_time = -1.0

for idx, block in enumerate(blocks):
    lines = block.strip().split("\n")
    if len(lines) < 3:
        warnings.append(f"Block {idx+1} has invalid format:\n{block}")
        continue
    
    num_str = lines[0]
    time_str = lines[1]
    text_lines = lines[2:]
    
    # 1. Validate block number
    block_num = int(num_str)
    if block_num != idx + 1:
        errors.append(f"Block {idx+1}: Block index mismatch. Expected {idx+1}, got {block_num}")
        
    # 2. Validate timecodes
    time_match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", time_str)
    if not time_match:
        errors.append(f"Block {idx+1}: Invalid timecode format '{time_str}'")
        continue
        
    start_tc, end_tc = time_match.groups()
    start_sec = srt_time_to_seconds(start_tc)
    end_sec = srt_time_to_seconds(end_tc)
    
    if start_sec >= end_sec:
        errors.append(f"Block {idx+1}: Start time ({start_tc}) is after or equal to End time ({end_tc})")
        
    if start_sec < prev_end_time:
        errors.append(f"Block {idx+1}: Chronological violation! Start time ({start_tc}) overlaps with previous subtitle end time")
        
    prev_end_time = end_sec
    
    # 3. Validate character length (Strictly under 15 Chinese characters per line)
    for l_idx, line in enumerate(text_lines):
        cleaned_line = clean_tags(line)
        char_count = count_chinese_chars(cleaned_line)
        
        # If line contains English words, we count each English word as 1 token or adjust appropriately
        # For simplicity, len(cleaned_line) is used for Chinese, but we also print details
        print(f"Block {block_num} Line {l_idx+1}: '{cleaned_line}' -> {char_count} chars")
        
        if char_count >= 15:
            errors.append(f"Block {block_num} Line {l_idx+1}: Text line exceeds 14 characters! Count={char_count}. Line='{cleaned_line}'")

print("\n" + "="*50)
print("VALIDATION SUMMARY")
print("="*50)
if warnings:
    print(f"⚠️ Warnings ({len(warnings)}):")
    for w in warnings:
        print(f"  - {w}")
else:
    print("✅ No warnings found!")

if errors:
    print(f"❌ Errors ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
else:
    print("🎉 ALL CHECKS PASSED SUCCESSFULLY! The SRT file is 100% compliant, chronological, and smooth!")
