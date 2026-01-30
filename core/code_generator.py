# -*- coding: utf-8 -*-
# ==============================================================================
# ID: core/code_generator.py
# Version: V10.0.0 (Modular Refactored Edition) 🎯
# Last Updated: 2026-01-30
# Author: Math AI Research Team (Advisor & Student)
#
# [Refactoring Status]:
#   ✅ V10.0 重構: 將 3008 行代碼拆分成模組化架構
#   📦 新模組:
#      - core.utils (math_utils, latex_utils, file_utils)
#      - core.healers (regex_healer, ast_healer)
#      - core.validators (syntax_validator, dynamic_sampler)
#      - core.prompts (prompt_builder)
#   🔒 向後相容: auto_generate_skill_code() 簽名保持不變
#
# [Description]:
#   本程式是「自動出題系統」的核心引擎 (Core Engine)，也是本次科展實驗的
#   「手術室 (The Operating Room)」。它負責將 LLM 生成的原始 Python 代碼
#   通過多層次的「自癒流水線 (Self-Healing Pipeline)」進行修復與優化。
#
#   [Core Technology: AST + Regex Healing]:
#   為了驗證小模型 (14B/7B) 在數學邏輯編程上的潛力，本模組實作了兩層修復機制：
#   1. Regex Syntax Healer: 處理 LaTeX 格式錯誤、Markdown 殘留、f-string 語法問題。
#   2. AST Logic Surgeon  : 解析抽象語法樹，修復遞迴死鎖 (Infinite Loop)、
#                           攔截危險函數 (eval -> safe_eval)、注入缺失依賴。
#
# [Database Schema Usage]:
#   1. Read:  SkillGenCodePrompt (讀取標籤為 'standard_14b' 的標準規格書)
#   2. Write: experiment_log (寫入詳細的修復數據：Regex修復數、AST修復數、語法分)
#   3. Write: Local File System (產出最終可執行的技能 .py 檔)
#
# [Logic Flow]:
#   1. Input         -> 接收 Skill ID 與 Coder Model (如 Qwen-14B)。
#   2. Retrieval     -> 從 DB 讀取黃金標準規格 (MASTER_SPEC)。
#   3. Generation    -> 呼叫 Coder 生成原始代碼 (Raw Code)。
#   4. Healing       -> 執行 Regex 清洗 -> AST 深度修復 -> 注入 PERFECT_UTILS。
#   5. Validation    -> 沙盒執行與動態採樣 (Dynamic Sampling) 驗證邏輯正確性。
#   6. Logging       -> 記錄實驗數據 (Ablation Result) 並輸出檔案。
# ==============================================================================

import os
import re
import sys
import io
import time
import ast
import random
import textwrap
import sqlite3
import psutil
import math
import operator
from fractions import Fraction
import datetime as _pydt
from flask import current_app
from pyflakes.api import check as pyflakes_check
from pyflakes.reporter import Reporter

# Local Imports
from core.ai_wrapper import get_ai_client
from models import db, SkillGenCodePrompt
from config import Config

# 🎯 [V10.0 Refactor] 新模組引入（向後相容）
# 注意：舊函數定義仍保留在本檔案中作為臨時實現
# 後續將逐步完全遷移到新模組
try:
    from core.code_utils import (
        safe_choice, to_latex, fmt_num, safe_eval,
        is_prime, gcd, lcm, get_factors,
        clean_latex_output, check,
        clamp_fraction, safe_pow, factorial_bounded, nCr, nPr,
        rational_gauss_solve, normalize_angle,
        fmt_set, fmt_interval, fmt_vec,
        get_base_root, path_in_root, ensure_dir,
        build_polynomial_text  # V10.0 新增：防止幻覺函數
    )
    from core.healers import RegexHealer, ASTHealer
    from core.validators import SyntaxValidator, DynamicSampler
    from core.prompts import PromptBuilder
    
    REFACTOR_MODULES_AVAILABLE = True
except ImportError as e:
    # 降級：如果新模組不可用，使用舊函數
    REFACTOR_MODULES_AVAILABLE = False
    import warnings
    warnings.warn(f"Refactored modules not available: {e}. Using legacy functions.")

# v0.1 Architect Support (optional, try to import)
try:
    from core.architect_v01 import ArchitectV01
except ImportError:
    ArchitectV01 = None

# Optional GPU Monitor
try:
    import GPUtil
except ImportError:
    GPUtil = None

# --- Path helpers (robust base root resolver) ---
def _get_base_root():
    """
    優先用 Flask current_app.root_path；若不可用，回退到 core/ 的上一層（專案根）
    """
    try:
        from flask import has_app_context
        if has_app_context():
            return current_app.root_path
    except Exception:
        pass
    # fallback: project root = parent of core/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def _path_in_root(*parts):
    return os.path.join(_get_base_root(), *parts)

def _ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p

# ==============================================================================
# 1. 基礎建設函式 (Infrastructure)
# ==============================================================================
def get_system_snapshot():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    gpu, gpuram = 0.0, 0.0
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0].load * 100
                gpuram = gpus[0].memoryUtil * 100
        except: pass
    return cpu, ram, gpu, gpuram

def categorize_error(error_msg):
    if not error_msg or error_msg == "None": return None
    err_low = error_msg.lower()
    if "syntax" in err_low: return "SyntaxError"
    if "list" in err_low: return "FormatError"
    return "RuntimeError"

# ==============================================================================
# 2. 預編譯正則表達式（性能優化）
# ==============================================================================
# [Performance Fix V9.2.1] 預編譯所有重複使用的 regex pattern
# 避免在主循環中重複編譯，提升 20-30% 執行速度

COMPILED_PATTERNS = {
    # Markdown 清洗 - 提取代码块内容
    'markdown_blocks': re.compile(r'```(?:python)?\s*\n?(.*?)```', re.DOTALL),
    
    # Import 清洗
    'import_random': re.compile(r'^\s*import\s+random\s*$', re.MULTILINE),
    'import_math': re.compile(r'^\s*import\s+math\s*$', re.MULTILINE),
    'import_re': re.compile(r'^\s*import\s+re\s*$', re.MULTILINE),
    'from_fractions': re.compile(r'^\s*from\s+fractions', re.MULTILINE),
    'import_fractions': re.compile(r'^\s*import\s+fractions', re.MULTILINE),
    'from_math': re.compile(r'^\s*from\s+math', re.MULTILINE),
    
    # 函數名稱修復
    'eval_to_safe': re.compile(r'\beval\s*\('),
    'clean_expression': re.compile(r'\bclean_expression\s*\('),
    'to_latex_call': re.compile(r'\bto_latex\s*\('),
    
    # LaTeX 修復
    'excess_braces': re.compile(r'\{{4,}([^}]+)\}{4,}'),
    'op_latex_double': re.compile(r'\{\{op_latex\[(.+?)\]\}\}'),
    'latex_asterisk': re.compile(r'\\\\\*'),
    'latex_slash': re.compile(r'\\\\/'),
    
    # Return 格式修復
    'question_key': re.compile(r"['\"]question['\"]\s*:"),
    'question_text_dollar': re.compile(r"'question_text':\s*f?['\"]?\$\{q\}\$['\"]?"),
    'fmt_num_double': re.compile(r"f['\"]?\$\{q\}\$['\"]?"),
    
    # 格式化函數修復
    'forbidden_func_format': re.compile(r'\b(format_number_for_latex|format_num_latex|latex_format)\s*\('),
    'fmt_num_type_param': re.compile(r',\s*type\s*=\s*[\'"][^\'"]*[\'"]'),
    'fmt_neg_paren': re.compile(r'\bfmt_neg_paren\s*\('),
    
    # 工具函數定義檢測（動態生成）
    # 'def_<tool_name>': 將在運行時生成
    
    # 混合數字串修復
    'mixed_num_return': re.compile(r'return\s+f"(\{[^}]+\})\{fmt_num\(([^)]+)\)\}"'),
    
    # Python 語法修復
    'range_concat': re.compile(r'range\(([^)]+)\)\s*\+\s*range\(([^)]+)\)'),
    
    # Op_latex 注入檢測
    'op_latex_usage': re.compile(r'\bop_latex\s*\['),
    'local_op_latex': re.compile(r'^([ \t]+)op_latex\s*=\s*\{[^}]+\}\s*\n', re.MULTILINE),
    
    # F-string 修復
    'fstring_var_q': re.compile(r"(q\s*[\+\-]?=\s*)'([^'\n]*?\{[^'\n]*?\}[^'\n]*?)'"),
    'fmt_clean_chain': re.compile(r'fmt_num\s*\(\s*clean_latex_output\s*\)\s*\(\s*([a-zA-Z_]\w*)\s*\)'),
    
    # Fraction 除法
    'fraction_div': re.compile(r'Fraction\s*\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)\s*\)\s*/\s*Fraction\s*\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)\s*\)'),
}

# ==============================================================================
# 3. 完美工具庫 (Perfect Utils - Standard Edition)
# ==============================================================================
PERFECT_UTILS = r'''
import random
from random import randint, choice
import math
from fractions import Fraction
import re
import ast
import operator

# [Research Standard Utils]

def safe_choice(seq):
    """
    [Auto-Injected] 安全的 random.choice，避免空序列崩潰
    """
    if not seq: return 1
    return random.choice(seq)

def to_latex(num):
    """
    將數字轉換為 LaTeX 格式 (支援分數、整數、小數)
    [V46.2 Fix]: 強制限制分數的複雜度 (分母 <= 100)，避免出現百萬級大數。
    """
    if isinstance(num, int): return str(num)
    if isinstance(num, float): num = Fraction(str(num)).limit_denominator(100)
    
    if isinstance(num, Fraction):
        # [Critical Fix] 強制整形：如果分母太大，強制找最接近的簡單分數
        # 這能把 1060591/273522 自動變成合理的 K12 數字 (如 3 7/8)
        if num.denominator > 100:
            num = num.limit_denominator(100)

        if num == 0: return "0"
        if num.denominator == 1: return str(num.numerator)
        
        # 統一處理正負號
        is_neg = num < 0
        sign_str = "-" if is_neg else ""
        abs_num = abs(num)
        
        # 帶分數處理 (Mixed Number)
        if abs_num.numerator > abs_num.denominator:
            whole = abs_num.numerator // abs_num.denominator
            rem_num = abs_num.numerator % abs_num.denominator
            if rem_num == 0: 
                return f"{sign_str}{whole}"
            # ✅ 修正: 整數部分不加大括號 (V46.5)
            return f"{sign_str}{whole}\\frac{{{rem_num}}}{{{abs_num.denominator}}}"
            
        # 真分數處理 (Proper Fraction)
        return f"{sign_str}\\frac{{{abs_num.numerator}}}{{{abs_num.denominator}}}"
        
    return str(num)

def fmt_num(num, signed=False, op=False):
    """
    格式化數字 (標準樣板要求)：
    - 自動括號：負數會自動被包在括號內 (-5) 或 (-\frac{1}{2})
    - signed=True: 強制顯示正負號 (+3, -5)
    """
    # 1. 取得基礎 LaTeX 字串
    latex_val = to_latex(num)
    
    # 2. 判斷是否為 0
    if num == 0 and not signed and not op: return "0"
    
    # 3. 判斷正負 (依賴數值本身)
    is_neg = (num < 0)
    
    # 為了處理 op=True 或 signed=True，我們需要絕對值的字串
    if is_neg:
        # 移除開頭的負號以取得絕對值內容
        # 注意: to_latex 可能回傳 "-{1}\frac..." 或 "-\frac..."
        if latex_val.startswith("-"):
            abs_latex_val = latex_val[1:] 
        else:
            abs_latex_val = latex_val # Should not happen but safe fallback
    else:
        abs_latex_val = latex_val

    # 4. 組裝回傳值
    if op: 
        return f" - {abs_latex_val}" if is_neg else f" + {abs_latex_val}"
    
    if signed: 
        return f"-{abs_latex_val}" if is_neg else f"+{abs_latex_val}"
    
    if is_neg: 
        return f"({latex_val})"
        
    return latex_val

# [AST Healer Inject] 安全運算核心
def safe_eval(expr_str):
    """
    [AST Healer 專用] 安全的數學表達式解析器
    [V46.4 Fix]: Python 3.12+ 兼容性修復，移除 ast.Num 依賴。
    """
    # 允許的運算子白名單
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv, 
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _eval(node):
        # [Python 3.12+ Fix] ast.Num 已被移除，使用 ast.Constant
        if isinstance(node, ast.Constant):
            return node.value
        # [Legacy] 保留 ast.Num 以支持舊版 Python (< 3.8)
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            # 關鍵：遇到除法，自動轉 Fraction
            if isinstance(node.op, ast.Div):
                return Fraction(left, right)
            return ops[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](_eval(node.operand))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'Fraction':
                args = [_eval(a) for a in node.args]
                return Fraction(*args)
        raise TypeError(f"Unsupported type: {node}")

    try:
        # 預處理：將 LaTeX 運算符轉回 Python
        clean_expr = str(expr_str).replace('\\times', '*').replace('\\div', '/')
        # 解析並計算
        result = _eval(ast.parse(clean_expr, mode='eval').body)
        
        # [Clamp] 強制整形：運算結果如果是複雜分數，直接化簡
        if isinstance(result, Fraction):
            if result.denominator > 100 or abs(result.numerator) > 10000:
                result = result.limit_denominator(100)
                
        return result
    except Exception as e:
        return 0

# [數論工具箱]
def is_prime(n):
    if n <= 1: return False
    if n <= 3: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def gcd(a, b): return math.gcd(int(a), int(b))
def lcm(a, b): return abs(int(a) * int(b)) // math.gcd(int(a), int(b))

def get_factors(n):
    n = abs(n)
    factors = set()
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            factors.add(i)
            factors.add(n // i)
    return sorted(list(factors))

def clean_latex_output(q_str):
    """
    [V47.7 Fix] LaTeX 格式清洗器 - 尊重預先包裝的 $...$ 塊
    
    邏輯：
    1. 提取已經包裝的 $...$ 塊，暫時保留
    2. 對剩餘的純文本進行中文/數學分離
    3. 合併結果
    """
    if not isinstance(q_str, str): 
        return str(q_str)
    
    import re
    
    # 第一步：提取所有已經包裝的 $...$ 塊
    latex_blocks = []
    def placeholder_replacer(match):
        latex_blocks.append(match.group(1))
        return f"__LATEX_BLOCK_{len(latex_blocks)-1}__"
    
    # 提取 $...$ 塊
    temp_str = re.sub(r'\$([^$]*)\$', placeholder_replacer, q_str)
    
    # 第二步：對剩餘的純文本進行處理
    clean_q = temp_str.strip()
    
    # 修復運算符：* -> \times, / -> \div（只在非 LaTeX 塊中）
    clean_q = re.sub(r'(?<![\\a-zA-Z])\s*\*\s*(?!_)', r' \\times ', clean_q)
    clean_q = re.sub(r'(?<![\\a-zA-Z])\s*/\s*(?![{}])', r' \\div ', clean_q)
    
    # 修復雙重括號 ((...)) -> (...)
    clean_q = re.sub(r'\(\(([^()]+)\)\)', r'(\1)', clean_q)
    
    # 移除多餘空白
    clean_q = re.sub(r'\s+', ' ', clean_q).strip()
    
    # 第三步：智能分離中文與數學式（僅對非 LaTeX 塊的部分）
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', clean_q))
    
    if has_chinese:
        # 分離中文和數學
        math_pattern = r'(?:[\d\-+*/()（）\[\]【】\\]|\\[a-z]+(?:\{[^}]*\})?|[a-zA-Z])+(?:\s+(?:[\d\-+*/()（）\[\]【】\\]|\\[a-z]+(?:\{[^}]*\})?|[a-zA-Z])+)*'
        
        parts = []
        last_end = 0
        
        for match in re.finditer(math_pattern, clean_q):
            start, end = match.span()
            
            # 添加之前的文本（中文部分）
            if start > last_end:
                text_part = clean_q[last_end:start].strip()
                if text_part:
                    parts.append(text_part)
            
            # 添加數學部分（需要包裹 $）
            math_part = match.group().strip()
            if math_part:
                parts.append(f'${math_part}$')
            
            last_end = end
        
        # 添加剩餘的文本
        if last_end < len(clean_q):
            text_part = clean_q[last_end:].strip()
            if text_part:
                parts.append(text_part)
        
        # 合併
        result = ' '.join(parts)
        result = re.sub(r'\s+', ' ', result).strip()
        
        # 清理連續的 $ 符號
        result = re.sub(r'\$\s+\$', ' ', result)
    else:
        # 沒有中文：直接包裹整個表達式
        result = f"${clean_q}$"
    
    # 第四步：恢復 LaTeX 塊
    for i, block in enumerate(latex_blocks):
        result = result.replace(f"__LATEX_BLOCK_{i}__", f"${block}$")
    
    return result


def check(user_answer, correct_answer):
    """
    [V45.7 Smart Validator]
    """
    if not user_answer: return {"correct": False, "result": "未作答"}
    
    def parse_value(val_str):
        s = str(val_str).strip().replace(" ", "").replace("$", "").replace("\\", "")
        s = s.replace("times", "*").replace("div", "/")
        try:
            s = re.sub(r'frac\{(\d+)\}\{(\d+)\}', r'(\1/\2)', s)
            s = re.sub(r'(?<=\d)\(', r'*(', s)  # NEW [V47.3]: 將 "3(1/2)" 轉為 "3*(1/2)" 避免 eval 視為函式呼叫
            return float(eval(s))
        except:
            return None

    val_u = parse_value(user_answer)
    val_c = parse_value(correct_answer)

    if val_u is not None and val_c is not None:
        if math.isclose(val_u, val_c, rel_tol=1e-7):
            return {"correct": True, "result": "正確"}
    
    u_clean = str(user_answer).strip().replace(" ", "")
    c_clean = str(correct_answer).strip().replace(" ", "")
    if u_clean == c_clean:
        return {"correct": True, "result": "正確"}

    return {"correct": False, "result": f"正確答案: {correct_answer}"}

# [V47.4 跨領域工具組]

def clamp_fraction(fr, max_den=1000, max_num=100000):
    """防止分數爆炸：限制分子分母"""
    if not isinstance(fr, Fraction):
        fr = Fraction(fr)
    if abs(fr.numerator) > max_num or fr.denominator > max_den:
        fr = fr.limit_denominator(max_den)
    return fr

def safe_pow(base, exp, max_abs_exp=10):
    """安全指數運算，避免溢出"""
    if abs(exp) > max_abs_exp:
        return Fraction(0)  # 或其他安全默認
    try:
        if isinstance(base, Fraction) and exp >= 0:
            return Fraction(base.numerator ** exp, base.denominator ** exp)
        elif isinstance(base, Fraction) and exp < 0:
            return Fraction(base.denominator ** (-exp), base.numerator ** (-exp))
        else:
            return Fraction(int(base ** exp), 1)
    except:
        return Fraction(0)

def factorial_bounded(n, max_n=1000):
    """有界階乘"""
    if not (0 <= n <= max_n):
        return None
    result = 1
    for i in range(2, int(n) + 1):
        result *= i
    return result

def nCr(n, r, max_n=5000):
    """組合數 C(n,r)"""
    n, r = int(n), int(r)
    if not (0 <= r <= n <= max_n):
        return None
    if r > n - r:
        r = n - r
    result = 1
    for i in range(r):
        result = result * (n - i) // (i + 1)
    return result

def nPr(n, r, max_n=5000):
    """排列數 P(n,r)"""
    n, r = int(n), int(r)
    if not (0 <= r <= n <= max_n):
        return None
    result = 1
    for i in range(n, n - r, -1):
        result *= i
    return result

def rational_gauss_solve(a, b, p, c, d, q):
    """2x2 線性系統求解器 (用 Fraction)
    a*x + b*y = p
    c*x + d*y = q
    返回 {'x': Fraction, 'y': Fraction} 或 None
    """
    a, b, p, c, d, q = [Fraction(x) for x in [a, b, p, c, d, q]]
    det = a * d - b * c
    if det == 0:
        return None  # 無解或無窮解
    x = (p * d - b * q) / det
    y = (a * q - p * c) / det
    return {'x': x, 'y': y}

def normalize_angle(theta, unit='deg'):
    """角度正規化到 [0, 360) 或 [0, 2π)"""
    theta = float(theta)
    if unit == 'deg':
        theta = theta % 360
        if theta < 0:
            theta += 360
        return theta
    else:  # rad
        theta = theta % (2 * math.pi)
        if theta < 0:
            theta += 2 * math.pi
        return theta

def fmt_set(iterable, braces='{}'):
    """集合顯示：元素使用 fmt_num（不含外層 $）"""
    items = [fmt_num(x) for x in iterable]
    inner = ", ".join(items)
    return ("\\{" + inner + "\\}") if braces == '\\{\\}' else ("{" + inner + "}")

def fmt_interval(a, b, left_open=False, right_open=False):
    """區間顯示：(a,b)、[a,b)、(a,b]、[a,b]；端點使用 fmt_num"""
    l = "(" if left_open else "["
    r = ")" if right_open else "]"
    return f"{l}{fmt_num(a)}, {fmt_num(b)}{r}"

def fmt_vec(*coords):
    """向量顯示：分量使用 fmt_num（不含外層 $）"""
    inner = ", ".join(fmt_num(x) for x in coords)
    return "\\langle " + inner + " \\rangle"

# ✅ 預設的 LaTeX 運算子映射（四則）- 全域可用
op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
'''

# ==============================================================================
# 3. 骨架與 Prompt 定義
# ==============================================================================
CALCULATION_SKELETON = r'''

# [INJECTED UTILS]
''' + PERFECT_UTILS + r'''

# [AI GENERATED CODE]
# ---------------------------------------------------------
''' + "\n"  # <--- [修正] 強制補一個換行，防止黏合錯誤

def get_dynamic_skeleton(skill_id):
    return CALCULATION_SKELETON

# ==============================================================================
# [Research Edition] Ablation Prompts
# ==============================================================================

BARE_MINIMAL_PROMPT = r"""你是 Python 程式設計師。請根據以下 MASTER_SPEC 生成數學題目生成函數。

要求：
1. 實作函數：def generate(level=1, **kwargs)
2. 回傳字典格式：{'question_text': 題目字串, 'answer': 答案字串, 'mode': 1}
3. 只輸出 Python 代碼，不要有任何說明或 Markdown 標記

🔴 LaTeX 格式鐵律（必須遵守）：
   question_text 格式：
      ✅ 正確："計算 $(-3) + 5$ 的值"（中文在外，數學式用 $ $ 包裹）
      ✅ 正確："求 $2 \times (-4)$ 的結果"
      ❌ 錯誤："$(-3) + 5$"（缺少中文說明）
      ❌ 錯誤："計算$(-3) + 5$的值"（$ $ 與中文直接相連）
   
   answer 格式：
      ✅ 正確："42"（純數字）
      ✅ 正確："\frac{3}{7}"（LaTeX 分數，不含 $ $）
      ❌ 錯誤："答案是 42"（不要加中文說明）

📐 題目字串拼接範例（3步驟標準流程）：
   # 步驟1: 先拼接數學式（不含 $ $）
   math_expr = f"{fmt_num(n1)} {op_latex['+']} {fmt_num(n2)}"
   
   # 步驟2: 組合中文與數學式（手動加 $ $）
   q_str = f"計算 ${math_expr}$ 的值"
   
   # 步驟3: 最後呼叫 clean_latex_output()（可選，用於進階清洗）
   question_output = clean_latex_output(q_str)
   
   # 回傳
   return {'question_text': question_output, 'answer': str(answer), 'mode': 1}

❌ 常見錯誤（絕對不要這樣寫）：
   # 錯誤1: 在 f-string 內呼叫 clean_latex_output()
   q_str = f"計算 {clean_latex_output(expr)} 的值"  # ❌ 錯誤
   
   # 錯誤2: 字串拼接時用 + 運算符混合函式呼叫
   q_str = f"計算 {clean_latex_output(fmt_num(n1) + op_latex['*'] + fmt_num(n2))} 的值"  # ❌ 錯誤

📐 使用以下工具函數（已預先定義）：
   - fmt_num(x): 格式化數字（負數自動加括號）
   - op_latex: 運算符映射字典 {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
   - clean_latex_output(q_str): 自動清洗 LaTeX 格式（僅用於最後一步）

提示：你可以使用 Python 的 random, math, Fraction 等標準庫。
"""

UNIVERSAL_GEN_CODE_PROMPT = r"""【角色】K12 數學演算法工程師。
【任務】實作 `def generate(level=1, **kwargs)`，根據 MASTER_SPEC 產出完整的 Python 代碼。
【限制】僅輸出代碼，無 Markdown/說明。**嚴禁 eval/exec/safe_eval**。

🔴 【最最最重要】輸出格式要求
- **完全禁止**任何 Markdown 代碼塊標記：
  ❌ ```python（開頭）
  ❌ ```（結尾）
  ❌ 任何 Markdown 格式符號
- **必須輸出純 Python 代碼**（直接從 `def generate` 開始）
- **沒有任何額外的說明或格式化**
- 示例（正確）：
  ```
  def generate(level=1, **kwargs):
      # 代碼內容
      return {...}
  ```
- 示例（❌ 錯誤）：
  ```
  ```python
  def generate(level=1, **kwargs):
      # 代碼內容
      return {...}
  ```
  ```

🔴 【CRITICAL】工具函數保護條款
- 以下工具函數已由系統預先定義在環境中，**嚴禁重新定義或修改**：
  * fmt_num(num, signed=False, op=False) - 已完整實作，包括負數括號、分數處理
  * to_latex(num) - 已實作 Fraction 轉 LaTeX
  * clean_latex_output(q_str) - 已實作自動 $ $ 包裝
  * check(user_answer, correct_answer) - 已實作答案驗證
  * op_latex 字典 - {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
- **禁止的行為**：
  ❌ def fmt_num(x): ...  (重新定義)
  ❌ def to_latex(x): ...  (重新定義)
  ❌ fmt_num = lambda x: ...  (覆蓋定義)
- **如果你的代碼中有上述定義，會導致運行時 TypeError！**
- **直接使用這些函數即可，無需定義**

🔴 **最高優先級：MASTER_SPEC 是唯一權威來源**
- 你收到的 MASTER_SPEC 包含完整的題型定義、複雜度要求和實現檢查清單
- **必須逐項實現 MASTER_SPEC 中的所有要求**，包括：
  * entities 定義的所有變數和約束
  * complexity_requirements 定義的最小複雜度
  * implementation_checklist 中的每一項檢查
  * templates 中描述的所有計算步驟
- **任何簡化都是錯誤的**：如果 MASTER_SPEC 要求 3 個運算數，你不能只生成 2 個
- **本文件末尾的範例僅供結構參考**，絕不代表實際邏輯

🔴 **實現前必須檢查 MASTER_SPEC 的以下部分**：
1. **complexity_requirements**: 確認最小複雜度要求
2. **entities.constraints**: 確認每個變數的範圍和限制
3. **implementation_checklist**: 確認所有必須實現的項目
4. **construction**: 確認所有計算步驟

⚠️ 重要約束：
1. 代碼必須少於 50 行
2. **所有數學運算必須使用 Python 原生運算符** (+, -, *, /)，**嚴禁使用 eval(), exec(), safe_eval() 或任何字符串評估**
3. return 字典格式固定為：
   return {
       'question_text': q,
       'correct_answer': a,
       'answer': a,
       'mode': 1
   }
4. fmt_num() 只接受 (num, signed=Bool, op=Bool)，不接受 'fraction' 等字串參數

【預載工具 (直接使用，禁止重新定義)】
- random, math, re, ast, operator, Fraction
- fmt_num(n), to_latex(n), clean_latex_output(q)
- check(u, c)
- op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
- 數論: gcd, lcm, is_prime, get_factors
- 進階: clamp_fraction, safe_pow, factorial_bounded, nCr, nPr, rational_gauss_solve, normalize_angle, fmt_set, fmt_interval, fmt_vec

【生成管線標準】
0. **🔴 首要原則：完整實作 MASTER_SPEC + 中文+LaTeX 格式**
   - **必須**閱讀並完整實作 MASTER_SPEC 中的所有 template 邏輯
   - **必須**遵守 MASTER_SPEC 中的 entities、constraints、operators 定義
   - **必須**實現 MASTER_SPEC 要求的複雜度（運算數數量、運算符種類、括號結構等）
   - **必須**遵循 formatting 部分的中文+LaTeX 規則（見下方【格式化三步驟】）
   - **禁止**簡化或省略 MASTER_SPEC 中的任何要求
   - **範例僅供結構參考**，不代表實際邏輯！

【格式化三步驟】（針對包含中文的題目）
Step A: 構造 LaTeX 式子
   expr = fmt_num(a) + op_latex['*'] + fmt_num(b) + op_latex['+'] + fmt_num(c)
   # 產生: "a \\times b + c"

Step B: 嵌入中文敘述
   q = f"已知多項式 $f(x) = {expr}$，求 $f'(x)$。"
   # 此時還沒有呼叫 clean_latex_output()

Step C: 清洗並自動加 $ $
   q = clean_latex_output(q)  # 產生最終格式，自動補足 $ $ 符號
   # 結果: "已知多項式 $f(x) = a \\times b + c$，求 $f'(x)$。"

1. **變數生成**: 
   - **嚴格遵守 MASTER_SPEC 中的 entities 定義**：
     * 數值範圍（value_range）
     * 分母範圍（denominator_range）
     * 約束條件（constraints）
     * 互斥規則（mutually_exclusive_with）
   - **通用安全原則**：
     * 分母/除數不可為 0（使用 while 迴圈確保）
     * 遵守 MASTER_SPEC 定義的數值邊界
   
2. **運算**: 
   - **必須使用 Python 直接計算** (Fraction/int)。
   - **嚴禁 eval/exec/safe_eval**。
   - 正確示例：
     ```python
     # ✅ 正確：直接運算
     result = Fraction(1, 2) + Fraction(3, 4)
     result = a * b - c
     result = (a + b) * (c - d)
     
     # ❌ 錯誤：使用 eval 相關
     result = safe_eval(f'{a} + {b}')
     result = eval(expression_string)
     ```

3. **⚠️ 運算順序與括號（關鍵！）**：
   - **逐步計算模式**：如果分步計算
     * 題目**必須**添加對應括號以匹配計算順序
     * 範例（正確）：
       ```python
       val1 = a + b            # 步驟 1
       val2 = val1 * c         # 步驟 2
       val3 = val2 - d         # 步驟 3
       q = f'(({fmt_num(a)} + {fmt_num(b)}) {op_latex["*"]} {fmt_num(c)}) {op_latex["-"]} {fmt_num(d)}'
       # ✅ 括號對應計算順序
       ```
     * 範例（錯誤）：
       ```python
       val1 = a + b
       val2 = val1 * c
       q = f'({fmt_num(a)} + {fmt_num(b)}) {op_latex["*"]} {fmt_num(c)} {op_latex["-"]} {fmt_num(d)}'
       # ❌ 缺少外層括號！
       # 題目暗示：先算乘法再減法（數學優先級）
       # 實際計算：((a+b)*c)-d（逐步左結合）
       # 結果：題目 ≠ 答案！
       ```
   
   - **標準優先級模式**：遵守數學運算優先級
     * 題目可以省略外層括號（依賴數學優先級）
     * 範例：
       ```python
       result = (a + b) * c - d  # Python 自動按優先級計算
       q = f'({fmt_num(a)} + {fmt_num(b)}) {op_latex["*"]} {fmt_num(c)} {op_latex["-"]} {fmt_num(d)}'
       # ✅ 遵守數學優先級
       ```

4. **題幹格式化 (LaTeX + 中文處理)**：
   
   🔴 **LaTeX 格式化鐵律**：
   - **中文字和文字敘述永遠在 $ $ 外面**
   - **數學式子永遠在 $ $ 裡面**
   - **使用 clean_latex_output() 自動包裝**（僅呼叫一次）
   
   ✅ **正確模式 A：純數學式**
   ```python
   # 只有數學式，無中文
   q = f"{fmt_num(a)} + {fmt_num(b)}"
   q = clean_latex_output(q)  # 自動變成 $a + b$
   ```
   
   ✅ **正確模式 B：中文 + 數學式**
   ```python
   # 方法 1：中文在外，clean_latex_output 包數學式
   q = f"{fmt_num(a)} + {fmt_num(b)}"
   q = clean_latex_output(q)  # 得到 $a + b$
   q = f"計算 {q} 的值"  # 得到 "計算 $a + b$ 的值"
   
   # 方法 2：手動包裝（不推薦，容易出錯）
   q = f"計算 ${fmt_num(a)} + {fmt_num(b)}$ 的值"
   # 不要再呼叫 clean_latex_output()！
   ```
   
   ❌ **錯誤示範**：
   ```python
   # 錯誤 1：中文在 $ $ 內（matplotlib 無法渲染）
   q = f"計算 {fmt_num(a)} + {fmt_num(b)} 的值"
   q = clean_latex_output(q)  # ❌ 變成 $計算 a + b 的值$
   
   # 錯誤 2：重複包裝
   q = f"計算 ${fmt_num(a)} + {fmt_num(b)}$ 的值"
   q = clean_latex_output(q)  # ❌ 變成 $計算 $a + b$ 的值$
   
   # 錯誤 3：fmt_num 參數錯誤
   q = f"${fmt_num(n, 'fraction')}$"  # ❌ 無此參數
   ```
   
   🔴 **f-string 中的 LaTeX 運算符**：
   ```python
   # ✅ 正確：使用 op_latex 字典
   q = f"{fmt_num(a)} {op_latex['*']} {fmt_num(b)}"  # a \times b
   q = f"{fmt_num(a)} {op_latex['/']} {fmt_num(b)}"  # a \div b
   
   # ❌ 錯誤：直接寫符號
   q = f"{fmt_num(a)} * {fmt_num(b)}"  # ❌ 顯示為 a * b（不是 ×）
   q = f"{fmt_num(a)} / {fmt_num(b)}"  # ❌ 顯示為 a / b（不是 ÷）
   ```
   
   🔴 **fmt_num 的正確使用**：
   ```python
   # ✅ 正確：基本用法
   fmt_num(5)           # "5"
   fmt_num(-3)          # "(-3)"
   fmt_num(Fraction(1, 2))  # "\\frac{1}{2}"
   
   # ✅ 正確：在 f-string 中必須用 {}
   q = f"{fmt_num(a)} + {fmt_num(b)}"  # 正確
   
   # ❌ 錯誤：雙層括號或無效參數
   q = f"${{fmt_num(n), 'fraction'}}"  # ❌ 語法錯誤
   q = f"{fmt_num(n, 'fraction')}"     # ❌ 無此參數
   ```
   
   🔴 **指數格式化 (LaTeX 上標) - 關鍵！**：
   ```python
   # 問題：如何在 f-string 中正確表達 a^n？
   
   # ❌ 錯誤 1：單層大括號
   q = f"{fmt_num(a)}^{fmt_num(n)}"  # 變成 "a^{fmt_num(n)}"
   
   # ❌ 錯誤 2：格式化函數後接大括號
   q = f"({fmt_num(a)}x {op_latex['+']} {fmt_num(b)})^{fmt_num(p)}"
   # 變成 "(...some_latex...)^{fmt_num(p)}" → ❌ 亂碼
   
   # ✅ 正確：使用轉義的三層大括號 {{{...}}}
   # 原理：f-string 中 {{ 轉義為 {，所以 {{{x}}} 變成 {x}
   q = f"{fmt_num(a)}^{{{fmt_num(n)}}}"  # 變成 "a^{value_of_n}"
   q = f"({fmt_num(a)}x {op_latex['+']} {fmt_num(b)})^{{{fmt_num(p)}}}"
   # 變成 "(...some_latex...)^{value_of_p}" → ✅ 正確的 LaTeX 上標
   
   # 等效的非 f-string 寫法：
   a_latex = fmt_num(a)
   n_latex = fmt_num(n)
   q = f"{a_latex}^{{{n_latex}}}"  # 一樣正確
   ```
   
   **指數規則總結**：
   - **不要**：`^{fmt_num(...)}` 或 `^fmt_num(...)`
   - **要用**：`^{{{fmt_num(...)}}}`（三層括號表達法）
   - **原因**：f-string 中 { 和 } 有特殊意義，需要轉義

5. **答案 (a)**: 
   - ⚠️ **答案格式必須是純數字，不使用LaTeX格式**
   - 整數：直接用 `str(result)` 或 `str(int(result))`
   - 分數：使用 Python Fraction 的字符串表示 `str(result)` (自動格式為 "3/7")
   - 帶分數：手動轉換為 "整數 分子/分母" 格式
   - **禁止**使用 `fmt_num(result)` 作為答案（會產生LaTeX格式）
   - **正確示例**：
     ```python
     # 整數答案
     a = str(result)  # "42"
     
     # 分數答案
     a = str(result)  # "3/7" (Fraction自動格式化)
     
     # 帶分數答案
     if result.numerator > result.denominator:
         whole = result.numerator // result.denominator
         rem = result.numerator % result.denominator
         a = f"{whole} {rem}/{result.denominator}"  # "2 3/7"
     else:
         a = str(result)  # "3/7"
     ```
6. **回傳**: `return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}`

【防呆檢查】
- 變數名固定為 `q` 和 `a`。
- 嚴禁 `import` (已預載)。
- 嚴禁自創函式 (如 random_fraction)。
- 列表操作需小心 IndexError。

【範例結構 (僅供參考，必須根據 MASTER_SPEC 生成實際邏輯)】
⚠️ **致命警告**：
- 以下範例**過於簡單**，僅展示代碼框架結構
- **禁止直接使用此範例**，必須根據 MASTER_SPEC 完整實作
- 如果你的代碼和此範例類似，說明你**沒有實作 MASTER_SPEC**

```python
# ========== 結構框架 (NOT 實際邏輯) ==========
def generate(level=1, **kwargs):
    # 第 1 步：根據 MASTER_SPEC 的 entities 和 variables 生成所有必要變數
    # TODO: 實作 MASTER_SPEC 定義的變數生成邏輯
    # 範例：var1 = <根據 MASTER_SPEC 生成>
    # 範例：var2 = <根據 MASTER_SPEC 生成>
    
    # 第 2 步：根據 MASTER_SPEC 的 construction 執行計算
    # TODO: 實作 MASTER_SPEC 定義的所有計算步驟
    # 範例：result = <根據 MASTER_SPEC 計算>
    
    # 第 3 步：構建題目 LaTeX（使用 fmt_num 和 op_latex）
    # TODO: 根據 MASTER_SPEC 的 formatting.question_display
    # q = <構建題目字串>
    # q = clean_latex_output(q)  # 僅呼叫一次
    
    # 第 4 步：格式化答案為純數字
    # TODO: 根據 MASTER_SPEC 的 formatting.answer_display
    # a = str(result)  # 或其他適當格式
    
    # 第 5 步：返回標準格式
    return {
        'question_text': q,
        'correct_answer': a,
        'answer': a,
        'mode': 1
    }
```

⚠️ **實作檢查清單**：完成代碼後，對照 MASTER_SPEC 的 implementation_checklist 逐項確認：
- [ ] 是否生成了所有必要的變數？
- [ ] 是否遵守了所有 constraints？
- [ ] 是否達到了 complexity_requirements 的最小要求？
- [ ] 是否實現了所有 construction 步驟？
- [ ] 題目和答案格式是否符合 formatting 規則？
"""

# ==============================================================================
# 4. 修復與驗證工具
# ==============================================================================

class ASTHealer(ast.NodeTransformer):
    """
    [V45.0 AST Logic Surgeon]
    深入語法樹層級，修復 Regex 無法觸及的邏輯錯誤。
    """
    def __init__(self):
        self.fixes = 0

    def visit_BinOp(self, node):
        self.generic_visit(node)
        # 1. 修復次方符號：將 XOR (^) 轉為 Pow (**)
        if isinstance(node.op, ast.BitXor):
            self.fixes += 1
            node.op = ast.Pow()
            return node
        # [V47.4 REMOVED] 不再攔截 ast.Div：
        # Python Fraction 物件本來就支援 / 運算回傳 Fraction
        # 攔截會導致 Fraction(Fraction(...), Fraction(...)) TypeError
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        
        # 0. [V10.0 新增] 檢測並處理幻覺函數 (Hallucinated Functions)
        # 常見的 LLM 幻覺函數包括：build_polynomial_text, format_polynomial, poly_to_latex 等
        hallucinated_funcs = [
            'build_polynomial_text', 'format_polynomial', 'poly_to_latex',
            'build_expression', 'format_expression', 'latex_polynomial',
            'polynomial_text', 'expr_to_latex', 'build_latex'
        ]
        
        if isinstance(node.func, ast.Name) and node.func.id in hallucinated_funcs:
            self.fixes += 1
            print(f"🔴 [AST Healer] 偵測到幻覺函數: {node.func.id}() -> 重定向到 build_polynomial_text()")
            
            # 將幻覺函數調用轉換為調用真實的 build_polynomial_text
            node.func.id = 'build_polynomial_text'
            return node
        
        # 1. 攔截 eval/exec/safe_eval (轉接或標準化為 safe_eval)
        # 或者直接攔截 safe_eval (如果 AI 已經學會用 safe_eval 但用錯了參數)
        target_funcs = ['eval', 'exec', 'safe_eval']
        
        if isinstance(node.func, ast.Name) and node.func.id in target_funcs:
            self.fixes += 1
            node.func.id = 'safe_eval'
            
            # [V46.0 Fix] 強制清洗 safe_eval 的參數
            # 我們的 safe_eval 只接受一個參數 (expr_str)
            # 如果 AI 傳了 globals/locals 字典 (例如 eval(s, {...}))，全部丟掉
            if len(node.args) > 1:
                print(f"🧹 [AST Healer] 清除 safe_eval 的多餘參數 (只保留運算式)")
                node.args = [node.args[0]] # 只保留第一個
                
            return node
        
        # 2. 處理 fmt_num
        if isinstance(node.func, ast.Name) and node.func.id == 'fmt_num':
            # [Fix A] 移除幻想參數
            if node.keywords:
                original_len = len(node.keywords)
                node.keywords = [k for k in node.keywords if k.arg in ['signed', 'op']]
                if len(node.keywords) != original_len:
                    self.fixes += 1
            # [Fix B] 補救空參數
            if not node.args:
                self.fixes += 1
                node.args = [
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='random', ctx=ast.Load()),
                            attr='randint',
                            ctx=ast.Load()
                        ),
                        args=[
                            ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=10)),
                            ast.Constant(value=10)
                        ],
                        keywords=[]
                    )
                ]
            return node
        
        # 3. [V47.0] 格式化函式重定向（加白名單保護系統工具）
        if isinstance(node.func, ast.Name):
            # 白名單：保護系統合法工具，不要動手腳
            protected = {
                'fmt_num', 'to_latex', 'clean_latex_output', 'check', 'safe_eval',
                'gcd', 'lcm', 'is_prime', 'get_factors',
                'clamp_fraction', 'safe_pow', 'factorial_bounded', 'nCr', 'nPr',
                'rational_gauss_solve', 'normalize_angle',
                'fmt_set', 'fmt_interval', 'fmt_vec'
            }
            
            # 只對非白名單且可疑名稱的函數進行重定向
            if node.func.id not in protected and re.search(r'(format|latex|display)', node.func.id, re.IGNORECASE):
                self.fixes += 1
                node.func.id = 'fmt_num'
                node.keywords = [k for k in node.keywords if k.arg in ['signed', 'op']]
                return node
        return node
    
    def visit_Import(self, node):
        self.fixes += 1
        return None
    
    def visit_ImportFrom(self, node):
        self.fixes += 1
        return None
    
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        
        # 1. [原有逻辑] 移除自创的格式化函数
        if re.search(r'(Format|LaTeX|Display)', node.name, re.IGNORECASE) and node.name != 'generate':
            self.fixes += 1
            return None 
        
        # 2. [V9.2.5 新增] 检测内部辅助函数是否缺少默认返回值
        # 目标：避免 "TypeError: cannot unpack non-iterable NoneType object"
        if node.name != 'generate' and node.body:  # 排除主函数
            # 检查函数体是否有 for 循环
            has_loop = False
            for stmt in node.body:
                if isinstance(stmt, (ast.For, ast.While)):
                    has_loop = True
                    break
            
            if has_loop:
                #检查最后一个语句是否是 return
                last_stmt = node.body[-1]
                
                # 如果最后一个语句不是 return，或者是循环本身，添加默认返回
                if not isinstance(last_stmt, ast.Return):
                    print(f"🔧 [AST Healer] 内部函数 '{node.name}' 缺少默认返回值，正在添加...")
                    
                    # 添加 return (0, 0) 作为默认值（适用于大多数辅助函数）
                    default_return = ast.Return(
                        value=ast.Tuple(
                            elts=[ast.Constant(value=0), ast.Constant(value=0)],
                            ctx=ast.Load()
                        )
                    )
                    node.body.append(default_return)
                    self.fixes += 1
        
        return node
    
    def visit_While(self, node):
        """
        [Circuit Breaker]
        將潛在的無窮迴圈 while True 轉換為有限的 for _ in range(1000)
        [V45.9 Fix]: 增加次數至 1000，避免隨機生成演算法過早失敗導致變數未定義。
        """
        self.generic_visit(node)
        
        is_infinite = False
        
        # 檢查是否為 while True
        # 1. 現代 Python (3.8+)
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            is_infinite = True
        # 2. 舊版 Python (<3.8) - 必須檢查 hasattr 避免 3.12+ 崩潰
        elif hasattr(ast, 'NameConstant') and isinstance(node.test, ast.NameConstant) and node.test.value is True:
            is_infinite = True
            
        if is_infinite:
            self.fixes += 1
            print(f"🛑 [AST Healer] 熔斷機制啟動: while True -> for loop (1000 runs)")
            
            # 轉換為 for _ in range(1000):
            return ast.For(
                target=ast.Name(id='_safety_loop_var', ctx=ast.Store()),
                iter=ast.Call(
                    func=ast.Name(id='range', ctx=ast.Load()),
                    args=[ast.Constant(value=1000)], # [Fix] 給予更多嘗試機會
                    keywords=[]
                ),
                body=node.body,
                orelse=node.orelse,
                type_comment=None
            )
            
        return node

    def visit_Assign(self, node):
        self.generic_visit(node)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
            target_tuple = node.targets[0]
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'fmt_num':
                self.fixes += 1
                val_var = target_tuple.elts[0]
                latex_var = target_tuple.elts[1]
                if node.value.args:
                    num_source = node.value.args[0]
                else:
                    num_source = ast.Call(
                        func=ast.Attribute(value=ast.Name(id='random', ctx=ast.Load()), attr='randint', ctx=ast.Load()),
                        args=[ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=10)), ast.Constant(value=10)],
                        keywords=[]
                    )
                assign_val = ast.Assign(targets=[val_var], value=num_source)
                assign_latex = ast.Assign(
                    targets=[latex_var],
                    value=ast.Call(
                        func=ast.Name(id='fmt_num', ctx=ast.Load()),
                        args=[val_var],
                        keywords=node.value.keywords
                    )
                )
                return [assign_val, assign_latex]
        
        return node

# [NEW] 新增這個函式來過濾 import
def clean_redundant_imports(code_str):
    """
    [V47.6 CRITICAL FIX] 不刪除任何 import！
    
    原因：
    1. LLM 新生成的 import 是必需的（如 from random import randint）
    2. PERFECT_UTILS 後續會注入全域 import，不需要提前刪除
    3. AST Healer 會處理真正的重複問題
    
    修復策略：保留所有 import，讓後續管線處理重複檢測
    """
    # 不做任何修改，直接回傳原始代碼
    return code_str, 0, []

def remove_forbidden_functions_unified(code_str, forbidden_list):
    """
    [Performance Fix V9.2.1] 統一的函數移除器
    合併原本在 refine_ai_code(), 工具函式重定義偵測器, 通用語法修復 三處的邏輯
    避免重複掃描，提升 15-20% 執行速度
    """
    lines = code_str.split('\n')
    cleaned_lines = []
    skip_mode = False
    target_indent = -1
    removed_count = 0
    
    for line in lines:
        # 檢查是否進入禁止函數定義
        should_skip = False
        for func_name in forbidden_list:
            # 嚴格匹配定義行（避免誤判函數調用）
            if re.match(rf'^\s*def\s+{func_name}\s*\(', line):
                skip_mode = True
                target_indent = len(line) - len(line.lstrip())
                removed_count += 1
                should_skip = True
                print(f"🔧 [Unified Remover] 移除函數定義: {func_name}")
                break
        
        if should_skip:
            continue
        
        if skip_mode:
            current_indent = len(line) - len(line.lstrip())
            # 空行或註釋：跳過
            if not line.strip() or line.strip().startswith('#'):
                continue
            # 縮排回到定義層級或更外層：結束跳過模式
            if current_indent <= target_indent and line.strip():
                skip_mode = False
            else:
                continue  # 仍在函數體內，跳過
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines), removed_count

def refine_ai_code(code_str):
    """
    [Active Healer V9.2.1] 針對 14B 模型「不聽話」特性的強力矯正
    """
    fixes = 0
    refined_code = code_str

    # -----------------------------------------------------------
    # 0. [Complexity Checker] 檢測過於簡單的代碼（可能抄襲範例）
    # -----------------------------------------------------------
    # 警告標誌：如果代碼過於簡單，輸出警告（但不阻止生成）
    complexity_warnings = []
    
    # 檢查 1：運算數數量（尋找 random.randint 或 Fraction 的數量）
    num_random_ints = len(re.findall(r'random\.randint\(', code_str))
    num_fractions = len(re.findall(r'Fraction\(', code_str))
    total_operands = num_random_ints + num_fractions
    
    if total_operands < 3:
        complexity_warnings.append(f"⚠️  運算數過少: 僅發現 {total_operands} 個變數生成")
    
    # 檢查 2：運算符種類（尋找 *, /, +, - 的使用）
    has_multiply = '*' in code_str or '\\times' in code_str
    has_divide = '/' in code_str or '\\div' in code_str
    
    if not (has_multiply or has_divide):
        complexity_warnings.append("⚠️  缺少乘除運算: 僅發現加減運算")
    
    # 檢查 3：分數使用（至少應該有一個 Fraction）
    if num_fractions == 0:
        complexity_warnings.append("⚠️  未使用分數: 可能全為整數")
    
    # 檢查 4：代碼長度（太短可能是抄襲範例）
    code_lines = [line for line in code_str.split('\n') if line.strip() and not line.strip().startswith('#')]
    if len(code_lines) < 10:
        complexity_warnings.append(f"⚠️  代碼過短: 僅 {len(code_lines)} 行有效代碼")
    
    # 輸出警告（但繼續修復）
    if complexity_warnings:
        print("=" * 60)
        print("🔴 [Complexity Checker] 偵測到可能未完整實現 MASTER_SPEC:")
        for warning in complexity_warnings:
            print(f"   {warning}")
        print("   建議檢查: MASTER_SPEC 的 complexity_requirements 和 implementation_checklist")
        print("=" * 60)

    # -----------------------------------------------------------
    # 0.5 [Undefined Variable Healer] 修復反向推導中的未定義變數
    # -----------------------------------------------------------
    # 問題：AI 使用反向推導邏輯時，會在定義之前就使用變數（如 final_result）
    # 症狀：if op3 == '*': result = final_result // n4  # final_result 未定義
    # 修復：偵測並在迴圈開頭注入目標值定義
    
    # Pattern 1: 偵測使用未定義的 final_result 或 target_value
    undefined_vars = []
    for var_name in ['final_result', 'target_value', 'answer_value', 'result_value', 'tangent_x0', 'tangent_y0']:
        # 檢查是否在定義前使用
        usage_pattern = rf'\b{var_name}\b\s*[/\-+*%]|[/\-+*%=]\s*\b{var_name}\b|while.*\b{var_name}\b'
        definition_pattern = rf'\b{var_name}\s*='
        
        if re.search(usage_pattern, refined_code):
            # 找到第一次使用的位置
            usage_match = re.search(usage_pattern, refined_code)
            usage_pos = usage_match.start()
            
            # 檢查在此之前是否有定義
            pre_code = refined_code[:usage_pos]
            if not re.search(definition_pattern, pre_code):
                undefined_vars.append(var_name)
    
    if undefined_vars:
        print(f"🔧 [Healer] 偵測到未定義變數使用順序問題: {', '.join(undefined_vars)}")
        
        # [修復策略] 將未定義的變數定義注入到 generate() 函數開頭（Step 1 之前）
        # 這樣可以確保所有變數都在使用前被定義
        
        # 找到 def generate 或 Step 1 的位置
        gen_pattern = r'(def generate\(.*?\):\n\s+import random\n)'
        gen_match = re.search(gen_pattern, refined_code)
        
        if gen_match:
            # 在 import random 之後注入變數定義
            injection_lines = []
            for var_name in undefined_vars:
                if var_name in ['tangent_x0', 'x0']:
                    # 定義為隨機選擇（來自集合）
                    injection_lines.append(f"    {var_name} = random.choice([-2, -1, 0, 1, 2])")
                elif var_name in ['tangent_y0', 'y0']:
                    # 先定義為 0，後續會被重新計算
                    injection_lines.append(f"    {var_name} = 0  # Will be calculated later")
                else:
                    # 其他變數：定義為隨機整數
                    injection_lines.append(f"    {var_name} = random.randint(-50, 50)")
                    injection_lines.append(f"    if {var_name} == 0: {var_name} = 1  # 確保非零")
            
            if injection_lines:
                # 構造注入代碼
                injection_code = '\n'.join(injection_lines) + '\n'
                
                # 在 import random 之後插入
                insert_pos = gen_match.end()
                refined_code = refined_code[:insert_pos] + f"    # [Auto-Healer] 預先定義未定義變數\n" + injection_code + refined_code[insert_pos:]
                
                fixes += len(undefined_vars)
                print(f"   ✅ 已在 generate() 開頭注入 {len(undefined_vars)} 個變數的初始定義")
        else:
            print(f"   ⚠️  無法找到 generate() 函數定義，無法注入變數")

    # -----------------------------------------------------------
    # 0. [Garbage Cleaner] 移除 AI 生成的孤立字元和垃圾語法
    # -----------------------------------------------------------
    # 問題：AI 有時會生成孤立的反引號、特殊字元（如 `1, `2）導致 SyntaxError
    # 修復：移除孤立的反引號行（不在字串內的 ` 符號）
    
    garbage_patterns = [
        # Pattern 1: 孤立的反引號（單獨一行或在代碼行中）
        (r'^\s*`\d*\s*$', ''),  # 如: `1, `2
        (r'(\n\s*)`(\d*)\s*\n', r'\1\n'),  # 代碼間的孤立反引號
        
        # Pattern 2: 其他常見的 AI 垃圾字元
        (r'^\s*```\s*$', ''),  # 孤立的代碼塊標記
        (r'^\s*\.\.\.$', ''),  # 孤立的省略號
    ]
    
    for pattern, replacement in garbage_patterns:
        original = refined_code
        refined_code = re.sub(pattern, replacement, refined_code, flags=re.MULTILINE)
        if refined_code != original:
            count = original.count('\n') - refined_code.count('\n') + 1
            print(f"🔧 [Healer] 移除孤立字元: {pattern[:30]}... ({count} 處)")
            fixes += count

    # -----------------------------------------------------------
    # 1. [Hallucination Killer] 殺死自創函式，強制導回標準工具
    # -----------------------------------------------------------
    
    # 強制替換: clean_expression -> clean_latex_output (使用預編譯 pattern)
    # 14B 很喜歡自己寫 clean_expression，導致 Latex 處理不統一
    if "clean_expression" in refined_code:
        refined_code, n = COMPILED_PATTERNS['clean_expression'].subn('clean_latex_output(', refined_code)
        if n > 0:
            print(f"🔧 [Healer] 矯正幻覺函式: clean_expression -> clean_latex_output ({n} 處)")
            fixes += n

    # 移除自創的 clean_expression 定義 (因為我們已經把它換成系統工具了，留著定義也沒用)
    if "def clean_expression" in refined_code:
        # 簡單暴力的移除：將 def clean_expression... 換成註解
        refined_code, n = re.subn(r'(def clean_expression.*?:)', r'# \1 (Removed by Healer)', refined_code)
        fixes += n

    # -----------------------------------------------------------
    # 1.5 [Tuple Return Fixer] 修復錯誤的 tuple 返回格式
    # -----------------------------------------------------------
    # 問題：AI 有時會返回 tuple: return question, answer
    # 應該返回 dict: return {'question_text': ..., 'answer': ...}
    
    # Pattern 1: 偵測 return question, answer 或 return q, a 的模式
    tuple_return_patterns = [
        # return question_display_output, answer_display_output
        r'return\s+(\w+),\s*(\w+)\s*$',
        # return q, a
        r'return\s+([qa]|question|answer|result),\s*([qa]|question|answer|result)\s*$'
    ]
    
    for pattern in tuple_return_patterns:
        match = re.search(pattern, refined_code, re.MULTILINE)
        if match:
            var1 = match.group(1)
            var2 = match.group(2)
            
            print(f"🔧 [Healer] 偵測到 tuple 返回格式: return {var1}, {var2}")
            print(f"   正在轉換為標準 dict 格式...")
            
            # 替換為標準格式
            new_return = f"return {{'question_text': {var1}, 'correct_answer': {var2}, 'answer': {var2}, 'mode': 1}}"
            refined_code = re.sub(pattern, new_return, refined_code, flags=re.MULTILINE)
            fixes += 1
            print(f"   ✅ 已修復: {new_return}")
            break

    # -----------------------------------------------------------
    # 1.6 [Overly Strict Constraint Remover] 移除過度嚴格的複雜度約束
    # -----------------------------------------------------------
    # 問題：AI 有時會在代碼中加入過度嚴格的檢查，導致 Dynamic Sampling 失敗
    # 症狀：raise ValueError("Final result exceeds complexity constraints.")
    #      if abs(result.numerator) > 3 or abs(result.denominator) > 3: raise ...
    # 修復：移除這些不合理的運行時約束（生成邏輯已經控制了複雜度）
    
    overly_strict_patterns = [
        # Pattern 1: raise ValueError("Final result exceeds complexity constraints.")
        r'if\s+(?:isinstance\([^)]+,\s*Fraction\)\s*and\s*)?(?:\()?abs\([^)]+\.numerator\)\s*>\s*\d+\s+or\s+abs\([^)]+\.denominator\)\s*>\s*\d+(?:\))?\s*:\s*\n\s+raise\s+ValueError\(["\']Final result exceeds complexity constraints["\'][^\n]*\)',
        
        # Pattern 2: 帶括號的版本
        r'if\s+isinstance\([^)]+,\s*Fraction\)\s*:\s*\n\s+if\s+abs\([^)]+\.numerator\)\s*>\s*\d+\s+or\s+abs\([^)]+\.denominator\)\s*>\s*\d+\s*:\s*\n\s+raise\s+ValueError\(["\'][^"\']*complexity[^"\']*["\'][^\n]*\)',
    ]
    
    for pattern in overly_strict_patterns:
        matches = re.findall(pattern, refined_code, re.MULTILINE | re.DOTALL)
        if matches:
            print(f"🔧 [Healer] 偵測到過度嚴格的複雜度約束 ({len(matches)} 處)")
            print(f"   這會導致 Dynamic Sampling 失敗，正在移除...")
            
            # 移除這些約束
            refined_code = re.sub(pattern, '', refined_code, flags=re.MULTILINE | re.DOTALL)
            fixes += len(matches)
            print(f"   ✅ 已移除 {len(matches)} 個不合理的運行時約束")

    # -----------------------------------------------------------
    # 1.7 [Missing Append Fixer] - 已禁用
    # -----------------------------------------------------------
    # ⚠️ 此 Healer 會導致回歸錯誤（A 成功後修 B 會讓 A 失敗）
    # 問題：字串插入破壞後續匹配位置，且過度匹配正常代碼
    # TODO: 改用 AST-based 修復方式
    # 暫時完全移除此 Healer 的邏輯

    # -----------------------------------------------------------
    # 1.8 [Undefined Variable in Return Fixer] - 已禁用
    # -----------------------------------------------------------
    # ⚠️ 此 Healer 會導致回歸錯誤
    # TODO: 改用 AST-based 修復方式
    # 暫時完全移除此 Healer 的邏輯

    # -----------------------------------------------------------
    # 2. [Return Format Fixer] 強制修復回傳字典格式
    # -----------------------------------------------------------
    # 問題：模型常回傳 {'question': q, 'answer': a}，但系統要 {'question_text': ...}
    
    # 偵測錯誤的 key (單引號或雙引號)
    has_wrong_key = re.search(r"['\"]question['\"]\s*:", refined_code)
    
    if has_wrong_key:
        print(f"🔧 [Healer] 偵測到錯誤的 Return Key，正在重組...")
        
        # 策略：抓出 return {...} 的內容，直接暴力重寫
        # 假設變數名通常是 q 或 question, a 或 answer
        
        # 1. 先把 'question': 換成 'question_text':
        refined_code, n1 = re.subn(r"(['\"])question\1\s*:", r"'question_text':", refined_code)
        
        # 2. 確保有 correct_answer
        # 如果有 'answer': a，但沒有 'correct_answer'，我們需要補上
        if "'correct_answer'" not in refined_code and '"correct_answer"' not in refined_code:
            # [V9.2.2 Fix] 改進的 pattern：支持 f-string、字符串、變數名
            # 匹配: 'answer': <value>
            # <value> 可以是:
            #   - 變數名: a, ans, answer
            #   - f-string: f'...' 或 f"..."
            #   - 普通字串: '...' 或 "..."
            
            # 先嘗試找到整個 return 語句
            return_pattern = r"return\s*\{([^}]+)\}"
            match = re.search(return_pattern, refined_code)
            
            if match:
                dict_content = match.group(1)
                
                # 檢查是否有 'answer': ... 但沒有 'correct_answer':
                if re.search(r"['\"]answer['\"]", dict_content) and not re.search(r"['\"]correct_answer['\"]", dict_content):
                    # 提取 answer 的值（支持多種格式）
                    # Pattern 1: 'answer': f'...' 或 f"..."
                    ans_match = re.search(r"['\"]answer['\"]\s*:\s*f['\"]([^'\"]+)['\"]", dict_content)
                    if ans_match:
                        ans_value = f"f'{ans_match.group(1)}'"
                    else:
                        # Pattern 2: 'answer': '...' 或 "..."
                        ans_match = re.search(r"['\"]answer['\"]\s*:\s*['\"]([^'\"]+)['\"]", dict_content)
                        if ans_match:
                            ans_value = f"'{ans_match.group(1)}'"
                        else:
                            # Pattern 3: 'answer': variable_name
                            ans_match = re.search(r"['\"]answer['\"]\s*:\s*([a-zA-Z_]\w*)", dict_content)
                            if ans_match:
                                ans_value = ans_match.group(1)
                            else:
                                ans_value = "a"  # 默認
                    
                    # 重建 return 語句
                    new_dict_content = f"'question_text': q, 'correct_answer': {ans_value}, 'answer': {ans_value}, 'mode': 1"
                    new_return = f"return {{{new_dict_content}}}"
                    
                    # 替換整個 return 語句
                    refined_code = re.sub(return_pattern, new_return, refined_code)
                    fixes += 1
                    print(f"🔧 [Healer] 重建 return 語句：{new_return[:80]}...")

    # -----------------------------------------------------------
    # 2.5. [Variable Regeneration Blocker] 禁止在計算階段重新生成變數
    # -----------------------------------------------------------
    # 問題：AI 在計算階段使用 while 迴圈重新生成變數，可能導致：
    #   1. 無限迴圈（條件永遠無法滿足）
    #   2. 題目與答案不一致（變數被覆蓋）
    # 
    # 症狀示例：
    #   while next_operand == 0:
    #       next_operand = random.randint(-100, 100)  # ❌ 在計算中重新生成
    #
    # 解決方案：刪除這些危險的 while 迴圈
    # 安全性：只刪除包含 zero-check 的 while 迴圈
    
    # [V47.5 重構] 使用簡單有效的方法：移除所有 "while ... == 0:" 迴圈
    # -----------------------------------------------------------
    # [Healer V47.5] 零值檢查迴圈移除器 - 已禁用
    # -----------------------------------------------------------
    # ⚠️ 此 Healer 會導致回歸錯誤
    # 問題：直接刪除 while 迴圈會留下孤立的 continue/break 語句
    # 結果：SyntaxError: 'continue' not properly in loop
    # TODO: 改用 AST-based 安全移除

    # -----------------------------------------------------------
    # 2.6. [Semantic Error Fixer] 修復函數調用的參數類型不匹配
    # -----------------------------------------------------------
    # 問題：AI 生成的代碼可能在 while 迴圈中調用檢查函數（如 ensure_negative、ensure_fraction）
    #      但使用錯誤的參數類型，例如：
    #        ensure_negative(operators)  # ❌ operators 是字符串列表，不支援 < 比較
    #
    # 症狀：TypeError: '<' not supported between instances of 'str' and 'int'
    #
    # 解決方案：偵測並移除這些語義上不安全的 while 迴圈
    
    # 偵測 "while not ensure_xxx(operators)" 或類似的模式
    # 因為 ensure_xxx 函數設計用於檢查 operands，而不是 operators
    semantic_error_patterns = [
        (r'while\s+.*?ensure_\w+\s*\(\s*operators\s*\)', 'operators passed to operand-checking function'),
        (r'while\s+.*?\<\s*\d+\s*:\s*\n\s+for\s+\w+\s+in\s+range', 'unsafe loop structure'),
    ]
    
    for pattern_str, error_desc in semantic_error_patterns:
        pattern = re.compile(pattern_str, re.MULTILINE | re.DOTALL)
        matches = list(pattern.finditer(refined_code))
        
        if matches:
            print(f"🔧 [Healer V47.6] 偵測到 {len(matches)} 個語義錯誤: {error_desc}")
            
            # 從後往前刪除
            for match in reversed(matches):
                # 計算迴圈範圍並刪除
                start_pos = match.start()
                
                # 尋找整個迴圈體的結束位置
                # 方法：從 while 開始，找到對應的縮排級別
                before_match = refined_code[:start_pos]
                match_indent = len(before_match.split('\n')[-1])
                
                # 從 match.end() 開始逐行掃描
                remaining = refined_code[match.end():]
                lines = remaining.split('\n')
                
                end_line_offset = 0
                for line_idx, line in enumerate(lines):
                    if not line.strip():  # 空行
                        end_line_offset = len('\n'.join(lines[:line_idx+1])) + 1
                        continue
                    
                    current_indent = len(line) - len(line.lstrip())
                    
                    # 如果縮排回到原始級別或更低，迴圈已結束
                    if current_indent <= match_indent:
                        end_line_offset = len('\n'.join(lines[:line_idx]))
                        break
                    
                    end_line_offset = len('\n'.join(lines[:line_idx+1])) + 1
                else:
                    # 到達文件末尾
                    end_line_offset = len(remaining)
                
                # 刪除整個 while 迴圈
                end_pos = match.end() + end_line_offset
                refined_code = refined_code[:start_pos] + refined_code[end_pos:]
                fixes += 1
                print(f"   ✅ 已移除語義錯誤的 while 迴圈: {error_desc}")

    # -----------------------------------------------------------
    # 2.7. [Float/Fraction Consistency] 確保數值類型一致性
    # -----------------------------------------------------------
    # 問題：AI 可能混合使用 float 和 Fraction，導致最終結果是 float
    #      而代碼期望 Fraction 有 .denominator 屬性
    #
    # 症狀：AttributeError: 'float' object has no attribute 'denominator'
    #
    # 解決方案：只修復明確的 float 返回和 float() 調用
    
    # 1. 修復 "return float(...)" -> "return Fraction(...)"
    float_returns = re.findall(
        r'return\s+float\s*\((.*?)\)',
        refined_code
    )
    
    if float_returns:
        print(f"🔧 [Healer V47.7] 修復 {len(float_returns)} 個 float 返回，轉換為 Fraction")
        refined_code = re.sub(
            r'return\s+float\s*\((.*?)\)',
            r'return Fraction(\1)',
            refined_code
        )
        fixes += len(float_returns)
    
    # 2. 更仔細地修復 operand 的 float 賦值
    # 只修復明確的 float(...) 調用，避免誤傷
    float_assignments = re.findall(
        r'(\w+operand\w*)\s*=\s*float\s*\((.*?)\)',
        refined_code
    )
    
    if float_assignments:
        print(f"🔧 [Healer V47.7] 修復 {len(float_assignments)} 個 operand float 轉換")
        refined_code = re.sub(
            r'(\w+operand\w*)\s*=\s*float\s*\((.*?)\)',
            r'\1 = Fraction(\2)',
            refined_code
        )
        fixes += len(float_assignments)


    # -----------------------------------------------------------
    # 3. [Existing Logics] 保留原有的基礎修復
    # -----------------------------------------------------------

    # -----------------------------------------------------------
    # 4. [Eval Eliminator] 智能替換 safe_eval 為直接計算
    # -----------------------------------------------------------
    # 問題：AI 常用 safe_eval(f'{a} {op} {b}')，違反 MASTER_SPEC 禁止 eval 原則
    # 修復：將 safe_eval 調用替換成直接的 Python 運算符
    
    if 'safe_eval(' in refined_code:
        eval_count = 0
        
        # Pattern: safe_eval(f'{var1} {op} {var2}')
        # 替換為: (var1 op var2)
        def replace_safe_eval(match):
            nonlocal eval_count
            full_expr = match.group(0)
            content = match.group(1)  # f'{...}' 的內容
            
            # 從 f-string 中提取所有 {變數名}
            # Pattern: f'{var1} {op} {var2}' -> 提取 [var1, op, var2]
            var_pattern = r'\{(\w+)\}'
            vars_found = re.findall(var_pattern, content)
            
            # 標準的三元組：var1, op, var2
            if len(vars_found) == 3:
                var1, op_var, var2 = vars_found
                eval_count += 1
                # 使用括號確保優先級正確
                return f"({var1} {op_var} {var2})"
            
            # 其他情況（如兩個變數、四個變數等），保持原樣並警告
            print(f"⚠️  [Healer] 無法解析 safe_eval 表達式: {full_expr[:60]}...")
            return full_expr
        
        # 匹配 safe_eval(f'...') 或 safe_eval(f"...")
        refined_code = re.sub(
            r'safe_eval\(([^)]+)\)',
            replace_safe_eval,
            refined_code
        )
        
        if eval_count > 0:
            print(f"🔧 [Healer] 移除 safe_eval 調用，替換為直接計算 ({eval_count} 處)")
            fixes += eval_count

    # [V9.2.2 Fix] 修復 op_latex(...) -> op_latex[...]
    # AI 有時會把字典當函數調用
    if 'op_latex(' in refined_code:
        refined_code, n = re.subn(r'op_latex\(([^\)]+)\)', r'op_latex[\1]', refined_code)
        if n > 0:
            print(f"🔧 [Healer] 修復 op_latex 調用方式: op_latex(...) -> op_latex[...] ({n} 處)")
            fixes += n

    # 移除自創的格式化函式
    forbidden_funcs = ['format_number_for_latex', 'format_num_latex', 'latex_format', '_format_term_with_parentheses']
    for func_name in forbidden_funcs:
        if f'def {func_name}' in refined_code:
            lines = refined_code.split('\n')
            cleaned_lines = []
            skip_mode = False
            target_indent = -1
            
            for line in lines:
                # 偵測函式定義開頭
                if f'def {func_name}' in line:
                    skip_mode = True
                    target_indent = len(line) - len(line.lstrip())
                    fixes += 1
                    continue
                
                if skip_mode:
                    current_indent = len(line) - len(line.lstrip())
                    if not line.strip(): 
                        continue
                    if current_indent > target_indent:
                        continue
                    else:
                        skip_mode = False  # 縮排回來了，結束跳過
                
                cleaned_lines.append(line)
            
            refined_code = '\n'.join(cleaned_lines)
            
    for old_func in forbidden_funcs:
        refined_code, n = re.subn(f'{old_func}\\(', 'fmt_num(', refined_code)
        fixes += n

    # LaTeX 運算符修復
    refined_code, n1 = re.subn(r'(?<=f")([^{"]*?)\\\*([^{"]*?)(?=")', r'\1\\times\2', refined_code)
    refined_code, n2 = re.subn(r'(?<=f")([^{"]*?)\\\/([^{"]*?)(?=")', r'\1\\div\2', refined_code)
    fixes += (n1 + n2)

    # f-string fmt_num 包裹修復
    pattern = r'(f["\'])([^"\']*?)\bfmt_num\(([^)]+)\)([^"\']*?)(["\'])'
    def fix_fmt_num(match):
        prefix, before, var, after, quote = match.groups()
        # 檢查是否已經被 {} 包裹
        if before.strip().endswith('{') and after.strip().startswith('}'):
            return match.group(0)
        return f'{prefix}{before}{{fmt_num({var})}}{after}{quote}'
    
    refined_code, n = re.subn(pattern, fix_fmt_num, refined_code)
    fixes += n

    # random.choice -> safe_choice
    refined_code, n = re.subn(r'\brandom\.choice\s*\(', 'safe_choice(', refined_code)
    fixes += n

    # [V9.2.3 Fix] 修復中文字被錯誤包在 LaTeX $ 內的問題
    # 問題：AI 常生成 q = f'計算 [ $5 \times (-3)$ ] 的值。'
    # 原因：中文字「計算」「的值」在 LaTeX 數學模式內，matplotlib 無法渲染
    # 修復：移除題幹中的所有 $ 符號，讓 clean_latex_output() 重新包裝
    if 'question_text' in refined_code or 'q =' in refined_code:
        # 檢測是否有中文字在 $ 符號附近（高概率有問題）
        if re.search(r'f[\'"][^\'"]*(計算|的值|求|解|判斷)', refined_code):
            print(f"🔧 [Healer] 偵測到題幹可能有 LaTeX 格式問題，正在移除內嵌 $ 符號...")
            
            # 策略：找到題幹賦值語句，移除其中的 $ 符號
            # Pattern: q = f'...$...$...' 或 question_text = f'...$...$...'
            def remove_dollar_in_question(match):
                var_name = match.group(1)  # q 或 question_text
                quote = match.group(2)      # ' 或 "
                content = match.group(3)    # 題幹內容
                
                # 移除所有 $ 符號（clean_latex_output 會重新添加）
                fixed_content = content.replace('$', '')
                
                return f"{var_name} = f{quote}{fixed_content}{quote}"
            
            # 匹配 q = f'...' 或 question_text = f'...'
            original_code = refined_code
            refined_code = re.sub(
                r"(question_text|q)\s*=\s*f(['\"])(.+?)\2",
                remove_dollar_in_question,
                refined_code
            )
            
            if refined_code != original_code:
                fixes += 1
                print(f"🔧 [Healer] 已移除題幣中的 $ 符號，clean_latex_output() 會重新包裝")

    # [V9.2.4 Fix] 檢測內部函數缺少返回值（None unpacking bug）
    # 問題：AI 定義的內部函數在 for 循環後沒有 return，導致返回 None
    # 例如：def helper(...): for i in range(1000): ... return value  ← 如果循環完沒找到，返回 None
    if 'def ' in refined_code and 'for _safety_loop_var in range' in refined_code:
        # 檢測內部函數定義
        inner_func_pattern = r'(    def \w+\([^)]*\):.*?)(    \w+|def generate)'
        matches = list(re.finditer(inner_func_pattern, refined_code, re.DOTALL))
        
        for match in matches:
            func_body = match.group(1)
            func_name_match = re.search(r'def (\w+)\(', func_body)
            if not func_name_match:
                continue
                
            func_name = func_name_match.group(1)
            
            # 檢查是否在 for 循環後缺少返回值
            if 'for _safety_loop_var in range' in func_body:
                # 檢查最後一行是否有 return（排除循環內的 return）
                lines = func_body.strip().split('\n')
                last_non_empty_line = ''
                indent_count = 0
                for line in reversed(lines):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#'):
                        indent = len(line) - len(line.lstrip())
                        # 找到函數定義層級的最後一行
                        if indent == 4:  # 函數體的縮排
                            last_non_empty_line = stripped
                            indent_count = indent
                            break
                
                # 如果最後一行不是 return，添加默認返回
                if last_non_empty_line and not last_non_empty_line.startswith('return'):
                    print(f"🔧 [Healer] 偵測到內部函數 '{func_name}' 可能缺少默認返回值，正在添加...")
                    
                    # 在函數末尾添加默認返回None（或合適的值）
                    # 策略：在函數體最後添加 return (0, 0) 或 return None
                    func_indent = '    '  # 內部函數縮排
                    default_return = f"{func_indent}return (0, 0)  # [Auto-Fixed] 默認返回值（避免 None unpacking）\n"
                    
                    # 找到函數結束位置（下一個 def 或函數體減少縮排的位置）
                    func_start = refined_code.find(func_body)
                    if func_start != -1:
                        func_end = func_start + len(func_body)
                        # 在函數結尾前插入默認返回
                        refined_code = refined_code[:func_end] + default_return + refined_code[func_end:]
                        fixes += 1

    return refined_code, fixes

def fix_code_syntax(code_str, error_msg=""):
    """
    [V45.6 Syntax Emergency Room + Orthopedic Surgeon]
    1. Regex 修復語法錯誤 (Latex, Break, Op-var)。
    2. [NEW] Auto-Indenter: 自動矯正 IndentationError。
    """
    # --- Part 1: Regex Healers ---
    fixed_code = code_str.replace("，", ", ").replace("：", ": ")
    fixed_code = re.sub(r'###.*?\n', '', fixed_code) 
    
    total_fixes = 0
    def apply_fix(pattern, replacement, code):
        new_code, count = re.subn(pattern, replacement, code, flags=re.MULTILINE)
        return new_code, count

    # 1. Latex Fixes
    fixed_code, c = apply_fix(r'(?<!\\)\\ ', r'\\\\ ', fixed_code); total_fixes += c
    fixed_code, c = apply_fix(r'(?<!\\)\\u(?![0-9a-fA-F]{4})', r'\\\\u', fixed_code); total_fixes += c

    # 2. Tuple Unpacking Fix (Missing Comma)
    # [V45.3 Fix] 排除 Python 關鍵字，避免誤將 `continue\nvar =` 轉成 `continue, var =`
    # 原 pattern 會把跨行的 continue/expression = 誤判為 tuple unpacking
    unpacking_pattern = r'^(\s*(?!break|continue|return|pass|raise|yield)[a-zA-Z_]\w*)\s+([a-zA-Z_]\w*)\s*=(?!=)'
    fixed_code, c = re.subn(unpacking_pattern, r'\1, \2 =', fixed_code, flags=re.MULTILINE)
    total_fixes += c

    # 3. [Fix] "break, var = val" Hallucination
    # 改良策略：不嘗試猜縮排，直接用 ; 接在同一行 (Python 允許)
    # var = val; break
    # [V45.1 Fix] 使用 [ \t]* 取代 \s*，確保 pattern 必須在同一行匹配（\s 會跨越換行符）
    break_pattern = r'^[ \t]*break[ \t]*,[ \t]*([a-zA-Z_]\w*)[ \t]*=[ \t]*(.+)$'
    fixed_code, c = re.subn(break_pattern, r'\1 = \2; break', fixed_code, flags=re.MULTILINE)
    if c > 0: print(f"🚑 [Syntax Healer] 修復了 {c} 處 break 賦值幻覺 (使用分號策略)")
    total_fixes += c

    # 4. [Fix] "Variable as Operator" (a op b)
    op_vars = r'(?:op\d+|current_op|Op_\w+)'
    
    # Pattern A: 括號內的運算
    pattern_inner = rf'\(([\w\.]+)\s+({op_vars})\s+([\w\.]+)\)'
    for _ in range(3): 
        fixed_code, c = re.subn(pattern_inner, r'safe_eval(f"{ \1 } { \2 } { \3 }")', fixed_code)
        total_fixes += c

    # Pattern B: 賦值語句
    pattern_assign = rf'=\s*(.+?)\s+({op_vars})\s+([\w\.]+)\s*$'
    def assign_replacer(match):
        left = match.group(1)
        op = match.group(2)
        right = match.group(3)
        return f'= safe_eval(f"""{{ {left} }} {{ {op} }} {{ {right} }}""")'

    fixed_code, c = re.subn(pattern_assign, assign_replacer, fixed_code, flags=re.MULTILINE)
    if c > 0: print(f"🚑 [Syntax Healer] 修復了 {c} 處運算符變數語法")
    total_fixes += c
    
    # 5. f-string braces
    def fix_latex_braces(match):
        content = match.group(1)
        if not (re.search(r'\\[a-zA-Z]+', content) and not re.search(r'^\\n', content)):
            return f'f"{content}"'
        pattern = r'(\{[a-zA-Z_][a-zA-Z0-9_]*(\(.*\))?\})|(\{)|(\})'
        def token_sub(m):
            if m.group(1): return m.group(1) 
            if m.group(3): return "{{"        
            if m.group(4): return "}}"        
            return m.group(0)
        new_content = re.sub(pattern, token_sub, content)
        return f'f"{new_content}"'

    fixed_code, c = re.subn(r'f"(.*?)"', fix_latex_braces, fixed_code); total_fixes += c

    # --- Part 2: Auto-Indenter (The Orthopedic Surgeon) ---
    # 這是專門用來修復 IndentationError 的邏輯
    lines = fixed_code.split('\n')
    indented_lines = []
    prev_line_ends_colon = False
    prev_indent = 0
    
    for line in lines:
        stripped = line.strip()
        # 忽略空行
        if not stripped:
            indented_lines.append(line)
            continue
            
        current_indent = len(line) - len(line.lstrip())
        
        # 如果上一行是冒號結尾 (if/for/while/def)，這一行必須縮排
        if prev_line_ends_colon:
            if current_indent <= prev_indent:
                # 偵測到縮排錯誤！強制縮排
                new_indent = prev_indent + 4 # 補 4 個空白
                fixed_line = " " * new_indent + line.lstrip()
                indented_lines.append(fixed_line)
                
                # 更新狀態 (假設修好了，這行就不是冒號結尾了，除非它自己也是)
                # 但要注意這行可能也是冒號結尾 (巢狀結構)
                # 這裡簡單處理：既然我們強制縮排了，我們信任這個新縮排
                prev_indent = new_indent 
            else:
                indented_lines.append(line)
                prev_indent = current_indent
        else:
            indented_lines.append(line)
            prev_indent = current_indent
            
        # 檢查這一行是否以冒號結尾 (忽略註解)
        # 用 split('#')[0] 去掉註解
        code_part = stripped.split('#')[0].rstrip()
        if code_part.endswith(':'):
            prev_line_ends_colon = True
        else:
            prev_line_ends_colon = False
            
    fixed_code = '\n'.join(indented_lines)

    return fixed_code, total_fixes

def fix_code_via_ast(code_str):
    """
    使用 AST Transformer 進行邏輯手術
    [V9.2.1 Performance Fix] 添加預檢查，避免不必要的 AST 解析
    """
    # ✅ 預檢查：如果不包含需要修復的關鍵字，直接跳過
    # 這可以節省 5-10% 的執行時間（在乾淨代碼情況下）
    keywords_need_ast = ['eval', 'exec', 'while True', '^', 'import ', '    def ']  # ✅ 添加内部函数检测
    if not any(kw in code_str for kw in keywords_need_ast):
        # print("⚡ [AST Healer] 預檢查通過，跳過 AST 解析")
        return code_str, 0
    
    try:
        tree = ast.parse(code_str)
        healer = ASTHealer()
        new_tree = healer.visit(tree)
        ast.fix_missing_locations(new_tree)  # 修正行號
        
        # 轉回程式碼
        new_code = ast.unparse(new_tree)
        return new_code, healer.fixes
    except Exception as e:
        # 如果 AST 解析本身就失敗（代表語法爛到無法解析），則放棄治療，交給原流程
        print(f"AST Healing Failed: {e}")
        return code_str, 0

def validate_python_code(code_str):
    try:
        # [V46.1 Fix] 修正 Host 端 NameError
        # 我們不需要手動傳入 safe_eval，因為 code_str (生成的代碼)
        # 裡面已經透過 PERFECT_UTILS 注入了 safe_eval 的定義。
        # exec 執行時會自然地先定義函式，再執行後面的邏輯。
        
        exec(code_str, {
            'Fraction': Fraction, 
            'random': random, 
            'math': math, 
            're': re,
            'ast': ast,
            'operator': operator
        })
        return True, "Success"
    except Exception as e:
        # [Debug] 詳細錯誤輸出
        error_msg = f"{type(e).__name__}: {str(e)}"
        
        # 過濾掉一些非代碼邏輯的干擾訊息
        if "break outside loop" in error_msg:
             return False, error_msg

        print(f"❌ [Validation Failed] 執行時錯誤: {error_msg}")
        
        if "local variable" in error_msg and "referenced before assignment" in error_msg:
            print(f"   💡 提示: 這可能是因為 while True 熔斷後，迴圈內變數未初始化導致。")
        elif "safe_eval" in error_msg:
             print(f"   💡 提示: 請檢查生成的代碼開頭是否包含 PERFECT_UTILS 定義。")
             
        return False, error_msg

def log_experiment(skill_id, start_time, prompt_len, code_len, is_valid, error_msg, repaired, model_name, actual_provider=None, **kwargs):
    """實驗數據記錄"""
    duration = time.time() - start_time
    # [V47.9 Fix] 設置 UTF-8 編碼以支持中文
    conn = sqlite3.connect(Config.db_path)
    conn.execute("PRAGMA encoding='UTF-8'")
    c = conn.cursor()
    query = """
    INSERT INTO experiment_log (
        skill_id, start_time, duration_seconds, prompt_len, code_len, 
        is_success, error_msg, repaired, model_name, 
        model_size_class, prompt_level, raw_response, final_code,
        score_syntax, score_math, score_visual, healing_duration, 
        is_executable, ablation_id, missing_imports_fixed, resource_cleanup_flag,
        prompt_tokens, completion_tokens, total_tokens,
        experiment_group, garbage_cleaner_count, eval_eliminator_count,
        sampling_success_count, sampling_total_count, spec_prompt_id, use_master_spec
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    # [V47.10 Fix] 確保所有字符串參數使用 UTF-8 編碼
    def safe_utf8(val):
        if isinstance(val, str):
            return val.encode('utf-8', errors='replace').decode('utf-8')
        return val
    
    params = (
        skill_id, start_time, duration, prompt_len, code_len,
        1 if is_valid else 0, safe_utf8(str(error_msg)), 1 if repaired else 0, safe_utf8(model_name),
        safe_utf8(kwargs.get('model_size_class', 'Unknown')),
        safe_utf8(kwargs.get('prompt_level', 'Bare')),
        safe_utf8(kwargs.get('raw_response', '')),
        safe_utf8(kwargs.get('final_code', '')),
        kwargs.get('score_syntax', 0.0),
        kwargs.get('score_math', 0.0),
        kwargs.get('score_visual', 0.0),
        kwargs.get('healing_duration', 0.0),
        kwargs.get('is_executable', 1 if is_valid else 0),
        kwargs.get('ablation_id', 1),
        safe_utf8(kwargs.get('missing_imports_fixed', '')),
        1 if kwargs.get('resource_cleanup_flag') else 0,
        kwargs.get('prompt_tokens', 0),
        kwargs.get('completion_tokens', 0),
        kwargs.get('total_tokens', 0),
        # [旺宏科學獎 3×3 設計專用欄位]
        kwargs.get('experiment_group', None),
        kwargs.get('garbage_cleaner_count', 0),
        kwargs.get('eval_eliminator_count', 0),
        kwargs.get('sampling_success_count', 0),
        kwargs.get('sampling_total_count', 0),
        kwargs.get('spec_prompt_id', None),
        1 if kwargs.get('use_master_spec') else 0
    )
    try:
        c.execute(query, params)
        conn.commit()
    except Exception as e:
        print(f"❌ Database Log Error: {e}")
    finally:
        conn.close()

# ==============================================================================
# 5. 核心生成函式 (V44.9 Main Engine - Hybrid-Healing)
# ==============================================================================
def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    start_time = time.time()
    role_config = Config.MODEL_ROLES.get('coder', {'provider': 'google', 'model': 'gemini-1.5-flash'})
    current_model = role_config.get('model', 'Unknown')
    ablation_id = kwargs.get('ablation_id', 3)
    
    # [Research Fix] 讀取 Ablation 設定
    from models import AblationSetting
    ablation_config = AblationSetting.query.get(ablation_id)
    # Ab1, Ab2: 無 Healer; Ab3: 完整 Healer (Regex + AST)
    use_regex_healer = ablation_config.use_regex if ablation_config else (ablation_id >= 3)
    use_ast_healer = ablation_config.use_ast if ablation_config else (ablation_id >= 3)
    
    # [Ablation Study] 支援自定義輸出路徑
    custom_output_path = kwargs.get('custom_output_path', None)
    
    print(f"\n{'='*70}")
    print(f"🧪 [Ablation {ablation_id}] {ablation_config.name if ablation_config else 'Unknown'}")
    print(f"   Regex Healer: {'✅ Enabled' if use_regex_healer else '❌ Disabled'}")
    print(f"   AST Healer:   {'✅ Enabled' if use_ast_healer else '❌ Disabled'}")
    if custom_output_path:
        print(f"   Output: {os.path.basename(custom_output_path)}")
    print(f"{'='*70}\n")
    
    # 1. 讀取 Spec (從資料庫)
    active_prompt = SkillGenCodePrompt.query.filter_by(skill_id=skill_id, prompt_type="MASTER_SPEC").order_by(SkillGenCodePrompt.created_at.desc()).first()
    db_master_spec = active_prompt.prompt_content if active_prompt else "生成一題簡單的整數四則運算。"
    
    # 2. [Research Fix] 根據 ablation_id 選擇 Prompt 策略
    if ablation_id == 1:
        # Ab1 (Bare): 最簡 Prompt + MASTER_SPEC，無 Healer
        prompt = BARE_MINIMAL_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
        print(f"📝 [Prompt] Ab1 - BARE_MINIMAL_PROMPT")
        print(f"   📝 Bare Prompt: {len(BARE_MINIMAL_PROMPT)} chars")
        print(f"   📄 MASTER_SPEC: {len(db_master_spec)} chars")
        print(f"   ⚠️  無工程化指導，無 Healer")
    elif ablation_id == 2:
        # Ab2 = 完整工程化 Prompt + MASTER_SPEC，無 Healer（測試提示工程價值）
        prompt = UNIVERSAL_GEN_CODE_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
        print(f"📝 [Prompt] Ab2 - UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC")
        print(f"   📝 Universal Prompt: {len(UNIVERSAL_GEN_CODE_PROMPT)} chars")
        print(f"   📄 MASTER_SPEC: {len(db_master_spec)} chars")
        print(f"   ⚠️  無 Healer（測試提示工程的貢獻）")
    else:
        # Ab3 = 完整工程化 Prompt + MASTER_SPEC + 完整 Healer (Regex + AST)
        prompt = UNIVERSAL_GEN_CODE_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
        print(f"📝 [Prompt] Ab{ablation_id} - UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC")
        print(f"   📝 Universal Prompt: {len(UNIVERSAL_GEN_CODE_PROMPT)} chars")
        print(f"   📄 MASTER_SPEC: {len(db_master_spec)} chars")
        print(f"   ✅ 完整 Healer (Regex + AST)")
    
    raw_output = ""
    prompt_tokens, completion_tokens = 0, 0

    try:
        # 3. 呼叫 AI
        client = get_ai_client(role='coder') 
        response = client.generate_content(prompt)
        raw_output = response.text
        
        # 4. Token 統計
        try:
            if hasattr(response, 'usage_metadata'): 
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count
            elif hasattr(response, 'usage'): 
                u = response.usage
                prompt_tokens = getattr(u, 'prompt_tokens', 0)
                completion_tokens = getattr(u, 'completion_tokens', 0)
        except: pass

        # 5. 清洗與組裝 (Strict Pipeline Order)
        regex_fixes = 0
        ast_fixes = 0
        markdown_cleanup_count = 0  # 獨立計數：Markdown 預處理清洗
        
        # [CRITICAL] 無條件清洗：移除 Markdown 代碼塊標記
        # 這必須在 Healer 判斷之前執行，以確保 Ab1/Ab2/Ab3 都會被清掉
        # 否則 Ab1/Ab2 會有 ```python 和 ``` 標記，導致代碼無法執行
        raw_output = raw_output.strip()
        markdown_before = raw_output
        raw_output = re.sub(r'^(\s*)```python\s*\n', '', raw_output, flags=re.MULTILINE)
        raw_output = re.sub(r'\n(\s*)```\s*$', '', raw_output, flags=re.MULTILINE)
        raw_output = re.sub(r'\n\s*```\s*\n', '\n', raw_output)
        
        # 檢查是否有清洗
        if markdown_before != raw_output:
            markdown_cleanup_count = 1
            print(f"🧹 [{skill_id}] Markdown 預處理: 移除代碼塊標記")
        
        # [Research Fix] 基礎清理也是 Healer 的一部分
        # Ab1/Ab2: 完全不做清理，Ab3: 執行完整 Healer（基礎清理 + Regex + AST）
        if use_regex_healer:
            # Step A: 移除 Markdown - 提取代碼塊內容
            # [CRITICAL FIX] 由於無條件清理已經移除了 Markdown 塊標記，
            # 這裡的 regex 可能找不到原始 ```python 標記
            # 因此直接使用已清理的 raw_output 即可
            match = COMPILED_PATTERNS['markdown_blocks'].search(raw_output)
            if match:
                # 提取第一個代碼塊的內容
                clean_code = match.group(1).strip()
                # 注意：Markdown 清理已經計在 markdown_cleanup_count 中了
                # 這裡不重複計算
            else:
                # 沒有 Markdown 塊（或已被無條件清理移除），直接使用當前輸出
                clean_code = raw_output.strip()

            # Step B: 清洗特殊空格 (MUST DO BEFORE IMPORT CLEANING)
            # [旺宏科學獎] Garbage Cleaner 獨立計數
            garbage_cleaner_count = 0
            original_len = len(clean_code)
            clean_code = clean_code.replace('\xa0', ' ').replace('　', ' ').strip()
            if len(clean_code) != original_len:
                garbage_cleaner_count = 1
                regex_fixes += 1

            # Step C: 移除重複 Import (優化版)
            clean_code, import_removed, removed_list = clean_redundant_imports(clean_code)
            regex_fixes += import_removed
            
            # Step D: 包裹函式與縮排修復
            if "def generate" not in clean_code:
                indent_str = '    '  # Standard 4 spaces
                clean_code = "def generate(level=1, **kwargs):\n" + textwrap.indent(clean_code, indent_str)
                
                if "return" not in clean_code:
                    clean_code += "\n    return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}"
                regex_fixes += 1
        else:
            # Ab1/Ab2: 不做任何清理，直接使用 LLM 原始輸出
            clean_code = raw_output
            garbage_cleaner_count = 0
            removed_list = []
            print(f"⏭️  [{skill_id}] 基礎清理 SKIPPED (ablation_id={ablation_id}, 無 Healer)")

        # Step E: [NEW] 主動邏輯修復 (Healer)
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        if use_regex_healer:
            clean_code, healer_fixes = refine_ai_code(clean_code)
            regex_fixes += healer_fixes
        else:
            print(f"⏭️  [{skill_id}] Regex Healer SKIPPED (ablation_id={ablation_id})")

        # ========================================
        # Step E.5: [OPTIMIZED V9.2.1] 統一函數移除器
        # ========================================
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        if use_regex_healer:
            # 合併原本的三處函數清洗邏輯，避免重複掃描
            
            # 建立完整的禁止函數清單
            PROTECTED_TOOLS = [
                'fmt_num', 'to_latex', 'is_prime', 'gcd', 'lcm', 'get_factors', 'check',
                'clamp_fraction', 'safe_pow', 'factorial_bounded', 'nCr', 'nPr',
                'rational_gauss_solve', 'normalize_angle',
                'fmt_set', 'fmt_interval', 'fmt_vec',
                'format_number_for_latex', 'format_num_latex', 'latex_format',
                '_format_term_with_parentheses', 'clean_expression'
            ]
            
            # ✅ 一次性移除所有禁止的函數定義
            if 'def generate' in clean_code:
                gen_start = clean_code.find('def generate')
                gen_content = clean_code[gen_start:]
                
                gen_content, shadowing_fixes = remove_forbidden_functions_unified(
                    gen_content, 
                    PROTECTED_TOOLS
                )
                
                clean_code = clean_code[:gen_start] + gen_content
                regex_fixes += shadowing_fixes

        # ========================================
        # Step E.6: [NEW] 混合數字串修復
        # ========================================
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        if use_regex_healer:
            mixed_num_fixes = 0

            # Pattern 1: 偵測並修復 f"{A}{fmt_num(frac)}" 模式
            pattern1 = r'return\s+f"(\{[^}]+\})\{fmt_num\(([^)]+)\)\}"'
            if re.search(pattern1, clean_code):
                print(f"🔴 [{skill_id}] CRITICAL: 偵測到混合數字串拼接")
                # 修復：改為回傳 Fraction 相加
                clean_code = re.sub(
                    pattern1,
                    r'return Fraction(\1) + \2',
                    clean_code
                )
                mixed_num_fixes += 1

            # Pattern 2: 偵測 eval(字串) 用於混合數
            if re.search(r'elif isinstance\([^,]+, str\):\s+return eval\(', clean_code):
                print(f"⚠️ [{skill_id}] 偵測到 eval(字串)，可能導致混合數錯誤")

            # Pattern 3: 修復 _generate_mixed_number 的實作
            mixed_num_pattern = r'(def _generate_mixed_number\(\):.*?)(return f".*?fmt_num.*?")'
            if re.search(mixed_num_pattern, clean_code, re.DOTALL):
                print(f"🔧 [{skill_id}] 修復 _generate_mixed_number")
                clean_code = re.sub(
                    r'(def _generate_mixed_number\(\):.*?frac = [^\n]+\n\s+)return f".*?fmt_num.*?"',
                    r'\1return Fraction(A) + frac',
                    clean_code,
                    flags=re.DOTALL
                )
                mixed_num_fixes += 1

            regex_fixes += mixed_num_fixes

        # ========================================
        # Step E.7: LaTeX 格式修復（混合數專用）
        # ========================================
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        if use_regex_healer:
            latex_fixes = 0

            # 修復 1：過多的大括號 {{{{num}}}} (使用預編譯 pattern)
            clean_code, n = COMPILED_PATTERNS['excess_braces'].subn(r'{\1}', clean_code)
            latex_fixes += n

            # 修復 2：TO_LATEX 內部包含 $ 符號
            if 'return f"$' in clean_code and 'def TO_LATEX' in clean_code:
                print(f"⚠️ [{skill_id}] TO_LATEX 內部不應包含 $ 符號")
                clean_code = re.sub(r'return f"\$([^"]+)\$"', r'return f"\1"', clean_code)
                latex_fixes += 1

            # 修復 3：整數除法應改為普通除法
            clean_code, n = re.subn(
                r'(\w+)\s*=\s*(\w+)\s*//\s*(\w+)(?=.*# Division)',
                r'\1 = \2 / \3',
                clean_code
            )
            latex_fixes += n

            regex_fixes += latex_fixes

        # ========================================
        # Step E.9: [V47.0] Return 語句修正
        # ========================================
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        if use_regex_healer:
            return_fixes = 0

            # Fix 1: 修正 fmt_num(字串變數) 的錯誤用法
            if "'question_text': fmt_num(" in clean_code:
                pattern = r"'question_text':\s*fmt_num\(([a-zA-Z_]\w*)\)"
                matches = list(re.finditer(pattern, clean_code))
                
                for match in reversed(matches):
                    var_name = match.group(1)
                    # 判斷是否為字串變數
                    if any(kw in var_name.lower() for kw in ['latex', 'question', 'q', 'text', 'str']):
                        new_str = f"'question_text': clean_latex_output({var_name})"
                        clean_code = clean_code[:match.start()] + new_str + clean_code[match.end():]
                        return_fixes += 1
                        print(f"🔧 [{skill_id}] 修正: fmt_num({var_name}) → clean_latex_output({var_name})")

            regex_fixes += return_fixes

        # ========================================
        # Step E.8: [NEW] 變數名稱對齊與雙重 $ 修復
        # ========================================
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        if use_regex_healer:
            var_fixes = 0
            
            # Fix 1: 如果 AI 用了 'a' 但實際變數叫 'answer'
            # 檢查：有 'answer =' 但沒有 'a =' 定義
            has_answer_def = re.search(r'\banswer\s*=', clean_code)
            has_a_def = re.search(r'\ba\s*=\s*(?!answer)', clean_code)  # a = 但不是 a = answer
            has_a_usage = 'isinstance(a, str)' in clean_code or "'a'" in clean_code
            
            if has_answer_def and not has_a_def and has_a_usage:
                # 替換所有 'a' 引用為 'answer'
                clean_code = clean_code.replace('isinstance(a, str)', 'isinstance(answer, str)')
                clean_code = re.sub(r"'='\s+in\s+a\b", "'=' in answer", clean_code)
                clean_code = re.sub(r'"="\s+in\s+a\b', '"=" in answer', clean_code)
                clean_code = re.sub(r'\ba\.split\(', 'answer.split(', clean_code)
                # 同時處理 return 中的 'answer': a
                clean_code = re.sub(r"'answer':\s*a\b", "'answer': answer", clean_code)
                clean_code = re.sub(r"'correct_answer':\s*a\b", "'correct_answer': answer", clean_code)
                var_fixes += 1
                print(f"🔧 [{skill_id}] 修復變數名稱: a -> answer")
            
            # Fix 2: 防止 return 中雙重 $ 包裹 (終極版 V46.8)
            # 當 clean_latex_output() 已經處理過 q，return 中不需要再包 $
            if "clean_latex_output" in clean_code:
                old_len = len(clean_code)
                
                # Pattern 1: 直接在 return 中用 f'${q}$' 的各種形式
                clean_code = re.sub(
                    r"'question_text':\s*f?['\"]?\$\{q\}\$['\"]?",
                    r"'question_text': q",
                    clean_code
                )
                
                # Pattern 2: 在 clean_latex_output 之前就加了 $ 的情況
                clean_code = re.sub(
                    r'q\s*=\s*f?["\']?\$\{[^}]+\}\$["\']?\s*\n\s*q\s*=\s*clean_latex_output\(q\)',
                    r'q = clean_latex_output(q)',
                    clean_code
                )
                
                # Pattern 3: 已經有 clean_latex_output 但 return 仍包 $
                clean_code = re.sub(
                    r"'question_text':\s*f\['\"]\$\{q\}\$['\"]\b",
                    r"'question_text': q",
                    clean_code
                )
                
                # Pattern 4: [V46.8 NEW] 通用 f-string 形式 f'${q}$' → q
                clean_code = re.sub(
                    r"f['\"]?\$\{q\}\$['\"]?",
                    r"q",
                    clean_code
                )
                
                if len(clean_code) != old_len:
                    var_fixes += 1
                    print(f"🔧 [{skill_id}] 移除雙重 $ 包裹 (終極版)")
            
            regex_fixes += var_fixes

        # ========================================
        # Step E.9: [V47.4 優化] Return 語句自動 LaTeX 清洗（僅對 q）
        # ========================================
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        if use_regex_healer:
            return_fixes = 0
            
            if "'question_text':" in clean_code:
                # 檢查前面是否已經有 q = clean_latex_output(q)
                already_clean_q = re.search(r'\bq\s*=\s*clean_latex_output\s*\(\s*q\s*\)', clean_code)
                
                # 僅對 'q' 自動包裝；若前面已清洗過則維持 'q'
                if already_clean_q:
                    # 已清洗過，不需要再包裝
                    pass
                else:
                    # 未清洗，在 return 時包裝
                    old_pattern = r"'question_text':\s*q\b"
                    new_str = "'question_text': clean_latex_output(q)"
                    clean_code, n = re.subn(old_pattern, new_str, clean_code)
                    return_fixes = n
                    if return_fixes > 0:
                        print(f"🔧 [{skill_id}] 在 return 中包裹 clean_latex_output(q) ({return_fixes} 處)")
            
            # ❌ 已在前面累加過，此處不重複累加
            # regex_fixes += return_fixes

        # ========================================
        # Step F.5: [NEW V46.8] Pre-AST 語法清洗
        # ========================================
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        if use_regex_healer:
            pre_ast_fixes = 0

            # Fix 1: 修復 eval(calc_string) → safe_eval(calc_string)
            # [旺宏科學獎] Eval Eliminator 獨立計數
            eval_eliminator_count = 0
            clean_code, n = re.subn(
                r'\beval\s*\(',
                r'safe_eval(',
                clean_code
            )
            eval_eliminator_count = n
            pre_ast_fixes += n
            if n > 0:
                print(f"🔧 [{skill_id}] 轉換 eval() → safe_eval() ({n} 處)")

            # Fix 2: 修復可能的語法錯誤（多餘的括號、引號）
            # 檢查是否有未閉合的字串
            open_quotes = clean_code.count('"') % 2
            if open_quotes != 0:
                print(f"⚠️ [{skill_id}] 偵測到未閉合的引號")
                # 嘗試自動閉合（在最後一個 return 之前）
                lines = clean_code.split('\n')
                for i in range(len(lines) - 1, -1, -1):
                    if 'return' in lines[i]:
                        if not lines[i].rstrip().endswith('"'):
                            lines[i] = lines[i].rstrip() + '"'
                            pre_ast_fixes += 1
                        break
                clean_code = '\n'.join(lines)

            regex_fixes += pre_ast_fixes
        else:
            eval_eliminator_count = 0
            print(f"⏭️  [{skill_id}] Pre-AST 清洗 SKIPPED (ablation_id={ablation_id})")

        # Step F: 基礎語法修復
        # [Research Fix] 僅在 use_regex_healer=True 時執行
        healing_start = time.time()
        if use_regex_healer:
            clean_code, r_fixes = fix_code_syntax(clean_code)
            regex_fixes += r_fixes
        else:
            r_fixes = 0
            print(f"⏭️  [{skill_id}] 基礎語法修復 SKIPPED (ablation_id={ablation_id})")

        # ========================================
        # 6.5. 通用語法修復（適用所有領域）
        # [Research Fix] 僅在 use_regex_healer=True 時執行，以確保純淨的 AB1/AB2 實驗
        # ========================================
        qwen_fixes = 0
        
        if use_regex_healer:
            # A0. [新增] 移除 Markdown 代碼塊標記（LLM 幻覺）
            # 問題：LLM 可能在開頭輸出 ```python，結尾輸出 ```
            # 修復：自動移除這些標記
            
            # 移除開頭的 ```python 或 ``` 
            clean_code, n = re.subn(r'^(\s*)```python\s*\n', '', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] Markdown 清理: 移除開頭的 ```python ({n} 處)")
            
            # 移除結尾的 ``` 
            clean_code, n = re.subn(r'\n(\s*)```\s*$', '', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] Markdown 清理: 移除結尾的 ``` ({n} 處)")
            
            # 移除多餘的 Markdown 代碼塊標記（中間出現的）
            clean_code, n = re.subn(r'\n\s*```\s*\n', '\n', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] Markdown 清理: 移除中間的 ``` ({n} 處)")
            
            # A. 移除自創工具函式（通用 pattern）
            forbidden_funcs = ['format_number_for_latex', 'format_num', 'latex_format']
            for func_name in forbidden_funcs:
                if f'def {func_name}' in clean_code:
                    lines = clean_code.split('\n')
                    cleaned_lines = []
                    skip_mode = False
                    indent_level = 0
                    
                    for line in lines:
                        if f'def {func_name}' in line:
                            skip_mode = True
                            indent_level = len(line) - len(line.lstrip())
                            continue
                        
                        if skip_mode:
                            current_indent = len(line) - len(line.lstrip())
                            if not line.strip() or line.strip().startswith('#'):
                                continue
                            if current_indent <= indent_level and line.strip():
                                skip_mode = False
                            else:
                                continue
                        
                        cleaned_lines.append(line)
                    
                    clean_code = '\n'.join(cleaned_lines)
                    qwen_fixes += 1

            # B. 替換自創函式為標準工具（通用替換）
            for old_func in forbidden_funcs:
                clean_code, n = re.subn(f'{old_func}\\(', 'fmt_num(', clean_code)
                qwen_fixes += n

            # B.1 修復 LaTeX 運算符錯誤 (使用預編譯 pattern)
            clean_code, n = COMPILED_PATTERNS['latex_asterisk'].subn(r'\\times', clean_code)
            qwen_fixes += n
            clean_code, n = COMPILED_PATTERNS['latex_slash'].subn(r'\\div', clean_code)
            qwen_fixes += n

            # B.2 偵測危險的 f-string 反斜線插入樣式
            b_fstring_issue = re.search(r'f["\'].*\\\{', clean_code)
            fstring_problem_detected = bool(b_fstring_issue)

            # C. 修復 Python 3 語法錯誤 (使用預編譯 pattern)
            clean_code, n = COMPILED_PATTERNS['range_concat'].subn(
                r'list(range(\1)) + list(range(\2))',
                clean_code
            )
            qwen_fixes += n

            # E. 偵測 op_latex[...] 用法但無定義，自動注入
            needs_op_map = COMPILED_PATTERNS['op_latex_usage'].search(clean_code) and 'op_latex =' not in clean_code
            if needs_op_map:
                clean_code = re.sub(
                    r'(def\s+generate\s*\([^)]*\):\n)',
                    r"\1    op_latex = {'+': '+', '-': '-', '*': '\\\\times', '/': '\\\\div'}\n",
                    clean_code,
                    count=1
                )
                qwen_fixes += 1
                print(f"🔧 [{skill_id}] 自動注入 op_latex 映射表")
            
            # [V45.2 Fix] 移除函數內部的重複 op_latex 定義
            local_op_latex_pattern = r'^([ \t]+)op_latex\s*=\s*\{[^}]+\}\s*\n'
            local_op_matches = list(re.finditer(local_op_latex_pattern, clean_code, re.MULTILINE))
            if local_op_matches:
                for match in reversed(local_op_matches):
                    indent = len(match.group(1))
                    if indent >= 8:
                        clean_code = clean_code[:match.start()] + clean_code[match.end():]
                        qwen_fixes += 1
                        print(f"🔧 [{skill_id}] 移除內部重複 op_latex 定義 (縮排 {indent})")
            
            # F-Zero. [V45.4 Fix] 幻覺函數修復 (Hallucination Healer)
            # 1. fmt_neg_paren -> fmt_num (使用預編譯 pattern)
            clean_code, n = COMPILED_PATTERNS['fmt_neg_paren'].subn('fmt_num(', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 幻覺修復: fmt_neg_paren -> fmt_num ({n} 處)")

            # 2. fmt_num(..., type='...') -> fmt_num(...) 移除 type 參數
            clean_code, n = COMPILED_PATTERNS['fmt_num_type_param'].subn('', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 幻覺修復: 移除 fmt_num 的 type 參數 ({n} 處)")

            # 3. 注入缺失的 random 工具
            hallucination_utils = ""
            
            if 'random_fraction(' in clean_code and 'def random_fraction' not in clean_code:
                hallucination_utils += """
    def random_fraction(min_v, max_v, min_den=2, max_den=10, *args):
        # [Auto-Injected Helper]
        num = random.randint(min_v, max_v)
        den = random.randint(min_den, max_den)
        return Fraction(num, den) if den != 0 else Fraction(num, 1)
"""
                qwen_fixes += 1
                print(f"🔧 [{skill_id}] 自動注入 random_fraction 輔助函式")

            if 'random_mixed_number(' in clean_code and 'def random_mixed_number' not in clean_code:
                hallucination_utils += """
    def random_mixed_number(min_whole, max_whole, min_num, max_num, min_den, max_den):
        # [Auto-Injected Helper]
        w = random.randint(min_whole, max_whole)
        n = random.randint(min_num, max_num)
        d = random.randint(min_den, max_den)
        if d == 0: d = 1
        return Fraction(w * d + n, d)
"""
                qwen_fixes += 1
                print(f"🔧 [{skill_id}] 自動注入 random_mixed_number 輔助函式")

            if hallucination_utils:
                clean_code = re.sub(
                    r'(def\s+generate\s*\([^)]*\):\n)',
                    r'\1' + hallucination_utils,
                    clean_code,
                    count=1
                )

            # F. Healer 熱修補：題幹強制使用 fmt_num，修復雙括號與缺 f-string
            # F.1 強制題幹使用 fmt_num：將所有 to_latex(...) 改為 fmt_num(...)
            clean_code, n = re.subn(r'\bto_latex\s*\(', 'fmt_num(', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 題幹格式修復: to_latex(...) → fmt_num(...) ({n} 處)")
            
            # F.2 修復 f-string 內雙大括號包 op_latex 的情況
            clean_code, n = re.subn(r'\{\{op_latex\[(.+?)\]\}\}', r'{op_latex[\1]}', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] f-string 修復: {{{{op_latex[...]}}}} → {{op_latex[...]}} ({n} 處)")
            
            # F.3 若 q 行包含 {...} 但不是 f-string，補上 f 前綴
            clean_code, n = re.subn(
                r"(q\s*[\+\-]?=\s*)'([^'\n]*?\{[^'\n]*?\}[^'\n]*?)',",
                r"\1f'\2',",
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] f-string 前綴修復: q = '{{...}}' → q = f'{{...}}' ({n} 處)")
            
            # F.4 修復 fmt_num(clean_latex_output)(X) 這種錯誤串接
            clean_code, n = re.subn(
                r'fmt_num\s*\(\s*clean_latex_output\s*\)\s*\(\s*([a-zA-Z_]\w*)\s*\)',
                r'clean_latex_output(\1)',
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 修復函式串接錯誤: fmt_num(clean_latex_output)(X) → clean_latex_output(X) ({n} 處)")

            # F.5 [新增] 修復指數格式化 (LaTeX 指數)
            # 問題：LLM 生成 ^{fmt_num(p)} → 應該是 ^{{{fmt_num(p)}}}（轉義的三重括號）
            # 這樣在 f-string 中會被正確解析為單一 {fmt_num(p)}
            
            # 修復 1：^{var} → ^{{{var}}}
            clean_code, n = re.subn(
                r'\^\{([a-zA-Z_]\w*)\}',  # 匹配 ^{variable_name}（無函數呼叫）
                r'^{{{\1}}}',               # 替換為 ^{{{variable_name}}}
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 指數修復: ^var 轉換 ({n} 處)")
            
            # 修復 2：^{fmt_num(...)} → ^{{{fmt_num(...)}}}（最常見的情況）
            # 這必須在 ^fmt_num 修復之前做，以免被錯誤修復
            clean_code, n = re.subn(
                r'\^\{(fmt_num\s*\([^)]+\))\}',  # 匹配 ^{fmt_num(...)}
                r'^{{{\1}}}',                       # 替換為 ^{{{fmt_num(...)}}}
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 指數修復: 指數中的 fmt_num 轉換 ({n} 處)")
            
            # 修復 3：^fmt_num( → ^{{{fmt_num(（用於無中括號的情況）
            clean_code, n = re.subn(
                r'\^fmt_num\s*\(',
                r'^{{{fmt_num(',
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 指數修復: 直接 ^fmt_num 轉換 ({n} 處)")
            
            # F.6 [新增] 修復係數-變數-括號問題
            # 問題：(a)x (b) → 應該是 {{fmt_num(a)}}x{{fmt_num(b)}}
            # 這樣學生才知道是「負數a乘以x加負數b」而不是「(a)乘以(b)」
            clean_code, n = re.subn(
                r'\(fmt_num\(([a-zA-Z_]\w*)\)\)([a-z])\s+\(fmt_num\(',
                r'{{{fmt_num(\1)}}}\2 {{{fmt_num(',
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 括號修復: (fmt_num(a))x (fmt_num(b)) → {{fmt_num(a)}}x {{fmt_num(b)}} ({n} 處)")

            # F.7 [新增] 修復多重賦值語法錯誤
            # 問題：m = ..., b_intercept = ... (逗號在中間，Python 認為是元組拆包)
            # 應該改為兩行分開的賦值
            # 模式：變數 = 長表達式 \\ ... \, 另一個變數 = ...
            # 改為：變數 = 長表達式 \\ ... \n 另一個變數 = ...
            clean_code, n = re.subn(
                r'(\n\s+)([a-zA-Z_]\w*)\s*=\s*(.+)\s*\\\s*(\n\s+.+)\s*,\s*([a-zA-Z_]\w*)\s*=\s*',
                r'\1\2 = \3 \\\\\4\n\1\5 = ',
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 多重賦值修復: var = ... , another_var = ... → 分開兩行 ({n} 處)")

            # F.8 [新增] 修復 LaTeX 表達式包裝問題
            # 問題：f_x_latex 和 point_latex 沒有用 $ 包裝，導致 clean_latex_output 斷裂
            # 修復 1：f_x_latex = f'f(x) = ...' → f_x_latex = f'$f(x) = ...$'
            clean_code, n1 = re.subn(
                r"(\s+f_x_latex\s*=\s*f)'([^']+)'",
                lambda m: f"{m.group(1)}f'${m.group(2)}$'",
                clean_code
            )
            qwen_fixes += n1
            if n1 > 0:
                print(f"🔧 [{skill_id}] LaTeX 函數包裝: f_x_latex 添加 $ ({n1} 處)")
            
            # 修復 2：point_latex = f'P(..., ...)' → point_latex = f'$P(..., ...)$'
            clean_code, n2 = re.subn(
                r"(\s+point_latex\s*=\s*f)'([^']+)'",
                lambda m: f"{m.group(1)}f'${m.group(2)}$'",
                clean_code
            )
            qwen_fixes += n2
            if n2 > 0:
                print(f"🔧 [{skill_id}] LaTeX 點包裝: point_latex 添加 $ ({n2} 處)")
            
            # 修復 3：處理已經有 f' 但缺少 $ 的其他 latex 變數
            clean_code, n3 = re.subn(
                r"(\s+[a-z_]*latex\s*=\s*f)'((?![\\$])[^'\$]*[a-zA-Z0-9\)}\]])'",
                lambda m: f"{m.group(1)}f'${m.group(2)}$'" if '$' not in m.group(2) else m.group(0),
                clean_code
            )
            qwen_fixes += n3
            if n3 > 0:
                print(f"🔧 [{skill_id}] 通用 LaTeX 變數包裝: 添加 $ ({n3} 處)")

            # G. 修復 to_latex(...) 在全域：轉為 fmt_num(...)
            clean_code, n = re.subn(r'\bto_latex\s*\(', 'fmt_num(', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 全域修復: to_latex(...) → fmt_num(...) ({n} 處)")
            
            # G.2 修復雙括號 {{}} 包 op_latex (使用預編譯 pattern)
            clean_code, n = COMPILED_PATTERNS['op_latex_double'].subn(r'{op_latex[\1]}', clean_code)
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 雙括號修復: {{{{op_latex[...]}}}} → {{op_latex[...]}} ({n} 處)")
            
            # G.3 修復 Fraction 除法 (使用預編譯 pattern)
            clean_code, n = COMPILED_PATTERNS['fraction_div'].subn(
                r'(\1 / \2) / (\3 / \4)',
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] Fraction 除法修復: Fraction(a,b)/Fraction(c,d) → 更清晰形式 ({n} 處)")
            
            # G.4 修復括號模式中的 None 值
            clean_code, n = re.subn(
                r'(bracket_structure\s*=\s*random\.choice\(\[)([^\]]*None[^\]]*)\](\))',
                r'\1\2\3',
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 括號候選篩選: 移除 None 或無效值 ({n} 處)")
        else:
            fstring_problem_detected = False
        
        regex_fixes += qwen_fixes
        healing_duration = time.time() - healing_start

        # ========================================
        # Step G: [NEW] AST 深度邏輯手術
        # ========================================
        # [Research Fix] AST Healer 條件執行
        # 只有當程式碼至少是語法正確(Syntax Valid)時，AST 才能運作
        # 所以先做一次快速檢查，或直接 try-catch
        
        ast_start = time.time()
        if use_ast_healer:
            clean_code, ast_fixes_count = fix_code_via_ast(clean_code)
            ast_fixes += ast_fixes_count
            if ast_fixes_count > 0:
                print(f"🔧 [AST Healer] {ast_fixes_count} structural fixes applied")
            
            # F.9 [Post-AST Fix] 修復 AST Healer 可能產生的 fmt_num(list) 錯誤
            # AST Healer 會將 polynomial_to_latex_string(coeffs) → fmt_num(coeffs)
            # 但 fmt_num 不接受 list，應該用 polynomial_to_string
            clean_code, n = re.subn(
                r'\bfmt_num\s*\(\s*(coeffs?|[a-z_]*_list|[a-z_]*s)\s*\)',
                r'polynomial_to_string(\1)',
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] fmt_num(list) 後置修復: 改為 polynomial_to_string() ({n} 處)")
            
            # F.11 [Post-AST Fix] 修復多項式格式化函數實現
            # 問題：LLM 生成的 polynomial_to_string/fmt_polynomial 使用 str(Fraction) 和錯誤的指數格式
            # 解決：替換整個函數實現為正確的 LaTeX 版本
            # [V47.10] 支援多種函數名稱變體：polynomial_to_string, fmt_polynomial, polynomial_to_latex
            poly_func_match = re.search(r'def ((?:fmt_)?polynomial(?:_(?:to_)?(?:string|latex))?)\s*\(', clean_code)
            if poly_func_match:
                poly_func_name = poly_func_match.group(1)
                print(f"📍 [DEBUG F.11] 觸發條件滿足：找到多項式函數 '{poly_func_name}'")
                # 定義正確的函數實現（不含縮排，稍後添加）
                correct_impl_lines = [
                    f'def {poly_func_name}(coeffs, variable=\'x\'):',
                    '    """正確的 LaTeX 多項式格式化函數"""',
                    '    terms = []',
                    '    degree = len(coeffs) - 1',
                    '    for i in range(degree + 1):',
                    '        coeff = coeffs[i]',
                    '        if coeff == 0:',
                    '            continue',
                    '        power = degree - i',
                    '        if power == 0:',
                    '            terms.append(fmt_num(coeff, op=True))',
                    '        elif power == 1:',
                    '            if abs(coeff) == 1:',
                    '                terms.append(f" {\'+\' if coeff > 0 else \'-\'} {variable}")',
                    '            else:',
                    '                terms.append(f"{fmt_num(coeff, op=True)}{variable}")',
                    '        else:',
                    '            if abs(coeff) == 1:',
                    '                terms.append(f" {\'+\' if coeff > 0 else \'-\'} {variable}^{{{power}}}")',
                    '            else:',
                    '                terms.append(f"{fmt_num(coeff, op=True)}{variable}^{{{power}}}")',
                    '    result = \'\'.join(terms)',
                    '    if result.startswith(\' + \'):',
                    '        result = result[3:]',
                    '    elif result.startswith(\'+\'):',
                    '        result = result[1:].strip()',
                    '    return result.strip()'
                ]
                
                # 找到並替換函數定義
                lines = clean_code.split('\n')
                new_lines = []
                skip_mode = False
                func_indent = None
                replaced = False
                
                for line in lines:
                    # 檢測函數定義開始（使用動態函數名）
                    match = re.match(rf'^(\s+)def {re.escape(poly_func_name)}\s*\(', line)
                    if match:
                        skip_mode = True
                        func_indent = match.group(1)  # 保存縮排字串
                        func_indent_len = len(func_indent)  # 保存縮排長度用於比較
                        # 添加正確的實現（每行加上相同縮排）
                        for impl_line in correct_impl_lines:
                            if impl_line:  # 非空行
                                new_lines.append(func_indent + impl_line)
                            else:  # 空行
                                new_lines.append('')
                        replaced = True
                        continue
                    
                    # 跳過舊的函數體
                    if skip_mode:
                        current_indent = len(line) - len(line.lstrip())
                        # 如果遇到相同或更小縮排的非空行，表示函數結束
                        if line.strip() and current_indent <= func_indent_len:
                            skip_mode = False
                            new_lines.append(line)
                        continue
                    
                    new_lines.append(line)
                
                if replaced:
                    clean_code = '\n'.join(new_lines)
                    qwen_fixes += 1
                    print(f"🔧 [{skill_id}] 替換 {poly_func_name} 為正確的 LaTeX 實現")
                else:
                    print(f"⚠️ [DEBUG F.11] 替換失敗：找不到匹配的函數定義 '{poly_func_name}'")
            
            # F.12 [Post-AST Fix] 修復多項式題目的 clean_latex_output 誤用
            # 問題：包含多項式格式化結果的題目不應再呼叫 clean_latex_output
            # 因為會將 "5x^{3} + 2x" 拆成 "$5x$ ^{ $3$ } $+ 2x$"
            # 解決：直接移除這類呼叫，並確保數學式已用 $ 包裹
            
            # [V47.10] 支援多種變數名稱：poly_str, f_x_latex, polynomial_str 等
            # 模式：移除對包含多項式變數的 clean_latex_output 呼叫
            clean_code, n = re.subn(
                r"(\n\s*)(q\s*=\s*f['\"][^'\"]*\{(?:poly_str|f_x_latex|polynomial_str)[_a-z0-9]*\}[^'\"]*['\"])\s*\n\s*q\s*=\s*clean_latex_output\s*\(\s*q\s*\)",
                r"\1\2  # 多項式已格式化，不需 clean_latex_output",
                clean_code
            )
            if n > 0:
                qwen_fixes += n
                print(f"🔧 [{skill_id}] 移除多項式題目的 clean_latex_output 呼叫 ({n} 處)")
                
                # 補充：確保題目中的數學式有 $ 包裹
                # 將 f'已知 f(x) = {f_x_latex}，求...' 改為 f'已知 $f(x) = {f_x_latex}$，求...'
                clean_code = re.sub(
                    r"(f['\"][^'\"]*)(f\(x\)\s*=\s*\{(?:poly_str|f_x_latex|polynomial_str)[_a-z0-9]*\})([^'\$\"]*['\"])",
                    r"\1$\2$\3",
                    clean_code
                )
        else:
            print(f"⏭️  [{skill_id}] AST Healer SKIPPED (ablation_id={ablation_id})")
            ast_fixes_count = 0
        # ========================================

        # ========================================
        # Step H: [DISABLED V46.9] 強制 LaTeX 清洗
        # ========================================
        # ❌ 已禁用原因：
        #    - 舊邏輯假設變數名稱為 q，但 AI 可能使用 q_latex、question 等
        #    - 導致 LaTeX 清洗邏輯無法應用（問題代碼中 return 用 q_latex 但檢查 q）
        # ✅ 新解決方案：使用 Step E.9 Return 語句自動清洗
        #    - 自動偵測 return 中的實際變數名稱
        #    - 對所有變數名稱都能正確應用 clean_latex_output()
        # ========================================

        # 組合
        final_code = CALCULATION_SKELETON + "\n" + clean_code

        # 7. 驗證
        is_valid, error_msg = validate_python_code(final_code)
        
        # 8. 生成完整標頭 (Header)
        duration = time.time() - start_time
        created_at = _pydt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 決定修復狀態標籤
        # 初始化動態採樣標誌（必須在使用前定義）
        dyn_ok = True
        sampling_success_count = 0
        sampling_total_count = 0
        temp_module = None
        
        if regex_fixes > 0 or ast_fixes > 0:
            fix_status_str = "[Repaired]"
        elif markdown_cleanup_count > 0:
            fix_status_str = "[Markdown-Cleaned]"
        else:
            fix_status_str = "[Clean Pass]"
        
        # [CRITICAL FIX] verify_status_str 应该同时检查 is_valid 和 dyn_ok
        # 不能只检查语法，还要检查动态采样（运行时验证）
        verify_status_str = "PASSED" if (is_valid and dyn_ok) else "FAILED"
        
        # 生成修復計數字符串（考慮 Markdown cleanup）
        if markdown_cleanup_count > 0:
            fixes_str = f"Markdown={markdown_cleanup_count}, Regex={regex_fixes}, AST={ast_fixes}"
        else:
            fixes_str = f"Regex={regex_fixes}, AST={ast_fixes}"
        
        header = f"""# ==============================================================================
# ID: {skill_id}
# Model: {current_model} | Strategy: V44.9 Hybrid-Healing
# Ablation ID: {ablation_id} | Healer: {'ON' if use_regex_healer else 'OFF'}
# Performance: {duration:.2f}s | Tokens: In={prompt_tokens}, Out={completion_tokens}
# Created At: {created_at}
# Fix Status: {fix_status_str} | Fixes: {fixes_str}
# Verification: Internal Logic Check = {verify_status_str}
# ==============================================================================
"""
        # 寫檔
        output_dir = _ensure_dir(_path_in_root('skills'))  # ← 用穩定解析
        # Dynamic Sampling: 精簡版（3次足夠，但可提前退出）
        # [旺宏科學獎] 獨立統計 Dynamic Sampling 次數
        # [注意] dyn_ok 已在上方初始化，此處不再重複初始化
        
        if is_valid:
            import importlib.util
            try:
                spec = importlib.util.spec_from_loader("temp_skill", loader=None)
                temp_module = importlib.util.module_from_spec(spec)
                exec(final_code, temp_module.__dict__)
            except Exception as e:
                dyn_ok = False
                print(f"[WARN] Code execution failed: {str(e)}")
        
        # Dynamic Sampling: 精簡版（3次足夠，但可提前退出）
        # [旺宏科學獎] 獨立統計 Dynamic Sampling 次數
        # [V47.10 Fix] 確保所有字符串使用 UTF-8 編碼
        if dyn_ok and temp_module:
            sampling_total_count = 0
            sampling_success_count = 0
            for sample_idx in range(3):
                sampling_total_count += 1
                try:
                    item = temp_module.generate()
                    # 验证返回结构
                    assert isinstance(item, dict), f"generate() must return dict, got {type(item)}"
                    assert 'question_text' in item, "Missing 'question_text' key"
                    assert 'answer' in item, "Missing 'answer' key"
                    # 验证没有函数对象或类型错误
                    question_str = str(item.get('question_text', ''))
                    if 'function' in str(type(item.get('question_text', ''))).lower():
                        raise TypeError(f"question_text is function object, not string: {type(item['question_text'])}")
                    
                    # [V47.10 NEW] 強制 UTF-8 編碼以保護中文字
                    if isinstance(item['question_text'], str):
                        item['question_text'] = item['question_text'].encode('utf-8', errors='replace').decode('utf-8')
                    if isinstance(item['answer'], str):
                        item['answer'] = item['answer'].encode('utf-8', errors='replace').decode('utf-8')
                    if 'correct_answer' in item and isinstance(item['correct_answer'], str):
                        item['correct_answer'] = item['correct_answer'].encode('utf-8', errors='replace').decode('utf-8')
                    
                    sampling_success_count += 1
                    
                    # ✅ 早期退出：如果前 2 次都成功，直接通過
                    if sampling_success_count >= 2:
                        print(f"✅ [{skill_id}] Dynamic sampling early pass (2/2 successful)")
                        break
                        
                except Exception as e:
                    error_msg = f"Dynamic sampling failed at iteration {sample_idx+1}: {str(e)}"
                    dyn_ok = False
                    print(f"[WARN] {error_msg}")
                    break
            else:
                # 如果跑完 3 次都沒 break，說明至少 2 次成功（因為失敗會 break）
                if sampling_success_count >= 2:
                    print(f"✅ [{skill_id}] Dynamic sampling passed all {sampling_success_count} iterations")
        
        # [V47.4] Gating 控制：只有當 is_valid AND dyn_ok 時，才寫檔
        success_final = bool(is_valid and dyn_ok)
        
        # [Ablation Study] 統一保存邏輯：無論成功或失敗，都保存到 skills\ 目錄
        # 使用統一的命名格式：{skill_id}_{model_size_class}_Ab{ablation_id}.py
        model_size_class = kwargs.get('model_size_class', '14b')
        ablation_id = kwargs.get('ablation_id', 3)
        
        if custom_output_path:
            out_path = custom_output_path
        else:
            # 使用統一的 Ablation 命名格式
            skills_dir = _ensure_dir(_path_in_root('skills'))
            out_path = os.path.join(skills_dir, f'{skill_id}_{model_size_class}_Ab{ablation_id}.py')
        
        # 總是保存到 skills\ 目錄（無論成功或失敗）
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(header + final_code)
            if success_final:
                print(f"✅ [{skill_id}] File written: {os.path.abspath(out_path)}")
            else:
                print(f"⚠️  [{skill_id}] File written (with errors): {os.path.abspath(out_path)}")
        except Exception as e:
            print(f"❌ [{skill_id}] Failed to write file: {e}")
        
        # [DEBUG INFO] 驗證結果說明
        if not success_final:
            if not is_valid:
                print(f"   • Syntax validation failed")
            if not dyn_ok:
                print(f"   • Dynamic sampling gating failed")
            
            # [V47.4] 影子寫檔：失敗樣本保留以便 debug（不影響正式）
            try:
                shadow_dir = _ensure_dir(_path_in_root('skills_shadow'))
                iso_dir    = _ensure_dir(_path_in_root('reports', 'isolated'))
                ts = _pydt.datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # 1) final_code（含 skeleton 的完整檔）
                shadow_path = os.path.join(shadow_dir, f"{skill_id}_FAILED_{ts}.py")
                with open(shadow_path, 'w', encoding='utf-8') as f:
                    f.write(header + final_code)
                
                # 2) clean_code（Healer 後、未包 skeleton）
                clean_only_path = os.path.join(shadow_dir, f"{skill_id}_FAILED_{ts}.clean.py")
                try:
                    with open(clean_only_path, 'w', encoding='utf-8') as f:
                        f.write(clean_code)
                except:
                    pass
                
                # 替代：直接再寫一份 final_code 到 iso_dir 當第二個落點（保險）
                iso_copy_path = os.path.join(iso_dir, f"{skill_id}_FAILED_{ts}.py")
                with open(iso_copy_path, 'w', encoding='utf-8') as f:
                    f.write(header + final_code)
                
                # 3) raw_output（模型原始文字）
                raw_path = os.path.join(shadow_dir, f"{skill_id}_FAILED_{ts}.raw.txt")
                with open(raw_path, 'w', encoding='utf-8') as f:
                    f.write(raw_output or "")
                
                print("📦 Isolated Save:")
                print("   • Final (skeleton+code):", os.path.abspath(shadow_path))
                print("   • Raw LLM output      :", os.path.abspath(raw_path))
                print("   • Extra copy (reports):", os.path.abspath(iso_copy_path))
            except Exception as e:
                print(f"[WARN] Shadow save failed: {e}")

        # [V47.4] Feature Flags 快照：把旗標串成文字，便於離線分析
        flags = {
            'capsule': 0,      # 是否啟用 Architect Domain Capsule（目前 0/1）
            'coderV': 'V47.4', # Coder prompt 流水線版本字串
            'regexV47': 1,     # 是否啟用通用 Regex 修補
            'dynStrict': 1,    # 嚴格動態採樣 gating
            'shadow': 0,       # 是否影子寫檔（skills_shadow）
        }
        prompt_level_with_flags = (kwargs.get('prompt_level', 'Full-Healing')
                                   + " | "
                                   + ";".join(f"{k}={v}" for k, v in flags.items()))

        # 9. Log
        log_experiment(
            skill_id=skill_id,
            start_time=start_time,
            prompt_len=len(prompt),
            code_len=len(final_code),
            is_valid=success_final,
            error_msg=error_msg,
            repaired=(regex_fixes > 0 or ast_fixes > 0),
            model_name=current_model,
            final_code=final_code,
            raw_response=raw_output,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            score_syntax=100.0 if success_final else 0.0,
            ablation_id=ablation_id,
            model_size_class=kwargs.get('model_size_class', 'cloud'),
            prompt_level=prompt_level_with_flags,
            healing_duration=healing_duration,
            is_executable=1 if success_final else 0,
            missing_imports_fixed=', '.join(removed_list) if removed_list else '',
            score_math=0.0,
            score_visual=0.0,
            resource_cleanup_flag=False,
            # [旺宏科學獎 3×3 設計專用欄位]
            experiment_group=kwargs.get('experiment_group', None),
            garbage_cleaner_count=garbage_cleaner_count,
            eval_eliminator_count=eval_eliminator_count,
            sampling_success_count=sampling_success_count,
            sampling_total_count=sampling_total_count,
            spec_prompt_id=kwargs.get('spec_prompt_id', None),
            use_master_spec=kwargs.get('use_master_spec', False)
        )

        return success_final, "V47.4 Generated", {
            'tokens': prompt_tokens + completion_tokens,
            'score_syntax': 100.0 if success_final else 0.0,
            'total_fixes': regex_fixes + ast_fixes,
            'regex_fixes': regex_fixes,
            'ast_fixes': ast_fixes,
            'is_valid': success_final
        }

    except Exception as e:
        print(f"Generate Error: {e}")
        # 保底落盤：把能拿到的 final_code 或 raw_output 寫到 reports/isolated/
        try:
            iso_dir = _ensure_dir(_path_in_root('reports', 'isolated'))
            ts = _pydt.datetime.now().strftime('%Y%m%d_%H%M%S')
            if 'final_code' in locals():
                p = os.path.join(iso_dir, f"{skill_id}_EXCEPTION_{ts}.py")
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(locals().get('header', '') + final_code)
                print("🧯 Saved final_code on exception:", os.path.abspath(p))
            if 'raw_output' in locals() and raw_output:
                p = os.path.join(iso_dir, f"{skill_id}_EXCEPTION_{ts}.raw.txt")
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(raw_output)
                print("🧯 Saved raw_output on exception:", os.path.abspath(p))
        except Exception as ee:
            print("[WARN] Exception fallback save failed:", ee)
        return False, str(e), {}

# ==============================================================================
# 6. Legacy Support (兼容舊腳本)
# ==============================================================================
def inject_robust_dispatcher(code_str):
    """
    [Legacy Stub]
    舊版 sync_skills_files.py 會呼叫此函式。
    在 V44.9 架構下，AI 已生成單一完整邏輯，不需要分流注入。
    直接回傳原代碼即可維持相容性。
    """
    return code_str

def validate_and_fix_code(c): return c, 0
def fix_logic_errors(c, e): return c, 0