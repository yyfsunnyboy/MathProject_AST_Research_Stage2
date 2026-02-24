import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-10, 11) if i != 0])
    q = random.randint(-10, 10)
    sum_ab = c * q
    a = random.randint(-30, 30)
    b = sum_ab - a
    d = random.randint(-10, 10)
    v1 = random.randint(-12, 12)
    v2 = random.randint(-12, 12)
    v3 = random.randint(-30, 30)
    op_abs = random.choice(['+', '-'])
    op_mid = random.choice(['+', '-'])
    def p(n):
        return f"({n})" if n < 0 else str(n)
    bracket_part = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}"
    abs_expr = f"|{v1}×{p(v2)}{op_abs}{p(v3)}|"
    val_bracket = q * d
    val_abs = abs(v1 * v2 + v3) if op_abs == '+' else abs(v1 * v2 - v3)
    if op_mid == '+':
        ans = val_bracket + val_abs
    else:
        ans = val_bracket - val_abs
    return {
        'question_text': f"計算 {bracket_part}{op_mid}{abs_expr} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }