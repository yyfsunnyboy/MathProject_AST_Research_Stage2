
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

try:
    from scripts.evaluate_mcri import create_database, insert_experiment_runs, insert_evaluation_items, write_ablation_summary_csv
except ImportError:
    print("❌ Failed to import scripts.evaluate_mcri")
    sys.exit(1)

def recover_db_from_csv(csv_prefix, db_timestamp):
    print(f"🔄 Recovering DB for {db_timestamp} from {csv_prefix}...")
    
    # Paths
    report_dir = os.path.join(
        PROJECT_ROOT, "agent_tools", "reports", 
        "jh_數學2上_FourOperationsOfRadicals"
    )
    
    runs_csv = os.path.join(report_dir, f"{csv_prefix}_runs_{db_timestamp}.csv")
    items_csv = os.path.join(report_dir, f"{csv_prefix}_items_{db_timestamp}.csv")
    summary_csv = os.path.join(report_dir, f"{csv_prefix}_summary_{db_timestamp}.csv")
    
    db_path = os.path.join(PROJECT_ROOT, "instance", f"benchmark_{db_timestamp}.db")
    
    if not os.path.exists(runs_csv):
        print(f"❌ Runs CSV not found: {runs_csv}")
        return

    # 1. Create DB (Correctly using IF NOT EXISTS now)
    create_database(db_path)
    conn = sqlite3.connect(db_path)
    
    # 2. Import Runs
    try:
        df_runs = pd.read_csv(runs_csv)
        records_runs = df_runs.to_dict('records')
        
        # Clean up data types (pandas reads NaN for empty strings sometimes)
        for r in records_runs:
            for k, v in r.items():
                if pd.isna(v): r[k] = None
                
        insert_experiment_runs(conn, records_runs)
        print(f"✅ Imported {len(records_runs)} runs.")
    except Exception as e:
        print(f"❌ Failed to import runs: {e}")

    # 3. Import Items
    if os.path.exists(items_csv):
        try:
            df_items = pd.read_csv(items_csv)
            records_items = df_items.to_dict('records')
            
            for r in records_items:
                for k, v in r.items():
                    if pd.isna(v): r[k] = None
            
            insert_evaluation_items(conn, records_items)
            print(f"✅ Imported {len(records_items)} items.")
        except Exception as e:
            print(f"❌ Failed to import items: {e}")
    else:
        print("⚠️ Items CSV not found (skipping).")

    # 4. Import Summary
    if os.path.exists(summary_csv):
        try:
            df_summary = pd.read_csv(summary_csv)
            records_summary = df_summary.to_dict('records')
            
            for r in records_summary:
                for k, v in r.items():
                    if pd.isna(v): r[k] = None
                    
            cursor = conn.cursor()
            for s in records_summary:
                cursor.execute("""
                    INSERT INTO ablation_summary
                    (summary_id, skill_name, ablation_id, model_name,
                     sample_count, total_runs,
                     mean_mcri_total, std_mcri_total, ci95_lower, ci95_upper,
                     mean_l3_external, mean_l4_numeric,
                     mean_program_total, mean_math_total, mean_l5_architecture, mean_l4_mqi,
                     p_value_vs_ab1, notes)
                    VALUES
                    (:summary_id, :skill_name, :ablation_id, :model_name,
                     :sample_count, :total_runs,
                     :mean_mcri_total, :std_mcri_total, :ci95_lower, :ci95_upper,
                     :mean_l3_external, :mean_l4_numeric,
                     :mean_program_total, :mean_math_total, :mean_l5_architecture, :mean_l4_mqi,
                     :p_value_vs_ab1, :notes)
                """, s)
            conn.commit()
            print(f"✅ Imported {len(records_summary)} summaries.")
        except Exception as e:
            print(f"❌ Failed to import summary: {e}")
    else:
        print("⚠️ Summary CSV not found (skipping).")

    conn.close()
    print(f"🎉 Recovery Complete for {db_timestamp}")

if __name__ == "__main__":
    # Target Run 1
    recover_db_from_csv("jh_數學2上_FourOperationsOfRadicals", "20260220_000857")
    
    # Target Run 2 (if user mentioned it)
    recover_db_from_csv("jh_數學2上_FourOperationsOfRadicals", "20260220_084756")
