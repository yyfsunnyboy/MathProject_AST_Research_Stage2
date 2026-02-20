
import sqlite3
import os

db_path = r"E:\Python\MathProject_AST_Research\instance\benchmark_20260220_000857.db"

if not os.path.exists(db_path):
    print(f"❌ DB not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get 10 entries with unknown model name
cursor.execute("SELECT run_id, model_name, source_code_path FROM experiment_runs WHERE model_name='unknown' LIMIT 10")
rows = cursor.fetchall()

print(f"🔍 Found {len(rows)} samples with model_name='unknown':")
for row in rows:
    print(f"Run ID: {row[0]}")
    print(f"Model: {row[1]}")
    print(f"Path:  {row[2]}")
    print("-" * 50)

conn.close()
