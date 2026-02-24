# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 9.95s | Tokens: In=508, Out=710
# Created At: 2026-02-24 00:30:51
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
        
        expression = f"[({a}+{b})÷({c})×{d}+|{e}×({f})-{g}|]÷({h})×{i}+|{j}×({k})-{l}|÷({m})×{n}+|{o}×({p})-{q}|÷({r})×{s}+|{t}×({u})-{v}|÷({w})×{x}+|{y}×({z})-{a}|"
        correct_answer = str(eval(expression))
        return {
            'question_text': f'計算 [{a}+{b})÷({c})×{d}+|{e}×({f})-{g}|]÷({h})×{i}+|{j}×({k})-{l}|÷({m})×{n}+|{o}×({p})-{q}|÷({r})×{s}+|{t}×({u})-{v}|÷({w})×{x}+|{y}×({z})-{a}| 的值。',
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
    else:
        return generate(level=1)

def check(user_answer, correct_answer):
    try:
        user_answer = user_answer.strip()
        if user_answer == correct_answer:
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}