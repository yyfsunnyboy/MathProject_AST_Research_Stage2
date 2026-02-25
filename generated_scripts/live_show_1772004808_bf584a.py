
# ==============================================================================
# [AUTO-INJECTED RESOURCE] FractionOps
# ==============================================================================
class FractionOps:
    """分數運算模組 - 精確處理分數與浮點數混合運算"""
    
    @staticmethod
    def create(value, den=None):
        """
        建立分數，具備「型別智慧」
        - 如果提供兩個參數 (num, den)，直接建立 Fraction(num, den)
        - 如果輸入是 float，先轉 str 再轉 Fraction（避免浮點精度誤差）
        - 支援 str 輸入（如 "-0.6"）
        - 支援 Fraction、int、float 輸入
        
        範例：
            FractionOps.create(3, 2)    → Fraction(3, 2)
            FractionOps.create(-0.6)    → Fraction(-3, 5)
            FractionOps.create("-0.6")  → Fraction(-3, 5)
            FractionOps.create(3)       → Fraction(3, 1)
        """
        if den is not None:
            return Fraction(value, den)
        
        if isinstance(value, float):
            value_str = str(value)
            return Fraction(value_str).limit_denominator(10000)
        elif isinstance(value, str):
            return Fraction(value)
        elif isinstance(value, Fraction):
            return value
        else:
            return Fraction(value)
    
    @staticmethod
    def to_latex(val, mixed=False):
        """輸出 LaTeX 格式"""
        if isinstance(val, Fraction):
            if val.denominator == 1:
                return str(val.numerator)
            if mixed and abs(val.numerator) > val.denominator:
                whole = val.numerator // val.denominator
                remainder = abs(val.numerator) % val.denominator
                if remainder == 0:
                    return str(whole)
                if whole == 0:
                    return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
                sign = "-" if val < 0 else ""
                return f"{sign}{abs(whole)} \\frac{{{remainder}}}{{{val.denominator}}}"
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
        return str(val)

    # 為了與其他 Ops (PolynomialOps/RadicalOps/IntegerOps) 保持一致
    format_latex = to_latex
    
    @staticmethod
    def format_plain(val):
        """格式化為純文字輸出"""
        if isinstance(val, Fraction):
            if val.denominator == 1:
                return str(val.numerator)
            return f"{val.numerator}/{val.denominator}"
        return str(val)
    
    @staticmethod
    def add(a, b):
        """分數加法"""
        return a + b
    
    @staticmethod
    def sub(a, b):
        """分數減法"""
        return a - b
    
    @staticmethod
    def mul(a, b):
        """分數乘法"""
        return a * b
    
    @staticmethod
    def div(a, b):
        """分數除法"""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

def generate(level=1, **kwargs):
    question_text = ''
    a = random.randint(-20, 20)
    b = random.randint(-20, 20)
    c = random.randint(-20, 20)
    d = random.randint(-20, 20)
    e = random.randint(-20, 20)
    f = random.randint(-20, 20)
    g = random.randint(-20, 20)
    h = random.randint(-20, 20)
    i = random.randint(-20, 20)
    j = random.randint(-20, 20)
    k = random.randint(-20, 20)
    l = random.randint(-20, 20)
    m = random.randint(-20, 20)
    n = random.randint(-20, 20)
    o = random.randint(-20, 20)
    p = random.randint(-20, 20)
    q = random.randint(-20, 20)
    r = random.randint(-20, 20)
    s = random.randint(-20, 20)
    t = random.randint(-20, 20)
    u = random.randint(-20, 20)
    v = random.randint(-20, 20)
    w = random.randint(-20, 20)
    x = random.randint(-20, 20)
    y = random.randint(-20, 20)
    z = random.randint(-20, 20)
    question_text = f'計算 $$ {FractionOps.format_latex(a)} \\times {FractionOps.format_latex(b)} + \\left|{FractionOps.format_latex(c)} \\times {FractionOps.format_latex(d)} - {FractionOps.format_latex(e)}\\right| + {FractionOps.format_latex(f)} \\times {FractionOps.format_latex(g)} - \\left({FractionOps.format_latex(h)} \\div {FractionOps.format_latex(i)}\\right) + \\left|{FractionOps.format_latex(j)} \\times {FractionOps.format_latex(k)} - {FractionOps.format_latex(l)}\\right| \\times {FractionOps.format_latex(m)} - {FractionOps.format_latex(n)} \\times {FractionOps.format_latex(o)} + \\left({FractionOps.format_latex(p)} \\div {FractionOps.format_latex(q)}\\right) \\times {FractionOps.format_latex(r)} - \\left|{FractionOps.format_latex(s)} \\times {FractionOps.format_latex(t)} - {FractionOps.format_latex(u)}\\right| + {FractionOps.format_latex(v)} \\times {FractionOps.format_latex(w)} - {FractionOps.format_latex(x)} \\times {FractionOps.format_latex(y)} + \\left({FractionOps.format_latex(z)} \\div {FractionOps.format_latex(1)}\\right) $$ 的值。'
    result = a * b + abs(c * d - e) + f * g - h / i + abs(j * k - l) * m - n * o + p / q * r - abs(s * t - u) + v * w - x * y + z / 1
    if result.denominator == 1:
        correct_answer = str(result.numerator)
    else:
        correct_answer = f'{result.numerator}/{result.denominator}'
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