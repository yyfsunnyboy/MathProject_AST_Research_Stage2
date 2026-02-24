# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 299.24s | Tokens: In=460, Out=540
# Created At: 2026-02-23 00:16:47
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    n1 = random.randint(-40, 40)
    n2 = random.randint(-40, 40)
    ops = ['+', '-']
    op1 = random.choice(ops)
    v1 = n1 + n2 if op1 == '+' else n1 - n2
    
    divs = [i for i in range(-20, 21) if i != 0 and v1 % i == 0]
    n3 = random.choice(divs) if divs else 1
    v2 = v1 // n3
    
    n4 = random.randint(-10, 10)
    v3 = v2 * n4
    
    n5 = random.randint(-12, 12)
    n6 = random.randint(-12, 12)
    op2 = random.choice(ops)
    n7 = random.randint(1, 30)
    v4 = n5 * n6
    v5 = v4 + n7 if op2 == '+' else v4 - n7
    v_abs = abs(v5)
    
    op_mid = random.choice(ops)
    ans = v3 + v_abs if op_mid == '+' else v3 - v_abs
    
    expr1 = f"[{p(n1)}{op1}{p(n2)}]÷{p(n3)}×{p(n4)}"
    expr2 = f"|{p(n5)}×{p(n6)}{op2}{n7}|"
    
    return {
        'question_text': f"計算 {expr1}{op_mid}{expr2} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip()
    ca = str(correct_answer).strip()
    is_correct = ua == ca
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }