
# ==============================================================================
# [AUTO-INJECTED RESOURCE] IntegerOps
# ==============================================================================
class IntegerOps:
    """整數運算模組 - 支援格式化、絕對值等"""
    
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
        expr = expr.replace('[', '(').replace(']', ')')
        try:
            return eval(expr, safe_dict)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expr}. Error: {e}")

def generate(level=1, **kwargs):
    question_text = ''
    r_min, r_max, div_max = (-20, 20, 10) if level == 1 else (-50, 50, 20) if level == 2 else (-100, 100, 30)
    divisor = random.randint(2, div_max)
    quotient = random.randint(-15, 15)
    dividend = divisor * quotient
    m = random.randint(2, 5)
    a_approx = dividend // m
    a = random.randint(a_approx - 5, a_approx + 5)
    b = dividend - a * m
    d = random.randint(-10, 15)
    e = random.randint(-10, 10)
    f = random.randint(1, 20)
    g = random.randint(-10, 10)
    h = random.randint(-10, 10)
    i = random.randint(2, 5)
    j = random.randint(1, 10)
    k = random.randint(-50, 50)
    part1_str = format_latex(f'[({IntegerOps.fmt_num(a)} \\times {IntegerOps.fmt_num(m)}) + {IntegerOps.fmt_num(b)}] \\div {IntegerOps.fmt_num(divisor)}')
    part2_str = format_latex(f'|{IntegerOps.fmt_num(d)} \\times {IntegerOps.fmt_num(e)} - {IntegerOps.fmt_num(f)}|')
    part3_str = format_latex(f'({IntegerOps.fmt_num(h)} \\times {IntegerOps.fmt_num(i)} - {IntegerOps.fmt_num(j)})')
    if level == 1:
        question_text = format_latex(f'計算 $${part1_str} + {part2_str}$$ 的值。')
        ans = quotient + abs(d * e - f)
    elif level == 2:
        question_text = format_latex(f'計算 $${part1_str} - {part2_str} + {part3_str}$$ 的值。')
        ans = quotient - abs(d * e - f) + (h * i - j)
    else:
        question_text = format_shuffled_latex([f'- {part1_str}', part2_str, f'- {part3_str}', IntegerOps.fmt_num(k)])
        ans = -quotient + abs(d * e - f - g) - (h * i - j) + k
    return {'question_text': question_text, 'answer': '', 'correct_answer': format_plain(ans), 'mode': 1}