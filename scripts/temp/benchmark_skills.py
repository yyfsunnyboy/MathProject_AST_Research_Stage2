# -*- coding: utf-8 -*-
# ==============================================================================
# Script: benchmark_skills.py
# Version: v2.1 (CSV Export Support)
# Description: 
#   基於 ISO/IEC 25010 標準進行評測，並自動將結果輸出為 CSV 檔案。
#   方便匯入 Excel 製作科展圖表。
# ==============================================================================

import sys
import os
import time
import importlib
import glob
import statistics
import traceback
import csv
from datetime import datetime
from tqdm import tqdm

# 路徑設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path: sys.path.insert(0, project_root)

from app import create_app

# ==============================================================================
# 理論權重設定
# ==============================================================================
WEIGHTS = {
    'robustness': 0.40,
    'compliance': 0.30,
    'syntax': 0.20,
    'performance': 0.10
}

TEST_ITERATIONS = 50 

class BenchmarkEngine:
    def __init__(self):
        self.results = []

    def check_latex_balance(self, text):
        if not isinstance(text, str): return False
        return text.count('{') == text.count('}')

    def evaluate_skill(self, skill_id, module):
        metrics = {
            'success_count': 0,
            'compliance_count': 0,
            'syntax_pass_count': 0,
            'latencies': []
        }
        errors = set()

        for _ in range(TEST_ITERATIONS):
            start_t = time.time()
            try:
                # 1. Robustness
                result = module.generate()
                metrics['success_count'] += 1
                
                # 2. Compliance
                is_compliant = False
                if isinstance(result, dict):
                    if all(k in result for k in ['question_text', 'answer', 'correct_answer']):
                        is_compliant = True
                        metrics['compliance_count'] += 1
                    else:
                        errors.add("Missing Keys")
                else:
                    errors.add(f"Invalid Type: {type(result)}")

                # 3. Syntax
                if is_compliant:
                    q_text = result.get('question_text', "")
                    if self.check_latex_balance(q_text):
                        metrics['syntax_pass_count'] += 1
                    else:
                        errors.add("LaTeX Braces Mismatch")
                
                # 4. Performance
                duration = time.time() - start_t
                metrics['latencies'].append(duration)

            except Exception as e:
                error_msg = traceback.format_exc().strip().split('\n')[-1]
                errors.add(error_msg)

        return self.calculate_score(metrics, errors)

    def calculate_score(self, metrics, errors):
        s_robust = (metrics['success_count'] / TEST_ITERATIONS) * 100
        
        if metrics['success_count'] > 0:
            s_compliance = (metrics['compliance_count'] / metrics['success_count']) * 100
            s_syntax = (metrics['syntax_pass_count'] / metrics['success_count']) * 100
        else:
            s_compliance = 0
            s_syntax = 0

        avg_latency = statistics.mean(metrics['latencies']) if metrics['latencies'] else 10.0
        if avg_latency <= 0.05: s_perf = 100
        elif avg_latency >= 1.0: s_perf = 0
        else: s_perf = 100 - ((avg_latency - 0.05) / (1.0 - 0.05) * 100)

        final_score = (
            s_robust * WEIGHTS['robustness'] +
            s_compliance * WEIGHTS['compliance'] +
            s_syntax * WEIGHTS['syntax'] +
            s_perf * WEIGHTS['performance']
        )

        return {
            'score': round(final_score, 1),
            'robustness': round(s_robust, 1),
            'compliance': round(s_compliance, 1),
            'syntax': round(s_syntax, 1),
            'performance': round(s_perf, 1),
            'avg_latency': round(avg_latency * 1000, 2), # ms
            'errors': "; ".join(list(errors))
        }

def save_report_to_csv(results, avg_score):
    """將結果儲存為 CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_report_{timestamp}.csv"
    filepath = os.path.join(project_root, 'reports')
    
    if not os.path.exists(filepath):
        os.makedirs(filepath)
        
    full_path = os.path.join(filepath, filename)
    
    # CSV Headers
    headers = ['Skill ID', 'Total Score', 'Robustness', 'Compliance', 'Syntax', 'Performance', 'Latency (ms)', 'Errors']
    
    try:
        with open(full_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for r in results:
                row = {
                    'Skill ID': r['id'],
                    'Total Score': r['score'],
                    'Robustness': r['robustness'],
                    'Compliance': r['compliance'],
                    'Syntax': r['syntax'],
                    'Performance': r['performance'],
                    'Latency (ms)': r['avg_latency'],
                    'Errors': r['errors']
                }
                writer.writerow(row)
                
        print(f"\n💾 報告已儲存: \033[1;32m{full_path}\033[0m")
        return full_path
    except Exception as e:
        print(f"❌ 儲存失敗: {e}")
        return None

def run_benchmark():
    app = create_app()
    engine = BenchmarkEngine()
    
    skills_dir = os.path.join(project_root, 'skills')
    files = glob.glob(os.path.join(skills_dir, "*.py"))
    skill_files = [f for f in files if os.path.basename(f) not in ["__init__.py", "base_skill.py", "Example_Program.py"]]
    
    print(f"\n🔬 [Science Fair Benchmark v2.1] Starting Analysis...")
    print(f"   Target: {len(skill_files)} skill units")
    print(f"   Sample Size: {TEST_ITERATIONS} iterations per unit")
    print("="*90)
    print(f"{'Skill ID':<45} | {'Score':<6} | {'Status':<10} | {'Latency':<10}")
    print("-" * 90)

    results_data = []

    for py_file in tqdm(skill_files, desc="Analyzing", ncols=100):
        skill_id = os.path.basename(py_file).replace(".py", "")
        module_name = f"skills.{skill_id}"
        
        try:
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
            
            result = engine.evaluate_skill(skill_id, module)
            result['id'] = skill_id
            results_data.append(result)
            
            status = "✅ PASS" if result['score'] >= 80 else "⚠️ WEAK" if result['score'] >= 60 else "❌ FAIL"
            tqdm.write(f"{skill_id:<45} | {result['score']:<6} | {status:<10} | {result['avg_latency']}ms")

        except Exception as e:
            tqdm.write(f"❌ Critical Error loading {skill_id}: {e}")

    # --- 統計與存檔 ---
    print("\n" + "="*90)
    scores = [r['score'] for r in results_data]
    avg_score = statistics.mean(scores) if scores else 0
    
    print(f"📊 綜合品質評分 (Mean Quality Score): {avg_score:.2f} / 100")
    
    # 儲存 CSV
    save_report_to_csv(results_data, avg_score)
    print("="*90)

if __name__ == "__main__":
    run_benchmark()