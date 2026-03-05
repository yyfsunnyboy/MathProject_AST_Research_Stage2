import random
import math
from fractions import Fraction

# ==============================================================================
# [AUTO-INJECTED RESOURCE] IntegerOps
# ==============================================================================
class IntegerOps:
    """整數運算模組 - 支援格式化、絕對值等"""
    
    @staticmethod
    def op_to_latex(op_str):
        """將基礎運算符號轉成國中課本 LaTeX 顯示"""
        if op_str == '*': 
            return '\\times'
        if op_str == '/': 
            return '\\div'
        return op_str

    @staticmethod
    def fmt_num(n):
        """格式化數字，為負數自動加括號"""
        if n < 0:
            return f"({n})"
        return str(n)
    
    @staticmethod
    def random_nonzero(min_val, max_val):
        """生成非零隨機整數"""
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        if not available:
            raise ValueError(f"No non-zero integers in range [{min_val}, {max_val}]")
        return random.choice(available)
    
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
        # 先將 LaTeX 符號與括號清理乾淨，轉為純 Python 計算式
        clean_expr = str(expr).replace('\\div', '/').replace('\\times', '*')
        clean_expr = clean_expr.replace('\\', '') # 移除殘留的反斜線
        # 移除方括號並替換為括號（如果需要）
        clean_expr = clean_expr.replace('[', '(').replace(']', ')')
        try:
            return eval(clean_expr, safe_dict)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expr} (cleaned: {clean_expr}). Error: {e}")

# ==============================================================================
# [AUTO-INJECTED RESOURCE] FractionOps
# ==============================================================================
class FractionOps:
    """分數運算模組 - 精確處理分數與浮點數混合運算"""
    
    @staticmethod
    def create(value):
        """
        建立分數，具備「型別智慧」
        - 如果輸入是 float，先轉 str 再轉 Fraction（避免浮點精度誤差）
        - 支援 str 輸入（如 "-0.6"）
        - 支援 Fraction、int、float 輸入
        
        範例：
            FractionOps.create(-0.6)    → Fraction(-3, 5)
            FractionOps.create("-0.6")  → Fraction(-3, 5)
            FractionOps.create(3)       → Fraction(3, 1)
        """
        if isinstance(value, float):
            value_str = str(value)
            return Fraction(value_str).limit_denominator(10000)
        elif isinstance(value, str):
            return Fraction(value)
        elif isinstance(value, Fraction):
            return value
        else:
            return Fraction(value)
    
    @staticmethod
    def to_latex(val, mixed=False):
        """輸出 LaTeX 格式"""
        if isinstance(val, Fraction):
            if val.denominator == 1:
                return str(val.numerator)
            if mixed and abs(val.numerator) > val.denominator:
                whole = val.numerator // val.denominator
                remainder = abs(val.numerator) % val.denominator
                if remainder == 0:
                    return str(whole)
                if whole == 0:
                    return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
                sign = "-" if val < 0 else ""
                return f"{sign}{abs(whole)} \\frac{{{remainder}}}{{{val.denominator}}}"
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
        return str(val)
    
    @staticmethod
    def add(a, b):
        """分數加法"""
        return a + b
    
    @staticmethod
    def sub(a, b):
        """分數減法"""
        return a - b
    
    @staticmethod
    def mul(a, b):
        """分數乘法"""
        return a * b
    
    @staticmethod
    def div(a, b):
        """分數除法"""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b


def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    if level == 1:
        n_min, n_max = (-50, 50)
        d_min, d_max = (-10, 10)
    elif level == 2:
        n_min, n_max = (-50, 50)
        d_min, d_max = (-10, 10)
    else:
        n_min, n_max = (-50, 50)
        d_min, d_max = (-10, 10)

    def rand_frac():
        num = IntegerOps.random_nonzero(n_min, n_max)
        den = random.randint(d_min, d_max)
        while den == 0 or abs(den) == 1:
            den = random.randint(d_min, d_max)
        return Fraction(num, den)

    def latex_frac_clean(x):
        x = Fraction(x)
        if x.denominator == 1:
            return str(x.numerator)
        return FractionOps.to_latex(x)
    for _ in range(40):
        try:
            a = rand_frac()
            b = rand_frac()
            c = rand_frac()
            d = rand_frac()
            e = rand_frac()
            f = rand_frac()
            g = rand_frac()
            h = rand_frac()
            if c == 0 or f == 0:
                continue
            p1_val = (a + b) * c
            p2_val = d
            p3_val = abs(e * f - g)
            p1_str = f'\\left[{latex_frac_clean(a)} + {latex_frac_clean(b)}\\right] \\times {latex_frac_clean(c)}'
            p2_str = f'\\left({latex_frac_clean(p2_val)}\\right)'
            p3_str = f'\\left|{latex_frac_clean(e)} \\times {latex_frac_clean(f)} - {latex_frac_clean(g)}\\right|'
            if level == 1:
                math_str = f'\\left[{p1_str}\\right] \\div {p2_str} + {p3_str}'
                ans = Fraction(p1_val, 1) / p2_val + p3_val
            elif level == 2:
                p4_val = abs(a - b / c)
                p4_str = f'\\left|{latex_frac_clean(a)} - {latex_frac_clean(b)} \\div {latex_frac_clean(c)}\\right|'
                math_str = f'\\left[{p1_str} - {latex_frac_clean(h)}\\right] \\div {p2_str} + {p4_str}'
                ans = (p1_val - h) / p2_val + p4_val
            else:
                p4_val = h
                p4_str = latex_frac_clean(p4_val)
                math_str = f'-\\left[{p1_str}\\right] + {p3_str} - \\left({latex_frac_clean(d)} \\div {latex_frac_clean(f)}\\right) + {p4_str}'
                ans = -p1_val + p3_val - d / f + p4_val
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f'{ans.numerator}/{ans.denominator}'
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
            if any((abs(x.numerator) > 50 for x in [a, b, c, d, e, f, g, h])):
                continue
            return {'question_text': f'計算 $' + math_str + '$ 的值。', 'answer': '', 'correct_answer': correct, 'mode': 1}
        except Exception:
            continue
    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if Fraction(ua) == Fraction(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}