# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 18.63s | Tokens: In=508, Out=1041
# Created At: 2026-02-24 13:39:32
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
        
        question_text = f"計算 [{a}{op1}{b}+{c}{op2}{d}]÷{e}{op3}{f}×{g}+|{h}{op4}{i}-{j}{op5}{k}|÷{l}{op6}{m}+{n}{op7}{o}×{p}{op8}{q}-{r}{op9}{s}|×{t}{op10}{u}+{v}{op11}{w}÷{x}{op12}{y}×{z}{op13}{a}{op14}{b}-{c}{op15}{d}|÷{e}{op16}{f}+{g}{op17}{h}×{i}{op18}{j}+{k}{op19}{l}÷{m}{op20}{n}|"
        correct_answer = str(eval(question_text.replace('÷', '/').replace('×', '*').replace('+', '+').replace('-', '-')))
        return {
            'question_text': question_text,
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
    else:
        return {
            'question_text': '',
            'answer': '',
            'correct_answer': '',
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