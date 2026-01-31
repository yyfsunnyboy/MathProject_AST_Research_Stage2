# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V47.5 Unified-Cleanup + Advanced-Healer
# Ablation ID: 2 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 25.90s | Tokens: In=5454, Out=3193
# Created At: 2026-01-31 16:21:22
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


# [AI GENERATED CODE]
# ---------------------------------------------------------


import random
import math
import re
from fractions import Fraction

# Assume pre-loaded tools are available:
# fmt_num(n), to_latex(n), clean_latex_output(q), op_latex, etc.

# Mock implementations for testing if not running in a specific environment
# In the actual environment, these would be provided.
try:
    fmt_num(1)
except NameError:
    def fmt_num(n):
        if isinstance(n, Fraction):
            if n.denominator == 1:
                return str(n.numerator)
            return f"\\frac{{{n.numerator}}}{{{n.denominator}}}"
        return str(n)

try:
    to_latex(1)
except NameError:
    def to_latex(n):
        if isinstance(n, Fraction):
            if n.denominator == 1:
                return str(n.numerator)
            return f"\\frac{{{n.numerator}}}{{{n.denominator}}}"
        return str(n)

try:
    op_latex
except NameError:
    op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}

# As per MASTER_SPEC, clean_latex_output should NOT be called for question_text
# when using _poly_to_latex and manual $ wrapping.
# So, we define a dummy if it's not already defined to avoid NameError,
# but it will not be used in the question formatting.
try:
    clean_latex_output("test")
except NameError:
    def clean_latex_output(q):
        return q


# Helper functions for polynomial formatting and differentiation
def _poly_to_latex(terms):
    """
    Converts a list of polynomial terms (coeff, exp) to a LaTeX string.
    Handles formatting for 1x^n, -1x^n, x^1, x^0, and signs.
    Does NOT wrap in $$.
    """
    if not terms:
        return "0"
    
    # Filter out zero terms and sort by exponent in descending order
    terms = [(c, e) for c, e in terms if c != 0]
    if not terms: return "0" # If all terms became zero after filtering

    terms.sort(key=lambda x: x[1], reverse=True)
    
    latex_parts = []
    for i, (coeff, exp) in enumerate(terms):
        part = ""
        
        # Handle sign for non-first terms
        if coeff > 0 and i > 0:
            part += "+"
        elif coeff < 0:
            part += "-"

        abs_coeff = abs(coeff)

        # Handle coefficient part
        if abs_coeff != 1 or exp == 0: # Show 1 for constant term, otherwise omit for x^n
            part += fmt_num(abs_coeff)
        
        # Handle x and exponent part
        if exp > 0:
            part += "x"
            if exp > 1:
                part += f"^{{{exp}}}"
        
        latex_parts.append(part)
    
    return "".join(latex_parts)

def _poly_to_text(terms):
    """
    Converts a list of polynomial terms (coeff, exp) to a plain text string.
    Handles formatting for 1x^n, -1x^n, x^1, x^0, and signs.
    Used for the answer field.
    """
    if not terms:
        return "0"

    # Filter out zero terms and sort by exponent in descending order
    terms = [(c, e) for c, e in terms if c != 0]
    if not terms: return "0" # If all terms became zero after filtering

    terms.sort(key=lambda x: x[1], reverse=True)
    
    text_parts = []
    for i, (coeff, exp) in enumerate(terms):
        part = ""
        
        # Handle sign and spacing
        if coeff > 0 and i > 0:
            part += " + "
        elif coeff < 0:
            part += " - "
        elif i > 0: # Should not happen if first term is positive
            pass # No sign for first positive term

        abs_coeff = abs(coeff)

        # Handle coefficient part
        if abs_coeff != 1 or exp == 0:
            part += str(abs_coeff)
        
        # Handle x and exponent part
        if exp > 0:
            part += "x"
            if exp > 1:
                part += f"^{exp}"
        
        text_parts.append(part.strip())
    
    result = "".join(text_parts)
    # Clean up leading '+' if present (from the first term being positive)
    if result.startswith('+ '):
        result = result[2:]
    return result

def _deriv_symbol_latex(order):
    """
    Returns the LaTeX string for the derivative symbol (e.g., f'(x), f''(x), f'''(x), f^(n)(x)).
    Does NOT wrap in $$.
    """
    if order == 1:
        return "f'(x)"
    elif order == 2:
        return "f''(x)"
    elif order == 3:
        return "f'''(x)"
    else:
        return f"f^{{({order})}}(x)"

def _calculate_derivative(polynomial_terms, order):
    """
    Calculates the derivative of a polynomial for a given order.
    Input: list of (coefficient, exponent) tuples.
    Output: list of (coefficient, exponent) tuples for the derivative.
    """
    current_terms = list(polynomial_terms) # Work on a copy
    
    for _ in range(order):
        next_terms = []
        for coeff, exp in current_terms:
            if exp > 0: # Only differentiate terms with exp > 0
                new_coeff = coeff * exp
                new_exp = exp - 1
                # Only keep terms with non-zero coefficient after differentiation
                if new_coeff != 0:
                    next_terms.append((new_coeff, new_exp))
        current_terms = next_terms
        
    # Filter out terms with coefficient 0 and sort by exponent
    current_terms = [(c, e) for c, e in current_terms if c != 0]
    current_terms.sort(key=lambda x: x[1], reverse=True)
    return current_terms

def generate(level=1, **kwargs):
    max_attempts = 100 # Max attempts to generate a valid question
    for _ in range(max_attempts):
        try:
            # 1. Generate degree (3~5)
            degree = random.randint(3, 5)

            # 2. Generate num_terms (3~5)
            num_terms = random.randint(3, min(degree + 1, 5)) # Ensure num_terms <= degree + 1

            # 3. Generate exponents: choose num_terms distinct exponents from degree down to 0
            # Ensure highest degree term is present
            available_exponents = list(range(degree + 1))
            
            exponents = set()
            exponents.add(degree) # Ensure highest degree term
            while len(exponents) < num_terms:
                exponents.add(random.choice(available_exponents))
            
            exponents = sorted(list(exponents), reverse=True)

            # 4. Generate coefficients for each exponent
            coefficients = []
            has_negative_coeff = False
            has_non_one_minus_one_coeff = False
            
            for exp in exponents:
                coeff = 0
                while coeff == 0: # Coefficient must be non-zero (unless it's a constant term that can be 0, but total polynomial cannot be zero)
                    coeff = random.randint(-10, 10)
                
                if coeff < 0:
                    has_negative_coeff = True
                if coeff not in [-1, 1]:
                    has_non_one_minus_one_coeff = True
                
                coefficients.append(coeff)
            
            # Ensure constraints for coefficients
            if not has_negative_coeff:
                # Find a non-constant term to make negative
                idx_to_negate = random.choice([i for i, exp in enumerate(exponents) if exp > 0])
                coefficients[idx_to_negate] = -abs(coefficients[idx_to_negate])
                has_negative_coeff = True # Redundant, but for clarity

            if not has_non_one_minus_one_coeff:
                # Find a term to make non-+-1
                idx_to_change = random.choice(range(len(coefficients)))
                original_coeff = coefficients[idx_to_change]
                new_coeff = random.choice([c for c in [-10, -9, -8, -7, -6, -5, -4, -3, -2, 2, 3, 4, 5, 6, 7, 8, 9, 10] if c != original_coeff])
                coefficients[idx_to_change] = new_coeff
                has_non_one_minus_one_coeff = True # Redundant

            # Ensure highest degree term has non-zero coefficient (already handled by coeff != 0 loop)
            # Ensure the polynomial is not a zero polynomial (handled by ensuring at least 3 terms with non-zero coefficients)

            # Construct polynomial_terms
            polynomial_terms = sorted(list(zip(coefficients, exponents)), key=lambda x: x[1], reverse=True)
            
            # Check basic polynomial validity
            if len(polynomial_terms) < 3 or polynomial_terms[0][1] < 3:
                raise ValueError("Polynomial does not meet minimum term/degree requirements.")
            if not has_negative_coeff or not has_non_one_minus_one_coeff:
                 raise ValueError("Polynomial does not meet coefficient diversity requirements.")


            # 6. Choose requested_derivative_orders
            possible_orders = [o for o in range(1, degree)] # 1 <= order < degree
            if len(possible_orders) < 2: # Need at least two distinct orders
                raise ValueError("Not enough possible derivative orders for this polynomial degree.")

            order1 = random.choice(possible_orders)
            order2 = random.choice([o for o in possible_orders if o != order1])
            requested_derivative_orders = sorted([order1, order2])

            # Ensure at least one order > 1
            if all(o == 1 for o in requested_derivative_orders):
                # If both are 1, try to change one to > 1
                if degree > 1: # This should always be true as degree >= 3
                    higher_orders = [o for o in possible_orders if o > 1]
                    if higher_orders:
                        requested_derivative_orders[random.randint(0,1)] = random.choice(higher_orders)
                        requested_derivative_orders.sort()
                    else:
                        raise ValueError("Cannot ensure at least one derivative order > 1 for this polynomial.")
                
            # 7. Calculate derivatives and check coefficient bounds
            derivative_results = {}
            for order in requested_derivative_orders:
                deriv_poly = _calculate_derivative(polynomial_terms, order)
                
                # Check if derivative is zero polynomial (e.g., if order >= original degree)
                if not deriv_poly:
                    raise ValueError(f"Derivative of order {order} resulted in a zero polynomial. Regenerating orders.")
                
                # Check coefficient bounds for the derivative
                for c, _ in deriv_poly:
                    if abs(c) > 1000:
                        raise ValueError(f"Derivative coefficient {c} exceeds absolute limit of 1000.")
                
                derivative_results[order] = deriv_poly
            
            # All checks passed, proceed to formatting
            
            # Question formatting
            poly_str = _poly_to_latex(polynomial_terms)
            
            deriv_req_parts_latex = []
            for order in requested_derivative_orders:
                deriv_req_parts_latex.append(f"${_deriv_symbol_latex(order)}$")
            
            derivative_requests_str = "與".join(deriv_req_parts_latex)
            
            q = f"已知 $f(x) = {poly_str}$，求 {derivative_requests_str}。"
            # CRITICAL: As per MASTER_SPEC "多項式 LaTeX 處理特殊規則", DO NOT call clean_latex_output(q) here.

            # Answer formatting
            answer_parts = []
            # Sort by order to ensure consistent answer output
            for order in sorted(requested_derivative_orders):
                deriv_poly_str_text = _poly_to_text(derivative_results[order])
                answer_parts.append(deriv_poly_str_text)
            
            # CRITICAL: As per MASTER_SPEC "導數題型特殊規範", answer should be
            # comma-separated polynomial expressions without f'(x) = prefixes.
            a = ", ".join(answer_parts)
            
            return {
                'question_text': q,
                'correct_answer': a,
                'answer': a,
                'mode': 1
            }

        except ValueError as e:
            # print(f"Regenerating due to: {e}") # For debugging purposes
            continue # Try again
    
    raise RuntimeError("Failed to generate a valid question after multiple attempts.")