
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

question_text = ''

def generate(level=1, **kwargs):
    a = IntegerOps.rand_nz(-100, 100)
    b = IntegerOps.rand_nz(-100, 100)
    c = IntegerOps.rand_nz(-100, 100)
    d = IntegerOps.rand_nz(-100, 100)
    e = IntegerOps.rand_nz(-100, 100)
    f = IntegerOps.rand_nz(-100, 100)
    g = IntegerOps.rand_nz(-100, 100)
    h = IntegerOps.rand_nz(-100, 100)
    i = IntegerOps.rand_nz(-100, 100)
    j = IntegerOps.rand_nz(-100, 100)
    k = IntegerOps.rand_nz(-100, 100)
    l = IntegerOps.rand_nz(-100, 100)
    m = IntegerOps.rand_nz(-100, 100)
    n = IntegerOps.rand_nz(-100, 100)
    o = IntegerOps.rand_nz(-100, 100)
    p = IntegerOps.rand_nz(-100, 100)
    q = IntegerOps.rand_nz(-100, 100)
    r = IntegerOps.rand_nz(-100, 100)
    s = IntegerOps.rand_nz(-100, 100)
    t = IntegerOps.rand_nz(-100, 100)
    u = IntegerOps.rand_nz(-100, 100)
    v = IntegerOps.rand_nz(-100, 100)
    w = IntegerOps.rand_nz(-100, 100)
    x = IntegerOps.rand_nz(-100, 100)
    y = IntegerOps.rand_nz(-100, 100)
    z = IntegerOps.rand_nz(-100, 100)
    expr1 = IntegerOps.fmt_num(a)
    expr2 = IntegerOps.fmt_num(b)
    expr3 = IntegerOps.fmt_num(c)
    expr4 = IntegerOps.fmt_num(d)
    expr5 = IntegerOps.fmt_num(e)
    expr6 = IntegerOps.fmt_num(f)
    expr7 = IntegerOps.fmt_num(g)
    expr8 = IntegerOps.fmt_num(h)
    expr9 = IntegerOps.fmt_num(i)
    expr10 = IntegerOps.fmt_num(j)
    expr11 = IntegerOps.fmt_num(k)
    expr12 = IntegerOps.fmt_num(l)
    expr13 = IntegerOps.fmt_num(m)
    expr14 = IntegerOps.fmt_num(n)
    expr15 = IntegerOps.fmt_num(o)
    expr16 = IntegerOps.fmt_num(p)
    expr17 = IntegerOps.fmt_num(q)
    expr18 = IntegerOps.fmt_num(r)
    expr19 = IntegerOps.fmt_num(s)
    expr20 = IntegerOps.fmt_num(t)
    expr21 = IntegerOps.fmt_num(u)
    expr22 = IntegerOps.fmt_num(v)
    expr23 = IntegerOps.fmt_num(w)
    expr24 = IntegerOps.fmt_num(x)
    expr25 = IntegerOps.fmt_num(y)
    expr26 = IntegerOps.fmt_num(z)
    exprs = [f'{expr1} \\div {expr2} \\times {expr3} - {expr4} \\div {expr5} \\times {expr6} + {expr7} \\div {expr8} \\times {expr9} - {expr10} \\div {expr11} \\times {expr12} + {expr13} \\div {expr14} \\times {expr15} - {expr16} \\div {expr17} \\times {expr18} + {expr19} \\div {expr20} \\times {expr21} - {expr22} \\div {expr23} \\times {expr24} + {expr25} \\div {expr26}']
    question_text = IntegerOps.format_shuffled_latex(exprs)
    ans = a // b * c - d // e * f + g // h * i - j // k * l + m // n * o - p // q * r + s // t * u - v // w * x + y // z
    return {'question_text': question_text, 'answer': '', 'correct_answer': IntegerOps.format_plain(ans), 'mode': 1}