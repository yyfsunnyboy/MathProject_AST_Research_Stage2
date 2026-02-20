
import os
import glob
import re
from collections import defaultdict

def analyze_healer_metrics():
    base_dir = r"E:\Python\MathProject_AST_Research\agent_tools\reports\jh_數學2上_FourOperationsOfRadicals\gen_code"
    
    print(f"Scanning: {base_dir}")
    final_files = glob.glob(os.path.join(base_dir, "*_final.py"))
    
    if not final_files:
        print("❌ No _final.py files found!")
        return
        
    pattern_ab = re.compile(r"radicals_L(\d+)_ab(\d+)_gen")
    pattern_fixes = re.compile(r"# Fix Status: .*Fixes: Basic=(\d+), Advanced=\(Regex=(\d+), AST=(\d+)\)")
    
    stats = defaultdict(list)
    
    for f in final_files:
        filename = os.path.basename(f)
        match_ab = pattern_ab.search(filename)
        
        if not match_ab:
            continue
            
        ab_id = match_ab.group(2)
        
        # Read header
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read(2000) # Read first 2KB for header
                
            match_metrics = pattern_fixes.search(content)
            if match_metrics:
                basic = int(match_metrics.group(1))
                regex = int(match_metrics.group(2))
                ast_fix = int(match_metrics.group(3))
                
                stats[ab_id].append((basic, regex, ast_fix))
            else:
                # Maybe header format is different?
                pass
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    print("\n--- Healer Metrics Summary by Ablation ---")
    
    for ab in sorted(stats.keys()):
        data = stats[ab]
        count = len(data)
        
        # Unique combinations found
        unique_combos = set(data)
        
        print(f"\n[Ab{ab}] Total Files: {count}")
        print(f"Unique Metric Combos (Basic, Regex, AST):")
        for combo in sorted(list(unique_combos)):
            occ = data.count(combo)
            print(f"  {combo}: {occ} times")
            
    print("\n--- End of Report ---")

if __name__ == "__main__":
    analyze_healer_metrics()
