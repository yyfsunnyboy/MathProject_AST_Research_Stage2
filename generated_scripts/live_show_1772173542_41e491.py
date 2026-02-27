
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
    fmt = IntegerOps.fmt_num
    if level == 1:
        divisor = IntegerOps.random_nonzero(2, 10)
        quotient = random.randint(2, 10)
        dividend = divisor * quotient
        a = IntegerOps.random_nonzero(-10, 10)
        b = IntegerOps.random_nonzero(-10, 10)
        c = IntegerOps.random_nonzero(-10, 10)
        d = IntegerOps.random_nonzero(2, 10)
        ans = a * b - c // d
        display_expr = f'{fmt(a)} \times {fmt(b)} - {fmt(c)} \\div {fmt(d)}'
    elif level == 3:
        divisor1 = IntegerOps.random_nonzero(2, 10)
        quotient1 = random.randint(2, 10)
        dividend1 = divisor1 * quotient1
        divisor2 = IntegerOps.random_nonzero(2, 10)
        quotient2 = random.randint(2, 10)
        dividend2 = divisor2 * quotient2
        a = IntegerOps.random_nonzero(-10, 10)
        b = IntegerOps.random_nonzero(-10, 10)
        c = IntegerOps.random_nonzero(-10, 10)
        d = divisor1
        e = IntegerOps.random_nonzero(-10, 10)
        f = IntegerOps.random_nonzero(-10, 10)
        g = IntegerOps.random_nonzero(-10, 10)
        h = divisor2
        part1 = abs(a * (b - c) // d)
        part2 = e * f
        part3 = g // h
        ans = part1 + part2 - part3
        display_expr = f'|{fmt(a)} \times ({fmt(b)} - {fmt(c)}) \\div {fmt(d)}| + {fmt(e)} \times {fmt(f)} - {fmt(g)} \\div {fmt(h)}'
    else:
        pass
    return {'question_text': f'計算 $${display_expr}$$ 的值。', 'answer': '', 'correct_answer': str(int(ans)), 'mode': 1}