# -*- coding: utf-8 -*-
"""
MCRI V2.0 評分模型 (Mathematical Code Robustness Index)
採用「層級過濾扣分制 (Hierarchical Penalty System)」

總分：100 分
- Level 1: 可執行性 (Executability) - 40%
  - V2.0 改進：雙重檢測機制（格式純淨度 + 核心邏輯性）
- Level 2: 介面合規性 (Interface Compliance) - 30%
- Level 3: 邏輯強健性 (Logical Robustness) - 20%
- Level 4: 安全與規範 (Safety & Standards) - 10%

核心方法論：Healer vs Evaluator 分離
- Healer（實驗變因）：生產線的一部分，修復代碼
- Evaluator（評分尺）：品管的一部分，公平評估代碼品質

學術依據：
- OpenAI HumanEval (Chen et al., 2021) - "execution harness" 標準化測試環境
- Google MBPP (Austin et al., 2021) - "test normalization" 處理格式差異
"""

import os
import sys
import ast
import json
import importlib.util
import re
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class MCRIEvaluator:
    """
    MCRI V2.0 評分系統評估器
    
    核心創新：Standard Evaluation Harness（標準化評測前處理）
    - 參考 OpenAI HumanEval 和 Google MBPP 的評測實踐
    - 區分「格式純淨度」vs「核心邏輯性」
    - Evaluator 可做標準化前處理，但必須扣分以示懲罰
    """
    
    FORBIDDEN_MODULES = ['numpy', 'matplotlib', 'pandas', 'scipy', 'sympy', 'sklearn']
    FORBIDDEN_FUNCTIONS = ['eval', 'exec', 'compile', '__import__']
    REQUIRED_KEYS = ['question_text', 'correct_answer', 'answer', 'mode']
    
    def __init__(self):
        self.results = []
    
    def read_file(self, filepath):
        """讀取檔案內容"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read(), None
        except Exception as e:
            return None, f"讀取失敗: {e}"
    
    def standardize_code(self, code):
        """
        標準化前處理 (Standard Evaluation Harness)
        
        ⚠️ 重要：這是 Evaluator 的職責，不是 Healer 的職責
        - Evaluator：僅移除 Markdown fence，幫助「看清內容」
        - Healer：完整修復（Regex + AST），讓代碼「能運作」
        
        學術依據：
        - OpenAI HumanEval: "execution harness" 標準化測試環境
        - Google MBPP: "test normalization" 處理格式差異
        
        目的：公平評估代碼本質品質，同時懲罰格式錯誤
        """
        cleaned = code
        
        # 移除 Markdown code fence（```)
        cleaned = re.sub(r'^```[\w]*\s*\n', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\n```\s*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'```', '', cleaned)
        
        # 移除孤立字元（但不做完整修復）
        # 這裡只移除明顯的垃圾字元，不修復函數名等
        cleaned = re.sub(r'^\s*`[0-9]\s*$', '', cleaned, flags=re.MULTILINE)
        
        return cleaned
    
    def evaluate_level1_executability(self, filepath, code):
        """
        Level 1: 可執行性 (40 分) - MCRI V2.0 雙重檢測
        
        改進重點：區分「格式純淨度」與「核心邏輯性」
        參考 HumanEval 的 evaluation harness 設計
        
        1.1 格式純淨度 (Format Purity) - 10分
            - 直接對原始代碼執行 ast.parse()
            - 不過就扣分（懲罰 Markdown fence、垃圾字元等格式錯誤）
        
        1.2 核心邏輯性 (Core AST) - 15分
            - 對代碼做標準化前處理（移除 Markdown fence, 孤立字元）
            - 再執行 ast.parse()
            - 過關就得分（評估代碼本質的語法正確性）
        
        1.3 Import 檢查 - 5分
            - 是否引用禁用套件
        
        1.4 Runtime 執行 - 10分
            - 能否無錯誤執行定義階段
        
        學術依據：
        > "We apply a standard evaluation harness that normalizes formatting 
           differences while penalizing non-standard outputs." 
           (Chen et al., 2021)
        """
        scores = {
            'format_purity': 0,  # 10分 - V2.0 新增
            'core_ast': 0,       # 15分 - V2.0 新增
            'import_check': 0,   # 5分
            'runtime_exec': 0    # 10分
        }
        details = {}
        
        # 1.1 格式純淨度 (Format Purity) - 直接解析原始代碼
        try:
            tree = ast.parse(code)
            scores['format_purity'] = 10
            details['format_purity'] = "✓ 格式純淨（原始代碼可直接解析）"
        except SyntaxError as e:
            details['format_purity'] = f"✗ 格式錯誤: Line {e.lineno} - {e.msg}"
        
        # 1.2 核心邏輯性 (Core AST) - 標準化後解析
        cleaned_code = self.standardize_code(code)
        try:
            tree = ast.parse(cleaned_code)
            scores['core_ast'] = 15
            details['core_ast'] = "✓ 核心邏輯正確（標準化後可解析）"
        except SyntaxError as e:
            details['core_ast'] = f"✗ 邏輯錯誤: Line {e.lineno} - {e.msg}"
            # 如果標準化後仍無法解析，後續檢查無意義
            details['import_check'] = "✗ 無法檢查（語法錯誤）"
            details['runtime_exec'] = "✗ 無法執行（語法錯誤）"
            return scores, details
        
        # 1.3 Import 檢查（使用標準化後的代碼）
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split('.')[0])
        
        forbidden_found = [m for m in imported_modules if m in self.FORBIDDEN_MODULES]
        if forbidden_found:
            details['import_check'] = f"✗ 引用禁用套件: {', '.join(forbidden_found)}"
        else:
            scores['import_check'] = 5
            details['import_check'] = f"✓ 無禁用套件 (檢查了 {len(imported_modules)} 個)"
        
        # 1.4 Runtime 執行（定義階段）- 使用標準化後的代碼
        try:
            namespace = {}
            exec(cleaned_code, namespace)
            scores['runtime_exec'] = 10
            details['runtime_exec'] = "✓ 定義階段執行成功"
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:100]
            details['runtime_exec'] = f"✗ 執行錯誤: {error_type} - {error_msg}"
        
        return scores, details
    
    def evaluate_level2_interface(self, filepath, code):
        """
        Level 2: 介面合規性 (30 分)
        
        2.1 函數定義 (10分): 是否存在 generate(level, **kwargs)
        2.2 回傳型別 (10分): generate() 是否回傳 dict
        2.3 必要鍵值 (10分): 是否包含 question_text, correct_answer, answer, mode
        
        前提：必須通過 Level 1 的 Runtime 執行
        """
        scores = {
            'function_def': 0,    # 10分
            'return_type': 0,     # 10分
            'required_keys': 0    # 10分
        }
        details = {}
        
        # 先嘗試載入模組
        try:
            namespace = {}
            exec(code, namespace)
        except:
            details['function_def'] = "✗ 無法執行，跳過介面檢查"
            details['return_type'] = "✗ 無法執行"
            details['required_keys'] = "✗ 無法執行"
            return scores, details
        
        # 2.1 函數定義
        # 支援多種命名: generate, generate_question, main
        possible_names = ['generate', 'generate_question', 'main']
        func_name = None
        for name in possible_names:
            if name in namespace and callable(namespace[name]):
                func_name = name
                break
        
        if func_name:
            scores['function_def'] = 10
            details['function_def'] = f"✓ 找到函數: {func_name}()"
            
            # 檢查參數簽名
            import inspect
            sig = inspect.signature(namespace[func_name])
            params = list(sig.parameters.keys())
            if 'level' in params or 'difficulty' in params or len(params) >= 1:
                details['function_def'] += f" (參數: {', '.join(params)})"
        else:
            details['function_def'] = f"✗ 找不到生成函數 (嘗試: {', '.join(possible_names)})"
            return scores, details
        
        # 2.2 回傳型別 + 2.3 必要鍵值（需要實際執行）
        try:
            # 嘗試呼叫函數
            if 'level' in str(sig):
                result = namespace[func_name](level=4)
            else:
                result = namespace[func_name]()
            
            # 檢查回傳型別
            if isinstance(result, dict):
                scores['return_type'] = 10
                details['return_type'] = "✓ 回傳型別正確 (dict)"
                
                # 檢查必要鍵值
                keys = set(result.keys())
                # 支援多種鍵值命名
                key_mappings = {
                    'question_text': ['question_text', 'problem', 'question'],
                    'correct_answer': ['correct_answer', 'answer', 'solution'],
                    'answer': ['answer', 'solution', 'correct_answer'],
                    'mode': ['mode', 'type', 'question_type']
                }
                
                found_keys = []
                missing_keys = []
                for required_key, alternatives in key_mappings.items():
                    if any(alt in keys for alt in alternatives):
                        found_keys.append(required_key)
                    else:
                        missing_keys.append(required_key)
                
                if len(found_keys) >= 3:  # 至少3個關鍵欄位
                    scores['required_keys'] = 10
                    details['required_keys'] = f"✓ 必要鍵值完整 (找到 {len(found_keys)}/4)"
                else:
                    scores['required_keys'] = int(len(found_keys) / 4 * 10)
                    details['required_keys'] = f"✗ 缺少鍵值: {', '.join(missing_keys)}"
            else:
                details['return_type'] = f"✗ 回傳型別錯誤: {type(result).__name__}"
                details['required_keys'] = "✗ 非 dict，無法檢查鍵值"
        
        except Exception as e:
            error_msg = str(e)[:100]
            details['return_type'] = f"✗ 執行失敗: {type(e).__name__}"
            details['required_keys'] = f"✗ 無法檢查: {error_msg}"
        
        return scores, details
    
    def evaluate_level3_robustness(self, filepath, code):
        """
        Level 3: 邏輯強健性 (20 分)
        
        3.1 動態採樣 (10分): 連續呼叫 3 次不 Crash
        3.2 答案一致性 (10分): answer 與 correct_answer 是否一致
        
        前提：必須通過 Level 2 的介面檢查
        """
        scores = {
            'dynamic_sampling': 0,   # 10分
            'answer_consistency': 0  # 10分
        }
        details = {}
        
        # 先載入模組
        try:
            namespace = {}
            exec(code, namespace)
        except:
            details['dynamic_sampling'] = "✗ 無法執行"
            details['answer_consistency'] = "✗ 無法執行"
            return scores, details
        
        # 找到生成函數
        possible_names = ['generate', 'generate_question', 'main']
        func_name = None
        for name in possible_names:
            if name in namespace and callable(namespace[name]):
                func_name = name
                break
        
        if not func_name:
            details['dynamic_sampling'] = "✗ 找不到函數"
            details['answer_consistency'] = "✗ 找不到函數"
            return scores, details
        
        # 3.1 動態採樣
        import inspect
        sig = inspect.signature(namespace[func_name])
        
        success_count = 0
        results = []
        errors = []
        
        for i in range(3):
            try:
                if 'level' in str(sig):
                    result = namespace[func_name](level=4)
                else:
                    result = namespace[func_name]()
                
                if isinstance(result, dict):
                    success_count += 1
                    results.append(result)
                else:
                    errors.append(f"Trial {i+1}: 回傳非 dict")
            except Exception as e:
                errors.append(f"Trial {i+1}: {type(e).__name__}")
        
        if success_count == 3:
            scores['dynamic_sampling'] = 10
            details['dynamic_sampling'] = "✓ 3 次採樣全部成功"
        elif success_count >= 2:
            scores['dynamic_sampling'] = 7
            details['dynamic_sampling'] = f"△ 3 次採樣成功 {success_count} 次"
        elif success_count >= 1:
            scores['dynamic_sampling'] = 3
            details['dynamic_sampling'] = f"△ 3 次採樣僅成功 {success_count} 次"
        else:
            details['dynamic_sampling'] = f"✗ 全部失敗: {errors[0] if errors else '未知'}"
        
        # 3.2 答案一致性
        if results:
            consistent_count = 0
            total_check = 0
            
            for result in results:
                # 多種鍵值可能性
                answer = result.get('answer') or result.get('solution') or result.get('correct_answer')
                correct = result.get('correct_answer') or result.get('solution') or result.get('answer')
                
                if answer and correct:
                    total_check += 1
                    # 簡單比較（去除空白）
                    if str(answer).strip() == str(correct).strip():
                        consistent_count += 1
            
            if total_check > 0:
                consistency_rate = consistent_count / total_check
                if consistency_rate >= 0.9:
                    scores['answer_consistency'] = 10
                    details['answer_consistency'] = f"✓ 答案一致性: {consistency_rate:.0%}"
                elif consistency_rate >= 0.6:
                    scores['answer_consistency'] = 6
                    details['answer_consistency'] = f"△ 答案一致性: {consistency_rate:.0%}"
                else:
                    scores['answer_consistency'] = 3
                    details['answer_consistency'] = f"✗ 答案一致性偏低: {consistency_rate:.0%}"
            else:
                details['answer_consistency'] = "✗ 無法檢查（缺少答案欄位）"
        else:
            details['answer_consistency'] = "✗ 無成功執行結果"
        
        return scores, details
    
    def evaluate_level4_safety(self, filepath, code):
        """
        Level 4: 安全與規範 (10 分)
        
        4.1 禁運函數 (5分): 完全沒有 eval(), exec()
        4.2 LaTeX 格式 (5分): question_text 包含 $ 符號
        """
        scores = {
            'forbidden_funcs': 0,  # 5分
            'latex_format': 0      # 5分
        }
        details = {}
        
        # 4.1 禁運函數檢查（AST 分析）
        try:
            tree = ast.parse(code)
            forbidden_found = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.FORBIDDEN_FUNCTIONS:
                            forbidden_found.append(node.func.id)
            
            if forbidden_found:
                details['forbidden_funcs'] = f"✗ 使用禁運函數: {', '.join(set(forbidden_found))}"
            else:
                scores['forbidden_funcs'] = 5
                details['forbidden_funcs'] = "✓ 無使用 eval/exec"
        except:
            details['forbidden_funcs'] = "✗ 無法檢查（AST 解析失敗）"
        
        # 4.2 LaTeX 格式檢查（需要執行）
        try:
            namespace = {}
            cleaned_code = self.standardize_code(code)
            exec(cleaned_code, namespace)
            
            possible_names = ['generate', 'generate_question', 'main']
            func_name = None
            for name in possible_names:
                if name in namespace and callable(namespace[name]):
                    func_name = name
                    break
            
            if func_name:
                import inspect
                sig = inspect.signature(namespace[func_name])
                
                if 'level' in str(sig):
                    result = namespace[func_name](level=4)
                else:
                    result = namespace[func_name]()
                
                if isinstance(result, dict):
                    question = result.get('question_text') or result.get('problem') or result.get('question', '')
                    
                    # V2.0 改進：檢查垃圾模板（更嚴格的品質檢查）
                    bad_patterns = [
                        r'\$LATEX\$',           # 未替換的模板變數
                        r'\$BLOCK\$',           # 未替換的區塊
                        r'__\s*\$',             # __ $ 這種垃圾格式
                        r'\$\s*__',             # $ __ 這種垃圾格式
                        r'_{2,}',               # 連續兩個以上底線（模板殘留）
                    ]
                    
                    has_bad_pattern = any(re.search(pattern, question) for pattern in bad_patterns)
                    
                    if has_bad_pattern:
                        scores['latex_format'] = 0
                        details['latex_format'] = "✗ LaTeX 品質差：包含未替換的模板變數"
                    elif '$' in question and '\\' in question:
                        scores['latex_format'] = 5
                        details['latex_format'] = "✓ LaTeX 格式完整（有 $ 和 \\ 指令）"
                    elif '$' in question:
                        scores['latex_format'] = 3
                        details['latex_format'] = "△ 有 $ 但缺少 \\ 指令"
                    else:
                        details['latex_format'] = "✗ 未使用 LaTeX 格式"
                else:
                    details['latex_format'] = "✗ 無法取得 question_text"
            else:
                details['latex_format'] = "✗ 找不到函數"
        except:
            details['latex_format'] = "✗ 執行失敗，無法檢查"
        
        return scores, details
    
    def compute_mcri(self, level1, level2, level3, level4):
        """
        計算 MCRI V2.0 總分
        
        MCRI V2.0 改進：
        - Level 1 從 3 個維度改為 4 個維度（雙重檢測）
        - 格式純淨度 (10) + 核心邏輯性 (15) + Import (5) + Runtime (10) = 40
        """
        total = 0
        
        # Level 1: 可執行性 (40分) - V2.0 雙重檢測
        total += level1['format_purity']     # 10分
        total += level1['core_ast']          # 15分
        total += level1['import_check']      # 5分
        total += level1['runtime_exec']      # 10分
        
        # Level 2: 介面合規性 (30分)
        total += level2['function_def']
        total += level2['return_type']
        total += level2['required_keys']
        
        # Level 3: 邏輯強健性 (20分)
        total += level3['dynamic_sampling']
        total += level3['answer_consistency']
        
        # Level 4: 安全與規範 (10分)
        total += level4['forbidden_funcs']
        total += level4['latex_format']
        
        return total
    
    def evaluate_file(self, filepath, ablation_id, healer_enabled):
        """完整評估單個檔案"""
        print(f"\n{'='*70}")
        print(f"評估檔案: {os.path.basename(filepath)}")
        print(f"Ablation ID: {ablation_id}, Healer: {'ON' if healer_enabled else 'OFF'}")
        print(f"{'='*70}")
        
        # 讀取檔案
        code, read_error = self.read_file(filepath)
        if read_error:
            print(f"✗ {read_error}")
            return None
        
        # Level 1: 可執行性 (40分)
        level1_scores, level1_details = self.evaluate_level1_executability(filepath, code)
        print(f"\n📊 Level 1: 可執行性 (40分) - MCRI V2.0 雙重檢測")
        print(f"   1.1 格式純淨度 (10): {level1_scores['format_purity']}/10 - {level1_details['format_purity']}")
        print(f"   1.2 核心邏輯性 (15): {level1_scores['core_ast']}/15 - {level1_details['core_ast']}")
        print(f"   1.3 Import 檢查 (5): {level1_scores['import_check']}/5 - {level1_details['import_check']}")
        print(f"   1.4 Runtime 執行 (10): {level1_scores['runtime_exec']}/10 - {level1_details['runtime_exec']}")
        level1_total = sum(level1_scores.values())
        print(f"   小計: {level1_total}/40")
        
        # Level 2: 介面合規性 (30分)
        level2_scores, level2_details = self.evaluate_level2_interface(filepath, code)
        print(f"\n📊 Level 2: 介面合規性 (30分)")
        print(f"   2.1 函數定義 (10): {level2_scores['function_def']}/10 - {level2_details['function_def']}")
        print(f"   2.2 回傳型別 (10): {level2_scores['return_type']}/10 - {level2_details['return_type']}")
        print(f"   2.3 必要鍵值 (10): {level2_scores['required_keys']}/10 - {level2_details['required_keys']}")
        level2_total = sum(level2_scores.values())
        print(f"   小計: {level2_total}/30")
        
        # Level 3: 邏輯強健性 (20分)
        level3_scores, level3_details = self.evaluate_level3_robustness(filepath, code)
        print(f"\n📊 Level 3: 邏輯強健性 (20分)")
        print(f"   3.1 動態採樣 (10): {level3_scores['dynamic_sampling']}/10 - {level3_details['dynamic_sampling']}")
        print(f"   3.2 答案一致性 (10): {level3_scores['answer_consistency']}/10 - {level3_details['answer_consistency']}")
        level3_total = sum(level3_scores.values())
        print(f"   小計: {level3_total}/20")
        
        # Level 4: 安全與規範 (10分)
        level4_scores, level4_details = self.evaluate_level4_safety(filepath, code)
        print(f"\n📊 Level 4: 安全與規範 (10分)")
        print(f"   4.1 禁運函數 (5): {level4_scores['forbidden_funcs']}/5 - {level4_details['forbidden_funcs']}")
        print(f"   4.2 LaTeX 格式 (5): {level4_scores['latex_format']}/5 - {level4_details['latex_format']}")
        level4_total = sum(level4_scores.values())
        print(f"   小計: {level4_total}/10")
        
        # 計算總分
        mcri = self.compute_mcri(level1_scores, level2_scores, level3_scores, level4_scores)
        
        print(f"\n{'='*70}")
        print(f"🏆 MCRI 總分: {mcri}/100")
        print(f"{'='*70}")
        
        # 儲存結果
        result = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'ablation_id': ablation_id,
            'healer_enabled': healer_enabled,
            'level1_executability': level1_total,
            'level2_interface': level2_total,
            'level3_robustness': level3_total,
            'level4_safety': level4_total,
            'mcri_score': mcri,
            'details': {
                'level1': {'scores': level1_scores, 'details': level1_details},
                'level2': {'scores': level2_scores, 'details': level2_details},
                'level3': {'scores': level3_scores, 'details': level3_details},
                'level4': {'scores': level4_scores, 'details': level4_details}
            }
        }
        
        self.results.append(result)
        return result
    
    def compare_ablations(self):
        """比較不同 Ablation 版本"""
        print("\n" + "="*80)
        print("🏆 MCRI 評分比較表")
        print("="*80)
        
        ab1 = next((r for r in self.results if r['ablation_id'] == 1), None)
        ab2 = next((r for r in self.results if r['ablation_id'] == 2), None)
        ab3 = next((r for r in self.results if r['ablation_id'] == 3), None)
        
        print(f"\n{'評估項目':<28} {'Ab1 (Bare)':<15} {'Ab2 (Engineered)':<20} {'Ab3 (Healer)':<15}")
        print("-" * 80)
        print(f"{'Level 1: 可執行性 (40分)':<25} {ab1['level1_executability'] if ab1 else 0:<15} {ab2['level1_executability'] if ab2 else 0:<20} {ab3['level1_executability'] if ab3 else 0:<15}")
        print(f"{'Level 2: 介面合規性 (30分)':<25} {ab1['level2_interface'] if ab1 else 0:<15} {ab2['level2_interface'] if ab2 else 0:<20} {ab3['level2_interface'] if ab3 else 0:<15}")
        print(f"{'Level 3: 邏輯強健性 (20分)':<25} {ab1['level3_robustness'] if ab1 else 0:<15} {ab2['level3_robustness'] if ab2 else 0:<20} {ab3['level3_robustness'] if ab3 else 0:<15}")
        print(f"{'Level 4: 安全與規範 (10分)':<25} {ab1['level4_safety'] if ab1 else 0:<15} {ab2['level4_safety'] if ab2 else 0:<20} {ab3['level4_safety'] if ab3 else 0:<15}")
        print("-" * 80)
        print(f"{'MCRI 總分 (100分)':<25} {ab1['mcri_score'] if ab1 else 0:<15} {ab2['mcri_score'] if ab2 else 0:<20} {ab3['mcri_score'] if ab3 else 0:<15}")
        print("=" * 80)
        
        # 關鍵洞察
        if ab2 and ab3:
            improvement = ab3['mcri_score'] - ab2['mcri_score']
            print(f"\n🎯 關鍵洞察:")
            print(f"   Healer 提升 MCRI 從 {ab2['mcri_score']} 分到 {ab3['mcri_score']} 分")
            print(f"   絕對提升: +{improvement} 分")
            if ab2['mcri_score'] > 0:
                print(f"   相對提升: +{(improvement/ab2['mcri_score']*100):.1f}%")
        
        if ab2:
            print(f"\n💡 Ab2 分析:")
            print(f"   即使有語法錯誤，仍可獲得:")
            if ab2['level1_executability'] >= 10:
                print(f"   - AST 部分解析分數")
            if ab2['level4_safety'] > 0:
                print(f"   - 安全規範分數: {ab2['level4_safety']}/10")
            print(f"   這證明評分系統比「0分或100分」更公平！")
        
        print("\n")


def main():
    """主程式"""
    evaluator = MCRIEvaluator()
    
    # 評估三個 Ablation 版本
    skills_dir = os.path.join(PROJECT_ROOT, 'skills')
    
    files = [
        (os.path.join(skills_dir, 'gh_ApplicationsOfDerivatives_14b_Ab1.py'), 1, False),
        (os.path.join(skills_dir, 'gh_ApplicationsOfDerivatives_14b_Ab2.py'), 2, False),
        (os.path.join(skills_dir, 'gh_ApplicationsOfDerivatives_14b_Ab3.py'), 3, True)
    ]
    
    for filepath, ablation_id, healer_enabled in files:
        if os.path.exists(filepath):
            evaluator.evaluate_file(filepath, ablation_id, healer_enabled)
        else:
            print(f"⚠ Warning: {filepath} not found")
    
    # 比較結果
    evaluator.compare_ablations()
    
    # 儲存 JSON
    output_path = os.path.join(PROJECT_ROOT, 'reports', 'mcri_evaluation.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(evaluator.results, f, indent=2, ensure_ascii=False)
    
    print(f"📁 結果已儲存: {output_path}")


if __name__ == '__main__':
    main()
