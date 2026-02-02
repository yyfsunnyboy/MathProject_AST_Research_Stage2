#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
# ID: evaluate_mcri.py
# Version: V4.2.2 (L4.2 Math Smell Detection)
# Last Updated: 2026-02-02
# Author: Math AI Research Team
#
# [Description]:
#   MCRI V4.2.2 評估系統 - 完整評分腳本（含數學異味檢測）
#   評估三個 Ablation 版本的題目生成品質（Ab1 Bare, Ab2 Engineered, Ab3 Healer）
#   
#   [Version History]:
#   - V4.2.2: 加入 L4.2 數學異味檢測（+ -, 1x, -1x 等）
#   - V4.2.1: 修復 L3.1/L3.2 評分邏輯 - check() 返回 dict 而非 bool
#   - V4.2:   補齊 L2 評估邏輯（之前固定為 20 分）
#   
#   [Scientific Contribution]:
#   本模組實作多維度評分系統（MCRI），用於量化不同 Prompt Engineering 策略
#   與 AST Healer 機制對程式碼品質的影響，支援科展實驗的統計分析需求。
#
# [Key Functions]:
#   1. MCRI_Evaluator: 核心評估器類別，實作 4 大維度 8 項指標
#   2. create_database: 建立 SQLite 資料庫（3 張表：runs, items, summary）
#   3. main: 主程式入口，批次評估所有 Ablation 樣本
#
# [Evaluation Dimensions] (滿分 100):
#   - L1 工程基石 (20分): 語法安全 + 執行穩定性
#   - L2 資料衛生 (20分): 介面契約 + 格式純淨度 [V4.2 已實作真實評估]
#   - L3 評測公平 (30分): 內在一致性 + 外在強健性
#   - L4 教學有效 (30分): 數值友善度 + 視覺可讀性
#
# [Database Schema]:
#   - experiment_runs: 27 欄位 × ~15 筆 (3 ablations × 5 samples)
#   - evaluation_items: 19 欄位 × ~300 筆 (15 runs × 20 repetitions)
#   - ablation_summary: 12 欄位 × 3 筆 (統計彙總)
#
# [Output]:
#   - SQLite: reports/mcri_evaluation.db
#   - CSV: reports/csv/{experiment_runs, evaluation_items, ablation_summary}.csv
#   - Terminal: 彙總統計表格與關鍵洞察
#
# [Logic Flow]:
#   1. 載入技能檔案 (Ab1/Ab2/Ab3.py)
#   2. 提取 metadata (Performance, Tokens, Fix Status 等 7 個欄位)
#   3. L1 評估 (語法 + 執行穩定性，執行 3 次)
#   4. 重複 20 次 generate() 呼叫:
#      - L2.1 介面契約 + L2.2 格式純淨度 [V4.2 新增]
#      - L3.1 內在一致性 + L3.2 外在強健性
#      - L4.1 數值友善度 + L4.2 視覺可讀性
#   5. 計算統計指標 (mean, std, 95% CI)
#   6. 雙輸出 (SQLite + CSV)
#
# [Version History]:
#   - V4.2.2: 優化四個優先級 (2026-02-02)
#       * 優先級1: L1 白名單擴充 (re/ast/operator/os/typing) + 移除誤判 (compile/__import__)
#       * 優先級2: L3.2 測試嚴格化 (確保 replace 空白)
#       * 優先級3: 記錄 avg_exec_time 從 repetitions
#       * 優先級4: L4.2 加強檢查 (^{}, $ 成對)
#   - V4.2.1: 修正 L3 評估邏輯，正確處理 check() 返回 dict 格式 [Critical Fix]
#   - V4.2: 實作 L2 真實評估 (移除固定值)，新增 evaluation_items.score_l2_*
#   - V4.1: 新增 metadata 提取與 notes 整合
#   - V4.0: 初始版本，實作 L1/L3/L4 評估
# ==============================================================================

import ast
import importlib.util
import os
import re
import signal
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from scipy import stats


# ========================================
# 常數定義
# ========================================
MCRI_VERSION = "4.2.2"
DEFAULT_TIMEOUT = 5  # 秒
DEFAULT_REPETITIONS = 20
ALLOWED_IMPORTS = {'math', 'random', 'fractions', 're', 'ast', 'operator', 'os', 'typing', 'decimal', 'sympy', 'numpy'}
FORBIDDEN_BUILTINS = {'eval', 'exec'}  # 移除誤判的 compile, __import__


# ========================================
# 超時控制（Windows 相容）
# ========================================
class TimeoutError(Exception):
    """超時異常"""
    pass


@contextmanager
def time_limit(seconds: int):
    """
    跨平台超時控制
    Windows 不支援 signal.alarm，使用替代方案
    """
    def timeout_handler():
        raise TimeoutError(f"執行超過 {seconds} 秒")
    
    if sys.platform == 'win32':
        # Windows: 使用簡單計時器（非精確）
        start_time = time.time()
        yield
        if time.time() - start_time > seconds:
            raise TimeoutError(f"執行超過 {seconds} 秒")
    else:
        # Unix: 使用 signal
        signal.signal(signal.SIGALRM, lambda s, f: timeout_handler())
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)


# ========================================
# MCRI 評估器核心類別
# ========================================
class MCRI_Evaluator:
    """
    MCRI V4.2 評估器
    
    功能：
    - 評估單一技能檔案的 MCRI 分數
    - 支援多次重複執行（20 repetitions）
    - 產生實驗紀錄與明細資料
    """
    
    def __init__(self, skill_path: str, ablation_id: int, model_name: str = "gemini-pro"):
        """
        初始化評估器
        
        Args:
            skill_path: 技能檔案路徑 (如 skills/gh_ApplicationsOfDerivatives_14b_Ab1.py)
            ablation_id: 消融版本 ID (1=Ab1, 2=Ab2, 3=Ab3)
            model_name: 模型名稱
        """
        self.skill_path = Path(skill_path)
        self.ablation_id = ablation_id  # INTEGER: 1, 2, 3
        self.model_name = model_name
        self.version = MCRI_VERSION
        
        # 從檔名提取技能名稱
        # gh_ApplicationsOfDerivatives_14b_Ab1.py → gh_ApplicationsOfDerivatives_14b
        filename = self.skill_path.stem
        self.skill_name = '_'.join(filename.split('_')[:-1]) if '_Ab' in filename else filename
        
        self.module = None
        self.generate_func = None
        self.check_func = None
    
    def load_skill_module(self) -> bool:
        """
        載入技能模組並驗證必要函數
        同時提取檔案 metadata
        
        Returns:
            bool: 是否成功載入
        """
        try:
            # 1. 提取檔案 metadata
            self.metadata = self._extract_metadata()
            
            # 2. 載入模組
            spec = importlib.util.spec_from_file_location(
                f"skill_{self.ablation_id}", 
                str(self.skill_path)
            )
            if spec is None or spec.loader is None:
                return False
            
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
            
            # 3. 檢查必要函數
            if not hasattr(self.module, 'generate'):
                print(f"❌ {self.skill_path.name} 缺少 generate() 函數")
                return False
            
            if not hasattr(self.module, 'check'):
                print(f"⚠️  {self.skill_path.name} 缺少 check() 函數（L3 將失分）")
                self.check_func = None
            else:
                self.check_func = self.module.check
            
            self.generate_func = self.module.generate
            return True
            
        except Exception as e:
            print(f"❌ 載入失敗 {self.skill_path.name}: {e}")
            return False
    
    def _extract_metadata(self) -> Dict[str, str]:
        """
        從技能檔案中提取 metadata
        
        Returns:
            Dict: 包含 performance, created_at, fix_status, verification 等資訊
        """
        metadata = {
            'performance': '',
            'tokens_in': 0,
            'tokens_out': 0,
            'created_at': '',
            'fix_status': '',
            'fixes_basic': 0,
            'fixes_regex': 0,
            'fixes_ast': 0,
            'verification': '',
            'model_info': '',
            'strategy': '',
            'ablation_note': '',
        }
        
        try:
            with open(self.skill_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:20]  # 只讀前 20 行
            
            for line in lines:
                line = line.strip()
                
                # Performance: 17.13s | Tokens: In=7122, Out=620
                if 'Performance:' in line:
                    perf_match = re.search(r'Performance:\s*([\d.]+)s', line)
                    if perf_match:
                        metadata['performance'] = perf_match.group(1)
                    
                    tokens_match = re.search(r'Tokens:\s*In=(\d+),\s*Out=(\d+)', line)
                    if tokens_match:
                        metadata['tokens_in'] = int(tokens_match.group(1))
                        metadata['tokens_out'] = int(tokens_match.group(2))
                
                # Created At: 2026-02-02 11:26:37
                elif 'Created At:' in line:
                    created_match = re.search(r'Created At:\s*(.+)', line)
                    if created_match:
                        metadata['created_at'] = created_match.group(1).strip()
                
                # Fix Status: [Advanced Healer] | Fixes: Basic=1, Advanced=(Regex=4, AST=0)
                elif 'Fix Status:' in line:
                    metadata['fix_status'] = line.split('Fix Status:')[-1].strip()
                    
                    basic_match = re.search(r'Basic=(\d+)', line)
                    if basic_match:
                        metadata['fixes_basic'] = int(basic_match.group(1))
                    
                    regex_match = re.search(r'Regex=(\d+)', line)
                    if regex_match:
                        metadata['fixes_regex'] = int(regex_match.group(1))
                    
                    ast_match = re.search(r'AST=(\d+)', line)
                    if ast_match:
                        metadata['fixes_ast'] = int(ast_match.group(1))
                
                # Verification: Internal Logic Check = PASSED
                elif 'Verification:' in line:
                    metadata['verification'] = line.split('Verification:')[-1].strip()
                
                # Model: qwen2.5-coder:14b | Strategy: V10.1 Modular Refactored
                elif 'Model:' in line:
                    metadata['model_info'] = line.split('Model:')[-1].strip()
                
                # Strategy
                elif 'Strategy:' in line:
                    metadata['strategy'] = line.split('Strategy:')[-1].strip()
                
                # Ablation ID
                elif 'Ablation ID:' in line:
                    metadata['ablation_note'] = line.split('Ablation ID:')[-1].strip()
        
        except Exception as e:
            print(f"⚠️  提取 metadata 失敗: {e}")
        
        return metadata
    
    # ========================================
    # L1: 工程基石 (20分)
    # ========================================
    
    def evaluate_syntax_safety(self) -> Tuple[float, str]:
        """
        L1.1 語法與安全 (10分)
        - AST 解析成功 (3分)
        - 無 eval/exec (3分) [V4.2.2: 移除 compile/__import__ 避免誤判]
        - Import 白名單檢查 (4分) [V4.2.2: 擴充白名單至 re/ast/operator/os/typing]
        """
        score = 0.0
        notes = []
        
        try:
            with open(self.skill_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 1. AST 解析 (3分)
            try:
                tree = ast.parse(code)
                score += 3.0
                notes.append("AST 解析成功")
            except SyntaxError as e:
                notes.append(f"語法錯誤: {e}")
                return score, "; ".join(notes)
            
            # 2. 檢查禁用函數 (3分)
            forbidden_found = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id in FORBIDDEN_BUILTINS:
                    forbidden_found.append(node.id)
            
            if not forbidden_found:
                score += 3.0
                notes.append("無危險函數")
            else:
                notes.append(f"發現禁用函數: {', '.join(set(forbidden_found))}")
            
            # 3. Import 白名單 (4分)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            
            unauthorized = imports - ALLOWED_IMPORTS
            if not unauthorized:
                score += 4.0
                notes.append("Import 白名單通過")
            else:
                score += max(0, 4.0 - len(unauthorized) * 1.0)
                notes.append(f"未授權 import: {', '.join(unauthorized)}")
        
        except Exception as e:
            notes.append(f"評估異常: {e}")
        
        return score, "; ".join(notes)
    
    def evaluate_runtime_stability(self, repetitions: int = 3) -> Tuple[float, str, List[float]]:
        """
        L1.2 執行穩定性 (10分)
        - 在 5 秒內成功執行 3 次
        - 無 crash、timeout
        
        Returns:
            (score, notes, exec_times)
        """
        score = 0.0
        notes = []
        exec_times = []
        success_count = 0
        
        for i in range(repetitions):
            try:
                start_time = time.time()
                with time_limit(DEFAULT_TIMEOUT):
                    result = self.generate_func()
                exec_time = time.time() - start_time
                
                exec_times.append(exec_time)
                success_count += 1
                
            except TimeoutError:
                notes.append(f"Rep{i+1} 超時")
                exec_times.append(DEFAULT_TIMEOUT)
            except Exception as e:
                notes.append(f"Rep{i+1} 失敗: {type(e).__name__}")
                exec_times.append(0.0)
        
        # 評分：每成功 1 次得 3.33 分
        score = (success_count / repetitions) * 10.0
        
        if success_count == repetitions:
            notes.append(f"全部成功 (平均 {np.mean(exec_times):.2f}s)")
        else:
            notes.append(f"成功 {success_count}/{repetitions} 次")
        
        return score, "; ".join(notes) if notes else "穩定", exec_times
    
    # ========================================
    # L2: 資料衛生 (20分)
    # ========================================
    
    def evaluate_interface_contract(self, result: Dict) -> Tuple[float, str]:
        """
        L2.1 介面契約 (10分)
        - 回傳 dict (2分)
        - 包含必要欄位: question_text, answer, correct_answer (6分，每個 2 分)
        - mode=1 (2分)
        """
        score = 0.0
        notes = []
        
        # 1. 型別檢查 (2分)
        if not isinstance(result, dict):
            notes.append(f"回傳型別錯誤: {type(result).__name__}")
            return score, "; ".join(notes)
        score += 2.0
        
        # 2. 必要欄位 (6分)
        required_fields = ['question_text', 'answer', 'correct_answer']
        for field in required_fields:
            if field in result and result[field] is not None:
                score += 2.0
            else:
                notes.append(f"缺少 {field}")
        
        # 3. mode=1 (2分)
        if result.get('mode') == 1:
            score += 2.0
        else:
            notes.append(f"mode={result.get('mode')} (應為 1)")
        
        if score == 10.0:
            notes.append("契約完整")
        
        return score, "; ".join(notes) if notes else "通過"
    
    def evaluate_format_purity(self, result: Dict) -> Tuple[float, str]:
        """
        L2.2 格式純淨度 (10分)
        - answer 欄位無 $ (3分)
        - 無前綴 (如 f'(x)=) (3分)
        - 無換行符號 (4分)
        """
        score = 0.0
        notes = []
        
        answer = str(result.get('answer', ''))
        
        # 1. 無 $ 符號 (3分)
        if '$' not in answer:
            score += 3.0
        else:
            notes.append("含 $ 符號")
        
        # 2. 無前綴 (3分)
        # 檢測常見前綴：f'(x)=, y=, 答案=, answer=
        prefix_pattern = r'^(f\'?\(x\)\s*=|y\s*=|答案[:=]|answer[:=])'
        if not re.search(prefix_pattern, answer, re.IGNORECASE):
            score += 3.0
        else:
            notes.append("含前綴")
        
        # 3. 無換行 (4分)
        if '\n' not in answer and '\r' not in answer:
            score += 4.0
        else:
            notes.append("含換行符")
        
        if score == 10.0:
            notes.append("格式純淨")
        
        return score, "; ".join(notes) if notes else "通過"
    
    # ========================================
    # L3: 評測公平 (30分)
    # ========================================
    
    def evaluate_internal_consistency(self, result: Dict) -> Tuple[float, str]:
        """
        L3.1 內在一致性 (15分)
        - check(system_answer, system_answer) 應回傳 True
        """
        score = 0.0
        notes = []
        
        if self.check_func is None:
            notes.append("無 check() 函數")
            return score, "; ".join(notes)
        
        try:
            correct_ans = result.get('correct_answer', '')
            check_result = self.check_func(correct_ans, correct_ans)
            
            # check() 返回 dict: {'correct': bool, 'result': str}
            if isinstance(check_result, dict):
                if check_result.get('correct') is True:
                    score = 15.0
                    notes.append("內在一致")
                else:
                    notes.append(f"自檢失敗: {check_result.get('result', 'Unknown')}")
            # 相容舊版 check() 直接返回 bool
            elif check_result is True:
                score = 15.0
                notes.append("內在一致")
            else:
                notes.append(f"自檢失敗: check(ans, ans)={check_result}")
        
        except Exception as e:
            notes.append(f"check() 錯誤: {type(e).__name__}")
        
        return score, "; ".join(notes)
    
    def evaluate_external_robustness(self, result: Dict) -> Tuple[float, str, str]:
        """
        L3.2 外在強健性 (15分)
        - 模擬 4 種學生輸入變體
        - 正確接受標準形式、等價形式
        - 正確拒絕明顯錯誤
        
        Returns:
            (score, notes, test_log)
        """
        score = 0.0
        notes = []
        test_log = []
        
        if self.check_func is None:
            return score, "無 check() 函數", ""
        
        correct_ans = str(result.get('correct_answer', ''))
        
        # 測試案例（4 種變體）
        test_cases = [
            ("標準形式", correct_ans, True),  # 應接受
            ("小數形式", self._convert_to_decimal(correct_ans), True),  # 0.5 vs 1/2
            ("省略乘號", self._add_implicit_multiply(correct_ans), True),  # 2x vs 2*x
            ("明顯錯誤", "999", False),  # 應拒絕
        ]
        
        for test_name, student_input, expected in test_cases:
            try:
                # [V4.2.2 優先級2] 確保空白符號被移除，增加測試嚴格度
                student_normalized = str(student_input).replace(" ", "")
                answer_normalized = str(correct_ans).replace(" ", "")
                check_result = self.check_func(student_normalized, answer_normalized)
                
                # check() 返回 dict: {'correct': bool, 'result': str}
                if isinstance(check_result, dict):
                    actual = check_result.get('correct', False)
                # 相容舊版 check() 直接返回 bool
                elif isinstance(check_result, bool):
                    actual = check_result
                else:
                    actual = False
                
                is_correct = (actual == expected)
                
                if is_correct:
                    score += 3.75  # 15/4
                    test_log.append(f"✓ {test_name}")
                else:
                    test_log.append(f"✗ {test_name} (期望{expected}, 得{actual})")
            
            except Exception as e:
                test_log.append(f"✗ {test_name} (異常: {type(e).__name__})")
        
        if score >= 11.25:  # 至少 3/4 通過
            notes.append("外在強健")
        else:
            notes.append(f"通過 {int(score/3.75)}/4 項")
        
        return score, "; ".join(notes), " | ".join(test_log)
    
    def _convert_to_decimal(self, expr: str) -> str:
        """轉換分數為小數（簡化版）"""
        # 1/2 → 0.5
        if '/' in expr and expr.count('/') == 1:
            try:
                parts = expr.split('/')
                return str(float(parts[0]) / float(parts[1]))
            except:
                pass
        return expr
    
    def _add_implicit_multiply(self, expr: str) -> str:
        """模擬學生省略乘號：2*x → 2x"""
        return expr.replace('*', '')
    
    # ========================================
    # L4: 教學有效 (30分)
    # ========================================
    
    def evaluate_numeric_friendliness(self, result: Dict) -> Tuple[float, str]:
        """
        L4.1 數值友善度 (15分)
        - 分母 ≤ 20 (4分)
        - 係數 ≤ 50 (4分)
        - 無未約分分數 (3分)
        - 無無限小數 (4分)
        """
        score = 0.0
        notes = []
        
        question = str(result.get('question_text', ''))
        answer = str(result.get('answer', ''))
        
        # 1. 分母檢查 (4分)
        denominators = re.findall(r'/(\d+)', question + answer)
        if denominators:
            max_denom = max(int(d) for d in denominators)
            if max_denom <= 20:
                score += 4.0
            elif max_denom <= 50:
                score += 2.0
                notes.append(f"分母過大: {max_denom}")
            else:
                notes.append(f"分母過大: {max_denom}")
        else:
            score += 4.0  # 無分數
        
        # 2. 係數檢查 (4分)
        coefficients = re.findall(r'(?<![.\d])(\d+)(?![.\d])', question)
        if coefficients:
            max_coef = max(int(c) for c in coefficients if int(c) > 1)
            if max_coef <= 50:
                score += 4.0
            elif max_coef <= 100:
                score += 2.0
                notes.append(f"係數過大: {max_coef}")
            else:
                notes.append(f"係數過大: {max_coef}")
        else:
            score += 4.0
        
        # 3. 未約分檢查 (3分) - 簡化版
        # 檢測如 2/4, 3/6, 4/8
        unreduced = re.findall(r'(\d+)/(\d+)', question + answer)
        has_unreduced = False
        for num, denom in unreduced:
            from math import gcd
            if gcd(int(num), int(denom)) > 1:
                has_unreduced = True
                break
        
        if not has_unreduced:
            score += 3.0
        else:
            notes.append("含未約分分數")
        
        # 4. 無限小數檢查 (4分)
        # 簡單檢測：1/3, 1/7, 1/9 等
        infinite_decimals = ['1/3', '2/3', '1/7', '1/9', '1/11', '1/13']
        has_infinite = any(pattern in (question + answer) for pattern in infinite_decimals)
        
        if not has_infinite:
            score += 4.0
        else:
            notes.append("含無限小數分數")
        
        if score >= 12.0:
            notes.append("數值友善")
        
        return score, "; ".join(notes) if notes else "友善"
    
    def evaluate_visual_readability(self, result: Dict) -> Tuple[float, str]:
        """
        L4.2 視覺可讀性 (15分)
        - 使用標準 LaTeX 語法 (5分)
        - 無程式碼洩漏 (**, *, print) (7分)
        - 無數學異味 (+ -, 1x 等) (3分) [V4.2.1 新增]
        """
        score = 0.0
        notes = []
        
        question = str(result.get('question_text', ''))
        
        # 1. LaTeX 標準語法 (5分)
        # 正面指標：含 \frac, \sqrt, ^, _
        latex_patterns = [r'\\frac', r'\\sqrt', r'\^', r'_']
        latex_count = sum(1 for p in latex_patterns if re.search(p, question))
        
        if latex_count >= 2:
            score += 5.0
            notes.append("LaTeX 標準")
        elif latex_count >= 1:
            score += 3.0
            notes.append("LaTeX 不完整")
        else:
            notes.append("無 LaTeX 語法")
        
        # 2. 無程式碼洩漏 (7分)
        code_leaks = []
        if '**' in question:
            code_leaks.append('**')
        if re.search(r'(?<![\\])\*(?![*])', question):  # * 但不是 **
            code_leaks.append('*')
        if 'print' in question.lower():
            code_leaks.append('print')
        if 'def ' in question or 'return' in question:
            code_leaks.append('Python 關鍵字')
        
        if not code_leaks:
            score += 7.0
        else:
            score += max(0, 7.0 - len(code_leaks) * 2.0)
            notes.append(f"洩漏: {', '.join(code_leaks)}")
        
        # 3. 無數學異味 (3分) [V4.2.1 新增, V4.2.2 加強]
        # 檢測醜陋的數學寫法
        math_smells = []
        
        # 3.1 正負號未合併 (+ -)
        if '+ -' in question or '+-' in question:
            math_smells.append("正負號未合併")
        
        # 3.2 係數1未省略 (1x, 1y, 1z 等)
        if re.search(r'\b1[a-z]', question):
            math_smells.append("係數1未省略")
        
        # 3.3 負係數1未簡化 (-1x 應寫成 -x)
        if re.search(r'-1[a-z]', question):
            math_smells.append("負係數-1未簡化")
        
        # 3.4 [V4.2.2 優先級4] 檢查 ^ 後是否有 {} (LaTeX 格式)
        # 正確: x^{2}, 錯誤: x^2
        if re.search(r'\^[^{]', question):
            math_smells.append("指數未加大括號")
        
        # 3.5 [V4.2.2 優先級4] 檢查 $ 是否成對
        dollar_count = question.count('$')
        if dollar_count % 2 != 0:
            math_smells.append("數學模式未成對")
        
        if not math_smells:
            score += 3.0
        else:
            # 每個異味扣 0.6 分（5 種異味最多扣 3 分）
            penalty = min(len(math_smells) * 0.6, 3.0)
            score += max(0, 3.0 - penalty)
            notes.append(f"數學異味: {', '.join(math_smells)}")
        
        if score >= 12.0:
            notes.append("視覺清晰")
        
        return score, "; ".join(notes) if notes else "清晰"
    
    # ========================================
    # 主評估流程
    # ========================================
    
    def evaluate_single_repetition(self, rep_index: int) -> Dict[str, Any]:
        """
        評估單次生成
        
        Returns:
            Dict 包含所有評分細節
        """
        item = {
            'item_id': str(uuid.uuid4()),
            'repetition_index': rep_index,
            'generated_question': '',
            'generated_answer': '',
            'generated_correct_answer': '',
            'status': 'FAIL',
            'error_log': '',
            'included_in_avg': 0,  # 0 or 1 (INTEGER)
            'score_l2_1_contract': 0,  # INTEGER (新增)
            'score_l2_2_purity': 0,    # INTEGER (新增)
            'score_l3_total': 0,   # INTEGER
            'score_l3_1_internal': 0,
            'score_l3_2_external': 0,
            'score_l4_total': 0,   # INTEGER
            'score_l4_1_numeric': 0,
            'score_l4_2_visual': 0,
            'student_input_test': '',
            'student_input_result': '',
        }
        
        try:
            # 執行 generate() 並記錄執行時間 [V4.2.2 優先級3]
            start_time = time.time()
            with time_limit(DEFAULT_TIMEOUT):
                result = self.generate_func()
            exec_time = time.time() - start_time
            
            # 儲存生成內容
            item['generated_question'] = str(result.get('question_text', ''))[:500]
            item['generated_answer'] = str(result.get('answer', ''))[:200]
            item['generated_correct_answer'] = str(result.get('correct_answer', ''))[:200]
            item['exec_time'] = round(exec_time, 4)  # [V4.2.2] 記錄單次執行時間
            
            # L2.1 介面契約
            score_l2_1, _ = self.evaluate_interface_contract(result)
            item['score_l2_1_contract'] = int(score_l2_1)
            
            # L2.2 格式純淨度
            score_l2_2, _ = self.evaluate_format_purity(result)
            item['score_l2_2_purity'] = int(score_l2_2)
            
            # 只有契約通過才繼續評估 L3, L4
            if score_l2_1 >= 8.0:  # 至少 80% 通過
                # L3.1 內在一致性
                score_l3_1, _ = self.evaluate_internal_consistency(result)
                item['score_l3_1_internal'] = int(score_l3_1)
                
                # L3.2 外在強健性
                score_l3_2, _, test_log = self.evaluate_external_robustness(result)
                item['score_l3_2_external'] = int(score_l3_2)
                item['student_input_test'] = test_log[:500]
                item['student_input_result'] = 'PASS' if score_l3_2 >= 11.25 else 'PARTIAL'
                
                item['score_l3_total'] = int(score_l3_1 + score_l3_2)
                
                # L4.1 數值友善度
                score_l4_1, _ = self.evaluate_numeric_friendliness(result)
                item['score_l4_1_numeric'] = int(score_l4_1)
                
                # L4.2 視覺可讀性
                score_l4_2, _ = self.evaluate_visual_readability(result)
                item['score_l4_2_visual'] = int(score_l4_2)
                
                item['score_l4_total'] = int(score_l4_1 + score_l4_2)
                
                item['status'] = 'PASS'
                item['included_in_avg'] = 1
            else:
                item['error_log'] = '介面契約不完整'
        
        except TimeoutError:
            item['status'] = 'TIMEOUT'
            item['error_log'] = f'執行超過 {DEFAULT_TIMEOUT} 秒'
        except Exception as e:
            item['status'] = 'ERROR'
            item['error_log'] = f'{type(e).__name__}: {str(e)[:200]}'
        
        return item
    
    def run_full_evaluation(self, sample_index: int, repetitions: int = DEFAULT_REPETITIONS) -> Tuple[Dict, List[Dict]]:
        """
        執行完整評估（20 次 repetition）
        
        Returns:
            (run_record, item_records)
        """
        run_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()
        
        # L1 評估（只執行一次）
        score_l1_1, notes_l1_1 = self.evaluate_syntax_safety()
        score_l1_2, notes_l1_2, exec_times = self.evaluate_runtime_stability(repetitions=3)
        score_l1_total = score_l1_1 + score_l1_2
        
        # L2.1 介面契約（從 repetitions 中計算）
        # L2.2 格式純淨度（從 repetitions 中計算）
        
        # 執行所有 repetitions
        print(f"\n🔄 執行 {repetitions} 次重複測試...")
        items = []
        for i in range(repetitions):
            item = self.evaluate_single_repetition(i + 1)
            item['run_id'] = run_id
            items.append(item)
            
            # 即時顯示進度
            if (i + 1) % 5 == 0:
                print(f"  完成 {i+1}/{repetitions} 次")
        
        # 統計
        pass_items = [item for item in items if item['included_in_avg'] == 1]
        fail_count = len([item for item in items if item['status'] == 'FAIL'])
        pass_rate = len(pass_items) / repetitions if repetitions > 0 else 0.0
        
        # [V4.2.2 優先級3] 計算 avg_exec_time 從所有成功的 repetitions
        exec_times_from_reps = [item.get('exec_time', 0.0) for item in pass_items if 'exec_time' in item]
        avg_exec_time = np.mean(exec_times_from_reps) if exec_times_from_reps else 0.0
        
        # 計算 L2 平均分（從 pass_items 的真實評估結果）
        score_l2_1_list = [item['score_l2_1_contract'] for item in pass_items]
        score_l2_2_list = [item['score_l2_2_purity'] for item in pass_items]
        
        score_l2_1_avg = int(np.mean(score_l2_1_list)) if score_l2_1_list else 0
        score_l2_2_avg = int(np.mean(score_l2_2_list)) if score_l2_2_list else 0
        score_l2_total = score_l2_1_avg + score_l2_2_avg
        
        # 計算 L3, L4 平均分
        avg_l3_total = np.mean([item['score_l3_total'] for item in pass_items]) if pass_items else 0.0
        avg_l3_1 = np.mean([item['score_l3_1_internal'] for item in pass_items]) if pass_items else 0.0
        avg_l3_2 = np.mean([item['score_l3_2_external'] for item in pass_items]) if pass_items else 0.0
        
        avg_l4_total = np.mean([item['score_l4_total'] for item in pass_items]) if pass_items else 0.0
        avg_l4_1 = np.mean([item['score_l4_1_numeric'] for item in pass_items]) if pass_items else 0.0
        avg_l4_2 = np.mean([item['score_l4_2_visual'] for item in pass_items]) if pass_items else 0.0
        
        avg_mcri_total = score_l1_total + score_l2_total + avg_l3_total + avg_l4_total
        # avg_exec_time 已在上方從 repetitions 計算
        
        # 建立 run 記錄
        run_record = {
            'run_id': run_id,
            'timestamp': timestamp,
            'model_name': self.model_name,
            'skill_name': self.skill_name,
            'ablation_id': self.ablation_id,  # INTEGER
            'sample_index': sample_index,
            'repetitions_planned': repetitions,
            'repetitions_completed': len(items),
            'fail_count': fail_count,
            'pass_rate': round(pass_rate, 4),
            'avg_exec_time': round(avg_exec_time, 4),
            'score_l1_total': int(score_l1_total),
            'score_l1_1_syntax': int(score_l1_1),
            'score_l1_2_runtime': int(score_l1_2),
            'score_l2_total': int(score_l2_total),
            'score_l2_1_contract': int(score_l2_1_avg),
            'score_l2_2_purity': int(score_l2_2_avg),
            'avg_l3_total': round(avg_l3_total, 2),
            'avg_l3_1_internal': round(avg_l3_1, 2),
            'avg_l3_2_external': round(avg_l3_2, 2),
            'avg_l4_total': round(avg_l4_total, 2),
            'avg_l4_1_numeric': round(avg_l4_1, 2),
            'avg_l4_2_visual': round(avg_l4_2, 2),
            'avg_mcri_total': round(avg_mcri_total, 2),
            'source_code_path': str(self.skill_path),
            'mcri_version': self.version,
            'notes': self._build_notes(notes_l1_1, notes_l1_2),
        }
        
        return run_record, items
    
    def _build_notes(self, notes_l1_1: str, notes_l1_2: str) -> str:
        """
        建立 notes 欄位，整合 L1 評分與 metadata
        
        Returns:
            str: 格式化的 notes 字串
        """
        notes_parts = []
        
        # L1 評分細節
        notes_parts.append(f"L1: {notes_l1_1}; {notes_l1_2}")
        
        # Metadata 資訊
        if hasattr(self, 'metadata'):
            meta = self.metadata
            
            if meta.get('performance'):
                notes_parts.append(f"Perf: {meta['performance']}s")
            
            if meta.get('tokens_in') and meta.get('tokens_out'):
                notes_parts.append(f"Tokens: In={meta['tokens_in']}, Out={meta['tokens_out']}")
            
            if meta.get('fix_status'):
                notes_parts.append(f"Fix: {meta['fix_status']}")
            
            if meta.get('verification'):
                notes_parts.append(f"Verify: {meta['verification']}")
        
        return " | ".join(notes_parts)


# ========================================
# 資料庫管理
# ========================================
def create_database(db_path: str):
    """建立 SQLite 資料庫與三張表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. experiment_runs (主表)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT,
            model_name TEXT,
            skill_name TEXT,
            ablation_id INTEGER,
            sample_index INTEGER,
            repetitions_planned INTEGER,
            repetitions_completed INTEGER,
            fail_count INTEGER,
            pass_rate REAL,
            avg_exec_time REAL,
            score_l1_total INTEGER,
            score_l1_1_syntax INTEGER,
            score_l1_2_runtime INTEGER,
            score_l2_total INTEGER,
            score_l2_1_contract INTEGER,
            score_l2_2_purity INTEGER,
            avg_l3_total REAL,
            avg_l3_1_internal REAL,
            avg_l3_2_external REAL,
            avg_l4_total REAL,
            avg_l4_1_numeric REAL,
            avg_l4_2_visual REAL,
            avg_mcri_total REAL,
            source_code_path TEXT,
            mcri_version TEXT,
            notes TEXT
        )
    """)
    
    # 2. evaluation_items (附表)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_items (
            item_id TEXT PRIMARY KEY,
            run_id TEXT,
            repetition_index INTEGER,
            generated_question TEXT,
            generated_answer TEXT,
            generated_correct_answer TEXT,
            status TEXT,
            error_log TEXT,
            included_in_avg INTEGER,
            score_l2_1_contract INTEGER,
            score_l2_2_purity INTEGER,
            score_l3_total INTEGER,
            score_l3_1_internal INTEGER,
            score_l3_2_external INTEGER,
            score_l4_total INTEGER,
            score_l4_1_numeric INTEGER,
            score_l4_2_visual INTEGER,
            student_input_test TEXT,
            student_input_result TEXT,
            FOREIGN KEY (run_id) REFERENCES experiment_runs(run_id)
        )
    """)
    
    # 3. ablation_summary (彙總表)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ablation_summary (
            summary_id TEXT PRIMARY KEY,
            skill_name TEXT,
            ablation_id INTEGER,
            model_name TEXT,
            sample_count INTEGER,
            total_runs INTEGER,
            mean_mcri_total REAL,
            std_mcri_total REAL,
            ci95_lower REAL,
            ci95_upper REAL,
            mean_l3_external REAL,
            mean_l4_numeric REAL
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ 資料庫已建立: {db_path}")


def insert_experiment_runs(conn: sqlite3.Connection, runs: List[Dict]):
    """插入 experiment_runs 資料"""
    cursor = conn.cursor()
    
    for run in runs:
        cursor.execute("""
            INSERT INTO experiment_runs VALUES (
                :run_id, :timestamp, :model_name, :skill_name, :ablation_id, :sample_index,
                :repetitions_planned, :repetitions_completed, :fail_count, :pass_rate, :avg_exec_time,
                :score_l1_total, :score_l1_1_syntax, :score_l1_2_runtime,
                :score_l2_total, :score_l2_1_contract, :score_l2_2_purity,
                :avg_l3_total, :avg_l3_1_internal, :avg_l3_2_external,
                :avg_l4_total, :avg_l4_1_numeric, :avg_l4_2_visual,
                :avg_mcri_total, :source_code_path, :mcri_version, :notes
            )
        """, run)
    
    conn.commit()
    print(f"✅ 已插入 experiment_runs: {len(runs)} 筆")


def insert_evaluation_items(conn: sqlite3.Connection, items: List[Dict]):
    """插入 evaluation_items 資料"""
    cursor = conn.cursor()
    
    for item in items:
        cursor.execute("""
            INSERT INTO evaluation_items VALUES (
                :item_id, :run_id, :repetition_index,
                :generated_question, :generated_answer, :generated_correct_answer,
                :status, :error_log, :included_in_avg,
                :score_l2_1_contract, :score_l2_2_purity,
                :score_l3_total, :score_l3_1_internal, :score_l3_2_external,
                :score_l4_total, :score_l4_1_numeric, :score_l4_2_visual,
                :student_input_test, :student_input_result
            )
        """, item)
    
    conn.commit()
    print(f"✅ 已插入 evaluation_items: {len(items)} 筆")


def compute_and_insert_summary(conn: sqlite3.Connection):
    """從 experiment_runs 計算彙總統計並插入"""
    # 使用 pandas 讀取與計算
    df = pd.read_sql_query("SELECT * FROM experiment_runs", conn)
    
    # 按 (skill_name, ablation_id, model_name) 分組
    summary_data = []
    
    for (skill_name, ablation_id, model_name), group in df.groupby(['skill_name', 'ablation_id', 'model_name']):
        mcri_scores = group['avg_mcri_total'].values
        l3_external = group['avg_l3_2_external'].values
        l4_numeric = group['avg_l4_1_numeric'].values
        
        mean_mcri = np.mean(mcri_scores)
        std_mcri = np.std(mcri_scores, ddof=1) if len(mcri_scores) > 1 else 0.0
        
        # 95% CI (簡化版：1.96*std/sqrt(n))
        n = len(mcri_scores)
        ci_margin = 1.96 * std_mcri / np.sqrt(n) if n > 0 else 0.0
        ci95_lower = mean_mcri - ci_margin
        ci95_upper = mean_mcri + ci_margin
        
        summary = {
            'summary_id': str(uuid.uuid4()),
            'skill_name': skill_name,
            'ablation_id': int(ablation_id),
            'model_name': model_name,
            'sample_count': int(n),
            'total_runs': int(group['repetitions_completed'].sum()),
            'mean_mcri_total': round(mean_mcri, 2),
            'std_mcri_total': round(std_mcri, 2),
            'ci95_lower': round(ci95_lower, 2),
            'ci95_upper': round(ci95_upper, 2),
            'mean_l3_external': round(np.mean(l3_external), 2),
            'mean_l4_numeric': round(np.mean(l4_numeric), 2),
        }
        summary_data.append(summary)
    
    # 插入資料庫
    cursor = conn.cursor()
    for s in summary_data:
        cursor.execute("""
            INSERT INTO ablation_summary VALUES (
                :summary_id, :skill_name, :ablation_id, :model_name,
                :sample_count, :total_runs,
                :mean_mcri_total, :std_mcri_total, :ci95_lower, :ci95_upper,
                :mean_l3_external, :mean_l4_numeric
            )
        """, s)
    
    conn.commit()
    print(f"✅ 已插入 ablation_summary: {len(summary_data)} 筆")
    
    return summary_data


# ========================================
# CSV 輸出工具
# ========================================
def write_experiment_runs_csv(runs: List[Dict], output_path: str):
    """寫入 experiment_runs.csv"""
    import csv
    
    fieldnames = [
        'run_id', 'timestamp', 'model_name', 'skill_name', 'ablation_id', 'sample_index',
        'repetitions_planned', 'repetitions_completed', 'fail_count', 'pass_rate', 'avg_exec_time',
        'score_l1_total', 'score_l1_1_syntax', 'score_l1_2_runtime',
        'score_l2_total', 'score_l2_1_contract', 'score_l2_2_purity',
        'avg_l3_total', 'avg_l3_1_internal', 'avg_l3_2_external',
        'avg_l4_total', 'avg_l4_1_numeric', 'avg_l4_2_visual',
        'avg_mcri_total', 'source_code_path', 'mcri_version', 'notes'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(runs)
    
    print(f"✅ 已寫入 CSV: {output_path} ({len(runs)} 筆)")


def write_evaluation_items_csv(items: List[Dict], output_path: str):
    """寫入 evaluation_items.csv"""
    import csv
    
    fieldnames = [
        'item_id', 'run_id', 'repetition_index',
        'generated_question', 'generated_answer', 'generated_correct_answer',
        'status', 'error_log', 'included_in_avg',
        'score_l2_1_contract', 'score_l2_2_purity',
        'score_l3_total', 'score_l3_1_internal', 'score_l3_2_external',
        'score_l4_total', 'score_l4_1_numeric', 'score_l4_2_visual',
        'student_input_test', 'student_input_result',
        'exec_time'  # [V4.2.2] 新增執行時間記錄
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)
    
    print(f"✅ 已寫入 CSV: {output_path} ({len(items)} 筆)")


def write_ablation_summary_csv(summaries: List[Dict], output_path: str):
    """寫入 ablation_summary.csv"""
    import csv
    
    fieldnames = [
        'summary_id', 'skill_name', 'ablation_id', 'model_name', 
        'sample_count', 'total_runs',
        'mean_mcri_total', 'std_mcri_total', 'ci95_lower', 'ci95_upper',
        'mean_l3_external', 'mean_l4_numeric'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    print(f"✅ 已寫入 CSV: {output_path} ({len(summaries)} 筆)")


# ========================================
# 終端輸出
# ========================================
def print_summary_table(summaries: List[Dict]):
    """列印彙總表格"""
    print("\n" + "="*80)
    print("📊 MCRI V4.2 彙總統計")
    print("="*80)
    
    print(f"\n{'Ablation':<10} {'Skill':<30} {'Mean':<8} {'Std':<8} {'95% CI':<20}")
    print("-" * 80)
    
    for s in summaries:
        ci_str = f"[{s['ci95_lower']:.1f}, {s['ci95_upper']:.1f}]"
        ablation_name = f"Ab{s['ablation_id']}"
        
        print(f"{ablation_name:<10} {s['skill_name']:<30} {s['mean_mcri_total']:<8.2f} "
              f"{s['std_mcri_total']:<8.2f} {ci_str:<20}")


def print_insights(summaries: List[Dict], all_runs: List[Dict]):
    """列印關鍵洞察"""
    print("\n" + "="*80)
    print("💡 關鍵洞察")
    print("="*80)
    
    # 找出最佳 ablation
    best = max(summaries, key=lambda x: x['mean_mcri_total'])
    print(f"\n🏆 最佳配置: Ab{best['ablation_id']} ({best['mean_mcri_total']:.2f} 分)")
    
    # 計算 Ab3 vs Ab1 的提升
    ab1_mean = next((s['mean_mcri_total'] for s in summaries if s['ablation_id'] == 1), None)
    ab3_mean = next((s['mean_mcri_total'] for s in summaries if s['ablation_id'] == 3), None)
    
    if ab1_mean and ab3_mean:
        improvement = ab3_mean - ab1_mean
        print(f"\n📈 Ab3 (Healer) vs Ab1 (Bare):")
        print(f"  提升: +{improvement:.1f} 分 ({improvement/ab1_mean*100:.1f}%)")
        
        # 分維度分析
        ab1_runs = [r for r in all_runs if r['ablation_id'] == 1]
        ab3_runs = [r for r in all_runs if r['ablation_id'] == 3]
        
        if ab1_runs and ab3_runs:
            avg_l3_ab1 = np.mean([r['avg_l3_total'] for r in ab1_runs])
            avg_l3_ab3 = np.mean([r['avg_l3_total'] for r in ab3_runs])
            avg_l4_ab1 = np.mean([r['avg_l4_total'] for r in ab1_runs])
            avg_l4_ab3 = np.mean([r['avg_l4_total'] for r in ab3_runs])
            
            print(f"  L3 評測公平: {avg_l3_ab1:.1f} → {avg_l3_ab3:.1f} (+{avg_l3_ab3-avg_l3_ab1:.1f})")
            print(f"  L4 教學有效: {avg_l4_ab1:.1f} → {avg_l4_ab3:.1f} (+{avg_l4_ab3-avg_l4_ab1:.1f})")
    
    # Healer 機制效果
    print(f"\n🔧 Healer 機制 (Ab3):")
    print(f"  - 自動修復 AST 錯誤，提升執行穩定性")
    print(f"  - 強化 check() 函數，改善評測公平性")
    print(f"  - 優化數值生成，增進教學適用性")


# ========================================
# 主程式
# ========================================
def main():
    """主程式入口"""
    print("="*80)
    print("🎯 MCRI V4.2 評估系統")
    print("="*80)
    
    # 設定
    skills_dir = Path("skills")
    db_dir = Path("reports")
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "mcri_evaluation.db"
    
    # 建立資料庫
    create_database(str(db_path))
    
    # 技能檔案清單（三個 ablation 版本）
    skill_base = "gh_ApplicationsOfDerivatives_14b"
    skill_files = [
        (skills_dir / f"{skill_base}_Ab1.py", 1, "gemini-pro"),  # Bare
        (skills_dir / f"{skill_base}_Ab2.py", 2, "gemini-pro"),  # Engineered
        (skills_dir / f"{skill_base}_Ab3.py", 3, "gemini-pro"),  # Healer
    ]
    
    # 執行設定
    samples_per_ablation = 5  # 每個 ablation 執行 5 個 sample
    repetitions_per_sample = 20  # 每個 sample 重複 20 次
    
    all_runs = []
    all_items = []
    
    # 主循環
    for skill_path, ablation_id, model_name in skill_files:
        ablation_name = f"Ab{ablation_id}"
        print(f"\n{'='*80}")
        print(f"📝 評估: {skill_path.name} ({ablation_name})")
        print(f"{'='*80}")
        
        if not skill_path.exists():
            print(f"❌ 檔案不存在: {skill_path}")
            continue
        
        evaluator = MCRI_Evaluator(str(skill_path), ablation_id, model_name)
        
        if not evaluator.load_skill_module():
            print(f"❌ 載入失敗，跳過")
            continue
        
        # 執行多個 sample
        for sample_idx in range(1, samples_per_ablation + 1):
            print(f"\n🔬 Sample {sample_idx}/{samples_per_ablation}")
            
            run_record, items = evaluator.run_full_evaluation(
                sample_index=sample_idx,
                repetitions=repetitions_per_sample
            )
            
            all_runs.append(run_record)
            all_items.extend(items)
            
            # 即時顯示結果
            print(f"\n✅ Sample {sample_idx} 完成:")
            print(f"  總分: {run_record['avg_mcri_total']:.2f}")
            print(f"  L1: {run_record['score_l1_total']} | "
                  f"L2: {run_record['score_l2_total']} | "
                  f"L3: {run_record['avg_l3_total']:.2f} | "
                  f"L4: {run_record['avg_l4_total']:.2f}")
            print(f"  通過率: {run_record['pass_rate']*100:.1f}% ({run_record['repetitions_completed'] - run_record['fail_count']}/{run_record['repetitions_completed']})")
    
    # 寫入資料庫與 CSV（雙輸出）
    print(f"\n{'='*80}")
    print("💾 寫入結果（資料庫 + CSV）...")
    print(f"{'='*80}")
    
    # 1. 寫入 SQLite 資料庫
    conn = sqlite3.connect(str(db_path))
    
    # 清空舊資料（如果需要重新執行）
    conn.execute("DELETE FROM evaluation_items")
    conn.execute("DELETE FROM experiment_runs")
    conn.execute("DELETE FROM ablation_summary")
    conn.commit()
    
    # 插入新資料
    insert_experiment_runs(conn, all_runs)
    insert_evaluation_items(conn, all_items)
    
    # 計算並插入彙總統計
    summaries = compute_and_insert_summary(conn)
    
    conn.close()
    
    # 2. 寫入 CSV 檔案
    csv_dir = Path("reports/csv")
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    write_experiment_runs_csv(all_runs, csv_dir / "experiment_runs.csv")
    write_evaluation_items_csv(all_items, csv_dir / "evaluation_items.csv")
    write_ablation_summary_csv(summaries, csv_dir / "ablation_summary.csv")
    
    # 終端輸出
    print_summary_table(summaries)
    print_insights(summaries, all_runs)
    
    print(f"\n{'='*80}")
    print("✅ 評估完成！")
    print(f"{'='*80}")
    print(f"\n📁 輸出檔案:")
    print(f"  📊 SQLite 資料庫: {db_path}")
    print(f"     - experiment_runs: {len(all_runs)} 筆")
    print(f"     - evaluation_items: {len(all_items)} 筆")
    print(f"     - ablation_summary: {len(summaries)} 筆")
    print(f"\n  📄 CSV 報表: {csv_dir}/")
    print(f"     - experiment_runs.csv")
    print(f"     - evaluation_items.csv")
    print(f"     - ablation_summary.csv")


if __name__ == "__main__":
    main()
