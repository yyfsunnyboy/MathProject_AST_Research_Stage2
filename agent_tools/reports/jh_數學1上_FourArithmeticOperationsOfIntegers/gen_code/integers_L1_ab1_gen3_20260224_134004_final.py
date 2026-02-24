# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 16.66s | Tokens: In=508, Out=1204
# Created At: 2026-02-24 13:40:04
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(-20, 20)
        b = random.randint(-20, 20)
        c = random.randint(-20, 20)
        d = random.randint(-20, 20)
        e = random.randint(-20, 20)
        f = random.randint(-20, 20)
        g = random.randint(-20, 20)
        h = random.randint(-20, 20)
        i = random.randint(-20, 20)
        j = random.randint(-20, 20)
        k = random.randint(-20, 20)
        l = random.randint(-20, 20)
        m = random.randint(-20, 20)
        n = random.randint(-20, 20)
        o = random.randint(-20, 20)
        p = random.randint(-20, 20)
        q = random.randint(-20, 20)
        r = random.randint(-20, 20)
        s = random.randint(-20, 20)
        t = random.randint(-20, 20)
        u = random.randint(-20, 20)
        v = random.randint(-20, 20)
        w = random.randint(-20, 20)
        x = random.randint(-20, 20)
        y = random.randint(-20, 20)
        z = random.randint(-20, 20)

        expr = f"({a}+{b})÷({c}×{d})+{e}×{f}+|{g}×({h}-{i})-{j}|"
        answer = eval(expr)
        return {
            'question_text': f'計算 [{a}+{b}]÷({c}×{d})+{e}×{f}+|{g}×({h}-{i})-{j}| 的值。',
            'answer': '',
            'correct_answer': str(answer),
            'mode': 1
        }
    elif level == 2:
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

        expr = f"({a}+{b})÷({c}×{d})+{e}×{f}+|{g}×({h}-{i})-{j}|+{k}÷({l}+{m})×{n}-{o}×{p}+{q}÷({r}-{s})+{t}×{u}-{v}÷{w}+{x}×{y}-{z}"
        answer = eval(expr)
        return {
            'question_text': f'計算 [{a}+{b}]÷({c}×{d})+{e}×{f}+|{g}×({h}-{i})-{j}|+{k}÷({l}+{m})×{n}-{o}×{p}+{q}÷({r}-{s})+{t}×{u}-{v}÷{w}+{x}×{y}-{z} 的值。',
            'answer': '',
            'correct_answer': str(answer),
            'mode': 1
        }
    else:
        return {
            'question_text': '計算 [(-20)+(-10)]÷(-5)×3+|8×(-2)-5| 的值。',
            'answer': '',
            'correct_answer': '39',
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