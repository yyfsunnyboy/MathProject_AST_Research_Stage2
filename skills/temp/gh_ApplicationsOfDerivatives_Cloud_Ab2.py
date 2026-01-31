# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V47.5 Unified-Cleanup + Advanced-Healer
# Ablation ID: 2 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 47.22s | Tokens: In=6662, Out=3881
# Created At: 2026-01-31 12:51:21
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
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
import ast
import operator
from fractions import Fraction

# --- Preloaded tools ---
def fmt_num(n):
    if isinstance(n, Fraction):
        if n.denominator == 1:
            return str(n.numerator)
        return f"\\frac{{{n.numerator}}}{{{n.denominator}}}"
    return str(n)

def to_latex(n):
    if isinstance(n, Fraction):
        if n.denominator == 1:
            return str(n.numerator)
        return f"\\frac{{{n.numerator}}}{{{n.denominator}}}"
    return str(n)

def clean_latex_output(q):
    # This function is usually for simple math expressions.
    # For polynomials using _poly_to_latex, it's explicitly forbidden by MASTER_SPEC.
    # So, it's defined but not used for the 'question_text' in this specific problem.
    q = q.replace('+-', '-').replace('--', '+')
    q = re.sub(r'\s*([+\-*/=])\s*', r'\1', q) # Remove spaces around operators
    q = q.replace('$', ' $ ').replace('{', ' { ').replace('}', ' } ')
    q = re.sub(r'\s+', ' ', q).strip()
    q = q.replace(' $ ', '$').replace(' { ', '{').replace(' } ', '}')
    return q

def check(user_answer, correct_answer):
    # Placeholder for a check function, not used in generate
    pass

op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}

# --- Number Theory Functions (placeholders as not directly used in this problem) ---
def is_prime(n): pass
def gcd(a, b): pass
def lcm(a, b): pass
def get_factors(n): pass

# --- Combinatorics (placeholders) ---
def nCr(n, r): pass
def nPr(n, r): pass
def factorial_bounded(n): pass

# --- Other (placeholders) ---
def clamp_fraction(f): pass
def safe_pow(base, exp): pass
def rational_gauss_solve(*args): pass


# ===== 多項式標準函數庫 (Provided by prompt) =====

def _poly_to_latex(terms):
    '''
    將多項式內部表示轉換為 LaTeX 字符串
    參數: terms = [(coeff, exp), ...] 例如 [(3, 2), (-5, 0)] → 3x² - 5
    返回: LaTeX 字符串（不含 $ 符號）
    '''
    if not terms:
        return '0'
    parts = []
    # Filter out (0, exp) terms, except if it's the only term and it's (0,0)
    non_zero_terms = [(c, e) for c, e in terms if c != 0]
    
    if not non_zero_terms: # If all coefficients are zero or all terms were (0, exp)
        return '0'

    # Sort terms by exponent in descending order
    sorted_terms = sorted(non_zero_terms, key=lambda x: x[1], reverse=True)

    for i, (c, e) in enumerate(sorted_terms):
        sign = ''
        if i > 0:
            sign = ' + ' if c > 0 else ' - '
        elif c < 0:
            sign = '-' # First term negative

        abs_c = abs(c)
        coeff_str = ''
        if e == 0: # Constant term
            coeff_str = str(abs_c)
        elif abs_c != 1: # Coefficient is not 1 or -1
            coeff_str = str(abs_c)
        
        var_str = ''
        if e == 1:
            var_str = 'x'
        elif e > 1:
            var_str = f'x^{{{e}}}'
        # If e == 0, var_str remains empty, coeff_str is the number itself

        parts.append(f'{sign}{coeff_str}{var_str}')
    return ''.join(parts).strip()


def _poly_to_plain(terms):
    '''
    將多項式內部表示轉換為純文本字符串
    參數: terms = [(coeff, exp), ...]
    返回: 純文本字符串，例如 "3x^2 - 5"
    '''
    if not terms:
        return '0'
    parts = []
    # Filter out (0, exp) terms, except if it's the only term and it's (0,0)
    non_zero_terms = [(c, e) for c, e in terms if c != 0]

    if not non_zero_terms: # If all coefficients are zero or all terms were (0, exp)
        return '0'

    # Sort terms by exponent in descending order
    sorted_terms = sorted(non_zero_terms, key=lambda x: x[1], reverse=True)

    for i, (c, e) in enumerate(sorted_terms):
        sign = ''
        if i > 0:
            sign = ' + ' if c > 0 else ' - '
        elif c < 0:
            sign = '-' # First term negative

        abs_c = abs(c)
        coeff_str = ''
        if e == 0: # Constant term
            coeff_str = str(abs_c)
        elif abs_c != 1: # Coefficient is not 1 or -1
            coeff_str = str(abs_c)
        
        var_str = ''
        if e == 1:
            var_str = 'x'
        elif e > 1:
            var_str = f'x^{e}'
        # If e == 0, var_str remains empty, coeff_str is the number itself

        parts.append(f'{sign}{coeff_str}{var_str}')
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
            if e > 0: # Only differentiate terms with exponent > 0
                new_c = c * e
                # Intermediate coefficient check (can be higher than final limit)
                if abs(new_c) > 100000: # A generous internal limit to prevent overflow
                    raise ValueError(f"Intermediate coefficient {new_c} exceeds internal limit during differentiation.")
                new_terms.append((new_c, e - 1))
        result = new_terms
    
    # Filter out zero coefficient terms. If the result is all zeros, return [(0,0)].
    filtered_result = [(c, e) for c, e in result if c != 0]
    if not filtered_result:
        return [(0,0)] # Represents the polynomial '0'
    return filtered_result

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

# ===== 微積分標準函數庫 (Provided by prompt) =====
# (多項式微分已在 POLYNOMIAL_HELPERS 中定義)

def _find_critical_points(coeffs):
    '''
    找多項式的臨界點（一階導數為 0 的點）
    參數: coeffs = [a_n, a_{n-1}, ..., a_0] (降冪排列)
    返回: 臨界點列表
    '''
    # Not used in this problem
    pass

def _evaluate_poly(coeffs, x):
    '''計算多項式在 x 點的值'''
    # Not used in this problem
    result = 0
    for i, c in enumerate(coeffs):
        result += c * (x ** (len(coeffs) - 1 - i))
    return result

# --- Helper function for generating polynomial terms based on MASTER_SPEC ---
def _generate_polynomial_terms_with_constraints(degree, coeff_range_min, coeff_range_max, min_nonzero_terms_excluding_constant):
    """
    Generates a polynomial in [(coeff, exp)] format satisfying all constraints.
    Returns None if constraints cannot be met within reasonable attempts.
    """
    
    terms = []
    
    # 1. Leading coefficient (must be non-zero)
    leading_coeff = 0
    while leading_coeff == 0:
        leading_coeff = random.randint(coeff_range_min, coeff_range_max)
    terms.append((leading_coeff, degree))
    
    # 2. Generate other coefficients (from degree-1 down to 1)
    # Keep track of exponents that must be non-zero
    non_constant_exps = list(range(1, degree)) # Exponents from 1 to degree-1
    random.shuffle(non_constant_exps)
    
    # We already have 1 non-zero term (leading). Need (min_nonzero_terms_excluding_constant - 1) more.
    num_additional_nonzero_needed = max(0, min_nonzero_terms_excluding_constant - 1)
    
    guaranteed_nonzero_exps = set()
    if num_additional_nonzero_needed > 0 and len(non_constant_exps) >= num_additional_nonzero_needed:
        for _ in range(num_additional_nonzero_needed):
            guaranteed_nonzero_exps.add(non_constant_exps.pop())
    
    for exp in range(degree - 1, 0, -1):
        if exp in guaranteed_nonzero_exps:
            coeff = 0
            while coeff == 0:
                coeff = random.randint(coeff_range_min, coeff_range_max)
            terms.append((coeff, exp))
        else:
            # For remaining exponents, randomly decide if it's zero or non-zero
            coeff = random.randint(coeff_range_min, coeff_range_max)
            terms.append((coeff, exp))
    
    # 3. Constant term (can be zero)
    constant_coeff = random.randint(coeff_range_min, coeff_range_max)
    terms.append((constant_coeff, 0))
    
    # Verification step: Check min_nonzero_terms_excluding_constant
    actual_nonzero_non_constant_count = sum(1 for c, e in terms if c != 0 and e > 0)
    if actual_nonzero_non_constant_count < min_nonzero_terms_excluding_constant:
        return None # Indicate failure to meet criteria, caller should retry

    # Filter out zero terms for a clean internal representation, but keep (0,0) if it's the only result
    final_terms = [(c, e) for c, e in terms if c != 0]
    if not final_terms: # If all coefficients are zero after filtering
        return [(0,0)] # Represent as 0 polynomial
    
    # Ensure constant term is present if it's non-zero
    if constant_coeff != 0 and (constant_coeff, 0) not in final_terms:
        final_terms.append((constant_coeff, 0))
    
    final_terms.sort(key=lambda x: x[1], reverse=True)
    return final_terms


def generate(level=1, **kwargs):
    max_retries = 1000
    for _ in range(max_retries):
        try:
            # 1. Variable Generation (Entities & Constraints)
            original_degree = random.randint(3, 5) # polynomial_degree: 3~5
            
            # coefficients: -10~10, leading_coefficient_nonzero, minimum_nonzero_terms_excluding_constant: 3
            original_terms = _generate_polynomial_terms_with_constraints(
                original_degree, -10, 10, 3
            )
            
            if original_terms is None: # Helper function indicates failure to meet constraints
                continue

            # derivative_order_1: 1 ~ (polynomial_degree - 1)
            # Ensure there's at least one degree for order_2
            if original_degree - 1 < 1: # If original degree is 1 or 0, no valid order_1
                continue
            
            order_1 = random.randint(1, original_degree - 1)
            
            # derivative_order_2: (derivative_order_1 + 1) ~ (polynomial_degree - 1)
            # Ensure valid range for order_2 (must be strictly greater than order_1)
            if original_degree - 1 <= order_1: # No room for order_2 > order_1
                continue
            
            order_2 = random.randint(order_1 + 1, original_degree - 1)
            
            # 2. Operations (Python direct calculation)
            f_derivative_1_terms = _differentiate_poly(original_terms, order_1)
            f_derivative_2_terms = _differentiate_poly(original_terms, order_2)

            # Check coefficient limit for final derivatives
            coeff_exceeds_limit = False
            for term_list in [f_derivative_1_terms, f_derivative_2_terms]:
                for c, _ in term_list:
                    if abs(c) > 1000:
                        coeff_exceeds_limit = True
                        break
                if coeff_exceeds_limit:
                    break
            
            if coeff_exceeds_limit:
                continue # Retry if coefficients are too large

            # 3. Formatting
            # Question Text
            poly_str = _poly_to_latex(original_terms)
            
            # MASTER_SPEC requires f^{n}(x) directly, not _deriv_symbol_latex
            deriv_sym_1 = f"f^{{{fmt_num(order_1)}}}(x)"
            deriv_sym_2 = f"f^{{{fmt_num(order_2)}}}(x)"
            
            # CRITICAL: Do NOT call clean_latex_output for polynomial expressions with _poly_to_latex
            q = f"已知 $f(x) = {poly_str}$，求 ${deriv_sym_1}$ 與 ${deriv_sym_2}$。"
            
            # Answer Text
            poly_str_1_plain = _poly_to_plain(f_derivative_1_terms)
            poly_str_2_plain = _poly_to_plain(f_derivative_2_terms)
            
            # MASTER_SPEC requires f^(order)(x) directly for plain text
            answer_deriv_sym_1 = f"f^({order_1})(x)"
            answer_deriv_sym_2 = f"f^({order_2})(x)"
            
            a = f"{answer_deriv_sym_1} = {poly_str_1_plain}; {answer_deriv_sym_2} = {poly_str_2_plain}"
            
            # All checks passed, return the result
            return {
                'question_text': q,
                'correct_answer': a,
                'answer': a,
                'mode': 1
            }

        except ValueError as e:
            # If any ValueError (like coefficient limit during diff) occurs, retry
            continue
        except Exception as e:
            # Catch other unexpected errors during generation
            # print(f"Unexpected error during generation: {e}") # For debugging
            continue

    # If max_retries reached without success
    raise RuntimeError("Failed to generate a valid polynomial derivative problem after multiple attempts.")