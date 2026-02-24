import random
import math

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(-50, 50)
        b = random.randint(-50, 50)
        c = random.randint(-50, 50)
        d = random.randint(-50, 50)
        e = random.randint(-50, 50)
        f = random.randint(-50, 50)
        g = random.randint(-50, 50)
        h = random.randint(-50, 50)
        i = random.randint(-50, 50)
        j = random.randint(-50, 50)
        k = random.randint(-50, 50)
        l = random.randint(-50, 50)
        m = random.randint(-50, 50)
        n = random.randint(-50, 50)
        o = random.randint(-50, 50)
        p = random.randint(-50, 50)
        q = random.randint(-50, 50)
        r = random.randint(-50, 50)
        s = random.randint(-50, 50)
        t = random.randint(-50, 50)
        u = random.randint(-50, 50)
        v = random.randint(-50, 50)
        w = random.randint(-50, 50)
        x = random.randint(-50, 50)
        y = random.randint(-50, 50)
        z = random.randint(-50, 50)
        
        expr = f"[{a}+{b}]÷{c}×{d}+|{e}×({f}-{g})-{h}|×({i}+{j})÷({k}-{l})×{m}+{n}÷{o}×({p}+{q})-{r}÷{s}×{t}+{u}÷{v}×{w}+{x}÷{y}×{z}"
        correct_answer = str(eval(expr))
        return {
            'question_text': f'計算 [{a}+{b}]÷{c}×{d}+|{e}×({f}-{g})-{h}|×({i}+{j})÷({k}-{l})×{m}+{n}÷{o}×({p}+{q})-{r}÷{s}×{t}+{u}÷{v}×{w}+{x}÷{y}×{z} 的值。',
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
    else:
        return generate(level=1)

def check(user_answer, correct_answer):
    try:
        user_answer = int(user_answer)
        correct_answer = int(correct_answer)
        return {'correct': user_answer == correct_answer, 'result': '正確' if user_answer == correct_answer else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}