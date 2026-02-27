
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
    r_min, r_max, div_max = (0, 0, 0)
    if level == 1:
        r_min, r_max, div_max = (-20, 20, 10)
    elif level == 2:
        r_min, r_max, div_max = (-50, 50, 20)
    else:
        r_min, r_max, div_max = (-100, 100, 30)

    def rand_nz(a, b):
        return random.choice([x for x in range(a, b + 1) if x != 0])
    divisor = rand_nz(2, div_max)
    quotient = rand_nz(-15, 15)
    dividend = divisor * quotient
    m = rand_nz(2, 5)
    a_approx = dividend // m
    a = rand_nz(a_approx - 5, a_approx + 5)
    b = dividend - a * m
    part1_str = f'[({IntegerOps.fmt_num(a)} \\times {IntegerOps.fmt_num(m)}) + {IntegerOps.fmt_num(b)}] \\div {IntegerOps.fmt_num(divisor)}'
    part1_val = quotient
    d = rand_nz(-10, 15)
    e = rand_nz(-10, 10)
    f = rand_nz(1, 20)
    g = rand_nz(-10, 10)
    if level == 1:
        part2_str = f'|{IntegerOps.fmt_num(d)} \\times {IntegerOps.fmt_num(e)} - {IntegerOps.fmt_num(f)}|'
        part2_val = abs(d * e - f)
    else:
        part2_str = f'|{IntegerOps.fmt_num(d)} \\times {IntegerOps.fmt_num(e)} - {IntegerOps.fmt_num(f)} + {IntegerOps.fmt_num(g)}|'
        part2_val = abs(d * e - f + g)
    h = rand_nz(-10, 10)
    i = rand_nz(2, 5)