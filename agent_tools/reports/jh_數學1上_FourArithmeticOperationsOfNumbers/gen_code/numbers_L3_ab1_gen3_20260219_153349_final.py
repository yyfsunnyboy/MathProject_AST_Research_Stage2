# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 296.40s | Tokens: In=471, Out=763
# Created At: 2026-02-19 15:33:49
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt(n, b=False):
        if isinstance(n, Fraction):
            res = f"{n.numerator}/{n.denominator}" if n.denominator != 1 else str(n.numerator)
        else:
            res = str(n)
        return f"({res})" if (n < 0 and b) else res

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    while a + b == 0:
        b = random.randint(-10, 10)
    
    c_n = random.randint(1, 9)
    c_d = random.randint(2, 9)
    c = Fraction(c_n, c_d)
    
    e_n = random.choice([i for i in range(-9, 10) if i != 0])
    e_d = random.randint(2, 9)
    e = Fraction(e_n, e_d)
    
    g = random.randint(-10, 10)
    while g == 0:
        g = random.randint(-10, 10)
        
    h_n = random.choice([i for i in range(-9, 10) if i != 0])
    h_d = random.randint(2, 9)
    h = Fraction(h_n, h_d)
    
    j = random.randint(-10, 10)

    val = ((a + b) * c) / e + abs(g * h - j)
    
    sa = str(a)
    sb = f"+{b}" if b >= 0 else str(b)
    sc = fmt(c, True)
    se = fmt(e, True)
    sg = str(g)
    sh = fmt(h, True)
    sj = f"-{j}" if j >= 0 else f"+{abs(j)}"
    
    q_text = f"計算 [({sa}{sb})×{sc}]÷{se} + |{sg}×{sh}{sj}| 的值。"
    ans_str = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)
    
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        def parse(s):
            s = s.strip().replace(' ', '')
            if '/' in s:
                parts = s.split('/')
                return Fraction(int(parts[0]), int(parts[1]))
            return Fraction(s)
        
        u = parse(user_answer)
        c = parse(correct_answer)
        is_correct = (u == c)
        return {
            'correct': is_correct,
            'result': '正確' if is_correct else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }