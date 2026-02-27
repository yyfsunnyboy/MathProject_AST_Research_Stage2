
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
        divisor1 = random.randint(1, 10)
        quotient1 = random.randint(1, 10)
        dividend1 = divisor1 * quotient1
        divisor2 = random.randint(1, 10)
        quotient2 = random.randint(1, 10)
        dividend2 = divisor2 * quotient2
    elif level == 3:
        divisor1 = random.randint(-50, -10)
        quotient1 = random.randint(1, 10)
        dividend1 = divisor1 * quotient1
        divisor2 = random.randint(1, 10)
        quotient2 = random.randint(-10, -1)
        dividend2 = divisor2 * quotient2
    expr = f'{fmt(dividend1)} \\div {fmt(divisor1)} - {fmt(dividend2)} \\div {fmt(divisor2)}'
    ans = IntegerOps.safe_eval(expr)
    return {'question_text': f'計算 $${expr}$$ 的值。', 'answer': '', 'correct_answer': str(int(ans)), 'mode': 1}

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip()}
    except:
        return {'correct': False}