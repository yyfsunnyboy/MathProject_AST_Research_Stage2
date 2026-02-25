
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
    if level == 1:
        a = IntegerOps.rand_nz(-20, 20)
        b = IntegerOps.rand_nz(-20, 20)
        c = IntegerOps.rand_nz(-20, 20)
        d = IntegerOps.rand_nz(-20, 20)
        part1 = IntegerOps.fmt_num(a)
        part2 = IntegerOps.fmt_num(b)
        part3 = IntegerOps.fmt_num(c)
        part4 = IntegerOps.fmt_num(d)
        question_text = f'計算 $${part1} + {part2} \\times {part3} - {part4}$$ 的值。'
        answer = a + b * c - d
    elif level == 2:
        a = IntegerOps.rand_nz(-50, 50)
        b = IntegerOps.rand_nz(-50, 50)
        c = IntegerOps.rand_nz(-50, 50)
        d = IntegerOps.rand_nz(-50, 50)
        part1 = IntegerOps.fmt_num(a)
        part2 = IntegerOps.fmt_num(b)
        part3 = IntegerOps.fmt_num(c)
        part4 = IntegerOps.fmt_num(d)
        question_text = f'計算 $${part1} - {part2} \\div {part3} + {part4}$$ 的值。'
        answer = a - b / c + d
    elif level == 3:
        a = IntegerOps.rand_nz(-100, 100)
        b = IntegerOps.rand_nz(-100, 100)
        c = IntegerOps.rand_nz(-100, 100)
        d = IntegerOps.rand_nz(-100, 100)
        part1 = IntegerOps.fmt_num(a)
        part2 = IntegerOps.fmt_num(b)
        part3 = IntegerOps.fmt_num(c)
        part4 = IntegerOps.fmt_num(d)
        question_text = f'計算 $${part1} \\div {part2} \\times {part3} - {part4}$$ 的值。'
        answer = a / b * c - d
    correct_answer = IntegerOps.format_plain(answer)
    return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}