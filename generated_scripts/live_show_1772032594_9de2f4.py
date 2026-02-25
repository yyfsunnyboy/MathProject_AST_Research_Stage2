
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

def generate(**kwargs):
    level = kwargs.get('level', 1)
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
        choices = [x for x in range(a, b + 1) if x != 0 and x not in [1, -1]]
        if not choices:
            return 2
        return random.choice(choices)
    if level == 1:
        op = random.choice(['*', '/'])
        if op == '*':
            a = rand_nz(-15, 15)
            b = rand_nz(-10, 10)
            ans = a * b
        else:
            b = rand_nz(-15, 15)
            ans = rand_nz(-10, 10)
            a = b * ans
    elif level == 2:
        b = rand_nz(-15, 15)
        temp_ans = rand_nz(-15, 15)
        a = b * temp_ans
        c = rand_nz(-10, 10)
        if random.choice([True, False]):
            ans = a // b * c
        else:
            c2 = rand_nz(-15, 15)
            q = rand_nz(-5, 5)
            b2 = c2 * q
            a2 = rand_nz(-10, 10)
            ans = a2 * (b2 // c2)
    elif random.choice([True, False]):
        a = rand_nz(-10, 10)
        b = rand_nz(-10, 10)
        d = rand_nz(-15, 15)
        q = rand_nz(-10, 10)
        c = d * q
        ans = a * b + c // d
    else:
        a = rand_nz(-20, 20)
        c = rand_nz(-15, 15)
        q = rand_nz(-10, 10)
        b = c * q
        d = rand_nz(-10, 10)
        ans = a - b // c * d
    fmt = IntegerOps.fmt_num
    if level == 1:
        if op == '*':
            question_text = f'計算 $${fmt(a)} \\times {fmt(b)}$$ 的值。'  # [AST Fix: 安全初始化防護]
        else:
            question_text = f'計算 $${fmt(a)} \\div {fmt(b)}$$ 的值。'  # [AST Fix: 安全初始化防護]
    elif level == 2:
        if random.choice([True, False]):
            question_text = f'計算 $${fmt(a)} \\div {fmt(b)} \\times {fmt(c)}$$ 的值。'  # [AST Fix: 安全初始化防護]
        else:
            question_text = f'計算 $${fmt(a2)} \\times {fmt(b2)} \\div {fmt(c2)}$$ 的值。'  # [AST Fix: 安全初始化防護]
    elif random.choice([True, False]):
        question_text = f'計算 $${fmt(a)} \\times {fmt(b)} + {fmt(c)} \\div {fmt(d)}$$ 的值。'  # [AST Fix: 安全初始化防護]
    else:
        question_text = f'計算 $${fmt(a)} - {fmt(b)} \\div {fmt(c)} \\times {fmt(d)}$$ 的值。'  # [AST Fix: 安全初始化防護]
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