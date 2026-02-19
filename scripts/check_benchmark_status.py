import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = r"E:\Python\MathProject_AST_Research\instance\benchmark.db"

def check_progress():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check runs in the last 2 hours
    two_hours_ago = (datetime.utcnow() - timedelta(hours=2)).isoformat()
    
    query = """
    SELECT 
        skill_name, 
        ablation_id, 
        COUNT(*) as count, 
        SUM(CASE WHEN fail_count > 0 THEN 1 ELSE 0 END) as failures,
        MAX(timestamp) as last_run
    FROM experiment_runs 
    WHERE timestamp > ?
    GROUP BY skill_name, ablation_id
    ORDER BY last_run DESC
    """
    
    cursor.execute(query, (two_hours_ago,))
    rows = cursor.fetchall()
    
    print(f"--- Benchmark Progress (Last 2 Hours) ---")
    if not rows:
        print("No runs recorded in the last 2 hours.")
    else:
        for row in rows:
            skill, ab, count, fails, last = row
            print(f"Skill: {skill} | Ablation: {ab} | Runs: {count} | Fails: {fails} | Last: {last}")

    conn.close()

if __name__ == "__main__":
    check_progress()
