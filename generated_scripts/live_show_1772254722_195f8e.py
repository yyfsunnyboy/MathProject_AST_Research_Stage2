
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
    if level == 1:
        r_min, r_max = (-20, 20)
        div_max = 10
    elif level == 2:
        r_min, r_max = (-50, 50)
        div_max = 20
    else:
        r_min, r_max = (-100, 100)
        div_max = 30

    def rand_nz(a, b):
        choices = [x for x in range(a, b + 1) if x != 0]
        if not choices:
            return 1
        return random.choice(choices)
    divisor = rand_nz(2, div_max)
    quotient = rand_nz(-15, 15)
    dividend = divisor * quotient
    m = rand_nz(2, 5)
    a_approx = dividend // m
    if a_approx == 0:
        a_approx = 5
    a = rand_nz(a_approx - 5, a_approx + 5)
    b = dividend - a * m
    d = rand_nz(-10, 15)
    e = rand_nz(-10, 10)
    f = rand_nz(1, 20)
    g = rand_nz(-10, 10)
    h = rand_nz(-10, 10)
    i = rand_nz(2, 5)
    j = rand_nz(1, 10)
    k = rand_nz(-50, 50)
    fmt = IntegerOps.fmt_num
    part1_str = f'[({fmt(a)} \\times {fmt(m)}) + {fmt(b)}] \\div {fmt(divisor)}'
    part1_val = quotient
    if level == 1:
        part2_str = f'|{fmt(d)} \\times {fmt(e)} - {fmt(f)}|'
        part2_val = abs(d * e - f)
    else:
        part2_str = f'|{fmt(d)} \\times {fmt(e)} - {fmt(f)} + {fmt(g)}|'
        part2_val = abs(d * e - f + g)
    part3_str = f'({fmt(h)} \\times {fmt(i)} - {fmt(j)})'
    part3_val = h * i - j
    if level == 1:
        question_text = f'計算 $${part1_str} + {part2_str}$$ 的值。'  # [AST Fix: 安全初始化防護]
        ans = part1_val + part2_val
    elif level == 2:
        question_text = f'計算 $${part1_str} - {part2_str} + {part3_str}$$ 的值。'  # [AST Fix: 安全初始化防護]
        ans = part1_val - part2_val + part3_val
    else:
        question_text = f'計算 $$- {part1_str} + {part2_str} - {part3_str} + {fmt(k)}$$ 的值。'  # [AST Fix: 安全初始化防護]
        ans = -part1_val + part2_val - part3_val + k
    return {'question_text': question_text, 'answer': '', 'correct_answer': str(int(ans)), 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-06:
            return {'correct': True, 'result': '正確'}
    except:
        pass
    return {'correct': False, 'result': '錯誤'}