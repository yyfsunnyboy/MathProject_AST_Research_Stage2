

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

def random_nonzero(min_val, max_val):
    """
    [Auto-Injected] 產生非零隨機整數
    """
    val = 0
    while val == 0:
        val = random.randint(min_val, max_val)
    return val

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
            if isinstance(node.func, ast.Name):
                if node.func.id == 'Fraction':
                    args = [_eval(a) for a in node.args]
                    return Fraction(*args)
                elif node.func.id == 'abs':
                    return abs(_eval(node.args[0]))
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


# [DOMAIN HELPERS - Auto-Injected for jh_數學1上_FourArithmeticOperationsOfIntegers]

# ==============================================================================
# [AUTO-INJECTED RESOURCE] RadicalOps
# ==============================================================================
class RadicalOps:
    """根號運算模組 - 化簡與精確計算"""
    
    @staticmethod
    def create(inner):
        """建立根號 sqrt(inner) 並自動化簡"""
        if inner < 0:
            raise ValueError("Cannot take square root of negative number")
        if inner == 0:
            return "0"
        
        i = int(math.sqrt(inner))
        while i > 1:
            if inner % (i * i) == 0:
                sqrt_val = i
                remainder = inner // (i * i)
                if remainder == 1:
                    return str(sqrt_val)
                return f"{sqrt_val}√{remainder}"
            i -= 1
        
        return f"√{inner}"
    
    @staticmethod
    def is_perfect_square(n):
        """檢查 n 是否為完全平方數"""
        if n < 0:
            return False
        sqrt = int(n ** 0.5)
        return sqrt * sqrt == n
    
    @staticmethod
    def to_latex(expr):
        """輸出根號的 LaTeX 格式"""
        return f"\\sqrt{{{expr}}}"

    @staticmethod
    def get_prime_factors(n):
        """質因數分解 (例: 12 -> {2:2, 3:1})"""
        n = abs(int(n))
        factors = {}
        d = 2
        temp = n
        while d * d <= temp:
            while temp % d == 0:
                factors[d] = factors.get(d, 0) + 1
                temp //= d
            d += 1
        if temp > 1:
            factors[temp] = factors.get(temp, 0) + 1
        return factors

    @staticmethod
    def simplify_term(coeff, radicand):
        """化簡單項根式 c√r -> (new_c, new_r)"""
        radicand = int(radicand)
        if radicand == 0: return 0, 1
        if radicand == 1: return coeff, 1
        factors = RadicalOps.get_prime_factors(radicand)
        out_factor = 1
        new_radicand = 1
        for p, exp in factors.items():
            out_factor *= p**(exp // 2)
            new_radicand *= p**(exp % 2)
        return coeff * out_factor, new_radicand

    @staticmethod
    def format_term(coeff, radicand, is_first=True):
        """格式化單項根式 (LaTeX)"""
        if coeff == 0: return ""
        c_val, r_val = RadicalOps.simplify_term(coeff, radicand)
        if r_val == 1:
            if is_first: return str(c_val)
            return f" + {c_val}" if c_val > 0 else f" - {-c_val}"
        
        sign = ""
        if not is_first:
            sign = " + " if c_val > 0 else " - "
        elif c_val < 0:
            sign = "-"
            
        abs_c = abs(c_val)
        c_str = "" if abs_c == 1 else str(abs_c)
        return f"{sign}{c_str}\\sqrt{{{r_val}}}"

    @staticmethod
    def format_term_unsimplified(coeff, radicand, is_first=True):
        """格式化單項根式 (不化簡，用於題目展示)"""
        if coeff == 0: return ""
        
        sign = ""
        if not is_first:
            sign = " + " if coeff > 0 else " - "
        elif coeff < 0:
            sign = "-"
            
        abs_c = abs(coeff)
        c_str = "" if abs_c == 1 else str(abs_c)
        return f"{sign}{c_str}\\sqrt{{{radicand}}}"

    @staticmethod
    def format_expression(terms_dict, denominator=1):
        """格式化多項根式表達式 (terms_dict: {radicand: coeff})"""
        if not terms_dict: return "0"
        
        # 1. 內部化簡合併
        simplified = {}
        for r, c in terms_dict.items():
            if c == 0: continue
            c_s, r_s = RadicalOps.simplify_term(c, r)
            simplified[r_s] = simplified.get(r_s, 0) + c_s
        
        simplified = {r: c for r, c in simplified.items() if c != 0}
        if not simplified: return "0"
        
        # 2. 處理分母約分
        if denominator != 1:
            import math
            all_coeffs = [int(c) for c in simplified.values()]
            common = abs(int(denominator))
            for c in all_coeffs:
                common = math.gcd(common, abs(c))
            if common > 1:
                denominator //= common
                for r in simplified:
                    simplified[r] //= common
        
        # 3. 排序 (整數項 radicand=1 排最前，其他從小到大)
        sorted_rads = sorted(simplified.keys())
        if 1 in sorted_rads:
            sorted_rads.remove(1)
            sorted_rads.insert(0, 1)
            
        # 4. 生成字串
        parts = []
        is_first = True
        for r in sorted_rads:
            term_str = RadicalOps.format_term(simplified[r], r, is_first)
            if term_str:
                parts.append(term_str)
                is_first = False
                
        final_str = "".join(parts).lstrip()
        
        if denominator == 1 or not final_str:
            return final_str if final_str else "0"
        return f"\\frac{{{final_str}}}{{{denominator}}}"

# [Global Aliases for AI Convenience]
simplify_term = RadicalOps.simplify_term
format_term = RadicalOps.format_term
format_term_unsimplified = RadicalOps.format_term_unsimplified
format_expression = RadicalOps.format_expression


# ==============================================================================
# [AUTO-INJECTED RESOURCE] IntegerOps
# ==============================================================================
class IntegerOps:
    """整數運算模組 - 支援格式化、絕對值等"""
    
    @staticmethod
    def fmt_num(n):
        """格式化數字，為負數自動加括號"""
        try:
            if float(n) < 0:
                return f"({n})"
        except (ValueError, TypeError):
            if str(n).strip().startswith("-"):
                return f"({n})"
        return str(n)
    
    @staticmethod
    def rand_nz(a, b):
        """生成非零、非 ±1 的隨機整數"""
        choices = [x for x in range(a, b + 1) if x != 0 and x not in [1, -1]]
        if not choices:
            return 2
        return random.choice(choices)
    
    @staticmethod
    def is_divisible(a, b):
        """檢查 a 是否能被 b 整除"""
        if b == 0:
            return False
        return a % b == 0
    
    @staticmethod
    def safe_eval(expr):
        """安全評估算式，支援：abs()、基本四則運算、括號"""
        safe_dict = {
            '__builtins__': {},
            'abs': abs,
            'sum': sum,
            'max': max,
            'min': min,
        }
        expr = expr.replace('[', '(').replace(']', ')')
        expr = expr.replace('\\times', '*').replace('\\div', '/')
        expr = expr.replace('{', '').replace('}', '')
        expr = expr.replace(' ', '')
        try:
            return eval(expr, safe_dict)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expr}. Error: {e}")

    @staticmethod
    def format_latex(val):
        """格式化為 LaTeX 輸出，為了與 PolynomialOps/RadicalOps 介面一致"""
        return IntegerOps.fmt_num(val)
        
    @staticmethod
    def format_plain(val):
        """格式化為純文字輸出，為了與 PolynomialOps/RadicalOps 介面一致"""
        return str(val)


# [AI GENERATED CODE]
# ---------------------------------------------------------


# 數學題目生成器(整數四則運算)

## 題目生成邏輯說明

## 生成的題目範例
### Level 1(兩項運算)

### Level 2(三項混合運算)

### Level 3(四項混合運算)

## 生成的題目範例(除法)
### Level 1(兩項運算)

### Level 2(三項混合運算)

### Level 3(四項混合運算)

## 生成的題目範例(加減乘除混合)
### Level 3(四項混合運算)

## 生成的題目範例(乘除混合)
### Level 2(三項混合運算)

## 生成的題目範例(加減混合)
### Level 3(四項混合運算)

## 生成的題目範例(乘法)
### Level 1(兩項運算)

## 生成的題目範例(除法)
### Level 1(兩項運算)

## 生成的題目範例(加減乘除混合)
### Level 3(四項混合運算)

## 生成的題目範例(乘除混合)
### Level 2(三項混合運算)

## 生成的題目範例(加減混合)
### Level 3(四項混合運算)