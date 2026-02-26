
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
    question_text = ''
    op = random.choice(['+', '-', '*', '/'])
    v1 = Fraction(random.randint(-100, 100), 1)
    v2 = Fraction(random.randint(-100, 100), 1)
    v3 = Fraction(random.randint(-100, 100), 1)
    v4 = Fraction(random.randint(-100, 100), 1)
    v5 = Fraction(random.randint(-100, 100), 1)
    if op == '+':
        result = v1 + v2 + v3 + v4 + v5
    elif op == '-':
        result = v1 - v2 - v3 - v4 - v5
    elif op == '*':
        result = v1 * v2 * v3 * v4 * v5
    elif op == '/':
        if v2 == 0 or v3 == 0 or v4 == 0 or (v5 == 0):
            return generate()
        result = v1 / v2 / v3 / v4 / v5
    if result.denominator == 1:
        correct_answer = str(result.numerator)
    else:
        correct_answer = f'{result.numerator}/{result.denominator}'
    question_text = f'計算 $$ {IntegerOps.fmt_num(v1)} {op} {IntegerOps.fmt_num(v2)} {op} {IntegerOps.fmt_num(v3)} {op} {IntegerOps.fmt_num(v4)} {op} {IntegerOps.fmt_num(v5)} $$ 的值。'
    return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}

def check(user_answer, correct_answer):
    try:
        ua_str = str(user_answer).strip()
        ca_str = str(correct_answer).strip()
        if ua_str == ca_str:
            return {'correct': True, 'result': '正確'}
        ua = float(Fraction(ua_str))
        ca = float(Fraction(ca_str))
        if abs(ua - ca) < 1e-09:
            return {'correct': True, 'result': '正確'}
        return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}