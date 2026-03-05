
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

def generate():
    import random
    from fractions import Fraction
    for _safety_loop_var in range(1000):
        a = Fraction(random.randint(-50, 50), random.randint(1, 10))
        b = Fraction(random.randint(-50, 50), random.randint(1, 10))
        c = Fraction(random.randint(-50, 50), random.randint(1, 10))
        d = Fraction(random.randint(-50, 50), random.randint(1, 10))
        e = Fraction(random.randint(-50, 50), random.randint(1, 10))
        f = Fraction(random.randint(-50, 50), random.randint(1, 10))
        g = Fraction(random.randint(-50, 50), random.randint(1, 10))
        try:
            if abs(a.numerator) > 50 or abs(b.numerator) > 50 or abs(c.numerator) > 50 or (abs(d.numerator) > 50) or (abs(e.numerator) > 50) or (abs(f.numerator) > 50) or (abs(g.numerator) > 50):
                continue
            part1 = f'\\frac{{{a.numerator}}}{{{a.denominator}}}'
            part2 = IntegerOps.fmt_num(b.numerator) if b.denominator == 1 else f'\\frac{{{b.numerator}}}{{{b.denominator}}}'
            part3 = f'|{IntegerOps.fmt_num(e.numerator)} \\times {IntegerOps.fmt_num(f.numerator)} - {IntegerOps.fmt_num(g.numerator)}|'
            math_str = f'\\left[{part1} \\div {part2}\\right] + {part3}'
            ans = a / b + abs(e * f - g)
            part4 = IntegerOps.fmt_num(c.numerator) if c.denominator == 1 else f'\\frac{{{c.numerator}}}{{{c.denominator}}}'
            part5 = f'|{IntegerOps.fmt_num(d.numerator)} \\times {IntegerOps.fmt_num(e.numerator)} - {IntegerOps.fmt_num(f.numerator)}|'
            math_str = f'\\left[{part1} - {part4}\\right] \\div {part2} + {part5}'
            ans = (a - c) / b + abs(d * e - f)
            part6 = IntegerOps.fmt_num(g.numerator) if g.denominator == 1 else f'\\frac{{{g.numerator}}}{{{g.denominator}}}'
            math_str = f'-\\left[{part1}\\right] + {part3} - \\left({IntegerOps.fmt_num(d.numerator)} \\div {IntegerOps.fmt_num(e.numerator)}\\right) + {part6}'
            ans = -a + abs(d * e - f) - d / e + g
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f'{ans.numerator}/{ans.denominator}'
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
            return {'question_text': f'計算 $' + math_str + '$ 的值。', 'answer': '', 'correct_answer': correct, 'mode': 1}
        except Exception:
            continue

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