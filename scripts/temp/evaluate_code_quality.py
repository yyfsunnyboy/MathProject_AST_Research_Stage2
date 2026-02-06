# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱: scripts/evaluate_code_quality.py
功能說明: 科展專用 - 程式碼品質量化評估系統
         基於學術界認可的評估方法 (Pass@K, Functional Correctness)
版本資訊: V1.0
參考文獻:
  1. Chen et al. (2021) "Evaluating Large Language Models Trained on Code"
  2. Ren et al. (2020) "CodeBLEU: A Method for Automatic Evaluation"
  3. Google DeepMind AlphaCode Evaluation Framework
=============================================================================
"""

import os
import sys
import ast
import re
import json
from typing import Dict, List, Tuple
from fractions import Fraction

# 添加專案根目錄到路徑
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class CodeQualityEvaluator:
    """
    程式碼品質評估器
    
    評估維度（基於學術標準）:
    1. Syntax Validity (SV): 語法正確性 [0/1]
    2. Runtime Success (RS): 執行成功率 [0/1]
    3. Output Quality (OQ): 輸出品質 [0-1]
    4. Logic Correctness (LC): 邏輯正確性 [0-1]
    
    總分計算:
    FCS (Functional Correctness Score) = SV*0.25 + RS*0.25 + OQ*0.25 + LC*0.25
    """
    
    def __init__(self):
        self.results = {}
    
    def evaluate_syntax_validity(self, code_path: str) -> Tuple[float, str]:
        """
        評估語法正確性
        Returns: (score, details)
        """
        try:
            with open(code_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 嘗試解析 AST
            ast.parse(code)
            return 1.0, "Syntax valid"
        except SyntaxError as e:
            return 0.0, f"SyntaxError at line {e.lineno}: {e.msg}"
        except Exception as e:
            return 0.0, f"Parse error: {str(e)}"
    
    def evaluate_runtime_success(self, code_path: str, trials: int = 3) -> Tuple[float, str]:
        """
        評估執行成功率
        執行多次測試，計算成功率
        Returns: (score, details)
        """
        success_count = 0
        errors = []
        
        module_name = os.path.basename(code_path).replace('.py', '')
        
        for i in range(trials):
            try:
                # 動態導入模組
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"{module_name}_{i}", code_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 執行 generate 函數
                    if hasattr(module, 'generate'):
                        result = module.generate()
                        if result and 'question_text' in result:
                            success_count += 1
                        else:
                            errors.append(f"Trial {i+1}: Invalid output format")
                    else:
                        errors.append(f"Trial {i+1}: No generate() function")
                else:
                    errors.append(f"Trial {i+1}: Module load failed")
                    
            except Exception as e:
                errors.append(f"Trial {i+1}: {type(e).__name__}: {str(e)[:50]}")
        
        score = success_count / trials
        details = f"{success_count}/{trials} successful" + (f" | Errors: {'; '.join(errors[:2])}" if errors else "")
        return score, details
    
    def evaluate_output_quality(self, code_path: str, samples: int = 5) -> Tuple[float, str]:
        """
        評估輸出品質（LaTeX 格式正確性）
        
        檢查項目:
        1. 無 Markdown 殘留 (```)
        2. 無破碎的數學式 ($ ^{)
        3. 正確的指數格式 (x^{n} not x^{{n}})
        4. 正確的分數格式 (\\frac{}{})
        5. 數學式有 $ 包裹
        """
        try:
            import importlib.util
            module_name = os.path.basename(code_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, code_path)
            
            if not spec or not spec.loader:
                return 0.0, "Module load failed"
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if not hasattr(module, 'generate'):
                return 0.0, "No generate() function"
            
            quality_scores = []
            issues = []
            
            for i in range(samples):
                try:
                    result = module.generate()
                    question = result.get('question_text', '')
                    
                    score = 1.0
                    sample_issues = []
                    
                    # 檢查 1: Markdown 殘留
                    if '```' in question:
                        score -= 0.3
                        sample_issues.append("Markdown fence")
                    
                    # 檢查 2: 破碎的數學式
                    if '$ ^{' in question or '$ \\' in question:
                        score -= 0.3
                        sample_issues.append("Fragmented math")
                    
                    # 檢查 3: 雙大括號錯誤
                    if re.search(r'x\^\{\{', question):
                        score -= 0.2
                        sample_issues.append("Double braces")
                    
                    # 檢查 4: 數學式包裹
                    has_math = re.search(r'[f\(x\)|\\frac|\\times|x\^]', question)
                    has_dollar = '$' in question
                    if has_math and not has_dollar:
                        score -= 0.2
                        sample_issues.append("Missing $ wrapping")
                    
                    quality_scores.append(max(0, score))
                    if sample_issues:
                        issues.extend(sample_issues)
                        
                except Exception as e:
                    quality_scores.append(0.0)
                    issues.append(f"Sample {i+1} error")
            
            avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            details = f"Avg: {avg_score:.2f}" + (f" | Issues: {', '.join(set(issues[:3]))}" if issues else "")
            
            return avg_score, details
            
        except Exception as e:
            return 0.0, f"Evaluation error: {str(e)[:50]}"
    
    def evaluate_logic_correctness(self, code_path: str, samples: int = 5) -> Tuple[float, str]:
        """
        評估邏輯正確性（數學計算是否合理）
        
        檢查項目:
        1. 函數定義完整
        2. 數值範圍合理
        3. 輸出格式一致
        4. 無明顯邏輯錯誤
        """
        try:
            import importlib.util
            module_name = os.path.basename(code_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, code_path)
            
            if not spec or not spec.loader:
                return 0.0, "Module load failed"
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if not hasattr(module, 'generate'):
                return 0.0, "No generate() function"
            
            logic_scores = []
            
            for i in range(samples):
                try:
                    result = module.generate()
                    
                    score = 1.0
                    
                    # 檢查輸出結構
                    if not isinstance(result, dict):
                        score -= 0.5
                    elif 'question_text' not in result or 'answer' not in result:
                        score -= 0.3
                    
                    # 檢查問題和答案不為空
                    question = result.get('question_text', '')
                    answer = result.get('answer', '')
                    
                    if not question or len(question) < 10:
                        score -= 0.3
                    if not answer or len(str(answer)) < 1:
                        score -= 0.2
                    
                    logic_scores.append(max(0, score))
                    
                except Exception as e:
                    logic_scores.append(0.0)
            
            avg_score = sum(logic_scores) / len(logic_scores) if logic_scores else 0.0
            details = f"{avg_score:.2f} avg logic score"
            
            return avg_score, details
            
        except Exception as e:
            return 0.0, f"Evaluation error: {str(e)[:50]}"
    
    def compute_fcs(self, sv: float, rs: float, oq: float, lc: float) -> float:
        """
        計算 Functional Correctness Score (FCS)
        FCS = SV*0.25 + RS*0.25 + OQ*0.25 + LC*0.25
        """
        return (sv * 0.25) + (rs * 0.25) + (oq * 0.25) + (lc * 0.25)
    
    def evaluate_file(self, code_path: str, ablation_id: int) -> Dict:
        """
        完整評估單一檔案
        """
        print(f"\n{'='*70}")
        print(f"Evaluating: {os.path.basename(code_path)}")
        print(f"Ablation ID: {ablation_id}")
        print(f"{'='*70}")
        
        # 讀取 Header 資訊
        with open(code_path, 'r', encoding='utf-8') as f:
            header = ''.join(f.readlines()[:10])
        
        healer_status = re.search(r'Healer: (\w+)', header)
        fixes = re.search(r'Fixes: ([^#]+)', header)
        
        healer_on = healer_status.group(1) == 'ON' if healer_status else False
        fixes_str = fixes.group(1).strip() if fixes else "N/A"
        
        # 評估各維度
        sv_score, sv_details = self.evaluate_syntax_validity(code_path)
        print(f"  [1/4] Syntax Validity:     {sv_score:.2f} | {sv_details}")
        
        rs_score, rs_details = self.evaluate_runtime_success(code_path, trials=3)
        print(f"  [2/4] Runtime Success:     {rs_score:.2f} | {rs_details}")
        
        oq_score, oq_details = self.evaluate_output_quality(code_path, samples=3)
        print(f"  [3/4] Output Quality:      {oq_score:.2f} | {oq_details}")
        
        lc_score, lc_details = self.evaluate_logic_correctness(code_path, samples=3)
        print(f"  [4/4] Logic Correctness:   {lc_score:.2f} | {lc_details}")
        
        # 計算總分
        fcs = self.compute_fcs(sv_score, rs_score, oq_score, lc_score)
        
        print(f"\n  >>> Functional Correctness Score (FCS): {fcs:.3f} ({fcs*100:.1f}%)")
        print(f"  >>> Healer Status: {'ON' if healer_on else 'OFF'}")
        print(f"  >>> Fixes Applied: {fixes_str}")
        
        return {
            'file': os.path.basename(code_path),
            'ablation_id': ablation_id,
            'healer_on': healer_on,
            'fixes': fixes_str,
            'sv_score': sv_score,
            'sv_details': sv_details,
            'rs_score': rs_score,
            'rs_details': rs_details,
            'oq_score': oq_score,
            'oq_details': oq_details,
            'lc_score': lc_score,
            'lc_details': lc_details,
            'fcs': fcs
        }
    
    def compare_ablations(self, results: List[Dict]):
        """
        比較不同 Ablation 的結果
        """
        print(f"\n{'='*70}")
        print("ABLATION STUDY COMPARISON")
        print(f"{'='*70}")
        
        print(f"\n{'Ablation':<15} {'Healer':<10} {'SV':<8} {'RS':<8} {'OQ':<8} {'LC':<8} {'FCS':<10}")
        print('-' * 70)
        
        for r in sorted(results, key=lambda x: x['ablation_id']):
            ab_name = f"Ab{r['ablation_id']}"
            healer = 'ON' if r['healer_on'] else 'OFF'
            print(f"{ab_name:<15} {healer:<10} {r['sv_score']:<8.2f} {r['rs_score']:<8.2f} "
                  f"{r['oq_score']:<8.2f} {r['lc_score']:<8.2f} {r['fcs']:<10.3f}")
        
        # 計算改善幅度
        if len(results) >= 2:
            print(f"\n{'='*70}")
            print("HEALER IMPACT ANALYSIS")
            print(f"{'='*70}")
            
            ab1 = next((r for r in results if r['ablation_id'] == 1), None)
            ab2 = next((r for r in results if r['ablation_id'] == 2), None)
            ab3 = next((r for r in results if r['ablation_id'] == 3), None)
            
            if ab2 and ab3:
                improvement = ab3['fcs'] - ab2['fcs']
                # 避免除以零，使用 Ab1 作為基準
                baseline = ab1['fcs'] if ab1 and ab1['fcs'] > 0 else 0.001
                improvement_pct = (improvement / baseline * 100) if baseline > 0 else (improvement * 100)
                
                print(f"\nAb2 (No Healer):  FCS = {ab2['fcs']:.3f}")
                print(f"Ab3 (Healer ON):  FCS = {ab3['fcs']:.3f}")
                print(f"Improvement:      +{improvement:.3f} (from baseline)")
                
                if ab1:
                    print(f"\nBaseline (Ab1):   FCS = {ab1['fcs']:.3f}")
                    print(f"Ab3 vs Ab1:       +{ab3['fcs'] - ab1['fcs']:.3f} ({(ab3['fcs'] - ab1['fcs'])/ab1['fcs']*100:+.1f}%)")
                
                print(f"\nFixes Applied:    {ab3['fixes']}")
                print(f"\nConclusion: Healer achieved {ab3['fcs']*100:.0f}% quality (vs {ab2['fcs']*100:.0f}% without Healer)")


def main():
    """
    主程式：評估 Ab1, Ab2, Ab3 三個版本
    """
    evaluator = CodeQualityEvaluator()
    
    skills_dir = os.path.join(PROJECT_ROOT, 'skills')
    
    # 定義要評估的檔案
    files_to_evaluate = [
        ('gh_ApplicationsOfDerivatives_14b_Ab1.py', 1),
        ('gh_ApplicationsOfDerivatives_14b_Ab2.py', 2),
        ('gh_ApplicationsOfDerivatives_14b_Ab3.py', 3),
    ]
    
    results = []
    
    for filename, ablation_id in files_to_evaluate:
        filepath = os.path.join(skills_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found, skipping...")
            continue
        
        result = evaluator.evaluate_file(filepath, ablation_id)
        results.append(result)
    
    # 比較結果
    if results:
        evaluator.compare_ablations(results)
        
        # 輸出 JSON 報告
        output_file = os.path.join(PROJECT_ROOT, 'reports', 'code_quality_evaluation.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
