import os

log_path = r"C:\Users\larrywu\.gemini\antigravity\brain\878978ab-d3f5-418c-88e5-9314eb79fe0f\.system_generated\logs\overview.txt"

if os.path.exists(log_path):
    print("🔍 Reading conversation logs header...")
    with open(log_path, "r", encoding="utf-8") as f:
        for idx in range(100):
            line = f.readline()
            if not line: break
            print(f"Line {idx+1}: {line.strip()[:180]}")
else:
    print("❌ Log file not found")
