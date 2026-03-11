import random
import math
from fractions import Fraction

# ==============================================================================
# [AUTO-INJECTED RESOURCE] IntegerOps
# ==============================================================================
class IntegerOps:
    """整數運算模組 - 支援格式化、絕對值等"""
    
    @staticmethod
    def op_to_latex(op_str):
        """將基礎運算符號轉成國中課本 LaTeX 顯示"""
        if op_str == '*': 
            return '\\times'
        if op_str == '/': 
            return '\\div'
        return op_str

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
        # 先將 LaTeX 符號與括號清理乾淨，轉為純 Python 計算式
        clean_expr = str(expr).replace('\\div', '/').replace('\\times', '*')
        clean_expr = clean_expr.replace('\\', '') # 移除殘留的反斜線
        # 移除方括號並替換為括號（如果需要）
        clean_expr = clean_expr.replace('[', '(').replace(']', ')')
        try:
            return eval(clean_expr, safe_dict)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expr} (cleaned: {clean_expr}). Error: {e}")


def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    for _ in range(200):
        v1 = IntegerOps.random_nonzero(1, 100) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 100)
        v2 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)
        v3 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)
        v4 = IntegerOps.random_nonzero(1, 15) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 15)
        v5 = IntegerOps.random_nonzero(1, 15) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 15)
        numerator = v1 * v2 - v3
        denominator = v4 * v5
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue
        final_ans = abs(numerator) // abs(denominator)
        if denominator < 0:
            final_ans = -final_ans
        eval_str = f'({v1} * {v2} - {v3}) / ({v4} * {v5})'
        math_str = f'\\left( {fmt(v1)} \\times {fmt(v2)} - {fmt(v3)} \\right) \\div {fmt(v4)} \\times {fmt(v5)}'
        ans = IntegerOps.safe_eval(eval_str)
        if abs(ans - round(ans)) < 1e-06:
            return {'question_text': '計算 $' + math_str + '$ 的值。', 'answer': '', 'correct_answer': str(int(round(ans))), 'mode': 1}
    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-06:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}