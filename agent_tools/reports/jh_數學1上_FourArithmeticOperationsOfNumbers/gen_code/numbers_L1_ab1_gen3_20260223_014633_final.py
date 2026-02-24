# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 49.92s | Tokens: In=471, Out=727
# Created At: 2026-02-23 01:46:33
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f, paren=False):
        res = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        if paren and f < 0:
            return f"({res})"
        return res

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    while a + b == 0:
        b = random.randint(-10, 10)
    
    c = Fraction(random.randint(1, 9), random.randint(2, 9))
    e = Fraction(random.choice([i for i in range(-9, 10) if i != 0]), random.randint(2, 9))
    
    g = random.choice([i for i in range(-10, 11) if i != 0])
    h = Fraction(random.choice([i for i in range(-9, 10) if i != 0]), random.randint(2, 9))
    j = random.randint(-10, 10)
    
    term1 = ((a + b) * c) / e
    term2 = abs(g * h + j)
    
    op = random.choice(['+', '-'])
    if op == '+':
        ans = term1 + term2
    else:
        ans = term1 - term2
        
    b_part = f"+{b}" if b >= 0 else f"{b}"
    j_part = f"+{j}" if j > 0 else (f"{j}" if j < 0 else "")
    
    part1 = f"[({a}{b_part})×{f_str(c)}]÷{f_str(e, True)}"
    part2 = f"|{g}×{f_str(h, True)}{j_part}|"
    
    q_text = f"計算 {part1} {op} {part2} 的值。"
    ans_str = str(ans.numerator) if ans.denominator == 1 else f"{ans.numerator}/{ans.denominator}"
    
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    def parse(s):
        s = str(s).strip().replace(" ", "")
        try:
            if '/' in s:
                n, d = s.split('/')
                return Fraction(int(n), int(d))
            return Fraction(int(s), 1)
        except:
            return None
    ua_f = parse(user_answer)
    ca_f = parse(correct_answer)
    is_correct = (ua_f == ca_f and ua_f is not None)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }