# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 14.67s | Tokens: In=508, Out=1058
# Created At: 2026-02-24 00:33:30
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
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
        
        op1 = random.choice(['+', '-', '×', '÷'])
        op2 = random.choice(['+', '-', '×', '÷'])
        op3 = random.choice(['+', '-', '×', '÷'])
        op4 = random.choice(['+', '-', '×', '÷'])
        op5 = random.choice(['+', '-', '×', '÷'])
        op6 = random.choice(['+', '-', '×', '÷'])
        op7 = random.choice(['+', '-', '×', '÷'])
        op8 = random.choice(['+', '-', '×', '÷'])
        op9 = random.choice(['+', '-', '×', '÷'])
        op10 = random.choice(['+', '-', '×', '÷'])
        op11 = random.choice(['+', '-', '×', '÷'])
        op12 = random.choice(['+', '-', '×', '÷'])
        op13 = random.choice(['+', '-', '×', '÷'])
        op14 = random.choice(['+', '-', '×', '÷'])
        op15 = random.choice(['+', '-', '×', '÷'])
        op16 = random.choice(['+', '-', '×', '÷'])
        op17 = random.choice(['+', '-', '×', '÷'])
        op18 = random.choice(['+', '-', '×', '÷'])
        op19 = random.choice(['+', '-', '×', '÷'])
        op20 = random.choice(['+', '-', '×', '÷'])
        
        question_text = f'計算 [{a}{op1}{b}+{c}×{d}÷{e}×{f}+{g}×{h}÷{i}×{j}+{k}×{l}÷{m}×{n}+{o}×{p}÷{q}×{r}+{s}×{t}÷{u}×{v}+{w}×{x}÷{y}×{z}] 的值。'
        answer = ''
        correct_answer = str(eval(f'({a}{op1}{b}+{c}×{d}÷{e}×{f}+{g}×{h}÷{i}×{j}+{k}×{l}÷{m}×{n}+{o}×{p}÷{q}×{r}+{s}×{t}÷{u}×{v}+{w}×{x}÷{y}×{z})'))
        return {
            'question_text': question_text,
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
    else:
        return {
            'question_text': '題目生成錯誤',
            'answer': '',
            'correct_answer': '0',
            'mode': 1
        }

def check(user_answer, correct_answer):
    try:
        user_ans = int(user_answer)
        correct_ans = int(correct_answer)
        return {
            'correct': user_ans == correct_ans,
            'result': '正確' if user_ans == correct_ans else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }