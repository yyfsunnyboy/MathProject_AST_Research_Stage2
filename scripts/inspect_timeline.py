
import sqlite3
import pandas as pd
import os

db_path = r"E:\Python\MathProject_AST_Research\instance\benchmark_20260220_000857.db"
output_file = r"E:\Python\MathProject_AST_Research\scripts\timeline_dump.txt"

conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT timestamp, model_name, ablation_id, sample_index, run_id FROM experiment_runs ORDER BY timestamp", conn)
conn.close()

with open(output_file, "w", encoding="utf-8") as f:
    f.write(df.to_string())

print(f"Dumped to {output_file}")
