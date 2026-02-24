import random
import math

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        c = random.randint(-100, 100)
        d = random.randint(-100, 100)
        e = random.randint(-100, 100)
        f = random.randint(-100, 100)
        g = random.randint(-100, 100)
        h = random.randint(-100, 100)
        i = random.randint(-100, 100)
        j = random.randint(-100, 100)
        k = random.randint(-100, 100)
        l = random.randint(-100, 100)
        m = random.randint(-100, 100)
        n = random.randint(-100, 100)
        o = random.randint(-100, 100)
        p = random.randint(-100, 100)
        q = random.randint(-100, 100)
        r = random.randint(-100, 100)
        s = random.randint(-100, 100)
        t = random.randint(-100, 100)
        u = random.randint(-100, 100)
        v = random.randint(-100, 100)
        w = random.randint(-100, 100)
        x = random.randint(-100, 100)
        y = random.randint(-100, 100)
        z = random.randint(-100, 100)
        
        expr = f"([{a}+{b}]÷{c}×{d}+|{e}×({f}-{g})-{h}|)÷({i}×{j}÷{k}+{l}×{m}÷{n}×{o}+{p}×{q}÷{r}+{s}×{t}÷{u}+{v}×{w}÷{x}+{y}×{z}÷{a})+{b}×{c}÷{d}+{e}×{f}-{g}÷{h}×{i}+{j}×{k}÷{l}+{m}×{n}÷{o}+{p}×{q}÷{r}+{s}×{t}÷{u}+{v}×{w}÷{x}+{y}×{z}÷{a}"
        correct_answer = str(eval(expr))
        return {
            'question_text': expr,
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
    else:
        return {
            'question_text': '錯誤的題目級數',
            'answer': '',
            'correct_answer': '0',
            'mode': 1
        }

def check(user_answer, correct_answer):
    try:
        user_answer = int(user_answer)
        correct_answer = int(correct_answer)
        return {
            'correct': user_answer == correct_answer,
            'result': '正確' if user_answer == correct_answer else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }