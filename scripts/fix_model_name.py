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

def update_database_explicit():
    """Explicitly update specific DB files to specific models."""
    targets = [
        # (DB Filename, Target Model)
        ("benchmark_20260219_154131.db", "qwen3-14b"),  # Early Qwen Run
        ("benchmark_20260219_183733.db", "qwen3-8b"),   # Late Qwen Run
        ("benchmark_20260219_142702.db", "gemini-3-flash") # Earliest Run
    ]
    
    for db_name, target_model in targets:
        db_path = os.path.join(INSTANCE_DIR, db_name)
        if not os.path.exists(db_path):
            print(f"Skipping DB (not found): {db_name}")
            continue
            
        print(f"--- Processing Database: {db_name} -> {target_model} ---")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Update 'experiment_runs' table
            cursor.execute(
                "UPDATE experiment_runs SET model_name = ? WHERE skill_name = ?", 
                (target_model, SKILL_FOLDER)
            )
            updated_rows_runs = cursor.rowcount
            
            # Update 'ablation_summary' table if it exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ablation_summary'")
            if cursor.fetchone():
                 cursor.execute(
                    "UPDATE ablation_summary SET model_name = ? WHERE skill_name = ?",
                    (target_model, SKILL_FOLDER)
                )
                 updated_rows_summary = cursor.rowcount
            else:
                 updated_rows_summary = 0
                 
            conn.commit()
            print(f"  Updated {updated_rows_runs} runs / {updated_rows_summary} summaries.")
             
        except Exception as e:
            print(f"  Database update failed: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    print("====================================")
    print(" FIX SCRIPT: Explicit Model Restoration")
    print("====================================")
    
    # 1. Fix Gemini (Earliest) ~14:27
    update_csv_files("gemini-3-flash", "142702")
    update_csv_files("gemini-3-flash", "143247")
    
    # 2. Fix Qwen 14B (Early) ~15:41
    # [CORRECTION] Previous run labelled this Gemini, restoring to 14B
    update_csv_files("qwen3-14b", "154131")
    
    # 3. Fix Qwen 8B (Late) ~18:37 & 19:18
    # [CORRECTION] Previous run labelled 183733 as 14B, correcting to 8B
    update_csv_files("qwen3-8b", "183733")
    update_csv_files("qwen3-8b", "191832")
    
    # 4. Fix Databases (Explicit)
    update_database_explicit()
    
    print("\nDone. Please check the results.")
