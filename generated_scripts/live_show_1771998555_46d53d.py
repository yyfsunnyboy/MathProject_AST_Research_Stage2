import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt(f):
        s = f"{f.numerator}/{f.denominator}" if f.denominator != 1 else str(f.numerator)
        return f"({s})" if f < 0 else s
    def get_f():
        return Fraction(random.randint(-10, 10), random.randint(1, 10))
    ops = [('+', lambda x,y: x+y), ('-', lambda x,y: x-y), ('*', lambda x,y: x*y), ('/', lambda x,y: x/y)]
    while True:
        try:
            f1, f2, f3 = get_f(), get_f(), get_f()
            o1_n, o1_f = random.choice(ops)
            o2_n, o2_f = random.choice(ops)
            res1 = o1_f(f1, f2)
            ans = o2_f(res1, f3)
            break
        except ZeroDivisionError:
            continue
    q = f"({fmt(f1)} {o1_n} {fmt(f2)}) {o2_n} {fmt(f3)}".replace('*', '×').replace('/', '÷')
    ans_s = f"{ans.numerator}/{ans.denominator}" if ans.denominator != 1 else str(ans.numerator)
    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': ans_s,
        'mode': 1
    }

def check(user_answer, correct_answer):
    u = str(user_answer).strip().replace(' ', '')
    c = str(correct_answer).strip().replace(' ', '')
    is_correct = (u == c)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }