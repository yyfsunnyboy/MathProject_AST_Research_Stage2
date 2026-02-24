import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def generate_fraction():
        numerator = random.randint(1, 10)
        denominator = random.randint(1, 10)
        if random.random() < 0.5:
            numerator = -numerator
        return f"{numerator}/{denominator}"

    def generate_operation():
        ops = ['+', '-']
        return random.choice(ops)

    def generate_abs_part():
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        op = random.choice(['*', '/'])
        return f"|{a}{op}{generate_fraction()} - {b}|"

    def generate_bracket_part():
        a = random.randint(-5, 5)
        b = random.randint(1, 5)
        op = random.choice(['+', '-'])
        return f"({a}{op}{b})"

    def generate_full_expression():
        part1 = generate_bracket_part()
        part2 = generate_fraction()
        part3 = generate_abs_part()
        op1 = random.choice(['*', '/'])
        op2 = random.choice(['+', '-'])
        return f"[{part1}{op1}{part2}]{op2}{part3}"

    question_text = generate_full_expression()
    expr = question_text.replace('÷', '/').replace('×', '*').replace('|', '')
    expr = expr.replace('÷', '/').replace('×', '*').replace('|', '')
    expr = expr.replace('÷', '/').replace('×', '*').replace('|', '')
    expr = expr.replace('÷', '/').replace('×', '*').replace('|', '')
    expr = expr.replace('÷', '/').replace('×', '*').replace('|', '')
    expr = expr.replace('÷', '/').replace('×', '*').replace('|', '')
    expr = expr.replace('÷', '/').replace('×', '*').replace('|', '')
    expr = expr.replace('÷', '/').

    correct_answer = eval(expr)
    correct_answer_str = str(correct_answer).replace('/', '⁄').replace(' ', '')
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_val = Fraction(user_answer.replace('⁄', '/'))
        correct_val = Fraction(correct_answer.replace('⁄', '/'))
        return {'correct': user_val == correct_val, 'result': '正確' if user_val == correct_val else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}