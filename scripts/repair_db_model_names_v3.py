
import sqlite3
import os
import re
from datetime import datetime, timedelta

db_path = r"E:\Python\MathProject_AST_Research\instance\benchmark_20260220_000857.db"
gen_code_dir = r"E:\Python\MathProject_AST_Research\agent_tools\reports\jh_數學2上_FourOperationsOfRadicals\gen_code"

if not os.path.exists(db_path):
    print(f"❌ DB not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Build a map of (ablation_id, sample_index, repetition) -> model
# We'll use the timestamp as a secondary filter
# Filename pattern: radicals_L{level}_ab{ab}_gen{rep}_{ts}_final.py
file_records = []
if os.path.exists(gen_code_dir):
    for filename in os.listdir(gen_code_dir):
        if filename.endswith("_final.py"):
            # radicals_L1_ab1_gen1_20260220_040240_final.py
            match = re.search(r'L(\d+)_ab(\d+)_gen(\d+)_(\d{8}_\d{6})_final\.py', filename)
            if match:
                level = int(match.group(1))
                ab_id = int(match.group(2))
                rep_i = int(match.group(3)) # 1-indexed
                ts_str = match.group(4)
                
                full_path = os.path.join(gen_code_dir, filename)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        header = "".join(f.readlines()[:10])
                        m = re.search(r'# Model:\s*([^|#\n]+)', header)
                        if m:
                            model = m.group(1).strip()
                            # We don't have 'idx' directly in filename, but 'gen' is the repetition index.
                            # WAIT: In benchmark.py, 'gen1' for 'idx=0' or what?
                            # Let's look at the timeline. 
                            # Usually repeat_count is how many files per CASE.
                            # So for idx=0, we have gen1, gen2... gen5.
                            file_records.append({
                                'ab_id': ab_id,
                                'rep_i': rep_i,
                                'ts_key': ts_str,
                                'model': model,
                                'filename': filename
                            })
                except:
                    pass

print(f"📂 Found {len(file_records)} records in gen_code.")

# 2. Get all unknown runs
cursor.execute("SELECT run_id, timestamp, ablation_id, sample_index FROM experiment_runs WHERE model_name='unknown'")
rows = cursor.fetchall()

print(f"🔧 Repairing {len(rows)} unknown entries...")

repaired_count = 0
for run_id, ts_iso, ab_id, sample_idx in rows:
    # Convert ISO timestamp (UTC) to datetime
    clean_ts = ts_iso.replace('T', ' ').split('.')[0]
    dt_utc = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
    # Convert to Local (UTC+8)
    dt_local = dt_utc + timedelta(hours=8)
    ts_local_key = dt_local.strftime("%Y%m%d_%H%M%S")
    
    # Try to find a match in file_records
    # Match criteria: ablation_id matches + timestamp is very close (+/- 60 seconds)
    found_match = None
    for rec in file_records:
        if rec['ab_id'] == ab_id:
            # Parse record timestamp
            rec_dt = datetime.strptime(rec['ts_key'], "%Y%m%d_%H%M%S")
            diff = abs((rec_dt - dt_local).total_seconds())
            if diff < 120: # 2 minutes buffer
                found_match = rec
                break
    
    if found_match:
        model_name = found_match['model']
        cursor.execute("UPDATE experiment_runs SET model_name=? WHERE run_id=?", (model_name, run_id))
        repaired_count += 1
        # print(f"  ✅ {ts_iso} (Local {ts_local_key}) -> {model_name} (via {found_match['filename']})")
    else:
        # print(f"  ❌ No match for {ts_iso} (Local {ts_local_key}) ab_id={ab_id}")
        pass

conn.commit()
conn.close()

print(f"🎉 Repair Complete! Repaired {repaired_count} entries.")
