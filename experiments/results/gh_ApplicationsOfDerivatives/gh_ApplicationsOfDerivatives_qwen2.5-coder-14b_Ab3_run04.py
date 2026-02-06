# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 3 | Basic Cleanup: ENABLED | Advanced Healer: ON
# Performance: 24.50s | Tokens: In=1592, Out=388
# Created At: 2026-02-06 10:44:36
# Fix Status: [Advanced Healer] | Fixes: Basic=1, Advanced=(Regex=1, AST=0)
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
import os

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

# 🔴 答案格式：純多項式逗號分隔（例："36x^2+10,72x"）
#    ✅ 用 _format_polynomial_for_answer() 組答案，再 ','.join()
#    ❌ 禁止：_deriv_symbol_plain() 只用於題目，不用於答案
#    ❌ 禁止：換行分隔 '\n'.join()

def _coeffs_to_terms(coeffs):
    '''係數列表 [a_n,...,a_0] → terms [(c,e),...]'''
    degree = len(coeffs) - 1
    return [(coeffs[i], degree - i) for i in range(len(coeffs))]

def _poly_to_latex(terms):
    '''terms → LaTeX (不含$)，例: [(3,2),(-5,0)] → "3x^{2} - 5"'''
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
    '''terms → 純文本答案格式 (無空格)，例: "3x^2-5"'''
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
    '''求導 order 次，返回新 terms'''
    result = list(terms)
    for _ in range(order):
        new_terms = []
        for c, e in result:
            if e > 0:
                new_c = c * e
                if abs(new_c) > 10000:
                    raise ValueError(f"Coefficient {new_c} exceeds limit")
                new_terms.append((new_c, e - 1))
        result = new_terms
    return result

def _deriv_symbol_latex(order):
    '''導數符號 LaTeX: f'(x), f''(x), f^{(n)}(x)'''
    if order == 1:
        return "f'(x)"
    elif order == 2:
        return "f''(x)"
    else:
        return f"f^{{({order})}}(x)"

def _deriv_symbol_plain(order):
    '''導數符號純文本: f'(x), f''(x), f^(n)(x)'''
    if order == 1:
        return "f'(x)"
    elif order == 2:
        return "f''(x)"
    else:
        return f"f^({order})(x)"

def _format_polynomial_for_answer(terms):
    '''Format polynomial terms for answer display - use plain text, no LaTeX brackets
    Examples:
      _format_polynomial_for_answer([(36, 3), (27, 2), (16, 1)]) → "36x^3+27x^2+16x"
      _format_polynomial_for_answer([(216, 1), (54, 0)]) → "216x+54"
    '''
    return _poly_to_plain(terms)



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


def generate(level=1, **kwargs):
    for _safety_counter in range(1000):
        degree = random.randint(3, 5)
        coeffs = [0] * (degree + 1)
        coeffs[degree] = random.randint(-10, 10)
        while coeffs[degree] == 0:
            coeffs[degree] = random.randint(1, 10)
        min_extra = 2
        max_extra = degree
        num_extra = random.randint(min_extra, max_extra)
        remaining_indices = list(range(degree))
        random.shuffle(remaining_indices)
        selected_indices = remaining_indices[:num_extra]
        for idx in selected_indices:
            c = random.randint(-10, 10)
            while c == 0:
                c = random.randint(-10, 10)
            coeffs[idx] = c
        terms = _coeffs_to_terms(coeffs)
        try:
            orders = list(range(1, degree))
            random.shuffle(orders)
            target_orders = sorted(orders[:2])
            deriv_results = []
            for order in target_orders:
                d_terms = _differentiate_poly(terms, order=order)
                deriv_results.append(d_terms)
        except ValueError:
            continue
        poly_latex = _poly_to_latex(terms)
        symbols = ' 與 '.join((f'${_deriv_symbol_latex(o)}$' for o in target_orders))
        q = f'已知 $f(x) = {poly_latex}$，求 {symbols}。'
        ans_parts = [_poly_to_plain(d) for d in deriv_results]
        a = ', '.join(ans_parts)
        return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}