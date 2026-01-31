# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V47.5 Unified-Cleanup + Advanced-Healer
# Ablation ID: 3 | Basic Cleanup: ENABLED | Advanced Healer: ON
# Performance: 52.20s | Tokens: In=5250, Out=2393
# Created At: 2026-01-31 00:01:56
# Fix Status: [Advanced Healer] | Fixes: Basic=1, Advanced=(Regex=13, AST=0)
# Verification: Internal Logic Check = FAILED
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

# Preloaded tools (assuming these are globally available as described in the prompt)
# fmt_num, to_latex, clean_latex_output, check, op_latex, etc.
# Mocking them here for standalone execution, but in the actual environment they are provided.


    
    # Ensure spaces around $ for readability and correct rendering
    q = re.sub(r'(\S)\$', r'\1 $', q)  # Add space before $ if not whitespace
    q = re.sub(r'\$(\S)', r'$ \1', q)  # Add space after $ if not whitespace
    
    # Specific rules for Chinese characters and $
    q = re.sub(r'([\u4e00-\u9fa5])\s*\$', r'\1 $', q) # Chinese char followed by $
    q = re.sub(r'\$\s*([\u4e00-\u9fa5])', r'$ \1', q) # $ followed by Chinese char
    
    # Remove redundant spaces
    q = re.sub(r'\s+', ' ', q).strip()
    
    return q

op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}

# Helper function to format polynomial terms into a LaTeX string
# Input: list of (coefficient, power) tuples, sorted high to low power
def format_poly_to_latex(terms):
    poly_parts = []
    
    # Filter out zero coefficient terms first to simplify logic
    filtered_terms = [(c, p) for c, p in terms if c != 0]

    if not filtered_terms:
        return "0" # If all terms are zero, the polynomial is 0

    for i, (coeff, power) in enumerate(filtered_terms):
        coeff_abs_str = fmt_num(abs(coeff))
        term_str = ""

        # Handle coefficient sign
        if coeff > 0 and i > 0: # Not the first term and positive
            poly_parts.append(op_latex['+'])
        elif coeff < 0: # Negative term
            poly_parts.append(op_latex['-'])
        
        # Handle coefficient value (1 or -1 for x terms) and power display
        if abs(coeff) == 1 and power != 0: # If coefficient is 1 or -1 and not a constant term
            if power == 1:
                term_str = "x"
            else:
                term_str = f"x^{{{power}}}"
        elif power == 0: # Constant term
            term_str = coeff_abs_str
        elif power == 1: # x term with coefficient other than 1 or -1
            term_str = f"{coeff_abs_str}x"
        else: # x^n term with coefficient other than 1 or -1
            term_str = f"{coeff_abs_str}x^{{{power}}}"
        
        poly_parts.append(term_str)
    
    return " ".join(poly_parts)

# Helper function to calculate the first derivative of a polynomial
# Input: poly_dict = {power: coefficient}
# Output: derived_poly_dict = {new_power: new_coefficient}
def calculate_derivative(poly_dict):
    derived_poly_dict = {}
    for power, coefficient in poly_dict.items():
        if power == 0:
            continue # Derivative of constant term is 0
        
        new_power = power - 1
        new_coefficient = coefficient * power
        
        if new_coefficient != 0:
            derived_poly_dict[new_power] = new_coefficient
            
    return derived_poly_dict

def generate(level=1, **kwargs):
    max_attempts = 1000
    for _ in range(max_attempts):
        try:
            # 1. Variable Generation (Strictly follow MASTER_SPEC)
            polynomial_degree = random.randint(3, 5)
            term_count = random.randint(3, 5)

            # Generate unique powers for the original polynomial
            powers = set()
            powers.add(polynomial_degree) # Ensure max degree is included
            while len(powers) < term_count:
                powers.add(random.randint(0, polynomial_degree - 1))
            
            # Sort powers in descending order
            sorted_powers = sorted(list(powers), reverse=True)

            original_polynomial_terms = []
            original_polynomial_dict = {}

            for p in sorted_powers:
                coeff = random.randint(-10, 10)
                # Ensure all generated terms have non-zero coefficients to meet term_count definition
                while coeff == 0:
                    coeff = random.randint(-10, 10)
                
                original_polynomial_terms.append((coeff, p))
                original_polynomial_dict[p] = coeff

            # Generate requested derivative orders
            max_deriv_order_possible = polynomial_degree - 1
            if max_deriv_order_possible < 1: # Should not happen with poly_degree 3-5
                raise ValueError("Polynomial degree too low for derivatives.")

            k1 = random.randint(1, max_deriv_order_possible)
            k2 = random.randint(1, max_deriv_order_possible)
            while k2 == k1: # Ensure distinct orders
                k2 = random.randint(1, max_deriv_order_possible)
            
            requested_derivative_orders = sorted([k1, k2])

            # 2. Operations (Calculate derivatives)
            current_poly_dict = dict(original_polynomial_dict) # Start with a copy
            results = {} # Stores {order: poly_dict}

            # Calculate derivatives up to the maximum requested order
            for order in range(1, max(requested_derivative_orders) + 1):
                current_poly_dict = calculate_derivative(current_poly_dict)
                
                if order in requested_derivative_orders:
                    # Check if the derivative resulted in a zero polynomial
                    if not current_poly_dict:
                        raise ValueError(f"Derivative of order {order} resulted in a zero polynomial.")
                    
                    # Check highest degree coefficient of this derivative
                    max_deriv_power = max(current_poly_dict.keys())
                    final_coeff = current_poly_dict[max_deriv_power]
                    
                    if final_coeff == 0:
                        raise ValueError(f"Derivative of order {order} has zero highest degree coefficient.")
                    
                    # Check coefficient magnitude constraint (absolute value not exceeding 3 digits)
                    if abs(final_coeff) >= 1000:
                        raise ValueError(f"Derivative of order {order} has coefficient {final_coeff} exceeding 3 digits.")
                    
                    results[order] = dict(current_poly_dict) # Store a copy

            # All checks passed, break the regeneration loop
            break
        except ValueError as e:
            # print(f"Regenerating problem: {e}") # For debugging purposes if needed
            continue
    else:
        # If loop finishes without breaking, it means max_attempts reached
        raise RuntimeError("Failed to generate a valid problem after multiple attempts.")

    # 4. Question Formatting
    poly_str = format_poly_to_latex(original_polynomial_terms)
    
    deriv_req_strs = []
    for order in requested_derivative_orders:
        if order == 1:
            deriv_req_strs.append("f'(x)")
        elif order == 2:
            deriv_req_strs.append("f''(x)")
        elif order == 3:
            deriv_req_strs.append("f'''(x)")
        else:
            deriv_req_strs.append(f"f^{{{order}}}(x)") # LaTeX for f^(n)(x)

    # 組合中文與數學式（手動加 $ $）
    q_str = f"已知 $f(x) = {poly_str}$, 求 {' 和 '.join(deriv_req_strs)}。"
    
    # 5. 最後清洗
    question_text = clean_latex_output(q_str)

    # 6. Answer Formatting
    answer_parts = []
    for order in requested_derivative_orders:
        deriv_poly_dict = results[order]
        # Convert dictionary to sorted (coefficient, power) list for formatting
        deriv_terms = sorted([(coeff, power) for power, coeff in deriv_poly_dict.items()], key=lambda x: x[1], reverse=True)
        
        deriv_str = format_poly_to_latex(deriv_terms)
        
        # Prepare derivative prefix for plain text answer
        deriv_prefix = ""
        if order == 1:
            deriv_prefix = "f'(x) = "
        elif order == 2:
            deriv_prefix = "f''(x) = "
        elif order == 3:
            deriv_prefix = "f'''(x) = "
        else:
            deriv_prefix = f"f^{{{order}}}(x) = " # Plain text, not LaTeX
        
        answer_parts.append(f"{deriv_prefix}{deriv_str}")
    
    answer = "\n".join(answer_parts)

    # 7. Return standard format
    return {
        'question_text': question_text,
        'answer': answer,
        'mode': 1
    }