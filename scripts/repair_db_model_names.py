
import sqlite3
import os
import re

db_path = r"E:\Python\MathProject_AST_Research\instance\benchmark_20260220_000857.db"

if not os.path.exists(db_path):
    print(f"❌ DB not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all unknown runs
cursor.execute("SELECT run_id, source_code_path FROM experiment_runs WHERE model_name='unknown'")
rows = cursor.fetchall()

print(f"🔧 Repairing {len(rows)} unknown entries...")

repaired_count = 0
for run_id, code_path in rows:
    if not code_path or not os.path.exists(code_path):
        print(f"  ⚠️ Skipping {run_id}: File not found ({code_path})")
        continue
    
    try:
        with open(code_path, 'r', encoding='utf-8') as f:
            # Look at first 10 lines for "# Model: ..."
            header = "".join(f.readlines()[:10])
            model_match = re.search(r'#\s*Model:\s*([^|#\n]+)', header)
            
            if model_match:
                model_name = model_match.group(1).strip()
                # Update DB
                cursor.execute("UPDATE experiment_runs SET model_name=? WHERE run_id=?", (model_name, run_id))
                repaired_count += 1
                # print(f"  ✅ {run_id} -> {model_name}")
            else:
                print(f"  ❌ No Model header found in {code_path}")
                
    except Exception as e:
        print(f"  💥 Error processing {run_id}: {e}")

conn.commit()
conn.close()

print(f"🎉 Repair Complete! Repaired {repaired_count} entries.")
