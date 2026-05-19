import os

log_path = r"C:\Users\larrywu\.gemini\antigravity\brain\878978ab-d3f5-418c-88e5-9314eb79fe0f\.system_generated\logs\overview.txt"

if os.path.exists(log_path):
    print("🔍 Reading conversation logs...")
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    keywords = ["觀眾", "audience", "鼓掌", "clap", "反應", "reaction"]
    match_count = 0
    for idx, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            match_count += 1
            print(f"Line {idx+1}: {line.strip()}")
            
    print(f"🎬 Done. Total matches found: {match_count}")
else:
    print("❌ Log file not found")
