
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
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        op1 = random.choice(['+', '-', '*', '÷'])
        op2 = random.choice(['+', '-', '*', '÷'])
        expr = f'({IntegerOps.fmt_num(a)} {op1} {IntegerOps.fmt_num(b)}) {op2} |{IntegerOps.fmt_num(a - b)}|'
        answer = IntegerOps.safe_eval(expr)
        return {'question_text': expr, 'answer': '', 'correct_answer': str(answer), 'mode': 1}
    elif level == 3:

        def generate_sub_expr():
            a = random.randint(-5, 5)
            b = random.randint(-5, 5)
            op = random.choice(['+', '-', '*', '÷'])
            return f'{IntegerOps.fmt_num(a)} {op} {IntegerOps.fmt_num(b)}'
        expr1 = generate_sub_expr()
        expr2 = generate_sub_expr()
        expr = f"|{expr1}| {random.choice(['+', '-', '*', '÷'])} |{expr2}|"
        answer = IntegerOps.safe_eval(expr)
        return {'question_text': expr, 'answer': '', 'correct_answer': str(answer), 'mode': 1}
    else:
        return {'question_text': '系統連線測試成功！', 'answer': '', 'correct_answer': '100', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if float(user_answer) == float(correct_answer):
            return {'correct': True, 'result': '正確'}
    except:
        pass
    return {'correct': False, 'result': '錯誤'}