
import sqlite3
import os
import re
from datetime import datetime

db_path = r"E:\Python\MathProject_AST_Research\instance\benchmark_20260220_000857.db"
gen_code_dir = r"E:\Python\MathProject_AST_Research\agent_tools\reports\jh_數學2上_FourOperationsOfRadicals\gen_code"

if not os.path.exists(db_path):
    print(f"❌ DB not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Build a map of timestamp -> model from filenames in gen_code
# Filename pattern: radicals_..._genN_YYYYMMDD_HHMMSS_final.py
file_map = {}
if os.path.exists(gen_code_dir):
    for filename in os.listdir(gen_code_dir):
        if filename.endswith("_final.py"):
            # Extract timestamp from filename
            match = re.search(r'(\d{8}_\d{6})_final\.py', filename)
            if match:
                ts_str = match.group(1)
                full_path = os.path.join(gen_code_dir, filename)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        header = "".join(f.readlines()[:5])
                        m = re.search(r'# Model:\s*([^|#\n]+)', header)
                        if m:
                            model = m.group(1).strip()
                            file_map[ts_str] = model
                except:
                    pass

print(f"📂 Found {len(file_map)} unique timestamps in gen_code headers.")

# 2. Get all unknown runs
cursor.execute("SELECT run_id, timestamp, skill_name, ablation_id, sample_index FROM experiment_runs WHERE model_name='unknown'")
rows = cursor.fetchall()

print(f"🔧 Repairing {len(rows)} unknown entries...")

repaired_count = 0
for run_id, ts_iso, skill, ab_id, sample_idx in rows:
    # Convert ISO timestamp (2026-02-20T04:02:40.123) to filename format (20260220_040240)
    # Handle both T and space separator
    clean_ts = ts_iso.replace('T', ' ').split('.')[0]
    dt = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
    ts_key = dt.strftime("%Y%m%d_%H%M%S")
    
    if ts_key in file_map:
        model_name = file_map[ts_key]
        cursor.execute("UPDATE experiment_runs SET model_name=? WHERE run_id=?", (model_name, run_id))
        repaired_count += 1
        # print(f"  ✅ {ts_key} -> {model_name}")
    else:
        # Try a fuzzy match (offset by 1 second)
        # Sometimes file timestamp is slightly different from DB timestamp
        found_fuzzy = False
        for offset in [-1, 1, -2, 2]:
            dt_fuzzy = datetime.fromtimestamp(dt.timestamp() + offset)
            ts_fuzzy = dt_fuzzy.strftime("%Y%m%d_%H%M%S")
            if ts_fuzzy in file_map:
                model_name = file_map[ts_fuzzy]
                cursor.execute("UPDATE experiment_runs SET model_name=? WHERE run_id=?", (model_name, run_id))
                repaired_count += 1
                found_fuzzy = True
                break
        
        if not found_fuzzy:
            print(f"  ❌ No match for {ts_iso} ({ts_key})")

conn.commit()
conn.close()

print(f"🎉 Repair Complete! Repaired {repaired_count} entries.")
