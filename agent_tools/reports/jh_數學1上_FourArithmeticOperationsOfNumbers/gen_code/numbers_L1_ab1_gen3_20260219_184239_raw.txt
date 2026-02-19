import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def generate_bracket():
        op = random.choice(['+', '-', '×', '÷'])
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        d = random.randint(1, 10)
        return f"({a} {op} {b}) × {c}/{d}"

    def generate_fraction_div():
        sign = random.choice(['', '-'])
        numerator = random.randint(1, 10)
        denominator = random.randint(1, 10)
        return f"{sign}{numerator}/{denominator}"

    def generate_abs():
        op = random.choice(['×', '÷'])
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        d = random.randint(1, 10)
        return f"{a} {op} (-{b}/{c}) - {d}"

    bracket_expr = generate_bracket()
    fraction_div_expr = generate_fraction_div()
    abs_expr = generate_abs()
    question_text = f"[{bracket_expr}] ÷ {fraction_div_expr} + |{abs_expr}|"
    
    def calculate(expr):
        expr = expr.replace('|', 'abs(').replace(')', ')')
        expr = expr.replace('÷', '/').replace('×', '*')
        try:
            result = eval(expr)
        except:
            result = None
        if isinstance(result, float):
            result = Fraction(result).limit_denominator()
        return str(result)
    
    correct_answer = calculate(question_text)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_result = Fraction(user_answer).limit_denominator()
        correct_result = Fraction(correct_answer).limit_denominator()
        return {'correct': user_result == correct_result, 'result': '正確' if user_result == correct_result else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}