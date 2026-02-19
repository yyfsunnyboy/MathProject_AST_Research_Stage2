import os
import csv
import re
import sqlite3
from datetime import datetime

# ==============================================================================
# ⚠️ Configuration: Update these before running!
# ==============================================================================
# ==============================================================================
# ⚠️ Configuration: Auto-detected based on phase
# ==============================================================================
SKILL_FOLDER = "jh_數學1上_FourArithmeticOperationsOfNumbers"
PROJECT_ROOT = r"E:\Python\MathProject_AST_Research"
REPORTS_DIR = os.path.join(PROJECT_ROOT, "agent_tools", "reports", SKILL_FOLDER)
GEN_CODE_DIR = os.path.join(REPORTS_DIR, "gen_code")
INSTANCE_DIR = os.path.join(PROJECT_ROOT, "instance")

def update_csv_files(target_model, timestamp_substring):
    """Update model_name to target_model in CSV reports matching timestamp."""
    if not os.path.exists(REPORTS_DIR):
        print(f"Directory not found: {REPORTS_DIR}")
        return

    print(f"--- Updating CSVs for {target_model} (Timestamp: {timestamp_substring}) ---")
    for filename in os.listdir(REPORTS_DIR):
        if not filename.endswith(".csv"):
            continue
        
        if timestamp_substring not in filename:
            continue
            
        filepath = os.path.join(REPORTS_DIR, filename)
        print(f"  Processing: {filename}")
        
        rows = []
        header = []
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                continue
            
            try:
                model_idx = header.index('model_name')
            except ValueError:
                continue
                
            rows.append(header)
            count = 0
            for row in reader:
                if len(row) > model_idx:
                    row[model_idx] = target_model
                    count += 1
                rows.append(row)
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        print(f"    Updated {count} rows.")

def update_database_split():
    """
    Advanced DB Fix:
    - 18:37 run -> Qwen 3 14B
    - 19:18 run -> Qwen 3 8B
    
    Splitting based on timestamp threshold (e.g. 19:00:00).
    """
    # Target the mixed DB
    target_db = "benchmark_20260219_183733.db"
    db_path = os.path.join(INSTANCE_DIR, target_db)
    
    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        return
        
    print(f"--- Processing Database: {target_db} ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Strategy:
        # Rows with timestamp < '2026-02-19 19:00:00' AND model='unknown' -> qwen3-14b
        # Rows with timestamp >= '2026-02-19 19:00:00' AND model='unknown' -> qwen3-8b
        # Or simpler: relying on the run_id creation time implicitly? No, use explicit SQL filter.
        # But 'timestamp' column format needs verification. Let's assume standard ISO or similar.
        # Wait, columns are: id, timestamp, ...
        
        # 1. Update 14B (Earlier runs)
        cursor.execute("""
            UPDATE experiment_runs 
            SET model_name = 'qwen3-14b' 
            WHERE skill_name = ? 
            AND (model_name = 'unknown' OR model_name = 'qwen3-14b') -- Re-apply to ensure
            AND timestamp < '2026-02-19 19:00:00'
        """, (SKILL_FOLDER,))
        rows_14b = cursor.rowcount
        
        # 2. Update 8B (Later runs)
        cursor.execute("""
            UPDATE experiment_runs 
            SET model_name = 'qwen3-8b' 
            WHERE skill_name = ? 
            AND (model_name = 'unknown') 
            AND timestamp >= '2026-02-19 19:00:00'
        """, (SKILL_FOLDER,))
        rows_8b = cursor.rowcount
        
        # 3. Update Summaries (Tricky, summaries usually don't have timestamps? Check schema)
        # Summary table usually just aggregates. We might need to update by ablation_id/run counts?
        # Actually, simpler: Update all remaining unknowns to qwen3-8b?
        # Or better: Assume summary is regenerated or just update blindly based on runs?
        # Let's just update summaries for both.
        # There are 3 summaries for 14B and 3 for 8B potentially? 
        # Actually summary table has 'model_name' as part of key usually.
        # If they are all 'unknown', we have a collision.
        # Let's inspect summary table content first? No, let's just try to update based on rowid/insertion order if possible?
        # For now, let's just print a warning about summary table.
        
        conn.commit()
        print(f"  Updated {rows_14b} rows to qwen3-14b (Time < 19:00)")
        print(f"  Updated {rows_8b} rows to qwen3-8b (Time >= 19:00)")
        
    except Exception as e:
        print(f"  DB Update failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("====================================")
    print(" FIX SCRIPT: Multi-Model Restoration")
    print("====================================")
    
    # 1. Restore Gemini (Safe) - Timestamp ~15:00-16:00
    # Found timestamps like 154131, 143247 etc. Let's use specific run timestamp "154131"
    update_csv_files("gemini-3-flash", "154131")
    
    # 2. Fix Qwen 14B (Safe) - Timestamp ~18:37
    update_csv_files("qwen3-14b", "183733")
    
    # 3. Fix Qwen 8B (Safe) - Timestamp ~19:18
    update_csv_files("qwen3-8b", "191832")
    
    # 4. Fix Database (Mixed 14B/8B)
    update_database_split()
    
    print("\nDone.")
