
import pandas as pd
import os
import glob

def verify_counts():
    csv_path = r"E:\Python\MathProject_AST_Research\agent_tools\reports\jh_數學2上_FourOperationsOfRadicals\jh_數學2上_FourOperationsOfRadicals_runs_20260220_000857.csv"
    gen_dir = r"E:\Python\MathProject_AST_Research\agent_tools\reports\jh_數學2上_FourOperationsOfRadicals\gen_code"
    
    # 1. Analyze CSV
    df = pd.read_csv(csv_path)
    csv_counts = df.groupby(['model_name', 'ablation_id']).size().unstack(fill_value=0)
    
    print("--- CSV Record Counts (Rows) ---")
    print(csv_counts)
    print("\nTotal CSV Rows:", len(df))
    
    # 2. Analyze File System
    # We key on the filename patterns we saw earlier:
    # radicals_L{level}_ab{ab}_MODEL_...
    # But we know the mapping:
    # Cloud/Gemini -> Gemini_3_flash
    # 14B -> Qwen3_14B
    # 8B -> Qwen3_8B
    
    files = glob.glob(os.path.join(gen_dir, "*_extracted.py"))
    
    file_stats = {
        'Gemini_3_flash': {'1':0, '2':0, '3':0},
        'Qwen3_14B': {'1':0, '2':0, '3':0},
        'Qwen3_8B': {'1':0, '2':0, '3':0}
    }
    
    for f in files:
        fname = os.path.basename(f)
        # Parse ablation
        ab_part = [p for p in fname.split('_') if p.startswith('ab')][0]
        ab_id = ab_part.replace('ab', '')
        
        # Parse model
        model_key = None
        if 'Cloud' in fname or 'Gemini' in fname:
            model_key = 'Gemini_3_flash'
        elif '14B' in fname:
            model_key = 'Qwen3_14B'
        elif '8B' in fname:
            model_key = 'Qwen3_8B'
            
        if model_key and ab_id in file_stats[model_key]:
            file_stats[model_key][ab_id] += 1
            
    print("\n--- Generated File Counts (Actual Files) ---")
    df_files = pd.DataFrame(file_stats).T
    df_files.index.name = 'model_name'
    print(df_files)
    print("\nTotal Files:", len(files))
    
    # 3. Comparison
    print("\n--- Discrepancy Analysis (CSV Rows - Files) ---")
    # This represents "Timeouts" or "Missing Files" rows
    diff = csv_counts - df_files
    print(diff)
    
    # 4. Total Check
    print("\n--- Summary ---")
    for model in csv_counts.index:
        total_csv = csv_counts.loc[model].sum()
        total_files = df_files.loc[model].sum()
        print(f"{model}: CSV={total_csv}, Files={total_files}, Diff (Timeout/Fail)={total_csv - total_files}")
        if total_csv != 45:
             print(f"  [!] Warning: Expected 45 total runs (15x3), found {total_csv}")

if __name__ == "__main__":
    verify_counts()
