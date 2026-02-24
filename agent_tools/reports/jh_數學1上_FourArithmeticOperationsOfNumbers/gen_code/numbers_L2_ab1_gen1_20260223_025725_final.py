# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 66.49s | Tokens: In=636, Out=1921
# Created At: 2026-02-23 02:57:25
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    fractions = []
    for _ in range(4):
        numerator = random.randint(1, 10)
        denominator = random.randint(1, 10)
        if denominator == numerator:
            denominator += 1
        fractions.append(f"{numerator}/{denominator}")
    
    part1 = f"({fractions[0]}{ops[0]}{fractions[1]}){ops[2]}{fractions[2]}"
    part2 = f"{fractions[3]}{ops[3]}{fractions[0]}"
    question_text = f"計算 $[{part1}]÷({part2}) + |{fractions[1]}×({fractions[2]}{ops[1]}{fractions[3]})|$ 的值"
    
    # 計算正確答案
    def eval_fraction(expr):
        expr = expr.replace('×', '*').replace('÷', '/')
        try:
            result = eval(expr)
            if result.is_integer():
                return str(int(result))
            else:
                return f"{result.numerator}/{result.denominator}"
        except:
            return "0"
    
    correct_answer = eval_fraction(f"({part1})/({part2}) + abs({fractions[1]}*({fractions[2]}{ops[1]}{fractions[3]}))")
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user = user_answer.strip()
    correct = correct_answer.strip()
    return {
        'correct': user == correct,
        'result': '正確' if user == correct else '錯誤'
    }