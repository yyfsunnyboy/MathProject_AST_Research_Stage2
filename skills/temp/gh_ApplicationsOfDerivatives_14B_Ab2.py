# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder:14b | Strategy: V47.5 Unified-Cleanup + Advanced-Healer
# Ablation ID: 2 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 20.93s | Tokens: In=7330, Out=603
# Created At: 2026-01-31 18:09:16
# Fix Status: [Basic Cleanup] | Fixes: Basic=2, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================


# [INJECTED UTILS]
import random
from random import randint, choice
import math
from fractions import Fraction
import re
import ast
import operator

# ✅ 預設的 LaTeX 運算子映射（四則）- 全域可用
op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}

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

def fmt_term(coeff, power, var='x'):
    """
    [Standard Utils] 格式化單一多項式項目
    例如: fmt_term(-1, 2, 'x') -> "-x^2"
          fmt_term(3, 1, 'x') -> "3x"
          fmt_term(-2, 0, 'x') -> "-2"
    
    Args:
        coeff: 係數（整數或分數）
        power: 次方數
        var: 變數名稱（預設 'x'）
        
    Returns:
        str: LaTeX 格式的項目字串
    """
    if coeff == 0: 
        return ""
    
    # 符號部分
    sign = ""
    if coeff < 0: 
        sign = "-"
    
    abs_c = abs(coeff)
    
    # 係數部分
    c_str = ""
    if abs_c != 1 or power == 0:
        c_str = fmt_num(abs_c)
    
    # 變數部分
    v_str = ""
    if power == 1:
        v_str = var
    elif power > 1:
        v_str = f"{var}^{{{power}}}"  # 使用 LaTeX 標準格式
        
    return f"{sign}{c_str}{v_str}"

# ==============================================================================
# 安全運算
# ==============================================================================

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

# ==============================================================================
# 數論工具
# ==============================================================================

def is_prime(n):
    if n <= 1: return False
    if n <= 3: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def gcd(a, b): 
    return math.gcd(int(a), int(b))

def lcm(a, b): 
    return abs(int(a) * int(b)) // math.gcd(int(a), int(b))

def get_factors(n):
    n = abs(n)
    factors = set()
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            factors.add(i)
            factors.add(n // i)
    return sorted(list(factors))

# ==============================================================================
# 跨領域工具組
# ==============================================================================

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

# ==============================================================================
# 答案驗證
# ==============================================================================

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


# ==============================================================================
# [V10.0 新增] 多項式處理工具 - 防止 LLM 幻覺函數
# ==============================================================================

def build_polynomial_text(coeffs):
    """
    將係數列表轉換為多項式文字表示
    
    Args:
        coeffs: 係數列表，從高次項到常數項 [a_n, a_{n-1}, ..., a_1, a_0]
                例如 [2, 0, -3, 1] 表示 2x³ - 3x + 1
    
    Returns:
        str: 多項式的 LaTeX 格式字串
    
    Examples:
        >>> build_polynomial_text([2, 0, -3, 1])
        '2x^{3} - 3x + 1'
        >>> build_polynomial_text([1, -2])
        'x - 2'
    """
    if not coeffs:
        return "0"
    
    # 移除前導零
    while len(coeffs) > 1 and coeffs[0] == 0:
        coeffs = coeffs[1:]
    
    if all(c == 0 for c in coeffs):
        return "0"
    
    terms = []
    n = len(coeffs) - 1  # 最高次數
    
    for i, coef in enumerate(coeffs):
        if coef == 0:
            continue
        
        power = n - i
        
        # 處理係數
        if power == 0:
            # 常數項
            terms.append(str(coef))
        elif power == 1:
            # 一次項
            if coef == 1:
                terms.append("x")
            elif coef == -1:
                terms.append("-x")
            else:
                terms.append(f"{coef}x")
        else:
            # 高次項
            if coef == 1:
                terms.append(f"x^{{{power}}}")
            elif coef == -1:
                terms.append(f"-x^{{{power}}}")
            else:
                terms.append(f"{coef}x^{{{power}}}")
    
    if not terms:
        return "0"
    
    # 組合項目，處理正負號
    result = terms[0]
    for term in terms[1:]:
        if term.startswith('-'):
            result += f" - {term[1:]}"
        else:
            result += f" + {term}"
    
    return result

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

def get_base_root():
    """
    優先用 Flask current_app.root_path；若不可用，回退到 core/ 的上一層（專案根）
    """
    try:
        from flask import has_app_context, current_app
        if has_app_context():
            return current_app.root_path
    except Exception:
        pass
    # fallback: project root = parent of core/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

def path_in_root(*parts):
    """構建專案根目錄下的路徑"""
    return os.path.join(get_base_root(), *parts)

def ensure_dir(p):
    """確保目錄存在"""
    os.makedirs(p, exist_ok=True)
    return p


# [DOMAIN HELPERS - Auto-Injected for gh_ApplicationsOfDerivatives]

# ===== 多項式標準函數庫 =====

def _poly_to_latex(terms):
    '''
    將多項式內部表示轉換為 LaTeX 字符串
    參數: terms = [(coeff, exp), ...] 例如 [(3, 2), (-5, 0)] → 3x² - 5
    返回: LaTeX 字符串（不含 $ 符號）
    '''
    if not terms:
        return '0'
    parts = []
    for i, (c, e) in enumerate(sorted(terms, key=lambda x: x[1], reverse=True)):
        if c == 0:
            continue
        sign = '' if i == 0 else (' + ' if c > 0 else ' - ')
        abs_c = abs(c)
        coeff_str = '' if (abs_c == 1 and e > 0) else str(abs_c)
        if e == 0:
            var_str = str(abs_c)
        elif e == 1:
            var_str = f'{coeff_str}x' if coeff_str else 'x'
        else:
            var_str = f'{coeff_str}x^{{{e}}}' if coeff_str else f'x^{{{e}}}'
        parts.append(f'{sign}{var_str}')
    return ''.join(parts).strip()

def _poly_to_plain(terms):
    '''
    將多項式內部表示轉換為純文本字符串
    參數: terms = [(coeff, exp), ...]
    返回: 純文本字符串，例如 "3x^2-5"（無空格）
    '''
    if not terms:
        return '0'
    parts = []
    for i, (c, e) in enumerate(sorted(terms, key=lambda x: x[1], reverse=True)):
        if c == 0:
            continue
        sign = '' if i == 0 else ('+' if c > 0 else '-')
        abs_c = abs(c)
        coeff_str = '' if (abs_c == 1 and e > 0) else str(abs_c)
        if e == 0:
            var_str = str(abs_c)
        elif e == 1:
            var_str = f'{coeff_str}x' if coeff_str else 'x'
        else:
            var_str = f'{coeff_str}x^{e}' if coeff_str else f'x^{e}'
        parts.append(f'{sign}{var_str}')
    return ''.join(parts).strip()

def _differentiate_poly(terms, order=1):
    '''
    對多項式求導 order 次
    參數:
        terms: [(coeff, exp), ...]
        order: 求導次數
    返回: 導數的內部表示 [(new_coeff, new_exp), ...]
    '''
    result = list(terms)
    for _ in range(order):
        new_terms = []
        for c, e in result:
            if e > 0:
                new_c = c * e
                if abs(new_c) > 10000:  # [Fix] 放寬限制，避免合理係數被拒絕
                    raise ValueError(f"Coefficient {new_c} exceeds limit")
                new_terms.append((new_c, e - 1))
        result = new_terms
    return result

def _deriv_symbol_latex(order):
    '''生成導數符號（LaTeX）: f'(x), f''(x), f^{(n)}(x)'''
    if order == 1:
        return "f'(x)"
    elif order == 2:
        return "f''(x)"
    else:
        return f"f^{{({order})}}(x)"

def _deriv_symbol_plain(order):
    '''生成導數符號（純文本）: f'(x), f''(x), f^(n)(x)'''
    if order == 1:
        return "f'(x)"
    elif order == 2:
        return "f''(x)"
    else:
        return f"f^({order})(x)"

# ===== 🔴 CRITICAL: 題目組裝規範（必須遵守）=====
# 
# 當使用多項式函數時，請按以下方式組裝題目：
# 
# ✅ 正確範例（手動添加 $ 符號，**不要** 使用 clean_latex_output）：
#   poly_str = _poly_to_latex(terms)        # 返回: "3x^{2} - 5x + 2"
#   deriv_sym = _deriv_symbol_latex(1)      # 返回: "f'(x)"
#   q = f'已知 $f(x) = {poly_str}$, 求 ${deriv_sym}$。'
#   # ⚠️ 直接使用 q，不要調用 clean_latex_output(q)！
#   return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
# 
# ❌ 錯誤範例（會破壞 LaTeX 格式）：
#   q = f'已知 $f(x) = {poly_str}$, 求 ${deriv_sym}$。'
#   return {'question_text': clean_latex_output(q), ...}  # ❌ 不要這樣做！
#   # 錯誤結果：$x$ ^{ $4$ } $- 6x$ ^{ $3$ }（每個符號都被錯誤地獨立包裝）
# 
# 原因：clean_latex_output() 適用於簡單運算（如 "3 + 5"），
#      但多項式函數已經返回正確的 LaTeX 格式（如 x^{4}），
#      再次呼叫會導致過度處理，將 x^{4} 拆分成 $x$ ^{ $4$ }



# ===== 微積分標準函數庫 =====
# (多項式微分已在 POLYNOMIAL_HELPERS 中定義)

def _find_critical_points(coeffs):
    '''
    找多項式的臨界點（一階導數為 0 的點）
    參數: coeffs = [a_n, a_{n-1}, ..., a_0] (降冪排列)
    返回: 臨界點列表
    '''
    # 實現求導 + 解方程
    pass

def _evaluate_poly(coeffs, x):
    '''計算多項式在 x 點的值'''
    result = 0
    for i, c in enumerate(coeffs):
        result += c * (x ** (len(coeffs) - 1 - i))
    return result



# [AI GENERATED CODE]
# ---------------------------------------------------------


import random

def generate(level=1, **kwargs):
    # Step 1: Generate the base polynomial terms
    max_degree = random.randint(3, 5)
    num_terms = random.randint(3, min(5, max_degree + 1))
    
    available_degrees = list(range(max_degree + 1))
    random.shuffle(available_degrees)
    selected_degrees = available_degrees[:num_terms]
    
    terms = []
    has_negative_coefficient = False
    for deg in selected_degrees:
        coeff = random.randint(-10, 10)
        while coeff == 0:
            coeff = random.randint(-10, 10)
        if coeff < 0:
            has_negative_coefficient = True
        terms.append((coeff, deg))
    
    # Ensure there is a constant term (degree 0) and at least one negative coefficient
    if 0 not in selected_degrees:
        terms.append((random.randint(1, 10), 0))
    elif not has_negative_coefficient:
        for i, (c, d) in enumerate(terms):
            if c > 0:
                terms[i] = (-c, d)
                break
    
    # Step 2: Generate the derivative orders
    num_derivatives = random.randint(1, 2)
    derivative_orders_list = []
    
    # [Fix] 確保求導次數 < max_degree，避免零多項式
    # 例如：max_degree=2 時，最多求 1 階導數（結果至少是一次多項式）
    max_derivative_order = max(1, max_degree - 1)
    
    for _ in range(num_derivatives):
        order = random.randint(1, min(max_derivative_order, 3))
        while order in derivative_orders_list:
            order = random.randint(1, min(max_derivative_order, 3))
        derivative_orders_list.append(order)
    
    # Step 3: Calculate the derivatives
    derivative_results = []
    for order in derivative_orders_list:
        deriv_terms = _differentiate_poly(terms, order=order)
        if not any(c != 0 for c, _ in deriv_terms):
            raise ValueError("Derivative resulted in a zero polynomial")
        derivative_results.append((order, deriv_terms))
    
    # Step 4: Format the question
    poly_latex = _poly_to_latex(terms)
    derivative_symbols_latex = ', '.join(_deriv_symbol_latex(order) for order in derivative_orders_list)
    q = f"已知 $f(x) = {poly_latex}$，求 {derivative_symbols_latex}。"
    
    # Step 5: Format the answer
    ans_parts = []
    for order, deriv_terms in sorted(derivative_results):
        deriv_poly_plain = _poly_to_plain(deriv_terms)
        ans_parts.append(deriv_poly_plain)
    correct_answer = ', '.join(ans_parts)
    
    return {
        'question_text': q,
        'correct_answer': correct_answer,
        'answer': correct_answer,
        'mode': 1
    }