
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

def generate(level=1, **kwargs):
    question_text = ''
    a = Fraction(random.randint(1, 10), 1)
    b = Fraction(random.randint(1, 10), 1)
    c = Fraction(random.randint(1, 10), 1)
    d = Fraction(random.randint(1, 10), 1)
    e = Fraction(random.randint(1, 10), 1)
    f = Fraction(random.randint(1, 10), 1)
    g = Fraction(random.randint(1, 10), 1)
    h = Fraction(random.randint(1, 10), 1)
    i = Fraction(random.randint(1, 10), 1)
    j = Fraction(random.randint(1, 10), 1)
    k = Fraction(random.randint(1, 10), 1)
    l = Fraction(random.randint(1, 10), 1)
    m = Fraction(random.randint(1, 10), 1)
    n = Fraction(random.randint(1, 10), 1)
    o = Fraction(random.randint(1, 10), 1)
    p = Fraction(random.randint(1, 10), 1)
    q = Fraction(random.randint(1, 10), 1)
    r = Fraction(random.randint(1, 10), 1)
    s = Fraction(random.randint(1, 10), 1)
    t = Fraction(random.randint(1, 10), 1)
    u = Fraction(random.randint(1, 10), 1)
    v = Fraction(random.randint(1, 10), 1)
    w = Fraction(random.randint(1, 10), 1)
    x = Fraction(random.randint(1, 10), 1)
    y = Fraction(random.randint(1, 10), 1)
    z = Fraction(random.randint(1, 10), 1)
    result = (a * b - c / d) * (e - f / g) + (h * i - j / k) * (l - m / n) + (o * p - q / r) * (s - t / u) + (v * w - x / y) * (z - Fraction(1, 1) / Fraction(1, 1))
    question_text = f'$$ \\left[{IntegerOps.fmt_num(a)} \\times {IntegerOps.fmt_num(b)} - {IntegerOps.fmt_num(c)} \\div \\left(-{IntegerOps.fmt_num(d)}\\right)\\right] \\times \\left[{IntegerOps.fmt_num(e)} - {IntegerOps.fmt_num(f)} \\div {IntegerOps.fmt_num(g)}\\right] + \\left[{IntegerOps.fmt_num(h)} \\times {IntegerOps.fmt_num(i)} - {IntegerOps.fmt_num(j)} \\div {IntegerOps.fmt_num(k)}\\right] \\times \\left[{IntegerOps.fmt_num(l)} - {IntegerOps.fmt_num(m)} \\div {IntegerOps.fmt_num(n)}\\right] + \\left[{IntegerOps.fmt_num(o)} \\times {IntegerOps.fmt_num(p)} - {IntegerOps.fmt_num(q)} \\div {IntegerOps.fmt_num(r)}\\right] \\times \\left[{IntegerOps.fmt_num(s)} - {IntegerOps.fmt_num(t)} \\div {IntegerOps.fmt_num(u)}\\right] + \\left[{IntegerOps.fmt_num(v)} \\times {IntegerOps.fmt_num(w)} - {IntegerOps.fmt_num(x)} \\div {IntegerOps.fmt_num(y)}\\right] \\times \\left[{IntegerOps.fmt_num(z)} - {IntegerOps.fmt_num(Fraction(1, 1))} \\div {IntegerOps.fmt_num(Fraction(1, 1))}\\right] $$'
    correct_answer = f'{result.numerator}/{result.denominator}' if result.denominator != 1 else f'{result.numerator}'
    return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}

def check(user_answer, correct_answer):
    try:
        user_result = Fraction(user_answer.replace(' ', ''))
        correct_result = Fraction(correct_answer.replace(' ', ''))
        return user_result == correct_result
    except:
        return False