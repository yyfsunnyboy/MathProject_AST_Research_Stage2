
import sqlite3
import os
from datetime import datetime

# Adjust path if needed
db_path = r'e:\Python\MathProject_AST_Research\instance\kumon_math.db'

print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    print("\n--- Recent 10 Experiment Logs ---")
    c.execute("""
        SELECT start_time, duration_seconds, prompt_len, code_len, model_name, is_success, total_tokens 
        FROM experiment_log 
        ORDER BY start_time DESC 
        LIMIT 10
    """)
    rows = c.fetchall()
    
    print(f"{'Time':<20} | {'Dur(s)':<8} | {'P_Len':<6} | {'C_Len':<6} | {'Tokens':<6} | {'Model':<20} | {'Success'}")
    print("-" * 100)
    for row in rows:
        # Convert timestamp if it's a float
        ts = row[0]
        try:
            dt = datetime.fromtimestamp(float(ts)).strftime('%H:%M:%S')
        except:
             dt = str(ts)
             
        dur = f"{row[1]:.1f}" if row[1] else "N/A"
        print(f"{dt:<20} | {dur:<8} | {row[2]:<6} | {row[3]:<6} | {row[6]:<6} | {row[4]:<20} | {row[5]}")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
