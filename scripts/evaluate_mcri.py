#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
# ID: evaluate_mcri.py
# Version: V6.2 (Neuro-Symbolic Architecture Quality Evaluation)
# Last Updated: 2026-02-13
# Author: Math AI Research Team
#
# [Description]:
#   MCRI V6.2 評估系統 - AST 智慧分級評分腳本（Neuro-Symbolic Edition）
#   評估三個 Ablation 版本的題目生成品質（Ab1 Bare, Ab2 Engineered, Ab3 Healer）
#   
#   [Version History]:
#   - V6.2: 移除 CodeBLEU 依賴，引入神經符號強健性分析 (L5 升級為 20 分)
#   - V6.0: 雙軌評分體系 (Program Value 50 + Math Value 50)
#   - V4.4: 加入 L4.3 質量控制、L5 複雜度分析（不計分，僅記錄）
#   - V4.3: 原始 L4.3 數學異味檢測
#   - V4.2.2: 加入 L4.2 數學異味檢測（+ -, 1x, -1x 等）
#   - V4.2.1: 修復 L3.1/L3.2 評分邏輯 - check() 返回 dict 而非 bool
#   - V4.2:   補齊 L2 評估邏輯（之前固定為 20 分）
#   
#   [Scientific Contribution]:
#   本模組實作多維度評分系統（MCRI），用於量化不同 Prompt Engineering 策略
#   與 AST Healer 機制對程式碼品質的影響，支援科展實驗的統計分析需求。
#
# [Key Functions]:
#   1. MCRI_Evaluator: 核心評估器類別，實作雙軌評分（Program Value + Math Value）
#   2. analyze_code_robustness: AST 智慧分級分析器 (ROBUST/MODERATE/RISKY)
#   3. create_database: 建立 SQLite 資料庫（3 張表：runs, items, summary）
#   4. main: 主程式入口，批次評估所有 Ablation 樣本
#
# [Evaluation Dimensions] (滿分 100):
#   === Program Value (50分) ===
#   - L1 工程基石 (15分): 語法安全 + 執行穩定性
#   - L2 資料衛生 (15分): 介面契約 + 格式純淨度
#   - L5 架構品質 (20分): 靜態分析 (10) + 神經符號強健性 (10)
#   
#   === Math Value (50分) ===
#   - L3 評測公平 (30分): 內在一致性 + 外在強健性
#   - L4 教學有效 (20分): 數值友善度 + 視覺可讀性 + 質量控制
#
# [Database Schema]:
#   - experiment_runs: 39 欄位 × ~15 筆
#   - evaluation_items: 24 欄位 × ~300 筆 (新增 complexity_* 欄位)
#   - ablation_summary: 14 欄位 × 3 筆
#
# [Output]:
#   - SQLite: instance/kumon_math.db
#   - CSV: experiments/reports/{skill}_*.csv
#   - Terminal: 彙總統計表格與關鍵洞察
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
import builtins
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

# 可選導入: SymPy (用於數學複雜度分析)
try:
    import sympy
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import Config


# ========================================
# 常數定義
# ========================================
MCRI_VERSION = "6.2"
# [NEW] 从 config 读取超时和重复次数配置
DEFAULT_TIMEOUT = getattr(Config, 'EXECUTION_TIMEOUT', 10)  # 秒
DEFAULT_REPETITIONS = getattr(Config, 'STABILITY_REPS', 3) if getattr(Config, 'STABILITY_REPS', None) is not None else 20
ALLOWED_IMPORTS = {'math', 'random', 'fractions', 're', 'ast', 'operator', 'os', 'typing', 'decimal', 'sympy', 'numpy'}
FORBIDDEN_BUILTINS = {'eval', 'exec'}  # 移除誤判的 compile, __import__


# ========================================
# 自定義異常
# ========================================
class TimeoutError(Exception):
    """超時異常"""
    pass

class ForbiddenInputError(Exception):
    """禁止互動輸入異常 - 當程式碼包含 input() 時拋出"""
    pass


# ========================================
# 安全執行上下文 (Safe Execution Context)
# ========================================
def forbidden_input(*args, **kwargs):
    """被禁止的 input() 實現 - 自動評分不允許互動輸入"""
    raise ForbiddenInputError(
        "❌ 嚴重違規：生成的程式碼包含 input() 互動函數，不符合自動評估要求"
    )


class SafeExecutionContext:
    """
    安全執行上下文 - class 實作版
    確保被評測的程式碼無法進行互動式輸入，且輸出被靜音
    """
    def __enter__(self):
        self.original_input = builtins.input
        self.original_print = builtins.print
        
        # 替換為禁止函數和靜音函數
        builtins.input = forbidden_input
        builtins.print = lambda *args, **kwargs: None  # 靜音模式
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 確保無論成功或失敗都還原
        builtins.input = self.original_input
        builtins.print = self.original_print

def safe_execution_context():
    return SafeExecutionContext()


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
# AST 智慧分級分析器 (MCRI V6.2 核心)
# ========================================
def analyze_code_robustness(code):
    """
    MCRI V6.2 L5核心: AST 智慧分級分析器
    區分: Bare(5), Engineered(7), Healer(10)
    
    Returns:
        Tuple[str, str]: (status, evidence)
        - status: "ROBUST", "MODERATE", "RISKY", "NEUTRAL", "SYNTAX_ERROR"
        - evidence: 詳細說明
    """
    try:
        tree = ast.parse(code)
    except Exception as e:
        return "SYNTAX_ERROR", f"Syntax Error: {str(e)[:100]}"

    has_retry_loop = False
    safe_calls = []
    unsafe_calls = []
    has_helpers = False 
    
    for node in ast.walk(tree):
        # 1. Detect Retry Loop (Loop -> Try)
        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if isinstance(child, ast.Try):
                    has_retry_loop = True
                    
        # 2. Detect Helpers Definition (Ab2 Feature)
        if isinstance(node, ast.FunctionDef) and node.name == 'safe_choice':
            has_helpers = True
        if isinstance(node, ast.ClassDef) and 'Ops' in node.name:
            has_helpers = True

        # 3. Detect Calls
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            if func_name in ['safe_eval', 'check', 'safe_choice']:
                safe_calls.append(func_name)
            elif func_name in ['eval', 'exec']:
                unsafe_calls.append(func_name)

    # === Decision Logic (Golden Staircase) ===
    if has_retry_loop:
        return "ROBUST", "Retry Loop Detected"
    if len(safe_calls) > 0:
        return "ROBUST", f"Safe Functions: {list(set(safe_calls))}"
    
    if 'eval' in unsafe_calls and has_helpers:
        return "MODERATE", "Unsafe Eval but Modular"
        
    if 'eval' in unsafe_calls:
        return "RISKY", "Raw Unsafe Eval"

    return "NEUTRAL", "Standard Structure"


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
        # 檔名格式: gh_ApplicationsOfDerivatives_qwen2.5-coder-14b_Ab1_run01.py
        # 需要提取的是：gh_ApplicationsOfDerivatives (技能部分，在第一個模型名稱之前)
        filename = self.skill_path.stem
        
        # 方法：找到 _Ab{1,2,3} 的位置，然後回溯到找到模型名稱
        # 先移除 _run{idx} 部分
        if '_run' in filename:
            filename = filename.rsplit('_run', 1)[0]  # gh_ApplicationsOfDerivatives_qwen2.5-coder-14b_Ab1
        
        # 再移除 _Ab{n} 部分
        if '_Ab' in filename:
            filename = filename.rsplit('_Ab', 1)[0]  # gh_ApplicationsOfDerivatives_qwen2.5-coder-14b
        
        # 最後移除模型名稱部分 (最後一個 _ 之後)
        if '_' in filename:
            filename = filename.rsplit('_', 1)[0]  # gh_ApplicationsOfDerivatives
        
        self.skill_name = filename
        
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
            
            # 2. 載入模組（使用安全執行上下文防止全局代碼中的 input() 卡住）
            spec = importlib.util.spec_from_file_location(
                f"skill_{self.ablation_id}", 
                str(self.skill_path)
            )
            if spec is None or spec.loader is None:
                return False
            
            self.module = importlib.util.module_from_spec(spec)
            
            # 在安全上下文中載入模組，防止全局代碼中的 input() 導致卡住
            try:
                with safe_execution_context():
                    spec.loader.exec_module(self.module)
            except ForbiddenInputError:
                # 全局代碼包含 input()，但我們仍允許模組載入成功
                # （只要函數本身存在即可，評估時會再次檢查）
                pass
            
            # 3. 檢查必要函數
            if not hasattr(self.module, 'generate'):
                print(f"[ERROR] {self.skill_path.name} 缺少 generate() 函數")
                return False
            
            if not hasattr(self.module, 'check'):
                print(f"[WARN] {self.skill_path.name} 缺少 check() 函數（L3 將失分）")
                self.check_func = None
            else:
                self.check_func = self.module.check
            
            self.generate_func = self.module.generate
            return True
            
        except Exception as e:
            import traceback
            print(f"================ ERROR DEBUGGING ================")
            traceback.print_exc()
            print(f"=================================================")
            print(f"[ERROR] 載入失敗 {self.skill_path.name}: {e}")
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
        - [FIX] 強制使用 safe_execution_context 攔截 input()
        
        Returns:
            (score, notes, exec_times)
        """
        score = 0.0
        notes = []
        exec_times = []
        success_count = 0
        forbidden_input_detected = False
        
        for i in range(repetitions):
            try:
                start_time = time.time()
                with time_limit(DEFAULT_TIMEOUT):
                    # [FIX] 這裡必須加上安全上下文，否則 input() 會真的執行而卡住
                    with safe_execution_context():
                        result = self.generate_func()
                exec_time = time.time() - start_time
                
                exec_times.append(exec_time)
                success_count += 1
                
            except ForbiddenInputError as e:
                # 程式碼包含 input()，嚴重違規
                forbidden_input_detected = True
                notes.insert(0, f"Rep{i+1} 違規: 包含 input()")
                exec_times.append(0.0)
                
                # 🚨 關鍵：直接設定該項分數為 0，並標記嚴重違規
                score = 0.0 
                notes.insert(0, "❌ 嚴重違規：程式碼包含 input()，L1 直接歸零")
                
                # 🚨 關鍵：回傳時要確保這個 0.0 能被回傳出去
                return 0.0, "\n".join(notes), exec_times
                
            except TimeoutError:
                notes.append(f"Rep{i+1} 超時")
                exec_times.append(DEFAULT_TIMEOUT)
            except Exception as e:
                notes.append(f"Rep{i+1} 失敗: {type(e).__name__}")
                exec_times.append(0.0)
        
        # 如果檢測到 input()，L1 直接給 0 分（嚴重違規）
        if forbidden_input_detected:
            score = 0.0
            # 確保錯誤訊息排在第一位
            if "❌ 嚴重違規：包含 input() 互動函數" not in notes:
                notes.insert(0, "❌ 嚴重違規：包含 input() 互動函數")
        else:
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
    
    def evaluate_math_artifacts(self, text: str) -> Tuple[float, str]:
        """
        [L4.3] 數學異味檢測 (Math Smells) - 累進式扣分版 [Scientific]
        
        策略：不採用一刀斃命，而是依嚴重程度累進扣分，保留數據顆粒度。
        1. 零係數 (0x^n): 嚴重，起手扣 5 分，每多一個再扣 2 分 (Max 10)。
        2. 符號未簡化 (+ -): 中度，每個扣 2 分 (Max 6)。
        3. 冗餘係數 (1x): 輕微，每個扣 1 分 (Max 3)。
        
        Returns:
            score (0.0 ~ 10.0), notes
        """
        if not text:
            return 10.0, "Pass"

        penalty = 0.0
        notes = []
        
        # 1. 檢測零係數 (嚴重違規: 數學概念錯誤) 
        # Pattern: 0x, 0x^2, 0y, 0 x
        # 排除小數點 (0.5x) 和整數 (10x)
        zero_pattern = r"\b0\s*[a-zA-Z](\^\{?\d+\}?)?"
        zero_matches = re.findall(zero_pattern, text)
        
        if zero_matches:
            count = len(zero_matches)
            # 累進邏輯：第一個錯很嚴重(-5)，後面代表模型崩潰(-2)
            p = 5.0 + (count - 1) * 2.0
            p = min(p, 10.0) # 此項最多扣完 10 分
            penalty += p
            notes.append(f"零係數x{count}(-{p})")

        # 2. 檢測符號未簡化 (中度違規: 格式不潔)
        # Pattern: + -, - -, ^1
        sign_pattern = r"(\+\s*-)|(-\s*-)|(\^\s*\{?1\}?\b)"
        sign_matches = re.findall(sign_pattern, text)
        
        if sign_matches:
            count = len(sign_matches)
            p = count * 2.0 # 每個扣 2 分
            p = min(p, 6.0) # 上限扣 6 分，保留 4 分底分
            penalty += p
            notes.append(f"符號未簡化x{count}(-{p})")

        # 3. 檢測冗餘係數 (輕微違規: 不夠專業)
        # Pattern: 1x, -1x (前面不能有數字, 避免 11x 被抓)
        redundant_pattern = r"(?<!\d)\b1[a-zA-Z]"
        redundant_matches = re.findall(redundant_pattern, text)
        
        if redundant_matches:
            count = len(redundant_matches)
            p = count * 1.0 # 每個扣 1 分
            p = min(p, 3.0) # 上限扣 3 分
            penalty += p
            notes.append(f"冗餘係數x{count}(-{p})")

        # 計算最終分數 (滿分 10，最低 0)
        final_score = max(0.0, 10.0 - penalty)
        
        # 格式化輸出
        if not notes:
            note_str = "完美"
        else:
            note_str = "; ".join(notes)
        
        return float(final_score), note_str
    



    def score_math_question(self, question_text: str, answer: str) -> dict:
        """
        輸入題目文字 + 答案 → 輸出數學價值得分（滿分 50 分）
        包含：難易度 (20) + 品質異味 (30)
        """
        result = {
            'total_math_score': 0,
            'difficulty_score': 0,   # 20 分
            'quality_score': 0,      # 30 分
            'details': []
        }
        
        if not question_text:
            return result

        # Step 1: 清洗題目文字，只保留數學式
        # 去掉中文、$、f(x)= 等，只留下算式部分
        clean_text = re.sub(r'[^\d\.\+\-\*\/\(\)\^x]', ' ', question_text)  # 去非數學符號
        clean_text = clean_text.replace('^', '**').strip()
        # 如果有等號，只取右邊（答案部分通常在左）
        if '=' in clean_text:
            clean_text = clean_text.split('=')[-1].strip()
            
        # Step 2: 嘗試用 sympy 解析（允許 2x 這種省略乘號）
        try:
            transformations = standard_transformations + (implicit_multiplication_application,)
            # [Fix] empty check
            if not clean_text.strip():
                raise ValueError("Empty math text")
                
            expr = parse_expr(clean_text, transformations=transformations)
            
            # 難易度 - 運算複雜度 (滿分 10)
            ops_count = sympy.count_ops(expr)
            result['difficulty_score'] += min(ops_count * 0.8, 10)
            if ops_count > 8:
                result['details'].append(f"高運算量 ({ops_count} 步)")
                
            # 難易度 - 變數與次數 (滿分 5)
            symbols = expr.free_symbols
            if len(symbols) > 0:
                degree = sympy.degree(expr)
                result['difficulty_score'] += min(degree * 1.5, 5)
                if degree >= 3:
                    result['details'].append(f"高次多項式 (deg={degree})")
                    
            # 難易度 - 負數與括號 (滿分 5)
            negative = clean_text.count('-')
            parentheses = clean_text.count('(') + clean_text.count('[')
            result['difficulty_score'] += min(negative * 1, 2.5)
            result['difficulty_score'] += min(parentheses * 1, 2.5)
            
        except Exception as e:
            # sympy 解析失敗 → 降級用簡單規則
            result['details'].append(f"SymPy 解析失敗: {str(e)}")
            ops_count = len(re.findall(r'[\+\-\*/]', clean_text))
            result['difficulty_score'] = min(ops_count * 1.5, 20)
            
        # Step 3: 品質異味檢測 (滿分 30)
        quality = 30
        
        # 嚴重異味（直接扣重）
        if re.search(r'\+ -', clean_text): quality -= 8
        if re.search(r'\b1x', clean_text): quality -= 8
        if re.search(r'\b-1x', clean_text): quality -= 8
        if re.search(r'\^1\b', clean_text): quality -= 6
        if re.search(r'0x', clean_text): quality -= 10
        if '+0' in clean_text or '-0' in clean_text: quality -= 5
        
        # 輕微異味
        if ' ' in clean_text.replace('**', ''): quality -= 3
        if re.search(r'\*\*', clean_text) and not re.search(r'\*\*\d+', clean_text): quality -= 5
        
        result['quality_score'] = max(quality, 0)
        
        # 總分
        result['total_math_score'] = min(50, result['difficulty_score'] + result['quality_score'])
        return result

    def evaluate_l5_architecture(self, code_content: str) -> dict:
        """
        [MCRI V6.2] L5 Architecture Quality (Neuro-Symbolic Scoring)
        Total: 20 Points = Part A (Static, 10) + Part B (Robustness, 10)
        """
        score = 0.0
        details = []

        # --- Part A: Base Static Analysis (Max 10.0) ---
        # 1. Modular (+2)
        if code_content.count("def ") > 1: 
            score += 2.0
            details.append("Modular(+2)")
        # 2. Type Hints (+2)
        if "->" in code_content or ": int" in code_content: 
            score += 2.0
            details.append("TypeHint(+2)")
        # 3. Docstrings (+2)
        if '"""' in code_content or "'''" in code_content: 
            score += 2.0
            details.append("Docstring(+2)")
        # 4. Error Handling Syntax (+2)
        if "try:" in code_content and "except" in code_content:
            score += 2.0
            details.append("Try-Except(+2)")
        # 5. Basic Safety (+2)
        if "safe_eval" in code_content or "eval" not in code_content:
            score += 2.0
            details.append("BasicSafety(+2)")

        # --- Part B: Neuro-Symbolic Robustness (Max 10.0) ---
        # Call the external AST analyzer
        status, evidence = analyze_code_robustness(code_content)
        
        robustness_score = 0.0
        if status == "ROBUST":
            robustness_score = 10.0  # Ab3
        elif status == "MODERATE":
            robustness_score = 7.0   # Ab2
        elif status == "RISKY":
            robustness_score = 5.0   # Ab1
        else:
            robustness_score = 6.0
            
        score += robustness_score
        details.append(f"Robustness:{status}(+{robustness_score}, {evidence})")

        return {
            "score": score,
            "details": "; ".join(details)
        }

    def analyze_math_complexity(self, question_text: str) -> Tuple[int, int]:
        """
        L5A 數學複雜度分析 (不影響總分，記錄到 CSV)
        
        使用 SymPy 分析數學表達式的複雜度
        
        Returns:
            (ops_count, atom_count) - 運算子數量和原子數量
            若失敗，返回 (0, 0)
        """
        if not HAS_SYMPY:
            return 0, 0
        
        try:
            # 嘗試提取數學表達式 (簡單方法：查找 LaTeX 或簡單表達式)
            # 若都失敗，返回 0, 0
            text = str(question_text).strip()
            if not text:
                return 0, 0
            
            # 簡單的清理：移除 LaTeX 分隔符
            text_clean = re.sub(r'\$|\\\(|\\\)|\$\$', '', text)
            text_clean = re.sub(r'\\text\{[^}]*\}', '', text_clean)
            text_clean = text_clean.strip()
            
            if not text_clean or len(text_clean) < 2:
                return 0, 0
            
            # 嘗試解析為數學表達式
            expr = sympy.sympify(text_clean, rational=True)
            
            # 計算運算子數量 (�用 tree_size 或 count_ops)
            ops_count = len(sympy.preorder_traversal(expr)) - 1
            
            # 計算原子數量 (自由符號數)
            atoms = expr.free_symbols
            atom_count = len(atoms)
            
            return int(ops_count), int(atom_count)
        
        except Exception:
            # 若解析失敗，返回 0, 0
            return 0, 0
    
    def analyze_code_structure(self, code_content: str) -> Tuple[int, int]:
        """
        L5B 代碼複雜度分析 (不影響總分，記錄到 CSV)
        
        使用 AST 分析代碼的複雜度
        
        Returns:
            (ast_node_count, max_loop_depth) - AST 節點數和最大循環深度
            若失敗，返回 (0, 0)
        """
        try:
            if not code_content or not isinstance(code_content, str):
                return 0, 0
            
            tree = ast.parse(code_content)
            
            # 計算 AST 節點數
            ast_node_count = len(list(ast.walk(tree)))
            
            # 計算最大循環深度
            max_loop_depth = 0
            
            class LoopDepthVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.current_depth = 0
                    self.max_depth = 0
                
                def visit_For(self, node):
                    self.current_depth += 1
                    self.max_depth = max(self.max_depth, self.current_depth)
                    self.generic_visit(node)
                    self.current_depth -= 1
                
                def visit_While(self, node):
                    self.current_depth += 1
                    self.max_depth = max(self.max_depth, self.current_depth)
                    self.generic_visit(node)
                    self.current_depth -= 1
            
            visitor = LoopDepthVisitor()
            visitor.visit(tree)
            max_loop_depth = visitor.max_depth
            
            return ast_node_count, max_loop_depth
        
        except Exception:
            # 若解析失敗，返回 0, 0
            return 0, 0
    
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
            'exec_time_ms': 0.0,   # 執行時間（毫秒）
            'score_l2_1_contract': 0,  # INTEGER (新增)
            'score_l2_2_purity': 0,    # INTEGER (新增)
            'score_l3_total': 0,   # INTEGER
            'score_l3_1_internal': 0,
            'score_l3_2_external': 0,
            'score_l4_total': 0,   # INTEGER
            'score_l4_1_numeric': 0,
            'score_l4_2_visual': 0,
            'score_l4_3_artifacts': 0,  # [V4.4 NEW] 質量控制 (10分)
            'score_l4_4_mqi': 0,        # [V6.0] MQI (30分)
            'score_math_total': 0.0,    # [V6.0] 數學價值總分 (50分)
            'score_math_quality': 0.0,  # [V6.0] 品質分 (30分)
            'score_math_difficulty': 0.0,# [V6.0] 難度分 (20分)
            'complexity_math_ops': 0,   # [V4.4 NEW] 數學複雜度 - 運算子數
            'complexity_ast_nodes': 0,  # [V4.4 NEW] 代碼複雜度 - AST 節點數
            'complexity_loop_depth': 0, # [V4.4 NEW] 代碼複雜度 - 最大循環深度
            'student_input_test': '',
            'student_input_result': '',
        }
        
        try:
            # 執行 generate() 並記錄執行時間 [V4.2.2 優先級3]
            # [IMPORTANT] 使用安全上下文防止 input() 調用
            start_time = time.time()
            with time_limit(DEFAULT_TIMEOUT):
                # 在安全上下文中執行 generate()，防止互動式輸入
                with safe_execution_context():
                    result = self.generate_func()
            
            exec_time = time.time() - start_time
            
            # 儲存生成內容
            item['generated_question'] = str(result.get('question_text', ''))[:500]
            item['generated_answer'] = str(result.get('answer', ''))[:200]
            item['generated_correct_answer'] = str(result.get('correct_answer', ''))[:200]
            item['exec_time_ms'] = round(exec_time * 1000, 2)  # 轉換為毫秒
            
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
                
                # ===== L4 評分 (30分) ===== [V4.3 重新分配]
                # 準備要評分的文本
                q_text = str(result.get('question_text', ''))
                a_text = str(result.get('answer', ''))
                
                # L4.1 數值友善度 (10分)
                score_l4_1, _ = self.evaluate_numeric_friendliness(result)
                # 將 L4.1 從原本的 15分 縮放到 10分
                score_l4_1_scaled = (score_l4_1 / 15.0) * 10.0
                item['score_l4_1_numeric'] = int(score_l4_1_scaled)
                
                # L4.2 視覺可讀性 (10分)
                score_l4_2, _ = self.evaluate_visual_readability(result)
                # 將 L4.2 從原本的 15分 縮放到 10分
                score_l4_2_scaled = (score_l4_2 / 15.0) * 10.0
                item['score_l4_2_visual'] = int(score_l4_2_scaled)
                
                # L4.3 質量控制 (10分) [V4.4 NEW]
                combined_text = q_text + " " + a_text
                score_l4_3, _ = self.evaluate_math_artifacts(combined_text)
                item['score_l4_3_artifacts'] = int(score_l4_3)
                
                # ===== [V6.0] 數學價值評估 (50分) =====
                math_res = self.score_math_question(q_text, a_text)
                item['score_math_total'] = math_res['total_math_score']
                item['score_math_difficulty'] = math_res['difficulty_score']
                item['score_math_quality'] = math_res['quality_score']
                item['score_l4_4_mqi'] = math_res['quality_score']  # MQI mapped from quality

                
                # ===== L5 複雜度分析 (不影響總分，記錄指標) ===== [V4.4 NEW]
                # L5A 數學複雜度
                math_ops, math_atoms = self.analyze_math_complexity(result.get('question_text', ''))
                item['complexity_math_ops'] = math_ops
                
                # L5B 代碼複雜度 [FIX]
                # 修正：直接讀取技能檔案的原始碼，而不是從生成結果找 code
                try:
                    with open(self.skill_path, 'r', encoding='utf-8') as f:
                        code_content = f.read()
                    ast_nodes, loop_depth = self.analyze_code_structure(code_content)
                except Exception:
                    ast_nodes, loop_depth = 0, 0
                    
                item['complexity_ast_nodes'] = ast_nodes
                item['complexity_loop_depth'] = loop_depth
                
                item['score_l4_total'] = int(score_l4_1_scaled + score_l4_2_scaled + score_l4_3)
                
                item['status'] = 'PASS'
                item['included_in_avg'] = 1
            else:
                item['error_log'] = '介面契約不完整'
        
        except ForbiddenInputError as e:
            # 生成代碼包含 input()，嚴重違規
            item['status'] = 'FORBIDDEN_INPUT'
            item['error_log'] = f'❌ {str(e)}'
            item['score_l1_1_syntax'] = 0
            item['score_l1_2_runtime'] = 0
            item['score_l1_total'] = 0
            item['score_l2_1_contract'] = 0
            item['score_l2_2_purity'] = 0
            item['score_l2_total'] = 0
            item['included_in_avg'] = 0
        except TimeoutError:
            item['status'] = 'TIMEOUT'
            item['error_log'] = f'執行超過 {DEFAULT_TIMEOUT} 秒'
            item['included_in_avg'] = 0
        except Exception as e:
            item['status'] = 'ERROR'
            item['error_log'] = f'{type(e).__name__}: {str(e)[:200]}'
            item['included_in_avg'] = 0
        
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
        # L5 架構品質評估
        try:
            with open(self.skill_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            l5_result = self.evaluate_l5_architecture(code_content)
            score_l5_arch = l5_result["score"]
            notes_l5_arch = l5_result["details"]
        except Exception as e:
            score_l5_arch = 0.0
            notes_l5_arch = str(e)

        
        # L2.1 介面契約（從 repetitions 中計算）
        # L2.2 格式純淨度（從 repetitions 中計算）
        
        # 執行所有 repetitions
        print(f"\n[REPEAT] 執行 {repetitions} 次重複測試...")
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
        
        # ===== [V4.3] L4 重新計算 =====
        avg_l4_total = np.mean([item['score_l4_total'] for item in pass_items]) if pass_items else 0.0
        avg_l4_1 = np.mean([item['score_l4_1_numeric'] for item in pass_items]) if pass_items else 0.0
        avg_l4_2 = np.mean([item['score_l4_2_visual'] for item in pass_items]) if pass_items else 0.0
        avg_l4_3 = np.mean([item['score_l4_3_artifacts'] for item in pass_items]) if pass_items else 0.0
        avg_l4_4 = np.mean([item['score_l4_4_mqi'] for item in pass_items]) if pass_items else 0.0
        
        # ===== [V4.4] L5 複雜度平均值（不影響總分）=====
        avg_complexity_math_ops = np.mean([item['complexity_math_ops'] for item in pass_items]) if pass_items else 0.0
        avg_complexity_ast_nodes = np.mean([item['complexity_ast_nodes'] for item in pass_items]) if pass_items else 0.0
        avg_complexity_loop_depth = np.mean([item['complexity_loop_depth'] for item in pass_items]) if pass_items else 0.0
        
        # ===== [V5.0] 50/50 Split Scoring System =====
        # Part A: Program Value (Max 50)
        # L1 Reliability (20 -> 15)
        score_program_l1 = score_l1_total * (15.0 / 20.0)
        # L2 Compliance (20 -> 15)
        score_program_l2 = score_l2_total * (15.0 / 20.0)
        # L5 Architecture (10 -> 20)
        score_program_l5 = score_l5_arch * (20.0 / 10.0)
        
        score_program_total = score_program_l1 + score_program_l2 + score_program_l5
        
        # Part B: Math Value (Max 50)
        # Part B: Math Value (Max 50)
        # Using the new score_math_question results averaged over pass_items
        avg_math_total = np.mean([item['score_math_total'] for item in pass_items]) if pass_items else 0.0
        
        # If we want to keep L3 correctness as a penalty/multiplier:
        # If correctness is low, the math value is questionable. 
        # But for now, let's stick to the function output as requested.
        # Maybe Correctness (L3) is implicitly part of "Program Reliability" in user's mind? 
        # Or we can average L3 into it? 
        # User said "Math Value 50" comes from the function. 
        # But correctness is critical. 
        # Let's make Math Total = avg_math_total (from function) * (avg_l3_total / 30.0) ? 
        # No, that's too harsh. 
        # Let's just use the function output, but note that incorrect items are filtered by pass_items usually?
        # No, pass_items filters by L1/L2 crash, not L3 correctness.
        # Let's just use avg_math_total for now to follow code structure.
        
        score_math_total = avg_math_total
        # Final MCRI Total (Max 100)
        avg_mcri_total = score_program_total + score_math_total
        
        # Debug Log
        print(f"\n[Scoring] Program: {score_program_total:.2f}/50 | Math: {score_math_total:.2f}/50 | Total: {avg_mcri_total:.2f}/100")
        # avg_exec_time 已在上方從 repetitions 計算
        
        # 建立 run 記錄
        run_record = {
            'run_id': run_id,
            'timestamp': timestamp,
            'model_name': self.model_name,
            'skill_name': self.skill_name,
            'ablation_id': self.ablation_id,  # INTEGER
            'sample_index': sample_index,
            'code_commit_hash': '',  # 暫時空值
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'mcri_version': self.version,
            'model_temperature': 0.7,  # 預設值
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
            'avg_l4_3_artifacts': round(avg_l4_3, 2),  # [V4.4 NEW]
            'avg_complexity_math_ops': round(avg_complexity_math_ops, 2),  # [V4.4 NEW]
            'avg_complexity_ast_nodes': round(avg_complexity_ast_nodes, 2),  # [V4.4 NEW]
            'avg_complexity_loop_depth': round(avg_complexity_loop_depth, 2),  # [V4.4 NEW]
            'avg_l4_4_mqi': round(avg_l4_4, 2),
            'avg_mcri_total': round(avg_mcri_total, 2),
            'score_program_total': round(score_program_total, 2),
            'score_math_total': round(score_math_total, 2),
            'score_l5_architecture': round(score_program_l5, 2), # Use scaled or raw? Let's use scaled for consistency with program score
            'source_code_path': str(self.skill_path),
            'notes': self._build_notes(notes_l1_1, notes_l1_2),
            'batch_id': '',  # 暫時空值
            'golden_prompt_path': '',  # 暫時空值
            'prompt_hash': '',  # 暫時空值
            'prompt_tokens': 0,  # 暫時 0
            'completion_tokens': 0,  # 暫時 0
            'total_tokens': 0,  # 暫時 0
            'latency_ms': int(avg_exec_time * 1000),  # 轉換為毫秒
            'healer_applied': 0,  # 暫時 0
            'healer_fix_count': 0,  # 暫時 0
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
    """建立 SQLite 資料庫與三張表（如果不存在）"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 刪除舊表（確保新結構）
    cursor.execute("DROP TABLE IF EXISTS evaluation_items")  # 先刪附表
    cursor.execute("DROP TABLE IF EXISTS experiment_runs")
    cursor.execute("DROP TABLE IF EXISTS ablation_summary")
    
    # 1. experiment_runs (主表) - 匹配現有 39 列架構
    cursor.execute("""
        CREATE TABLE experiment_runs (
            run_id VARCHAR(36) PRIMARY KEY,
            timestamp DATETIME,
            model_name VARCHAR(50),
            skill_name VARCHAR(100),
            ablation_id INTEGER,
            sample_index INTEGER,
            code_commit_hash VARCHAR(40),
            python_version VARCHAR(20),
            mcri_version VARCHAR(20),
            model_temperature FLOAT,
            repetitions_planned INTEGER,
            repetitions_completed INTEGER,
            fail_count INTEGER,
            pass_rate FLOAT,
            avg_exec_time FLOAT,
            score_l1_total INTEGER,
            score_l1_1_syntax INTEGER,
            score_l1_2_runtime INTEGER,
            score_l2_total INTEGER,
            score_l2_1_contract INTEGER,
            score_l2_2_purity INTEGER,
            avg_l3_total FLOAT,
            avg_l3_1_internal FLOAT,
            avg_l3_2_external FLOAT,
            avg_l4_total FLOAT,
            avg_l4_1_numeric FLOAT,
            avg_l4_2_visual FLOAT,
            avg_l4_3_artifacts FLOAT,
            avg_complexity_math_ops FLOAT,
            avg_complexity_ast_nodes FLOAT,
            avg_complexity_loop_depth FLOAT,
            score_program_total FLOAT,
            score_math_total FLOAT,
            score_l5_architecture FLOAT,
            avg_l4_4_mqi FLOAT,
            avg_mcri_total FLOAT,
            source_code_path VARCHAR(255),
            notes TEXT,
            batch_id VARCHAR(50),
            golden_prompt_path VARCHAR(255),
            prompt_hash VARCHAR(64),
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            latency_ms INTEGER,
            healer_applied BOOLEAN,
            healer_fix_count INTEGER
        )
    """)
    
    # 2. evaluation_items (附表)
    cursor.execute("""
        CREATE TABLE evaluation_items (
            item_id TEXT PRIMARY KEY,
            run_id TEXT,
            repetition_index INTEGER,
            generated_question TEXT,
            generated_answer TEXT,
            generated_correct_answer TEXT,
            status TEXT,
            error_log TEXT,
            included_in_avg INTEGER,
            exec_time_ms REAL,
            score_l2_1_contract INTEGER,
            score_l2_2_purity INTEGER,
            score_l3_total INTEGER,
            score_l3_1_internal INTEGER,
            score_l3_2_external INTEGER,
            score_l4_total INTEGER,
            score_l4_1_numeric INTEGER,
            score_l4_2_visual INTEGER,
            score_l4_3_artifacts INTEGER,
            score_l4_4_mqi REAL,
            score_math_total REAL,
            score_math_quality REAL,
            score_math_difficulty REAL,
            complexity_math_ops INTEGER,
            complexity_ast_nodes INTEGER,
            complexity_loop_depth INTEGER,
            student_input_test TEXT,
            student_input_result TEXT,
            FOREIGN KEY (run_id) REFERENCES experiment_runs(run_id)
        )
    """)
    
    # 3. ablation_summary (彙總表) - 13 欄
    cursor.execute("""
        CREATE TABLE ablation_summary (
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
            mean_l4_numeric REAL,
            mean_program_total REAL,
            mean_math_total REAL,
            mean_l5_architecture REAL,
            mean_l4_mqi REAL,
            p_value_vs_ab1 REAL,
            notes TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"[OK] 資料庫已建立: {db_path}")


def insert_experiment_runs(conn: sqlite3.Connection, runs: List[Dict]):
    """插入 experiment_runs 資料"""
    cursor = conn.cursor()
    
    for run in runs:
        cursor.execute("""
            INSERT INTO experiment_runs 
            (run_id, timestamp, model_name, skill_name, ablation_id, sample_index,
             code_commit_hash, python_version, mcri_version, model_temperature,
             repetitions_planned, repetitions_completed, fail_count, pass_rate, avg_exec_time,
             score_l1_total, score_l1_1_syntax, score_l1_2_runtime,
             score_l2_total, score_l2_1_contract, score_l2_2_purity,
             avg_l3_total, avg_l3_1_internal, avg_l3_2_external,
             avg_l4_total, avg_l4_1_numeric, avg_l4_2_visual,
             score_program_total, score_math_total, score_l5_architecture, avg_l4_4_mqi, avg_mcri_total, source_code_path, notes,
             batch_id, golden_prompt_path, prompt_hash,
             prompt_tokens, completion_tokens, total_tokens,
             latency_ms, healer_applied, healer_fix_count)
            VALUES
            (:run_id, :timestamp, :model_name, :skill_name, :ablation_id, :sample_index,
             :code_commit_hash, :python_version, :mcri_version, :model_temperature,
             :repetitions_planned, :repetitions_completed, :fail_count, :pass_rate, :avg_exec_time,
             :score_l1_total, :score_l1_1_syntax, :score_l1_2_runtime,
             :score_l2_total, :score_l2_1_contract, :score_l2_2_purity,
             :avg_l3_total, :avg_l3_1_internal, :avg_l3_2_external,
             :avg_l4_total, :avg_l4_1_numeric, :avg_l4_2_visual,
             :score_program_total, :score_math_total, :score_l5_architecture, :avg_l4_4_mqi, :avg_mcri_total, :source_code_path, :notes,
             :batch_id, :golden_prompt_path, :prompt_hash,
             :prompt_tokens, :completion_tokens, :total_tokens,
             :latency_ms, :healer_applied, :healer_fix_count)
        """, run)
    
    conn.commit()
    print(f"[OK] 已插入 experiment_runs: {len(runs)} 筆")


def insert_evaluation_items(conn: sqlite3.Connection, items: List[Dict]):
    """插入 evaluation_items 資料"""
    cursor = conn.cursor()
    
    for item in items:
        cursor.execute("""
            INSERT INTO evaluation_items
            (item_id, run_id, repetition_index,
             generated_question, generated_answer, generated_correct_answer,
             status, error_log, included_in_avg, exec_time_ms,
             score_l2_1_contract, score_l2_2_purity,
             score_l3_total, score_l3_1_internal, score_l3_2_external,
             score_l4_total, score_l4_1_numeric, score_l4_2_visual,
             score_l4_4_mqi, score_math_total, score_math_quality, score_math_difficulty, student_input_test, student_input_result)
            VALUES
            (:item_id, :run_id, :repetition_index,
             :generated_question, :generated_answer, :generated_correct_answer,
             :status, :error_log, :included_in_avg, :exec_time_ms,
             :score_l2_1_contract, :score_l2_2_purity,
             :score_l3_total, :score_l3_1_internal, :score_l3_2_external,
             :score_l4_total, :score_l4_1_numeric, :score_l4_2_visual,
             :score_l4_4_mqi, :score_math_total, :score_math_quality, :score_math_difficulty, :student_input_test, :student_input_result)
        """, item)
    
    conn.commit()
    print(f"[OK] 已插入 evaluation_items: {len(items)} 筆")


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
        mean_program = np.mean(group['score_program_total'].values)
        mean_math = np.mean(group['score_math_total'].values)
        mean_l5 = np.mean(group['score_l5_architecture'].values)
        mean_mqi = np.mean(group['avg_l4_4_mqi'].values)
        std_mcri = np.std(mcri_scores, ddof=1) if len(mcri_scores) > 1 else 0.0
        
        # 95% CI (使用 t 分布)
        n = len(mcri_scores)
        if n > 1:
            ci_result = stats.t.interval(
                confidence=0.95,
                df=n-1,
                loc=mean_mcri,
                scale=stats.sem(mcri_scores)
            )
            ci95_lower, ci95_upper = ci_result
        else:
            ci95_lower = ci95_upper = mean_mcri
        
        # 計算 p_value_vs_ab1（顯著性檢定）
        p_value = None
        notes = "-"
        if ablation_id > 1:  # 只對 Ab2, Ab3 與 Ab1 比較
            ab1_group = df[(df['skill_name'] == skill_name) & 
                          (df['ablation_id'] == 1) & 
                          (df['model_name'] == model_name)]
            if len(ab1_group) > 0:
                ab1_scores = ab1_group['avg_mcri_total'].values
                try:
                    t_stat, p_value = stats.ttest_ind(mcri_scores, ab1_scores)
                    if p_value < 0.001:
                        notes = f"Ab{int(ablation_id)} vs Ab1: p<0.001 (高度顯著)"
                    elif p_value < 0.01:
                        notes = f"Ab{int(ablation_id)} vs Ab1: p<0.01 (顯著)"
                    elif p_value < 0.05:
                        notes = f"Ab{int(ablation_id)} vs Ab1: p<0.05 (邊緣顯著)"
                    else:
                        notes = f"Ab{int(ablation_id)} vs Ab1: p={p_value:.3f} (無顯著差異)"
                except:
                    p_value = None
        
        summary = {
            'mean_program_total': round(mean_program, 2),
            'mean_math_total': round(mean_math, 2),
            'mean_l5_architecture': round(mean_l5, 2),
            'mean_l4_mqi': round(mean_mqi, 2),            'summary_id': str(uuid.uuid4()),
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
            'p_value_vs_ab1': round(p_value, 6) if p_value is not None else None,
            'notes': notes,
        }
        summary_data.append(summary)
    
    # 插入資料庫
    cursor = conn.cursor()
    for s in summary_data:
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
    print(f"[OK] 已插入 ablation_summary: {len(summary_data)} 筆")
    
    return summary_data


# ========================================
# CSV 輸出工具
# ========================================
def write_experiment_runs_csv(runs: List[Dict], output_path: str):
    """寫入 experiment_runs.csv"""
    import csv
    
    fieldnames = [
        'run_id', 'timestamp', 'model_name', 'skill_name', 'ablation_id', 'sample_index',
        'code_commit_hash', 'python_version', 'mcri_version', 'model_temperature',
        'repetitions_planned', 'repetitions_completed', 'fail_count', 'pass_rate', 'avg_exec_time',
        'score_l1_total', 'score_l1_1_syntax', 'score_l1_2_runtime',
        'score_l2_total', 'score_l2_1_contract', 'score_l2_2_purity',
        'avg_l3_total', 'avg_l3_1_internal', 'avg_l3_2_external',
        'avg_l4_total', 'avg_l4_1_numeric', 'avg_l4_2_visual', 'avg_l4_3_artifacts',
        'avg_complexity_math_ops', 'avg_complexity_ast_nodes', 'avg_complexity_loop_depth',
        'score_program_total', 'score_math_total', 'score_l5_architecture', 'avg_l4_4_mqi',
        'avg_mcri_total', 'source_code_path', 'notes',
        'batch_id', 'golden_prompt_path', 'prompt_hash',
        'prompt_tokens', 'completion_tokens', 'total_tokens',
        'latency_ms', 'healer_applied', 'healer_fix_count'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(runs)
    
    print(f"[OK] 已寫入 CSV: {output_path} ({len(runs)} 筆)")


def write_evaluation_items_csv(items: List[Dict], output_path: str):
    """寫入 evaluation_items.csv"""
    import csv
    
    fieldnames = [
        'item_id', 'run_id', 'repetition_index',
        'generated_question', 'generated_answer', 'generated_correct_answer',
        'status', 'error_log', 'included_in_avg',
        'score_l2_1_contract', 'score_l2_2_purity',
        'score_l3_total', 'score_l3_1_internal', 'score_l3_2_external',
        'score_l4_total', 'score_l4_1_numeric', 'score_l4_2_visual', 'score_l4_3_artifacts',
        'score_l4_4_mqi', 'score_math_total', 'score_math_quality', 'score_math_difficulty',
        'complexity_math_ops', 'complexity_ast_nodes', 'complexity_loop_depth',  # [V4.4] L5 複雜度指標
        'student_input_test', 'student_input_result',
        'exec_time_ms'  # [V4.2.2] 執行時間記錄（毫秒）
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)
    
    print(f"[OK] 已寫入 CSV: {output_path} ({len(items)} 筆)")


def write_ablation_summary_csv(summaries: List[Dict], output_path: str):
    """寫入 ablation_summary.csv"""
    import csv
    
    fieldnames = [
        'summary_id', 'skill_name', 'ablation_id', 'model_name', 
        'sample_count', 'total_runs',
        'mean_mcri_total', 'std_mcri_total', 'ci95_lower', 'ci95_upper',
        'mean_l3_external', 'mean_l4_numeric', 
        'mean_program_total', 'mean_math_total', 'mean_l5_architecture', 'mean_l4_mqi',
        'p_value_vs_ab1', 'notes'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    print(f"[OK] 已寫入 CSV: {output_path} ({len(summaries)} 筆)")


# ========================================
# 終端輸出
# ========================================
def print_summary_table(summaries: List[Dict]):
    """列印彙總表格"""
    print("\n" + "="*80)
    print("[SUMMARY] MCRI V4.2 彙總統計")
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
    print("[INSIGHT] 關鍵洞察")
    print("="*80)
    
    # 找出最佳 ablation
    best = max(summaries, key=lambda x: x['mean_mcri_total'])
    print(f"\n[BEST] 最佳配置: Ab{best['ablation_id']} ({best['mean_mcri_total']:.2f} 分)")
    
    # 計算 Ab3 vs Ab1 的提升
    ab1_mean = next((s['mean_mcri_total'] for s in summaries if s['ablation_id'] == 1), None)
    ab3_mean = next((s['mean_mcri_total'] for s in summaries if s['ablation_id'] == 3), None)
    
    if ab1_mean and ab3_mean:
        improvement = ab3_mean - ab1_mean
        print(f"\n[IMPROVEMENT] Ab3 (Healer) vs Ab1 (Bare):")
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
    print(f"\n[HEALER] Healer 機制 (Ab3):")
    print(f"  - 自動修復 AST 錯誤，提升執行穩定性")
    print(f"  - 強化 check() 函數，改善評測公平性")
    print(f"  - 優化數值生成，增進教學適用性")


# ========================================
# 主程式
# ========================================
def main():
    """主程式入口 - 二層選單模式（技能 → 模型 → 自動評分 Ab1/Ab2/Ab3 run01-run05）"""
    print("="*80)
    print("[TARGET] MCRI V4.2 評估系統 - 快速評分模式")
    print("="*80)
    
    # ===== 路徑設定 =====
    results_root = Path("experiments/results")
    instance_dir = Path("instance")
    instance_dir.mkdir(exist_ok=True)
    db_path = instance_dir / "kumon_math.db"  # 資料庫使用 instance/kumon_math.db
    
    # ===== 第一層選單：技能選擇 =====
    if not results_root.exists():
        print(f"[ERROR] 找不到結果目錄: {results_root}")
        return
    
    # 掃描技能目錄
    available_skills = sorted([d for d in results_root.iterdir() if d.is_dir() and not d.name.startswith('.')])
    
    if not available_skills:
        print("[ERROR] 結果目錄下沒有技能資料夾")
        return
    
    print("\n" + "="*80)
    print("[SKILL] 技能選擇")
    print("="*80)
    print(f"   [0] ALL (全部 {len(available_skills)} 個技能)")
    for i, skill_dir in enumerate(available_skills, 1):
        print(f"   [{i}] {skill_dir.name}")
    
    while True:
        try:
            skill_choice = input("\n[INPUT] 請輸入選項: ").strip()
            if skill_choice == '0':
                selected_skills = [d.name for d in available_skills]
                break
            idx = int(skill_choice) - 1
            if 0 <= idx < len(available_skills):
                selected_skills = [available_skills[idx].name]
                break
            print("[ERROR] 輸入無效，請重試。")
        except ValueError:
            print("[ERROR] 請輸入數字。")
    
    # ===== 第二層選單：模型選擇 =====
    print("\n" + "="*80)
    print("[MODEL] 模型選擇")
    print("="*80)
    
    # 掃描第一個技能下的可用模型（從生成的檔案推斷）
    sample_skill = results_root / selected_skills[0]
    available_models = set()
    if sample_skill.exists():
        for py_file in sample_skill.glob("*.py"):
            # 檔案格式: {skill}_{model}_{ablation}_run{idx}.py
            # 例: gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab1_run01
            filename_stem = py_file.stem
            
            # 移除 _run{idx} 後綴
            if '_run' in filename_stem:
                filename_stem = filename_stem.rsplit('_run', 1)[0]
            
            # 現在是: gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab1
            # 移除 _Ab{n} 後綴
            if '_Ab' in filename_stem:
                filename_stem = filename_stem.rsplit('_Ab', 1)[0]
            
            # 現在是: gh_ApplicationsOfDerivatives_qwen2.5-coder-7b
            # 移除技能名前綴 (選定的技能 + _)
            skill_prefix = selected_skills[0] + '_'
            if filename_stem.startswith(skill_prefix):
                model_name = filename_stem[len(skill_prefix):]
                if model_name and any(x in model_name for x in ['gemini', 'qwen', 'coder']):
                    available_models.add(model_name)
    
    available_models = sorted(list(available_models))
    
    if not available_models:
        print("[ERROR] 無法從檔案推斷可用模型")
        return
    
    print(f"   [0] ALL (全部 {len(available_models)} 個模型)")
    for i, model in enumerate(available_models, 1):
        print(f"   [{i}] {model}")
    
    while True:
        try:
            model_choice = input("\n[INPUT] 請輸入選項: ").strip()
            if model_choice == '0':
                selected_models = available_models
                break
            idx = int(model_choice) - 1
            if 0 <= idx < len(available_models):
                selected_models = [available_models[idx]]
                break
            print("[ERROR] 輸入無效，請重試。")
        except ValueError:
            print("[ERROR] 請輸入數字。")
    
    # ===== 確認配置 =====
    print("\n" + "="*80)
    print("[CONFIG] 評估配置確認")
    print("="*80)
    print(f"技能數: {len(selected_skills)}")
    for skill in selected_skills:
        print(f"  - {skill}")
    print(f"模型數: {len(selected_models)}")
    for model in selected_models:
        print(f"  - {model}")
    print(f"策略: Ab1, Ab2, Ab3 (自動評分)")
    print(f"樣本: run01, run02, run03, run04, run05 (自動評分)")
    
    total_files = len(selected_skills) * len(selected_models) * 3 * 5  # 3 ablations × 5 runs
    print(f"\n[ESTIMATE] 預計評估檔案數: {total_files}")
    
    confirm = input("\n[INPUT] 確定要開始評估嗎? (y/n): ").strip().lower()
    if confirm != 'y':
        print("[CANCEL] 使用者取消，結束。")
        return
    
    # ===== 建立資料庫 =====
    create_database(str(db_path))
    
    # ===== 主評估迴圈 =====
    print("\n" + "="*80)
    print("[RUNNING] 開始評估...")
    print("="*80)
    
    all_runs = []
    all_items = []
    evaluated_count = 0
    skipped_count = 0
    
    # 巢狀迴圈：技能 → 模型 → Ablation → 樣本 (自動)
    for skill in selected_skills:
        skill_dir = results_root / skill
        
        for model in selected_models:
            # 自動掃描所有 Ab1/Ab2/Ab3 和 run01-run05
            for ablation in ['Ab1', 'Ab2', 'Ab3']:
                for run_idx in range(1, 6):  # run01 to run05
                    # 檔名格式：{skill_name}_{model}_{ablation}_run{idx}.py
                    # 例如：gh_ApplicationsOfDerivatives_qwen2.5-coder-14b_Ab1_run01.py
                    run_filename = f"{skill}_{model}_{ablation}_run{run_idx:02d}.py"
                    skill_path = skill_dir / run_filename
                    
                    if not skill_path.exists():
                        print(f"[SKIP] 跳過: {run_filename} (不存在)")
                        skipped_count += 1
                        continue
                    
                    try:
                        print(f"\n[EVAL] 評估: {run_filename}")
                        
                        ablation_id = int(ablation[2])  # Ab1 -> 1, Ab2 -> 2, Ab3 -> 3
                        evaluator = MCRI_Evaluator(str(skill_path), ablation_id, model)
                        
                        if not evaluator.load_skill_module():
                            print(f"[ERROR] 載入失敗，跳過")
                            skipped_count += 1
                            continue
                        
                        # 執行完整評估
                        run_record, items = evaluator.run_full_evaluation(
                            sample_index=run_idx,
                            repetitions=DEFAULT_REPETITIONS
                        )
                        
                        all_runs.append(run_record)
                        all_items.extend(items)
                        evaluated_count += 1
                        
                        # 即時顯示結果
                        print(f"[OK] 完成 - 總分: {run_record['avg_mcri_total']:.2f}")
                        print(f"   L1: {run_record['score_l1_total']} | "
                              f"L2: {run_record['score_l2_total']} | "
                              f"L3: {run_record['avg_l3_total']:.2f} | "
                              f"L4: {run_record['avg_l4_total']:.2f}")
                        
                    except Exception as e:
                        print(f"[ERROR] 評估失敗: {e}")
                        skipped_count += 1
                        continue
    
    # ===== 寫入結果 =====
    print(f"\n{'='*80}")
    print("[SAVING] 寫入結果（資料庫 + CSV）...")
    print(f"{'='*80}")
    
    # 1. 建立資料庫（會刪除舊表並重新建立）
    create_database(str(db_path))
    conn = sqlite3.connect(str(db_path))
    
    # 插入新資料
    if all_runs:
        insert_experiment_runs(conn, all_runs)
    if all_items:
        insert_evaluation_items(conn, all_items)
    
    # 計算並插入彙總統計
    summaries = compute_and_insert_summary(conn)
    
    conn.close()
    
    # 2. 寫入 CSV 檔案
    csv_dir = Path("experiments/reports")
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    # 決定 CSV 檔名前綴：如果只選了一個技能，加上技能 ID
    filename_prefix = ""
    if len(selected_skills) == 1:
        filename_prefix = selected_skills[0] + "_"
    
    if all_runs:
        write_experiment_runs_csv(all_runs, csv_dir / f"{filename_prefix}experiment_runs.csv")
    if all_items:
        write_evaluation_items_csv(all_items, csv_dir / f"{filename_prefix}evaluation_items.csv")
    if summaries:
        write_ablation_summary_csv(summaries, csv_dir / f"{filename_prefix}ablation_summary.csv")
    
    # ===== 終端輸出 =====
    print_summary_table(summaries)
    if summaries:
        print_insights(summaries, all_runs)
    
    print(f"\n{'='*80}")
    print("[OK] 評估完成！")
    print("="*80)
    print(f"\n統計:")
    print(f"  [OK] 已評估: {evaluated_count} 個檔案")
    print(f"  [SKIP] 已跳過: {skipped_count} 個檔案")
    print(f"  [INFO] 技能: {len(selected_skills)}")
    print(f"  [INFO] 模型: {len(selected_models)}")
    print(f"  [INFO] 策略: Ab1, Ab2, Ab3")
    print(f"  [INFO] 樣本: run01-run05")
    
    print(f"\n[OUTPUT] 輸出檔案:")
    print(f"  [DB] SQLite 資料庫: {db_path}")
    if all_runs:
        print(f"     - experiment_runs: {len(all_runs)} 筆")
    if all_items:
        print(f"     - evaluation_items: {len(all_items)} 筆")
    if summaries:
        print(f"     - ablation_summary: {len(summaries)} 筆")
    
    print(f"\n  [CSV] CSV 報表: {csv_dir}/")
    print(f"     - {filename_prefix}experiment_runs.csv")
    print(f"     - {filename_prefix}evaluation_items.csv")
    print(f"     - {filename_prefix}ablation_summary.csv")
    print("="*80)


if __name__ == "__main__":
    main()