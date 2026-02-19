import pandas as pd
import re
import os
import sys

def recover_csv_metrics(csv_path):
    print(f"📂 Processing: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return

    # Counter for updates
    updated_count = 0
    
    for index, row in df.iterrows():
        notes = str(row.get('notes', ''))
        source_path = str(row.get('source_code_path', ''))
        
        # 1. Extract Performance (Latency) from Notes
        # Pattern: Perf: 12.34s
        perf_match = re.search(r'Perf:\s*([\d.]+)s', notes)
        if perf_match:
            try:
                seconds = float(perf_match.group(1))
                latency_ms = int(seconds * 1000)
                df.at[index, 'latency_ms'] = latency_ms
                updated_count += 1
            except ValueError:
                pass
        
        # 2. Extract Tokens from Notes (if available)
        # Pattern: Tokens: In=123, Out=456
        token_match = re.search(r'Tokens:\s*In=(\d+),\s*Out=(\d+)', notes)
        if token_match:
            try:
                tokens_in = int(token_match.group(1))
                tokens_out = int(token_match.group(2))
                df.at[index, 'prompt_tokens'] = tokens_in
                df.at[index, 'completion_tokens'] = tokens_out
                df.at[index, 'total_tokens'] = tokens_in + tokens_out
                updated_count += 1
            except ValueError:
                pass
        
        # 3. Fallback: If tokens are 0, try to read from source file header
        current_total = row.get('total_tokens', 0)
        if pd.isna(current_total) or current_total == 0:
            if os.path.exists(source_path):
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content = f.read(1024) # Read first 1kb for header
                        
                    # Fix Status: [Full Healer] | Fixes: Basic=0, Advanced=(Regex=0, AST=12)
                    # Performance: 0.00s | Tokens: In=0, Out=0
                    
                    t_match = re.search(r'Tokens:\s*In=(\d+),\s*Out=(\d+)', content)
                    if t_match:
                        t_in = int(t_match.group(1))
                        t_out = int(t_match.group(2))
                        df.at[index, 'prompt_tokens'] = t_in
                        df.at[index, 'completion_tokens'] = t_out
                        df.at[index, 'total_tokens'] = t_in + t_out
                        updated_count += 1
                        
                    # Also try to recover latency from file header if missing in CSV
                    if df.at[index, 'latency_ms'] == 0:
                         p_match = re.search(r'Performance:\s*([\d.]+)s', content)
                         if p_match:
                             sec = float(p_match.group(1))
                             df.at[index, 'latency_ms'] = int(sec * 1000)

                except Exception:
                    pass

    # Save back to CSV
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ Successfully updated {updated_count} rows in {csv_path}")
    except Exception as e:
        print(f"❌ Failed to save CSV: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recover_csv_metrics.py <path_to_csv>")
    else:
        recover_csv_metrics(sys.argv[1])
