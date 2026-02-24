# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 44.25s | Tokens: In=753, Out=1202
# Created At: 2026-02-20 03:49:07
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(random.randint(2,4)):
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        if random.random() < 0.5:
            terms.append(f"\\sqrt{{{a}}}")
        else:
            terms.append(f"{random.randint(1,3)}\\sqrt{{{a}}}")
    for _ in range(random.randint(1,2)):
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        if random.random() < 0.5:
            terms.append(f"\\sqrt{{{a}}} + \\sqrt{{{b}}}")
        else:
            terms.append(f"(\\sqrt{{{a}}} + \\sqrt{{{b}}})(\\sqrt{{{a}}} - \\sqrt{{{b}}})")
    expr = " ".join(random.choices(ops, k=len(terms)-1)) 
    expr = " ".join([terms[0]] + [f"{ops[i]} {terms[i+1]}" for i in range(len(terms)-1)])
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': simplify(expr),
        'mode': 1
    }

def simplify(expr):
    expr = expr.replace('sqrt', 'math.sqrt')
    expr = expr.replace('**', '^')
    expr = expr.replace(' ', '')
    try:
        result = eval(expr)
    except:
        return "0"
    if result < 0:
        return f"-\\sqrt{{{int(-result)}}}"
    return f"\\sqrt{{{int(result)}}}"

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}