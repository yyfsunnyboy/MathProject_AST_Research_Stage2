import random

def generate(level=1, **kwargs):
    n1 = random.randint(-50, 50)
    n2 = random.randint(-50, 50)
    op1 = random.choice(['+', '-'])
    v1 = n1 + n2 if op1 == '+' else n1 - n2
    ds = [i for i in range(-20, 21) if i != 0 and v1 % i == 0]
    if not ds: ds = [1]
    n3 = random.choice(ds)
    n4 = random.randint(-10, 10)
    n5 = random.randint(-15, 15)
    n6 = random.randint(-15, 15)
    n7 = random.randint(-50, 50)
    def f(x):
        if x < 0: return f"({x})"
        return str(x)
    expr = f"[{f(n1)}{op1}{f(n2)}]÷{f(n3)}×{f(n4)}+|{f(n5)}×{f(n6)}-{f(n7)}|"
    ans = (v1 // n3) * n4 + abs(n5 * n6 - n7)
    return {
        'question_text': f"計算 {expr} 的值。",
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