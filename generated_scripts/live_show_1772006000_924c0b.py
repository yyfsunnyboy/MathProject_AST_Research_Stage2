
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
    question_text = ''  # [AST Fix: 安全初始化防護]
    a = random.randint(5, 12)
    b = random.randint(1, 10)
    c = random.randint(1, 10)
    d = random.randint(1, 10)
    e = random.randint(1, 10)
    f = random.randint(1, 10)
    g = random.randint(1, 10)
    h = random.randint(1, 10)
    i = random.randint(1, 10)
    j = random.randint(1, 10)
    k = random.randint(1, 10)
    l = random.randint(1, 10)
    m = random.randint(1, 10)
    n = random.randint(1, 10)
    o = random.randint(1, 10)
    p = random.randint(1, 10)
    q = random.randint(1, 10)
    r = random.randint(1, 10)
    s = random.randint(1, 10)
    t = random.randint(1, 10)
    u = random.randint(1, 10)
    v = random.randint(1, 10)
    w = random.randint(1, 10)
    x = random.randint(1, 10)
    y = random.randint(1, 10)
    z = random.randint(1, 10)
    terms = [f'{a} \\times {b}', f'{c} \\times {d}', f'{e} \\times {f}', f'{g} \\times {h}', f'{i} \\times {j}', f'{k} \\times {l}', f'{m} \\times {n}', f'{o} \\times {p}', f'{q} \\times {r}', f'{s} \\times {t}', f'{u} \\times {v}', f'{w} \\times {x}', f'{y} \\times {z}']
    question_text = FractionOps.format_shuffled_latex(terms)  # [AST Fix: 安全初始化防護]
    terms = [f'{a} \\times {b}', f'{c} \\times {d}', f'{e} \\times {f}', f'{g} \\times {h}', f'{i} \\times {j}', f'{k} \\times {l}', f'{m} \\times {n}', f'{o} \\times {p}', f'{q} \\times {r}', f'{s} \\times {t}', f'{u} \\times {v}', f'{w} \\times {x}', f'{y} \\times {z}']
    answer = FractionOps.format_shuffled_plain(terms)
    return {'question_text': question_text, 'answer': answer, 'correct_answer': answer, 'mode': 1}

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