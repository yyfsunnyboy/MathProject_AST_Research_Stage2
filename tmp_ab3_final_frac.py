
# ==============================================================================
# [AUTO-INJECTED RESOURCE] FractionOps
# ==============================================================================
class FractionOps:
    """分數運算模組 - 精確處理分數與浮點數混合運算"""
    
    @staticmethod
    def create(value):
        """
        建立分數，具備「型別智慧」
        - 如果輸入是 float，先轉 str 再轉 Fraction（避免浮點精度誤差）
        - 支援 str 輸入（如 "-0.6"）
        - 支援 Fraction、int、float 輸入
        
        範例：
            FractionOps.create(-0.6)    → Fraction(-3, 5)
            FractionOps.create("-0.6")  → Fraction(-3, 5)
            FractionOps.create(3)       → Fraction(3, 1)
        """
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

def generate():
    import random
    from fractions import Fraction
    
    
        elif mixed:
            whole = val.numerator // val.denominator
            frac = Fraction(val.numerator % val.denominator, val.denominator)
            return f"{whole}\\frac{{{frac.numerator}}}{{{frac.denominator}}}"
        else:
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
    
    while True:
        try:
            # Level 1: [Part1] ÷ Part2 + |Part3|
            part1_num = random.randint(-50, 50)
            part1_den = random.choice([2, 3, 4, 5])
            part1 = Fraction(part1_num, part1_den)
            
            part2_num = random.randint(1, 10)
            part2_den = random.choice([2, 3, 4, 5])
            part2 = Fraction(part2_num, part2_den)
            
            part3_num = random.randint(-50, 50)
            part3_den = random.choice([2, 3, 4, 5])
            part3 = Fraction(abs(part3_num), part3_den)
            
            # Calculate answer
            ans = (part1 / part2) + part3
            
            # Format question
            q_part1 = FractionOps.to_latex(part1)
            q_part2 = FractionOps.to_latex(part2)
            q_part3 = FractionOps.to_latex(part3, mixed=True)
            
            math_str = f"\\left[{q_part1}\\right] \\div {q_part2} + \\left|{q_part3}\\right|"
            
            # Format answer
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            # Check constraints
            if (abs(ans.numerator) > 120 or ans.denominator > 30 or 
                any(abs(x.numerator) > 50 for x in [part1, part2, part3])):
                continue
            
            return {
                'question_text': f'計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct,
                'mode': 1
            }
        except Exception:
            continue

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if Fraction(ua) == Fraction(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}
