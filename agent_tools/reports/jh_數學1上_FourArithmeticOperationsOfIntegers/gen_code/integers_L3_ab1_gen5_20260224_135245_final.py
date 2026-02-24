# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 7.64s | Tokens: In=508, Out=558
# Created At: 2026-02-24 13:52:45
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

        expr = f"[({a}+{b})÷({c})×{d}+|{e}×({f})-{g}|]÷({h})×{i}+|{j}×({k})-{l}|÷({m})×{n}+|{o}×({p})-{q}|"
        correct_answer = str(eval(expr))
        return {
            'question_text': expr,
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
    else:
        raise ValueError("Level must be 1")

def check(user_answer, correct_answer):
    try:
        user_answer = int(user_answer)
        correct_answer = int(correct_answer)
        return {'correct': user_answer == correct_answer, 'result': '正確' if user_answer == correct_answer else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}